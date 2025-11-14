import csv
from decimal import Decimal
from pathlib import Path
from typing import Dict, Tuple

from django.core.management.base import BaseCommand

from api.models import Recipe


class Command(BaseCommand):
    help = "Load deliciousness notes from CSV files in back-end/tmp/"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Find the tmp directory
        back_end_root = Path(__file__).resolve().parents[3]
        tmp_dir = back_end_root / "tmp"

        if not tmp_dir.exists():
            self.stdout.write(self.style.ERROR(f"Directory not found: {tmp_dir}"))
            return

        # Find all CSV files matching recipe_scores_*.csv
        csv_files = sorted(tmp_dir.glob("recipe_scores_*.csv"))

        if not csv_files:
            self.stdout.write(self.style.WARNING(f"No recipe_scores_*.csv files found in {tmp_dir}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(csv_files)} CSV file(s)"))

        # Dictionary to store the latest data for each recipe_id
        # Key: recipe_id, Value: (score, notes, csv_filename)
        latest_data: Dict[int, Tuple[Decimal, str, str]] = {}

        # Process CSV files in chronological order (sorted by filename timestamp)
        for csv_path in csv_files:
            self.stdout.write(f"Processing: {csv_path.name}")

            try:
                with csv_path.open('r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)

                    # Verify expected columns
                    if reader.fieldnames != ['recipe_id', 'recipe_title', 'score', 'notes']:
                        self.stdout.write(self.style.WARNING(
                            f"Skipping {csv_path.name}: unexpected columns {reader.fieldnames}"
                        ))
                        continue

                    count = 0
                    for row in reader:
                        try:
                            recipe_id = int(row['recipe_id'])
                            score = Decimal(row['score'])
                            notes = row['notes'].strip()

                            # Store/overwrite with latest data
                            latest_data[recipe_id] = (score, notes, csv_path.name)
                            count += 1

                        except (ValueError, KeyError) as e:
                            self.stdout.write(self.style.WARNING(
                                f"Skipping invalid row in {csv_path.name}: {e}"
                            ))
                            continue

                    self.stdout.write(f"  Processed {count} rows")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading {csv_path.name}: {e}"))
                continue

        if not latest_data:
            self.stdout.write(self.style.WARNING("No valid data found in CSV files"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\nCollected data for {len(latest_data)} unique recipes"
        ))

        # Fetch all recipes that need updating
        recipe_ids = list(latest_data.keys())
        recipes = Recipe.objects.filter(id__in=recipe_ids)
        recipes_by_id = {r.id: r for r in recipes}

        # Update recipes with notes and scores
        updates = []
        stats = {
            'updated': 0,
            'not_found': 0,
            'already_current': 0,
        }

        for recipe_id, (score, notes, source_file) in latest_data.items():
            if recipe_id not in recipes_by_id:
                stats['not_found'] += 1
                self.stdout.write(self.style.WARNING(
                    f"Recipe ID {recipe_id} not found in database (from {source_file})"
                ))
                continue

            recipe = recipes_by_id[recipe_id]

            # Check if update is needed
            needs_update = False
            if recipe.deliciousness_score != score:
                recipe.deliciousness_score = score
                needs_update = True
            if recipe.deliciousness_notes != notes:
                recipe.deliciousness_notes = notes
                needs_update = True

            if needs_update:
                updates.append(recipe)
                stats['updated'] += 1
            else:
                stats['already_current'] += 1

        # Display summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Summary:")
        self.stdout.write(f"  Total recipes in CSVs: {len(latest_data)}")
        self.stdout.write(f"  Recipes to update: {stats['updated']}")
        self.stdout.write(f"  Already current: {stats['already_current']}")
        self.stdout.write(f"  Not found in DB: {stats['not_found']}")
        self.stdout.write("="*60)

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes saved to database"))
            if updates:
                self.stdout.write("\nSample updates (first 5):")
                for recipe in updates[:5]:
                    self.stdout.write(
                        f"  [{recipe.id}] {recipe.title[:50]} -> "
                        f"score={recipe.deliciousness_score}, "
                        f"notes=\"{recipe.deliciousness_notes[:40]}...\""
                    )
            return

        if not updates:
            self.stdout.write(self.style.SUCCESS("\nNo updates needed - all recipes already current"))
            return

        # Bulk update
        Recipe.objects.bulk_update(updates, ['deliciousness_score', 'deliciousness_notes'])

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Successfully updated {len(updates)} recipes with scores and notes"
        ))
