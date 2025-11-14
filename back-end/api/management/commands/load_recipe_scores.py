import csv
from pathlib import Path
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Recipe


class Command(BaseCommand):
    help = 'Load recipe deliciousness scores and notes from CSV into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='/scraping/production/recipe_scores.csv',
            help='Path to the CSV file (default: /scraping/production/recipe_scores.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading recipe scores from: {csv_path}')

        # Read and process CSV
        recipe_scores = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                required_columns = ['title', 'deliciousness_score', 'deliciousness_notes']
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                if missing_columns:
                    raise CommandError(f'CSV missing required columns: {", ".join(missing_columns)}')

                for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                    title = row.get('title', '').strip()
                    score_str = row.get('deliciousness_score', '').strip()
                    notes = row.get('deliciousness_notes', '').strip()

                    if not title:
                        self.stdout.write(self.style.WARNING(f'Row {row_num}: Skipping row with empty title'))
                        continue

                    # Parse and validate score
                    try:
                        score = Decimal(score_str) if score_str else Decimal('0')
                        if score < 0 or score > 100:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Row {row_num}: Score {score} for "{title}" is out of range (0-100), setting to 0'
                                )
                            )
                            score = Decimal('0')
                    except (InvalidOperation, ValueError):
                        self.stdout.write(
                            self.style.WARNING(
                                f'Row {row_num}: Invalid score "{score_str}" for "{title}", setting to 0'
                            )
                        )
                        score = Decimal('0')

                    recipe_scores.append({
                        'title': title,
                        'score': score,
                        'notes': notes
                    })

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(recipe_scores)} recipe scores in CSV')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            self.stdout.write(f'Sample recipe scores (first 10):')
            for recipe_data in recipe_scores[:10]:
                self.stdout.write(
                    f'  - {recipe_data["title"]}: {recipe_data["score"]} '
                    f'({recipe_data["notes"][:50]}{"..." if len(recipe_data["notes"]) > 50 else ""})'
                )
            if len(recipe_scores) > 10:
                self.stdout.write(f'  ... and {len(recipe_scores) - 10} more')
            return

        # Load scores using bulk updates
        self.stdout.write('\nLoading recipe scores...')
        updated_count = 0
        not_found_count = 0
        not_found_titles = []
        multiple_count = 0
        batch_size = 1000

        # Create a mapping of title -> score data
        title_to_score = {item['title']: item for item in recipe_scores}

        with transaction.atomic():
            # Process in batches
            titles = list(title_to_score.keys())
            for i in range(0, len(titles), batch_size):
                batch_titles = titles[i:i + batch_size]
                self.stdout.write(f'Processing batch {i // batch_size + 1} of {(len(titles) + batch_size - 1) // batch_size}...')

                # Fetch all recipes with titles in this batch
                recipes = Recipe.objects.filter(title__in=batch_titles)
                recipes_by_title = {}
                for recipe in recipes:
                    if recipe.title not in recipes_by_title:
                        recipes_by_title[recipe.title] = []
                    recipes_by_title[recipe.title].append(recipe)

                # Update recipes in memory
                recipes_to_update = []
                for title in batch_titles:
                    if title in recipes_by_title:
                        recipe_list = recipes_by_title[title]
                        score_data = title_to_score[title]

                        for recipe in recipe_list:
                            recipe.deliciousness_score = score_data['score']
                            recipe.deliciousness_notes = score_data['notes']
                            recipes_to_update.append(recipe)

                        updated_count += len(recipe_list)
                        if len(recipe_list) > 1:
                            multiple_count += 1
                    else:
                        not_found_count += 1
                        not_found_titles.append(title)

                # Bulk update all recipes in this batch
                if recipes_to_update:
                    Recipe.objects.bulk_update(
                        recipes_to_update,
                        ['deliciousness_score', 'deliciousness_notes'],
                        batch_size=batch_size
                    )

        # Report results
        result_msg = ['\n=== Load Complete ===']
        result_msg.append(f'Updated: {updated_count} recipes')
        if multiple_count > 0:
            result_msg.append(f'Multiple recipes with same title: {multiple_count} titles (all updated)')
        if not_found_count > 0:
            result_msg.append(f'Not found: {not_found_count} recipes')
            if not_found_count <= 10:
                result_msg.append('\nRecipes not found in database:')
                for title in not_found_titles:
                    result_msg.append(f'  - {title}')
            else:
                result_msg.append(f'\nFirst 10 recipes not found:')
                for title in not_found_titles[:10]:
                    result_msg.append(f'  - {title}')
                result_msg.append(f'  ... and {not_found_count - 10} more')

        self.stdout.write(self.style.SUCCESS('\n'.join(result_msg)))
