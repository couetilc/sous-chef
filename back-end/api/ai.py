"""
AI Nutritionist module for Sous Chef.

This module provides a clean API for the AI nutritionist feature using LangChain.
Uses factory functions with closures to inject user context into tools.

Usage in views:
    from .ai import NutritionistAgent

    agent = NutritionistAgent(user=request.user)
    response = agent.chat(
        message="What can I make with what I have?",
        conversation_history="Previous messages..."
    )
"""

import os
import json
import logging
import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from django.contrib.auth.models import User
from django.db import transaction
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .models import (
    Recipe,
    UserCuratedInventory,
    CuratedIngredient,
    InProgressRecipe,
    InProgressRecipeIngredient,
    MealPlan,
    MealPlanEntry,
    DietRestrictedCuratedIngredient,
)
from .intents import Intent
from decimal import Decimal

logger = logging.getLogger(__name__)

class Day(Enum):
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6
    Sunday = 7

class Meal(Enum):
    Breakfast = 1
    Lunch = 2
    Dinner = 3

# ============================================================================
# Tool Factory Functions (with user context in closure)
# ============================================================================

def create_search_recipes_tool(user: User):
    """
    Create a recipe search tool.

    Note: This tool doesn't need user context, so it's a simple function.
    ^^ Added user arg for grabbing diet restrictions
    """
    @tool
    def search_recipes_tool(
        search_query: str = "",
        max_calories: int = None,
        min_protein: int = None,
        max_fat: int = None,
        max_carbs: int = None,
        max_total_time: int = None,
        filter_diet_restricted: bool = False,
        page: int = 1
    ) -> str:
        """Search for recipes in the recipe library using full-text search.

        Use this tool to find recipes by searching across recipe titles, ingredients, and instructions.
        Supports natural language queries and returns results ranked by relevance.
        Also allows for filtering of recipes based on the user's saved dietary restrictions.
        Returns up to 5 recipes with complete details including ingredients and instructions.

        Args:
            search_query: Search query to find recipes (searches title, ingredients, instructions)
                         Examples: "pasta with chicken", "chocolate dessert", "vegan protein"
            max_calories: Maximum calories per serving (optional)
            min_protein: Minimum protein in grams (optional)
            max_fat: Maximum fat in grams (optional)
            max_carbs: Maximum carbohydrates in grams (optional)
            max_total_time: Maximum total cooking time in minutes (optional)
                           Includes both prep and cook time combined.
                           Examples: 30 for quick meals, 60 for moderate time commitment
            filter_diet_restricted: If True, remove all recipes containing ingredients conflicting with user dietary restrictions (optional)
            page:   Current page of recipes which is being displayed, with default value set to page 1. (optional)
                    Each page of recipes is 5 recipes long.
                    If user asks for more recipes with some query to be displayed, you can call this tool again with the next page to get the next 5 recipes to show them.

        Returns:
            A formatted string containing recipe details (id, title, nutrition, ingredients, instructions, link)
        """
        # Use full-text search if query provided, otherwise get all recipes
        if search_query and search_query.strip():
            queryset = Recipe.objects.search_full_text(search_query.strip())
        else:
            queryset = Recipe.objects.all().order_by('-created_at')

        if max_calories is not None:
            queryset = queryset.filter(calories_per_serving__lte=max_calories)

        if min_protein is not None:
            queryset = queryset.filter(protein_g__gte=min_protein)

        if max_fat is not None:
            queryset = queryset.filter(fat_g__lte=max_fat)

        if max_carbs is not None:
            queryset = queryset.filter(carbs_g__lte=max_carbs)

        if max_total_time is not None:
            queryset = queryset.filter(total_time_min__lte=max_total_time)
        
        if filter_diet_restricted:
            for userDiet in user.selected_diets.all():
                diet = userDiet.diet
                restricted_diet_ingredients = diet.restricted_ingredients.all()
                restricted_ingredients = CuratedIngredient.objects.filter(restricted_diets__in=restricted_diet_ingredients)
                queryset = queryset.exclude(curated_ingredients__curated_ingredient__in=restricted_ingredients)

        # Limit to 5 results
        slice_start = (page-1)*5
        recipes = queryset[slice_start:slice_start+5]

        if not recipes:
            return "No recipes found matching the search criteria."

        # Format results
        results = []
        for recipe in recipes:
            recipe_text = f"""
Title: {recipe.title}
Link: [{recipe.title}](/recipes/{recipe.id}/)
Nutrition (per serving): {recipe.calories_per_serving} calories, {recipe.protein_g}g protein, {recipe.carbs_g}g carbs, {recipe.fat_g}g fat
Servings: {recipe.servings}
Ingredients: {recipe.ingredients}
Instructions: {recipe.instructions}
---"""
            results.append(recipe_text.strip())

        return "\n\n".join(results)

    return search_recipes_tool


def create_suggest_recipe_tool():
    """
    Create a recipe suggestion tool.

    This tool allows the AI to actively recommend specific recipes from the database
    by displaying them as preview cards in the UI with a "View Full Recipe" button.
    """
    @tool
    def suggest_recipe(recipe_id: int) -> str:
        """Suggest an existing recipe to the user by ID.

        Use this tool when you want to actively recommend a specific recipe to the user
        based on their needs, preferences, or questions. This displays a preview card in
        the UI with recipe details (title, image, times, nutrition) and a button to view
        the full recipe.

        This is different from search_recipes_tool:
        - search_recipes_tool: For searching/browsing recipes (displays as markdown links in chat)
        - suggest_recipe: For actively recommending specific recipes (displays as preview card with "View Full Recipe" button)

        Use suggest_recipe when you want to highlight a recipe as a strong recommendation,
        not just list it among search results.

        Args:
            recipe_id: The ID of the recipe to suggest (from search results)

        Returns:
            JSON string with recipe data for display, or error message if not found
        """
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return f"Error: Recipe with ID {recipe_id} not found in the database."

        # Build recipe data for frontend preview card
        recipe_data = {
            'id': recipe.id,
            'title': recipe.title,
            'image_url': recipe.image_url if recipe.image_url else None,
            'servings': recipe.servings,
            'prep_time_min': recipe.prep_time_min,
            'cook_time_min': recipe.cook_time_min,
            'total_time_min': recipe.total_time_min,
            'calories_per_serving': recipe.calories_per_serving,
            'protein_g': recipe.protein_g,
            'carbs_g': recipe.carbs_g,
            'fat_g': recipe.fat_g,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions.split('|') if recipe.instructions else [],
        }

        return json.dumps(recipe_data)

    return suggest_recipe


def create_get_user_inventory_tool(user: User):
    """
    Create a user inventory tool with user context in closure.

    Args:
        user: Django User object for inventory lookup

    Returns:
        A LangChain tool that can access the user's inventory
    """
    @tool
    def get_user_inventory() -> str:
        """Get the user's current pantry inventory.

        Use this tool to see what ingredients the user currently has in their pantry.
        Returns a list of inventory items with their IDs and ingredient names.

        Returns:
            A formatted string containing inventory items (id and name for each item)
        """
        # User is captured from the closure
        inventory_items = UserCuratedInventory.objects.filter(
            user=user
        ).select_related('curated_ingredient')

        if not inventory_items.exists():
            return "Your pantry inventory is currently empty. Add ingredients to your inventory to track what you have on hand."

        # Format inventory items with ID and name
        items = []
        for item in inventory_items:
            items.append(
                f"ID: {item.id}, Name: {item.curated_ingredient.name}"
            )

        return "Current pantry inventory:\n" + "\n".join(items)

    return get_user_inventory

def create_reset_mealplan_tool(user: User):
    """
    Create a reset meal plan tool.
    """ 
    @tool
    def reset_mealplan_tool(

    ) -> str:
        """Resets the meal plan object which is to be filled with recipes.

        Use this tool to reset or inititalize a meal plan object for this conversation if it does not exist already.
        Only use this tool at the start of a session, or when the user asks to create an additional meal plan, since calling it will erase all of your edits!

        Returns:
            A string indicating whether or not the meal plan object was reset.
        """

        with transaction.atomic():
            mealPlan = MealPlan.objects.filter(user=user, ai_in_progress=True).first()
            if mealPlan: mealPlan.delete()
            mealPlan = MealPlan(
                user=user,
                week_start=datetime.datetime(2025, 11, 23, 6, 1, 53, 13941),
                ai_in_progress=True)
            mealPlan.save()

        return "Successfully created meal plan."

    return reset_mealplan_tool 

def create_edit_mealplan_tool(user: User):
    """
    Create an edit meal plan tool.
    """

    @tool
    def edit_mealplan_tool(
        day: Day,
        meal: Meal,
        title_query: str
    ) -> str:
        """Edit one of the current meal plan object's recipes.

        Use this tool to edit one of the slots in the weekly meal plan.
        This tool will search for recipes for you, so there is no need to search for recipes yourself.

        Args:
            day: The day of the week that the meal will be eaten on.
            meal: The meal (breakfast, lunch, dinner) that the recipe is for.
            title_query: The title which will be used to search the database for a recipe to insert. Do not be too specific so that there is a better chance of finding a recipe.

        Returns:                
            A string indicating whether or not the meal plan object was modified.
        """

        in_progress_mealplan = MealPlan.objects.filter(user=user, ai_in_progress=True).first()
        if (in_progress_mealplan == None):
            return "Could not edit meal plan: You should create a meal plan object first with reset_mealplan_tool, then try again."

        queryset = Recipe.objects.filter(title__icontains=title_query)
        queryset = queryset.filter(calories_per_serving__lt=1000) # TODO redo these bounds
        recipe = queryset.first()
        if (recipe == None):
            return "Could not edit meal plan: No recipes matched the given query. Try searching with a different title."

        with transaction.atomic():
            entry, created = MealPlanEntry.objects.get_or_create(
                meal_plan=in_progress_mealplan,
                day_of_week=day.value,
                meal_index=meal.value,
                defaults={'recipe': recipe, 'servings': 1.0}
            )

            if not created:
                entry.recipe = recipe
                entry.servings = 1.0
                entry.save()

        return f"""
Successfully inserted {recipe.title} as recipe for {day.name}, {meal.name}.
""".strip()
    return edit_mealplan_tool

def create_show_mealplan_tool(user: User):
    """
    Create a show meal plan tool.
    """

    @tool
    def show_mealplan_tool() -> str:
        """ Show the current meal plan being created by the user.

        Use this tool to show the in-progress meal plan to the user. This also displays the total nutrition statistics for the entire week.
        This tool fails if the meal plan object does not yet exist.
        If the meal plan's recipes are empty, you should ask the user if they want to fill their meal plan with recipes.
        When showing the meal plan contents to the user, be sure to include the ingredient ID for debugging purposes.

        Returns:                
            A formatted string containing all the recipes in the in-progress meal plan,
            or a string stating the meal plan is empty,
            or an error message if the meal plan object has not been created.
        """

        in_progress_mealplan = MealPlan.objects.filter(user=user, ai_in_progress=True).first()
        if (in_progress_mealplan == None):
            return "Could not display meal plan: You should create a meal plan object first with create_mealplan_tool, then try again."

        results = []
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        for day in Day:
            for meal in Meal:
                entry = in_progress_mealplan.entries.filter(day_of_week=day.value, meal_index=meal.value).first()
                if not entry:
                    recipe_text = f"""
No meal entry for {day.name}, {meal.name}.
---"""
                else:
                    recipe = entry.recipe
                    total_calories += recipe.calories_per_serving
                    total_protein += recipe.protein_g
                    total_carbs += recipe.carbs_g
                    total_fat += recipe.fat_g
                    recipe_text = f"""
Meal entry for {day.name}, {meal.name}:
Title: {recipe.title}
ID: {recipe.id}
Nutrition (per serving): {recipe.calories_per_serving} calories, {recipe.protein_g}g protein, {recipe.carbs_g}g carbs, {recipe.fat_g}g fat
---"""
                results.append(recipe_text.strip())

        total_nutrition_text = f"""
Total Nutrition Content for the Week: {total_calories} calories, {total_protein}g protein, {total_carbs}g carbs, {total_fat}g fat
                       """
        results.append(total_nutrition_text.strip())
        return "\n\n".join(results)

    return show_mealplan_tool

# ============================================================================
# Recipe Creation Tools (InProgressRecipe)
# ============================================================================

def create_search_ingredient_tool():
    """
    Create a tool to search for curated ingredients.

    Returns a LangChain tool that searches the curated ingredient database.
    """
    @tool
    def search_ingredient(query: str) -> str:
        """Search for curated ingredients by name.

        Use this tool to find available ingredients before adding them to a recipe.
        Returns up to 10 matching ingredient names.

        Args:
            query: Search term for ingredient name (e.g., "flour", "chicken", "olive")

        Returns:
            A formatted string containing matching ingredient names
        """
        if not query or not query.strip():
            return "Please provide a search term."

        # Search with case-insensitive partial match
        ingredients = CuratedIngredient.objects.filter(
            name__icontains=query.strip()
        ).order_by('name')[:10]

        if not ingredients.exists():
            return f"No ingredients found matching '{query}'. Try a different search term."

        # Format results
        results = [ingredient.name for ingredient in ingredients]
        return f"Found {len(results)} ingredient(s):\n" + "\n".join(f"- {name}" for name in results)

    return search_ingredient


def create_create_recipe_tool(user: User):
    """
    Create a tool to initialize a new in-progress recipe.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that creates an InProgressRecipe
    """
    @tool
    def create_recipe(title: str = "") -> str:
        """Create a new in-progress recipe or return existing draft.

        Use this tool to start building a new recipe with the user. Only one active recipe
        is allowed at a time. If a draft already exists, this returns the existing recipe.

        Args:
            title: Optional title for the recipe

        Returns:
            Confirmation message with recipe ID
        """
        # Check for existing active recipe
        existing_recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if existing_recipe:
            return (
                f"You already have an in-progress recipe: '{existing_recipe.title or 'Untitled'}' "
                f"(ID: {existing_recipe.id}). Let's continue working on that one, or you can ask me "
                f"to discard it if you want to start fresh."
            )

        # Create new recipe
        recipe = InProgressRecipe.objects.create(
            user=user,
            title=title,
            status='draft'
        )

        title_msg = f"'{title}'" if title else "a new recipe"
        return f"Created {title_msg} (ID: {recipe.id}). Let's start adding ingredients!"

    return create_recipe


def create_add_ingredient_tool(user: User):
    """
    Create a tool to add an ingredient to the in-progress recipe.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that adds ingredients to InProgressRecipe
    """
    @tool
    def add_ingredient(ingredient_name: str, quantity: float, unit: str) -> str:
        """Add an ingredient to the current in-progress recipe.

        Use this tool after searching for the ingredient name with search_ingredient.
        The ingredient_name must exactly match a curated ingredient in the database.

        Args:
            ingredient_name: Exact name of the curated ingredient (from search results)
            quantity: Amount of ingredient (e.g., 2, 1.5, 0.25)
            unit: Unit of measurement (e.g., "cups", "tbsp", "tsp", "oz", "lbs", "whole")

        Returns:
            Success or error message
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first using create_recipe."

        # Find curated ingredient (case-insensitive exact match)
        try:
            curated_ingredient = CuratedIngredient.objects.get(
                name__iexact=ingredient_name.strip()
            )
        except CuratedIngredient.DoesNotExist:
            return (
                f"Ingredient '{ingredient_name}' not found in the database. "
                f"Please use search_ingredient to find the correct name first."
            )

        # Check if ingredient already exists in recipe
        existing = InProgressRecipeIngredient.objects.filter(
            recipe=recipe,
            curated_ingredient=curated_ingredient
        ).first()

        if existing:
            return (
                f"'{ingredient_name}' is already in this recipe with {existing.quantity} {existing.unit}. "
                f"Use modify_ingredient to change the quantity."
            )

        # Add ingredient
        InProgressRecipeIngredient.objects.create(
            recipe=recipe,
            curated_ingredient=curated_ingredient,
            quantity=Decimal(str(quantity)),
            unit=unit
        )

        return f"Added {quantity} {unit} of {ingredient_name} to the recipe."

    return add_ingredient


def create_modify_ingredient_tool(user: User):
    """
    Create a tool to modify an existing ingredient in the recipe.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that modifies ingredient quantities/units
    """
    @tool
    def modify_ingredient(
        ingredient_name: str,
        new_quantity: float = None,
        new_unit: str = None
    ) -> str:
        """Modify an existing ingredient in the in-progress recipe.

        Use this tool to change the quantity or unit of an ingredient already in the recipe.
        At least one of new_quantity or new_unit must be provided.

        Args:
            ingredient_name: Name of the ingredient to modify
            new_quantity: New quantity (optional, leave unchanged if not provided)
            new_unit: New unit (optional, leave unchanged if not provided)

        Returns:
            Success or error message
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first."

        if new_quantity is None and new_unit is None:
            return "Please provide either new_quantity or new_unit (or both) to modify."

        # Find the ingredient in the recipe
        ingredient_entry = InProgressRecipeIngredient.objects.filter(
            recipe=recipe,
            curated_ingredient__name__iexact=ingredient_name.strip()
        ).first()

        if not ingredient_entry:
            return f"Ingredient '{ingredient_name}' not found in the recipe. Use add_ingredient to add it."

        # Update fields
        old_quantity = ingredient_entry.quantity
        old_unit = ingredient_entry.unit

        if new_quantity is not None:
            ingredient_entry.quantity = Decimal(str(new_quantity))

        if new_unit is not None:
            ingredient_entry.unit = new_unit

        ingredient_entry.save()

        # Build change message
        changes = []
        if new_quantity is not None:
            changes.append(f"quantity from {old_quantity} to {ingredient_entry.quantity}")
        if new_unit is not None:
            changes.append(f"unit from '{old_unit}' to '{ingredient_entry.unit}'")

        return f"Updated {ingredient_name}: changed {' and '.join(changes)}."

    return modify_ingredient


def create_remove_ingredient_tool(user: User):
    """
    Create a tool to remove an ingredient from the recipe.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that removes ingredients
    """
    @tool
    def remove_ingredient(ingredient_name: str) -> str:
        """Remove an ingredient from the in-progress recipe.

        Args:
            ingredient_name: Name of the ingredient to remove

        Returns:
            Success or error message
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first."

        # Find and delete the ingredient
        ingredient_entry = InProgressRecipeIngredient.objects.filter(
            recipe=recipe,
            curated_ingredient__name__iexact=ingredient_name.strip()
        ).first()

        if not ingredient_entry:
            return f"Ingredient '{ingredient_name}' not found in the recipe."

        ingredient_entry.delete()
        return f"Removed {ingredient_name} from the recipe."

    return remove_ingredient


def create_update_instructions_tool(user: User):
    """
    Create a tool to update recipe instructions.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that updates recipe instructions
    """
    @tool
    def update_instructions(instructions: str) -> str:
        """Update the cooking instructions for the in-progress recipe.

        Instructions should be formatted as pipe-separated steps.
        Example: "Preheat oven to 350°F|Mix dry ingredients|Bake for 30 minutes"

        Args:
            instructions: Pipe-separated instruction steps

        Returns:
            Success message with step count
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first."

        # Update instructions
        recipe.instructions = instructions
        recipe.save()

        # Count steps
        step_count = len([s for s in instructions.split('|') if s.strip()])

        return f"Updated recipe instructions with {step_count} step(s)."

    return update_instructions


def create_set_recipe_metadata_tool(user: User):
    """
    Create a tool to set recipe metadata (title, times, servings).

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that updates recipe metadata
    """
    @tool
    def set_recipe_metadata(
        title: str = None,
        prep_time_min: int = None,
        cook_time_min: int = None,
        total_time_min: int = None,
        servings: int = None
    ) -> str:
        """Set recipe metadata like title, cooking times, and servings.

        At least one parameter must be provided. All parameters are optional,
        and only provided values will be updated.

        Args:
            title: Recipe title (optional)
            prep_time_min: Preparation time in minutes (optional)
            cook_time_min: Cooking time in minutes (optional)
            total_time_min: Total time in minutes (optional)
            servings: Number of servings (optional)

        Returns:
            Success message with updated fields
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first."

        # Check that at least one parameter is provided
        if all(param is None for param in [title, prep_time_min, cook_time_min, total_time_min, servings]):
            return "Please provide at least one field to update (title, prep_time_min, cook_time_min, total_time_min, or servings)."

        # Update fields
        updates = []

        if title is not None:
            recipe.title = title
            updates.append(f"title to '{title}'")

        if prep_time_min is not None:
            recipe.prep_time_min = prep_time_min
            updates.append(f"prep time to {prep_time_min} minutes")

        if cook_time_min is not None:
            recipe.cook_time_min = cook_time_min
            updates.append(f"cook time to {cook_time_min} minutes")

        if total_time_min is not None:
            recipe.total_time_min = total_time_min
            updates.append(f"total time to {total_time_min} minutes")

        if servings is not None:
            recipe.servings = servings
            updates.append(f"servings to {servings}")

        recipe.save()

        return f"Updated recipe metadata: {', '.join(updates)}."

    return set_recipe_metadata


def create_mark_recipe_ready_tool(user: User):
    """
    Create a tool to mark the in-progress recipe as ready for human confirmation.

    Args:
        user: Django User object for recipe ownership

    Returns:
        A LangChain tool that marks the recipe as pending confirmation
    """
    @tool
    def mark_recipe_ready() -> str:
        """Mark the in-progress recipe as ready for human confirmation.

        Use this tool when the recipe is complete and ready for the user to review.
        The recipe should have:
        - A title
        - At least one ingredient
        - Instructions
        - Cooking times and servings (recommended)

        This will display a preview card to the user where they can save or discard the recipe.

        Returns:
            JSON string with the full recipe data for display, or an error message
        """
        # Get active recipe
        recipe = InProgressRecipe.objects.filter(
            user=user
        ).exclude(status='discarded').first()

        if not recipe:
            return "No active recipe found. Please create a recipe first using create_recipe."

        # Validate recipe has minimum required fields
        if not recipe.title:
            return "Recipe needs a title before it can be marked as ready. Use set_recipe_metadata to add a title."

        ingredients = list(recipe.ingredients.all().select_related('curated_ingredient'))
        if not ingredients:
            return "Recipe needs at least one ingredient before it can be marked as ready. Use add_ingredient to add ingredients."

        if not recipe.instructions:
            return "Recipe needs instructions before it can be marked as ready. Use update_instructions to add cooking steps."

        # Update status to pending confirmation
        recipe.status = 'pending_confirmation'
        recipe.save()

        # Build recipe data for frontend display
        recipe_data = {
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': [
                {
                    'name': ing.curated_ingredient.name,
                    'quantity': str(ing.quantity),
                    'unit': ing.unit
                }
                for ing in ingredients
            ],
            'instructions': recipe.instructions.split('|') if recipe.instructions else [],
            'prep_time_min': recipe.prep_time_min,
            'cook_time_min': recipe.cook_time_min,
            'total_time_min': recipe.total_time_min,
            'servings': recipe.servings,
            'status': recipe.status
        }

        return json.dumps(recipe_data)

    return mark_recipe_ready


# ============================================================================
# LLM and Prompt Configuration
# ============================================================================

NUTRITIONIST_TEMPLATE = """
# System Prompt

You are a nutritionist, ready to help customers create nutritious, simple recipes they want to cook. You can search for existing recipes, check their pantry inventory, and collaboratively build new custom recipes with them.

The current customer's name is {username}.

## Requirements

### When creating recipes:
- Search for ingredients using search_ingredient before adding them
- Build recipes step by step with create_recipe, add_ingredient, update_instructions, and set_recipe_metadata
- Be conversational and guide users through the recipe creation process
- When the recipe is complete (has title, ingredients, instructions, and ideally times/servings), use mark_recipe_ready to present it for the user's confirmation
- After calling mark_recipe_ready, let the user know they can review and save the recipe using the preview card that will appear

### When suggesting existing recipes:
- Use search_recipes_tool to find recipes matching user criteria
- **IMPORTANT:** When the user shows interest in a recipe (e.g., "that sounds good", "I like that one", "let's do that", or asking for a specific recipe recommendation), you **MUST** call suggest_recipe with the recipe's ID
- suggest_recipe displays a preview card with recipe details (title, image, times, nutrition) and two buttons: "View Recipe" and "Cook Now"
- **Always use suggest_recipe** when you want the user to see the interactive preview card - don't just mention recipes in text
- **Examples of when to use suggest_recipe:**
  - User asks: "What's a good high-protein dinner?" → Search, then suggest_recipe for 1-3 best matches
  - User says: "That chicken recipe sounds perfect" → Call suggest_recipe with that recipe's ID
  - User asks: "Can you recommend something quick?" → Search, then suggest_recipe for quick recipes
  - User says: "I'm happy with any of those" → Call suggest_recipe for all the recipes you mentioned
- Only suggest recipes that genuinely match the user's needs (dietary restrictions, time constraints, nutrition goals)
- You can suggest multiple recipes in one response by calling suggest_recipe multiple times
- After calling suggest_recipe, let the user know they can view the recipe details or start cooking with AI assistance

### When mentioning a recipe by name:
- You **MUST** include the recipe's markdown link in the message.
- You **MUST NOT** write the recipe ID outside a markdown link.
- At the end of your message, you **MUST** link to recipes from the search recipes tool call.
- Remember to share the links for **each** recipe.

## Meal Plan Instructions
The meal plan is an object with 21 recipe slots: 3 recipes for each day of the week.

If a user asks questions about their meal plan, you must use the <tool_name>reset_mealplan_tool</tool_name>, <tool_name>edit_mealplan_tool</tool_name>, and <tool_name>show_mealplan_tool</tool_name>.

The general flow for creating and displaying meal plans is as follows:
    1. The meal plan object must be created with <tool_name>reset_mealplan_tool</tool_name>. After the meal plan is initially created, ask the user if they want to fill it in with their own options, or if you should fill it for them.
    2. The meal plan object's meal slots start off empty, and they can be filled with a call to <tool_name>edit_mealplan_tool</tool_name> for each.
    3. The meal plan can also be shown to the user as a formatted string with <tool_name>show_mealplan_tool</tool_name>. It is not necessary for all recipe slots to be filled.

When showing the user their meal plan, keep the response short; do not include ingredients or instructions.
When editing entries in the meal plan, do **NOT** use <tool_name>search_recipes_tool</tool_name> to find recipes. The <tool_name>edit_mealplan_tool</tool_name> will find recipes for you.
When editing entries in the meal plan, if no recipes in the database match the given query, then just try again with a different recipe title. 
If a user asks you to fill all of the recipes for a day or for the entire week, you must use the <tool_name>edit_mealplan_tool</tool_name> for every relevant meal slot.
For example, if a user you asks to fill Monday's recipes for them, you could call <tool_name>edit_mealplan_tool</tool_name> three times, with "scrambled eggs" as the title_query for breakfast, "fish tacos" as the title_query for lunch, and "beef stew" as the title_query for dinner.

### Communication Requirements:
- You MUST always provide a conversational message to the user in addition to any tool calls
- When calling tools (search_recipes, search_ingredient, etc.), explain what you're doing and/or summarize results
- Never return only tool calls without accompanying explanatory or follow-up text
- Examples:
  - Before tool: "Let me search for recipes that match your criteria..."
  - After tool: "I found 3 delicious chicken recipes for you! Here they are..."
  - During creation: "Great! I've added flour to your recipe. What other ingredients would you like?"

## Conversation History

{conversation_history}

## Current message from {username}

{message}
""".strip()

def get_nutritionist_llm() -> ChatOpenAI:
    """Get the LLM configured for the nutritionist."""
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPEN_ROUTER_API_KEY environment variable is not set. "
            "Please configure this API key to use the AI nutritionist feature."
        )

    return ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model=os.getenv("AI_NUTRITIONIST_MODEL", "openai/gpt-oss-20b:free")
    )


def get_nutritionist_prompt() -> PromptTemplate:
    """Get the nutritionist prompt template."""
    return PromptTemplate(
        template=NUTRITIONIST_TEMPLATE,
        input_variables=["username", "conversation_history", "message"]
    )


# ============================================================================
# High-Level Agent API
# ============================================================================

class NutritionistAgent:
    """
    High-level API for the AI nutritionist agent.

    This class encapsulates all the complexity of tool creation, LLM configuration,
    and tool calling loops, providing a simple interface for views.

    Example:
        agent = NutritionistAgent(user=request.user)
        result = agent.chat(
            message="What's in my pantry?",
            conversation_history="Previous: ..."
        )
    """

    def __init__(self, user: User):
        """
        Initialize the nutritionist agent with user context.

        Args:
            user: Django User object for user-specific operations
        """
        self.user = user
        self.llm = get_nutritionist_llm()
        self.prompt = get_nutritionist_prompt()

        # Create tools with user context
        self.tools = self._create_tools()

        # Create tool lookup map
        self.tool_map = {tool.name: tool for tool in self.tools}

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create chain
        self.chain = self.prompt | self.llm_with_tools

    def _create_tools(self) -> List:
        """Create all tools for the agent with proper context."""
        return [
            # Recipe search and inventory
            create_search_recipes_tool(self.user),
            create_get_user_inventory_tool(self.user),
            create_reset_mealplan_tool(self.user),
            create_edit_mealplan_tool(self.user),
            create_show_mealplan_tool(self.user),

            create_suggest_recipe_tool(),

            # Recipe creation tools
            create_search_ingredient_tool(),
            create_create_recipe_tool(self.user),
            create_add_ingredient_tool(self.user),
            create_modify_ingredient_tool(self.user),
            create_remove_ingredient_tool(self.user),
            create_update_instructions_tool(self.user),
            create_set_recipe_metadata_tool(self.user),
            create_mark_recipe_ready_tool(self.user),
        ]

    def chat(
        self,
        message: str,
        conversation_history: str = "",
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response.

        This method handles the complete tool calling loop, executing tools
        as needed until the LLM provides a final answer.

        Args:
            message: The user's message
            conversation_history: Formatted string of previous conversation
            max_iterations: Maximum tool calling iterations (default: 50, safety limit)

        Returns:
            Dictionary containing:
                - content: The final response text
                - tool_calls: List of tool calls made (with name, args, result, timestamp)

        Raises:
            Exception: Re-raises any errors after logging for handling by views
        """
        from django.utils import timezone

        username = self.user.username

        # Log incoming user message
        logger.info(f"User message from {username}: {message[:100]}{'...' if len(message) > 100 else ''}")

        try:
            # Get initial LLM response
            response = self.chain.invoke({
                "username": username,
                "conversation_history": conversation_history,
                "message": message
            })
        except Exception as e:
            logger.error(f"LLM API error for user {username}: {e}", exc_info=True)
            raise

        # Log initial LLM response
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"LLM response for {username}: Calling {len(response.tool_calls)} tool(s)")
        else:
            logger.info(f"LLM response for {username}: Text-only response (no tool calls)")

        # Build message history for tool calling loop
        messages = [
            HumanMessage(content=f"Username: {username}\n\n{conversation_history}\n\nCurrent message: {message}")
        ]

        # Track all tool calls
        all_tool_calls_data = []
        iteration_count = 0

        # Tool calling loop
        while hasattr(response, 'tool_calls') and response.tool_calls and iteration_count < max_iterations:
            iteration_count += 1

            # Add AI's response with tool calls to history
            messages.append(response)

            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                call_timestamp = timezone.now().isoformat()

                # Log tool call details
                logger.info(f"  → Tool call: {json.dumps(tool_call)}")

                # Execute the tool
                if tool_name in self.tool_map:
                    tool = self.tool_map[tool_name]
                    try:
                        tool_result = tool.invoke(tool_args)
                        # Log successful tool result
                        logger.info(f"    ✓ Tool result: {str(tool_result)}")
                    except Exception as e:
                        logger.error(f"Tool execution error ({tool_name}) for user {username}: {e}", exc_info=True)
                        tool_result = f"Error executing tool: {str(e)}"
                        logger.info(f"    ✗ Tool error: {tool_result}")

                    # Add tool result to message history
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.get('id', 'unknown')
                    ))

                    # Capture tool call data
                    all_tool_calls_data.append({
                        'tool_name': tool_name,
                        'parameters': tool_args,
                        'result': tool_result,
                        'timestamp': call_timestamp,
                        'tool_call': tool_call,
                    })
                else:
                    # Unknown tool
                    error_msg = f"Error: Unknown tool '{tool_name}'"
                    logger.warning(f"Unknown tool requested ({tool_name}) for user {username}")
                    logger.info(f"    ✗ Unknown tool: {tool_name}")
                    messages.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call.get('id', 'unknown')
                    ))
                    all_tool_calls_data.append({
                        'tool_name': tool_name,
                        'parameters': tool_args,
                        'result': error_msg,
                        'timestamp': call_timestamp,
                        'tool_call': tool_call,
                    })

            if (iteration_count == max_iterations): logger.warning(f"Max iterations exceeded while generating respoonse.")
            # Get next response from LLM with tool results
            try:
                response = self.llm_with_tools.invoke(messages)
            except Exception as e:
                logger.error(f"LLM API error during tool loop for user {username}: {e}", exc_info=True)
                raise

        # Check if loop exited due to iteration limit
        if iteration_count >= max_iterations and hasattr(response, 'tool_calls') and response.tool_calls:
            logger.warning(
                f"Tool call iteration limit ({max_iterations}) reached for user {username}. "
                f"LLM still had pending tool calls. Consider increasing max_iterations if this happens frequently."
            )

        # Log final response
        final_content_preview = response.content[:150] + ('...' if len(response.content) > 150 else '')
        logger.info(f"Final response for {username}: {final_content_preview}")
        if all_tool_calls_data:
            logger.info(f"Total tool calls executed: {len(all_tool_calls_data)}")

        # Ensure we always have conversational content for the user
        # If content is empty but we made tool calls, request a concluding message
        if (not response.content or not response.content.strip()) and all_tool_calls_data:
            logger.debug("Content is empty after tool calls - requesting concluding message from LLM")

            # Create a temporary message requesting a summary (not saved to history)
            summary_request = HumanMessage(
                content="Please provide a brief message to the user about what you just did and/or the results."
            )

            # Get final message from LLM (without tool calling)
            final_response = self.llm.invoke(messages + [summary_request])

            # Use the generated content
            response.content = final_response.content
            logger.debug(f"Generated concluding message: {final_response.content[:100]}...")

        # Return final response and metadata
        return {
            'content': response.content,
            'tool_calls': all_tool_calls_data,
        }

# ============================================================================
# SousChef (AI cooking assistant)
# ============================================================================

SOUSCHEF_TEMPLATE = """
You are SousChef, a friendly step-by-step cooking assistant. The current user's username is {username}.

You may be helping the user cook a specific recipe. If RECIPE CONTEXT is provided, you must:

- Carefully read the ingredients and instructions.
- Refer to steps by number where helpful (e.g., "In step 3 you should sauté until translucent").
- Prefer clarifying questions over guessing when the user seems confused.
- Avoid inventing completely new ingredients or steps unless the user explicitly asks for substitutions or modifications.

RECIPE CONTEXT:
{recipe_context}

CONVERSATION HISTORY:
{conversation_history}

Current message from {username}: {message}
""".strip()


def get_souschef_llm() -> ChatOpenAI:
    """Get the LLM configured for the SousChef assistant."""
    api_key = os.environ.get("OPEN_ROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPEN_ROUTER_API_KEY environment variable is not set. "
            "Please configure this API key to use the SousChef AI feature."
        )

    return ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model="x-ai/grok-4.1-fast",
    )


def get_souschef_prompt() -> PromptTemplate:
    """Get the SousChef prompt template."""
    return PromptTemplate(
        template=SOUSCHEF_TEMPLATE,
        input_variables=["username", "recipe_context", "conversation_history", "message"],
    )


class SousChefAgent:
    """
    High-level API for the SousChef AI assistant.

    Very similar to NutritionistAgent, but with a cooking-focused prompt.
    """

    def __init__(self, user: User):
        self.user = user
        self.llm = get_souschef_llm()
        self.prompt = get_souschef_prompt()

        # Reuse the same tools for now (recipe search + user inventory)
        self.tools = self._create_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.chain = self.prompt | self.llm_with_tools

    def _create_tools(self) -> List:
        return [
            create_search_recipes_tool(self.user),
            create_get_user_inventory_tool(self.user),
        ]

    def chat(
        self,
        message: str,
        conversation_history: str = "",
        recipe_context: str = "",
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        from django.utils import timezone

        username = self.user.username

        # First LLM call with prompt (including recipe_context + history)
        try:
            response = self.chain.invoke(
                {
                    "username": username,
                    "recipe_context": recipe_context or "",
                    "conversation_history": conversation_history,
                    "message": message,
                }
            )
        except Exception as e:
            logger.error(f"SousChef LLM API error for user {username}: {e}", exc_info=True)
            raise

        # Build message history for tool loop
        messages = [
            HumanMessage(
                content=(
                    f"Username: {username}\n\n"
                    f"RECIPE CONTEXT (for reference):\n{recipe_context or '(none)'}\n\n"
                    f"{conversation_history}\n\n"
                    f"Current message: {message}"
                )
            )
        ]

        all_tool_calls_data = []
        iteration_count = 0

        # Tool-calling loop (same pattern as NutritionistAgent)
        while hasattr(response, "tool_calls") and response.tool_calls and iteration_count < max_iterations:
            iteration_count += 1
            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                call_timestamp = timezone.now().isoformat()

                if tool_name in self.tool_map:
                    tool = self.tool_map[tool_name]
                    try:
                        tool_result = tool.invoke(tool_args)
                    except Exception as e:
                        logger.error(
                            f"SousChef tool execution error ({tool_name}) for user {username}: {e}",
                            exc_info=True,
                        )
                        tool_result = f"Error executing tool: {str(e)}"

                    messages.append(
                        ToolMessage(
                            content=tool_result,
                            tool_call_id=tool_call.get("id", "unknown"),
                        )
                    )

                    all_tool_calls_data.append(
                        {
                            "tool_name": tool_name,
                            "parameters": tool_args,
                            "result": tool_result,
                            "timestamp": call_timestamp,
                        }
                    )
                else:
                    error_msg = f"Error: Unknown tool '{tool_name}'"
                    logger.warning(f"SousChef unknown tool requested ({tool_name}) for user {username}")
                    messages.append(
                        ToolMessage(
                            content=error_msg,
                            tool_call_id=tool_call.get("id", "unknown"),
                        )
                    )
                    all_tool_calls_data.append(
                        {
                            "tool_name": tool_name,
                            "parameters": tool_args,
                            "result": error_msg,
                            "timestamp": call_timestamp,
                        }
                    )

            # Next LLM call, now with tool results in history
            try:
                response = self.llm_with_tools.invoke(messages)
            except Exception as e:
                logger.error(
                    f"SousChef LLM API error during tool loop for user {username}: {e}",
                    exc_info=True,
                )
                raise

        return {
            "content": response.content,
            "tool_calls": all_tool_calls_data,
        }

# ============================================================================
# User Intent (AI SOUS CHEF) *WIP*
# ============================================================================


def souschef_llm_call(prompt: str) -> str:
    """
    Make a call to the SousChef LLM with the given prompt.

    Args:
        prompt: The prompt string to send to the LLM

    Returns:
        The LLM's response as a string
    """
    llm = get_souschef_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

def classify_user_intent(message: str, recipe_step: str) -> Intent:
    """
    Classify the user's intent based on their message and current recipe step.

    Args:
        message: The user's message
        recipe_step: The current step of the recipe being followed"""

    prompt = f"""
    USER MESSAGE: "{message}"
    CURRENT RECIPE STEP: "{recipe_step}"

    CLASSIFY THE USER'S INTENT INTO ONE OF THE FOLLOWING CATEGORIES:
    {", ".join([intent.value for intent in Intent])}.

    RETURN ONLY THE INTENT VALUE.
    """

    try:
        raw = souschef_llm_call(prompt).strip().lower()
    except Exception as e:
        logger.error(f"SousChef LLM error during intent classification: {e}", exc_info=True)
        return Intent.CLARIFY  # Default fallback intent

    # Map raw response to Intent enum
    for intent in Intent:
        if intent.value == raw:
            return intent

    # Fallback for weird LLM outputs
    return Intent.CLARIFY
    # This is a placeholder implementation. Will need to call an LLM to classify.

def handle_user_intent(
    intent: Intent,
    recipe_or_session,
    current_step_index=None,
    user_message: Optional[str] = None,
):
    """
    Handle the user's intent and return the appropriate recipe step or action.

    Args:
        intent: The classified user intent
        recipe_or_session: Either a CookingSession object (preferred) or a recipe-like
                           object with .steps (for testing/mocks)
        current_step_index: The index of the current recipe step (optional, used for testing)
        user_message: The original user message (used for clarify-like intents)

    Returns:
        Dictionary with 'step_index' and 'message' keys
    """
    # Import here to avoid circular dependency
    from .models import CookingSession as CS

    # Determine if we're working with a CookingSession or a test mock
    is_cooking_session = isinstance(recipe_or_session, CS)

    if is_cooking_session:
        session = recipe_or_session
        steps = session.get_steps_list()
        current_index = session.current_step_index
        recipe_obj = session.recipe
    else:
        # Testing mode with mock recipe object
        recipe = recipe_or_session
        steps = getattr(recipe, "steps", [])
        current_index = current_step_index if current_step_index is not None else 0
        # Best-effort: some mocks might hang the real recipe off `.recipe`
        recipe_obj = getattr(recipe_or_session, "recipe", None)

    if not steps:
        return {
            "step_index": 0,
            "message": "I don't see any steps for this recipe yet.",
        }

    if intent == Intent.NEXT_STEP:
        new_index = min(current_index + 1, len(steps) - 1)
        if is_cooking_session:
            session.current_step_index = new_index
            session.save(update_fields=['current_step_index'])
        return {
            "step_index": new_index,
            "message": f"Moving to the next step {new_index + 1}."
        }

    if intent == Intent.PREVIOUS_STEP:
        new_index = max(current_index - 1, 0)
        if is_cooking_session:
            session.current_step_index = new_index
            session.save(update_fields=['current_step_index'])
        return {
            "step_index": new_index,
            "message": f"Returning to the previous step {new_index + 1}."
        }

    if intent == Intent.RESTART_RECIPE:
        if is_cooking_session:
            session.restart()
        return {
            "step_index": 0,
            "message": "Restarting the recipe from the beginning."
        }

    if intent == Intent.CLARIFY:
        current_step = steps[current_index]
        explanation = clarify_step(
            step=current_step,
            user_message=user_message,
            recipe=recipe_obj,
        )
        return {
            "step_index": current_index,
            "message": explanation,
        }

    if intent == Intent.REPAIR:
        return {
            "step_index": current_index,
            "message": "I noticed some confusion. Let's go over the current step again carefully.",
        }

    # Fallback: don't move the step, just be conservative
    return {
        "step_index": current_index,
        "message": "Let's stay on this step and keep going from here.",
    }

def clarify_step(
    step: str,
    user_message: Optional[str] = None,
    recipe=None,
) -> str:
    """
    Provide a clarification for the given recipe step.

    Args:
        step: The recipe step to clarify
        user_message: The user's original question about this step (may be about the step
                      itself *or* about the overall recipe / final result)
        recipe: Optional Recipe object for full-context clarification
    """
    # Safely extract recipe context if available
    recipe_title = getattr(recipe, "title", None) if recipe is not None else None
    ingredients_raw = getattr(recipe, "ingredients", None) if recipe is not None else None
    instructions_raw = getattr(recipe, "instructions", None) if recipe is not None else None

    recipe_parts = []
    if recipe_title:
        recipe_parts.append(f"RECIPE TITLE:\n{recipe_title}")
    if ingredients_raw:
        recipe_parts.append(f"RECIPE INGREDIENTS (raw field):\n{ingredients_raw}")
    if instructions_raw:
        recipe_parts.append(f"FULL RECIPE INSTRUCTIONS (raw field):\n{instructions_raw}")

    recipe_block = "\n\n".join(recipe_parts) if recipe_parts else "(No additional recipe context was provided.)"

    prompt = f"""
You are SousChef, a friendly step-by-step cooking assistant.

The user is cooking this recipe:
{recipe_block}

They are currently at this step:
"{step}"

The user asked:
"{user_message or ''}"

Your job:
- Directly and concisely answer the user's question in clear, beginner-friendly language.
- Use the current step *and* the overall recipe context when helpful.
- Do NOT just repeat the original step; expand on it and make it specific and actionable.
"""

    return souschef_llm_call(prompt)
