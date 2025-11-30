from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Diet, CuratedIngredient, DietRestrictedCuratedIngredient

diet_names = ["Vegetarian", "Vegan", "Gluten-Free", "Kosher", "Halal"]

class Command(BaseCommand):
    help = 'Load diets-ingredient relations into Postgres Database'

    def handle(self, *args, **options):

         # Load into database
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            diet_vegetarian = Diet.objects.get(name="Vegetarian")
            vegetarian_restricted_names = ["pork", "beef", "chicken", "lamb", "turkey", "lard", "tallow", "bacon", "steak", "chorizo", "sausage", "meat", "salmon", "tilapia", "herring", "trout", "sardine",
            "fish", "mussel", "clam", "oyster", "shrimp", "crab", "lobster", "scallop", "duck"]
            for name in vegetarian_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.save(DietRestrictedCuratedIngredient(
                        diet=diet_vegetarian
                        ingredient=ingredient
                    ))

            diet_vegan= Diet.objects.get(name="Vegan")
            vegan_restricted_names = vegetarian_restricted_names.copy() + ["egg", "milk", "cheese"]
            for name in vegan_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.save(DietRestrictedCuratedIngredient(
                        diet=diet_vegan
                        ingredient=ingredient
                    ))

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded diets:\n'
                f'  - Created: {created_count}\n'
                f'  - Skipped (already exists): {skipped_count}\n'
                f'  - Total in database: {Diet.objects.count()}'
            )
        )

