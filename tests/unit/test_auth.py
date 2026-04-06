"""Unit tests for authentication endpoints."""
import pytest
from authentication.models import User


@pytest.mark.django_db
class TestRegistration:
    url = "/api/users/auth/registration/"

    def test_student_can_register(self, api_client):
        res = api_client.post(self.url, {
            "email": "newstudent@test.com",
            "username": "newstudent",
            "password": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
            "role": "student",
        })
        assert res.status_code == 201

    def test_teacher_can_register(self, api_client):
        res = api_client.post(self.url, {
            "email": "newteacher@test.com",
            "username": "newteacher",
            "password": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
            "role": "teacher",
        })
        assert res.status_code == 201

    def test_mismatched_passwords_returns_400(self, api_client):
        res = api_client.post(self.url, {
            "email": "mismatch@test.com",
            "username": "mismatch",
            "password": "Str0ng!Pass#99",
            "password2": "DifferentPass#88",
            "role": "student",
        })
        assert res.status_code == 400

    def test_duplicate_email_returns_400(self, api_client, student):
        res = api_client.post(self.url, {
            "email": student.email,
            "username": "another",
            "password": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
            "role": "student",
        })
        assert res.status_code == 400

    def test_missing_email_returns_400(self, api_client):
        res = api_client.post(self.url, {
            "username": "nomail",
            "password": "Str0ng!Pass#99",
            "password2": "Str0ng!Pass#99",
            "role": "student",
        })
        assert res.status_code == 400


@pytest.mark.django_db
class TestLogin:
    url = "/api/users/auth/login/"

    def test_verified_user_can_login(self, api_client, student):
        res = api_client.post(self.url, {
            "email": student.email,
            "password": "pass123",
        })
        assert res.status_code == 200
        assert "access" in res.data

    def test_wrong_password_returns_401(self, api_client, student):
        res = api_client.post(self.url, {
            "email": student.email,
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_nonexistent_user_returns_401(self, api_client):
        res = api_client.post(self.url, {
            "email": "ghost@test.com",
            "password": "pass123",
        })
        assert res.status_code == 401
