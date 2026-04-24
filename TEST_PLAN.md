# Test Plan — Erudite Django Web App

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 Purpose](#11-purpose)
  - [1.2 Scope](#12-scope)
  - [1.3 Intended Audience](#13-intended-audience)
  - [1.4 Document Terminology and Acronyms](#14-document-terminology-and-acronyms)
  - [1.5 References](#15-references)
  - [1.6 Document Structure](#16-document-structure)
- [2. Evaluation Mission and Test Motivation](#2-evaluation-mission-and-test-motivation)
  - [2.1 Background](#21-background)
  - [2.2 Evaluation Mission](#22-evaluation-mission)
  - [2.3 Test Motivators](#23-test-motivators)
- [3. Target Test Items](#3-target-test-items)
- [4. Outline of Planned Tests](#4-outline-of-planned-tests)
  - [4.1 Outline of Test Inclusions](#41-outline-of-test-inclusions)
  - [4.2 Outline of Other Candidates for Potential Inclusion](#42-outline-of-other-candidates-for-potential-inclusion)
  - [4.3 Outline of Test Exclusions](#43-outline-of-test-exclusions)
- [5. Test Approach](#5-test-approach)
  - [5.1 Initial Test-Idea Catalogs and Other Reference Sources](#51-initial-test-idea-catalogs-and-other-reference-sources)
  - [5.2 Testing Techniques and Types](#52-testing-techniques-and-types)
    - [5.2.1 Data and Database Integrity Testing](#521-data-and-database-integrity-testing)
    - [5.2.2 Functional Testing](#522-functional-testing)
    - [5.2.3 Business Cycle Testing](#523-business-cycle-testing)
    - [5.2.4 User Interface Testing](#524-user-interface-testing)
    - [5.2.5 Security and Access Control Testing](#525-security-and-access-control-testing)
- [6. Entry and Exit Criteria](#6-entry-and-exit-criteria)
  - [6.1 Test Plan Entry/Exit Criteria](#61-test-plan-entryexit-criteria)
  - [6.2 Test Cycle Entry/Exit Criteria](#62-test-cycle-entryexit-criteria)
- [7. Deliverables](#7-deliverables)
- [8. Testing Workflow](#8-testing-workflow)
- [9. Environmental Needs](#9-environmental-needs)
  - [9.1 Base System Hardware](#91-base-system-hardware)
  - [9.2 Base Software Elements in the Test Environment](#92-base-software-elements-in-the-test-environment)
  - [9.3 Productivity and Support Tools](#93-productivity-and-support-tools)
- [10. Responsibilities, Staffing, and Training Needs](#10-responsibilities-staffing-and-training-needs)
- [11. Iteration Milestones](#11-iteration-milestones)
- [12. Risks, Dependencies, Assumptions, and Constraints](#12-risks-dependencies-assumptions-and-constraints)

---

## 1. Introduction

### 1.1 Purpose

This Test Plan defines the testing strategy, scope, and approach for the **Erudite Django Web App** — the backend REST API of the Erudite e-learning platform. The purpose of this document is to plan and control the test effort, identify what will be tested, and define success criteria for the backend service.

### 1.2 Scope

This plan covers:
- **Unit and integration testing** of the authentication and course management API endpoints
- **BDD acceptance testing** of key user-facing workflows using Gherkin feature files
- **Continuous Integration** via GitHub Actions

It does not cover frontend rendering, mobile clients, or third-party service reliability (Cloudinary, email providers).

### 1.3 Intended Audience

This document is intended for:
- The development team maintaining the backend
- The course lecturer evaluating the testing deliverable
- Any contributor wishing to understand the testing setup before contributing

### 1.4 Document Terminology and Acronyms

| Term | Definition |
|------|-----------|
| API | Application Programming Interface |
| BDD | Behaviour-Driven Development |
| CI | Continuous Integration |
| DRF | Django REST Framework |
| JWT | JSON Web Token — used for authentication |
| RUP | Rational Unified Process |
| SUT | System Under Test |
| HTTP | HyperText Transfer Protocol |
| 2xx / 4xx | HTTP response status code families (success / client error) |

### 1.5 References

| Document | Location |
|----------|----------|
| GitHub Repository | https://github.com/coffee3333/erudite-django-web-app |
| Test code (unit) | `tests/unit/` |
| Test code (BDD) | `features/` |
| Dependency file | `requirements.txt` |
| CI workflow | `.github/workflows/` |
| SonarCloud dashboard | https://sonarcloud.io/project/overview?id=erudite_erudite-django-web-app |

### 1.6 Document Structure

- Sections 1–2: purpose, background, and motivation
- Section 3: what is being tested
- Sections 4–5: what tests are planned and how they are executed
- Sections 6–7: criteria for starting/stopping testing and deliverables
- Sections 8–12: environment, responsibilities, milestones, and risks

---

## 2. Evaluation Mission and Test Motivation

### 2.1 Background

The Erudite platform is a Django + DRF backend serving a React frontend. It handles user registration, authentication via JWT, course management, topic and lesson management, challenge submission, and course enrollment. Correctness and access control are critical — incorrect permission logic could allow students to modify teacher content or expose private data.

### 2.2 Evaluation Mission

The mission of the test effort is to verify that:
- All API endpoints return correct HTTP status codes and response bodies
- Authentication and authorization rules are enforced correctly
- Business rules (e.g. only course owners can update their course) are applied consistently

### 2.3 Test Motivators

- **Correctness** — ensure endpoints behave as specified in the API contract
- **Access control** — verify that role-based permissions (student / teacher / anonymous) are enforced
- **Regression prevention** — catch breaking changes introduced during development via CI
- **Confidence for deployment** — tests must pass before any merge to `main`

---

## 3. Target Test Items

The following backend components are the primary targets of this test plan:

- **Authentication endpoints** — registration, login, logout (`/api/users/auth/`)
- **Course management endpoints** — create, update, delete courses (`/api/platform/courses/`)
- **BDD user flows** — login/logout lifecycle, full course creation and update workflows
- **Permission logic** — role-based access control (IsTeacher, IsOwner, IsAuthenticated)

---

## 4. Outline of Planned Tests

### 4.1 Outline of Test Inclusions

| Test Type | Framework | Location | Count |
|-----------|-----------|----------|-------|
| Unit / Integration (pytest) | pytest + pytest-django | `tests/unit/` | 15 tests |
| BDD Acceptance (Gherkin) | behave + behave-django | `features/` | 7 scenarios |

**Covered areas:**
- User registration (valid / invalid / duplicate)
- User login (valid credentials / wrong password / unknown user)
- Course creation (teacher / student / anonymous / missing fields)
- Course update (owner / non-owner / anonymous)
- Login/logout lifecycle (BDD)
- Full course creation workflow (BDD)
- Full course update workflow (BDD)

### 4.2 Outline of Other Candidates for Potential Inclusion

The following areas are candidates for future test coverage but are not included in the current iteration:

- Topic and lesson CRUD endpoints
- Challenge submission and grading logic
- Course enrollment flows
- Password reset email flow
- Bookmark toggle endpoint
- Course feedback / rating submission

### 4.3 Outline of Test Exclusions

The following are explicitly excluded from this test plan:

- Frontend (React) behaviour — covered by the frontend test plan
- Third-party service reliability (Cloudinary file uploads, email delivery)
- Performance, load, and stress testing — out of scope for this iteration
- Database failover and recovery

---

## 5. Test Approach

### 5.1 Initial Test-Idea Catalogs and Other Reference Sources

- Django REST Framework documentation: https://www.django-rest-framework.org/
- pytest-django documentation: https://pytest-django.readthedocs.io/
- behave-django documentation: https://behave-django.readthedocs.io/
- Gherkin syntax reference: https://cucumber.io/docs/gherkin/

### 5.2 Testing Techniques and Types

#### 5.2.1 Data and Database Integrity Testing

| | |
|---|---|
| **Technique Objective** | Verify that the database correctly stores and retrieves user and course data, and that constraints (unique email, unique username, required fields) are enforced |
| **Technique** | Submit requests with valid and invalid data via the API; assert the database state through the ORM after each operation |
| **Oracles** | HTTP 201 for successful creation; HTTP 400 with field-level errors for constraint violations; confirm objects exist (or do not exist) in the database after each test |
| **Required Tools** | pytest-django (`@pytest.mark.django_db`), Django test client, SQLite in-memory database |
| **Success Criteria** | All constraint violations return 400; valid data is persisted and retrievable |
| **Special Considerations** | Each test runs in an isolated transaction that is rolled back after the test to prevent state leakage |

#### 5.2.2 Functional Testing

| | |
|---|---|
| **Technique Objective** | Verify that each API endpoint performs its intended function — correct status codes, response bodies, and side effects — for all key use-case scenarios |
| **Technique** | Exercise each endpoint with valid and invalid inputs using the DRF `APIClient`; assert response status and response data fields |
| **Oracles** | Expected HTTP status codes (201, 200, 400, 401, 403); presence of specific fields in the response JSON (e.g. `access` token on login) |
| **Required Tools** | pytest, pytest-django, DRF APIClient |
| **Success Criteria** | All 15 unit/integration tests pass; all 7 BDD scenarios pass |
| **Special Considerations** | Fixtures (`student`, `teacher`, `published_course`) are defined in `tests/conftest.py` and reused across test classes |

**Functional test cases:**

*Authentication — `tests/unit/test_auth.py`*

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Student can register | Valid student payload | 201 |
| 2 | Teacher can register | Valid teacher payload | 201 |
| 3 | Mismatched passwords | password ≠ password2 | 400 |
| 4 | Duplicate email | Existing user's email | 400 |
| 5 | Missing email | No email field | 400 |
| 6 | Verified user can login | Correct credentials | 200 + `access` token |
| 7 | Wrong password | Incorrect password | 401 |
| 8 | Unknown user login | Non-existent email | 401 |

*Course Management — `tests/unit/test_courses.py`*

| # | Test | Input | Expected |
|---|------|-------|----------|
| 1 | Teacher creates course | Valid course data | 201 |
| 2 | Student cannot create | Valid data, student auth | 403 |
| 3 | Anonymous cannot create | No auth | 401 |
| 4 | Missing title | No title field | 400 |
| 5 | Owner can update | PATCH as course owner | 200 |
| 6 | Non-owner cannot update | PATCH as different teacher | 403 |
| 7 | Anonymous cannot update | PATCH, no auth | 401 |

#### 5.2.3 Business Cycle Testing

| | |
|---|---|
| **Technique Objective** | Verify complete end-to-end user workflows as described in the acceptance criteria |
| **Technique** | Execute Gherkin feature file scenarios using behave-django; each scenario covers a full user journey from setup through action to assertion |
| **Oracles** | Scenario step assertions: HTTP status codes, response body content, token presence |
| **Required Tools** | behave, behave-django, Gherkin feature files in `features/` |
| **Success Criteria** | All 7 BDD scenarios pass |
| **Special Considerations** | Background steps create prerequisite data (e.g. verified teacher, existing course) before each scenario runs |

**BDD scenarios:**

| Feature File | Scenario | Expected Outcome |
|---|---|---|
| `authentication.feature` | Successful login | 200 + access + refresh tokens |
| `authentication.feature` | Failed login (wrong password) | 401 |
| `authentication.feature` | Successful logout | 205 + "Successfully logged out" |
| `create_course.feature` | Successfully create a course | 201 + "Course created successfully." |
| `create_course.feature` | Fail — missing title/description | 400 + "title" in response |
| `update_course.feature` | Successfully update a course | 200 + updated title in response |
| `update_course.feature` | Fail — empty fields | "No changes detected" in response |

#### 5.2.4 User Interface Testing

Not applicable. This is a REST API backend. UI testing is covered by the frontend test plan and the Playwright E2E suite in the React repository.

#### 5.2.5 Security and Access Control Testing

| | |
|---|---|
| **Technique Objective** | Verify that role-based permissions are enforced — unauthenticated users cannot access protected endpoints, students cannot perform teacher-only actions, and non-owners cannot modify resources they do not own |
| **Technique** | Submit requests using no credentials, student credentials, and teacher credentials to endpoints that require specific roles; assert the correct rejection status codes |
| **Oracles** | 401 for unauthenticated requests; 403 for authenticated but unauthorized requests |
| **Required Tools** | pytest-django, DRF APIClient with JWT token injection |
| **Success Criteria** | All permission tests pass (tests 2, 3, 6, 7 in `test_courses.py`) |
| **Special Considerations** | Tokens are injected via `client.credentials(HTTP_AUTHORIZATION='Bearer <token>')` in fixture setup |

---

## 6. Entry and Exit Criteria

### 6.1 Test Plan Entry/Exit Criteria

**Entry criteria (when testing can begin):**
- Django migrations are applied successfully
- All required environment variables are set (see Section 9)
- The virtual environment is active and all dependencies from `requirements.txt` are installed

**Exit criteria (when testing is complete):**
- All tests pass with 0 failures
- CI pipeline shows green on the `main` branch

**Suspension criteria:**
- If the database migrations fail, testing is suspended until migrations are repaired
- If more than 30% of tests fail due to a systemic issue (e.g. broken conftest), the run is suspended and the root cause investigated

### 6.2 Test Cycle Entry/Exit Criteria

**Entry:** A pull request is opened targeting `main`; GitHub Actions triggers the test pipeline automatically.

**Exit:** All tests pass and the CI workflow completes with status `success`. The PR may then be merged.

**Abnormal termination:** If CI times out or the environment fails to build, the run is marked failed and the PR is blocked from merging.

---

## 7. Deliverables

| Deliverable | Description | Location |
|---|---|---|
| Test code (unit) | pytest test classes for auth and course endpoints | `tests/unit/` |
| Test code (BDD) | Gherkin feature files + behave step definitions | `features/` |
| Test configuration | pytest settings | `pytest.ini` |
| CI workflow | GitHub Actions pipeline definition | `.github/workflows/bdd.yml`, `sonarcloud.yml` |
| Coverage report | XML coverage report generated by pytest-cov | Generated at runtime |
| SonarCloud report | Code quality and coverage dashboard | https://sonarcloud.io/project/overview?id=erudite_erudite-django-web-app |
| This test plan | RUP-format test plan document | `TEST_PLAN.md` |

---

## 8. Testing Workflow

1. Developer creates a feature branch and writes code
2. Developer runs tests locally: `pytest tests/ -v` (see `homework.md` for full command)
3. Developer opens a Pull Request targeting `main`
4. GitHub Actions automatically triggers the CI pipeline:
   - Installs Python dependencies from `requirements.txt`
   - Runs database migrations
   - Executes `pytest tests/` (unit + integration tests)
   - Executes `python -m behave` (BDD acceptance tests)
   - Uploads coverage to SonarCloud
5. If all steps pass, the PR is eligible for merge
6. If any step fails, the PR is blocked — the developer must fix the failure before merging

---

## 9. Environmental Needs

### 9.1 Base System Hardware

- Any machine capable of running Python 3.12
- No special hardware requirements — SQLite in-memory database is used for all tests (no external DB needed)

### 9.2 Base Software Elements in the Test Environment

| Software | Version | Purpose |
|---|---|---|
| Python | 3.12 | Runtime |
| Django | (see requirements.txt) | Web framework |
| Django REST Framework | (see requirements.txt) | API layer |
| pytest | 8.3.5 | Test runner |
| pytest-django | 4.9.0 | Django integration for pytest |
| pytest-bdd | 7.3.0 | BDD support for pytest |
| pytest-cov | 6.0.0 | Coverage measurement |
| behave | (see requirements.txt) | BDD runner for Gherkin features |
| behave-django | 1.4.0 | Django integration for behave |

Full dependency list: [`requirements.txt`](https://github.com/coffee3333/erudite-django-web-app/blob/main/requirements.txt)

### 9.3 Productivity and Support Tools

| Tool | Purpose |
|---|---|
| GitHub Actions | CI/CD — runs tests on every PR |
| SonarCloud | Static analysis, coverage tracking, security scan |
| pytest-cov / coverage.py | Generates `coverage.xml` for SonarCloud upload |

---

## 10. Responsibilities, Staffing, and Training Needs

| Role | Responsibility |
|---|---|
| Developer | Write unit and integration tests alongside feature code |
| Developer | Write and maintain BDD feature files and step definitions |
| Developer | Ensure CI pipeline passes before requesting PR review |
| Developer | Monitor SonarCloud results and address flagged issues |

All team members are expected to be familiar with pytest and basic Django test patterns. The `homework.md` file in the repo root provides the exact commands to run tests locally.

---

## 11. Iteration Milestones

| Milestone | Target |
|---|---|
| Unit tests passing locally | ✅ Achieved — 15/15 tests pass |
| BDD scenarios passing locally | ✅ Achieved — 7/7 scenarios pass |
| CI pipeline green on `main` | ✅ Achieved |
| SonarCloud connected | ✅ Achieved — 49.8% coverage reported |
| Coverage target | Goal: ≥ 60% (current: 49.8%) |
| Security rating | Goal: A (current: C — 17 issues to fix) |

---

## 12. Risks, Dependencies, Assumptions, and Constraints

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Missing environment variables cause CI failure | Medium | High | All required vars are set as GitHub Actions env vars with placeholder values |
| Migration conflicts block test database setup | Low | High | Migrations are regenerated from scratch; `migrate` runs before every CI test job |
| BDD steps fall out of sync with endpoint changes | Medium | Medium | Step definitions are co-located with feature files; review on every endpoint change |
| SonarCloud token expires or is revoked | Low | Medium | Token stored as GitHub secret `SONAR_TOKEN`; rotate if CI scan fails |
| Test coverage stays below 60% | Medium | Medium | Expand tests to cover topic, lesson, and challenge endpoints in the next iteration |

---

## 13. Test Execution Screenshots

### 13.1 Unit & Integration Tests (pytest)

Run command:
```bash
DJANGO_SECRET_KEY=test DEBUG=True \
CLOUDINARY_CLOUD_NAME=x CLOUDINARY_API_KEY=x CLOUDINARY_API_SECRET=x \
EMAIL_HOST_USER=x@x.com EMAIL_HOST_PASSWORD=x \
GOOGLE_CLIENT_ID=x GOOGLE_CLIENT_SECRET=x \
.venv/bin/pytest tests/ -v
```

<!-- Paste your pytest terminal screenshot here -->
![pytest test run](docs/screenshots/pytest_run.png)

### 13.2 BDD Acceptance Tests (behave)

Run command:
```bash
DJANGO_SECRET_KEY=test DEBUG=True \
CLOUDINARY_CLOUD_NAME=x CLOUDINARY_API_KEY=x CLOUDINARY_API_SECRET=x \
EMAIL_HOST_USER=x@x.com EMAIL_HOST_PASSWORD=x \
GOOGLE_CLIENT_ID=x GOOGLE_CLIENT_SECRET=x \
.venv/bin/python -m behave
```

<!-- Paste your behave terminal screenshot here -->
![behave BDD run](docs/screenshots/behave_run.png)
