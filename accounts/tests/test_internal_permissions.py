import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.models import AuditLog
from accounts.roles import INTERNAL_ROLE_NAMES


def role_client(role):
    user = get_user_model().objects.create_user(
        email=f"{role.lower()}@example.com",
        password="Strong-password-2026",
        is_internal=True,
    )
    user.groups.add(Group.objects.get(name=role))
    client = APIClient()
    client.force_authenticate(user)
    return client, user


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "allowed_paths"),
    (
        ("SUPPORT", {"/api/v1/auth/internal/support/"}),
        ("VERIFICATION", {"/api/v1/verification/queue/"}),
        ("FINANCE", set()),
        ("MODERATION", set()),
        (
            "ADMIN",
            {
                "/api/v1/auth/internal/support/",
                "/api/v1/internal/referentials/subjects/",
                "/api/v1/analytics/",
            },
        ),
        (
            "SUPER_ADMIN",
            {
                "/api/v1/auth/internal/support/",
                "/api/v1/internal/referentials/subjects/",
                "/api/v1/analytics/",
            },
        ),
    ),
)
def test_internal_roles_are_isolated_to_their_authorized_api(role, allowed_paths):
    client, _ = role_client(role)
    protected_paths = (
        "/api/v1/auth/internal/support/",
        "/api/v1/verification/queue/",
        "/api/v1/internal/referentials/subjects/",
        "/api/v1/analytics/",
    )

    for path in protected_paths:
        response = client.get(path)
        assert response.status_code == (200 if path in allowed_paths else 403)


@pytest.mark.django_db
def test_support_view_is_audited_and_limits_visible_user_fields():
    client, user = role_client("SUPPORT")
    public_user = get_user_model().objects.create_user(
        email="public-user@example.com", account_type="LEARNER"
    )

    response = client.get("/api/v1/auth/internal/support/")

    assert response.status_code == 200
    assert response.data["users"] == [
        {
            "id": public_user.pk,
            "email": public_user.email,
            "first_name": "",
            "last_name": "",
            "status": "ACTIVE",
        }
    ]
    assert AuditLog.objects.filter(actor=user, action="support.dashboard_view").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "path", "action"),
    (
        ("VERIFICATION", "/api/v1/verification/queue/", "verification.queue_view"),
        ("ADMIN", "/api/v1/internal/referentials/subjects/", "referential.list"),
        ("ADMIN", "/api/v1/analytics/", "analytics.dashboard_view"),
    ),
)
def test_sensitive_internal_consultations_are_audited(role, path, action):
    client, user = role_client(role)

    response = client.get(path)

    assert response.status_code == 200
    assert AuditLog.objects.filter(actor=user, action=action).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("account_status", ("SUSPENDED", "DEACTIVATED"))
def test_suspended_or_deactivated_internal_account_loses_access(account_status):
    client, user = role_client("ADMIN")
    user.status = account_status
    user.is_active = account_status != "DEACTIVATED"
    user.save(update_fields=("status", "is_active"))

    assert client.get("/api/v1/internal/referentials/subjects/").status_code == 403


@pytest.mark.django_db
def test_removing_internal_role_revokes_direct_api_access():
    client, user = role_client("VERIFICATION")
    user.groups.remove(Group.objects.get(name="VERIFICATION"))

    assert client.get("/api/v1/verification/queue/").status_code == 403


@pytest.mark.django_db
def test_all_internal_roles_exist():
    assert set(INTERNAL_ROLE_NAMES).issubset(set(Group.objects.values_list("name", flat=True)))
