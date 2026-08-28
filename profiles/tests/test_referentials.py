import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from rest_framework.test import APIClient

from accounts.models import AuditLog
from profiles.models import ConfigurationVersion, Subject, TeacherProfile
from profiles.services import booking_currency, cancellation_policy, payment_commission_rate


def admin_client():
    user = get_user_model().objects.create_user(
        email="referentials-admin@example.com",
        password="Strong-password-2026",
        is_internal=True,
    )
    user.groups.add(Group.objects.get(name="ADMIN"))
    client = APIClient()
    client.force_authenticate(user)
    return client, user


@pytest.mark.django_db
def test_referentials_api_requires_admin_role():
    client = APIClient()
    client.force_authenticate(get_user_model().objects.create_user(email="learner@example.com"))

    assert client.get("/api/v1/internal/referentials/subjects/").status_code == 403


@pytest.mark.django_db
def test_admin_can_crud_and_deactivate_subject_with_audit():
    client, admin = admin_client()
    created = client.post(
        "/api/v1/internal/referentials/subjects/",
        {"name": "Robotique", "code": "robotique"},
        format="json",
    )

    assert created.status_code == 201
    subject_id = created.data["id"]
    updated = client.patch(
        f"/api/v1/internal/referentials/subjects/{subject_id}/",
        {"is_active": False},
        format="json",
    )

    assert updated.status_code == 200
    assert updated.data["is_active"] is False
    assert AuditLog.objects.filter(actor=admin, action="referential.update").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("kind", "payload"),
    (
        ("subjects", {"name": "Robotique", "code": "robotique"}),
        ("levels", {"name": "Doctorat", "code": "doctorat", "order": 6}),
        ("teaching-modes", {"name": "Hybride", "code": "hybride"}),
        ("service-areas", {"name": "Nouvelle zone", "code": "nouvelle-zone"}),
    ),
)
def test_admin_can_create_each_referential_kind(kind, payload):
    client, _ = admin_client()

    response = client.post(f"/api/v1/internal/referentials/{kind}/", payload, format="json")

    assert response.status_code == 201
    assert response.data["is_active"] is True


@pytest.mark.django_db
def test_referential_in_use_cannot_be_deleted_and_remains_historical():
    client, _ = admin_client()
    subject = Subject.objects.first()
    teacher = get_user_model().objects.create_user(
        email="referential-teacher@example.com", account_type="TEACHER"
    )
    teacher_profile = TeacherProfile.objects.get(user=teacher)
    teacher_profile.subjects.add(subject)

    response = client.delete(f"/api/v1/internal/referentials/subjects/{subject.pk}/")

    assert response.status_code == 409
    subject.refresh_from_db()
    assert subject.is_active is True


@pytest.mark.django_db
def test_inactive_referential_is_rejected_for_new_teacher_profile_mutation():
    client, _ = admin_client()
    subject = Subject.objects.first()
    client.patch(
        f"/api/v1/internal/referentials/subjects/{subject.pk}/",
        {"is_active": False},
        format="json",
    )
    teacher = get_user_model().objects.create_user(
        email="inactive-reference@example.com", account_type="TEACHER"
    )
    teacher_client = APIClient()
    teacher_client.force_authenticate(teacher)

    response = teacher_client.patch(
        "/api/v1/teacher/profile/",
        {"subject_ids": [subject.pk]},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("matching_weights", {"subject": 25}),
        ("payment_commission", {"rate": "0.12"}),
        ("currency", {"code": "CDF"}),
        ("policies", {"cancellation": "24h"}),
    ),
)
def test_admin_publishes_immutable_configuration_versions(key, value):
    client, admin = admin_client()
    response = client.post(
        "/api/v1/internal/configurations/",
        {"key": key, "value": value},
        format="json",
    )

    assert response.status_code == 201
    configuration = ConfigurationVersion.objects.get(pk=response.data["id"])
    assert configuration.version == 1
    assert configuration.created_by == admin
    with pytest.raises(ValueError, match="immuable"):
        configuration.save()
    assert AuditLog.objects.filter(actor=admin, action="configuration.publish").exists()


@pytest.mark.django_db
def test_configuration_versions_are_sequential_and_invalid_values_are_rejected():
    client, _ = admin_client()
    first = client.post(
        "/api/v1/internal/configurations/",
        {"key": "matching_weights", "value": {"subject": 25}},
        format="json",
    )
    second = client.post(
        "/api/v1/internal/configurations/",
        {"key": "matching_weights", "value": {"subject": 30}},
        format="json",
    )
    invalid = client.post(
        "/api/v1/internal/configurations/",
        {"key": "currency", "value": {"code": "USD"}},
        format="json",
    )

    assert first.data["version"] == 1
    assert second.data["version"] == 2
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_configuration_version_uniqueness_prevents_concurrent_publication_conflicts():
    admin = get_user_model().objects.create_user(email="concurrency-admin@example.com")
    ConfigurationVersion.objects.create(
        key="matching_weights", version=1, value={"subject": 25}, created_by=admin
    )

    with pytest.raises(IntegrityError):
        ConfigurationVersion.objects.create(
            key="matching_weights", version=1, value={"subject": 30}, created_by=admin
        )


@pytest.mark.django_db
def test_published_configuration_is_used_for_new_operations():
    admin = get_user_model().objects.create_user(email="configuration-admin@example.com")
    ConfigurationVersion.objects.create(
        key="payment_commission", version=1, value={"rate": "0.12"}, created_by=admin
    )
    ConfigurationVersion.objects.create(
        key="currency", version=1, value={"code": "CDF"}, created_by=admin
    )
    ConfigurationVersion.objects.create(
        key="policies",
        version=1,
        value={"cancellation": "Annulation configurable."},
        created_by=admin,
    )

    assert payment_commission_rate() == "0.12"
    assert booking_currency() == "CDF"
    assert cancellation_policy() == "Annulation configurable."
