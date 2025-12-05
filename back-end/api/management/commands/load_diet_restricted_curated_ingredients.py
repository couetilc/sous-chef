from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Diet, CuratedIngredient, DietRestrictedCuratedIngredient, RecipeCuratedIngredient, Recipe

diet_names = ["Vegetarian", "Vegan", "Gluten-Free", "Kosher", "Halal"]

class Command(BaseCommand):
    help = 'Load diets-ingredient relations into Postgres Database'

    def handle(self, *args, **options):

         # Load into database
        with transaction.atomic():
            DietRestrictedCuratedIngredient.objects.all().delete()

            diet_vegetarian = Diet.objects.get(name="Vegetarian")
            vegetarian_restricted_names = ["pork", "beef", "chicken", "lamb", "turkey", "gelatin", "lard", "tallow", "ham" "bacon", "steak", "chorizo", "sausage", "meat", "salmon", "tilapia", "herring", "trout", "sardine",
            "fish", "tuna", "mussel", "clam", "oyster", "shrimp", "crab", "lobster", "scallop", "duck", "squid", "octopus"]
            for name in vegetarian_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.objects.get_or_create(
                        diet=diet_vegetarian,
                        ingredient=ingredient
                    )

            diet_vegan= Diet.objects.get(name="Vegan")
            vegan_restricted_names = vegetarian_restricted_names.copy() + ["egg", "milk", "cheese", "butter", "yogurt", "cream", "curd"]
            for name in vegan_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.objects.get_or_create(
                        diet=diet_vegan,
                        ingredient=ingredient
                    )

            diet_glutenfree = Diet.objects.get(name="Gluten-Free") 
            glutenfree_restricted_names = ["wheat", "barley", "rye", "oat", "couscous", "durum", "einkorn", "emmer", "farro", "graham", "kamut", "spelt", "bran", "semolina", "beer",
                                           "bread", "cereal", "crouton", "matzo", "pasta", "cake", "pie", "cookie", "cracker"]
            for name in glutenfree_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.objects.get_or_create(
                        diet=diet_glutenfree,
                        ingredient=ingredient
                    )

            diet_kosher = Diet.objects.get(name="Kosher")
            kosher_restricted_names = ["pork", "bacon", "chorizo", "ham", "sausage", "lard", "mussel", "clam", "gelatin", "oyster", "shrimp", "crab", "lobster", "scallop", "squid", "octopus"]
            for name in kosher_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.objects.get_or_create(
                        diet=diet_kosher,
                        ingredient=ingredient
                    )
            
            diet_halal = Diet.objects.get(name="Halal")
            halal_restricted_names = ["pork", "bacon", "chorizo", "ham", "sausage", "lard", "beer", "wine", "gelatin"]
            for name in halal_restricted_names:
                restricted_ingredients = CuratedIngredient.objects.filter(name__icontains=name)
                for ingredient in restricted_ingredients.all():
                    DietRestrictedCuratedIngredient.objects.get_or_create(
                        diet=diet_halal,
                        ingredient=ingredient
                    )
            
            # Fix Recipe for test
            cabbagerolls = Recipe.objects.get(id=16822)
            groundbeef = CuratedIngredient.objects.get(id=55)
            RecipeCuratedIngredient.objects.get_or_create(
                recipe=cabbagerolls,
                curated_ingredient=groundbeef
            )


        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded relations:\n'
                f'  - Total in database: {DietRestrictedCuratedIngredient.objects.count()}'
            )
        )

