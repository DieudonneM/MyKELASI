import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from accounts.tokens import make_email_verification_token


@pytest.mark.django_db
def test_api_registration_verification_login_and_logout(api_client):
    register_response = api_client.post(
        reverse("accounts-api:register"),
        {
            "email": "api-user@example.com",
            "first_name": "David",
            "last_name": "Kanku",
            "account_type": "LEARNER",
            "password": "Strong-password-2026",
            "password_confirm": "Strong-password-2026",
        },
        format="json",
    )

    assert register_response.status_code == 201
    assert "password" not in register_response.data
    assert len(mail.outbox) == 1
    user = get_user_model().objects.get(email="api-user@example.com")

    blocked_login = api_client.post(
        reverse("accounts-api:login"),
        {"email": user.email, "password": "Strong-password-2026"},
        format="json",
    )
    assert blocked_login.status_code == 401

    verify_response = api_client.post(
        reverse("accounts-api:verify-email"),
        {"token": make_email_verification_token(user)},
        format="json",
    )
    assert verify_response.status_code == 200

    login_response = api_client.post(
        reverse("accounts-api:login"),
        {"email": user.email, "password": "Strong-password-2026"},
        format="json",
    )
    assert login_response.status_code == 200
    access = login_response.data["access"]
    refresh = login_response.data["refresh"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    me_response = api_client.get(reverse("accounts-api:me"))
    assert me_response.status_code == 200
    assert me_response.data["email"] == user.email

    logout_response = api_client.post(
        reverse("accounts-api:logout"),
        {"refresh": refresh},
        format="json",
    )
    assert logout_response.status_code == 204

    api_client.credentials()
    refresh_response = api_client.post(
        reverse("accounts-api:refresh"),
        {"refresh": refresh},
        format="json",
    )
    assert refresh_response.status_code == 401


@pytest.mark.django_db
def test_api_me_requires_authentication(api_client):
    response = api_client.get(reverse("accounts-api:me"))

    assert response.status_code == 403


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
