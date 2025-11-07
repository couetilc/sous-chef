import pytest
from api.models import Recipe, CookedRecipe, Meal
from rest_framework import status
# import django timezone utilities
from django.utils import timezone
from freezegun import freeze_time

# We need endpoint for:
# - calories, proteins, fats, carbs consumption for the last day
# - calories for the past seven days.

@pytest.mark.django_db
class TestNutritionAPI:
    @freeze_time("2024-11-06 16:00:00", tz_offset=-5)
    def test_calories_calculation_last_week(self, authenticated_client, test_user):
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
            print(date)
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

        # Calories per day should match the created meals
        expected = {
            (now - timezone.timedelta(days=6)).date().isoformat(): 400.0,
            (now - timezone.timedelta(days=3)).date().isoformat(): 600.0,
            now.date().isoformat(): 300.0,
        }

        print(expected)
        for date, calories in calories_by_date.items():
            print(date)
            if date in expected:
                assert calories == expected[date]
            else:
                assert calories == 0.0

    def test_calories_calculation_beyond_last_week(self, authenticated_client, test_user):
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

    def test_nutrition_calculation_today(self, authenticated_client, test_user):
        """Check the nutrition information for today is calculated correctly."""
        now = timezone.now()

        recipes = [
            Recipe.objects.create(title="Breakfast", calories_per_serving=300, fat_g=10, carbs_g=30, protein_g=20),
            Recipe.objects.create(title="Lunch", calories_per_serving=600, fat_g=25, carbs_g=60, protein_g=35),
            Recipe.objects.create(title="Dinner", calories_per_serving=700, fat_g=30, carbs_g=65, protein_g=40),
        ]

        for recipe in recipes:
            cooked = CookedRecipe.objects.create(user=test_user, recipe=recipe, cooked_at=now)
            meal = Meal.objects.create(cooked_recipe=cooked, eaten_at=now, servings=1)
            meal.eaten_at = now
            meal.save()

        response = authenticated_client.get('/api/nutrition/nutrition_last_day/')

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        assert data['calories'] == 300 + 600 + 700
        assert data['fats'] == 10 + 25 + 30
        assert data['carbs'] == 30 + 60 + 65
        assert data['proteins'] == 20 + 35 + 40

    def test_nutrition_calculation_beyond_today(self, authenticated_client, test_user):
        """Check that meals beyond today are not counted in today's nutrition."""
        now = timezone.now()
        yesterday = now - timezone.timedelta(days=1)

        recipe_today1 = Recipe.objects.create(title="Meal 1", calories_per_serving=400, fat_g=15, carbs_g=45, protein_g=25)
        recipe_today2 = Recipe.objects.create(title="Meal 2", calories_per_serving=500, fat_g=20, carbs_g=55, protein_g=30)
        recipe_yesterday = Recipe.objects.create(title="Old Meal", calories_per_serving=800, fat_g=35, carbs_g=80, protein_g=50)

        # Meals eaten today (should count)
        for recipe in [recipe_today1, recipe_today2]:
            cooked = CookedRecipe.objects.create(user=test_user, recipe=recipe, cooked_at=now)
            meal = Meal.objects.create(cooked_recipe=cooked, eaten_at=now, servings=1)
            meal.eaten_at = now
            meal.save()

        # Meal eaten yesterday (should NOT count)
        cooked_old = CookedRecipe.objects.create(user=test_user, recipe=recipe_yesterday, cooked_at=yesterday)
        meal = Meal.objects.create(cooked_recipe=cooked_old, eaten_at=yesterday, servings=1)
        meal.eaten_at = yesterday
        meal.save()

        response = authenticated_client.get('/api/nutrition/nutrition_last_day/')

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Only today's meals should count
        assert data['calories'] == 400 + 500
        assert data['fats'] == 15 + 20
        assert data['carbs'] == 45 + 55
        assert data['proteins'] == 25 + 30
