import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
def test_registration_verification_and_login_flow(client):
    response = client.post(
        reverse("accounts:register"),
        {
            "email": "learner@example.com",
            "first_name": "Amina",
            "last_name": "Mbuyi",
            "account_type": "LEARNER",
            "password1": "Strong-password-2026",
            "password2": "Strong-password-2026",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:verification-sent")
    user = get_user_model().objects.get(email="learner@example.com")
    assert user.email_verified is False
    assert len(mail.outbox) == 1

    blocked_login = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "Strong-password-2026"},
    )
    assert blocked_login.status_code == 200
    assert "Vérifiez votre adresse email" in blocked_login.content.decode()

    verification_url = re.search(r"https?://[^\s]+", mail.outbox[0].body).group(0)
    verification_response = client.get(verification_url)
    assert verification_response.status_code == 302

    user.refresh_from_db()
    assert user.email_verified is True

    login_response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "Strong-password-2026"},
    )
    assert login_response.status_code == 302
    assert login_response.url == reverse("accounts:dashboard")
    assert client.get(reverse("accounts:dashboard")).status_code == 200


@pytest.mark.django_db
def test_password_reset_uses_generic_response_and_sends_email(client):
    get_user_model().objects.create_user(
        email="teacher@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
    )

    response = client.post(
        reverse("accounts:password-reset"),
        {"email": "teacher@example.com"},
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:password-reset-done")
    assert len(mail.outbox) == 1
    assert "mot de passe" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_invalid_verification_link_is_rejected(client):
    response = client.get(reverse("accounts:verify-email", kwargs={"token": "invalid"}))

    assert response.status_code == 302
    assert response.url == reverse("accounts:verification-invalid")
