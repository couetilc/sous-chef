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
from django.contrib.auth.models import User
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .models import Recipe, UserCuratedInventory
from .intents import Intent

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
            create_get_user_inventory_tool(self.user)
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