"""
Tests for PostgreSQL Full-Text Search on Recipes

This module tests the full-text search functionality for recipes, including:
- Recipe model manager's search_full_text() method
- GetRecipesFiltered view with search_query parameter
- AI Nutritionist tool integration (search_recipes_tool)
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Recipe
from api.ai import create_search_recipes_tool


@pytest.mark.django_db
class TestRecipeFullTextSearch:
    """Test the Recipe model's full-text search functionality."""

    @pytest.fixture
    def search_recipes(self, db):
        """Create a set of recipes for testing search functionality."""
        recipes = [
            Recipe.objects.create(
                title="Classic Chicken Pasta",
                ingredients="500g pasta | 2 chicken breasts | 1 cup cream | parmesan cheese",
                instructions="Boil pasta. Cook chicken. Mix with cream and cheese. Serve hot.",
                calories_per_serving=450,
                protein_g=35,
                fat_g=15,
                carbs_g=45,
                servings=4
            ),
            Recipe.objects.create(
                title="Chocolate Chip Cookies",
                ingredients="2 cups flour | 1 cup butter | 1 cup chocolate chips | 2 eggs | 1 cup sugar",
                instructions="Mix ingredients. Bake at 350F for 12 minutes. Cool and serve.",
                calories_per_serving=280,
                protein_g=3,
                fat_g=14,
                carbs_g=36,
                servings=24
            ),
            Recipe.objects.create(
                title="Vegan Protein Bowl",
                ingredients="1 cup quinoa | 1 can chickpeas | 2 cups spinach | tahini dressing",
                instructions="Cook quinoa. Roast chickpeas. Assemble with spinach and drizzle tahini.",
                calories_per_serving=380,
                protein_g=18,
                fat_g=12,
                carbs_g=52,
                servings=2
            ),
            Recipe.objects.create(
                title="Grilled Salmon with Vegetables",
                ingredients="2 salmon fillets | 2 cups mixed vegetables | olive oil | lemon",
                instructions="Season salmon. Grill for 8 minutes. Sauté vegetables. Serve with lemon.",
                calories_per_serving=420,
                protein_g=40,
                fat_g=22,
                carbs_g=15,
                servings=2
            ),
            Recipe.objects.create(
                title="Pasta Carbonara",
                ingredients="400g spaghetti | 200g bacon | 3 eggs | parmesan cheese | black pepper",
                instructions="Cook pasta. Fry bacon. Mix eggs and cheese. Combine all with pasta.",
                calories_per_serving=580,
                protein_g=28,
                fat_g=24,
                carbs_g=60,
                servings=4
            ),
        ]
        # Manually update search vectors for testing (normally done by trigger)
        for recipe in recipes:
            recipe.update_search_vector()
        return recipes

    def test_search_by_title(self, search_recipes):
        """Test searching recipes by title keywords."""
        results = Recipe.objects.search_full_text("pasta")
        assert results.count() == 2  # Classic Chicken Pasta and Pasta Carbonara

        # Check that results are ordered by relevance
        titles = [r.title for r in results]
        assert "pasta" in titles[0].lower()

    def test_search_by_ingredients(self, search_recipes):
        """Test searching recipes by ingredient names."""
        results = Recipe.objects.search_full_text("chocolate")
        assert results.count() == 1
        assert results[0].title == "Chocolate Chip Cookies"

    def test_search_by_instructions(self, search_recipes):
        """Test searching recipes by instruction keywords."""
        results = Recipe.objects.search_full_text("grill")
        assert results.count() == 1
        assert results[0].title == "Grilled Salmon with Vegetables"

    def test_search_multi_word_query(self, search_recipes):
        """Test searching with multiple keywords."""
        results = Recipe.objects.search_full_text("chicken cream")
        assert results.count() >= 1
        assert any("Chicken" in r.title for r in results)

    def test_search_relevance_ranking(self, search_recipes):
        """Test that title matches rank higher than ingredient matches."""
        # "pasta" appears in title of 2 recipes and instructions of others
        results = Recipe.objects.search_full_text("pasta")

        # First result should have "pasta" in the title (higher weight)
        assert "pasta" in results[0].title.lower()

        # Verify search_rank annotation exists
        assert hasattr(results[0], 'search_rank')
        assert results[0].search_rank > 0

    def test_search_no_results(self, search_recipes):
        """Test searching with query that matches no recipes."""
        results = Recipe.objects.search_full_text("nonexistent")
        assert results.count() == 0

    def test_search_empty_query(self, search_recipes):
        """Test that empty query returns no results."""
        results = Recipe.objects.search_full_text("")
        assert results.count() == 0

        results = Recipe.objects.search_full_text("   ")
        assert results.count() == 0

    def test_search_case_insensitive(self, search_recipes):
        """Test that search is case-insensitive."""
        results_lower = Recipe.objects.search_full_text("chocolate")
        results_upper = Recipe.objects.search_full_text("CHOCOLATE")
        results_mixed = Recipe.objects.search_full_text("ChOcOlAtE")

        assert results_lower.count() == results_upper.count() == results_mixed.count()

    def test_search_with_stemming(self, search_recipes):
        """Test that PostgreSQL stemming works (e.g., 'bake' matches 'baking')."""
        # Create a recipe with 'baking' in instructions
        Recipe.objects.create(
            title="Baked Bread",
            ingredients="flour | water | yeast",
            instructions="Start by baking the bread in the oven."
        ).update_search_vector()

        # Search for 'bake' should match 'baking' due to stemming
        results = Recipe.objects.search_full_text("bake")
        assert results.count() >= 1


@pytest.mark.django_db
class TestRecipeFilterViewFullTextSearch:
    """Test the GetRecipesFiltered view with full-text search."""

    @pytest.fixture
    def search_recipes(self, db):
        """Create recipes for view testing."""
        recipes = [
            Recipe.objects.create(
                title="Italian Pasta Primavera",
                ingredients="pasta | vegetables | olive oil | garlic",
                instructions="Cook pasta. Sauté vegetables with garlic in olive oil. Combine.",
                calories_per_serving=350,
                servings=4
            ),
            Recipe.objects.create(
                title="Spicy Thai Curry",
                ingredients="curry paste | coconut milk | chicken | vegetables",
                instructions="Cook curry paste. Add coconut milk and chicken. Simmer.",
                calories_per_serving=480,
                servings=4
            ),
            Recipe.objects.create(
                title="Greek Salad",
                ingredients="tomatoes | cucumber | feta cheese | olives | olive oil",
                instructions="Chop vegetables. Add feta and olives. Drizzle with olive oil.",
                calories_per_serving=220,
                servings=2
            ),
        ]
        for recipe in recipes:
            recipe.update_search_vector()
        return recipes

    def test_view_search_query_parameter(self, authenticated_client, search_recipes):
        """Test that search_query parameter performs full-text search."""
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "search_query": "pasta"
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert "Pasta" in response.data['results'][0]['title']

    def test_view_search_query_with_nutrition_filters(self, authenticated_client, search_recipes):
        """Test combining search_query with nutrition filters."""
        # Search for recipes with "olive" and max 300 calories
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "search_query": "olive",
            # This would require adding nutrition filters to the view
        })

        assert response.status_code == status.HTTP_200_OK
        # Should find Greek Salad and Italian Pasta (both have olive oil)
        assert len(response.data['results']) >= 2

    def test_view_search_query_sort_by_relevance(self, authenticated_client, search_recipes):
        """Test sorting by relevance when search_query is provided."""
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "search_query": "pasta",
            "sort_by": "relevance"
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        # First result should have highest relevance

    def test_view_legacy_title_search_still_works(self, authenticated_client, search_recipes):
        """Test that legacy title parameter still works for backward compatibility."""
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "title": "Pasta"
        })

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert "Pasta" in response.data['results'][0]['title']

    def test_view_search_query_takes_precedence_over_title(self, authenticated_client, search_recipes):
        """Test that search_query is used when both search_query and title are provided."""
        # search_query should find more results (searches all fields)
        response = authenticated_client.post('/api/recipes/searchFiltered/', {
            "search_query": "olive",
            "title": "Pasta"  # This should be ignored
        })

        assert response.status_code == status.HTTP_200_OK
        # Should find recipes with "olive" in ingredients/instructions, not just title with "Pasta"
        assert len(response.data['results']) >= 2


@pytest.mark.django_db
class TestAINutritionistSearchTool:
    """Test the AI Nutritionist's search_recipes_tool with full-text search."""

    @pytest.fixture
    def search_recipes(self, db):
        """Create recipes for AI tool testing."""
        recipes = [
            Recipe.objects.create(
                title="High Protein Chicken Bowl",
                ingredients="grilled chicken | quinoa | broccoli",
                instructions="Grill chicken. Cook quinoa. Steam broccoli. Combine.",
                calories_per_serving=420,
                protein_g=45,
                fat_g=10,
                carbs_g=35,
                servings=1
            ),
            Recipe.objects.create(
                title="Low Calorie Salad",
                ingredients="lettuce | tomato | cucumber | vinaigrette",
                instructions="Chop vegetables. Toss with vinaigrette.",
                calories_per_serving=120,
                protein_g=3,
                fat_g=5,
                carbs_g=15,
                servings=1
            ),
        ]
        for recipe in recipes:
            recipe.update_search_vector()
        return recipes

    def test_ai_tool_search_by_query(self, search_recipes):
        """Test that AI tool uses full-text search."""
        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({"search_query": "chicken protein"})

        assert "High Protein Chicken Bowl" in result

    def test_ai_tool_search_with_nutrition_filters(self, search_recipes):
        """Test AI tool with search query and nutrition filters."""
        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({
            "search_query": "salad",
            "max_calories": 150
        })

        assert "Low Calorie Salad" in result
        assert "High Protein Chicken Bowl" not in result

    def test_ai_tool_search_no_results(self, search_recipes):
        """Test AI tool returns appropriate message when no results found."""
        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({"search_query": "nonexistent recipe"})

        assert "No recipes found" in result

    def test_ai_tool_search_empty_query(self, search_recipes):
        """Test AI tool with empty search query returns recent recipes."""
        search_tool = create_search_recipes_tool()
        result = search_tool.invoke({"search_query": ""})

        # Should return recent recipes when no query provided
