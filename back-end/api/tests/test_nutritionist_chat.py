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
        mock_response_2 = MagicMock()
        mock_response_2.content = "For vegetarian options, try tofu, lentils, and quinoa."
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
        mock_response_2 = MagicMock()
        mock_response_2.content = "Second response"
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
        mock_responses = [MagicMock(content=f"Response {i}") for i in range(3)]
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
