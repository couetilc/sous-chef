"""
Tests for Filtering Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe, Ingredient, RecipeIngredient, UserInventory, CuratedIngredient, RecipeCuratedIngredient, UserCuratedInventory, UserRecipe

@pytest.mark.django_db
class TestFilterRecipes:
    def test_filter_name(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')

        favoriteFries = FavoriteRecipe.objects.create(user=test_user, recipe=fries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "title" : "Fri",
            "searchFavorite": False
        })

        assert len(response.data['results']) == 3

    def test_filter_name_nomatch(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')

        favoriteFries = FavoriteRecipe.objects.create(user=test_user, recipe=fries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "title" : "neon",
            "searchFavorite": False
        })

        assert len(response.data['results']) == 0

    def test_filter_name_none(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')

        favoriteFries = FavoriteRecipe.objects.create(user=test_user, recipe=fries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : ""
        })

        assert len(response.data['results']) == 4

    def test_filter_recipeingredient(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "ingredients" : [potatoes.id],
        })

        assert len(response.data['results']) == 2

    def test_filter_recipeingredient_multiple(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "ingredients" : [salt.id, potatoes.id],
        })

        assert len(response.data['results']) == 1


    def test_filter_recipeingredient_multiple_nomatch(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        potatoesFriesRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        potatoesChipsRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        saltFriesRI = RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        sPotatoesRI = RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "ingredients" : [salt.id, sPotatoes.id],
        })

        assert len(response.data['results']) == 0

    def test_filter_userinventory(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        UserInventory.objects.create(ingredient=potatoes, user=test_user)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "searchInventory": True,
        })

        assert(len(response.data['results'])) == 2

    def test_filter_userinventory_multiple(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        potatoesFriesRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        potatoesChipsRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        saltFriesRI = RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        sPotatoesRI = RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        potatoesInventoryIngredient = UserInventory.objects.create(ingredient=potatoes, user=test_user)
        sPotatoesInventoryIngredient = UserInventory.objects.create(ingredient=sPotatoes, user=test_user)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "searchInventory": True,
        })

        assert(len(response.data['results'])) == 3

    def test_filter_userinventory_nomatch(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        potatoesFriesRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        potatoesChipsRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        saltFriesRI = RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        sPotatoesRI = RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        yams = Ingredient.objects.create(name='Yams')
        yamsInventoryIngredient = UserInventory.objects.create(ingredient=yams, user=test_user)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "searchInventory": True,
        })

        assert(len(response.data['results'])) == 0

    def test_filter_userinventory_empty(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        potatoesFriesRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        chips = Recipe.objects.create(title='Chips')
        potatoesChipsRI = RecipeIngredient.objects.create(ingredient=potatoes, recipe=chips)

        salt = Ingredient.objects.create(name='Salt')
        saltFriesRI = RecipeIngredient.objects.create(ingredient=salt, recipe=fries)

        sFries = Recipe.objects.create(title='Sweet Potato Fries')
        sPotatoes = Ingredient.objects.create(name='Sweet Potatoes')
        sPotatoesRI = RecipeIngredient.objects.create(ingredient=sPotatoes, recipe=sFries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": False,
            "title" : "",
            "searchInventory": True,
        })

        assert(len(response.data['results'])) == 0



    def test_filter_favorite(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')

        FavoriteRecipe.objects.create(user=test_user, recipe=fries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": True,
            "title" : ""
        })

        assert len(response.data['results']) == 1

    def test_filter_favorite_nomatch(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')


        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchFavorite": True,
            "title" : ""
        })

        assert len(response.data['results']) == 0

    def test_filter_my_recipes(self, authenticated_client, test_user):
        """Test filtering by user's AI-created recipes"""
        # Create a public recipe (not created by user)
        public_recipe = Recipe.objects.create(title='Public Recipe', is_private=False)

        # Create a private recipe linked to the test user (AI-created)
        my_recipe = Recipe.objects.create(title='My AI Recipe', is_private=True)
        UserRecipe.objects.create(user=test_user, original_recipe=my_recipe, ingredients='test', instructions='test')

        # Create another private recipe not linked to user
        other_private = Recipe.objects.create(title='Other Private', is_private=True)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchMyRecipes": True
        })

        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'My AI Recipe'

    def test_filter_my_recipes_multiple(self, authenticated_client, test_user):
        """Test filtering returns multiple AI-created recipes"""
        my_recipe1 = Recipe.objects.create(title='My Recipe 1', is_private=True)
        UserRecipe.objects.create(user=test_user, original_recipe=my_recipe1, ingredients='test', instructions='test')

        my_recipe2 = Recipe.objects.create(title='My Recipe 2', is_private=True)
        UserRecipe.objects.create(user=test_user, original_recipe=my_recipe2, ingredients='test', instructions='test')

        public_recipe = Recipe.objects.create(title='Public Recipe', is_private=False)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchMyRecipes": True
        })

        assert len(response.data['results']) == 2
        titles = [r['title'] for r in response.data['results']]
        assert 'My Recipe 1' in titles
        assert 'My Recipe 2' in titles

    def test_filter_my_recipes_empty(self, authenticated_client, test_user):
        """Test filtering returns empty when user has no AI-created recipes"""
        public_recipe = Recipe.objects.create(title='Public Recipe', is_private=False)
        other_private = Recipe.objects.create(title='Other Private', is_private=True)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchMyRecipes": True
        })

        assert len(response.data['results']) == 0

    def test_filter_my_recipes_user_isolation(self, authenticated_client, test_user):
        """Test that my recipes filter only returns current user's recipes"""
        # Create another user with their own recipe
        other_user = User.objects.create_user(username='other', password='pass')
        other_recipe = Recipe.objects.create(title='Other User Recipe', is_private=True)
        UserRecipe.objects.create(user=other_user, original_recipe=other_recipe, ingredients='test', instructions='test')

        # Create test user's recipe
        my_recipe = Recipe.objects.create(title='My Recipe', is_private=True)
        UserRecipe.objects.create(user=test_user, original_recipe=my_recipe, ingredients='test', instructions='test')

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchMyRecipes": True
        })

        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'My Recipe'

    def test_filter_no_filters(self, authenticated_client, test_user):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        bfries = Recipe.objects.create(title='Bfries')
        chips = Recipe.objects.create(title='Chips')

        response = authenticated_client.post('/api/recipes/searchFiltered/')

        assert len(response.data['results']) == 4

    def test_filter_pagination(self, authenticated_client):
        for i in range(200):
            Recipe.objects.create(title=str(i))

        res = authenticated_client.post('/api/recipes/searchFiltered/?page=1')

        assert res.data['count'] == 200
        assert len(res.data['results']) == 100

    # Tests for NEW curated ingredient filtering
    def test_filter_curated_ingredient_single(self, authenticated_client, test_user):
        """Test filtering recipes by a single curated ingredient"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        grilled_chicken = Recipe.objects.create(title='Grilled Chicken')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=grilled_chicken, curated_ingredient=chicken)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id]
        })

        assert len(response.data['results']) == 2
        titles = [r['title'] for r in response.data['results']]
        assert 'Chicken Rice' in titles
        assert 'Grilled Chicken' in titles

    def test_filter_curated_ingredient_multiple(self, authenticated_client, test_user):
        """Test filtering recipes by multiple curated ingredients (AND logic)"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        salt = CuratedIngredient.objects.create(name='salt', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        grilled_chicken = Recipe.objects.create(title='Grilled Chicken')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=salt)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=grilled_chicken, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=grilled_chicken, curated_ingredient=salt)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id, rice.id]
        })

        # Only Chicken Rice has both chicken AND rice
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Chicken Rice'

    def test_filter_curated_ingredient_multiple_nomatch(self, authenticated_client, test_user):
        """Test filtering with curated ingredients that no recipe has together"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        tomato = CuratedIngredient.objects.create(name='tomato', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        tomato_soup = Recipe.objects.create(title='Tomato Soup')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=tomato_soup, curated_ingredient=tomato)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id, tomato.id]
        })

        # No recipe has both chicken AND tomato
        assert len(response.data['results']) == 0

    def test_filter_curated_ingredient_or_logic(self, authenticated_client, test_user):
        """Test filtering with OR logic - recipes with ANY selected ingredient"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        tomato = CuratedIngredient.objects.create(name='tomato', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        tomato_soup = Recipe.objects.create(title='Tomato Soup')
        pasta = Recipe.objects.create(title='Pasta')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=tomato_soup, curated_ingredient=tomato)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id, tomato.id],
            "curated_ingredients_match_all": False
        })

        # Should get Chicken Rice (has chicken) and Tomato Soup (has tomato)
        assert len(response.data['results']) == 2
        titles = [r['title'] for r in response.data['results']]
        assert 'Chicken Rice' in titles
        assert 'Tomato Soup' in titles

    def test_filter_curated_ingredient_or_logic_multiple_matches(self, authenticated_client, test_user):
        """Test OR logic with recipe that has multiple selected ingredients"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        tomato = CuratedIngredient.objects.create(name='tomato', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        pasta = Recipe.objects.create(title='Pasta')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id, rice.id],
            "curated_ingredients_match_all": False
        })

        # Should get both Chicken Rice (has both) and Fried Rice (has rice)
        # Note: distinct() prevents duplicates, so Chicken Rice appears once
        assert len(response.data['results']) == 2
        titles = [r['title'] for r in response.data['results']]
        assert 'Chicken Rice' in titles
        assert 'Fried Rice' in titles

    def test_filter_curated_ingredient_and_logic_explicit(self, authenticated_client, test_user):
        """Test that AND logic still works when explicitly set to True"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "curated_ingredients": [chicken.id, rice.id],
            "curated_ingredients_match_all": True
        })

        # Only Chicken Rice has both
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Chicken Rice'

    def test_filter_curated_inventory(self, authenticated_client, test_user):
        """Test filtering recipes by user's curated inventory"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        tomato = CuratedIngredient.objects.create(name='tomato', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        tomato_soup = Recipe.objects.create(title='Tomato Soup')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=tomato_soup, curated_ingredient=tomato)

        # User has chicken in inventory
        UserCuratedInventory.objects.create(user=test_user, curated_ingredient=chicken)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchCuratedInventory": True
        })

        # Should return only recipes with chicken
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Chicken Rice'

    def test_filter_curated_inventory_multiple(self, authenticated_client, test_user):
        """Test filtering with multiple items in curated inventory"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True)
        tomato = CuratedIngredient.objects.create(name='tomato', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        fried_rice = Recipe.objects.create(title='Fried Rice')
        tomato_soup = Recipe.objects.create(title='Tomato Soup')

        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=fried_rice, curated_ingredient=rice)
        RecipeCuratedIngredient.objects.create(recipe=tomato_soup, curated_ingredient=tomato)

        # User has chicken and rice in inventory
        UserCuratedInventory.objects.create(user=test_user, curated_ingredient=chicken)
        UserCuratedInventory.objects.create(user=test_user, curated_ingredient=rice)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchCuratedInventory": True
        })

        # Should return recipes with chicken OR rice
        assert len(response.data['results']) == 2
        titles = [r['title'] for r in response.data['results']]
        assert 'Chicken Rice' in titles
        assert 'Fried Rice' in titles

    def test_filter_curated_inventory_empty(self, authenticated_client, test_user):
        """Test filtering with empty curated inventory returns no results"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True)

        chicken_rice = Recipe.objects.create(title='Chicken Rice')
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)

        # User has no inventory
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchCuratedInventory": True
        })

        assert len(response.data['results']) == 0

    # Tests for backward compatibility with OLD ingredient filtering
    def test_old_ingredient_filter_still_works(self, authenticated_client, test_user):
        """Test that old ingredient filtering parameters still work"""
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        fries = Recipe.objects.create(title='Fries')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "ingredients": [potatoes.id]
        })

        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Fries'

    def test_old_inventory_filter_still_works(self, authenticated_client, test_user):
        """Test that old inventory filtering still works"""
        potatoes = Ingredient.objects.create(name='Russet Potatoes')
        fries = Recipe.objects.create(title='Fries')
        RecipeIngredient.objects.create(ingredient=potatoes, recipe=fries)

        UserInventory.objects.create(ingredient=potatoes, user=test_user)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "searchInventory": True
        })

        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Fries'

    # Tests for new score fields in serializer
    def test_serializer_includes_accessibility_score(self, authenticated_client, test_user):
        """Test that the serializer includes accessibility_score field"""
        chicken = CuratedIngredient.objects.create(name='chicken breast', is_approved=True, frequency=100)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True, frequency=80)

        chicken_rice = Recipe.objects.create(title='Chicken Rice', deliciousness_score=85)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)

        response = authenticated_client.post('/api/recipes/searchFiltered/')

        assert len(response.data['results']) == 1
        recipe = response.data['results'][0]
        assert 'accessibility_score' in recipe
        assert recipe['accessibility_score'] is not None

    def test_serializer_includes_deliciousness_notes(self, authenticated_client, test_user):
        """Test that the serializer includes deliciousness_notes field"""
        recipe = Recipe.objects.create(
            title='Test Recipe',
            deliciousness_score=90,
            deliciousness_notes='Rich flavors with perfect seasoning'
        )

        response = authenticated_client.post('/api/recipes/searchFiltered/')

        assert len(response.data['results']) == 1
        recipe_data = response.data['results'][0]
        assert 'deliciousness_notes' in recipe_data
        assert recipe_data['deliciousness_notes'] == 'Rich flavors with perfect seasoning'

    def test_serializer_includes_deliciousness_score(self, authenticated_client, test_user):
        """Test that the serializer includes deliciousness_score field"""
        recipe = Recipe.objects.create(title='Test Recipe', deliciousness_score=75.5)

        response = authenticated_client.post('/api/recipes/searchFiltered/')

        assert len(response.data['results']) == 1
        recipe_data = response.data['results'][0]
        assert 'deliciousness_score' in recipe_data
        assert float(recipe_data['deliciousness_score']) == 75.5

    # Tests for sort_by parameter
    def test_sort_by_accessibility_default(self, authenticated_client, test_user):
        """Test that default sorting is by accessibility (most accessible first)"""
        # Create curated ingredients with different frequencies
        common = CuratedIngredient.objects.create(name='salt', is_approved=True, frequency=100)
        rare = CuratedIngredient.objects.create(name='truffle', is_approved=True, frequency=10)

        # Recipe with common ingredients should rank higher
        easy_recipe = Recipe.objects.create(title='Easy Recipe', deliciousness_score=50)
        RecipeCuratedIngredient.objects.create(recipe=easy_recipe, curated_ingredient=common)

        # Recipe with rare ingredients should rank lower
        hard_recipe = Recipe.objects.create(title='Hard Recipe', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=hard_recipe, curated_ingredient=rare)

        response = authenticated_client.post('/api/recipes/searchFiltered/')

        assert len(response.data['results']) == 2
        # Easy recipe should come first (higher accessibility)
        assert response.data['results'][0]['title'] == 'Easy Recipe'
        assert response.data['results'][1]['title'] == 'Hard Recipe'

    def test_sort_by_accessibility_explicit(self, authenticated_client, test_user):
        """Test explicit sort_by=accessibility parameter"""
        common = CuratedIngredient.objects.create(name='salt', is_approved=True, frequency=100)
        rare = CuratedIngredient.objects.create(name='truffle', is_approved=True, frequency=10)

        easy_recipe = Recipe.objects.create(title='Easy Recipe', deliciousness_score=50)
        RecipeCuratedIngredient.objects.create(recipe=easy_recipe, curated_ingredient=common)

        hard_recipe = Recipe.objects.create(title='Hard Recipe', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=hard_recipe, curated_ingredient=rare)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            'sort_by': 'accessibility'
        })

        assert len(response.data['results']) == 2
        assert response.data['results'][0]['title'] == 'Easy Recipe'
        assert response.data['results'][1]['title'] == 'Hard Recipe'

    def test_sort_by_deliciousness(self, authenticated_client, test_user):
        """Test sort_by=deliciousness parameter (highest deliciousness first)"""
        common = CuratedIngredient.objects.create(name='salt', is_approved=True, frequency=100)

        mediocre_recipe = Recipe.objects.create(title='Mediocre Recipe', deliciousness_score=50)
        RecipeCuratedIngredient.objects.create(recipe=mediocre_recipe, curated_ingredient=common)

        delicious_recipe = Recipe.objects.create(title='Delicious Recipe', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=delicious_recipe, curated_ingredient=common)

        tasty_recipe = Recipe.objects.create(title='Tasty Recipe', deliciousness_score=75)
        RecipeCuratedIngredient.objects.create(recipe=tasty_recipe, curated_ingredient=common)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            'sort_by': 'deliciousness'
        })

        assert len(response.data['results']) == 3
        # Should be ordered by deliciousness score (highest first)
        assert response.data['results'][0]['title'] == 'Delicious Recipe'
        assert response.data['results'][1]['title'] == 'Tasty Recipe'
        assert response.data['results'][2]['title'] == 'Mediocre Recipe'

    def test_sort_by_combined(self, authenticated_client, test_user):
        """Test sort_by=combined parameter (accessibility * deliciousness)"""
        common = CuratedIngredient.objects.create(name='salt', is_approved=True, frequency=100)
        rare = CuratedIngredient.objects.create(name='truffle', is_approved=True, frequency=10)

        # High accessibility, low deliciousness: 90 * 40 = 3600
        easy_bland = Recipe.objects.create(title='Easy Bland', deliciousness_score=40)
        RecipeCuratedIngredient.objects.create(recipe=easy_bland, curated_ingredient=common)

        # Low accessibility, high deliciousness: 15 * 95 = 1425
        hard_delicious = Recipe.objects.create(title='Hard Delicious', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=hard_delicious, curated_ingredient=rare)

        # High accessibility, high deliciousness: 90 * 85 = 7650 (best combined)
        easy_delicious = Recipe.objects.create(title='Easy Delicious', deliciousness_score=85)
        RecipeCuratedIngredient.objects.create(recipe=easy_delicious, curated_ingredient=common)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            'sort_by': 'combined'
        })

        assert len(response.data['results']) == 3
        # Easy Delicious should be first (highest combined score)
        assert response.data['results'][0]['title'] == 'Easy Delicious'
        # Easy Bland should be second
        assert response.data['results'][1]['title'] == 'Easy Bland'
        # Hard Delicious should be last (lowest combined)
        assert response.data['results'][2]['title'] == 'Hard Delicious'

    def test_sort_by_combined_with_filters(self, authenticated_client, test_user):
        """Test that combined sorting works with other filters"""
        chicken = CuratedIngredient.objects.create(name='chicken', is_approved=True, frequency=90)
        rice = CuratedIngredient.objects.create(name='rice', is_approved=True, frequency=95)
        truffle = CuratedIngredient.objects.create(name='truffle', is_approved=True, frequency=10)

        # These should match filter
        chicken_rice = Recipe.objects.create(title='Chicken Rice', deliciousness_score=80)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=chicken)
        RecipeCuratedIngredient.objects.create(recipe=chicken_rice, curated_ingredient=rice)

        grilled_chicken = Recipe.objects.create(title='Grilled Chicken', deliciousness_score=70)
        RecipeCuratedIngredient.objects.create(recipe=grilled_chicken, curated_ingredient=chicken)

        # This should not match filter (no chicken)
        truffle_pasta = Recipe.objects.create(title='Truffle Pasta', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=truffle_pasta, curated_ingredient=truffle)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            'curated_ingredients': [chicken.id],
            'sort_by': 'combined'
        })

        assert len(response.data['results']) == 2
        # Both should have chicken, ordered by combined score
        titles = [r['title'] for r in response.data['results']]
        assert 'Chicken Rice' in titles
        assert 'Grilled Chicken' in titles
        assert 'Truffle Pasta' not in titles

    def test_sort_by_invalid_parameter(self, authenticated_client, test_user):
        """Test that invalid sort_by parameter defaults to accessibility"""
        common = CuratedIngredient.objects.create(name='salt', is_approved=True, frequency=100)
        rare = CuratedIngredient.objects.create(name='truffle', is_approved=True, frequency=10)

        easy_recipe = Recipe.objects.create(title='Easy Recipe', deliciousness_score=50)
        RecipeCuratedIngredient.objects.create(recipe=easy_recipe, curated_ingredient=common)

        hard_recipe = Recipe.objects.create(title='Hard Recipe', deliciousness_score=95)
        RecipeCuratedIngredient.objects.create(recipe=hard_recipe, curated_ingredient=rare)

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            'sort_by': 'invalid_sort_option'
        })

        # Should default to accessibility sorting
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['title'] == 'Easy Recipe'

@pytest.mark.django_db
class TestRecipeDetailAPI:
    def test_get_recipe(self, authenticated_client):
        foo = Recipe.objects.create(title="foo")

        response = authenticated_client.get(f'/api/recipes/{foo.id}/')

        assert 'id' in response.data
        assert response.data['id'] == foo.id
