"""
Tests for user registration endpoint.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration endpoint /api/register/"""

    def test_successful_registration(self, api_client):
        """Test that a new user can register successfully"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'newuser'
        assert response.data['email'] == 'newuser@example.com'
        assert response.data['first_name'] == 'New'
        assert response.data['last_name'] == 'User'
        assert 'password' not in response.data

        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.check_password('SecurePass123!')

    def test_registration_without_optional_fields(self, api_client):
        """Test registration with only required fields"""
        data = {
            'username': 'minimaluser',
            'email': 'minimal@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['username'] == 'minimaluser'
        assert response.data['email'] == 'minimal@example.com'
        assert response.data['first_name'] == ''
        assert response.data['last_name'] == ''

    def test_duplicate_username_rejected(self, api_client, test_user):
        """Test that duplicate usernames are rejected"""
        data = {
            'username': 'testuser',  # This user already exists
            'email': 'different@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_duplicate_email_rejected(self, api_client, test_user):
        """Test that duplicate emails are rejected"""
        data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # This email already exists
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data
        assert 'already exists' in str(response.data['email']).lower()

    def test_password_mismatch_rejected(self, api_client):
        """Test that mismatched passwords are rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data or 'non_field_errors' in response.data

    def test_weak_password_rejected(self, api_client):
        """Test that weak passwords are rejected"""
        # Test too short password
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
            'password_confirm': 'short'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_common_password_rejected(self, api_client):
        """Test that common passwords are rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_numeric_password_rejected(self, api_client):
        """Test that entirely numeric passwords are rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '12345678',
            'password_confirm': '12345678'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_missing_username_rejected(self, api_client):
        """Test that missing username is rejected"""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_missing_email_rejected(self, api_client):
        """Test that missing email is rejected"""
        data = {
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_missing_password_rejected(self, api_client):
        """Test that missing password is rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_missing_password_confirm_rejected(self, api_client):
        """Test that missing password confirmation is rejected"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password_confirm' in response.data

    def test_registration_is_public(self, api_client):
        """Test that registration endpoint does not require authentication"""
        # No authentication credentials set
        data = {
            'username': 'publicuser',
            'email': 'public@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        # Should succeed without authentication
        assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_email_format_rejected(self, api_client):
        """Test that invalid email format is rejected"""
        data = {
            'username': 'newuser',
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_password_is_hashed(self, api_client):
        """Test that password is properly hashed in database"""
        data = {
            'username': 'secureuser',
            'email': 'secure@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }
        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_201_CREATED

        # Retrieve user from database
        user = User.objects.get(username='secureuser')

        # Password should not be stored in plain text
        assert user.password != 'SecurePass123!'
        # Password should be hashed (starts with algorithm identifier)
        assert user.password.startswith('pbkdf2_sha256$')
        # But should validate correctly
        assert user.check_password('SecurePass123!')

    def test_cannot_set_is_staff_via_api(self, api_client):
        """Test that is_staff cannot be set to True through the registration API"""
        data = {
            'username': 'attacker',
            'email': 'attacker@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'is_staff': True
        }
        response = api_client.post('/api/register/', data)

        # Should either succeed with is_staff=False or reject the field
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(username='attacker')
            assert user.is_staff is False
        else:
            # If rejected, that's also acceptable
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_set_is_superuser_via_api(self, api_client):
        """Test that is_superuser cannot be set to True through the registration API"""
        data = {
            'username': 'attacker2',
            'email': 'attacker2@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'is_superuser': True
        }
        response = api_client.post('/api/register/', data)

        # Should either succeed with is_superuser=False or reject the field
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(username='attacker2')
            assert user.is_superuser is False
        else:
            # If rejected, that's also acceptable
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_set_admin_privileges_via_api(self, api_client):
        """Test that admin privileges cannot be escalated through registration"""
        data = {
            'username': 'attacker3',
            'email': 'attacker3@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
        response = api_client.post('/api/register/', data)

        # Regardless of response status, verify user doesn't have admin privileges
        if response.status_code == status.HTTP_201_CREATED:
            user = User.objects.get(username='attacker3')
            assert user.is_staff is False
            assert user.is_superuser is False
            # is_active should be True by default, that's fine
            assert user.is_active is True
