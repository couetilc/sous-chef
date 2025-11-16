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
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from django.contrib.auth.models import User
from django.db import transaction
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .models import Recipe, UserCuratedInventory, TestMealPlan, TestIncompleteMealPlan

logger = logging.getLogger(__name__)

class Meal(Enum):
    Breakfast = 1
    Lunch = 2
    Dinner = 3

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
        title_query: str = "",
        max_calories: int = None,
        min_protein: int = None,
        max_fat: int = None,
        max_carbs: int = None
    ) -> str:
        """Search for recipes in the recipe library.

        Use this tool to find recipes based on title keywords and nutritional criteria.
        Returns up to 5 recipes with complete details including ingredients and instructions.

        Args:
            title_query: Keywords to search in recipe titles (e.g., "chicken pasta", "salad")
            max_calories: Maximum calories per serving (optional)
            min_protein: Minimum protein in grams (optional)
            max_fat: Maximum fat in grams (optional)
            max_carbs: Maximum carbohydrates in grams (optional)

        Returns:
            A formatted string containing recipe details (id, title, nutrition, ingredients, instructions)
        """
        # Start with base queryset
        queryset = Recipe.objects.all().order_by('-created_at')

        # Apply filters
        if title_query and title_query.strip():
            queryset = queryset.filter(title__icontains=title_query.strip())

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
Recipe ID: {recipe.id}
Title: {recipe.title}
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

def create_create_mealplan_tool(user: User):
    """
    Create a create meal plan tool.
    """
    @tool
    def create_mealplan_tool(

    ) -> str:
        """Create a weekly meal plan object which can be filled with recipes

        Use this tool to create a meal plan object for this conversation if it does not exist already.
        This tool should be called before any tool calls to modify or show the weekly meal plan are made.

        Returns:
            A string indicating whether or not the meal plan object was created.
        """

        with transaction.atomic():
            mealPlan = TestMealPlan.objects.create()
            incompleteMealPlan = TestIncompleteMealPlan.objects.filter(user=user).first()
            if (incompleteMealPlan != None):
                incompleteMealPlan.mealPlan.delete()
                incompleteMealPlan.delete()
            incompleteMealPlan = TestIncompleteMealPlan.objects.create(
                user=user,
                mealPlan=mealPlan
            )

        return "Successfully created recipe."

    return create_mealplan_tool 

def create_edit_mealplan_tool(user: User):
    """
    Create an edit meal plan tool.
    """

    @tool
    def edit_mealplan_tool(
        meal: Meal,
        title: str
    ) -> str:
        """Edit one of the current weekly meal plan object's recipes.

        Use this tool to edit one of the three recipe slots of the weekly meal plan. 
        The tool's first argument corresponds to the meal slot being edited, and a title query to search for recipes to replace it.
        Choose a recipe title query which is appropriate for the meal being selected. For example, for breakfast an appropriate query might be "pancakes".

        Returns:                
            A string indicating whether or not the meal plan object was modified.
        """

        incompleteMealPlan = TestIncompleteMealPlan.objects.filter(user=user).first()
        if (incompleteMealPlan == None):
            return "Could not edit recipe: You should create a meal plan object first with create_mealplan_tool, then try again."

        with transaction.atomic():
            mealPlan = incompleteMealPlan.mealPlan
            if (meal == Meal.Breakfast):
                queryset = Recipe.objects.all().order_by('-created_at')
                queryset.filter(title=title)
                result = queryset.first()
                mealPlan.recipeBreakfast = result
            if (meal == Meal.Lunch):
                queryset = Recipe.objects.all().order_by('-created_at')
                queryset.filter(title=title)
                mealPlan.recipeLunch= queryset.first()
            if (meal == Meal.Dinner):
                queryset = Recipe.objects.all().order_by('-created_at')
                queryset.filter(title=title)
                mealPlan.recipeDinner= queryset.first()

        return "Successfully edited recipe."
    return edit_mealplan_tool

def create_show_mealplan_tool(user: User):
    """
    Create a show meal plan tool.
    """

    @tool
    def show_mealplan_tool() -> str:
        """ Show the current weekly meal plan being created by the user.

        Use this tool to show the in-progress meal plan to the user.
        This tool fails if the meal plan object does not yet exist, or if one of the meal slots has not yet been filled.

        Returns:                
            A formatted string containing all the recipes in the in-progress meal plan,
            or an error message if the meal plan is missing or incomplete.
        """
        return ""
    return show_mealplan_tool

# ============================================================================
# LLM and Prompt Configuration
# ============================================================================

NUTRITIONIST_TEMPLATE = """
You are a nutritionist, ready to help customers create nutritious, simple recipes they want to cook. The current customer's name is {username}.

{conversation_history}

Current message from {username}: {message}
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
        model="z-ai/glm-4.5-air:free",
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
            create_search_recipes_tool(),
            create_get_user_inventory_tool(self.user),
            create_create_mealplan_tool(self.user)
        ]

    def chat(
        self,
        message: str,
        conversation_history: str = "",
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Process a user message and return the agent's response.

        This method handles the complete tool calling loop, executing tools
        as needed until the LLM provides a final answer.

        Args:
            message: The user's message
            conversation_history: Formatted string of previous conversation
            max_iterations: Maximum tool calling iterations (safety limit)

        Returns:
            Dictionary containing:
                - content: The final response text
                - tool_calls: List of tool calls made (with name, args, result, timestamp)

        Raises:
            Exception: Re-raises any errors after logging for handling by views
        """
        from django.utils import timezone

        username = self.user.username

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

                # Execute the tool
                if tool_name in self.tool_map:
                    tool = self.tool_map[tool_name]
                    try:
                        tool_result = tool.invoke(tool_args)
                    except Exception as e:
                        logger.error(f"Tool execution error ({tool_name}) for user {username}: {e}", exc_info=True)
                        tool_result = f"Error executing tool: {str(e)}"

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
                        'timestamp': call_timestamp
                    })
                else:
                    # Unknown tool
                    error_msg = f"Error: Unknown tool '{tool_name}'"
                    logger.warning(f"Unknown tool requested ({tool_name}) for user {username}")
                    messages.append(ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call.get('id', 'unknown')
                    ))
                    all_tool_calls_data.append({
                        'tool_name': tool_name,
                        'parameters': tool_args,
                        'result': error_msg,
                        'timestamp': call_timestamp
                    })

            # Get next response from LLM with tool results
            try:
                response = self.llm_with_tools.invoke(messages)
            except Exception as e:
                logger.error(f"LLM API error during tool loop for user {username}: {e}", exc_info=True)
                raise

        # Return final response and metadata
        return {
            'content': response.content,
            'tool_calls': all_tool_calls_data if all_tool_calls_data else None
        }
