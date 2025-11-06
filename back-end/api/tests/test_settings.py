import pytest
from rest_framework import status
from api.models import Ingredient, DietaryIngredient, User

@pytest.mark.django_db
class TestSettingsAPI:
    def test_get_settings_restricted_ingredients_returns_ingredients(self, authenticated_client):
        Ingredient.objects.create(name="foo")
        Ingredient.objects.create(name="bar")

        response = authenticated_client.get('/api/settings/restricted_ingredients/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_get_settings_restricted_ingredients_always_returns_restricted_ingredients(self, authenticated_client, test_user):
        for i in range(100):
            Ingredient.objects.create(name=f"foo{i}")
        zoo = Ingredient.objects.create(name="zoo")
        DietaryIngredient.objects.create(ingredient=zoo,user=test_user)

        response = authenticated_client.get('/api/settings/restricted_ingredients/?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 101
        assert len(response.data['results']) == 100
        assert response.data['results'][0]['name'] == 'zoo'
        assert response.data['results'][99]['name'] == 'foo98'
        assert response.data['results'][0]['is_restricted'] == True
        assert response.data['results'][99]['name'] == False

    def test_get_settings_restricted_ingredients_must_only_return_users_restricted_ingredients(self, authenticated_client, test_user):
        Ingredient.objects.create(name=f"foo")
        zoo = Ingredient.objects.create(name="zoo")
        new_user = User.objects.create()
        DietaryIngredient.objects.create(
            ingredient=zoo,
            user=new_user
        )

        response = authenticated_client.get('/api/settings/restricted_ingredients/?page=1')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['name'] == 'foo'
        assert response.data['results'][1]['name'] == 'zoo'
        assert response.data['results'][0]['is_restricted'] == False
        assert response.data['results'][1]['is_restricted'] == False

    def test_get_settings_restricted_ingredients_search(self, authenticated_client, test_user):
        Ingredient.objects.create(name=f"foo")
        Ingredient.objects.create(name=f"bar")
        response = authenticated_client.get('/api/settings/restricted_ingredients/?page=1&search=foo')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'foo'
        assert response.data['results'][0]['is_restricted'] == False

    def test_get_settings_restricted_ingredients_search_with_restricted_ingredients(self, authenticated_client, test_user):
        Ingredient.objects.create(name=f"foo")
        Ingredient.objects.create(name=f"bar")
        zoo = Ingredient.objects.create(name="zoo")
        DietaryIngredient.objects.create(
            ingredient=zoo,
            user=test_user
        )

        response = authenticated_client.get('/api/settings/restricted_ingredients/?page=1&search=bar')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2
        assert response.data['results'][0]['name'] == 'zoo'
        assert response.data['results'][1]['name'] == 'bar'
        assert response.data['results'][0]['is_restricted'] == True
        assert response.data['results'][1]['is_restricted'] == False

    def test_post_settings_restricted_ingredients(self, authenticated_client):
        response = authenticated_client.post('/api/settings/restricted_ingredients/')

        assert response.status_code == status.HTTP_200_OK
