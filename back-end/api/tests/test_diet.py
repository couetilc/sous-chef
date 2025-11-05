import pytest
from api.models import Diet, UserDiet

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
