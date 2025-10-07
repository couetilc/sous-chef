"""
Pytest configuration and shared fixtures for the Django backend.
"""
import pytest
from django.contrib.auth.models import User, Group


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
def authenticated_client(api_client, test_user):
    """
    Provides an API client authenticated with session authentication.
    """
    api_client.force_authenticate(user=test_user)
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
