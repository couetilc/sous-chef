import pytest
from api.models import Tag, Recipe, TaggedRecipe
from rest_framework import status

@pytest.mark.django_db
class TestTagsAPI:
    def test_create_must_specify_name(self, authenticated_client):
        response = authenticated_client.post('/api/tags/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_create_tag(self, authenticated_client):
        assert Tag.objects.all().count() == 0

        response = authenticated_client.post('/api/tags/', {
            'name': 'foo'
        })

        assert Tag.objects.all().count() == 1
        assert Tag.objects.all().last().name == 'foo'

    def test_delete_tag(self, authenticated_client):
        foo = Tag.objects.create(name='foo')

        authenticated_client.delete(f'/api/tags/{foo.id}/')

        assert Tag.objects.all().count() == 0

    def test_delete_tag_must_exist(self, authenticated_client):
        foo = Tag.objects.create(name='foo')

        response = authenticated_client.delete(f'/api/tags/{foo.id + 1}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_create_tagged_recipe(self, authenticated_client, test_user):
        tag = Tag.objects.create(name='foo')
        recipe = Recipe.objects.create(title='bar')

        response = authenticated_client.post(f'/api/tags/{tag.id}/recipe/{recipe.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert TaggedRecipe.objects.all().count() == 1
        last = TaggedRecipe.objects.all().last()
        assert last.recipe == recipe
        assert last.tag == tag
        assert last.user == test_user

    def test_create_tagged_recipe_recipe_must_exist(self, authenticated_client, test_user):
        tag = Tag.objects.create(name='foo')
        recipe = Recipe.objects.create(title='bar')

        response = authenticated_client.post(f'/api/tags/{tag.id}/recipe/{recipe.id + 1}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_create_tagged_recipe_tag_must_exist(self, authenticated_client, test_user):
        tag = Tag.objects.create(name='foo')
        recipe = Recipe.objects.create(title='bar')

        response = authenticated_client.post(f'/api/tags/{tag.id + 1}/recipe/{recipe.id}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


    def test_delete_tagged_recipe(self, authenticated_client, test_user):
        tag = Tag.objects.create(name='foo')
        recipe = Recipe.objects.create(title='bar')
        TaggedRecipe.objects.create(tag=tag, recipe=recipe, user=test_user)

        response = authenticated_client.delete(f'/api/tags/{tag.id}/recipe/{recipe.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert TaggedRecipe.objects.all().count() == 0

    def test_delete_tagged_recipe_must_exist(self, authenticated_client, test_user):
        tag = Tag.objects.create(name='foo')
        recipe = Recipe.objects.create(title='bar')

        response = authenticated_client.delete(f'/api/tags/{tag.id}/recipe/{recipe.id}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
