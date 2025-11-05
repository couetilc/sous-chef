import pytest
from api.models import Diet

@pytest.mark.django_db
class TestDietAPI:
    def test_return_diet_list(self, authenticated_client):
        Diet.objects.create(name="foo")
        response = authenticated_client.get('/api/diets')
        print(response)

    def test_return_paged_diet(self, authenticated_client):
        for i in range(101):
            Diet.objects.create(name=f"foo{i}")
        response = authenticated_client.get('/api/diets')
        print(response)
