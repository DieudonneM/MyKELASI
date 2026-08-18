from datetime import time
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from learning.models import LearningEvent, LearningRequest, Proposal
from learning.services import generate_matches
from profiles.models import Availability, Level, ServiceArea, Subject, TeachingMode


def create_teacher(email, name, subject, level, mode, area, rate):
    user = get_user_model().objects.create_user(
        email=email,
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
        first_name=name,
        last_name="Test",
    )
    profile = user.teacher_profile
    profile.headline = "Enseignant expérimenté"
    profile.bio = "Accompagnement pédagogique personnalisé."
    profile.hourly_rate = Decimal(rate)
    profile.languages = "Français"
    profile.is_public = True
    profile.save()
    profile.subjects.add(subject)
    profile.levels.add(level)
    profile.teaching_modes.add(mode)
    profile.service_areas.add(area)
    Availability.objects.create(
        teacher=profile,
        weekday=Availability.Weekday.MONDAY,
        start_time=time(8),
        end_time=time(12),
    )
    return profile


@pytest.fixture
def learning_data(db):
    subject = Subject.objects.get(slug="mathematiques")
    level = Level.objects.get(code="secondaire")
    mode = TeachingMode.objects.get(code="en-ligne")
    area = ServiceArea.objects.get(slug="gombe")
    learner = get_user_model().objects.create_user(
        email="learner@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
        email_verified=True,
    )
    request = LearningRequest.objects.create(
        learner=learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=25000,
        description="Préparation aux examens de mathématiques.",
    )
    return request, subject, level, mode, area


@pytest.mark.django_db
def test_matching_is_ranked_explained_and_limited(learning_data):
    request, subject, level, mode, area = learning_data
    best = create_teacher("best@example.com", "Alice", subject, level, mode, area, "20000")
    other_area = ServiceArea.objects.get(slug="limete")
    second = create_teacher(
        "second@example.com", "Bruno", subject, level, mode, other_area, "30000"
    )

    results = generate_matches(request)

    assert [result.teacher for result in results] == [best, second]
    assert results[0].score > results[1].score
    assert "Matière correspondante" in results[0].reasons
    assert "Budget compatible" in results[0].reasons
    assert request.matches.count() == 2


@pytest.mark.django_db
def test_learner_cannot_read_another_learners_request(client, learning_data):
    request, *_ = learning_data
    other = get_user_model().objects.create_user(
        email="other@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
    )
    client.force_login(other)

    response = client.get(request.get_absolute_url())

    assert response.status_code == 404


@pytest.mark.django_db
def test_matched_teacher_can_send_one_proposal(client, learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("teacher@example.com", "Sarah", subject, level, mode, area, "20000")
    generate_matches(request)
    client.force_login(teacher.user)
    url = reverse("learning:proposal-create", args=(request.public_id,))

    response = client.post(url, {"amount": 20000, "message": "Je suis disponible."})

    assert response.status_code == 302
    proposal = Proposal.objects.get(learning_request=request, teacher=teacher)
    assert proposal.status == Proposal.Status.SENT
    assert request.events.filter(name=LearningEvent.Name.PROPOSAL_SENT).exists()

    duplicate = client.post(url, {"amount": 19000, "message": "Nouvelle offre."})
    assert duplicate.status_code == 200
    assert Proposal.objects.filter(learning_request=request, teacher=teacher).count() == 1


@pytest.mark.django_db
def test_unmatched_teacher_cannot_access_request(client, learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("teacher@example.com", "Sarah", subject, level, mode, area, "20000")
    client.force_login(teacher.user)

    assert client.get(request.get_absolute_url()).status_code == 404
    proposal_url = reverse("learning:proposal-create", args=(request.public_id,))
    assert client.get(proposal_url).status_code == 404


@pytest.mark.django_db
def test_api_creates_request_and_returns_explained_matches(learning_data):
    _, subject, level, mode, area = learning_data
    learner = get_user_model().objects.create_user(
        email="api-learner@example.com",
        password="Strong-password-2026",
        account_type="LEARNER",
    )
    create_teacher("api-teacher@example.com", "Grace", subject, level, mode, area, "18000")
    client = APIClient()
    client.force_authenticate(learner)

    response = client.post(
        reverse("learning-api:request-list"),
        {
            "subject": subject.pk,
            "level": level.pk,
            "teaching_mode": mode.pk,
            "service_area": area.pk,
            "budget_max": "20000.00",
            "frequency": "ONCE",
            "description": "Besoin de cours particuliers.",
        },
        format="json",
    )

    assert response.status_code == 201
    created_request = LearningRequest.objects.get(public_id=response.data["public_id"])
    assert created_request.events.filter(name=LearningEvent.Name.REQUEST_CREATED).exists()
    assert created_request.events.filter(name=LearningEvent.Name.MATCH_CREATED).exists()
    matches = client.get(reverse("learning-api:matches", args=(response.data["public_id"],)))
    assert matches.status_code == 200
    assert matches.data[0]["score"] > 0
    assert matches.data[0]["reasons"]
