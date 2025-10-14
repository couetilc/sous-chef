import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from foundation_cleaned_ingredients.csv into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: scraping/ingredient_scraping/ingredient_csv_files/foundation_cleaned_ingredients.csv)',
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
            csv_path = Path('/scraping/ingredient_scraping/ingredient_csv_files/foundation_cleaned_ingredients.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading ingredients from: {csv_path}')

        # Read and process CSV
        ingredient_names = set()
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                if 'description' not in reader.fieldnames:
                    raise CommandError('CSV must have a "description" column')

                for row in reader:
                    description = row.get('description', '').strip()
                    if description:
                        cleaned_name = self.clean_ingredient_name(description)
                        ingredient_names.add(cleaned_name)

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(ingredient_names)} unique ingredients')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            self.stdout.write(f'Sample ingredients (first 10):')
            for name in sorted(ingredient_names)[:10]:
                self.stdout.write(f'  - {name}')
            return

        # Load into database
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for name in ingredient_names:
                obj, created = Ingredient.objects.get_or_create(name=name)
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded ingredients:\n'
                f'  - Created: {created_count}\n'
                f'  - Skipped (already exists): {skipped_count}\n'
                f'  - Total in database: {Ingredient.objects.count()}'
            )
        )
