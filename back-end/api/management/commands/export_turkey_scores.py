import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import Recipe


class Command(BaseCommand):
    help = 'Export recipe turkey scores and notes to CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/scraping/production/turkey_scores.csv',
            help='Output CSV file path (default: /scraping/production/turkey_scores.csv)',
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get all recipes ordered by title
        recipes = Recipe.objects.all().order_by('title')

        self.stdout.write(f'Exporting turkey scores for {recipes.count()} recipes to {output_path}...')

        # Write to CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['title', 'turkey_score', 'turkey_notes'])

            # Write data
            for recipe in recipes:
                writer.writerow([
                    recipe.title,
                    str(recipe.turkey_score),
                    recipe.turkey_notes
                ])

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Successfully exported {recipes.count()} turkey scores to {output_path}'
            )
        )
