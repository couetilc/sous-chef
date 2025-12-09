"""
Tests for cooking session endpoints and recipe history integration.

Tests verify that when a cooking session ends (either manually or via AI),
it automatically creates a CookedRecipe and initial Meal entry.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework import status
from unittest.mock import patch
from api.models import Recipe, CookingSession, CookedRecipe, Meal
from api.intents import Intent


@pytest.mark.django_db
class TestEndCookingSessionWithHistory:
    """Test ending cooking session creates recipe history"""

    def test_end_session_creates_cooked_recipe(self, authenticated_client, test_user, test_recipe):
        """Ending session creates CookedRecipe entry with correct servings"""
        # Create active cooking session
        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        # End the session
        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['history_created'] is True
        assert 'cooked_recipe_id' in response.data

        # Verify CookedRecipe was created
        cooked_recipes = CookedRecipe.objects.filter(
            user=test_user,
            recipe=test_recipe
        )
        assert cooked_recipes.count() == 1

        cooked_recipe = cooked_recipes.first()
        assert cooked_recipe.total_servings_cooked == Decimal(str(test_recipe.servings))

    def test_end_session_creates_initial_meal(self, authenticated_client, test_user, test_recipe):
        """Ending session creates initial Meal entry with 1 serving"""
        # Create active cooking session
        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        # End the session
        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify CookedRecipe and Meal were created
        cooked_recipe = CookedRecipe.objects.get(user=test_user, recipe=test_recipe)
        meals = Meal.objects.filter(cooked_recipe=cooked_recipe)

        assert meals.count() == 1
        assert meals.first().servings == Decimal('1.0')

    def test_multiple_sessions_create_separate_history(self, authenticated_client, test_user, test_recipe):
        """Multiple cooking sessions for same recipe create separate history entries"""
        # Create and end first session
        session1 = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )
        authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        # Create and end second session
        session2 = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )
        authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        # Should have two separate CookedRecipe entries
        assert CookedRecipe.objects.filter(
            user=test_user,
            recipe=test_recipe
        ).count() == 2

    def test_end_session_with_zero_servings_recipe(self, authenticated_client, test_user, db):
        """Handles recipe with zero servings gracefully, defaults to 1"""
        recipe = Recipe.objects.create(
            title='No Servings Recipe',
            ingredients='test',
            instructions='test',
            servings=0  # Edge case
        )

        session = CookingSession.objects.create(
            user=test_user,
            recipe=recipe,
            is_active=True,
            current_step_index=0
        )

        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': recipe.id},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['history_created'] is True

        # Should default to 1 serving
        cooked_recipe = CookedRecipe.objects.get(user=test_user, recipe=recipe)
        assert cooked_recipe.total_servings_cooked == Decimal('1')

    def test_end_session_with_large_servings(self, authenticated_client, test_user, db):
        """Handles recipe with large servings correctly"""
        recipe = Recipe.objects.create(
            title='Large Batch Recipe',
            ingredients='test',
            instructions='test',
            servings=50  # Large batch
        )

        session = CookingSession.objects.create(
            user=test_user,
            recipe=recipe,
            is_active=True,
            current_step_index=0
        )

        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': recipe.id},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['history_created'] is True

        # Should preserve the large serving count
        cooked_recipe = CookedRecipe.objects.get(user=test_user, recipe=recipe)
        assert cooked_recipe.total_servings_cooked == Decimal('50')

    def test_end_session_requires_authentication(self, api_client, test_recipe):
        """Unauthenticated requests are rejected"""
        response = api_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_end_session_no_active_session(self, authenticated_client, test_recipe):
        """Returns 404 when no active session exists"""
        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_end_session_marks_session_inactive(self, authenticated_client, test_user, test_recipe):
        """Ending session sets is_active to False and sets end_time"""
        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        response = authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify session is now inactive
        session.refresh_from_db()
        assert session.is_active is False
        assert session.end_time is not None


@pytest.mark.django_db
class TestHelperFunction:
    """Test the create_recipe_history_from_session helper function directly"""

    def test_helper_creates_cooked_recipe_and_meal(self, test_user, test_recipe):
        """Helper function creates both CookedRecipe and Meal"""
        from api.views import create_recipe_history_from_session

        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        cooked_recipe, meal = create_recipe_history_from_session(session)

        # Verify both were created
        assert cooked_recipe is not None
        assert meal is not None
        assert cooked_recipe.user == test_user
        assert cooked_recipe.recipe == test_recipe
        assert cooked_recipe.total_servings_cooked == Decimal('4')  # test_recipe has 4 servings
        assert meal.cooked_recipe == cooked_recipe
        assert meal.servings == Decimal('1.0')

    def test_helper_handles_zero_servings(self, test_user, db):
        """Helper function defaults to 1 serving when recipe has 0 servings"""
        from api.views import create_recipe_history_from_session

        recipe = Recipe.objects.create(
            title='Zero Servings',
            ingredients='test',
            instructions='test',
            servings=0
        )

        session = CookingSession.objects.create(
            user=test_user,
            recipe=recipe,
            is_active=True,
            current_step_index=0
        )

        cooked_recipe, meal = create_recipe_history_from_session(session)

        assert cooked_recipe is not None
        assert cooked_recipe.total_servings_cooked == Decimal('1')  # Defaulted to 1

    def test_helper_atomic_transaction(self, test_user, test_recipe):
        """Helper function creates both records atomically"""
        from api.views import create_recipe_history_from_session

        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        # Call helper
        cooked_recipe, meal = create_recipe_history_from_session(session)

        # Verify both exist in database
        assert CookedRecipe.objects.filter(id=cooked_recipe.id).exists()
        assert Meal.objects.filter(id=meal.id).exists()


@pytest.mark.django_db
class TestRecipeHistoryIntegration:
    """Test that recipe history integrates properly with cooking sessions"""

    def test_ended_session_appears_in_history(self, authenticated_client, test_user, test_recipe):
        """Ended cooking session appears in /api/recipe_history/"""
        # Create and end session
        session = CookingSession.objects.create(
            user=test_user,
            recipe=test_recipe,
            is_active=True,
            current_step_index=0
        )

        authenticated_client.post(
            '/api/cooking_session/end/',
            {'recipe_id': test_recipe.id},
            format='json'
        )

        # Check recipe history endpoint
        history_response = authenticated_client.get('/api/recipe_history/')

        assert history_response.status_code == status.HTTP_200_OK
        assert len(history_response.data) == 1
        assert history_response.data[0]['recipe']['id'] == test_recipe.id
        assert len(history_response.data[0]['meals']) == 1
        assert history_response.data[0]['meals'][0]['servings'] == '1.00'

    def test_multiple_sessions_show_in_history(self, authenticated_client, test_user, test_recipe):
        """Multiple ended sessions all appear in recipe history"""
        # Create and end three sessions
        for i in range(3):
            session = CookingSession.objects.create(
                user=test_user,
                recipe=test_recipe,
                is_active=True,
                current_step_index=0
            )

            authenticated_client.post(
                '/api/cooking_session/end/',
                {'recipe_id': test_recipe.id},
                format='json'
            )

        # Check recipe history
        history_response = authenticated_client.get('/api/recipe_history/')

        assert history_response.status_code == status.HTTP_200_OK
        assert len(history_response.data) == 3

        # Each should have 1 initial meal
        for entry in history_response.data:
            assert len(entry['meals']) == 1
            assert entry['meals'][0]['servings'] == '1.00'
