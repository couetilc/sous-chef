"""
Tests for InProgressRecipe feature and AI recipe creation tools.

This test suite covers:
- Model constraints (unique active recipe per user, cascade deletes)
- AI tool functions (search, create, add/modify/remove ingredients, etc.)
- Complete recipe creation workflow
- Edge cases and error handling
"""

import pytest
from decimal import Decimal
from django.db import IntegrityError
from api.models import (
    InProgressRecipe,
    InProgressRecipeIngredient,
    CuratedIngredient
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def curated_flour():
    """Create a curated flour ingredient"""
    return CuratedIngredient.objects.create(
        name="all-purpose flour",
        is_approved=True,
        frequency=100
    )


@pytest.fixture
def curated_eggs():
    """Create a curated eggs ingredient"""
    return CuratedIngredient.objects.create(
        name="eggs",
        is_approved=True,
        frequency=95
    )


@pytest.fixture
def curated_salt():
    """Create a curated salt ingredient"""
    return CuratedIngredient.objects.create(
        name="salt",
        is_approved=True,
        frequency=90
    )


@pytest.fixture
def recipe_with_ingredient(test_user, curated_flour):
    """Create an InProgressRecipe with one ingredient"""
    recipe = InProgressRecipe.objects.create(
        user=test_user,
        title="Test Recipe",
        status='draft'
    )
    InProgressRecipeIngredient.objects.create(
        recipe=recipe,
        curated_ingredient=curated_flour,
        quantity=Decimal('2.0'),
        unit="cups"
    )
    return recipe


# ============================================================================
# Model Constraint Tests
# ============================================================================

@pytest.mark.django_db
class TestInProgressRecipeConstraints:
    """Test InProgressRecipe model constraints and relationships"""

    def test_one_active_recipe_per_user(self, test_user):
        """User cannot have two active recipes at once"""
        InProgressRecipe.objects.create(user=test_user, status='draft')

        with pytest.raises(IntegrityError):
            InProgressRecipe.objects.create(user=test_user, status='draft')

    def test_multiple_users_can_have_active_recipes(self, test_user, second_user):
        """Different users can each have their own active recipe"""
        recipe1 = InProgressRecipe.objects.create(user=test_user, status='draft')
        recipe2 = InProgressRecipe.objects.create(user=second_user, status='draft')

        assert recipe1.id is not None
        assert recipe2.id is not None
        assert recipe1.user != recipe2.user

    def test_discarded_recipes_dont_count(self, test_user):
        """Discarded recipes don't prevent creating new recipes"""
        InProgressRecipe.objects.create(user=test_user, status='discarded')
        recipe = InProgressRecipe.objects.create(user=test_user, status='draft')

        assert recipe.id is not None
        assert recipe.status == 'draft'

    def test_pending_confirmation_counts_as_active(self, test_user):
        """Pending confirmation recipes count as active"""
        InProgressRecipe.objects.create(user=test_user, status='pending_confirmation')

        with pytest.raises(IntegrityError):
            InProgressRecipe.objects.create(user=test_user, status='draft')

    def test_cascade_delete_removes_ingredients(self, test_user, curated_flour):
        """Deleting recipe deletes all its ingredients"""
        recipe = InProgressRecipe.objects.create(user=test_user)
        InProgressRecipeIngredient.objects.create(
            recipe=recipe,
            curated_ingredient=curated_flour,
            quantity=Decimal('1.0'),
            unit="cup"
        )

        assert InProgressRecipeIngredient.objects.count() == 1
        recipe.delete()
        assert InProgressRecipeIngredient.objects.count() == 0

    def test_string_representation(self, test_user):
        """__str__ returns readable format"""
        recipe = InProgressRecipe.objects.create(
            user=test_user,
            title="Pasta Carbonara",
            status='draft'
        )

        expected = f"{test_user.username}'s Pasta Carbonara (draft)"
        assert str(recipe) == expected


# ============================================================================
# AI Tool Function Tests
# ============================================================================

@pytest.mark.django_db
class TestRecipeCreationTools:
    """Test AI recipe creation tool functions"""

    def test_search_ingredient_returns_matches(self, curated_flour, curated_eggs):
        """search_ingredient tool returns matching ingredients"""
        from api.ai import create_search_ingredient_tool

        CuratedIngredient.objects.create(name="bread flour")
        CuratedIngredient.objects.create(name="almond flour")

        tool = create_search_ingredient_tool()
        result = tool.invoke({"query": "flour"})

        assert "3 ingredient(s)" in result
        assert "all-purpose flour" in result
        assert "bread flour" in result
        assert "almond flour" in result
        assert "eggs" not in result

    def test_search_ingredient_no_matches(self):
        """search_ingredient returns helpful message when no matches"""
        from api.ai import create_search_ingredient_tool

        tool = create_search_ingredient_tool()
        result = tool.invoke({"query": "unicorn_dust"})

        assert "No ingredients found" in result
        assert "Try a different search term" in result

    def test_create_recipe_success(self, test_user):
        """create_recipe tool creates new InProgressRecipe"""
        from api.ai import create_create_recipe_tool

        tool = create_create_recipe_tool(test_user)
        result = tool.invoke({"title": "Pasta Carbonara"})

        assert "Created 'Pasta Carbonara'" in result
        assert InProgressRecipe.objects.filter(user=test_user).count() == 1

        recipe = InProgressRecipe.objects.get(user=test_user)
        assert recipe.title == "Pasta Carbonara"
        assert recipe.status == 'draft'

    def test_create_recipe_prevents_duplicate(self, test_user):
        """create_recipe prevents creating second active recipe"""
        from api.ai import create_create_recipe_tool

        tool = create_create_recipe_tool(test_user)
        tool.invoke({"title": "First Recipe"})
        result = tool.invoke({"title": "Second Recipe"})

        assert "already have an in-progress recipe" in result
        assert InProgressRecipe.objects.filter(user=test_user).count() == 1

    def test_add_ingredient_success(self, test_user, curated_flour):
        """add_ingredient tool adds ingredient to recipe"""
        from api.ai import create_create_recipe_tool, create_add_ingredient_tool

        # Setup: Create recipe
        create_tool = create_create_recipe_tool(test_user)
        create_tool.invoke({"title": "Test"})

        # Test: Add ingredient
        add_tool = create_add_ingredient_tool(test_user)
        result = add_tool.invoke({
            "ingredient_name": "all-purpose flour",
            "quantity": 2.0,
            "unit": "cups"
        })

        assert "Added 2.0 cups of all-purpose flour" in result

        recipe = InProgressRecipe.objects.get(user=test_user)
        assert recipe.ingredients.count() == 1

        ingredient = recipe.ingredients.first()
        assert ingredient.curated_ingredient.name == "all-purpose flour"
        assert ingredient.quantity == Decimal('2.0')
        assert ingredient.unit == "cups"

    def test_add_ingredient_rejects_duplicate(self, test_user, recipe_with_ingredient):
        """add_ingredient rejects duplicate ingredients"""
        from api.ai import create_add_ingredient_tool

        add_tool = create_add_ingredient_tool(test_user)
        result = add_tool.invoke({
            "ingredient_name": "all-purpose flour",
            "quantity": 3.0,
            "unit": "tbsp"
        })

        assert "already in this recipe" in result
        assert recipe_with_ingredient.ingredients.count() == 1

    def test_modify_ingredient_updates_values(self, test_user, recipe_with_ingredient):
        """modify_ingredient tool updates quantity and unit"""
        from api.ai import create_modify_ingredient_tool

        modify_tool = create_modify_ingredient_tool(test_user)
        result = modify_tool.invoke({
            "ingredient_name": "all-purpose flour",
            "new_quantity": 3.0,
            "new_unit": "tbsp"
        })

        assert "Updated all-purpose flour" in result
        assert "quantity from 2.00 to 3" in result  # Flexible decimal formatting
        assert "unit from 'cups' to 'tbsp'" in result

        ingredient = recipe_with_ingredient.ingredients.first()
        assert ingredient.quantity == Decimal('3.0')
        assert ingredient.unit == "tbsp"

    def test_remove_ingredient_deletes_entry(self, test_user, recipe_with_ingredient):
        """remove_ingredient tool removes ingredient from recipe"""
        from api.ai import create_remove_ingredient_tool

        assert recipe_with_ingredient.ingredients.count() == 1

        remove_tool = create_remove_ingredient_tool(test_user)
        result = remove_tool.invoke({"ingredient_name": "all-purpose flour"})

        assert "Removed all-purpose flour" in result
        assert recipe_with_ingredient.ingredients.count() == 0

    def test_update_instructions_saves_steps(self, test_user, recipe_with_ingredient):
        """update_instructions tool saves pipe-separated steps"""
        from api.ai import create_update_instructions_tool

        instructions_tool = create_update_instructions_tool(test_user)
        result = instructions_tool.invoke({
            "instructions": "Preheat oven|Mix ingredients|Bake for 30 minutes"
        })

        assert "Updated recipe instructions with 3 step(s)" in result

        recipe_with_ingredient.refresh_from_db()
        assert recipe_with_ingredient.instructions == "Preheat oven|Mix ingredients|Bake for 30 minutes"

    def test_set_recipe_metadata_updates_fields(self, test_user, recipe_with_ingredient):
        """set_recipe_metadata tool updates title, times, and servings"""
        from api.ai import create_set_recipe_metadata_tool

        metadata_tool = create_set_recipe_metadata_tool(test_user)
        result = metadata_tool.invoke({
            "title": "Updated Title",
            "prep_time_min": 15,
            "cook_time_min": 30,
            "servings": 4
        })

        assert "Updated recipe metadata" in result
        assert "title to 'Updated Title'" in result
        assert "prep time to 15 minutes" in result
        assert "cook time to 30 minutes" in result
        assert "servings to 4" in result

        recipe_with_ingredient.refresh_from_db()
        assert recipe_with_ingredient.title == "Updated Title"
        assert recipe_with_ingredient.prep_time_min == 15
        assert recipe_with_ingredient.cook_time_min == 30
        assert recipe_with_ingredient.servings == 4


# ============================================================================
# Integration Workflow Test
# ============================================================================

@pytest.mark.django_db
class TestRecipeCreationWorkflow:
    """Test complete recipe creation workflow"""

    def test_complete_recipe_creation(self, test_user, curated_flour, curated_eggs, curated_salt):
        """Test full workflow: create → add ingredients → instructions → metadata"""
        from api.ai import (
            create_create_recipe_tool,
            create_add_ingredient_tool,
            create_update_instructions_tool,
            create_set_recipe_metadata_tool
        )

        # Step 1: Create recipe
        create_tool = create_create_recipe_tool(test_user)
        create_result = create_tool.invoke({"title": "Simple Pasta"})
        assert "Created 'Simple Pasta'" in create_result

        # Step 2: Add ingredients
        add_tool = create_add_ingredient_tool(test_user)
        add_tool.invoke({"ingredient_name": "all-purpose flour", "quantity": 2, "unit": "cups"})
        add_tool.invoke({"ingredient_name": "eggs", "quantity": 3, "unit": "whole"})
        add_tool.invoke({"ingredient_name": "salt", "quantity": 1, "unit": "tsp"})

        # Step 3: Add instructions
        instructions_tool = create_update_instructions_tool(test_user)
        instructions_tool.invoke({
            "instructions": "Mix flour and salt|Make a well in center|Add eggs to well|Mix until dough forms|Knead for 10 minutes"
        })

        # Step 4: Set metadata
        metadata_tool = create_set_recipe_metadata_tool(test_user)
        metadata_tool.invoke({
            "prep_time_min": 20,
            "cook_time_min": 5,
            "total_time_min": 25,
            "servings": 4
        })

        # Verify: Check final state
        recipe = InProgressRecipe.objects.get(user=test_user)

        assert recipe.title == "Simple Pasta"
        assert recipe.status == 'draft'
        assert recipe.ingredients.count() == 3
        assert recipe.prep_time_min == 20
        assert recipe.cook_time_min == 5
        assert recipe.total_time_min == 25
        assert recipe.servings == 4
        assert "Mix flour and salt" in recipe.instructions
        assert "Knead for 10 minutes" in recipe.instructions

        # Verify ingredients
        ingredient_names = [ing.curated_ingredient.name for ing in recipe.ingredients.all()]
        assert "all-purpose flour" in ingredient_names
        assert "eggs" in ingredient_names
        assert "salt" in ingredient_names


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.django_db
class TestRecipeCreationEdgeCases:
    """Test edge cases and error handling"""

    def test_add_ingredient_without_recipe(self, test_user, curated_flour):
        """add_ingredient fails gracefully without active recipe"""
        from api.ai import create_add_ingredient_tool

        add_tool = create_add_ingredient_tool(test_user)
        result = add_tool.invoke({
            "ingredient_name": "all-purpose flour",
            "quantity": 2,
            "unit": "cups"
        })

        assert "No active recipe found" in result
        assert "create a recipe first" in result

    def test_add_nonexistent_ingredient(self, test_user):
        """add_ingredient rejects ingredient not in database"""
        from api.ai import create_create_recipe_tool, create_add_ingredient_tool

        # Setup: Create recipe
        create_tool = create_create_recipe_tool(test_user)
        create_tool.invoke({"title": "Test"})

        # Test: Try to add non-existent ingredient
        add_tool = create_add_ingredient_tool(test_user)
        result = add_tool.invoke({
            "ingredient_name": "unicorn_dust",
            "quantity": 1,
            "unit": "pinch"
        })

        assert "not found in the database" in result
        assert "search_ingredient" in result.lower()

    def test_modify_nonexistent_ingredient(self, test_user, recipe_with_ingredient):
        """modify_ingredient returns error for non-existent ingredient"""
        from api.ai import create_modify_ingredient_tool

        modify_tool = create_modify_ingredient_tool(test_user)
        result = modify_tool.invoke({
            "ingredient_name": "nonexistent_ingredient",
            "new_quantity": 5.0
        })

        assert "not found in the recipe" in result

    def test_remove_nonexistent_ingredient(self, test_user, recipe_with_ingredient):
        """remove_ingredient returns error for non-existent ingredient"""
        from api.ai import create_remove_ingredient_tool

        remove_tool = create_remove_ingredient_tool(test_user)
        result = remove_tool.invoke({"ingredient_name": "nonexistent_ingredient"})

        assert "not found in the recipe" in result
