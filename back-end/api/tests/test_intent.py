import pytest
from django.contrib.auth.models import User
from rest_framework import status
from unittest.mock import patch, MagicMock
from api.models import ChatConversation, ChatMessage, Recipe
from api.ai import souschef_llm_call, classify_user_intent, handle_user_intent, clarify_step
from api.intents import Intent


class FakeRecipe:
    """Mock recipe object for testing"""
    def __init__(self, steps):
        self.steps = steps


@pytest.mark.django_db
class TestIntentClassification:

    @patch('api.ai.souschef_llm_call')
    def test_classify_next_step(self, mock_llm_call):
        mock_llm_call.return_value = "next_step"
        user_message = "What should I do next?"
        intent = classify_user_intent(user_message, recipe_step="Mix the ingredients.")
        assert intent == Intent.NEXT_STEP

    @patch('api.ai.souschef_llm_call')
    def test_classify_clarify(self, mock_llm_call):
        mock_llm_call.return_value = "clarify"
        user_message = "I don't understand this step."
        intent = classify_user_intent(user_message, recipe_step="Bake for 20 minutes.")
        assert intent == Intent.CLARIFY
    

    @patch('api.ai.souschef_llm_call')
    def test_classify_previous_step(self, mock_llm_call):
        mock_llm_call.return_value = "previous_step"
        user_message = "Can you go back to the last step?"
        intent = classify_user_intent(user_message, recipe_step="Add salt to the dish.")
        assert intent == Intent.PREVIOUS_STEP


    @patch('api.ai.souschef_llm_call')
    def test_classify_restart_recipe(self, mock_llm_call):
        mock_llm_call.return_value = "restart_recipe"
        user_message = "Let's start over."
        intent = classify_user_intent(user_message, recipe_step="Boil the water.")
        assert intent == Intent.RESTART_RECIPE
    

    @patch('api.ai.souschef_llm_call')
    def test_classify_repair_intent(self, mock_llm_call):
        mock_llm_call.return_value = "repair"
        user_message = "Something is wrong."
        intent = classify_user_intent(user_message, recipe_step="Chop the onions.")
        assert intent == Intent.REPAIR
    
@pytest.mark.django_db
class TestIntentHandlers:
    """Test the intent handlers with a mock recipe"""

    @pytest.fixture
    def recipe(self):
        """Fixture for a fake recipe object"""
        return FakeRecipe(["Step 1: Mix ingredients", "Step 2: Bake at 350°F", "Step 3: Let cool"])

    def test_next_step_handler(self, recipe):
        """Test moving to the next step"""
        result = handle_user_intent(Intent.NEXT_STEP, recipe, current_step_index=1)
        assert result["step_index"] == 2
        assert "next step" in result["message"].lower()
    
    def test_next_step_at_end(self, recipe):
        """Test that next step at the end stays at the last step"""
        result = handle_user_intent(Intent.NEXT_STEP, recipe, current_step_index=2)
        assert result["step_index"] == 2  # Should stay at last step
        assert "next step" in result["message"].lower()

    def test_previous_step_handler(self, recipe):
        """Test moving to the previous step"""
        result = handle_user_intent(Intent.PREVIOUS_STEP, recipe, current_step_index=2)
        assert result["step_index"] == 1
        assert "previous step" in result["message"].lower()

    def test_previous_step_at_beginning(self, recipe):
        """Test that previous step at beginning stays at first step"""
        result = handle_user_intent(Intent.PREVIOUS_STEP, recipe, current_step_index=0)
        assert result["step_index"] == 0  # Should stay at first step
        assert "previous step" in result["message"].lower()

    def test_restart_recipe_handler(self, recipe):
        """Test restarting the recipe from any step"""
        result = handle_user_intent(Intent.RESTART_RECIPE, recipe, current_step_index=2)
        assert result["step_index"] == 0
        assert "restarting" in result["message"].lower()

    @patch('api.ai.souschef_llm_call')
    def test_clarify_handler(self, mock_llm_call, recipe):
        """Test clarifying a step"""
        mock_llm_call.return_value = "This step means you should mix all ingredients thoroughly."
        result = handle_user_intent(Intent.CLARIFY, recipe, current_step_index=1)
        assert "mix all ingredients" in result["message"].lower()
        assert result["step_index"] == 1
        # Verify that clarify_step was called via souschef_llm_call
        mock_llm_call.assert_called_once()
    
    def test_repair_handler(self, recipe):
        """Test repair intent handling"""
        result = handle_user_intent(Intent.REPAIR, recipe, current_step_index=1)
        assert "confusion" in result["message"].lower() or "carefully" in result["message"].lower()
        assert result["step_index"] == 1