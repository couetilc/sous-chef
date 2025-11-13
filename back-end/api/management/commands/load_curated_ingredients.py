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
            # Now defaults to frequency report CSV which includes frequency and percentage
            csv_path = Path('/scraping/production/curated_ingredients_frequency_report.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading curated ingredients from: {csv_path}')

        # Read and process CSV
        ingredients = []
        has_frequency_data = False
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                if 'name' not in reader.fieldnames:
                    raise CommandError('CSV must have a "name" column')

                # Check if frequency and percentage columns exist
                has_frequency_data = 'frequency' in reader.fieldnames and 'percentage' in reader.fieldnames

                for row in reader:
                    name = row.get('name', '').strip()
                    if name:
                        ingredient_data = {'name': name}
                        if has_frequency_data:
                            ingredient_data['frequency'] = int(row.get('frequency', 0))
                            ingredient_data['percentage'] = float(row.get('percentage', 0.0))
                        ingredients.append(ingredient_data)

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(ingredients)} curated ingredients in CSV')
        if has_frequency_data:
            self.stdout.write('CSV includes frequency and percentage data')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN - No database changes made ==='))
            self.stdout.write(f'Sample ingredients (first 20):')
            for ingredient_data in ingredients[:20]:
                if has_frequency_data:
                    self.stdout.write(f'  - {ingredient_data["name"]}: {ingredient_data["frequency"]} recipes ({ingredient_data["percentage"]}%)')
                else:
                    self.stdout.write(f'  - {ingredient_data["name"]}')
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
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for ingredient_data in ingredients:
                name = ingredient_data['name']

                # Determine approval status
                # If we have frequency data, approve if frequency > 0 (appears in at least one recipe)
                # Otherwise, use the --auto-approve flag
                if has_frequency_data:
                    is_approved = ingredient_data['frequency'] > 0
                else:
                    is_approved = options['auto_approve']

                # Check if already exists
                existing = CuratedIngredient.objects.filter(name__iexact=name).first()

                if existing:
                    # Update existing ingredient with frequency data if available
                    if has_frequency_data:
                        existing.frequency = ingredient_data['frequency']
                        existing.percentage = ingredient_data['percentage']
                        existing.is_approved = is_approved
                        existing.save()
                        updated_count += 1
                    else:
                        skipped_count += 1
                    continue

                # Create curated ingredient
                create_kwargs = {
                    'name': name,
                    'is_approved': is_approved,
                }
                if has_frequency_data:
                    create_kwargs['frequency'] = ingredient_data['frequency']
                    create_kwargs['percentage'] = ingredient_data['percentage']

                CuratedIngredient.objects.create(**create_kwargs)
                created_count += 1

        # Report results
        total_in_db = CuratedIngredient.objects.count()
        approved_count = CuratedIngredient.objects.filter(is_approved=True).count()

        result_msg = ['\n=== Load Complete ===']
        result_msg.append(f'Created: {created_count} curated ingredients')
        if updated_count > 0:
            result_msg.append(f'Updated: {updated_count} (with frequency/percentage data)')
        if skipped_count > 0:
            result_msg.append(f'Skipped: {skipped_count} (already exist, no frequency data)')
        result_msg.append(f'Total curated ingredients in database: {total_in_db}')

        if has_frequency_data:
            result_msg.append(f'Approved ingredients (frequency > 0): {approved_count}')
            result_msg.append(f'Not approved (frequency = 0): {total_in_db - approved_count}')
        else:
            result_msg.append(f'Approved ingredients: {approved_count}')

        self.stdout.write(self.style.SUCCESS('\n'.join(result_msg)))
