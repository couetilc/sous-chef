import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import CuratedIngredient, Recipe


class Command(BaseCommand):
    help = 'Analyze curated ingredient frequency in recipes and generate a CSV report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='/scraping/production/curated_ingredients_frequency_report.csv',
            help='Output CSV file path (default: /scraping/production/curated_ingredients_frequency_report.csv)',
        )

    def handle(self, *args, **options):
        output_path = Path(options['output'])

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load all curated ingredients and recipes
        curated_ingredients = CuratedIngredient.objects.all()
        recipes = Recipe.objects.all()

        total_curated = curated_ingredients.count()
        total_recipes = recipes.count()

        self.stdout.write(f'Analyzing {total_curated} curated ingredients across {total_recipes} recipes...\n')

        if total_recipes == 0:
            self.stdout.write(self.style.WARNING('No recipes found in database. Cannot generate frequency report.'))
            return

        # Build frequency data
        frequency_data = []
        ingredients_with_zero_matches = 0

        for ingredient in curated_ingredients:
            count = 0
            # Case-insensitive substring search in recipe ingredients field
            for recipe in recipes:
                if recipe.ingredients and ingredient.name.lower() in recipe.ingredients.lower():
                    count += 1

            percentage = (count / total_recipes * 100) if total_recipes > 0 else 0
            frequency_data.append({
                'name': ingredient.name,
                'frequency': count,
                'percentage': round(percentage, 2)
            })

            if count == 0:
                ingredients_with_zero_matches += 1

        # Sort by frequency (descending - most common first)
        frequency_data.sort(key=lambda x: x['frequency'], reverse=True)

        # Write to CSV
        self.stdout.write(f'Writing report to {output_path}...')
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['name', 'frequency', 'percentage'])
            writer.writeheader()
            writer.writerows(frequency_data)

        # Display summary statistics
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully generated frequency report!'))
        self.stdout.write(f'\nSummary Statistics:')
        self.stdout.write(f'  Total curated ingredients analyzed: {total_curated}')
        self.stdout.write(f'  Total recipes searched: {total_recipes}')
        self.stdout.write(f'  Ingredients with 0 matches: {ingredients_with_zero_matches} ({round(ingredients_with_zero_matches/total_curated*100, 1)}%)')
        self.stdout.write(f'  Ingredients with 1+ matches: {total_curated - ingredients_with_zero_matches} ({round((total_curated - ingredients_with_zero_matches)/total_curated*100, 1)}%)')

        if frequency_data:
            self.stdout.write(f'\nTop 10 Most Common Ingredients:')
            for i, item in enumerate(frequency_data[:10], 1):
                self.stdout.write(f"  {i}. {item['name']}: {item['frequency']} recipes ({item['percentage']}%)")

        self.stdout.write(f'\nReport saved to: {output_path}')
