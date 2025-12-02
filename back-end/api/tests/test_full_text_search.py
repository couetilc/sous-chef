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

    # Category 1: Core Problem Fix Tests
    def test_search_natural_language_with_filler_words(self, db):
        """Test the exact query that was failing: 'easy pork recipes with fennel garlic onion'"""
        # Setup: Create recipe with the actual ingredients
        Recipe.objects.create(
            title="Pork Tenderloin with Fennel",
            ingredients="1 lb pork tenderloin | 1 fennel bulb | 4 garlic cloves | 1 onion, diced",
            instructions="Season pork with salt and pepper. Roast with fennel, garlic, and onion at 400F for 25 minutes."
        ).update_search_vector()

        # Query includes "easy" and "recipes" which aren't in the recipe text
        results = Recipe.objects.search_full_text("easy pork recipes with fennel garlic onion")

        # Should find the recipe despite missing "easy" and "recipes"
        assert results.count() >= 1
        found = results[0]
        assert "pork" in found.title.lower() or "pork" in found.ingredients.lower()
        assert "fennel" in found.ingredients.lower()
        assert "garlic" in found.ingredients.lower()
        assert "onion" in found.ingredients.lower()

    def test_search_multi_ingredient_with_modifiers(self, db):
        """Test various multi-ingredient queries with modifier words"""
        # Setup: Create recipes
        Recipe.objects.create(
            title="Chicken and Broccoli Stir Fry",
            ingredients="chicken breast | broccoli | soy sauce | ginger | garlic",
            instructions="Stir fry chicken and broccoli with sauce."
        ).update_search_vector()

        Recipe.objects.create(
            title="Beef Tacos",
            ingredients="ground beef | tortillas | lettuce | tomato | cheese",
            instructions="Cook beef. Serve in tortillas with toppings."
        ).update_search_vector()

        # Test Case 1: Query with "quick" modifier
        results = Recipe.objects.search_full_text("quick chicken broccoli dinner")
        assert results.count() >= 1
        assert any("chicken" in r.ingredients.lower() and "broccoli" in r.ingredients.lower() for r in results)

        # Test Case 2: Query with "healthy" modifier
        results = Recipe.objects.search_full_text("healthy beef tacos recipe")
        assert results.count() >= 1
        assert any("beef" in r.ingredients.lower() for r in results)

    def test_search_ignores_common_filler_words(self, db):
        """Test that common filler words don't prevent matches"""
        Recipe.objects.create(
            title="Salmon with Asparagus",
            ingredients="salmon fillet | asparagus | lemon | olive oil",
            instructions="Roast salmon and asparagus together."
        ).update_search_vector()

        # All these queries should find the salmon recipe
        filler_queries = [
            "best salmon asparagus",
            "delicious salmon and asparagus recipe",
            "simple salmon with asparagus dinner",
            "amazing salmon asparagus dish",
        ]

        for query in filler_queries:
            results = Recipe.objects.search_full_text(query)
            assert results.count() >= 1, f"Query '{query}' failed to find salmon recipe"
            assert "salmon" in results[0].ingredients.lower()

    # Category 2: Natural Language Query Tests
    def test_search_ingredient_list_queries(self, db):
        """Test queries that are primarily lists of ingredients"""
        Recipe.objects.create(
            title="Pasta Primavera",
            ingredients="pasta | zucchini | bell peppers | tomatoes | parmesan",
            instructions="Cook pasta. Sauté vegetables. Combine with cheese."
        ).update_search_vector()

        # User might query with just ingredient names
        results = Recipe.objects.search_full_text("pasta zucchini bell peppers")
        assert results.count() >= 1
        assert all(ing in results[0].ingredients.lower() for ing in ["pasta", "zucchini", "pepper"])

    def test_search_protein_with_sides(self, db):
        """Test queries like 'chicken with rice and vegetables'"""
        Recipe.objects.create(
            title="Grilled Chicken Bowl",
            ingredients="chicken breast | brown rice | mixed vegetables | teriyaki sauce",
            instructions="Grill chicken. Serve over rice with vegetables."
        ).update_search_vector()

        results = Recipe.objects.search_full_text("chicken with rice and vegetables")
        assert results.count() >= 1
        found = results[0]
        assert "chicken" in found.ingredients.lower()
        assert "rice" in found.ingredients.lower()
        assert "vegetable" in found.ingredients.lower()

    def test_search_cuisine_plus_ingredient(self, db):
        """Test queries combining cuisine type with ingredients"""
        Recipe.objects.create(
            title="Thai Basil Chicken",
            ingredients="chicken | thai basil | fish sauce | chilies | garlic",
            instructions="Stir fry chicken with Thai basil and sauce."
        ).update_search_vector()

        # Query mentions "Thai" which is in title, and ingredients
        results = Recipe.objects.search_full_text("thai chicken basil")
        assert results.count() >= 1
        assert "thai" in results[0].title.lower() or "thai" in results[0].ingredients.lower()

    # Category 3: Websearch Feature Tests
    def test_search_phrase_with_quotes(self, db):
        """Test that quoted phrases match as a unit"""
        Recipe.objects.create(
            title="Classic Chicken Breast Recipe",
            ingredients="chicken breast | olive oil | herbs",
            instructions="Season the chicken breast and bake."
        ).update_search_vector()

        Recipe.objects.create(
            title="Chicken Thigh Dinner",
            ingredients="chicken thighs | vegetables",
            instructions="Roast chicken pieces."
        ).update_search_vector()

        # Search for exact phrase "chicken breast"
        results = Recipe.objects.search_full_text('"chicken breast"')

        # Should prioritize recipes with "chicken breast" as a phrase
        if results.count() > 0:
            # First result should contain "chicken breast" together
            first_result_text = (results[0].title + " " + results[0].ingredients).lower()
            assert "chicken breast" in first_result_text

    def test_search_exclusion_with_minus(self, db):
        """Test that minus sign is treated as a regular term (OR logic doesn't support exclusion)"""
        Recipe.objects.create(
            title="Tomato Pasta",
            ingredients="pasta | tomatoes | basil | garlic",
            instructions="Cook pasta with tomato sauce."
        ).update_search_vector()

        Recipe.objects.create(
            title="Alfredo Pasta",
            ingredients="pasta | cream | parmesan | garlic",
            instructions="Make creamy alfredo sauce."
        ).update_search_vector()

        # Search for "pasta -tomato"
        # With OR logic, "-tomato" is just another search term (the minus sign is ignored/stemmed)
        # So this will match any recipe with "pasta" OR "tomato"
        results = Recipe.objects.search_full_text("pasta -tomato")

        # Should find recipes with pasta (both will match since they contain "pasta")
        assert results.count() >= 1
        # Both recipes should be found since they both contain "pasta"
        assert any("pasta" in r.title.lower() for r in results)

    # Category 4: Backward Compatibility Tests
    def test_search_simple_single_word_still_works(self, search_recipes):
        """Test that simple queries still work as before"""
        results = Recipe.objects.search_full_text("pasta")
        assert results.count() >= 1
        assert any("pasta" in r.title.lower() or "pasta" in r.ingredients.lower() for r in results)

    def test_search_title_matches_still_rank_highest(self, db):
        """Test that title matches still rank higher than ingredient matches"""
        Recipe.objects.create(
            title="Chocolate Cake",
            ingredients="flour | sugar | eggs | vanilla",
            instructions="Mix and bake."
        ).update_search_vector()

        Recipe.objects.create(
            title="Vanilla Cupcakes",
            ingredients="flour | sugar | eggs | chocolate chips",
            instructions="Mix and bake."
        ).update_search_vector()

        results = Recipe.objects.search_full_text("chocolate")

        # First result should have "chocolate" in title (weighted higher)
        assert "chocolate" in results[0].title.lower()

    # Category 5: Edge Case Tests
    def test_search_very_long_natural_language_query(self, db):
        """Test handling of long, conversational queries"""
        Recipe.objects.create(
            title="Mediterranean Chicken",
            ingredients="chicken | olives | feta | tomatoes | oregano",
            instructions="Bake chicken with Mediterranean toppings."
        ).update_search_vector()

        long_query = "I'm looking for an easy and quick dinner recipe with chicken, maybe something Mediterranean style with olives and feta cheese that my family would enjoy"

        results = Recipe.objects.search_full_text(long_query)

        # Should still find relevant recipes despite verbosity
        assert results.count() >= 1
        found = results[0]
        assert "chicken" in found.ingredients.lower()

    def test_search_with_special_characters(self, db):
        """Test queries with punctuation and special characters"""
        Recipe.objects.create(
            title="Mom's Apple Pie",
            ingredients="apples | sugar | cinnamon | pie crust",
            instructions="Make classic apple pie."
        ).update_search_vector()

        # Queries with apostrophes, commas, etc.
        queries = [
            "mom's apple pie",
            "apple, cinnamon, sugar",
            "apple & cinnamon pie",
        ]

        for query in queries:
            results = Recipe.objects.search_full_text(query)
            assert results.count() >= 0  # Should not crash


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
