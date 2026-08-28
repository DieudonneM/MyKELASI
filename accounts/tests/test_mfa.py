import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.mfa import totp_code
from accounts.models import MfaDevice


@pytest.fixture
def internal_user():
    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="admin@example.com",
        password="test-password",
        is_internal=True,
        email_verified=True,
    )
    user.groups.add(Group.objects.get(name="ADMIN"))
    return user


@pytest.mark.django_db
def test_internal_mfa_enrollment_and_confirmation(internal_user):
    client = APIClient()
    client.force_authenticate(internal_user)

    enroll = client.post(reverse("accounts-api:mfa-enroll"))

    assert enroll.status_code == 201
    assert enroll.data["provisioning_uri"].startswith("otpauth://totp/MyKELASI:")
    device = MfaDevice.objects.get(user=internal_user)
    assert device.confirmed_at is None

    confirm = client.post(
        reverse("accounts-api:mfa-confirm"),
        {"code": totp_code(device.secret)},
        format="json",
    )

    assert confirm.status_code == 200
    assert MfaDevice.objects.get(pk=device.pk).confirmed_at is not None


@pytest.mark.django_db
def test_public_user_cannot_enroll_mfa():
    user = get_user_model().objects.create_user(
        email="learner@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(reverse("accounts-api:mfa-enroll"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_internal_login_requires_valid_mfa_code(internal_user):
    device = MfaDevice.objects.create(user=internal_user, secret="JBSWY3DPEHPK3PXP")
    client = APIClient()

    without_code = client.post(
        reverse("accounts-api:login"),
        {"email": internal_user.email, "password": "test-password"},
        format="json",
    )
    with_code = client.post(
        reverse("accounts-api:login"),
        {
            "email": internal_user.email,
            "password": "test-password",
            "mfa_code": totp_code(device.secret),
        },
        format="json",
    )

    assert without_code.status_code == 401
    assert with_code.status_code == 200
    assert "access" in with_code.data
