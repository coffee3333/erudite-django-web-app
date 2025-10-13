from behave import given, when, then
from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()

@given('a registered user exists with email "{email}" and password "{password}"')
def step_create_user(context, email, password):
    User.objects.filter(email=email).delete()
    User.objects.create_user(username=email, email=email, password=password)
    context.client = Client()

@when('I send a POST request to "{endpoint}" with email "{email}" and password "{password}"')
def step_send_login_request(context, endpoint, email, password):
    response = context.client.post(endpoint, {
        "email": email,
        "password": password
    }, content_type="application/json")
    context.response = response

@then('the response status code should be {status_code:d}')
def step_check_status_code(context, status_code):
    assert context.response.status_code == status_code, f"Expected {status_code}, got {context.response.status_code}"

@then('the response should contain "{key}" and "{key2}" tokens')
def step_check_tokens(context, key, key2):
    data = json.loads(context.response.content)
    assert key in data and key2 in data, f"Expected keys '{key}' and '{key2}' in response."

@then('the response should contain "{text}"')
def step_check_response_contains(context, text):
    assert text in context.response.content.decode(), f"Expected '{text}' in response."

@given('I am logged in with email "{email}" and password "{password}"')
def step_login_and_store_refresh(context, email, password):
    response = context.client.post("/api/users/auth/login/", {
        "email": email,
        "password": password
    }, content_type="application/json")
    data = json.loads(response.content)
    context.refresh_token = data.get("refresh")
    context.access_token = data.get("access")


@when('I send a POST request to "{endpoint}" with a valid refresh token')
def step_send_logout_request(context, endpoint):
    import json
    body = json.dumps({"refresh_token": context.refresh_token})
    headers = {"HTTP_AUTHORIZATION": f"Bearer {context.access_token}"}

    response = context.client.post(
        endpoint,
        body,
        content_type="application/json",
        **headers
    )

    print("Logout response:", response.status_code, response.content)
    context.response = response
