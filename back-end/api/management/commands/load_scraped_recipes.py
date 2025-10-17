import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import ScrapedRecipe


class Command(BaseCommand):
    help = 'Load recipes from recipes_clean.csv into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to the CSV file (default: scraping/recipe_scraping/recipe_csv_files/recipes_clean.csv)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making database changes',
        )

    def clean_recipe_name(self, name):
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
            csv_path = Path('/scraping/recipe_scraping/recipe_csv_files/recipes_clean.csv')
        else:
            csv_path = Path(csv_path)

        # Validate file exists
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')

        self.stdout.write(f'Reading Recipes from: {csv_path}')

        # Read and process CSV
        recipes = list()
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify expected columns
                for column in ['title','url','image','ingredients','steps',]:
                    if column not in reader.fieldnames:
                        raise CommandError(f'CSV must have a "{column}" column')

                for row in reader:
                    title = row.get('title', '').strip()
                    url = row.get('url', '').strip()
                    image = row.get('image', '').strip()
                    ingredients = row.get('ingredients', '').strip()
                    steps = row.get('steps', '').strip()
                    recipes.append(ScrapedRecipe(
                        title=title,
                        url=url,
                        image=image,
                        ingredients=ingredients,
                        steps=steps,
                    ))

        except Exception as e:
            raise CommandError(f'Error reading CSV: {e}')

        self.stdout.write(f'Found {len(recipes)} unique recipes')

        # Dry run check
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No database changes made'))
            self.stdout.write(f'Sample recipes (first 10):')
            for name in sorted(recipes)[:10]:
                self.stdout.write(f'  - {name}')
            return

        # Load into database
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            ScrapedRecipe.objects.bulk_create(recipes, batch_size=1000)

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded recipes:\n'
                f'  - Created: {created_count}\n'
                f'  - Skipped (already exists): {skipped_count}\n'
                f'  - Total in database: {ScrapedRecipe.objects.count()}'
            )
        )
