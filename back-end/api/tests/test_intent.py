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


@pytest.mark.django_db
class TestCookingSessionIntegration:
    """Test CookingSession integration with intent handling"""

    @pytest.fixture
    def user(self):
        """Create a test user"""
        return User.objects.create_user(username='testuser', password='testpass123')

    @pytest.fixture
    def recipe(self):
        """Create a test recipe"""
        return Recipe.objects.create(
            title='Test Recipe',
            ingredients='Ingredient 1|Ingredient 2',
            instructions='Step 1: Do this|Step 2: Do that|Step 3: Finish',
            servings=2,
            prep_time_min=10,
            cook_time_min=20,
            total_time_min=30
        )

    @pytest.fixture
    def cooking_session(self, user, recipe):
        """Create a test cooking session"""
        from api.models import CookingSession
        return CookingSession.objects.create(
            user=user,
            recipe=recipe,
            current_step_index=0,
            is_active=True
        )

    def test_cooking_session_next_step(self, cooking_session):
        """Test moving to next step with CookingSession"""
        result = handle_user_intent(Intent.NEXT_STEP, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 1
        assert result["step_index"] == 1
        assert "next step" in result["message"].lower()

    def test_cooking_session_previous_step(self, cooking_session):
        """Test moving to previous step with CookingSession"""
        cooking_session.current_step_index = 2
        cooking_session.save()
        
        result = handle_user_intent(Intent.PREVIOUS_STEP, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 1
        assert result["step_index"] == 1
        assert "previous step" in result["message"].lower()

    def test_cooking_session_restart(self, cooking_session):
        """Test restarting recipe with CookingSession"""
        cooking_session.current_step_index = 2
        cooking_session.save()
        
        result = handle_user_intent(Intent.RESTART_RECIPE, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 0
        assert result["step_index"] == 0
        assert "restarting" in result["message"].lower()

    def test_cooking_session_get_current_step(self, cooking_session):
        """Test getting current step text"""
        current_step = cooking_session.get_current_step()
        assert current_step == "Step 1: Do this"
        
        cooking_session.current_step_index = 1
        cooking_session.save()
        current_step = cooking_session.get_current_step()
        assert current_step == "Step 2: Do that"

    def test_cooking_session_get_steps_list(self, cooking_session):
        """Test parsing instructions into steps list"""
        steps = cooking_session.get_steps_list()
        assert len(steps) == 3
        assert steps[0] == "Step 1: Do this"
        assert steps[1] == "Step 2: Do that"
        assert steps[2] == "Step 3: Finish"

    def test_cooking_session_next_step_at_end(self, cooking_session):
        """Test that next_step at end stays at last step"""
        cooking_session.current_step_index = 2
        cooking_session.save()
        
        result = handle_user_intent(Intent.NEXT_STEP, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 2
        assert result["step_index"] == 2

    def test_cooking_session_previous_step_at_beginning(self, cooking_session):
        """Test that previous_step at beginning stays at first step"""
        result = handle_user_intent(Intent.PREVIOUS_STEP, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 0
        assert result["step_index"] == 0

    @patch('api.ai.souschef_llm_call')
    def test_cooking_session_clarify(self, mock_llm_call, cooking_session):
        """Test clarifying current step with CookingSession"""
        mock_llm_call.return_value = "This means you should do this carefully."
        
        result = handle_user_intent(Intent.CLARIFY, cooking_session)
        cooking_session.refresh_from_db()
        
        assert cooking_session.current_step_index == 0  # Should stay at same step
        assert result["step_index"] == 0
        assert "carefully" in result["message"].lower()
        mock_llm_call.assert_called_once()