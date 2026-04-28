"""Tests for user profile retrieve and update endpoints."""
import pytest
from authentication.models import User


@pytest.mark.django_db
class TestGetProfile:
    url = "/api/users/profile/me/"

    def test_get_profile_authenticated(self, student_client, student):
        res = student_client.get(self.url)
        assert res.status_code == 200
        assert res.data["username"] == student.username
        assert res.data["role"] == "student"

    def test_get_profile_unauthenticated(self, api_client):
        res = api_client.get(self.url)
        assert res.status_code == 401

    def test_get_profile_contains_expected_fields(self, student_client):
        res = student_client.get(self.url)
        assert res.status_code == 200
        for field in ("id", "username", "role", "email_verified", "slug"):
            assert field in res.data


@pytest.mark.django_db
class TestUpdateProfile:
    url = "/api/users/profile/me/update/"

    def test_update_username(self, student_client):
        res = student_client.patch(self.url, {"username": "newname123"}, format="json")
        assert res.status_code == 200
        assert res.data["username"] == "newname123"

    def test_update_bio(self, student_client):
        res = student_client.patch(self.url, {"user_bio": "Hello world"}, format="json")
        assert res.status_code == 200
        assert res.data["user_bio"] == "Hello world"

    def test_update_duplicate_username_returns_400(self, student_client, teacher):
        res = student_client.patch(self.url, {"username": teacher.username}, format="json")
        assert res.status_code == 400

    def test_remove_photo_sets_null(self, student_client, student):
        res = student_client.patch(self.url, {"remove_photo": "1"}, format="multipart")
        assert res.status_code == 200
        student.refresh_from_db()
        assert not student.photo

    def test_update_unauthenticated(self, api_client):
        res = api_client.patch(self.url, {"username": "hacker"}, format="json")
        assert res.status_code == 401
