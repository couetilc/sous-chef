import pytest
from rest_framework import status
from api.models import UserRecipe, Recipe
from api.serializers import RecipeSerializer

@pytest.mark.django_db
class TestUserRecipeAPI:
     
    def test_get_user_recipe(self, test_user, authenticated_client):
        UserRecipe.objects.create(original_recipe=Recipe.objects.create(), user=test_user)
        response = authenticated_client.get('/api/user_recipe/')

        assert response.status_code == status.HTTP_200_OK

    def test_get_user_recipes(self, test_user, authenticated_client):
        UserRecipe.objects.create(original_recipe=Recipe.objects.create(), user=test_user)
        UserRecipe.objects.create(original_recipe=Recipe.objects.create(), user=test_user)
        response = authenticated_client.get('/api/user_recipe/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_set_user_recipe(self, test_user, authenticated_client):
        originalRecipe = Recipe.objects.create()
        userRecipe = UserRecipe.objects.create(original_recipe=originalRecipe, user=test_user)
        print("userRecipe: ", userRecipe.id)
        
        testDict = {
            'ingredients': 'carrrots',
            'instructions': 'cook',
            'original_recipe': originalRecipe.id
        }


        response = authenticated_client.post(f'/api/user_recipe_update/{userRecipe.id}/',
            testDict) 

        assert response.status_code == status.HTTP_200_OK
        ingredients.refresh_from_db()
        instructions.refresh_from_db()

