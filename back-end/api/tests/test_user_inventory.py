import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Ingredient, UserInventory


@pytest.mark.django_db
class TestUserInventoryAPI:
    def test_create_user_inventory(self, authenticated_client):
        # set the pre-conditions: put the database into a state we want to test
        ingredient = Ingredient.objects.create(name='Tomato')

        response = authenticated_client.post('/api/user_inventory/', { 'ingredient_id': ingredient.id})

        assert response.status_code == status.HTTP_201_CREATED
        assert UserInventory.objects.count() == 1
    
    def test_get_user_inventory(self, authenticated_client, test_user):
        ingredient1 = Ingredient.objects.create(name='Tomato')
        ingredient2 = Ingredient.objects.create(name='Lettuce')
        UserInventory.objects.create(user=test_user, ingredient=ingredient1)
        UserInventory.objects.create(user=test_user, ingredient=ingredient2)

        response = authenticated_client.get('/api/user_inventory/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['ingredient']['name'] == 'Lettuce'
        assert response.data[1]['ingredient']['name'] == 'Tomato'

    def test_delete_user_inventory(self, authenticated_client, test_user):
        ingredient = Ingredient.objects.create(name='Tomato')
        user_inventory = UserInventory.objects.create(user=test_user, ingredient=ingredient)

        response = authenticated_client.delete(f'/api/user_inventory/{user_inventory.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert UserInventory.objects.filter(id=user_inventory.id).count() == 0
    