import csv
import json
import os
import random
import re
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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
    help = "Compute turkey compatibility scores in parallel using SELECT FOR UPDATE SKIP LOCKED"

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=10, help='Recipes per LLM request (default: 10)')
        parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
        parser.add_argument('--worker-id', type=str, help='Optional worker identifier for logging')

    def handle(self, *args, **options):
        api_key = os.environ.get("OPEN_ROUTER_API_KEY")
        if not api_key:
            raise CommandError("OPEN_ROUTER_API_KEY environment variable is not set.")

        batch_size = max(1, options['batch_size'])
        dry_run = options['dry_run']
        worker_id = options.get('worker_id') or f"turkey-worker-{random.randint(1000, 9999)}"

        # Initialize CSV logging
        csv_path = self._init_csv(worker_id)
        csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
        csv_writer = csv.writer(csv_file)
        if csv_file.tell() == 0:
            csv_writer.writerow(['recipe_id', 'recipe_title', 'score', 'notes'])

        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="openrouter/bert-nebulon-alpha",
            temperature=0.0,
            default_headers={
                "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost:3000"),
                "X-Title": os.environ.get("OPENROUTER_APP_TITLE", "Sous Chef Turkey Score Parallel"),
            },
        )

        self.stdout.write(self.style.SUCCESS(f"[{worker_id}] Starting parallel turkey scoring worker"))
        self.stdout.write(self.style.SUCCESS(f"[{worker_id}] Logging to: {csv_path}"))

        total_scored = 0
        total_requests = 0
        avg_request_time = 0.0
        start_time = time.time()

        # Main loop: claim and score batches until no more unscored recipes
        while True:
            # Atomically claim a batch of unscored recipes
            try:
                with transaction.atomic():
                    # Use SELECT FOR UPDATE SKIP LOCKED for lock-free parallel processing
                    # Note: We can't use the manager method with FOR UPDATE,
                    # so we order by ID and rely on the filter for work distribution
                    batch = list(
                        Recipe.objects
                        .select_for_update(skip_locked=True)
                        .filter(turkey_score=0)
                        .order_by('id')[:batch_size]
                    )

                    if not batch:
                        # No more unscored recipes
                        break

                    # Score this batch
                    request_start = time.time()
                    results = self._score_with_fallback(batch, llm, worker_id)
                    request_end = time.time()
                    request_time = request_end - request_start

                    # Update rolling average
                    total_requests += 1
                    avg_request_time = ((avg_request_time * (total_requests - 1)) + request_time) / total_requests

                    # Handle results and update database
                    batch_updates = self._handle_results(results, csv_writer, batch, worker_id)
                    csv_file.flush()

                    if not dry_run and batch_updates:
                        # Update scores and notes in the database
                        Recipe.objects.bulk_update(batch_updates, ['turkey_score', 'turkey_notes'])

                    total_scored += len(batch_updates)

                # Transaction committed - now query for remaining work (will see all workers' updates)
                unscored_remaining = Recipe.objects.filter(turkey_score=0).count()
                batches_remaining = unscored_remaining / batch_size
                estimated_seconds = batches_remaining * avg_request_time

                # Format ETA
                if estimated_seconds < 60:
                    eta_str = f"{estimated_seconds:.0f}s"
                elif estimated_seconds < 3600:
                    eta_str = f"{estimated_seconds/60:.1f}min"
                else:
                    eta_str = f"{estimated_seconds/3600:.1f}hr"

                # Display progress
                self.stdout.write(
                    f"[{worker_id}] Scored: {len(batch_updates)} | "
                    f"Total by worker: {total_scored} | "
                    f"Remaining (all): {unscored_remaining} | "
                    f"Avg: {avg_request_time:.2f}s | ETA: {eta_str}"
                )

            except Exception as exc:
                self.stdout.write(self.style.ERROR(
                    f"[{worker_id}] Error processing batch: {exc}"
                ))
                # Continue to next batch instead of crashing
                continue

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
                f"\n[{worker_id}] Statistics: {total_requests} API requests | "
                f"Avg: {avg_request_time:.2f}s | Total time: {elapsed_str}"
            )

        if total_scored == 0:
            self.stdout.write(self.style.WARNING(f"[{worker_id}] No recipes were scored (all done or claimed by other workers)."))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[{worker_id}] Dry run complete. Database was not updated."))
            return

        self.stdout.write(self.style.SUCCESS(f"[{worker_id}] Scored {total_scored} recipes."))

    def _tmp_dir(self) -> Path:
        back_end_root = Path(__file__).resolve().parents[3]
        tmp_dir = back_end_root / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _init_csv(self, worker_id: str) -> str:
        tmp_dir = self._tmp_dir()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = tmp_dir / f"turkey_scores_{worker_id}_{timestamp}.csv"
        return str(path)

    def _score_batch(self, recipes: List[Recipe], llm: ChatOpenAI, worker_id: str) -> List[Dict[str, Any]]:
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
                # No rate limiting, so just log and retry or fail
                last_error_path = self._write_error_file(prompt, response_content, exc, worker_id)
                self.stdout.write(self.style.WARNING(
                    f"[{worker_id}] API error (attempt {attempt}/{MAX_LLM_RETRIES}): {exc}"
                ))
                if attempt < MAX_LLM_RETRIES:
                    time.sleep(2)  # Brief backoff between retries
                    continue
                break

        if last_error_path:
            raise CommandError(f"LLM scoring failed. See {last_error_path}")
        raise CommandError("LLM scoring failed after retries.")

    def _score_with_fallback(self, recipes: List[Recipe], llm: ChatOpenAI, worker_id: str) -> List[Dict[str, Any]]:
        try:
            return self._score_batch(recipes, llm, worker_id)
        except CommandError as exc:
            if len(recipes) == 1:
                raise

            self.stdout.write(self.style.WARNING(
                f"[{worker_id}] Batch of {len(recipes)} recipes failed ({exc}). Retrying individually..."
            ))

            aggregated: List[Dict[str, Any]] = []
            for recipe in recipes:
                try:
                    aggregated.extend(self._score_batch([recipe], llm, worker_id))
                except CommandError as single_exc:
                    self.stdout.write(self.style.ERROR(
                        f"[{worker_id}] Failed to score recipe {recipe.id} ({recipe.title}): {single_exc}"
                    ))

            if not aggregated:
                raise CommandError(
                    f"Failed to score any recipes in batch after fallbacks (size={len(recipes)})"
                )
            return aggregated

    def _handle_results(self, entries: List[Dict[str, Any]], csv_writer, batch_recipes: List[Recipe], worker_id: str) -> List[Recipe]:
        updates: List[Recipe] = []
        by_id = {recipe.id: recipe for recipe in batch_recipes}
        for entry in entries:
            recipe_id = entry.get('id')
            score = entry.get('score')
            notes = entry.get('notes', '').strip()
            if recipe_id not in by_id:
                self.stdout.write(self.style.WARNING(f"[{worker_id}] Skipping unknown recipe ID in response: {entry}"))
                continue

            try:
                score_decimal = Decimal(str(score))
            except Exception:
                self.stdout.write(self.style.WARNING(f"[{worker_id}] Invalid score for recipe {recipe_id}: {score}"))
                continue

            score_decimal = max(Decimal('0'), min(Decimal('100'), score_decimal))
            recipe = by_id[recipe_id]
            recipe.turkey_score = score_decimal
            recipe.turkey_notes = notes
            updates.append(recipe)

            csv_writer.writerow([recipe_id, recipe.title, str(score_decimal), notes])
        return updates

    def _write_error_file(self, prompt: str, response_content: Optional[str], exc: Exception, worker_id: str) -> str:
        error_dir = self._tmp_dir() / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = error_dir / f"turkey_score_error_{worker_id}_{timestamp}.txt"
        with path.open('w', encoding='utf-8') as fh:
            fh.write(f"Worker: {worker_id}\n")
            fh.write("Prompt:\n")
            fh.write(prompt)
            fh.write("\n\nResponse:\n")
            fh.write(response_content or "(no response)")
            fh.write("\n\nError:\n")
            fh.write(str(exc))
        return str(path)
