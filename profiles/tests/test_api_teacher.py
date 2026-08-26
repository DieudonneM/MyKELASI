from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from profiles.models import Availability, Level, ServiceArea, Subject, TeachingMode


def teacher_with_complete_profile(email="api-teacher@example.com"):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(
        email=email,
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
        first_name="Aline",
        last_name="Mukendi",
    )
    profile = user.teacher_profile
    profile.headline = "Formatrice"
    profile.bio = "Présentation"
    profile.years_experience = 5
    profile.hourly_rate = Decimal("25000.00")
    profile.languages = "Français"
    profile.save()
    profile.subjects.add(Subject.objects.first())
    profile.levels.add(Level.objects.first())
    profile.teaching_modes.add(TeachingMode.objects.first())
    profile.service_areas.add(ServiceArea.objects.first())
    return user


@pytest.mark.django_db
def test_teacher_profile_api_reads_and_updates_identity_and_offer():
    user = teacher_with_complete_profile()
    client = APIClient()
    client.force_authenticate(user)

    response = client.get(reverse("profiles-teacher-api:teacher-profile"))
    assert response.status_code == 200
    assert response.data["currency"] == "CDF"
    assert response.data["subjects"][0]["id"] == Subject.objects.first().id
    assert response.data["can_publish"] is True

    response = client.patch(
        reverse("profiles-teacher-api:teacher-profile"),
        {"first_name": "Sarah", "hourly_rate": "30000.00", "is_public": True},
        format="json",
    )
    user.refresh_from_db()
    assert response.status_code == 200
    assert user.first_name == "Sarah"
    assert response.data["hourly_rate"] == "30000.00"
    assert response.data["is_public"] is True


@pytest.mark.django_db
def test_teacher_api_urls_match_flutter_contract():
    assert reverse("profiles-teacher-api:teacher-profile") == "/api/v1/teacher/profile/"
    assert reverse("profiles-teacher-api:teacher-profile-catalog") == (
        "/api/v1/teacher/profile/catalog/"
    )
    assert (
        reverse("profiles-teacher-api:teacher-availabilities") == "/api/v1/teacher/availabilities/"
    )
    assert reverse("profiles-teacher-api:teacher-availability-detail", kwargs={"pk": 7}) == (
        "/api/v1/teacher/availabilities/7/"
    )


@pytest.mark.django_db
def test_teacher_profile_catalog_returns_only_active_references():
    user = teacher_with_complete_profile()
    inactive_subject = Subject.objects.create(
        name="Matière inactive",
        slug="matiere-inactive",
        is_active=False,
    )
    client = APIClient()
    client.force_authenticate(user)

    response = client.get(reverse("profiles-teacher-api:teacher-profile-catalog"))

    assert response.status_code == 200
    assert set(response.data) == {
        "subjects",
        "levels",
        "teaching_modes",
        "service_areas",
    }
    assert inactive_subject.pk not in {item["id"] for item in response.data["subjects"]}
    assert response.data["levels"][0]["code"] == Level.objects.first().code
    assert response.data["teaching_modes"]
    assert response.data["service_areas"]


@pytest.mark.django_db
def test_profile_api_blocks_learner_and_incomplete_publication():
    from django.contrib.auth import get_user_model

    learner = get_user_model().objects.create_user(
        email="learner-api@example.com", account_type="LEARNER"
    )
    client = APIClient()
    client.force_authenticate(learner)
    assert client.get(reverse("profiles-teacher-api:teacher-profile")).status_code == 403

    user = get_user_model().objects.create_user(
        email="incomplete-api@example.com", account_type="TEACHER", email_verified=False
    )
    client.force_authenticate(user)
    response = client.patch(
        reverse("profiles-teacher-api:teacher-profile"), {"is_public": True}, format="json"
    )
    assert response.status_code == 400
    assert "is_public" in response.data

    response = client.get(reverse("profiles-teacher-api:teacher-profile"))
    assert response.status_code == 200
    assert response.data["completion_percentage"] == 0
    assert response.data["can_publish"] is False
    assert [requirement["code"] for requirement in response.data["missing_requirements"]] == [
        "first_name",
        "last_name",
        "headline",
        "bio",
        "hourly_rate",
        "subjects",
        "levels",
        "teaching_modes",
        "service_areas",
    ]


@pytest.mark.django_db
def test_availability_api_is_scoped_and_validates_overlap():
    user = teacher_with_complete_profile("availability-api@example.com")
    other = teacher_with_complete_profile("other-availability-api@example.com")
    client = APIClient()
    client.force_authenticate(user)
    url = reverse("profiles-teacher-api:teacher-availabilities")

    created = client.post(
        url, {"weekday": 1, "start_time": "08:00:00", "end_time": "10:00:00"}, format="json"
    )
    assert created.status_code == 201
    assert Availability.objects.filter(teacher=user.teacher_profile).count() == 1

    conflict = client.post(
        url, {"weekday": 1, "start_time": "09:00:00", "end_time": "11:00:00"}, format="json"
    )
    assert conflict.status_code == 400
    assert "weekday" in conflict.data

    client.force_authenticate(other)
    assert client.get(url).data["count"] == 0
