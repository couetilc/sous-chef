from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from api.models import Recipe, Ingredient, RecipeIngredient

class Command(BaseCommand):
    help = 'Load demo recipes and ingredients with bindings into Postgres Database'

    def handle(self, *args, **options):

        with transaction.atomic():

            # Ingredients for Recipe 1
            asparagus = Ingredient.objects.get_or_create(name="Asparagus")[0]
            blackpepper = Ingredient.objects.get_or_create(name="Black Pepper")[0]

            # Ingredients for Recipe 2

            # Create Recipe Objects
            recipe1 = Recipe.objects.filter(title="Couscous with Asparagus and Bleu Cheese").first()
            if (recipe1 != None): recipe1.delete()
            recipe1 = Recipe.objects.create(
                title="Couscous with Asparagus and Bleu Cheese",
                ingredients="2.75 cups water, divided | 2 cups uncooked couscous | 0.5 cup raisins | 1.5 tablespoons olive oil | 1.5 cups fresh asparagus tips and pieces | 0.5 cup thinly sliced green onions | 0.33333334326744 cup shredded carrots | 2 tablespoons white wine vinegar | 1 tablespoon white sugar | 1.5 teaspoons curry powder | 1 teaspoon minced fresh ginger root | 0.75 teaspoon salt | 3 ounces crumbled blue cheese | 0.25 cup sunflower kernels",
                instructions="Bring 1 3/4 cups water to a boil in a saucepan. Slowly pour couscous and raisins into the boiling water while stirring. Place a cover on the saucepan, reduce heat to low, and simmer until the couscous absorbs most of the water, 8 to 10 minutes. | Remove saucepan from heat and set aside until couscous absorbs remaining water, about 5 minutes more. Fluff couscous with a fork. | Heat olive oil in a skillet over medium-high heat. Saute asparagus, green onions, and carrots in hot oil until tender-crisp, about 5 minutes. | Mix vinegar, sugar, curry powder, ginger, and salt together in a large bowl until the sugar is completely dissolved into the vinegar; add the couscous mixture, asparagus mixture, blue cheese, and sunflower kernels. Gently fold the mixture until the kernels are evenly distributed through the mixture.",
                image_url="https://www.allrecipes.com/thmb/WTqIhqa-MjYX87feDWWPQ4bMivI=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/1114778-7411281f82274014a699866947e3fa9d.jpg",
                source_url="https://www.allrecipes.com/recipe/236802/curried-couscous-with-asparagus-and-bleu-cheese",
                servings=6,
                calories_per_serving=395,
                fat_g=11,
                carbs_g=62,
                protein_g=13,
                prep_time_min=20,
                cook_time_min=15,
                total_time_min=40,
                price_per_serving_usd=1.21,
                total_price_usd=7.29,
            )

            recipe2 = Recipe.objects.filter(title="Roasted Chorizo with Potatoes and Asparagus for Two").first()
            if (recipe2 != None): recipe2.delete()
            recipe2 = Recipe.objects.create(
                title="Roasted Chorizo with Potatoes and Asparagus for Two",
                ingredients="0.5 pound baby red potatoes, halved | 1 cup baby carrots | 3 tablespoons olive oil, divided | 0.5 teaspoon salt | 0.25 teaspoon ground black pepper | 0.25 teaspoon garlic powder | 0.25 teaspoon smoked paprika | 2 links chorizo sausage | 1 red onion, quartered | 0.25 bunch fresh asparagus, trimmed",
                instructions="Preheat the oven to 400 degrees F (200 degrees C). | Place potatoes and carrots on a baking sheet. Season with 2 tablespoons olive oil, salt, black pepper, garlic powder, and smoked paprika; toss until well coated. Place chorizo sausages on top. | Bake in the preheated oven until sausages are golden, about 15 minutes. | Remove sausages and slice in rounds. Add red onion and asparagus; place sausage slices on the sheet pan. Drizzle with remaining olive oil; toss to coat. | Bake in the preheated oven until vegetables are golden and roasted, about 15 minutes more.",
                image_url="https://www.allrecipes.com/thmb/XMhd2evzH0UslrtTG8KOFTaG_Xs=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/6843513-fe5dab2298ba49578965a955c5dfe355.jpg",
                source_url="https://www.allrecipes.com/recipe/262459/sheet-pan-chorizo-with-potatoes-and-asparagus-for-two",
                servings=2,
                fat_g=44,
                carbs_g=34,
                protein_g=19,
                prep_time_min=15,
                cook_time_min=30,
                total_time_min=45,
                price_per_serving_usd=0.46,
                total_price_usd=0.92,
            )

            recipe3 = Recipe.objects.filter(title="Stuffed Chicken Breasts with Asparagus and Parmesan Rice").first()
            if (recipe3 != None): recipe3.delete()
            recipe3 = Recipe.objects.create(
                title="Stuffed Chicken Breasts with Asparagus and Parmesan Rice",
                ingredients="4 skinless, boneless chicken breast halves | 1 tablespoon extra-virgin olive oil, or more as needed | 1 cup chopped fresh asparagus | 0.25 teaspoon garlic powder, or to taste | salt and ground black pepper to taste | 4 slices deli ham | 0.5 cup shredded Cheddar cheese | 2 tablespoons butter, divided | 2 cups chicken broth | 1 tablespoon butter | 1 cup uncooked white rice | 1 (14.5 ounce) can diced tomatoes with onion and celery, drained | 0.33333334326744 cup grated Parmesan cheese, or to taste",
                instructions="Preheat oven to 350 degrees F (175 degrees C). | Place the chicken breasts between two sheets of heavy plastic (resealable freezer bags work well) on a solid, level surface. Firmly pound the chicken with the smooth side of a meat mallet to a thickness of 1/4 inch. | Heat the olive oil in a skillet over medium heat, and cook and stir the asparagus, garlic powder, salt, and black pepper just until the asparagus is bright green and beginning to become tender, about 5 minutes. Remove from heat. | Lay each chic…fed breast should read 160 degrees F (70 degrees C). Baste the stuffed chicken breasts occasionally with pan juices while baking. | While chicken is baking, bring chicken broth and 1 tablespoon of butter to a boil in a saucepan. Stir in rice and tomatoes, reduce heat to a simmer, cover, and cook the rice until tender and the broth has been absorbed, about 20 minutes. Remove from heat, and let rice stand covered for about 5 minutes; stir in Parmesan cheese. Serve stuffed chicken breasts on the cooked rice.",
                image_url="https://www.allrecipes.com/thmb/CKTE3dd46p2almq3T5aB7NFjZzs=/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/image-499-3036919b62aa4528850ab49a028e29dc.jpg",
                source_url="https://www.allrecipes.com/recipe/217094/stuffed-chicken-breasts-with-asparagus-and-parmesan-rice",
                servings=4,
                calories_per_serving=573,
                fat_g=24,
                carbs_g=44,
                protein_g=41,
                prep_time_min=20,
                cook_time_min=40,
                total_time_min=60,
                price_per_serving_usd=2.94,
                total_price_usd=11.74,
            )

            # Create recipe/ingredient bindings (<ingredient>RI<recipeindex>)
            asparagusRI1 = RecipeIngredient.objects.get_or_create(recipe=recipe1, ingredient=asparagus)
            asparagusRI2 = RecipeIngredient.objects.get_or_create(recipe=recipe2, ingredient=asparagus)
            asparagusRI3 = RecipeIngredient.objects.get_or_create(recipe=recipe3, ingredient=asparagus)
            blackpepperRI2 = RecipeIngredient.objects.get_or_create(recipe=recipe2, ingredient=blackpepper)
            blackpepperRI3 = RecipeIngredient.objects.get_or_create(recipe=recipe3, ingredient=blackpepper)

        # Report results
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded demo objects:\n'
            )
        )

