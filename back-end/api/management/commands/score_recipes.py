import csv
import json
import os
import re
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError

from api.models import Recipe
from langchain_openai import ChatOpenAI


PROMPT_INTRO = """You are a discerning, no-nonsense food critic.
Score each recipe's overall deliciousness on a 0-100 scale based on its name, ingredients, and instructions. Reward recipes that promise nutritious, satisfying meals that home cooks can execute without much hassle.

Scoring rubric:
0-49: Unappealing or likely to fail.
50-69: Edible but forgettable.
70-84: Tasty everyday cooking that most people would enjoy.
85-92: Crowd-pleasing dish with craveable flavor or texture.
93-100: Exceptional, "must cook" recipes people rave about.

Guidelines:
- Reward recipes that are both nutritious and satisfying without being overly complicated.
- Prioritize dishes that seem easy to cook yet still deliver bold, craveable flavor.
- Penalize vague instructions or missing flavor-building steps.
- Reward balanced seasoning, appealing textures, and smart technique.

Return ONLY valid JSON with this exact shape:
{"recipes":[{"id":123,"score":87,"notes":"short justification"}]}

Notes must be 5-25 words describing the main reason for the score.
Do not include markdown code fences or any text before/after the JSON.

Recipes to score:
""".strip()

MAX_CHARS = 1200
SLEEP_SECONDS = 0.3
MAX_LLM_RETRIES = 3


def clean_and_truncate(text: str, max_chars: int = MAX_CHARS) -> str:
    if not text:
        return ""
    cleaned = " ".join(text.replace("\r", " ").split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def build_recipe_block(recipe: Recipe) -> str:
    ingredients = clean_and_truncate(recipe.ingredients or "")
    instructions = clean_and_truncate(recipe.instructions or "")
    return (
        f"ID: {recipe.id}\n"
        f"Name: {recipe.title.strip()}\n"
        f"Ingredients: {ingredients}\n"
        f"Instructions: {instructions}\n"
    )


def extract_json_object(raw_content: str) -> Dict[str, Any]:
    candidate = raw_content.strip()
    if candidate.startswith("```"):
        # Attempt to pull JSON block inside fences
        fence_start = candidate.find("{")
        fence_end = candidate.rfind("}")
        if fence_start != -1 and fence_end != -1:
            candidate = candidate[fence_start:fence_end + 1]
    if not candidate.startswith("{"):
        first_brace = candidate.find("{")
        last_brace = candidate.rfind("}")
        if first_brace == -1 or last_brace == -1:
            raise ValueError("Response did not contain JSON object.")
        candidate = candidate[first_brace:last_brace + 1]
    return json.loads(candidate)


class Command(BaseCommand):
    help = "Compute deliciousness scores for recipes using the Polaris Alpha model."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, help='Maximum number of recipes to score')
        parser.add_argument('--batch-size', type=int, default=5, help='Recipes per LLM request (default: 5)')
        parser.add_argument('--resume-from', type=int, help='Recipe ID to resume after (skips until this ID is seen)')
        parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
        parser.add_argument('--only-missing', action='store_true', help='Only score recipes with a zero deliciousness score')
        parser.add_argument('--csv-path', type=str, help='Optional path for the incremental CSV log')

    def handle(self, *args, **options):
        api_key = os.environ.get("OPEN_ROUTER_API_KEY")
        if not api_key:
            raise CommandError("OPEN_ROUTER_API_KEY environment variable is not set.")

        batch_size = max(1, options['batch_size'])
        limit = options.get('limit')
        dry_run = options['dry_run']
        resume_from = options.get('resume_from')
        only_missing = options['only_missing']

        queryset = Recipe.objects.order_by_ingredient_accessibility()
        if only_missing:
            queryset = queryset.filter(deliciousness_score=0)

        csv_path = options.get('csv_path') or self._init_csv()
        csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        if csv_file.tell() == 0:
            csv_writer.writerow(['recipe_id', 'recipe_title', 'score', 'notes'])

        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="z-ai/glm-4.5-air:free",
            temperature=0.0,
            default_headers={
                "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost:3000"),
                "X-Title": os.environ.get("OPENROUTER_APP_TITLE", "Sous Chef Deliciousness"),
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Logging batch results to: {csv_path}"))

        processed = 0
        batch: List[Recipe] = []
        resume_reached = resume_from is None
        total_updates = 0

        for recipe in queryset.iterator(chunk_size=500):
            if not resume_reached:
                if recipe.id == resume_from:
                    resume_reached = True
                continue

            if limit and processed >= limit:
                break

            batch.append(recipe)
            processed += 1

            if len(batch) == batch_size:
                batch_copy = list(batch)
                results = self._score_with_fallback(batch_copy, llm)
                batch_updates = self._handle_results(results, csv_writer, batch_copy)
                csv_file.flush()
                if not dry_run and batch_updates:
                    Recipe.objects.bulk_update(batch_updates, ['deliciousness_score'])
                total_updates += len(batch_updates)
                batch = []
                time.sleep(SLEEP_SECONDS)

        if resume_from and not resume_reached:
            self.stdout.write(self.style.WARNING(
                f"Resume ID {resume_from} was not found in the current queryset."
            ))

        # Process any remaining recipes
        if batch:
            batch_copy = list(batch)
            results = self._score_with_fallback(batch_copy, llm)
            batch_updates = self._handle_results(results, csv_writer, batch_copy)
            csv_file.flush()
            if not dry_run and batch_updates:
                Recipe.objects.bulk_update(batch_updates, ['deliciousness_score'])
            total_updates += len(batch_updates)

        csv_file.close()

        if total_updates == 0:
            self.stdout.write(self.style.WARNING("No recipes were scored."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. Database was not updated."))
            return

        self.stdout.write(self.style.SUCCESS(f"Updated {total_updates} recipes with new deliciousness scores."))

    def _tmp_dir(self) -> Path:
        back_end_root = Path(__file__).resolve().parents[3]
        tmp_dir = back_end_root / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _init_csv(self) -> str:
        tmp_dir = self._tmp_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = tmp_dir / f"recipe_scores_{timestamp}.csv"
        return str(path)

    def _score_batch(self, recipes: List[Recipe], llm: ChatOpenAI) -> List[Dict[str, Any]]:
        prompt = PROMPT_INTRO + "\n\n" + "\n---\n".join(build_recipe_block(r) for r in recipes)
        attempt = 0
        last_error_path: Optional[str] = None
        while attempt < MAX_LLM_RETRIES:
            attempt += 1
            response_content: Optional[str] = None
            try:
                response = llm.invoke(prompt)
                response_content = response.content.strip()
                data = extract_json_object(response_content)
                if 'recipes' not in data or not isinstance(data['recipes'], list):
                    raise ValueError("JSON response missing 'recipes' list.")
                return data['recipes']
            except Exception as exc:
                wait_seconds = self._get_rate_limit_wait_seconds(exc)
                if wait_seconds is not None:
                    self.stdout.write(self.style.WARNING(
                        f"Rate limit hit. Waiting {wait_seconds:.1f}s before retry (attempt {attempt}/{MAX_LLM_RETRIES})."
                    ))
                    time.sleep(wait_seconds)
                    continue

                last_error_path = self._write_error_file(prompt, response_content, exc)
                break

        if last_error_path:
            raise CommandError(f"LLM scoring failed. See {last_error_path}")
        raise CommandError("LLM scoring failed after repeated rate limit retries.")

    def _score_with_fallback(self, recipes: List[Recipe], llm: ChatOpenAI) -> List[Dict[str, Any]]:
        try:
            return self._score_batch(recipes, llm)
        except CommandError as exc:
            if len(recipes) == 1:
                raise

            self.stdout.write(self.style.WARNING(
                f"Batch of {len(recipes)} recipes failed ({exc}). Retrying individually..."
            ))

            aggregated: List[Dict[str, Any]] = []
            for recipe in recipes:
                try:
                    aggregated.extend(self._score_batch([recipe], llm))
                except CommandError as single_exc:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to score recipe {recipe.id} ({recipe.title}): {single_exc}"
                    ))

            if not aggregated:
                raise CommandError(
                    f"Failed to score any recipes in batch after fallbacks (size={len(recipes)})"
                )
            return aggregated

    def _handle_results(self, entries: List[Dict[str, Any]], csv_writer, batch_recipes: List[Recipe]) -> List[Recipe]:
        updates: List[Recipe] = []
        by_id = {recipe.id: recipe for recipe in batch_recipes}
        for entry in entries:
            recipe_id = entry.get('id')
            score = entry.get('score')
            notes = entry.get('notes', '').strip()
            if recipe_id not in by_id:
                self.stdout.write(self.style.WARNING(f"Skipping unknown recipe ID in response: {entry}"))
                continue

            try:
                score_decimal = Decimal(str(score))
            except Exception:
                self.stdout.write(self.style.WARNING(f"Invalid score for recipe {recipe_id}: {score}"))
                continue

            score_decimal = max(Decimal('0'), min(Decimal('100'), score_decimal))
            recipe = by_id[recipe_id]
            recipe.deliciousness_score = score_decimal
            updates.append(recipe)

            csv_writer.writerow([recipe_id, recipe.title, str(score_decimal), notes])
        return updates

    def _write_error_file(self, prompt: str, response_content: Optional[str], exc: Exception) -> str:
        error_dir = self._tmp_dir() / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = error_dir / f"recipe_score_error_{timestamp}.txt"
        with path.open('w', encoding='utf-8') as fh:
            fh.write("Prompt:\n")
            fh.write(prompt)
            fh.write("\n\nResponse:\n")
            fh.write(response_content or "(no response)")
            fh.write("\n\nError:\n")
            fh.write(str(exc))
        return str(path)

    def _get_rate_limit_wait_seconds(self, exc: Exception) -> Optional[float]:
        response = getattr(exc, 'response', None)
        headers = {}
        if response is not None:
            headers = getattr(response, 'headers', {}) or {}

        reset_header = headers.get('X-RateLimit-Reset')
        if not reset_header:
            body = getattr(exc, 'body', None)
            if isinstance(body, dict):
                reset_header = (
                    body.get('error', {})
                    .get('metadata', {})
                    .get('headers', {})
                    .get('X-RateLimit-Reset')
                )

        if not reset_header:
            message = str(exc)
            match = re.search(r"X-RateLimit-Reset': '(\d+)'", message)
            if match:
                reset_header = match.group(1)

        if not reset_header:
            if 'Rate limit exceeded' in str(exc):
                return 10.0
            return None

        try:
            reset_value = float(reset_header)
            if reset_value > 10**12:
                reset_value /= 1000.0
            wait_seconds = max(0.0, reset_value - time.time())
            if wait_seconds == 0:
                wait_seconds = 1.0
            return min(wait_seconds + 1.0, 120.0)
        except Exception:
            return 10.0
