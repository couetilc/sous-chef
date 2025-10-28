"""
Tests for Filtering Recipes
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, FavoriteRecipe 

@pytest.mark.django_db
class TestFilterRecipes:
    def test_filter_name(self, authenticated_client):
        fries = Recipe.objects.create(title='Fries')
        ofries = Recipe.objects.create(title='Ofries')
        chips = Recipe.objects.create(title='Chips')

        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "title" : "Fri"
        })

        print(response.data)