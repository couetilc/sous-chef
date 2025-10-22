"""
Tests for recipe history API endpoints.
Tests the external-facing API that the front-end will consume.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, CookedRecipe, Meal


@pytest.fixture
def test_recipe(db):
    """Creates a test recipe"""
    return Recipe.objects.create(
        title='Test Recipe',
        ingredients='1 cup flour\n2 eggs',
        instructions='Mix and bake'
    )


@pytest.fixture
def second_user(db):
    """Creates a second test user"""
    return User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='pass123'
    )


@pytest.fixture
def test_cooked_recipe(db, test_user, test_recipe):
    """Creates a cooked recipe for test_user"""
    return CookedRecipe.objects.create(user=test_user, recipe=test_recipe)


@pytest.mark.django_db
class TestRecipeHistoryEndpoint:
    """Test GET /api/recipe_history/"""

    def test_requires_authentication(self, api_client):
        """Unauthenticated requests are rejected"""
        response = api_client.get('/api/recipe_history/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_empty_history(self, authenticated_client):
        """Returns empty list when user has no cooked recipes"""
        response = authenticated_client.get('/api/recipe_history/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_returns_cooked_recipes(self, authenticated_client, test_cooked_recipe):
        """Returns user's cooked recipes"""
        response = authenticated_client.get('/api/recipe_history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        data = response.data[0]
        assert data['id'] == test_cooked_recipe.id
        assert data['recipe']['title'] == 'Test Recipe'
        assert 'cooked_at' in data
        assert 'meals' in data

    def test_includes_meals_in_response(self, authenticated_client, test_cooked_recipe):
        """Cooked recipes include their meals"""
        # Create two meals
        Meal.objects.create(cooked_recipe=test_cooked_recipe, portion=Decimal('0.25'))
        Meal.objects.create(cooked_recipe=test_cooked_recipe, portion=Decimal('0.5'))

        response = authenticated_client.get('/api/recipe_history/')

        assert response.status_code == status.HTTP_200_OK
        meals = response.data[0]['meals']
        assert len(meals) == 2

        # Verify meal structure
        assert 'portion' in meals[0]
        assert 'eaten_at' in meals[0]

    def test_user_isolation(self, api_client, test_user, second_user, test_recipe):
        """Users only see their own cooked recipes"""
        # Create cooked recipes for both users
        user1_cooked = CookedRecipe.objects.create(user=test_user, recipe=test_recipe)
        user2_cooked = CookedRecipe.objects.create(user=second_user, recipe=test_recipe)

        # Check test_user sees only their recipe
        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/recipe_history/')
        assert len(response.data) == 1
        assert response.data[0]['id'] == user1_cooked.id

        # Check second_user sees only their recipe
        api_client.force_authenticate(user=second_user)
        response = api_client.get('/api/recipe_history/')
        assert len(response.data) == 1
        assert response.data[0]['id'] == user2_cooked.id


@pytest.mark.django_db
class TestCreateMealEndpoint:
    """Test POST /api/recipe_history/<cooked_recipe_id>/meal/"""

    def test_requires_authentication(self, api_client, test_cooked_recipe):
        """Unauthenticated requests are rejected"""
        response = api_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.25}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_meal_success(self, authenticated_client, test_cooked_recipe):
        """Successfully creates a meal"""
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.25},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['cooked_recipe'] == test_cooked_recipe.id
        assert response.data['portion'] == '0.2500'
        assert 'eaten_at' in response.data

    def test_portion_required(self, authenticated_client, test_cooked_recipe):
        """Returns error when portion is missing"""
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_invalid_cooked_recipe_id(self, authenticated_client):
        """Returns 404 for non-existent cooked recipe"""
        response = authenticated_client.post(
            '/api/recipe_history/99999/meal/',
            {'portion': 0.25},
            format='json'
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authorization_check(self, api_client, test_user, second_user, test_recipe):
        """Users cannot create meals for other users' cooked recipes"""
        # Create cooked recipe for test_user
        cooked_recipe = CookedRecipe.objects.create(user=test_user, recipe=test_recipe)

        # Try to create meal as second_user
        api_client.force_authenticate(user=second_user)
        response = api_client.post(
            f'/api/recipe_history/{cooked_recipe.id}/meal/',
            {'portion': 0.25},
            format='json'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'permission' in response.data['error'].lower()

    def test_portion_validation_exceeds_remaining(self, authenticated_client, test_cooked_recipe):
        """Returns error when portion exceeds what remains"""
        # Consume 80%
        Meal.objects.create(cooked_recipe=test_cooked_recipe, portion=Decimal('0.8'))

        # Try to consume 30% (would be 110% total)
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.3},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_consume_exact_remaining(self, authenticated_client, test_cooked_recipe):
        """Can consume exact remaining portion"""
        # Consume 75%
        Meal.objects.create(cooked_recipe=test_cooked_recipe, portion=Decimal('0.75'))

        # Consume remaining 25%
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.25},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_add_to_fully_consumed(self, authenticated_client, test_cooked_recipe):
        """Cannot add meals when cooked recipe is fully consumed"""
        # Consume 100%
        Meal.objects.create(cooked_recipe=test_cooked_recipe, portion=Decimal('1.0'))

        # Try to add more
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.01},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRecipeHistoryWorkflow:
    """Test complete workflows that the front-end will use"""

    def test_create_meals_and_view_history(self, authenticated_client, test_cooked_recipe):
        """Complete workflow: create multiple meals and view in history"""
        # Create first meal (25%)
        response1 = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.25},
            format='json'
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second meal (50%)
        response2 = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'portion': 0.5},
            format='json'
        )
        assert response2.status_code == status.HTTP_201_CREATED

        # View history - should show both meals
        history = authenticated_client.get('/api/recipe_history/')
        assert history.status_code == status.HTTP_200_OK
        assert len(history.data) == 1
        assert len(history.data[0]['meals']) == 2

    def test_multiple_cooked_recipes_with_meals(
        self, authenticated_client, test_user, test_recipe
    ):
        """User can have multiple cooked recipes, each with their own meals"""
        # Cook recipe twice
        cooked1 = CookedRecipe.objects.create(user=test_user, recipe=test_recipe)
        cooked2 = CookedRecipe.objects.create(user=test_user, recipe=test_recipe)

        # Add meals to first cooked recipe
        authenticated_client.post(
            f'/api/recipe_history/{cooked1.id}/meal/',
            {'portion': 0.5},
            format='json'
        )

        # Add meals to second cooked recipe
        authenticated_client.post(
            f'/api/recipe_history/{cooked2.id}/meal/',
            {'portion': 0.75},
            format='json'
        )

        # View history - should show both cooked recipes with their meals
        history = authenticated_client.get('/api/recipe_history/')
        assert len(history.data) == 2

        # Each cooked recipe tracks portions independently
        assert len(history.data[0]['meals']) == 1
        assert len(history.data[1]['meals']) == 1
