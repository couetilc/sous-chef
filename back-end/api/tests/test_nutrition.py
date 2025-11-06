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
        )
        meal.eaten_at = past_date
        meal.save()

        response = authenticated_client.get('/api/nutrition/calories_last_week/')

        assert response.status_code == status.HTTP_200_OK
        assert 'daily_calories' in response.data

        daily_data = response.data['daily_calories']
        assert len(daily_data) == 7

        calories_by_date = {entry['date']: entry['calories'] for entry in daily_data}
        date_6_days_ago = past_date.date().isoformat()

        # 6 days ago should have 500 calories, others 0
        assert calories_by_date[date_6_days_ago] == 500.0
        for date, calories in calories_by_date.items():
            if date != date_6_days_ago:
                assert calories == 0.0

    def test_nutrition_calculation_beyond_last_week(self, authenticated_client, test_user):
        # calculate a date time 8 days in the past
        past_date = timezone.now() - timezone.timedelta(days=8)

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
        assert 'daily_calories' in response.data

        daily_data = response.data['daily_calories']
        assert len(daily_data) == 7

        calories_by_date = {entry['date']: entry['calories'] for entry in daily_data}
        date_8_days_ago = past_date.date().isoformat()

        # Everything should be 0 since the meal is beyond last week
        for date, calories in calories_by_date.items():
            assert calories == 0.0