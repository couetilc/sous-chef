"""
Tests for Filtering Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe 

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
            "searchFavorite": True
        })

        print(response.data)