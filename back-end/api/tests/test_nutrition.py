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
        """Check calories are calculated correctly for the past 7 days."""
        now = timezone.now()

        recipe1 = Recipe.objects.create(title="Recipe 1", calories_per_serving=400)
        recipe2 = Recipe.objects.create(title="Recipe 2", calories_per_serving=600)
        recipe3 = Recipe.objects.create(title="Recipe 3", calories_per_serving=300)

        dates = [
            now - timezone.timedelta(days=6),
            now - timezone.timedelta(days=3),
            now,
        ]

        for recipe, date in zip([recipe1, recipe2, recipe3], dates):
            cooked_recipe = CookedRecipe.objects.create(
                user=test_user,
                recipe=recipe,
                cooked_at=date
            )
            meal = Meal.objects.create(cooked_recipe=cooked_recipe)
            meal.eaten_at = date
            meal.save()

        response = authenticated_client.get('/api/nutrition/calories_last_week/')

        assert response.status_code == status.HTTP_200_OK
        assert 'daily_calories' in response.data

        daily_data = response.data['daily_calories']
        assert len(daily_data) == 7

        calories_by_date = {entry['date']: entry['calories'] for entry in daily_data}

        # Expected calories by day
        expected = {
            (now - timezone.timedelta(days=6)).date().isoformat(): 400.0,
            (now - timezone.timedelta(days=3)).date().isoformat(): 600.0,
            now.date().isoformat(): 300.0,
        }

        for date, calories in calories_by_date.items():
            if date in expected:
                assert calories == expected[date]
            else:
                assert calories == 0.0

    def test_nutrition_calculation_beyond_last_week(self, authenticated_client, test_user):
        """Check that meals beyond the last 7 days are not counted."""
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