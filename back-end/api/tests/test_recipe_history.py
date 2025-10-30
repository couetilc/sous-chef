"""
Tests for recipe history API endpoints.
Now uses *servings* (a positive decimal that can be > 1) instead of percent-of-recipe.
Also validates against remaining servings for a cooked recipe.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe, CookedRecipe, Meal


@pytest.fixture
def test_recipe(db):
    """Creates a test recipe with a defined total_servings."""
    return Recipe.objects.create(
        title='Test Recipe',
        ingredients='1 cup flour\n2 eggs',
        instructions='Mix and bake',
        # NEW: total servings defined on the base recipe
        servings=Decimal('4')
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
    """
    Creates a cooked recipe for test_user.

    Assumes CookedRecipe stores the total at cook time (copy from recipe)
    so history is immutable even if the recipe changes later.
    """
    return CookedRecipe.objects.create(
        user=test_user,
        recipe=test_recipe,
        # NEW: persist the servings snapshot on the cooked instance
        total_servings_cooked=test_recipe.servings
    )


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
        # NEW: expose total servings context to the client
        assert Decimal(str(data['total_servings_cooked'])) == Decimal('4')

    def test_includes_meals_in_response(self, authenticated_client, test_cooked_recipe):
        """Cooked recipes include their meals"""
        # Create two meals in servings
        Meal.objects.create(cooked_recipe=test_cooked_recipe, servings=Decimal('0.50'))
        Meal.objects.create(cooked_recipe=test_cooked_recipe, servings=Decimal('1.25'))

        response = authenticated_client.get('/api/recipe_history/')

        assert response.status_code == status.HTTP_200_OK
        meals = response.data[0]['meals']
        assert len(meals) == 2

        # Verify meal structure
        assert 'servings' in meals[0]
        assert 'eaten_at' in meals[0]

    def test_user_isolation(self, api_client, test_user, second_user, test_recipe):
        """Users only see their own cooked recipes"""
        user1_cooked = CookedRecipe.objects.create(
            user=test_user, recipe=test_recipe, total_servings_cooked=test_recipe.servings
        )
        user2_cooked = CookedRecipe.objects.create(
            user=second_user, recipe=test_recipe, total_servings_cooked=test_recipe.servings
        )

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
    """Test POST /api/recipe_history/<cooked_recipe_id>/meal/ with servings"""

    def test_requires_authentication(self, api_client, test_cooked_recipe):
        """Unauthenticated requests are rejected"""
        response = api_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 0.5}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_meal_success(self, authenticated_client, test_cooked_recipe):
        """Successfully creates a meal (decimal servings, can be < 1)"""
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 0.5},
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['cooked_recipe'] == test_cooked_recipe.id
        # Responses should be strings for Decimal fields via DRF
        assert response.data['servings'] == '0.50'
        assert 'eaten_at' in response.data

    def test_servings_required(self, authenticated_client, test_cooked_recipe):
        """Returns error when servings is missing"""
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
            {'servings': 0.5},
            format='json'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authorization_check(self, api_client, test_user, second_user, test_recipe):
        """Users cannot create meals for other users' cooked recipes"""
        cooked_recipe = CookedRecipe.objects.create(
            user=test_user, recipe=test_recipe, total_servings_cooked=test_recipe.servings
        )

        api_client.force_authenticate(user=second_user)
        response = api_client.post(
            f'/api/recipe_history/{cooked_recipe.id}/meal/',
            {'servings': 0.5},
            format='json'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'permission' in response.data['error'].lower()

    def test_servings_validation_exceeds_remaining(self, authenticated_client, test_cooked_recipe):
        """Returns error when servings exceeds what remains"""
        # total_servings_cooked is 4; consume 3.2 servings
        Meal.objects.create(cooked_recipe=test_cooked_recipe, servings=Decimal('3.20'))

        # Try to consume 1.0 (would bring total to 4.2 > 4.0)
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 1.0},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_consume_exact_remaining(self, authenticated_client, test_cooked_recipe):
        """Can consume exactly the remaining servings"""
        # total 4; consume 2.75, then 1.25 (total 4.0 exact)
        Meal.objects.create(cooked_recipe=test_cooked_recipe, servings=Decimal('2.75'))

        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 1.25},
            format='json'
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_add_to_fully_consumed(self, authenticated_client, test_cooked_recipe):
        """Cannot add meals when cooked recipe is fully consumed"""
        # total 4; consume all 4 in one go
        Meal.objects.create(cooked_recipe=test_cooked_recipe, servings=Decimal('4.00'))

        # Try to add more
        response = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 0.25},
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRecipeHistoryWorkflow:
    """Test complete workflows that the front-end will use (servings)"""

    def test_create_meals_and_view_history(self, authenticated_client, test_cooked_recipe):
        """Create multiple meals in servings and view in history"""
        # First meal: 0.5 servings
        response1 = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 0.5},
            format='json'
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Second meal: 1.25 servings
        response2 = authenticated_client.post(
            f'/api/recipe_history/{test_cooked_recipe.id}/meal/',
            {'servings': 1.25},
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
        cooked1 = CookedRecipe.objects.create(
            user=test_user, recipe=test_recipe, total_servings_cooked=test_recipe.servings
        )
        cooked2 = CookedRecipe.objects.create(
            user=test_user, recipe=test_recipe, total_servings_cooked=test_recipe.servings
        )

        # Add meals to first cooked recipe
        authenticated_client.post(
            f'/api/recipe_history/{cooked1.id}/meal/',
            {'servings': 1.00},
            format='json'
        )

        # Add meals to second cooked recipe
        authenticated_client.post(
            f'/api/recipe_history/{cooked2.id}/meal/',
            {'servings': 0.75},
            format='json'
        )

        # View history - should show both cooked recipes with their meals
        history = authenticated_client.get('/api/recipe_history/')
        assert len(history.data) == 2

        # Each cooked recipe tracks servings independently
        assert len(history.data[0]['meals']) == 1
        assert len(history.data[1]['meals']) == 1
