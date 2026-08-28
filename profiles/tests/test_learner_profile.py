import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from profiles.models import Level, ServiceArea, Subject


@pytest.fixture
def learner_user(db):
    user = get_user_model().objects.create_user(
        email="learner.test@example.com",
        password="Password-2026",
        account_type="LEARNER",
        first_name="Jean",
        last_name="Mukendi",
        email_verified=True,
    )
    return user


@pytest.fixture
def teacher_user(db):
    user = get_user_model().objects.create_user(
        email="teacher.test@example.com",
        password="Password-2026",
        account_type="TEACHER",
        first_name="Alice",
        last_name="Kambale",
        email_verified=True,
    )
    return user


@pytest.mark.django_db
def test_learner_profile_api_get_and_patch(learner_user):
    client = APIClient()
    client.force_authenticate(user=learner_user)

    subject = Subject.objects.first()
    level = Level.objects.first()
    area = ServiceArea.objects.first()

    # GET profile
    response = client.get(reverse("profiles-learner-api:learner-profile"))
    assert response.status_code == 200
    assert response.data["user"]["email"] == learner_user.email

    # PATCH profile
    patch_data = {
        "first_name": "Jean-Marc",
        "last_name": "Mukendi",
        "interest_ids": [subject.pk],
        "level_ids": [level.pk],
        "preferred_service_area_id": area.pk,
    }
    patch_response = client.patch(
        reverse("profiles-learner-api:learner-profile"), patch_data, format="json"
    )
    assert patch_response.status_code == 200
    assert patch_response.data["preferred_service_area"]["id"] == area.pk
    assert patch_response.data["completion_percentage"] == 100

    learner_user.refresh_from_db()
    assert learner_user.first_name == "Jean-Marc"


@pytest.mark.django_db
def test_learner_cannot_access_teacher_profile_api_and_vice_versa(learner_user, teacher_user):
    client = APIClient()

    # Learner calling teacher profile API -> 403
    client.force_authenticate(user=learner_user)
    response = client.get(reverse("profiles-teacher-api:teacher-profile"))
    assert response.status_code == 403

    # Teacher calling learner profile API -> 403
    client.force_authenticate(user=teacher_user)
    response = client.get(reverse("profiles-learner-api:learner-profile"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_learner_profile_catalog_api(learner_user):
    client = APIClient()
    client.force_authenticate(user=learner_user)

    response = client.get(reverse("profiles-learner-api:learner-profile-catalog"))
    assert response.status_code == 200
    assert "levels" in response.data
    assert "interests" in response.data
    assert "service_areas" in response.data


@pytest.mark.django_db
def test_learner_profile_web_views(client, learner_user):
    client.force_login(learner_user)

    # Learner profile detail
    response = client.get(reverse("profiles:learner-profile"))
    assert response.status_code == 200
    assert "Mon profil Apprenant" in response.content.decode()

    # Learner profile edit GET
    response = client.get(reverse("profiles:learner-profile-edit"))
    assert response.status_code == 200

    # Learner profile edit POST
    subject = Subject.objects.first()
    level = Level.objects.first()
    area = ServiceArea.objects.first()
    post_data = {
        "first_name": "Jean-Pierre",
        "last_name": "Mukendi",
        "interests": [subject.pk],
        "levels": [level.pk],
        "preferred_service_area": area.pk,
    }
    response = client.post(reverse("profiles:learner-profile-edit"), post_data)
    assert response.status_code == 302
    assert response.url == reverse("profiles:learner-profile")

    learner_user.refresh_from_db()
    assert learner_user.first_name == "Jean-Pierre"


@pytest.mark.django_db
def test_account_settings_and_deactivation_web_view(client, learner_user):
    client.force_login(learner_user)

    # Settings GET
    response = client.get(reverse("accounts:settings"))
    assert response.status_code == 200
    assert "Paramètres du compte" in response.content.decode()

    # Deactivate account POST
    response = client.post(reverse("accounts:deactivate"))
    assert response.status_code == 302
    assert response.url == reverse("accounts:login")

    learner_user.refresh_from_db()
    assert learner_user.status == get_user_model().Status.DEACTIVATED
    assert learner_user.is_active is False
