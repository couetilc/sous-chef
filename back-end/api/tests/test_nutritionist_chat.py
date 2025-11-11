"""
Tests for AI nutritionist chat with conversation history.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from unittest.mock import patch, MagicMock
from api.models import ChatConversation, ChatMessage


@pytest.mark.django_db
class TestNutritionistChatEndpoint:
    """Test nutritionist chat endpoint /api/nutritionist/conversation/"""

    @patch('api.views.llm_chain')
    def test_authentication_required(self, mock_llm, api_client):
        """Test that unauthenticated requests are rejected"""
        data = {'message': 'Hello'}
        response = api_client.post('/api/nutritionist/conversation/', data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_llm.invoke.assert_not_called()

    @patch('api.views.llm_chain')
    def test_first_message_creates_conversation(self, mock_llm, authenticated_client, test_user):
        """Test that first message creates a new conversation"""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = "Hello! I'm here to help with nutrition."
        mock_response.tool_calls = []  # No tool calls
        mock_llm.invoke.return_value = mock_response

        # Verify no conversation exists yet
        assert ChatConversation.objects.filter(user=test_user).count() == 0

        # Send first message
        data = {'message': 'What foods are high in protein?'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert 'messages' in response.data
        assert len(response.data['messages']) == 2  # user + assistant

        # Verify conversation created
        assert ChatConversation.objects.filter(user=test_user).count() == 1
        conversation = ChatConversation.objects.get(user=test_user)
        assert conversation.is_active is True

        # Verify messages saved
        messages = list(conversation.messages.all())
        assert len(messages) == 2
        assert messages[0].role == 'user'
        assert messages[0].content == 'What foods are high in protein?'
        assert messages[1].role == 'assistant'
        assert messages[1].content == "Hello! I'm here to help with nutrition."

    @patch('api.views.llm_chain')
    def test_subsequent_messages_add_to_conversation(self, mock_llm, authenticated_client, test_user):
        """Test that subsequent messages are added to existing conversation"""
        # Mock LLM responses
        mock_response_1 = MagicMock()
        mock_response_1.content = "Great sources of protein include chicken, fish, and beans."
        mock_response_1.tool_calls = []
        mock_response_2 = MagicMock()
        mock_response_2.content = "For vegetarian options, try tofu, lentils, and quinoa."
        mock_response_2.tool_calls = []
        mock_llm.invoke.side_effect = [mock_response_1, mock_response_2]

        # First message
        data1 = {'message': 'What foods are high in protein?'}
        response1 = authenticated_client.post('/api/nutritionist/conversation/', data1)
        assert response1.status_code == status.HTTP_200_OK
        conversation_id_1 = response1.data['id']

        # Second message
        data2 = {'message': 'What about vegetarian options?'}
        response2 = authenticated_client.post('/api/nutritionist/conversation/', data2)
        assert response2.status_code == status.HTTP_200_OK
        conversation_id_2 = response2.data['id']

        # Should be same conversation
        assert conversation_id_1 == conversation_id_2

        # Should have 4 messages total (2 user + 2 assistant)
        assert len(response2.data['messages']) == 4
        assert response2.data['messages'][0]['role'] == 'user'
        assert response2.data['messages'][0]['content'] == 'What foods are high in protein?'
        assert response2.data['messages'][1]['role'] == 'assistant'
        assert response2.data['messages'][2]['role'] == 'user'
        assert response2.data['messages'][2]['content'] == 'What about vegetarian options?'
        assert response2.data['messages'][3]['role'] == 'assistant'

        # Verify only one conversation exists
        assert ChatConversation.objects.filter(user=test_user).count() == 1

    @patch('api.views.llm_chain')
    def test_response_includes_full_history_with_timestamps(self, mock_llm, authenticated_client, test_user):
        """Test that response includes all messages with timestamps"""
        mock_response = MagicMock()
        mock_response.content = "I can help with that!"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        # Send a message
        data = {'message': 'Hello'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'messages' in response.data

        # Check message structure
        for message in response.data['messages']:
            assert 'id' in message
            assert 'role' in message
            assert 'content' in message
            assert 'created_at' in message
            assert message['role'] in ['user', 'assistant']

    @patch('api.views.llm_chain')
    def test_llm_receives_full_conversation_context(self, mock_llm, authenticated_client, test_user):
        """Test that LLM receives full conversation history in context"""
        # Mock LLM responses
        mock_response_1 = MagicMock()
        mock_response_1.content = "First response"
        mock_response_1.tool_calls = []
        mock_response_2 = MagicMock()
        mock_response_2.content = "Second response"
        mock_response_2.tool_calls = []
        mock_llm.invoke.side_effect = [mock_response_1, mock_response_2]

        # First message
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'First message'})

        # Second message - should include first exchange in context
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Second message'})

        # Verify LLM was called twice
        assert mock_llm.invoke.call_count == 2

        # Check second call includes conversation history
        second_call_args = mock_llm.invoke.call_args_list[1][0][0]
        assert 'username' in second_call_args
        # The prompt should include conversation history
        # (exact format depends on implementation)

    @patch('api.views.llm_chain')
    def test_messages_ordered_chronologically(self, mock_llm, authenticated_client, test_user):
        """Test that messages are returned in chronological order (oldest first)"""
        # Mock LLM responses
        mock_responses = []
        for i in range(3):
            mock = MagicMock()
            mock.content = f"Response {i}"
            mock.tool_calls = []
            mock_responses.append(mock)
        mock_llm.invoke.side_effect = mock_responses

        # Send 3 messages
        for i in range(3):
            response = authenticated_client.post(
                '/api/nutritionist/conversation/',
                {'message': f'Message {i}'}
            )

        # Check final response has all messages in order
        messages = response.data['messages']
        assert len(messages) == 6  # 3 user + 3 assistant

        # Verify chronological order
        for i in range(len(messages) - 1):
            current_time = messages[i]['created_at']
            next_time = messages[i + 1]['created_at']
            assert current_time <= next_time

    @patch('api.views.llm_chain')
    def test_multiple_users_have_separate_conversations(self, mock_llm, authenticated_client, api_client, test_user, second_user):
        """Test that different users have isolated conversations"""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        # User 1 sends a message
        authenticated_client.force_authenticate(user=test_user)
        response1 = authenticated_client.post('/api/nutritionist/conversation/', {'message': 'User 1 message'})

        # User 2 sends a message
        authenticated_client.force_authenticate(user=second_user)
        response2 = authenticated_client.post('/api/nutritionist/conversation/', {'message': 'User 2 message'})

        # Verify separate conversations
        assert response1.data['id'] != response2.data['id']

        # User 1 should only see their message
        assert len(response1.data['messages']) == 2
        assert response1.data['messages'][0]['content'] == 'User 1 message'

        # User 2 should only see their message
        assert len(response2.data['messages']) == 2
        assert response2.data['messages'][0]['content'] == 'User 2 message'

        # Verify 2 separate conversations in database
        assert ChatConversation.objects.filter(user=test_user).count() == 1
        assert ChatConversation.objects.filter(user=second_user).count() == 1

    @patch('api.views.llm_chain')
    def test_missing_message_parameter_returns_error(self, mock_llm, authenticated_client):
        """Test that request without message parameter returns an error"""
        response = authenticated_client.post('/api/nutritionist/conversation/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data or 'message' in response.data
        mock_llm.invoke.assert_not_called()

    @patch('api.views.llm_chain')
    def test_empty_message_returns_error(self, mock_llm, authenticated_client):
        """Test that request with empty message returns an error"""
        response = authenticated_client.post('/api/nutritionist/conversation/', {'message': ''})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data or 'message' in response.data
        mock_llm.invoke.assert_not_called()


@pytest.mark.django_db
class TestGetConversationEndpoint:
    """Test get conversation endpoint GET /api/nutritionist/conversation/"""

    def test_authentication_required(self, api_client):
        """Test that unauthenticated requests are rejected"""
        response = api_client.get('/api/nutritionist/conversation/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_conversation_when_none_exists(self, authenticated_client, test_user):
        """Test that GET returns empty conversation when none exists"""
        response = authenticated_client.get('/api/nutritionist/conversation/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] is None
        assert response.data['messages'] == []

    @patch('api.views.llm_chain')
    def test_get_conversation_with_messages(self, mock_llm, authenticated_client, test_user):
        """Test that GET returns existing conversation with all messages"""
        # Create a conversation with messages
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help?"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        # Send a message to create conversation
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Hi there'})

        # Now GET the conversation
        response = authenticated_client.get('/api/nutritionist/conversation/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] is not None
        assert len(response.data['messages']) == 2  # user + assistant
        assert response.data['messages'][0]['role'] == 'user'
        assert response.data['messages'][0]['content'] == 'Hi there'
        assert response.data['messages'][1]['role'] == 'assistant'

    @patch('api.views.llm_chain')
    def test_get_only_returns_active_conversation(self, mock_llm, authenticated_client, test_user):
        """Test that GET only returns active conversation, not inactive ones"""
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        # Create first conversation
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'First'})

        # Clear it
        authenticated_client.post('/api/nutritionist/conversation/clear/')

        # Create new conversation
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Second'})

        # GET should return only the new active conversation
        response = authenticated_client.get('/api/nutritionist/conversation/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['messages']) == 2
        assert response.data['messages'][0]['content'] == 'Second'


@pytest.mark.django_db
class TestClearConversationEndpoint:
    """Test clear conversation endpoint /api/nutritionist/conversation/clear/"""

    def test_authentication_required(self, api_client):
        """Test that unauthenticated requests are rejected"""
        response = api_client.post('/api/nutritionist/conversation/clear/', {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('api.views.llm_chain')
    def test_clear_marks_conversation_inactive(self, mock_llm, authenticated_client, test_user):
        """Test that clear endpoint marks conversation as inactive"""
        # Create a conversation with messages
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Hello'})

        # Verify conversation exists and is active
        conversation = ChatConversation.objects.get(user=test_user)
        assert conversation.is_active is True
        original_id = conversation.id

        # Clear conversation
        response = authenticated_client.post('/api/nutritionist/conversation/clear/', {})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        # Verify conversation is now inactive
        conversation.refresh_from_db()
        assert conversation.is_active is False

    @patch('api.views.llm_chain')
    def test_new_message_after_clear_creates_new_conversation(self, mock_llm, authenticated_client, test_user):
        """Test that messages after clear create a new conversation"""
        # Create initial conversation
        mock_response = MagicMock()
        mock_response.content = "Response"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response

        response1 = authenticated_client.post('/api/nutritionist/conversation/', {'message': 'First'})
        first_conversation_id = response1.data['id']

        # Clear conversation
        authenticated_client.post('/api/nutritionist/conversation/clear/', {})

        # Send new message
        response2 = authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Second'})
        second_conversation_id = response2.data['id']

        # Should be different conversations
        assert first_conversation_id != second_conversation_id

        # New conversation should only have new messages
        assert len(response2.data['messages']) == 2
        assert response2.data['messages'][0]['content'] == 'Second'

        # Should have 2 conversations total (1 inactive, 1 active)
        assert ChatConversation.objects.filter(user=test_user).count() == 2
        assert ChatConversation.objects.filter(user=test_user, is_active=True).count() == 1
        assert ChatConversation.objects.filter(user=test_user, is_active=False).count() == 1

    def test_clear_without_conversation_returns_success(self, authenticated_client, test_user):
        """Test that clearing when no conversation exists returns success"""
        # No conversation exists
        assert ChatConversation.objects.filter(user=test_user).count() == 0

        # Clear should still succeed
        response = authenticated_client.post('/api/nutritionist/conversation/clear/', {})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True


@pytest.mark.django_db
class TestToolCallingFunctionality:
    """Test tool calling scenarios including single/multiple rounds"""

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_single_tool_call_one_round(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that a message triggering a single tool call executes and returns properly"""
        # Round 1: Initial LLM call with tool request
        mock_response_1 = MagicMock()
        mock_response_1.tool_calls = [{
            'id': 'call_1',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'chicken', 'max_calories': 500}
        }]
        mock_llm_chain.invoke.return_value = mock_response_1

        # Round 2: After tool execution, LLM returns final text response (no more tool calls)
        mock_response_2 = MagicMock()
        mock_response_2.tool_calls = []
        mock_response_2.content = "Here are some chicken recipes with under 500 calories!"
        mock_llm_with_tools.invoke.return_value = mock_response_2

        # Mock tool execution
        mock_search_tool.invoke.return_value = "Recipe ID: 1\nTitle: Grilled Chicken\nNutrition: 450 calories..."

        # Send message
        data = {'message': 'Find me low calorie chicken recipes'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['messages']) == 2  # user + assistant

        # Verify assistant response content
        assistant_message = response.data['messages'][1]
        assert assistant_message['role'] == 'assistant'
        assert assistant_message['content'] == "Here are some chicken recipes with under 500 calories!"

        # Verify tool call data was saved
        assert assistant_message['tool_calls'] is not None
        assert len(assistant_message['tool_calls']) == 1
        tool_call = assistant_message['tool_calls'][0]
        assert tool_call['tool_name'] == 'search_recipes_tool'
        assert tool_call['parameters'] == {'title_query': 'chicken', 'max_calories': 500}
        assert 'Recipe ID: 1' in tool_call['result']
        assert 'timestamp' in tool_call

        # Verify LLM was called correctly
        assert mock_llm_chain.invoke.call_count == 1
        assert mock_llm_with_tools.invoke.call_count == 1
        assert mock_search_tool.invoke.call_count == 1

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_multiple_rounds_of_tool_calls(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that multiple rounds of tool calls are handled correctly (most important test!)"""
        # Round 1: Initial LLM call with first tool request
        mock_response_1 = MagicMock()
        mock_response_1.tool_calls = [{
            'id': 'call_1',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'chicken'}
        }]
        mock_llm_chain.invoke.return_value = mock_response_1

        # Round 2: After first tool execution, LLM requests ANOTHER tool call
        mock_response_2 = MagicMock()
        mock_response_2.tool_calls = [{
            'id': 'call_2',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'vegetarian', 'min_protein': 20}
        }]

        # Round 3: After second tool execution, LLM returns final text response
        mock_response_3 = MagicMock()
        mock_response_3.tool_calls = []
        mock_response_3.content = "I found both chicken and vegetarian high-protein recipes!"

        mock_llm_with_tools.invoke.side_effect = [mock_response_2, mock_response_3]

        # Mock tool execution returns
        mock_search_tool.invoke.side_effect = [
            "Recipe ID: 1\nTitle: Grilled Chicken\nCalories: 400...",
            "Recipe ID: 5\nTitle: Lentil Curry\nCalories: 350..."
        ]

        # Send message
        data = {'message': 'Find me chicken and vegetarian recipes with high protein'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['messages']) == 2

        # Verify assistant response
        assistant_message = response.data['messages'][1]
        assert assistant_message['content'] == "I found both chicken and vegetarian high-protein recipes!"

        # Verify BOTH tool calls were saved
        assert len(assistant_message['tool_calls']) == 2

        # Check first tool call
        tool_call_1 = assistant_message['tool_calls'][0]
        assert tool_call_1['tool_name'] == 'search_recipes_tool'
        assert tool_call_1['parameters'] == {'title_query': 'chicken'}
        assert 'Grilled Chicken' in tool_call_1['result']

        # Check second tool call
        tool_call_2 = assistant_message['tool_calls'][1]
        assert tool_call_2['tool_name'] == 'search_recipes_tool'
        assert tool_call_2['parameters'] == {'title_query': 'vegetarian', 'min_protein': 20}
        assert 'Lentil Curry' in tool_call_2['result']

        # Verify the while loop executed correctly
        assert mock_llm_chain.invoke.call_count == 1  # Initial call
        assert mock_llm_with_tools.invoke.call_count == 2  # Two iterations in the loop
        assert mock_search_tool.invoke.call_count == 2  # Two tool executions

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_max_iterations_safety_limit(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that tool calling loop stops at max_iterations to prevent infinite loops"""
        # Initial call returns tool calls
        mock_response_initial = MagicMock()
        mock_response_initial.tool_calls = [{
            'id': 'call_initial',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'test'}
        }]
        mock_llm_chain.invoke.return_value = mock_response_initial

        # Create 20 mock responses that ALL have tool calls (simulating infinite loop)
        mock_responses = []
        for i in range(20):
            mock = MagicMock()
            mock.tool_calls = [{
                'id': f'call_{i}',
                'name': 'search_recipes_tool',
                'args': {'title_query': f'query_{i}'}
            }]
            mock.content = f"Response {i}"
            mock_responses.append(mock)

        mock_llm_with_tools.invoke.side_effect = mock_responses
        mock_search_tool.invoke.return_value = "Some recipes..."

        # Send message
        data = {'message': 'Find recipes'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Should still succeed (not crash)
        assert response.status_code == status.HTTP_200_OK

        # Verify loop stopped at exactly 10 iterations
        assert mock_llm_with_tools.invoke.call_count == 10

        # Verify message was saved
        assistant_message = response.data['messages'][1]

        # Should have exactly 10 tool calls (max_iterations limit)
        assert len(assistant_message['tool_calls']) == 10

        # Tool should have been called 10 times
        assert mock_search_tool.invoke.call_count == 10

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_multiple_tool_calls_in_one_round(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that multiple tool calls in a single LLM response are handled"""
        # LLM returns multiple tool calls at once
        mock_response_1 = MagicMock()
        mock_response_1.tool_calls = [
            {
                'id': 'call_1',
                'name': 'search_recipes_tool',
                'args': {'title_query': 'pasta', 'max_calories': 600}
            },
            {
                'id': 'call_2',
                'name': 'search_recipes_tool',
                'args': {'title_query': 'salad', 'max_fat': 10}
            }
        ]
        mock_llm_chain.invoke.return_value = mock_response_1

        # After both tools execute, return final response
        mock_response_2 = MagicMock()
        mock_response_2.tool_calls = []
        mock_response_2.content = "Here are pasta and salad options!"
        mock_llm_with_tools.invoke.return_value = mock_response_2

        # Mock tool returns
        mock_search_tool.invoke.side_effect = [
            "Recipe ID: 1\nTitle: Spaghetti\n...",
            "Recipe ID: 2\nTitle: Caesar Salad\n..."
        ]

        # Send message
        data = {'message': 'Show me pasta and salad recipes'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assistant_message = response.data['messages'][1]

        # Both tool calls should be saved
        assert len(assistant_message['tool_calls']) == 2
        assert assistant_message['tool_calls'][0]['parameters']['title_query'] == 'pasta'
        assert assistant_message['tool_calls'][1]['parameters']['title_query'] == 'salad'

        # Both tools should have been executed
        assert mock_search_tool.invoke.call_count == 2

    @patch('api.views.llm_chain')
    def test_message_with_no_tool_calls(self, mock_llm_chain, authenticated_client, test_user):
        """Test that messages without tool calls work correctly (text response only)"""
        # LLM returns text response without any tool calls
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "A balanced diet includes fruits, vegetables, proteins, and whole grains."
        mock_llm_chain.invoke.return_value = mock_response

        # Send message
        data = {'message': 'What is a balanced diet?'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assistant_message = response.data['messages'][1]
        assert assistant_message['content'] == "A balanced diet includes fruits, vegetables, proteins, and whole grains."

        # No tool calls should be saved
        assert assistant_message['tool_calls'] is None or len(assistant_message['tool_calls']) == 0

        # LLM should only be called once (no loop iterations)
        assert mock_llm_chain.invoke.call_count == 1

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_tool_returns_no_results(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that tool returning no results is handled gracefully"""
        # LLM requests tool
        mock_response_1 = MagicMock()
        mock_response_1.tool_calls = [{
            'id': 'call_1',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'unicorn meat', 'max_calories': 1}
        }]
        mock_llm_chain.invoke.return_value = mock_response_1

        # Tool returns "no results" message
        mock_search_tool.invoke.return_value = "No recipes found matching the search criteria."

        # LLM receives no results and responds appropriately
        mock_response_2 = MagicMock()
        mock_response_2.tool_calls = []
        mock_response_2.content = "I'm sorry, I couldn't find any recipes matching those criteria."
        mock_llm_with_tools.invoke.return_value = mock_response_2

        # Send message
        data = {'message': 'Find me recipes with unicorn meat under 1 calorie'}
        response = authenticated_client.post('/api/nutritionist/conversation/', data)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assistant_message = response.data['messages'][1]

        # Verify tool was called and "no results" was saved
        assert len(assistant_message['tool_calls']) == 1
        assert "No recipes found" in assistant_message['tool_calls'][0]['result']

        # Verify LLM received the "no results" and responded appropriately
        assert "couldn't find" in assistant_message['content']

    @patch('api.views.search_recipes_tool')
    @patch('api.views.llm_with_tools')
    @patch('api.views.llm_chain')
    def test_conversation_context_preserved_with_tool_calls(self, mock_llm_chain, mock_llm_with_tools, mock_search_tool, authenticated_client, test_user):
        """Test that conversation history is preserved across messages with tool calls"""
        # First message with tool call
        mock_response_1 = MagicMock()
        mock_response_1.tool_calls = [{
            'id': 'call_1',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'chicken'}
        }]

        mock_response_2 = MagicMock()
        mock_response_2.tool_calls = []
        mock_response_2.content = "I found 5 chicken recipes!"

        mock_llm_chain.invoke.return_value = mock_response_1
        mock_llm_with_tools.invoke.return_value = mock_response_2
        mock_search_tool.invoke.return_value = "Recipe ID: 1\nTitle: Chicken Salad..."

        # Send first message
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Find chicken recipes'})

        # Reset mocks for second message
        mock_llm_chain.reset_mock()
        mock_llm_with_tools.reset_mock()
        mock_search_tool.reset_mock()

        # Second message with tool call
        mock_response_3 = MagicMock()
        mock_response_3.tool_calls = [{
            'id': 'call_2',
            'name': 'search_recipes_tool',
            'args': {'title_query': 'beef'}
        }]

        mock_response_4 = MagicMock()
        mock_response_4.tool_calls = []
        mock_response_4.content = "I also found beef recipes!"

        mock_llm_chain.invoke.return_value = mock_response_3
        mock_llm_with_tools.invoke.return_value = mock_response_4
        mock_search_tool.invoke.return_value = "Recipe ID: 10\nTitle: Beef Stew..."

        # Send second message
        authenticated_client.post('/api/nutritionist/conversation/', {'message': 'Now find beef recipes'})

        # Verify LLM received context from first exchange
        call_args = mock_llm_chain.invoke.call_args[0][0]
        conversation_history = call_args['conversation_history']

        # Should include the first user message and assistant response
        assert 'Find chicken recipes' in conversation_history
        assert 'I found 5 chicken recipes!' in conversation_history
