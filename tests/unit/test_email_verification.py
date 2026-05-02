"""Tests for email verification request and confirm endpoints."""
import pytest
from django.utils import timezone
from datetime import timedelta
from authentication.models import EmailVerificationCode


REQUEST_URL = "/api/users/users/me/email/verify/request/"
CONFIRM_URL = "/api/users/users/me/email/verify/confirm/"


@pytest.mark.django_db
class TestRequestEmailVerification:

    def test_request_code_creates_record(self, unverified_client, unverified_student):
        res = unverified_client.post(REQUEST_URL, format="json")
        assert res.status_code == 200
        assert EmailVerificationCode.objects.filter(user=unverified_student).exists()

    def test_request_already_verified_returns_200(self, student_client):
        res = student_client.post(REQUEST_URL, format="json")
        assert res.status_code == 200
        assert "already verified" in res.data["message"]

    def test_request_unauthenticated(self, api_client):
        res = api_client.post(REQUEST_URL, format="json")
        assert res.status_code == 401


@pytest.mark.django_db
class TestConfirmEmailVerification:

    def _create_code(self, user, code="654321"):
        return EmailVerificationCode.objects.create(user=user, code=code)

    def test_confirm_code_success(self, unverified_client, unverified_student):
        code_obj = self._create_code(unverified_student)
        res = unverified_client.post(CONFIRM_URL, {"code": code_obj.code}, format="json")
        assert res.status_code == 200
        unverified_student.refresh_from_db()
        assert unverified_student.email_verified is True

    def test_confirm_code_marks_used(self, unverified_client, unverified_student):
        code_obj = self._create_code(unverified_student)
        unverified_client.post(CONFIRM_URL, {"code": code_obj.code}, format="json")
        code_obj.refresh_from_db()
        assert code_obj.is_used is True

    def test_confirm_wrong_code(self, unverified_client, unverified_student):
        self._create_code(unverified_student, code="111111")
        res = unverified_client.post(CONFIRM_URL, {"code": "999999"}, format="json")
        assert res.status_code == 400

    def test_confirm_expired_code(self, unverified_client, unverified_student):
        code_obj = self._create_code(unverified_student)
        EmailVerificationCode.objects.filter(pk=code_obj.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        res = unverified_client.post(CONFIRM_URL, {"code": code_obj.code}, format="json")
        assert res.status_code == 400

    def test_confirm_unauthenticated(self, api_client):
        res = api_client.post(CONFIRM_URL, {"code": "123456"}, format="json")
        assert res.status_code == 401
