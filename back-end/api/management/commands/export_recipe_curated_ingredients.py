import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import RecipeCuratedIngredient


class Command(BaseCommand):
    help = 'Export recipe-curated ingredient links to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/scraping/production/recipe_curated_ingredients.csv',
            help='Output CSV file path (default: /scraping/production/recipe_curated_ingredients.csv)',
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all recipe-curated ingredient links
        links = RecipeCuratedIngredient.objects.all().select_related(
            'recipe', 'curated_ingredient'
        ).order_by('recipe_id', 'curated_ingredient__name')

        count = links.count()
        self.stdout.write(f'Exporting {count} recipe-curated ingredient links to {output_path}...')

        # Write to CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['recipe_id', 'curated_ingredient_id'])

            # Write data
            for link in links:
                writer.writerow([link.recipe.id, link.curated_ingredient.id])

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully exported {count} recipe-curated ingredient links to {output_path}'
            )
        )
