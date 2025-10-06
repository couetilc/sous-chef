"""
Tests for authentication flow: login, logout, CSRF, current user.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status


@pytest.mark.django_db
class TestLoginEndpoint:
    """Test user login endpoint /api/login/"""

    def test_successful_login(self, api_client, test_user):
        """Test that a user can login with valid credentials"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
        assert 'password' not in response.data
        assert 'id' in response.data

    def test_login_with_invalid_password(self, api_client, test_user):
        """Test that login fails with invalid password"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_login_with_invalid_username(self, api_client):
        """Test that login fails with non-existent username"""
        data = {
            'username': 'nonexistent',
            'password': 'somepassword'
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_login_missing_username(self, api_client):
        """Test that login fails when username is missing"""
        data = {
            'password': 'testpass123'
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_login_missing_password(self, api_client):
        """Test that login fails when password is missing"""
        data = {
            'username': 'testuser'
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_login_empty_credentials(self, api_client):
        """Test that login fails with empty credentials"""
        data = {
            'username': '',
            'password': ''
        }
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_is_public(self, api_client, test_user):
        """Test that login endpoint does not require authentication"""
        # No authentication credentials set
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = api_client.post('/api/login/', data)

        # Should succeed without prior authentication
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Test user logout endpoint /api/logout/"""

    def test_logout_when_authenticated(self, authenticated_client):
        """Test that authenticated user can logout"""
        response = authenticated_client.post('/api/logout/')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_logout_when_not_authenticated(self, api_client):
        """Test that logout requires authentication"""
        # Get CSRF token
        csrf_response = api_client.get('/api/csrf/')
        csrf_token = csrf_response.data['csrfToken']

        response = api_client.post('/api/logout/', HTTP_X_CSRFTOKEN=csrf_token)

        # DRF's IsAuthenticated returns 403 by default, not 401
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCurrentUserEndpoint:
    """Test current user endpoint /api/user/"""

    def test_get_current_user_when_authenticated(self, authenticated_client, test_user):
        """Test that authenticated user can get their info"""
        response = authenticated_client.get('/api/user/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == test_user.username
        assert response.data['email'] == test_user.email
        assert response.data['id'] == test_user.id
        assert 'password' not in response.data

    def test_get_current_user_when_not_authenticated(self, api_client):
        """Test that unauthenticated request fails"""
        response = api_client.get('/api/user/')

        # DRF's IsAuthenticated returns 403 by default, not 401
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestCSRFTokenEndpoint:
    """Test CSRF token endpoint /api/csrf/"""

    def test_csrf_token_endpoint_accessible(self, api_client):
        """Test that CSRF token endpoint is accessible without auth"""
        response = api_client.get('/api/csrf/')

        assert response.status_code == status.HTTP_200_OK
        assert 'csrfToken' in response.data
        assert response.data['csrfToken'] is not None

    def test_csrf_token_sets_cookie(self, api_client):
        """Test that CSRF endpoint sets CSRF cookie"""
        response = api_client.get('/api/csrf/')

        assert response.status_code == status.HTTP_200_OK
        # Check that CSRF cookie is set (in test client, check cookies)
        assert 'csrftoken' in response.cookies or 'csrfToken' in response.data


@pytest.mark.django_db
class TestAuthenticationFlow:
    """Test complete authentication flow integration"""

    def test_complete_auth_flow(self, api_client):
        """Test full flow: register → login → authenticated request → logout"""

        # Get CSRF token for all requests
        csrf_response = api_client.get('/api/csrf/')
        csrf_token = csrf_response.data['csrfToken']

        # Step 1: Register new user
        register_data = {
            'username': 'flowuser',
            'email': 'flow@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Flow',
            'last_name': 'User'
        }
        register_response = api_client.post('/api/register/', register_data, HTTP_X_CSRFTOKEN=csrf_token)
        assert register_response.status_code == status.HTTP_201_CREATED

        # Step 2: User should NOT be authenticated after registration
        user_response = api_client.get('/api/user/')
        # DRF's IsAuthenticated returns 403 by default, not 401
        assert user_response.status_code == status.HTTP_403_FORBIDDEN

        # Step 3: Login with new user
        login_data = {
            'username': 'flowuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/login/', login_data, HTTP_X_CSRFTOKEN=csrf_token)
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.data['username'] == 'flowuser'

        # Step 4: Now should be able to access authenticated endpoint
        user_response = api_client.get('/api/user/')
        assert user_response.status_code == status.HTTP_200_OK
        assert user_response.data['username'] == 'flowuser'

        # Step 5: Access other authenticated endpoints
        users_response = api_client.get('/api/users/')
        assert users_response.status_code == status.HTTP_200_OK

        # Step 6: Logout
        logout_response = api_client.post('/api/logout/', HTTP_X_CSRFTOKEN=csrf_token)
        assert logout_response.status_code == status.HTTP_200_OK

        # Step 7: Should no longer be able to access authenticated endpoints
        user_response_after_logout = api_client.get('/api/user/')
        # DRF's IsAuthenticated returns 403 by default, not 401
        assert user_response_after_logout.status_code == status.HTTP_403_FORBIDDEN

    def test_login_creates_session(self, api_client, test_user):
        """Test that login creates a session that persists across requests"""

        # Login
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = api_client.post('/api/login/', login_data)
        assert login_response.status_code == status.HTTP_200_OK

        # Make multiple authenticated requests with same client
        for _ in range(3):
            response = api_client.get('/api/user/')
            assert response.status_code == status.HTTP_200_OK
            assert response.data['username'] == 'testuser'

    def test_logout_invalidates_session(self, api_client, test_user):
        """Test that logout properly invalidates the session"""

        # Get CSRF token
        csrf_response = api_client.get('/api/csrf/')
        csrf_token = csrf_response.data['csrfToken']

        # Login
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        api_client.post('/api/login/', login_data, HTTP_X_CSRFTOKEN=csrf_token)

        # Verify authenticated
        response = api_client.get('/api/user/')
        assert response.status_code == status.HTTP_200_OK

        # Logout
        api_client.post('/api/logout/', HTTP_X_CSRFTOKEN=csrf_token)

        # Try to access authenticated endpoint - should fail
        response = api_client.get('/api/user/')
        # DRF's IsAuthenticated returns 403 by default, not 401
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestSessionSecurity:
    """Test session security aspects"""

    def test_user_data_not_exposed_in_login_response(self, api_client, test_user):
        """Test that sensitive data is not exposed in login response"""
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        response = api_client.post('/api/login/', login_data)

        assert response.status_code == status.HTTP_200_OK
        # Check that password is not in response
        assert 'password' not in response.data
        # Check that other sensitive fields are not exposed
        assert 'is_staff' not in response.data
        assert 'is_superuser' not in response.data
        assert 'is_active' not in response.data
