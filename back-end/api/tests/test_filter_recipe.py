"""
Tests for Filtering Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe, Ingredient, RecipeIngredient, UserInventory, CuratedIngredient, RecipeCuratedIngredient, UserCuratedInventory

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

@pytest.mark.django_db
class TestRecipeDetailAPI:
    def test_get_recipe(self, authenticated_client):
        foo = Recipe.objects.create(title="foo")

        response = authenticated_client.get(f'/api/recipes/{foo.id}/')

        assert 'id' in response.data
        assert response.data['id'] == foo.id
