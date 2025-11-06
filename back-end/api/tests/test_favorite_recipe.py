"""
Tests for Favoriting Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe 

@pytest.mark.django_db
class TestFavoriteRecipes:
    def test_create_favorite(self, authenticated_client):
        fries = Recipe.objects.create(title='Fries')
        id = fries.id

        response = authenticated_client.post('/api/recipes/createFavorite/', {
            "recipeID" : id
        })

        print(response.data['message'])
        assert(FavoriteRecipe.objects.count() == 1)

    def test_delete_favorite(self, authenticated_client):
        fries = Recipe.objects.create(title='Fries')
        id = fries.id

        response = authenticated_client.post('/api/recipes/createFavorite/', {
            "recipeID" : id
        })

        print(response.data['message'])
        assert(FavoriteRecipe.objects.count() == 1)

        response = authenticated_client.post('/api/recipes/createFavorite/', {
            "recipeID" : id
        })

        print(response.data['message'])
        assert(FavoriteRecipe.objects.count() == 0)