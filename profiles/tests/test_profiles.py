import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from profiles.models import Level, ServiceArea, Subject, TeachingMode


@pytest.mark.django_db
def test_account_creation_creates_matching_profile():
    user_model = get_user_model()
    learner = user_model.objects.create_user(email="learner@example.com", account_type="LEARNER")
    teacher = user_model.objects.create_user(email="teacher@example.com", account_type="TEACHER")

    assert learner.learner_profile.user == learner
    assert teacher.teacher_profile.user == teacher


@pytest.mark.django_db
def test_complete_verified_teacher_can_publish(client):
    user = get_user_model().objects.create_user(
        email="teacher@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
        first_name="Sarah",
        last_name="Ilunga",
    )
    profile = user.teacher_profile
    profile.headline = "Professeure de mathématiques"
    profile.bio = "Cours personnalisés pour progresser durablement."
    profile.years_experience = 5
    profile.hourly_rate = 25000
    profile.languages = "Français, lingala"
    profile.save()
    profile.subjects.add(Subject.objects.first())
    profile.levels.add(Level.objects.first())
    profile.teaching_modes.add(TeachingMode.objects.first())
    profile.service_areas.add(ServiceArea.objects.first())

    assert profile.completion_percentage == 100
    assert profile.can_publish is True

    client.force_login(user)
    response = client.post(reverse("profiles:onboarding-publish"), {"confirm": True})

    profile.refresh_from_db()
    assert response.status_code == 302
    assert profile.is_public is True
    assert client.get(profile.get_absolute_url()).status_code == 200


@pytest.mark.django_db
def test_private_teacher_profile_returns_404(client):
    user = get_user_model().objects.create_user(
        email="private@example.com",
        account_type="TEACHER",
    )

    response = client.get(user.teacher_profile.get_absolute_url())

    assert response.status_code == 404


@pytest.mark.django_db
def test_learner_cannot_open_teacher_onboarding(client):
    learner = get_user_model().objects.create_user(
        email="learner@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
    )
    client.force_login(learner)

    response = client.get(reverse("profiles:onboarding-identity"))

    assert response.status_code == 403
