"""
Pytest configuration and shared fixtures for the Django backend.
"""
import pytest
from django.contrib.auth.models import User, Group
from oauth2_provider.models import Application, AccessToken
from datetime import timedelta
from django.utils import timezone


@pytest.fixture
def api_client():
    """
    Provides a Django REST framework API client for testing.
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def test_user(db):
    """
    Creates a test user.
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def test_superuser(db):
    """
    Creates a test superuser.
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def test_group(db):
    """
    Creates a test group.
    """
    return Group.objects.create(name='Test Group')


@pytest.fixture
def oauth_application(db, test_user):
    """
    Creates an OAuth2 application for testing.
    """
    return Application.objects.create(
        name='Test Application',
        user=test_user,
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
        client_id='test-client-id',
        client_secret='test-client-secret'
    )


@pytest.fixture
def access_token(db, test_user, oauth_application):
    """
    Creates an OAuth2 access token with read/write scope.
    """
    return AccessToken.objects.create(
        user=test_user,
        application=oauth_application,
        token='test-access-token-12345',
        expires=timezone.now() + timedelta(hours=1),
        scope='read write'
    )


@pytest.fixture
def access_token_with_groups_scope(db, test_user, oauth_application):
    """
    Creates an OAuth2 access token with groups scope.
    """
    return AccessToken.objects.create(
        user=test_user,
        application=oauth_application,
        token='test-access-token-groups-67890',
        expires=timezone.now() + timedelta(hours=1),
        scope='read write groups'
    )


@pytest.fixture
def expired_access_token(db, test_user, oauth_application):
    """
    Creates an expired OAuth2 access token.
    """
    return AccessToken.objects.create(
        user=test_user,
        application=oauth_application,
        token='expired-token-12345',
        expires=timezone.now() - timedelta(hours=1),
        scope='read write'
    )


@pytest.fixture
def authenticated_client(api_client, access_token):
    """
    Provides an API client authenticated with OAuth2 token.
    """
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token.token}')
    return api_client


@pytest.fixture
def authenticated_client_with_groups(api_client, access_token_with_groups_scope):
    """
    Provides an API client authenticated with OAuth2 token including groups scope.
    """
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token_with_groups_scope.token}')
    return api_client


@pytest.fixture
def multiple_users(db):
    """
    Creates multiple test users for list testing.
    """
    users = []
    for i in range(5):
        user = User.objects.create_user(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password=f'pass{i}123',
            first_name=f'User{i}',
            last_name=f'Test{i}'
        )
        users.append(user)
    return users


@pytest.fixture
def multiple_groups(db):
    """
    Creates multiple test groups for list testing.
    """
    groups = []
    for i in range(3):
        group = Group.objects.create(name=f'Group {i}')
        groups.append(group)
    return groups
