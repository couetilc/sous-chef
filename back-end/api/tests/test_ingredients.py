"""
Tests for ingredient endpoints: ingredient list and dietary restrictions.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import Ingredient, DietaryIngredient


@pytest.fixture
def test_ingredients(db):
    """Creates test ingredients"""
    ingredients = [
        Ingredient.objects.create(name='Milk'),
        Ingredient.objects.create(name='Eggs'),
        Ingredient.objects.create(name='Peanuts'),
        Ingredient.objects.create(name='Wheat'),
        Ingredient.objects.create(name='Soy'),
    ]
    return ingredients


@pytest.fixture
def second_user(db):
    """Creates a second test user"""
    return User.objects.create_user(
        username='user2',
        email='user2@example.com',
        password='pass123',
        first_name='User',
        last_name='Two'
    )


@pytest.fixture
def test_dietary_restrictions(db, test_user, second_user, test_ingredients):
    """Creates dietary restrictions for test users"""
    # test_user restricts Milk, Eggs, and Peanuts
    restrictions = [
        DietaryIngredient.objects.create(user=test_user, ingredient=test_ingredients[0]),  # Milk
        DietaryIngredient.objects.create(user=test_user, ingredient=test_ingredients[1]),  # Eggs
        DietaryIngredient.objects.create(user=test_user, ingredient=test_ingredients[2]),  # Peanuts
    ]

    # second_user restricts only Wheat
    DietaryIngredient.objects.create(user=second_user, ingredient=test_ingredients[3])  # Wheat

    return restrictions


@pytest.mark.django_db
class TestIngredientListEndpoint:
    """Test ingredient list endpoint /api/ingredients/"""

    def test_list_ingredients_requires_authentication(self, api_client, test_ingredients):
        """Test that unauthenticated requests are rejected"""
        response = api_client.get('/api/ingredients/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_all_ingredients(self, authenticated_client, test_ingredients):
        """Test that authenticated user can list all ingredients"""
        response = authenticated_client.get('/api/ingredients/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
        assert response.data['count'] == 5

        # Verify all ingredients are returned (ordered by name)
        ingredient_names = [item['name'] for item in response.data['results']]
        assert ingredient_names == ['Eggs', 'Milk', 'Peanuts', 'Soy', 'Wheat']

    def test_ingredient_serialization(self, authenticated_client, test_ingredients):
        """Test that ingredients are properly serialized with id and name"""
        response = authenticated_client.get('/api/ingredients/')

        assert response.status_code == status.HTTP_200_OK

        # Check that each ingredient has id and name fields
        for ingredient_data in response.data['results']:
            assert 'id' in ingredient_data
            assert 'name' in ingredient_data
            assert isinstance(ingredient_data['id'], int)
            assert isinstance(ingredient_data['name'], str)

    def test_empty_ingredient_list(self, authenticated_client):
        """Test that empty list is returned when no ingredients exist"""
        response = authenticated_client.get('/api/ingredients/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_ingredient_list_ordering(self, authenticated_client):
        """Test that ingredients are ordered alphabetically by name"""
        # Create ingredients out of alphabetical order
        Ingredient.objects.create(name='Zucchini')
        Ingredient.objects.create(name='Apple')
        Ingredient.objects.create(name='Mango')

        response = authenticated_client.get('/api/ingredients/')

        assert response.status_code == status.HTTP_200_OK
        ingredient_names = [item['name'] for item in response.data['results']]
        assert ingredient_names == ['Apple', 'Mango', 'Zucchini']


@pytest.mark.django_db
class TestDietaryIngredientListEndpoint:
    """Test dietary restriction list endpoint /api/ingredients/restricted/"""

    def test_restricted_ingredients_requires_authentication(self, api_client, test_dietary_restrictions):
        """Test that unauthenticated requests are rejected"""
        response = api_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_user_restricted_ingredients(self, authenticated_client, test_user, test_dietary_restrictions):
        """Test that user gets only their own restricted ingredients"""
        response = authenticated_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        # Verify correct ingredients are returned (ordered by name)
        ingredient_names = [item['name'] for item in response.data]
        assert ingredient_names == ['Eggs', 'Milk', 'Peanuts']

    def test_user_only_sees_own_restrictions(self, api_client, second_user, test_dietary_restrictions):
        """Test that users only see their own restrictions, not other users'"""
        # Authenticate as second_user
        api_client.force_authenticate(user=second_user)

        response = api_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        # second_user should only see Wheat
        ingredient_names = [item['name'] for item in response.data]
        assert ingredient_names == ['Wheat']

    def test_restricted_ingredient_serialization(self, authenticated_client, test_dietary_restrictions):
        """Test that restricted ingredients are properly serialized"""
        response = authenticated_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_200_OK

        # Check that each ingredient has id and name fields
        for ingredient_data in response.data:
            assert 'id' in ingredient_data
            assert 'name' in ingredient_data
            assert isinstance(ingredient_data['id'], int)
            assert isinstance(ingredient_data['name'], str)

    def test_empty_restricted_list(self, authenticated_client, test_user):
        """Test that empty list is returned when user has no restrictions"""
        # Create some ingredients but don't restrict any
        Ingredient.objects.create(name='Milk')
        Ingredient.objects.create(name='Eggs')

        response = authenticated_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0
        assert response.data == []

    def test_restricted_list_ordering(self, authenticated_client, test_user):
        """Test that restricted ingredients are ordered alphabetically"""
        # Create ingredients and restrictions out of order
        zucchini = Ingredient.objects.create(name='Zucchini')
        apple = Ingredient.objects.create(name='Apple')
        mango = Ingredient.objects.create(name='Mango')

        DietaryIngredient.objects.create(user=test_user, ingredient=zucchini)
        DietaryIngredient.objects.create(user=test_user, ingredient=apple)
        DietaryIngredient.objects.create(user=test_user, ingredient=mango)

        response = authenticated_client.get('/api/ingredients/restricted/')

        assert response.status_code == status.HTTP_200_OK
        ingredient_names = [item['name'] for item in response.data]
        assert ingredient_names == ['Apple', 'Mango', 'Zucchini']


@pytest.mark.django_db
class TestDietaryIngredientModelConstraints:
    """Test DietaryIngredient model constraints"""

    def test_unique_together_constraint(self, test_user, test_ingredients):
        """Test that a user cannot restrict the same ingredient twice"""
        milk = test_ingredients[0]

        # Create first restriction
        DietaryIngredient.objects.create(user=test_user, ingredient=milk)

        # Try to create duplicate restriction
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            DietaryIngredient.objects.create(user=test_user, ingredient=milk)

    def test_different_users_can_restrict_same_ingredient(self, test_user, second_user, test_ingredients):
        """Test that different users can restrict the same ingredient"""
        milk = test_ingredients[0]

        # Both users can restrict milk
        restriction1 = DietaryIngredient.objects.create(user=test_user, ingredient=milk)
        restriction2 = DietaryIngredient.objects.create(user=second_user, ingredient=milk)

        assert restriction1.id != restriction2.id
        assert DietaryIngredient.objects.count() == 2

    def test_user_can_restrict_multiple_ingredients(self, test_user, test_ingredients):
        """Test that a user can restrict multiple different ingredients"""
        restrictions = []
        for ingredient in test_ingredients[:3]:
            restriction = DietaryIngredient.objects.create(user=test_user, ingredient=ingredient)
            restrictions.append(restriction)

        assert len(restrictions) == 3
        assert DietaryIngredient.objects.filter(user=test_user).count() == 3

    def test_dietary_ingredient_string_representation(self, test_user, test_ingredients):
        """Test the __str__ method of DietaryIngredient"""
        milk = test_ingredients[0]
        restriction = DietaryIngredient.objects.create(user=test_user, ingredient=milk)

        expected_str = f"{test_user.username} restricts {milk.name}"
        assert str(restriction) == expected_str

    def test_cascade_delete_user(self, test_user, test_ingredients):
        """Test that restrictions are deleted when user is deleted"""
        milk = test_ingredients[0]
        DietaryIngredient.objects.create(user=test_user, ingredient=milk)

        assert DietaryIngredient.objects.count() == 1

        test_user.delete()

        assert DietaryIngredient.objects.count() == 0

    def test_cascade_delete_ingredient(self, test_user, test_ingredients):
        """Test that restrictions are deleted when ingredient is deleted"""
        milk = test_ingredients[0]
        DietaryIngredient.objects.create(user=test_user, ingredient=milk)

        assert DietaryIngredient.objects.count() == 1

        milk.delete()

        assert DietaryIngredient.objects.count() == 0


@pytest.mark.django_db
class TestIngredientEndpointsIntegration:
    """Test integration scenarios between the two endpoints"""

    def test_restricted_ingredients_subset_of_all_ingredients(
        self, authenticated_client, test_dietary_restrictions
    ):
        """Test that restricted ingredients are a subset of all ingredients"""
        # Get all ingredients
        all_response = authenticated_client.get('/api/ingredients/')
        all_ids = {item['id'] for item in all_response.data['results']}

        # Get restricted ingredients
        restricted_response = authenticated_client.get('/api/ingredients/restricted/')
        restricted_ids = {item['id'] for item in restricted_response.data}

        # Restricted should be a subset of all
        assert restricted_ids.issubset(all_ids)

    def test_endpoints_return_consistent_data_format(
        self, authenticated_client, test_dietary_restrictions
    ):
        """Test that both endpoints return data in the same format"""
        all_response = authenticated_client.get('/api/ingredients/')
        restricted_response = authenticated_client.get('/api/ingredients/restricted/')

        # Both should be lists
        assert isinstance(all_response.data['results'], list)
        assert isinstance(restricted_response.data, list)

        # If both have data, check structure matches
        if all_response.data and restricted_response.data:
            all_keys = set(all_response.data['results'][0].keys())
            restricted_keys = set(restricted_response.data[0].keys())
            assert all_keys == restricted_keys
            assert all_keys == {'id', 'name'}

@pytest.mark.django_db
class TestIngredientSearch:
    def test_ordered_by_name(self, authenticated_client):
        Ingredient.objects.create(name='foo')
        Ingredient.objects.create(name='bar')
        response = authenticated_client.get('/api/ingredients/')
        assert response.data['results'][0]['name'] == 'bar'
        assert response.data['results'][1]['name'] == 'foo'

    def test_search_by_ingredient_name(self, authenticated_client):
        Ingredient.objects.create(name='foo')
        Ingredient.objects.create(name='bar')

        response = authenticated_client.get('/api/ingredients/?search=foo')

        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
