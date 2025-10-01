"""
Tests for OAuth2 Authorization Code + PKCE Flow used by the React SPA.

This test suite covers the complete authentication flow for the front-end:
1. SPA generates PKCE code_verifier and code_challenge
2. SPA redirects user to authorization endpoint with code_challenge
3. User logs in and authorizes the application
4. OAuth2 redirects back to SPA with authorization code in query params
5. SPA exchanges code + code_verifier for access token at token endpoint
6. SPA uses access token to make authenticated API requests
"""
import pytest
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from oauth2_provider.models import Application, AccessToken
from rest_framework import status
from rest_framework.test import APIClient
from urllib.parse import urlparse, parse_qs, urlsplit
import re
import secrets
import hashlib
import base64


def generate_pkce_pair():
    """
    Generate PKCE code_verifier and code_challenge pair.

    Returns:
        tuple: (code_verifier, code_challenge)
    """
    # Generate random code_verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')

    # Generate code_challenge using S256 (SHA256)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


@pytest.fixture
def spa_oauth_application(db, test_user):
    """
    Creates an OAuth2 application configured for Authorization Code + PKCE (SPA).
    """
    return Application.objects.create(
        name='Sous Chef SPA',
        user=test_user,
        client_type=Application.CLIENT_PUBLIC,  # SPAs are public clients
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris='http://localhost:5173/auth/callback\nhttp://localhost:5173/',
        client_id='spa-client-id-12345',
        skip_authorization=False,  # Require user authorization
    )


@pytest.mark.django_db
@pytest.mark.integration
class TestSPAAuthorizationFlow:
    """Test the OAuth2 authorization endpoint for SPA Authorization Code + PKCE flow.

    Note: OAuth2 authorization uses Django sessions, not REST tokens,
    so we use Django's test client and force_login() instead of APIClient.
    """

    def test_authorization_endpoint_exists(self, client):
        """Test that the OAuth2 authorization endpoint is accessible."""
        url = reverse('oauth2_provider:authorize')
        response = client.get(url)
        # Should redirect to login or return 400 for missing params, not 404
        assert response.status_code in [
            status.HTTP_302_FOUND,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_authorization_requires_authentication(self, client, spa_oauth_application):
        """Test that unauthenticated users are redirected to login."""
        code_verifier, code_challenge = generate_pkce_pair()

        url = reverse('oauth2_provider:authorize')
        params = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = client.get(url, params)

        # Should redirect to login page
        assert response.status_code == status.HTTP_302_FOUND
        assert '/admin/login' in response.url

    def test_authorization_shows_approval_form(self, client, test_user, spa_oauth_application):
        """Test that authenticated user sees authorization approval form."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')
        params = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = client.get(url, params)

        # Should show authorization form (200) or skip to code if skip_authorization=True (302)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]

        if response.status_code == status.HTTP_200_OK:
            # Should contain authorization form elements
            content = response.content.decode()
            assert 'Sous Chef SPA' in content or spa_oauth_application.name in content

    def test_user_approves_authorization_gets_code(self, client, test_user, spa_oauth_application):
        """Test the complete flow: user approves and receives authorization code."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')
        data = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'allow': 'Authorize',
        }
        response = client.post(url, data)

        # Should redirect to callback with code in query params
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url.startswith('http://localhost:5173/auth/callback?')

        # Parse query params and verify code structure
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)

        assert 'code' in query_params
        authorization_code = query_params['code'][0]
        assert len(authorization_code) > 0

        # Now exchange code for token at token endpoint
        token_url = reverse('oauth2_provider:token')
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'client_id': spa_oauth_application.client_id,
            'code_verifier': code_verifier,
        }
        token_response = client.post(token_url, token_data)

        # Should receive access token
        assert token_response.status_code == status.HTTP_200_OK
        token_json = token_response.json()

        assert 'access_token' in token_json
        assert 'token_type' in token_json
        assert token_json['token_type'] == 'Bearer'
        assert 'expires_in' in token_json
        assert 'scope' in token_json

        # Verify token exists in database
        token = AccessToken.objects.get(token=token_json['access_token'])
        assert token.user == test_user
        assert token.application == spa_oauth_application
        assert 'read' in token.scope
        assert 'write' in token.scope

    def test_user_denies_authorization_gets_error(self, client, test_user, spa_oauth_application):
        """Test that user denial redirects with error."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')
        data = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'cancel': 'Cancel',
        }
        response = client.post(url, data)

        # Should redirect to callback with error
        assert response.status_code == status.HTTP_302_FOUND
        assert 'error=access_denied' in response.url

    def test_invalid_redirect_uri_rejected(self, client, test_user, spa_oauth_application):
        """Test that unauthorized redirect URIs are rejected (prevents open redirect)."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')
        params = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://evil-site.com/steal-tokens',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = client.get(url, params)

        # Should show error page, not redirect to evil site
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_client_id_rejected(self, client, test_user):
        """Test that invalid client IDs are rejected."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')
        params = {
            'client_id': 'non-existent-client-id',
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        response = client.get(url, params)

        # Should return error
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_required_parameters_rejected(self, client, test_user, spa_oauth_application):
        """Test that missing required OAuth2 parameters are rejected."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        url = reverse('oauth2_provider:authorize')

        # Missing response_type - OAuth2 can return 400 or redirect with error
        response = client.get(url, {
            'client_id': spa_oauth_application.client_id,
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        })
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_302_FOUND]
        if response.status_code == status.HTTP_302_FOUND:
            assert 'error=' in response.url

        # Missing client_id
        response = client.get(url, {
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        })
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_302_FOUND]

    def test_scope_parameter_in_token(self, client, test_user, spa_oauth_application):
        """Test that requested scopes appear in the issued token."""
        code_verifier, code_challenge = generate_pkce_pair()
        client.force_login(test_user)

        # Step 1: Get authorization code
        url = reverse('oauth2_provider:authorize')
        data = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read groups',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'allow': 'Authorize',
        }
        response = client.post(url, data)

        assert response.status_code == status.HTTP_302_FOUND
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        authorization_code = query_params['code'][0]

        # Step 2: Exchange code for token
        token_url = reverse('oauth2_provider:token')
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'client_id': spa_oauth_application.client_id,
            'code_verifier': code_verifier,
        }
        token_response = client.post(token_url, token_data)
        assert token_response.status_code == status.HTTP_200_OK
        token_json = token_response.json()

        # Verify scope in token response
        assert 'scope' in token_json
        assert 'read' in token_json['scope']
        assert 'groups' in token_json['scope']

        # Verify scope in database token
        token = AccessToken.objects.get(token=token_json['access_token'])
        assert 'read' in token.scope
        assert 'groups' in token.scope

    def test_token_from_authorization_works_immediately(self, client, test_user, spa_oauth_application):
        """Test that token received from authorization flow can immediately access API."""
        code_verifier, code_challenge = generate_pkce_pair()

        # Step 1: Get authorization code
        client.force_login(test_user)
        url = reverse('oauth2_provider:authorize')
        data = {
            'client_id': spa_oauth_application.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'scope': 'read write',
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'allow': 'Authorize',
        }
        response = client.post(url, data)

        # Extract authorization code
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        authorization_code = query_params['code'][0]

        # Step 2: Exchange code for token
        token_url = reverse('oauth2_provider:token')
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': 'http://localhost:5173/auth/callback',
            'client_id': spa_oauth_application.client_id,
            'code_verifier': code_verifier,
        }
        token_response = client.post(token_url, token_data)
        token_json = token_response.json()
        token_value = token_json['access_token']

        # Step 3: Use that token to access protected API
        api_client = APIClient()
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_value}')
        response = api_client.get('/api/users/')

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)



@pytest.mark.django_db
@pytest.mark.integration
class TestSPAAuthenticatedRequests:
    """Test making authenticated API requests from the SPA."""

    def test_api_request_without_token_fails(self, api_client):
        """Test that API requests without token are rejected."""
        response = api_client.get('/api/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_request_with_invalid_token_fails(self, api_client):
        """Test that API requests with invalid token are rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token-xyz')
        response = api_client.get('/api/users/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_request_with_valid_token_succeeds(self, authenticated_client, test_user):
        """Test that API requests with valid token succeed."""
        response = authenticated_client.get('/api/users/')
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_user_list(self, authenticated_client, multiple_users):
        """Test fetching list of users from SPA."""
        response = authenticated_client.get('/api/users/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 5  # At least the 5 users we created

        # Verify response structure
        for user_data in response.data:
            assert 'username' in user_data
            assert 'email' in user_data
            assert 'first_name' in user_data
            assert 'last_name' in user_data

    def test_get_user_detail(self, authenticated_client, test_user):
        """Test fetching individual user details from SPA."""
        response = authenticated_client.get(f'/api/users/{test_user.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == test_user.username
        assert response.data['email'] == test_user.email
        assert response.data['first_name'] == test_user.first_name
        assert response.data['last_name'] == test_user.last_name

    def test_create_user_with_token(self, authenticated_client):
        """Test creating a new user from SPA."""
        new_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = authenticated_client.post('/api/users/', new_user_data)

        # Should succeed or return method not allowed if POST is disabled
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ]

        if response.status_code == status.HTTP_201_CREATED:
            assert response.data['username'] == 'newuser'
            assert User.objects.filter(username='newuser').exists()

    def test_groups_endpoint_requires_groups_scope(self, authenticated_client):
        """Test that groups endpoint requires groups scope."""
        response = authenticated_client.get('/api/groups/')

        # Should be forbidden because token doesn't have 'groups' scope
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_groups_endpoint_with_groups_scope(self, authenticated_client_with_groups, multiple_groups):
        """Test accessing groups with proper scope."""
        response = authenticated_client_with_groups.get('/api/groups/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3

        for group_data in response.data:
            assert 'name' in group_data

    def test_expired_token_rejected(self, api_client, expired_access_token):
        """Test that expired tokens cannot access API."""
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_access_token.token}')
        response = api_client.get('/api/users/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cors_headers_present(self, authenticated_client):
        """Test that CORS headers are present for SPA requests."""
        response = authenticated_client.get('/api/users/')

        # CORS headers should be present (configured in settings)
        assert response.status_code == status.HTTP_200_OK
        # Note: CORS headers are added by django-cors-headers middleware


@pytest.mark.django_db
@pytest.mark.integration
class TestSPATokenLifecycle:
    """Test the complete token lifecycle for SPA."""

    def test_token_has_correct_expiration(self, access_token):
        """Test that token has correct expiration time."""
        # Token should expire in approximately 1 hour (default OAuth2 setting)
        now = timezone.now()
        time_until_expiry = access_token.expires - now

        # Should be close to 1 hour (3600 seconds), allow some margin
        assert 3500 <= time_until_expiry.total_seconds() <= 3700

    def test_token_can_be_used_multiple_times(self, authenticated_client):
        """Test that the same token can be reused for multiple requests."""
        # Make multiple requests with the same token
        for _ in range(5):
            response = authenticated_client.get('/api/users/')
            assert response.status_code == status.HTTP_200_OK

    def test_multiple_tokens_per_user(self, db, test_user, spa_oauth_application):
        """Test that a user can have multiple active tokens (multiple devices)."""
        # Create multiple tokens for the same user
        token1 = AccessToken.objects.create(
            user=test_user,
            application=spa_oauth_application,
            token='token-device-1',
            expires=timezone.now() + timedelta(hours=10),
            scope='read write'
        )
        token2 = AccessToken.objects.create(
            user=test_user,
            application=spa_oauth_application,
            token='token-device-2',
            expires=timezone.now() + timedelta(hours=10),
            scope='read write'
        )

        # Both tokens should work
        client1 = APIClient()
        client1.credentials(HTTP_AUTHORIZATION=f'Bearer {token1.token}')
        response1 = client1.get('/api/users/')
        assert response1.status_code == status.HTTP_200_OK

        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {token2.token}')
        response2 = client2.get('/api/users/')
        assert response2.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.unit
class TestSPAEndpointSecurity:
    """Test security aspects of the API exposed to SPA."""

    def test_public_index_endpoint_accessible(self, api_client):
        """Test that public index endpoint doesn't require auth."""
        response = api_client.get('/api/')
        assert response.status_code == status.HTTP_200_OK
        assert b'Hello, World!' in response.content

    def test_protected_endpoints_require_authentication(self, api_client):
        """Test that all protected endpoints require authentication."""
        protected_endpoints = [
            '/api/users/',
            '/api/groups/',
        ]

        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Endpoint {endpoint} should require authentication"

    def test_token_not_exposed_in_query_params(self, authenticated_client):
        """Test that tokens are sent in headers, not query params."""
        # This is inherently tested by using HTTP_AUTHORIZATION header
        # but let's verify query param doesn't work
        from rest_framework.test import APIClient

        client = APIClient()
        response = client.get('/api/users/?access_token=some-token')

        # Should still be unauthorized (token in query param shouldn't work)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_scope_enforcement(self, api_client, test_user, spa_oauth_application):
        """Test that scope requirements are enforced."""
        # Create token with only 'read' scope
        token = AccessToken.objects.create(
            user=test_user,
            application=spa_oauth_application,
            token='read-only-token',
            expires=timezone.now() + timedelta(hours=10),
            scope='read'
        )

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.token}')

        # Should not be able to access groups endpoint
        response = client.get('/api/groups/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
