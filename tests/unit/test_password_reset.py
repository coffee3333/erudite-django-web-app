"""Tests for password reset request and confirm endpoints."""
import pytest
from django.utils import timezone
from datetime import timedelta
from authentication.models import PasswordResetOTP


REQUEST_URL = "/api/users/auth/password/reset/request/"
CONFIRM_URL = "/api/users/auth/password/reset/confirm/"


@pytest.mark.django_db
class TestRequestPasswordReset:

    def test_request_otp_success(self, api_client, student):
        res = api_client.post(REQUEST_URL, {"email": student.email}, format="json")
        assert res.status_code == 200
        assert PasswordResetOTP.objects.filter(user=student).exists()

    def test_request_otp_unknown_email(self, api_client):
        res = api_client.post(REQUEST_URL, {"email": "nobody@example.com"}, format="json")
        assert res.status_code == 404

    def test_request_otp_missing_email(self, api_client):
        res = api_client.post(REQUEST_URL, {}, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestConfirmPasswordReset:

    def _create_otp(self, user, code="123456"):
        return PasswordResetOTP.objects.create(user=user, otp_code=code)

    def test_confirm_otp_success(self, api_client, student):
        otp = self._create_otp(student)
        res = api_client.post(CONFIRM_URL, {
            "email": student.email,
            "otp_code": otp.otp_code,
            "new_password": "newpassword99",
        }, format="json")
        assert res.status_code == 200
        otp.refresh_from_db()
        assert otp.is_used is True

    def test_confirm_otp_wrong_code(self, api_client, student):
        self._create_otp(student, code="111111")
        res = api_client.post(CONFIRM_URL, {
            "email": student.email,
            "otp_code": "999999",
            "new_password": "newpassword99",
        }, format="json")
        assert res.status_code == 400

    def test_confirm_otp_expired(self, api_client, student):
        otp = self._create_otp(student)
        PasswordResetOTP.objects.filter(pk=otp.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        res = api_client.post(CONFIRM_URL, {
            "email": student.email,
            "otp_code": otp.otp_code,
            "new_password": "newpassword99",
        }, format="json")
        assert res.status_code == 400

    def test_confirm_otp_already_used(self, api_client, student):
        otp = self._create_otp(student)
        otp.is_used = True
        otp.save()
        res = api_client.post(CONFIRM_URL, {
            "email": student.email,
            "otp_code": otp.otp_code,
            "new_password": "newpassword99",
        }, format="json")
        assert res.status_code == 400

    def test_confirm_unknown_email(self, api_client):
        res = api_client.post(CONFIRM_URL, {
            "email": "nobody@example.com",
            "otp_code": "123456",
            "new_password": "newpassword99",
        }, format="json")
        assert res.status_code == 404
