import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Ingredient
from decimal import Decimal 


class Command(BaseCommand):
    help = 'Load ingredients from canonical_ingredients.csv into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: scraping/production/canonical_ingredients.csv)',
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
        # Determine CSV path
        csv_path = options.get('csv_path')
        if not csv_path:
            # Default path in Docker container (scraping is mounted at /scraping)
            csv_path = Path('/scraping/production/canonical_ingredients.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading ingredients from: {csv_path}')

        # Read and process CSV
        ingredients = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                for field in ['description', 'food_category', 'calories', 'protein_g', 'fat_g', 'carbs_g', 'quantity_other', 'price_g', 'price']:
                    if  field not in reader.fieldnames:
                        raise CommandError('CSV must have a "{field}" column')

                def clean_float(value):
                    try:
                        return float(value)
                    except ValueError:
                        return 0.0

                for row in reader:
                    description = row.get('description', '').strip()
                    if description:
                        description = self.clean_ingredient_name(description)
                    food_category = row.get('food_category', '').strip()
                    calories = clean_float(row.get('calories', '0').strip())
                    protein_g = clean_float(row.get('protein_g', '0').strip())
                    fat_g = clean_float(row.get('fat_g', '0').strip())
                    carbs_g = clean_float(row.get('carbs_g', '0').strip())
                    quantity_other = row.get('quantity_other', '').strip()
                    price_g = clean_float(row.get('price_g', '0').strip())
                    price = clean_float(row.get('price', '0').strip())
                    ingredients.append(Ingredient(
                        name=description,
                        food_category=food_category,
                        calories=calories,
                        protein_g=protein_g,
                        fat_g=fat_g,
                        carbs_g=carbs_g,
                        quantity_other=quantity_other,
                        price_g=price_g,
                        price=price,
                    ))

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(ingredients)} unique ingredients')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            self.stdout.write(f'Sample ingredients (first 10):')
            for ingredient in ingredients[:10]:
                self.stdout.write(f'  - {ingredient.name}')
            return

        with transaction.atomic():
            Ingredient.objects.bulk_create(ingredients)

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded ingredients:\n'
                f'  - Total in database: {Ingredient.objects.count()}'
            )
        )
