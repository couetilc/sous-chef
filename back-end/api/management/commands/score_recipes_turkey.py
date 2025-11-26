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


PROMPT_INTRO = """You are a turkey compatibility expert evaluating recipes for Thanksgiving turkey meals.
Score each recipe on a 0-100 scale based on how well it pairs with turkey as a Thanksgiving side dish or complement. Focus on traditional Thanksgiving flavors and how harmoniously the dish works alongside roasted turkey.

Scoring rubric:
0-49: Clashes with turkey or doesn't fit Thanksgiving themes (e.g., spicy Asian dishes, seafood-forward dishes).
50-69: Acceptable but not traditional or harmonious (e.g., generic vegetables, basic starches).
70-84: Good Thanksgiving compatibility, complements turkey well (e.g., roasted vegetables, simple stuffing).
85-92: Excellent turkey pairing, classic Thanksgiving flavors (e.g., cranberry sauce, green bean casserole, traditional stuffing).
93-100: Perfect Thanksgiving essential, iconic turkey companion (e.g., classic gravy, perfect mashed potatoes, traditional stuffing with sage).

Guidelines:
- Prioritize traditional Thanksgiving flavors: sage, thyme, rosemary, cranberry, sweet potato, etc.
- Reward dishes that complement turkey's savory, mild flavor profile.
- Consider balance: does this add something turkey lacks (sweetness, acidity, crunch)?
- Favor comforting, fall-appropriate ingredients and preparations.
- Penalize dishes that compete with turkey (other proteins, strong conflicting flavors, non-seasonal ingredients).

Return ONLY valid JSON with this exact shape:
{"recipes":[{"id":123,"score":87,"notes":"short justification"}]}

Notes must be 5-25 words describing why this recipe works (or doesn't) with turkey.
Do not include markdown code fences or any text before/after the JSON.

Recipes to score:
""".strip()

MAX_CHARS = 1200
SLEEP_SECONDS = 0.1
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
    help = "Compute turkey compatibility scores for recipes using the Grok AI model."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, help='Maximum number of recipes to score')
        parser.add_argument('--batch-size', type=int, default=10, help='Recipes per LLM request (default: 10)')
        parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
        parser.add_argument('--only-missing', action='store_true', help='Only score recipes with a zero turkey score')
        parser.add_argument('--csv-path', type=str, help='Optional path for the incremental CSV log')

    def handle(self, *args, **options):
        api_key = os.environ.get("OPEN_ROUTER_API_KEY")
        if not api_key:
            raise CommandError("OPEN_ROUTER_API_KEY environment variable is not set.")

        batch_size = max(1, options['batch_size'])
        limit = options.get('limit')
        dry_run = options['dry_run']
        only_missing = options['only_missing']

        queryset = Recipe.objects.order_by_ingredient_accessibility()
        if only_missing:
            queryset = queryset.filter(turkey_score=0)

        # Calculate total for progress tracking (always count unscored for accurate ETA)
        unscored_count = Recipe.objects.filter(turkey_score=0).count()
        total_recipes = queryset.count()  # What we'll actually process
        if limit:
            total_recipes = min(total_recipes, limit)
            unscored_count = min(unscored_count, limit)

        csv_path = options.get('csv_path') or self._init_csv()
        csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        if csv_file.tell() == 0:
            csv_writer.writerow(['recipe_id', 'recipe_title', 'score', 'notes'])

        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="x-ai/grok-4.1-fast",
            temperature=0.0,
            default_headers={
                "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost:3000"),
                "X-Title": os.environ.get("OPENROUTER_APP_TITLE", "Sous Chef Turkey Score"),
            },
        )

        self.stdout.write(self.style.SUCCESS(f"Logging batch results to: {csv_path}"))
        self.stdout.write(self.style.SUCCESS(f"Total recipes to process: {total_recipes}"))
        if total_recipes != unscored_count:
            self.stdout.write(self.style.SUCCESS(f"Unscored recipes (for ETA): {unscored_count}"))

        processed = 0
        batch: List[Recipe] = []
        total_updates = 0
        total_requests = 0
        avg_request_time = 0.0
        start_time = time.time()

        for recipe in queryset.iterator(chunk_size=500):
            if limit and processed >= limit:
                break

            batch.append(recipe)
            processed += 1

            if len(batch) == batch_size:
                batch_copy = list(batch)

                # Time the API request
                request_start = time.time()
                results = self._score_with_fallback(batch_copy, llm)
                request_end = time.time()
                request_time = request_end - request_start

                # Update rolling average
                total_requests += 1
                avg_request_time = ((avg_request_time * (total_requests - 1)) + request_time) / total_requests

                batch_updates = self._handle_results(results, csv_writer, batch_copy)
                csv_file.flush()
                if not dry_run and batch_updates:
                    Recipe.objects.bulk_update(batch_updates, ['turkey_score', 'turkey_notes'])
                total_updates += len(batch_updates)

                # Calculate statistics (use unscored_count for accurate ETA)
                recipes_remaining = max(0, unscored_count - total_updates)
                batches_remaining = recipes_remaining / batch_size
                estimated_seconds = (batches_remaining * avg_request_time) + (batches_remaining * SLEEP_SECONDS)

                # Format time remaining
                if estimated_seconds < 60:
                    eta_str = f"{estimated_seconds:.0f}s"
                elif estimated_seconds < 3600:
                    eta_str = f"{estimated_seconds/60:.1f}min"
                else:
                    eta_str = f"{estimated_seconds/3600:.1f}hr"

                # Display progress
                percentage = (total_updates / unscored_count * 100) if unscored_count > 0 else 0
                self.stdout.write(
                    f"Scored: {total_updates}/{unscored_count} ({percentage:.1f}%) | "
                    f"Processed: {processed}/{total_recipes} | "
                    f"Avg request: {avg_request_time:.2f}s | ETA: {eta_str}"
                )

                batch = []
                time.sleep(SLEEP_SECONDS)

        # Process any remaining recipes
        if batch:
            batch_copy = list(batch)

            # Time the final API request
            request_start = time.time()
            results = self._score_with_fallback(batch_copy, llm)
            request_end = time.time()
            request_time = request_end - request_start

            # Update rolling average
            total_requests += 1
            avg_request_time = ((avg_request_time * (total_requests - 1)) + request_time) / total_requests

            batch_updates = self._handle_results(results, csv_writer, batch_copy)
            csv_file.flush()
            if not dry_run and batch_updates:
                Recipe.objects.bulk_update(batch_updates, ['turkey_score', 'turkey_notes'])
            total_updates += len(batch_updates)

            # Display final progress
            percentage = (total_updates / unscored_count * 100) if unscored_count > 0 else 0
            self.stdout.write(
                f"Scored: {total_updates}/{unscored_count} ({percentage:.1f}%) | "
                f"Processed: {processed}/{total_recipes} | "
                f"Avg request: {avg_request_time:.2f}s"
            )

        csv_file.close()

        # Display final statistics
        total_elapsed = time.time() - start_time
        if total_elapsed < 60:
            elapsed_str = f"{total_elapsed:.1f}s"
        elif total_elapsed < 3600:
            elapsed_str = f"{total_elapsed/60:.1f}min"
        else:
            elapsed_str = f"{total_elapsed/3600:.2f}hr"

        if total_requests > 0:
            self.stdout.write(
                f"\nStatistics: {total_requests} API requests | "
                f"Avg: {avg_request_time:.2f}s | Total time: {elapsed_str}"
            )

        if total_updates == 0:
            self.stdout.write(self.style.WARNING("No recipes were scored."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run complete. Database was not updated."))
            return

        self.stdout.write(self.style.SUCCESS(f"Updated {total_updates} recipes with new turkey scores."))

    def _tmp_dir(self) -> Path:
        back_end_root = Path(__file__).resolve().parents[3]
        tmp_dir = back_end_root / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _init_csv(self) -> str:
        tmp_dir = self._tmp_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = tmp_dir / f"turkey_scores_{timestamp}.csv"
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
            recipe.turkey_score = score_decimal
            recipe.turkey_notes = notes
            updates.append(recipe)

            csv_writer.writerow([recipe_id, recipe.title, str(score_decimal), notes])
        return updates

    def _write_error_file(self, prompt: str, response_content: Optional[str], exc: Exception) -> str:
        error_dir = self._tmp_dir() / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = error_dir / f"turkey_score_error_{timestamp}.txt"
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
