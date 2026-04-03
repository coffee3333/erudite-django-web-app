"""Step definitions for authentication.feature"""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from rest_framework.test import APIClient

from authentication.models import User, EmailVerificationCode

scenarios("../features/authentication.feature")

from tests.step_defs.conftest import Context, make_user, auth_client


# ── Given ─────────────────────────────────────────────────────────────────────

@given(parsers.parse('a student exists with email "{email}"'), target_fixture="ctx")
def student_exists_email_only(db, email):
    c = Context()
    make_user(email, role="student")
    return c


@given(parsers.parse('a student exists with email "{email}" and password "{password}"'), target_fixture="ctx")
def student_exists_with_creds(db, email, password):
    c = Context()
    make_user(email, password=password, role="student")
    return c


# ── When ──────────────────────────────────────────────────────────────────────

@when(parsers.parse('a student registers with email "{email}" and password "{password}"'))
def register_student(ctx, email, password):
    ctx.response = ctx.client.post("/api/users/auth/registration/", {
        "email": email,
        "username": email.split("@")[0],
        "password": password,
        "password2": password,
        "role": "student",
    })


@when(parsers.parse('a teacher registers with email "{email}" and password "{password}"'))
def register_teacher(ctx, email, password):
    ctx.response = ctx.client.post("/api/users/auth/registration/", {
        "email": email,
        "username": email.split("@")[0],
        "password": password,
        "password2": password,
        "role": "teacher",
    })


@when("a student registers with mismatched passwords")
def register_mismatched(ctx):
    ctx.response = ctx.client.post("/api/users/auth/registration/", {
        "email": "mismatch@test.com",
        "username": "mismatch",
        "password": "Str0ng!Pass#99",
        "password2": "DifferentPass#88",
        "role": "student",
    })


@when(parsers.parse('the user logs in with email "{email}" and password "{password}"'))
def login_user(ctx, email, password):
    ctx.response = ctx.client.post("/api/users/auth/login/", {
        "email": email,
        "password": password,
    })


@when("I GET my profile")
def get_profile(ctx):
    ctx.response = ctx.client.get("/api/users/profile/me/")


@when("an anonymous user GETs their profile")
def anon_get_profile(ctx):
    ctx.response = ctx.client.get("/api/users/profile/me/")


@when("I request email verification")
def request_verification(ctx):
    ctx.response = ctx.client.post("/api/users/users/me/email/verify/request/", {"email": ctx.user.email})


@given("an email verification code exists")
def create_verification_code(ctx):
    from authentication.models import EmailVerificationCode
    ctx._verif_code = EmailVerificationCode.objects.create(user=ctx.user, code="123456")


@when("I confirm the email verification with the correct code")
def confirm_verification_correct(ctx):
    ctx.response = ctx.client.post("/api/users/users/me/email/verify/confirm/", {
        "email": ctx.user.email,
        "code": ctx._verif_code.code,
    })


@when(parsers.parse('I confirm email verification with code "{code}"'))
def confirm_verification_wrong(ctx, code):
    ctx.response = ctx.client.post("/api/users/users/me/email/verify/confirm/", {
        "email": ctx.user.email,
        "code": code,
    })


@when("I GET my dashboard")
def get_dashboard(ctx):
    ctx.response = ctx.client.get("/api/users/dashboard/")


@when("an anonymous user GETs the dashboard")
def anon_get_dashboard(ctx):
    ctx.response = ctx.client.get("/api/users/dashboard/")


@when("I GET the teacher dashboard")
def get_teacher_dashboard(ctx):
    ctx.response = ctx.client.get("/api/users/teacher-dashboard/")


@when("an anonymous user GETs the leaderboard")
def anon_get_leaderboard(ctx):
    ctx.response = ctx.client.get("/api/users/leaderboard/")


# ── Then ──────────────────────────────────────────────────────────────────────

@then(parsers.parse('the response status is {code:d}'))
def check_status(ctx, code):
    assert ctx.response.status_code == code, (
        f"Expected {code}, got {ctx.response.status_code}. Body: {ctx.response.data}"
    )


@then(parsers.parse('the response contains "{key}"'))
def check_response_key(ctx, key):
    assert key in ctx.response.data, f"'{key}' not found in {ctx.response.data}"
