import pytest
from api.models import Recipe, CookedRecipe, Meal
from rest_framework import status
# import django timezone utilities
from django.utils import timezone

# We need endpoint for:
# - calories, proteins, fats, carbs consumption for the last day
# - calories for the past seven days.

@pytest.mark.django_db
class TestNutritionAPI:
    def test_nutrition_calculation_last_week(self, authenticated_client, test_user):
        # calculate a date time 6 days in the past
        past_date = timezone.now() - timezone.timedelta(days=6)

        recipe = Recipe.objects.create(title="Test Recipe 1", calories_per_serving=500)
        cooked_recipe = CookedRecipe.objects.create(
            user=test_user,
            recipe=recipe,
            cooked_at=past_date
        )
        meal = Meal.objects.create(
            cooked_recipe=cooked_recipe,
            eaten_at=past_date
        )
        response = authenticated_client.get('/api/nutrition/calories_last_week/')

        assert response.status_code == status.HTTP_200_OK
        assert 'calories' in response.data
        assert response.data['calories'] == 500

    def test_nutrition_calculation_beyond_last_week(self, authenticated_client, test_user):
        # calculate a date time 6 days in the past
        past_date = timezone.now() - timezone.timedelta(days=8)

        print("past_date: ", past_date)

        recipe = Recipe.objects.create(title="Test Recipe 1", calories_per_serving=500)
        cooked_recipe = CookedRecipe.objects.create(
            user=test_user,
            recipe=recipe,
            cooked_at=past_date
        )
        meal = Meal.objects.create(
            cooked_recipe=cooked_recipe,
        )
        meal.eaten_at = past_date
        meal.save()
        
        response = authenticated_client.get('/api/nutrition/calories_last_week/')

        assert response.status_code == status.HTTP_200_OK
        assert 'calories' in response.data
        assert response.data['calories'] == 0