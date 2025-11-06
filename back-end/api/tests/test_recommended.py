import pytest
from django.contrib.auth.models import User
from rest_framework import status
from api.models import HealthDetails

RECS_URL = '/api/user/health/recommendations/'

@pytest.mark.django_db
class TestHealthRecommendationsEndpoint:
    def test_requires_authentication(self, api_client):
        resp = api_client.get(RECS_URL)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_404_when_no_health_profile(self, authenticated_client):
        resp = authenticated_client.get(RECS_URL)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_recommendations_change_when_health_changes(self, authenticated_client, test_user):
        """
        Create baseline health -> read recommendations.
        Then make the user 'bigger' and more active -> read again and
        assert calories_goal and protein_goal_g increase.
        """
        # Baseline/normal-ish profile
        baseline = HealthDetails.objects.create(
            user=test_user,
            age=20,
            height_ft=5,
            height_in=9,            # 5'9"
            weight=170,             # lb
            activity_level='moderate',
            goal='maintain',
            sex='male',
        )

        # First read
        r1 = authenticated_client.get(RECS_URL)
        assert r1.status_code == status.HTTP_200_OK
        assert 'calories_goal' in r1.data and 'protein_goal_g' in r1.data
        cal1 = r1.data['calories_goal']
        pro1 = r1.data['protein_goal_g']

        # Make the user "much bigger" and more active, and switch to a gaining goal
        baseline.height_ft = 6
        baseline.height_in = 4           # 6'4"
        baseline.weight = 250            # lb
        baseline.activity_level = 'high' # higher TDEE multiplier
        baseline.goal = 'gain'           # +calorie adjustment, higher protein/kg
        baseline.save()

        # Second read
        r2 = authenticated_client.get(RECS_URL)
        assert r2.status_code == status.HTTP_200_OK
        assert 'calories_goal' in r2.data and 'protein_goal_g' in r2.data
        cal2 = r2.data['calories_goal']
        pro2 = r2.data['protein_goal_g']

        # Sanity checks: values should increase with weight/height/activity/goal
        assert cal2 > cal1, f"Expected calories to increase: before={cal1}, after={cal2}"
        assert pro2 > pro1, f"Expected protein to increase: before={pro1}, after={pro2}"

        # Optional: ensure response also echoes key context (helps debugging)
        assert r2.data['goal'] == 'gain'
        assert r2.data['activity_level'] == 'high'
        assert r2.data['sex'] == 'male'
