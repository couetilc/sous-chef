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
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .models import (
    Recipe,
    UserCuratedInventory,
    CuratedIngredient,
    InProgressRecipe,
    InProgressRecipeIngredient
)
from .intents import Intent
from decimal import Decimal

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Factory Functions (with user context in closure)
# ============================================================================

def create_search_recipes_tool():
    """
    Create a recipe search tool.

    Note: This tool doesn't need user context, so it's a simple function.
    """
    @tool
    def search_recipes_tool(
        search_query: str = "",
        max_calories: int = None,
        min_protein: int = None,
        max_fat: int = None,
        max_carbs: int = None
    ) -> str:
        """Search for recipes in the recipe library using full-text search.

        Use this tool to find recipes by searching across recipe titles, ingredients, and instructions.
        Supports natural language queries and returns results ranked by relevance.
        Returns up to 5 recipes with complete details including ingredients and instructions.

        Args:
            search_query: Search query to find recipes (searches title, ingredients, instructions)
                         Examples: "pasta with chicken", "chocolate dessert", "vegan protein"
            max_calories: Maximum calories per serving (optional)
            min_protein: Minimum protein in grams (optional)
            max_fat: Maximum fat in grams (optional)
            max_carbs: Maximum carbohydrates in grams (optional)

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

        # Limit to 5 results
        recipes = queryset[:5]

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

### When mentioning a recipe by name:
- You **MUST** include the recipe's markdown link in the message.
- You **MUST NOT** write the recipe ID outside a markdown link.
- At the end of your message, you **MUST** link to recipes from the search recipes tool call.
- Remember to share the links for **each** recipe.

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
            create_search_recipes_tool(),
            create_get_user_inventory_tool(self.user),

            # Recipe creation tools
            create_search_ingredient_tool(),
            create_create_recipe_tool(self.user),
            create_add_ingredient_tool(self.user),
            create_modify_ingredient_tool(self.user),
            create_remove_ingredient_tool(self.user),
            create_update_instructions_tool(self.user),
            create_set_recipe_metadata_tool(self.user),
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

        # Return final response and metadata
        return {
            'content': response.content,
            'tool_calls': all_tool_calls_data,
        }


SOUSCHEF_TEMPLATE = """
You are SousChef, a friendly step-by-step cooking assistant. The current user's username is {username}.

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
        model="openrouter/sherlock-think-alpha",
    )


def get_souschef_prompt() -> PromptTemplate:
    """Get the SousChef prompt template."""
    return PromptTemplate(
        template=SOUSCHEF_TEMPLATE,
        input_variables=["username", "conversation_history", "message"],
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
            create_search_recipes_tool(),
            create_get_user_inventory_tool(self.user),
        ]

    def chat(
        self,
        message: str,
        conversation_history: str = "",
        max_iterations: int = 10,
    ) -> Dict[str, Any]:
        from django.utils import timezone

        username = self.user.username

        try:
            response = self.chain.invoke(
                {
                    "username": username,
                    "conversation_history": conversation_history,
                    "message": message,
                }
            )
        except Exception as e:
            logger.error(f"SousChef LLM API error for user {username}: {e}", exc_info=True)
            raise

        messages = [
            HumanMessage(
                content=f"Username: {username}\n\n{conversation_history}\n\nCurrent message: {message}"
            )
        ]

        all_tool_calls_data = []
        iteration_count = 0

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
    #response = ask_llm(prompt)
    #return Intent(response.strip())
    # This is a placeholder implementation. Will need to call an LLM to classify.

def handle_user_intent(intent: Intent, recipe, current_step_index):
    """
    Handle the user's intent and return the appropriate recipe step or action.

    Args:
        intent: The classified user intent
        recipe: The recipe object being followed
        current_step_index: The index of the current recipe step
    """
    if intent == Intent.NEXT_STEP:
        new_index = min(current_step_index + 1, len(recipe.steps) - 1)
        return {
            "step_index": new_index,
            "message": f"Moving to the next step {new_index + 1}."
        }
    if intent == Intent.PREVIOUS_STEP:
        new_index = max(current_step_index - 1, 0)
        return {
            "step_index": new_index,
            "message": f"Returning to the previous step {new_index + 1}."
        }
    if intent == Intent.RESTART_RECIPE:
        return {
            "step_index": 0,
            "message": "Restarting the recipe from the beginning."
        }
    if intent == Intent.CLARIFY:
        explanation = clarify_step(recipe.steps[current_step_index])
        return {
            "step_index": current_step_index,
            "message": explanation
        }
    if intent == Intent.REPAIR:
        return {
            "step_index": current_step_index,
            "message": "I noticed confusion. Let's go over the current step again carefully."
        }

def clarify_step(step: str) -> str:
    """
    Provide a clarification for the given recipe step.

    Args:
        step: The recipe step to clarify
    """
    prompt = f"""
    The user wants clarification on the following recipe step:
    "{step}"

    Explain it in SIMPLE cooking-friendly language.
    """

    # return ask_llm(prompt)
    # This is a placeholder implementation.
