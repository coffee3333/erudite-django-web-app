"""Tests for Dashboard and Leaderboard endpoints."""
import pytest
from core.models.submission_model import Submission
from authentication.models import User


@pytest.mark.skip(reason="dashboard URL not yet registered")
@pytest.mark.django_db
class TestDashboard:
    url = "/api/users/dashboard/"

    def test_unauthenticated_returns_401(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == 401

    def test_authenticated_returns_dashboard_structure(self, student_client):
        res = student_client.get(self.url)
        assert res.status_code == 200
        data = res.data
        assert "profile" in data
        assert "stats" in data
        assert "courses" in data
        assert "certificates" in data
        assert "recent_activity" in data

    def test_stats_zero_for_new_student(self, student_client):
        res = student_client.get(self.url)
        assert res.status_code == 200
        stats = res.data["stats"]
        assert stats["total_points"] == 0
        assert stats["challenges_passed"] == 0
        assert stats["challenges_attempted"] == 0
        assert stats["certificates_earned"] == 0

    def test_profile_contains_username(self, student, student_client):
        res = student_client.get(self.url)
        assert res.data["profile"]["username"] == student.username

    def test_rank_is_positive_integer(self, student_client):
        res = student_client.get(self.url)
        assert res.data["stats"]["rank"] >= 1

    def test_recent_activity_is_empty_for_new_student(self, student_client):
        res = student_client.get(self.url)
        assert res.data["recent_activity"] == []


@pytest.mark.skip(reason="leaderboard URL not yet registered")
@pytest.mark.django_db
class TestLeaderboard:
    url = "/api/users/leaderboard/"

    def test_returns_list(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == 200
        assert isinstance(res.data, list)

    def test_anonymous_can_view_leaderboard(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == 200

    def test_leaderboard_entry_has_expected_fields(self, student_client, student, challenge, published_course):
        res = student_client.get(self.url)
        assert res.status_code == 200
        if res.data:
            entry = res.data[0]
            assert "username" in entry
            assert "total_points" in entry
