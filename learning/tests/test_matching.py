from datetime import time, timedelta
from decimal import Decimal

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from bookings.models import Booking, Session
from learning.models import LearningEvent, LearningRequest, MatchResult, Proposal
from learning.services import _score_teacher, generate_matches
from profiles.models import Availability, Level, ServiceArea, Subject, TeachingMode
from reviews.models import Review
from notifications.models import Notification


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
    assert request.events.filter(name=LearningEvent.Name.MATCH_CREATED).count() == 1
    generate_matches(request)
    assert request.events.filter(name=LearningEvent.Name.MATCH_CREATED).count() == 1


@pytest.mark.django_db
def test_teacher_matching_contract_lists_requests_and_creates_proposal(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("contract-teacher@example.com", "Aline", subject, level, mode, area, "20000")
    generate_matches(request)
    client = APIClient()
    client.force_authenticate(teacher.user)
    matched = client.get("/api/v1/teacher/matched-requests/")
    assert matched.status_code == 200
    assert matched.data["results"][0]["match_reasons"]
    proposal = client.post(
        f"/api/v1/teacher/proposals/{request.pk}/",
        {"hourly_rate": "20000", "message": "Je peux vous accompagner efficacement.", "availability": "Lundi 8h"},
        format="json",
    )
    assert proposal.status_code == 201
    assert proposal.data["request_id"] == request.pk

@pytest.mark.django_db
def test_learner_sees_match_score_reasons_on_request_detail(client, learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("explained@example.com", "Alice", subject, level, mode, area, "20000")
    generate_matches(request)
    client.force_login(request.learner)

    response = client.get(request.get_absolute_url())

    assert response.status_code == 200
    content = response.content.decode()
    assert "Pourquoi ce profil correspond" in content
    assert "Matière correspondante" in content
    assert "Budget compatible" in content
    assert str(request.matches.get(teacher=teacher).score) in content


@pytest.mark.django_db
@override_settings(
    MATCHING_WEIGHTS={
        "subject": 5,
        "level": 40,
        "teaching_mode": 2,
        "service_area": 1,
        "budget": 1,
        "availability": 1,
        "reliability": 0,
        "reputation": 0,
        "response_rate": 0,
    }
)
def test_matching_score_uses_configured_weights(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("weighted@example.com", "Alice", subject, level, mode, area, "20000")

    score, _ = _score_teacher(request, teacher)

    assert score == 50


@pytest.mark.django_db
@override_settings(
    MATCHING_WEIGHTS={
        "subject": 0,
        "level": 0,
        "teaching_mode": 0,
        "service_area": 0,
        "budget": 0,
        "availability": 0,
        "reliability": 10,
        "reputation": 10,
        "response_rate": 5,
    }
)
def test_matching_score_includes_reliability_reputation_and_response_rate(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("signals@example.com", "Alice", subject, level, mode, area, "20000")
    proposal = Proposal.objects.create(
        learning_request=request,
        teacher=teacher,
        amount=20000,
        message="Disponible pour cette demande.",
    )
    MatchResult.objects.create(
        learning_request=request,
        teacher=teacher,
        score=0,
        reasons=[],
    )
    now = timezone.now()
    booking = Booking.objects.create(
        proposal=proposal,
        learner=request.learner,
        teacher=teacher.user,
        start_at=now,
        end_at=now + timedelta(hours=1),
        teaching_mode=mode,
        service_area=area,
        amount=20000,
        cancellation_policy="Annulation selon les conditions affichées.",
        status=Booking.Status.COMPLETED,
    )
    Session.objects.create(
        booking=booking,
        teacher_present_at=now,
        actual_started_at=now,
        actual_ended_at=now + timedelta(hours=1),
    )
    Review.objects.create(
        session=booking.session,
        reviewer=request.learner,
        subject=teacher.user,
        rating=5,
        punctuality=5,
        communication=5,
        quality=5,
    )

    score, reasons = _score_teacher(request, teacher)

    assert score == 25
    assert "Fiabilité basée sur les sessions terminées" in reasons
    assert "Réputation basée sur les avis publiés" in reasons
    assert "Taux de réponse basé sur les propositions envoyées" in reasons


@pytest.mark.django_db
def test_premium_status_is_not_an_organic_matching_factor(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("organic@example.com", "Alice", subject, level, mode, area, "20000")

    score, reasons = _score_teacher(request, teacher)

    assert "premium" not in settings.MATCHING_WEIGHTS
    assert score == 75
    assert all("premium" not in reason.lower() for reason in reasons)


@pytest.mark.django_db
def test_learning_request_requires_a_complete_time_slot(learning_data):
    request, *_ = learning_data
    request.preferred_date = request.created_at.date()
    request.preferred_start_time = None

    with pytest.raises(ValidationError):
        request.full_clean()


@pytest.mark.django_db
def test_learning_request_accepts_a_complete_time_slot(learning_data):
    request, *_ = learning_data
    request.preferred_date = request.created_at.date()
    request.preferred_start_time = time(9)

    request.full_clean()


@pytest.mark.django_db
def test_short_request_form_exposes_only_essential_fields(client, learning_data):
    client.force_login(learning_data[0].learner)

    response = client.get(reverse("learning:request-create"))

    assert response.status_code == 200
    assert set(response.context["form"].fields) == {
        "subject",
        "level",
        "teaching_mode",
        "budget_max",
        "description",
    }
    assert "Ajouter les détails de ma demande" in response.content.decode()


@pytest.mark.django_db
def test_detailed_request_form_creates_request_with_schedule(client, learning_data):
    request, subject, level, mode, area = learning_data
    client.force_login(request.learner)

    response = client.post(
        reverse("learning:request-create-detailed"),
        {
            "subject": subject.pk,
            "level": level.pk,
            "teaching_mode": mode.pk,
            "service_area": area.pk,
            "budget_max": "20000.00",
            "preferred_date": "2026-09-01",
            "preferred_start_time": "09:00",
            "frequency": "WEEKLY",
            "description": "Cours hebdomadaires de préparation.",
        },
    )

    assert response.status_code == 302
    created_request = LearningRequest.objects.exclude(pk=request.pk).get()
    assert created_request.preferred_date.isoformat() == "2026-09-01"
    assert created_request.preferred_start_time == time(9)
    assert created_request.frequency == LearningRequest.Frequency.WEEKLY


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
def test_api_request_access_requires_owner_or_matched_teacher(learning_data):
    request, subject, level, mode, area = learning_data
    matched_teacher = create_teacher(
        "matched-api-access@example.com", "Sarah", subject, level, mode, area, "20000"
    )
    unmatched_teacher = create_teacher(
        "unmatched-api-access@example.com", "Paul", subject, level, mode, area, "20000"
    )
    unmatched_teacher.subjects.clear()
    generate_matches(request)
    client = APIClient()
    url = reverse("learning-api:request-detail", args=(request.public_id,))

    client.force_authenticate(matched_teacher.user)
    assert client.get(url).status_code == 200

    client.force_authenticate(unmatched_teacher.user)
    assert client.get(url).status_code == 404

    staff = get_user_model().objects.create_user(
        email="staff-access@example.com",
        password="Strong-password-2026",
        is_staff=True,
    )
    client.force_authenticate(staff)
    assert client.get(url).status_code == 404
    assert client.get(reverse("learning-api:proposals", args=(request.public_id,))).status_code == 403


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


@pytest.mark.django_db
def test_api_matched_teacher_can_create_only_one_proposal(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("api-proposal@example.com", "Grace", subject, level, mode, area, "18000")
    generate_matches(request)
    client = APIClient()
    client.force_authenticate(teacher.user)
    url = reverse("learning-api:proposals", args=(request.public_id,))
    payload = {"amount": "18000.00", "message": "Je peux vous accompagner."}

    response = client.post(url, payload, format="json")
    duplicate = client.post(url, payload, format="json")

    assert response.status_code == 201
    assert duplicate.status_code == 400
    assert Proposal.objects.filter(learning_request=request, teacher=teacher).count() == 1
    assert request.events.filter(name=LearningEvent.Name.PROPOSAL_SENT).count() == 1

    request.status = LearningRequest.Status.CLOSED
    request.save(update_fields=("status", "updated_at"))
    another_request = LearningRequest.objects.create(
        learner=request.learner,
        subject=subject,
        level=level,
        teaching_mode=mode,
        service_area=area,
        budget_max=20000,
        description="Autre besoin de cours.",
        status=LearningRequest.Status.CLOSED,
    )
    MatchResult.objects.create(learning_request=another_request, teacher=teacher, score=50, reasons=[])
    closed_response = client.post(
        reverse("learning-api:proposals", args=(another_request.public_id,)),
        payload,
        format="json",
    )

    assert closed_response.status_code == 400


@pytest.mark.django_db
def test_learner_can_accept_one_proposal_and_lock_the_others(learning_data):
    request, subject, level, mode, area = learning_data
    first = create_teacher("first-choice@example.com", "Alice", subject, level, mode, area, "18000")
    second = create_teacher("second-choice@example.com", "Bruno", subject, level, mode, area, "20000")
    generate_matches(request)
    first_proposal = Proposal.objects.create(
        learning_request=request, teacher=first, amount=18000, message="Je suis disponible.",
    )
    second_proposal = Proposal.objects.create(
        learning_request=request, teacher=second, amount=20000, message="Je peux vous aider.",
    )
    client = APIClient()
    client.force_authenticate(request.learner)

    response = client.post(
        reverse("learning-api:proposal-action", args=(first_proposal.public_id, "accept")),
    )

    assert response.status_code == 200
    first_proposal.refresh_from_db()
    second_proposal.refresh_from_db()
    request.refresh_from_db()
    assert first_proposal.status == Proposal.Status.ACCEPTED
    assert second_proposal.status == Proposal.Status.REJECTED
    assert request.status == LearningRequest.Status.CLOSED
    assert request.events.filter(name=LearningEvent.Name.PROPOSAL_ACCEPTED).count() == 1
    assert Notification.objects.filter(
        proposal=first_proposal,
        kind=Notification.Kind.PROPOSAL_ACCEPTED,
    ).count() == 2

    repeated = client.post(
        reverse("learning-api:proposal-action", args=(first_proposal.public_id, "accept")),
    )
    assert repeated.status_code == 200
    assert request.events.filter(name=LearningEvent.Name.PROPOSAL_ACCEPTED).count() == 1


@pytest.mark.django_db
def test_only_owner_can_reject_a_proposal(learning_data):
    request, subject, level, mode, area = learning_data
    teacher = create_teacher("reject-teacher@example.com", "Alice", subject, level, mode, area, "18000")
    generate_matches(request)
    proposal = Proposal.objects.create(
        learning_request=request, teacher=teacher, amount=18000, message="Je suis disponible.",
    )
    client = APIClient()
    other = get_user_model().objects.create_user(email="other-learner@example.com", account_type="LEARNER")
    client.force_authenticate(other)

    response = client.post(
        reverse("learning-api:proposal-action", args=(proposal.public_id, "reject")),
    )

    assert response.status_code == 403
    proposal.refresh_from_db()
    assert proposal.status == Proposal.Status.SENT
