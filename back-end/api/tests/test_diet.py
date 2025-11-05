import pytest
from api.models import Diet, UserDiet
from rest_framework import status

@pytest.mark.django_db
class TestDietAPI:
    def test_return_diet_list(self, authenticated_client):
        Diet.objects.create(name="foo")
        Diet.objects.create(name="bar")
        response = authenticated_client.get('/api/diets/')
        assert len(response.data) == 2

    def test_diet_list_marked_by_chosen(self, authenticated_client, test_user):
        foo = Diet.objects.create(name="foo")
        bar = Diet.objects.create(name="bar")
        UserDiet.objects.create(user=test_user, diet=bar)

        response = authenticated_client.get('/api/diets/')

        assert all('is_restricted' in i for i in response.data)
        assert False == next(
            i['is_restricted'] for i in response.data if i['id'] == foo.id
        )
        assert True == next(
            i['is_restricted'] for i in response.data if i['id'] == bar.id
        )

@pytest.mark.django_db
class TestDietSyncAPI:
    def test_diet_ids_are_list(self, authenticated_client):
        response = authenticated_client.post('/api/diets/sync/', {
            'diet_ids': 1,
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_diet_ids_are_valid(self, authenticated_client):
        foo = Diet.objects.create(name="foo")
        response = authenticated_client.post('/api/diets/sync/', {
            'diet_ids': [foo.id + 1],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_user_diet_is_created(self, authenticated_client):
        foo = Diet.objects.create(name="foo")
        response = authenticated_client.post('/api/diets/sync/', {
            'diet_ids': [foo.id]
        })
        assert response.status_code == status.HTTP_200_OK
        assert UserDiet.objects.last().diet_id == foo.id

    def test_user_diet_is_deleted(self, authenticated_client, test_user):
        foo =Diet.objects.create(name="foo")
        UserDiet.objects.create(diet=foo, user=test_user)
        response = authenticated_client.post('/api/diets/sync/', {
            'diet_ids': []
        })
        assert response.status_code == status.HTTP_200_OK
        assert UserDiet.objects.all().count() == 0

    def test_user_diet_is_synced(self, authenticated_client, test_user):
        foo = Diet.objects.create(name="foo")
        bar = Diet.objects.create(name="bar")
        UserDiet.objects.create(diet=foo, user=test_user)

        response = authenticated_client.post('/api/diets/sync/', {
            'diet_ids': [bar.id],
        })

        assert response.status_code == status.HTTP_200_OK
        assert UserDiet.objects.all().count() == 1
        assert UserDiet.objects.last().diet_id == bar.id
