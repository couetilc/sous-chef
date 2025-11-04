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
