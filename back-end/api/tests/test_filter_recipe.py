"""
Tests for Filtering Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe, Ingredient, RecipeIngredient, UserInventory

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

        favoriteFries = FavoriteRecipe.objects.create(user=test_user, recipe=fries)

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
