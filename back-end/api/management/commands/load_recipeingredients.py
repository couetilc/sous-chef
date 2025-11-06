import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Recipe, Ingredient, RecipeIngredient
from decimal import Decimal 
import time


class Command(BaseCommand):
    help = 'Load recipe/ingredient matchings from recipes_with_matches.csv into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: scraping/recipe_scraping/recipe_csv_files/recipes_with_matches.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )

    def clean_ingredient_name(self, name):
        """
        Basic cleaning: strip whitespace, normalize internal spaces, title case
        """
        # Strip leading/trailing whitespace
        name = name.strip()
        # Collapse multiple spaces to single space
        name = ' '.join(name.split())
        # Convert to title case
        name = name.title()
        return name

    def handle(self, *args, **options):
        start = time.time()
        # Determine CSV path
        csv_path = options.get('csv_path')
        if not csv_path:
            # Default path in Docker container (scraping is mounted at /scraping)
            csv_path = Path('/scraping/recipe_scraping/recipe_csv_files/recipes_with_matches.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading ingredients from: {csv_path}')

        # Read and process CSV
        recipeingredients = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                for field in ['ingredients_match']:
                    if  field not in reader.fieldnames:
                        raise CommandError('CSV must have a "{field}" column')

                unknownIngredient = Ingredient.objects.get_or_create(
                    name="(Unknown Ingredient)"
                )[0]

                waterPlaceholder = Ingredient.objects.get_or_create(
                    name="Water"
                )[0]

                recipe_id = 0
                for row in reader:
                    recipe_id += 1 # id corresponds to row index; start at 1
                    recipe = Recipe.objects.get(id=recipe_id)
                    ingredients_match = row.get('ingredients_match', '').strip()
                    ingredient_names = ingredients_match.split('|')
                    for name_raw in ingredient_names:
                        name_clean = self.clean_ingredient_name(name_raw)
                        try:
                            ingredient = Ingredient.objects.get(name=name_clean)
                        except:
                            print("Failed to match name: " + name_clean + " At recipe id: " + str(recipe_id))
                            ingredient = unknownIngredient
                        recipeingredients.append(RecipeIngredient(
                            quantity="Unspecified amount",
                            recipe=recipe,
                            ingredient=ingredient
                        ))

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        end = time.time()
        duration = end - start
        self.stdout.write(f'Found {len(recipeingredients)} unique mappings in '
                           + str(duration) + " seconds (Average " 
                           + str(round(duration / (recipe_id - 1) , 2)) + " seconds per recipe)" )

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            self.stdout.write(f'Sample ingredients (first 10):')
            for recipeingredient in recipeingredients[:10]:
                print(recipeingredient)
            return

        with transaction.atomic():
             RecipeIngredient.objects.all().delete()
             RecipeIngredient.objects.bulk_create(recipeingredients)

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded recipeingredients:\n'
                f'  - Total in database: {RecipeIngredient.objects.count()}'
            )
        )
