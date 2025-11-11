import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import CuratedIngredient


class Command(BaseCommand):
    help = 'Export curated ingredients to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/scraping/production/curated_ingredients.csv',
            help='Output CSV file path (default: /scraping/production/curated_ingredients.csv)',
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all curated ingredients ordered by name
        ingredients = CuratedIngredient.objects.all().order_by('name')

        self.stdout.write(f'Exporting {ingredients.count()} curated ingredients to {output_path}...')

        # Write to CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['name'])

            # Write data
            for ingredient in ingredients:
                writer.writerow([ingredient.name])

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully exported {ingredients.count()} curated ingredients to {output_path}'
            )
        )
