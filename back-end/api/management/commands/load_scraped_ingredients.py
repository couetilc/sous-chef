import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import ScrapedIngredient


class Command(BaseCommand):
    help = 'Load ingredients from legacy_cleaned_ingredients.csv into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: scraping/ingredient_scraping/ingredient_csv_files/legacy_cleaned_ingredients.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )

    def clean_ingredient_name(self, name):
        """ Basic cleaning: strip whitespace, normalize internal spaces, title case """
        name = name.strip()
        name = ' '.join(name.split())
        return name.title()

    def handle(self, *args, **options):
        csv_path = options.get('csv_path')
        if not csv_path:
            csv_path = Path('/scraping/ingredient_scraping/ingredient_csv_files/legacy_cleaned_ingredients.csv')
        else:
            csv_path = Path(csv_path)

        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading ingredients from: {csv_path}')

        # Map cleaned_name -> first seen food_category (or '' if none)
        ingredient_map = {}

        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                if 'description' not in reader.fieldnames:
                    raise CommandError('CSV must have a "description" column')

                # food_category is optional in case some files don't have it
                has_food_cat = 'food_category' in reader.fieldnames

                for row in reader:
                    description = row.get('description', '').strip()
                    if not description:
                        continue

                    cleaned = self.clean_ingredient_name(description)

                    # choose category if present (first seen)
                    if has_food_cat:
                        fc = row.get('food_category', '').strip()
                        if cleaned not in ingredient_map:
                            ingredient_map[cleaned] = fc
                    else:
                        if cleaned not in ingredient_map:
                            ingredient_map[cleaned] = ''

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(ingredient_map)} unique ingredients')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            self.stdout.write('Sample ingredients (first 10):')
            for name in sorted(ingredient_map.keys())[:10]:
                self.stdout.write(f'  - {name} (category: {ingredient_map[name]})')
            return

        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for name, food_category in ingredient_map.items():
                obj, created = ScrapedIngredient.objects.get_or_create(
                    description=name,
                    defaults={'food_category': food_category}
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded ingredients:\n'
                f'  - Created: {created_count}\n'
                f'  - Skipped (already exists): {skipped_count}\n'
                f'  - Total in database: {ScrapedIngredient.objects.count()}'
            )
        )
