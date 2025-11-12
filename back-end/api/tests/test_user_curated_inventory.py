import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import CuratedIngredient, UserCuratedInventory


@pytest.mark.django_db
class TestUserCuratedInventoryAPI:
    def test_create_user_curated_inventory_no_list(self, authenticated_client):
        curated_ingredient = CuratedIngredient.objects.create(name='chicken breast')

        response = authenticated_client.post('/api/user_curated_inventory/', {
            'curated_ingredient_ids': curated_ingredient.id
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_create_user_curated_inventory_invalid_id(self, authenticated_client):
        curated_ingredient = CuratedIngredient.objects.create(name='chicken breast')

        response = authenticated_client.post('/api/user_curated_inventory/', {
            'curated_ingredient_ids': [curated_ingredient.id + 1]
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_create_user_curated_inventory(self, authenticated_client):
        # set the pre-conditions: put the database into a state we want to test
        curated_ingredient = CuratedIngredient.objects.create(name='chicken breast')

        response = authenticated_client.post('/api/user_curated_inventory/', {
            'curated_ingredient_ids': [curated_ingredient.id]
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert UserCuratedInventory.objects.count() == 1

    def test_get_user_curated_inventory(self, authenticated_client, test_user):
        curated_ingredient1 = CuratedIngredient.objects.create(name='chicken breast')
        curated_ingredient2 = CuratedIngredient.objects.create(name='olive oil')
        UserCuratedInventory.objects.create(user=test_user, curated_ingredient=curated_ingredient1)
        UserCuratedInventory.objects.create(user=test_user, curated_ingredient=curated_ingredient2)

        response = authenticated_client.get('/api/user_curated_inventory/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['curated_ingredient']['name'] == 'chicken breast'
        assert response.data[1]['curated_ingredient']['name'] == 'olive oil'

    def test_delete_user_curated_inventory(self, authenticated_client, test_user):
        curated_ingredient = CuratedIngredient.objects.create(name='chicken breast')
        user_curated_inventory = UserCuratedInventory.objects.create(user=test_user, curated_ingredient=curated_ingredient)

        response = authenticated_client.delete(f'/api/user_curated_inventory/{user_curated_inventory.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert UserCuratedInventory.objects.filter(id=user_curated_inventory.id).count() == 0
