import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Recipe, CuratedIngredient, RecipeCuratedIngredient


class Command(BaseCommand):
    help = 'Load recipe-curated ingredient links from CSV into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: /scraping/production/recipe_curated_ingredients.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing links before loading',
        )

    def handle(self, *args, **options):
        # Determine CSV path
        csv_path = options.get('csv_path')
        if not csv_path:
            csv_path = Path('/scraping/production/recipe_curated_ingredients.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading recipe-curated ingredient links from: {csv_path}')

        # Read and process CSV
        links = []
        invalid_recipes = set()
        invalid_ingredients = set()

        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                if 'recipe_id' not in reader.fieldnames or 'curated_ingredient_id' not in reader.fieldnames:
                    raise CommandError('CSV must have "recipe_id" and "curated_ingredient_id" columns')

                for row in reader:
                    recipe_id = row.get('recipe_id', '').strip()
                    curated_ingredient_id = row.get('curated_ingredient_id', '').strip()

                    if recipe_id and curated_ingredient_id:
                        try:
                            links.append({
                                'recipe_id': int(recipe_id),
                                'curated_ingredient_id': int(curated_ingredient_id)
                            })
                        except ValueError:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipping invalid IDs: recipe_id={recipe_id}, '
                                    f'curated_ingredient_id={curated_ingredient_id}'
                                )
                            )

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(links)} links in CSV')

        # Validate that recipes and curated ingredients exist
        recipe_ids = {link['recipe_id'] for link in links}
        ingredient_ids = {link['curated_ingredient_id'] for link in links}

        existing_recipes = set(Recipe.objects.filter(id__in=recipe_ids).values_list('id', flat=True))
        existing_ingredients = set(
            CuratedIngredient.objects.filter(id__in=ingredient_ids).values_list('id', flat=True)
        )

        # Filter out invalid links
        valid_links = []
        for link in links:
            if link['recipe_id'] not in existing_recipes:
                invalid_recipes.add(link['recipe_id'])
            elif link['curated_ingredient_id'] not in existing_ingredients:
                invalid_ingredients.add(link['curated_ingredient_id'])
            else:
                valid_links.append(link)

        if invalid_recipes:
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: {len(invalid_recipes)} recipe IDs not found in database'
                )
            )
        if invalid_ingredients:
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: {len(invalid_ingredients)} curated ingredient IDs not found in database'
                )
            )

        self.stdout.write(f'Valid links to process: {len(valid_links)}')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            self.stdout.write(f'Would load {len(valid_links)} recipe-curated ingredient links')
            if invalid_recipes or invalid_ingredients:
                self.stdout.write(
                    f'Would skip {len(links) - len(valid_links)} invalid links'
                )
            return

        # Clear existing data if requested
        if options['clear']:
            existing_count = RecipeCuratedIngredient.objects.count()
            self.stdout.write(f'Clearing {existing_count} existing links...')
            RecipeCuratedIngredient.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing data'))

        # Load links
        self.stdout.write('\nLoading links...')
        created_count = 0

        with transaction.atomic():
            # Create RecipeCuratedIngredient objects
            objects_to_create = [
                RecipeCuratedIngredient(
                    recipe_id=link['recipe_id'],
                    curated_ingredient_id=link['curated_ingredient_id']
                )
                for link in valid_links
            ]

            # Use bulk_create with ignore_conflicts to skip duplicates
            created = RecipeCuratedIngredient.objects.bulk_create(
                objects_to_create,
                ignore_conflicts=True
            )
            created_count = len(created)

        # Report results
        total_links = RecipeCuratedIngredient.objects.count()

        result_msg = ['\n=== Load Complete ===']
        result_msg.append(f'Created: {created_count} new links')
        result_msg.append(f'Skipped: {len(valid_links) - created_count} duplicate links')
        if invalid_recipes or invalid_ingredients:
            result_msg.append(f'Invalid: {len(links) - len(valid_links)} links (recipe or ingredient not found)')
        result_msg.append(f'Total links in database: {total_links}')

        self.stdout.write(self.style.SUCCESS('\n'.join(result_msg)))
