import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import CuratedIngredient


class Command(BaseCommand):
    help = 'Load curated ingredients from CSV into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: /scraping/production/curated_ingredients.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing curated ingredients before loading',
        )
        parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Automatically approve all loaded ingredients',
        )

    def handle(self, *args, **options):
        # Determine CSV path
        csv_path = options.get('csv_path')
        if not csv_path:
            # Default path in Docker container (scraping is mounted at /scraping)
            csv_path = Path('/scraping/production/curated_ingredients.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading curated ingredients from: {csv_path}')

        # Read and process CSV
        ingredients = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                if 'name' not in reader.fieldnames:
                    raise CommandError('CSV must have a "name" column')

                for row in reader:
                    name = row.get('name', '').strip()
                    if name:
                        ingredients.append(name)

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(ingredients)} curated ingredients in CSV')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            self.stdout.write(f'Sample ingredients (first 20):')
            for name in ingredients[:20]:
                self.stdout.write(f'  - {name}')
            if len(ingredients) > 20:
                self.stdout.write(f'  ... and {len(ingredients) - 20} more')
            return

        # Clear existing data if requested
        if options['clear']:
            existing_count = CuratedIngredient.objects.count()
            self.stdout.write(f'Clearing {existing_count} existing curated ingredients...')
            CuratedIngredient.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared existing data'))

        # Load ingredients
        self.stdout.write('\nLoading ingredients...')
        created_count = 0
        skipped_count = 0
        is_approved = options['auto_approve']

        with transaction.atomic():
            for name in ingredients:
                # Check if already exists
                if CuratedIngredient.objects.filter(name__iexact=name).exists():
                    skipped_count += 1
                    continue

                # Create curated ingredient
                CuratedIngredient.objects.create(
                    name=name,
                    is_approved=is_approved,
                )
                created_count += 1

        # Report results
        approval_msg = f" (auto-approved)" if is_approved else ""
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Load Complete ===\n'
                f'Created: {created_count} curated ingredients{approval_msg}\n'
                f'Skipped: {skipped_count} (already exist)\n'
                f'Total curated ingredients in database: {CuratedIngredient.objects.count()}'
            )
        )

        if is_approved:
            approved_count = CuratedIngredient.objects.filter(is_approved=True).count()
            self.stdout.write(f'Approved ingredients: {approved_count}')
