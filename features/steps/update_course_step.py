import requests
from behave import given, when, then

API_BASE_URL = "http://127.0.0.1:8000"


@given("I am logged in as an existing teacher with verified email for updating")
def step_impl(context):
    email = "test@mail.com"
    password = "123456789A@"

    login_response = requests.post(
        f"{API_BASE_URL}/api/users/auth/login/",
        data={"email": email, "password": password},
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json().get("access")
    assert token, f"Missing token in response: {login_response.text}"

    context.token = token


@given('a course already exists with title "{title}" and slug "{slug}"')
def step_impl(context, title, slug):
    headers = {"Authorization": f"Bearer {context.token}"}
    data = {
        "title": title,
        "description": "Initial course description",
        "language": "English",
        "level": "beginner",
        "status": "draft",
    }

    response = requests.post(
        f"{API_BASE_URL}/api/platform/courses/create/",
        data=data,
        headers=headers,
    )

    assert response.status_code in [200, 201], (
        f"Failed to create initial course. Response: {response.status_code}, {response.text}"
    )

    try:
        actual_slug = response.json().get("slug", slug)
    except Exception:
        actual_slug = slug

    context.course_slug = actual_slug
    print(f"✅ Created course with slug: {context.course_slug}")


@when('I send a PATCH request to "{endpoint}" with the following data:')
def step_impl(context, endpoint):
    data = {}
    for row in context.table:
        key, value = row.cells
        data[key.strip()] = value.strip()

    headers = {"Authorization": f"Bearer {context.token}"}

    endpoint = endpoint.format(course_slug=context.course_slug)

    response = requests.patch(
        f"{API_BASE_URL}{endpoint}",
        data=data,
        files={},
        headers=headers,
    )

    print("UPDATE DEBUG:", response.status_code, response.text)
    context.response = response




@then("the course update response status code should be {status_code:d}")
def step_impl(context, status_code):
    assert context.response.status_code == status_code, (
        f"Expected {status_code}, got {context.response.status_code}. "
        f"Response: {context.response.text}"
    )


@then('the course update response should contain {text}')
def step_impl(context, text):
    assert text in context.response.text, (
        f'Expected text "{text}" not found in response: {context.response.text}'
    )
