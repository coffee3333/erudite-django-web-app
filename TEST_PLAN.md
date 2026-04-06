# Test Plan — Erudite Django Web App

## Overview

This document describes the testing strategy, test types, and test cases implemented for the `erudite-django-web-app` backend service.

---

## Testing Strategy

| Layer | Framework | Location |
|-------|-----------|----------|
| Unit / Integration tests | pytest + pytest-django | `tests/unit/` |
| BDD acceptance tests | behave + behave-django | `features/` |
| Code coverage | pytest-cov | CI report |
| Code quality | SonarCloud | GitHub Actions |

---

## Test Environment

- Python 3.12
- Django (DRF, SimpleJWT)
- SQLite (in-memory, created per test run)
- Required env vars: `DJANGO_SECRET_KEY`, `DEBUG`, `CLOUDINARY_*`, `EMAIL_HOST_*`, `GOOGLE_CLIENT_*`

---

## Unit / Integration Tests (`tests/unit/`)

### `test_auth.py` — Authentication (8 tests)

**Class: `TestRegistration`**

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `test_student_can_register` | POST `/api/users/auth/registration/` with valid student data → 201 |
| 2 | `test_teacher_can_register` | POST with valid teacher data → 201 |
| 3 | `test_mismatched_passwords_returns_400` | POST with password ≠ password2 → 400 |
| 4 | `test_duplicate_email_returns_400` | POST with already-registered email → 400 |
| 5 | `test_missing_email_returns_400` | POST without email field → 400 |

**Class: `TestLogin`**

| # | Test | Expected Result |
|---|------|-----------------|
| 6 | `test_verified_user_can_login` | POST `/api/users/auth/login/` with correct credentials → 200, `access` token in response |
| 7 | `test_wrong_password_returns_401` | POST with wrong password → 401 |
| 8 | `test_nonexistent_user_returns_401` | POST with unknown email → 401 |

---

### `test_courses.py` — Course Management (7 tests)

**Class: `TestCourseCreate`**

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | `test_verified_teacher_can_create_course` | POST `/api/platform/courses/create/` as teacher → 201 |
| 2 | `test_student_cannot_create_course` | POST as student → 403 |
| 3 | `test_anonymous_cannot_create_course` | POST unauthenticated → 401 |
| 4 | `test_missing_title_returns_400` | POST without `title` field → 400 |

**Class: `TestCourseUpdate`**

| # | Test | Expected Result |
|---|------|-----------------|
| 5 | `test_owner_can_update_course` | PATCH `/api/platform/courses/<slug>/update/` as owner → 200 |
| 6 | `test_non_owner_cannot_update_course` | PATCH as a different teacher → 403 |
| 7 | `test_anonymous_cannot_update_course` | PATCH unauthenticated → 401 |

---

## BDD Acceptance Tests (`features/`)

### `authentication.feature` — User Login/Logout (3 scenarios)

| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | Successful login | POST with valid credentials → 200, `access` + `refresh` tokens in response |
| 2 | Failed login with invalid credentials | POST with wrong password → 401 |
| 3 | Successful logout | POST to `/logout/` with valid refresh token → 205, "Successfully logged out" |

### `create_course.feature` — Course Creation (2 scenarios)

| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | Successfully create a course | POST with full valid data as teacher → 201, "Course created successfully." |
| 2 | Fail with missing title and description | POST with empty title/description → 400, "title" in response |

### `update_course.feature` — Course Update (2 scenarios)

| # | Scenario | Expected Result |
|---|----------|-----------------|
| 1 | Successfully update a course | PATCH with valid new data → 200, updated title in response |
| 2 | Fail to update with empty fields | PATCH with empty title/description → "No changes detected" |

---

## Total Test Count

| Suite | Tests |
|-------|-------|
| Unit / Integration | 15 |
| BDD | 7 |
| **Total** | **22** |

---

## CI/CD

- **`bdd.yml`** — runs `python -m behave` on every push/PR to `main`
- **`sonarcloud.yml`** — runs `pytest --cov`, uploads coverage + Sonar scan on push/PR to `main`

---

## Running Tests Locally

See `homework.md` in the project root for the full local setup and run commands.
