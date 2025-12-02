"""
Tests for AI recipe search tool functionality.
"""
import pytest
from api.models import Recipe
from api.ai import create_search_recipes_tool


@pytest.mark.django_db
class TestSearchRecipesToolTimeFiltering:
    """Test max_total_time parameter in search_recipes_tool"""

    def test_basic_time_filtering(self):
        """Test that max_total_time filters recipes correctly"""
        # Create test recipes with different times
        quick = Recipe.objects.create(
            title='Quick Pasta',
            total_time_min=15,
            ingredients='pasta, sauce',
            instructions='boil pasta, add sauce'
        )
        medium = Recipe.objects.create(
            title='Roasted Chicken',
            total_time_min=45,
            ingredients='chicken, herbs',
            instructions='season and roast'
        )
        slow = Recipe.objects.create(
            title='Slow Braised Beef',
            total_time_min=180,
            ingredients='beef, vegetables',
            instructions='braise for 3 hours'
        )

        # Test filtering
        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 45
        })

        # Verify only recipes <= 45 minutes returned
        assert 'Quick Pasta' in result
        assert 'Roasted Chicken' in result
        assert 'Slow Braised Beef' not in result

    def test_no_results_when_too_restrictive(self):
        """Test that very restrictive time filter returns no results message"""
        Recipe.objects.create(
            title='Long Recipe',
            total_time_min=120,
            ingredients='ingredients',
            instructions='cook for 2 hours'
        )

        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 30
        })

        assert "No recipes found" in result

    def test_time_combined_with_nutrition_filters(self):
        """Test that time filter works with nutrition filters (AND logic)"""
        # High calorie, quick recipe
        Recipe.objects.create(
            title='Quick High Cal',
            total_time_min=20,
            calories_per_serving=800,
            ingredients='butter, sugar',
            instructions='mix'
        )
        # Low calorie, quick recipe
        low_cal_quick = Recipe.objects.create(
            title='Quick Low Cal',
            total_time_min=20,
            calories_per_serving=200,
            ingredients='vegetables',
            instructions='steam'
        )
        # Low calorie, slow recipe
        Recipe.objects.create(
            title='Slow Low Cal',
            total_time_min=90,
            calories_per_serving=200,
            ingredients='vegetables',
            instructions='slow roast'
        )

        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 30,
            'max_calories': 300
        })

        # Only the low calorie AND quick recipe should match
        assert 'Quick Low Cal' in result
        assert 'Quick High Cal' not in result
        assert 'Slow Low Cal' not in result

    def test_edge_case_zero_time_recipes(self):
        """Test that recipes with total_time_min=0 pass filter"""
        # Recipe with unknown/zero time
        unknown_time = Recipe.objects.create(
            title='Unknown Time Recipe',
            total_time_min=0,
            ingredients='ingredients',
            instructions='instructions'
        )

        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 100
        })

        # Recipe with 0 time should be included (0 <= 100)
        assert 'Unknown Time Recipe' in result

    def test_edge_case_exact_match(self):
        """Test that recipe with exactly max_total_time is included (<=)"""
        exact_match = Recipe.objects.create(
            title='Exactly 45 Minutes',
            total_time_min=45,
            ingredients='ingredients',
            instructions='instructions'
        )

        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 45
        })

        # Should use <= not <, so exact match included
        assert 'Exactly 45 Minutes' in result

    def test_edge_case_very_large_value(self):
        """Test that very large max_total_time returns all recipes"""
        Recipe.objects.create(
            title='Quick Recipe',
            total_time_min=15,
            ingredients='ingredients',
            instructions='instructions'
        )
        Recipe.objects.create(
            title='Long Recipe',
            total_time_min=200,
            ingredients='ingredients',
            instructions='instructions'
        )

        tool = create_search_recipes_tool()
        result = tool.invoke({
            'search_query': '',
            'max_total_time': 9999
        })

        # Both recipes should be returned
        assert 'Quick Recipe' in result
        assert 'Long Recipe' in result

    def test_omitted_parameter_skips_filter(self):
        """Test that omitting max_total_time doesn't apply filter"""
        Recipe.objects.create(
            title='Any Time Recipe',
            total_time_min=500,
            ingredients='ingredients',
            instructions='instructions'
        )

        tool = create_search_recipes_tool()
        # Don't include max_total_time parameter at all
        result = tool.invoke({
            'search_query': ''
        })

        # Should return recipe even though it takes 500 minutes
        assert 'Any Time Recipe' in result


@pytest.mark.django_db
class TestSearchRecipesToolWebsearch:
    """Test AI Tool Integration with websearch natural language queries (Category 6)"""

    def test_ai_tool_with_problematic_query(self):
        """Test search_recipes_tool with the original problem query"""
        Recipe.objects.create(
            title="Pork with Fennel and Garlic",
            ingredients="pork tenderloin | fennel | garlic | onion",
            instructions="Roast everything together.",
            calories_per_serving=350,
            protein_g=30,
            fat_g=15,
            carbs_g=20,
            servings=4
        ).update_search_vector()

        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({"search_query": "easy pork recipes with fennel garlic onion"})

        # Should return recipe, not "No recipes found"
        assert "No recipes found" not in result
        assert "Pork" in result
        assert "fennel" in result.lower()

    def test_ai_tool_with_various_natural_queries(self):
        """Test tool handles different natural language patterns"""
        Recipe.objects.create(
            title="Quick Chicken Stir Fry",
            ingredients="chicken | vegetables | soy sauce",
            instructions="Stir fry quickly.",
            calories_per_serving=300,
            protein_g=35,
            servings=2
        ).update_search_vector()

        search_tool = create_search_recipes_tool()

        # Test queries that contain terms that will match the recipe
        queries = [
            "healthy chicken dinner",  # Contains "chicken"
            "quick stir fry with chicken and veggies",  # Contains "quick", "stir", "chicken"
            "simple chicken recipe",  # Contains "chicken"
        ]

        for query in queries:
            result = search_tool.invoke({"search_query": query})
            # Should find the chicken recipe since query contains matching terms
            assert "No recipes found" not in result
            assert "chicken" in result.lower() or "Chicken" in result

    def test_ai_tool_combined_search_and_filters(self):
        """Test tool with both text search and nutrition filters"""
        Recipe.objects.create(
            title="Low Cal Pork Tenderloin",
            ingredients="pork | vegetables | herbs",
            instructions="Roast lean pork.",
            calories_per_serving=250,
            protein_g=30,
            fat_g=8,
            servings=4
        ).update_search_vector()

        Recipe.objects.create(
            title="Rich Pork Chops",
            ingredients="pork chops | butter | cream",
            instructions="Pan fry in butter.",
            calories_per_serving=500,
            protein_g=35,
            fat_g=30,
            servings=2
        ).update_search_vector()

        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({
            "search_query": "pork dinner",
            "max_calories": 300
        })

        # Should find low-cal pork, not rich pork chops
        assert "Low Cal" in result or "Tenderloin" in result
        assert "Rich Pork Chops" not in result
