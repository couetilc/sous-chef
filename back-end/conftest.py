"""
Pytest configuration and shared fixtures for the Django backend.
"""
import pytest
from django.contrib.auth.models import User, Group
from api.models import Recipe, CookedRecipe
from decimal import Decimal

@pytest.fixture
def api_client():
    """
    Provides a Django REST framework API client for testing.
    """
    from rest_framework.test import APIClient
    client = APIClient()
    client.default_format = 'json'
    return client


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

@pytest.fixture
def test_recipe(db):
    """Creates a test recipe with a defined total_servings."""
    return Recipe.objects.create(
        title='Test Recipe',
        ingredients='1 cup flour\n2 eggs',
        instructions='Mix and bake',
        # NEW: total servings defined on the base recipe
        servings=Decimal('4')
    )


@pytest.fixture
def second_user(db):
    """Creates a second test user"""
    return User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='pass123'
    )


@pytest.fixture
def test_cooked_recipe(db, test_user, test_recipe):
    """
    Creates a cooked recipe for test_user.

    Assumes CookedRecipe stores the total at cook time (copy from recipe)
    so history is immutable even if the recipe changes later.
    """
    return CookedRecipe.objects.create(
        user=test_user,
        recipe=test_recipe,
        # NEW: persist the servings snapshot on the cooked instance
        total_servings_cooked=test_recipe.servings
    )
