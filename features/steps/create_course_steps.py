import json
import requests
from behave import given, when, then

API_BASE_URL = "http://127.0.0.1:8000"  # поменяй при необходимости

@given("I am logged in as an existing teacher with verified email")
def step_impl(context):
    email = "test@mail.com"
    password = "123456789A@"

    login_response = requests.post(
        f"{API_BASE_URL}/api/users/auth/login/",
        data={"email": email, "password": password},
    )

    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json().get("access") or login_response.json().get("token")
    assert token, f"Could not get token from login response: {login_response.text}"

    context.token = token


@when('I send a POST request to "{endpoint}" with the following data:')
def step_impl(context, endpoint):
    data = {}
    for row in context.table:
        key = row[0].strip()
        value = row[1].strip()
        data[key] = value

    print("DATA SENT:", data)

    headers = {
        "Authorization": f"Bearer {context.token}",
    }

    response = requests.post(
        f"{API_BASE_URL}{endpoint}",
        data=data,
        files={},
        headers=headers,
    )

    print("DEBUG:", response.status_code, response.text)
    context.response = response



@then("the course response status code should be {status_code:d}")
def step_impl(context, status_code):
    assert context.response.status_code == status_code, (
        f"Expected {status_code}, got {context.response.status_code}. "
        f"Response: {context.response.text}"
    )


@then('the course response should contain "{text}"')
def step_impl(context, text):
    assert text in context.response.text, (
        f'Expected text "{text}" not found in response: {context.response.text}'
    )
