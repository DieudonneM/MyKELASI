from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.models import Booking, Session
from bookings.services import create_booking, mark_session_presence, transition_booking
from learning.models import LearningEvent, LearningRequest, Proposal
from messaging.models import Report
from messaging.services import get_reportable_target
from profiles.models import Level, ServiceArea, Subject, TeachingMode
from reviews.models import Review, TrustScoreSnapshot
from reviews.services import create_review, create_review_response, moderate_review


@pytest.fixture
def review_data(db):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="review-learner@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    teacher = user_model.objects.create_user(
        email="review-teacher@example.com",
        password="test-password",
        account_type="TEACHER",
        email_verified=True,
    )
    outsider = user_model.objects.create_user(
        email="review-outsider@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    learning_request = LearningRequest.objects.create(
        learner=learner,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=25000,
        description="Session à évaluer.",
    )
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible.",
    )
    start_at = timezone.now() + timedelta(days=2)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    booking = transition_booking(booking=booking, actor=teacher, action="confirm")
    return learner, teacher, outsider, learning_request, booking


def review_values():
    return {
        "rating": 5,
        "punctuality": 4,
        "communication": 5,
        "quality": 5,
        "comment": "Session claire et utile.",
    }


def complete_booking(booking, learner, teacher):
    Session.objects.get_or_create(booking=booking)
    Booking.objects.filter(pk=booking.pk).update(
        start_at=timezone.now() - timedelta(hours=2),
        end_at=timezone.now() - timedelta(hours=1),
    )
    booking.refresh_from_db()
    mark_session_presence(booking=booking, actor=learner)
    mark_session_presence(booking=booking, actor=teacher)
    return transition_booking(booking=booking, actor=teacher, action="complete")


@pytest.mark.django_db
def test_review_requires_completed_transaction_participant_and_is_unique(review_data):
    learner, teacher, outsider, learning_request, booking = review_data
    Session.objects.create(booking=booking)
    with pytest.raises(ValidationError, match="session terminée"):
        create_review(session=booking.session, reviewer=learner, **review_values())

    booking = complete_booking(booking, learner, teacher)

    with pytest.raises(PermissionDenied):
        create_review(session=booking.session, reviewer=outsider, **review_values())
    review = create_review(session=booking.session, reviewer=learner, **review_values())

    assert review.subject == teacher
    assert review.status == Review.Status.PUBLISHED
    assert learning_request.events.filter(name=LearningEvent.Name.REVIEW_CREATED).exists()
    snapshot = TrustScoreSnapshot.objects.get(teacher_profile=teacher.teacher_profile)
    assert snapshot.version == "trust-v1"
    assert snapshot.components["reviews"] == 95.0
    assert snapshot.input_counts["published_reviews"] == 1
    with pytest.raises(ValidationError, match="déjà publié"):
        create_review(session=booking.session, reviewer=learner, **review_values())


@pytest.mark.django_db
def test_public_review_response_and_moderation_recalculate_score(client, review_data):
    learner, teacher, outsider, _, booking = review_data
    booking = complete_booking(booking, learner, teacher)
    review = create_review(session=booking.session, reviewer=learner, **review_values())
    teacher.teacher_profile.is_public = True
    teacher.teacher_profile.save(update_fields=("is_public",))

    public_response = client.get(teacher.teacher_profile.get_absolute_url())
    assert public_response.status_code == 200
    assert review.comment in public_response.content.decode()
    assert "Trust Score" in public_response.content.decode()

    client.force_login(outsider)
    report_response = client.post(
        reverse("messaging:report-target", args=("review", review.public_id)),
        {"reason": Report.Reason.INAPPROPRIATE, "description": "Avis à vérifier."},
    )
    assert report_response.status_code == 302
    assert Report.objects.filter(reporter=outsider, review=review).exists()

    with pytest.raises(PermissionDenied):
        create_review_response(review=review, author=outsider, content="Réponse interdite")
    response = create_review_response(
        review=review,
        author=teacher,
        content="Merci pour votre retour.",
    )
    assert response.author == teacher

    moderator = get_user_model().objects.create_user(
        email="review-moderator@example.com",
        password="test-password",
        is_staff=True,
    )
    moderator.groups.add(Group.objects.get(name="MODERATION"))
    snapshots_before = TrustScoreSnapshot.objects.filter(
        teacher_profile=teacher.teacher_profile
    ).count()
    moderate_review(
        review=review,
        moderator=moderator,
        action="hide",
        reason="Contenu masqué après vérification.",
    )

    assert TrustScoreSnapshot.objects.filter(
        teacher_profile=teacher.teacher_profile
    ).count() == snapshots_before + 1
    assert "reviews" not in teacher.teacher_profile.trust_score_snapshots.first().components
    hidden_response = client.get(teacher.teacher_profile.get_absolute_url())
    assert review.comment not in hidden_response.content.decode()
    with pytest.raises(Http404):
        get_reportable_target(
            target_type="review",
            public_id=review.public_id,
            user=outsider,
        )


@pytest.mark.django_db
def test_review_api_creation_and_public_listing(review_data):
    learner, teacher, outsider, _, booking = review_data
    booking = complete_booking(booking, learner, teacher)
    teacher.teacher_profile.is_public = True
    teacher.teacher_profile.save(update_fields=("is_public",))
    client = APIClient()
    client.force_authenticate(outsider)
    payload = review_values()

    outsider_response = client.post(
        reverse("reviews-api:create", args=(booking.public_id,)),
        payload,
        format="json",
    )
    assert outsider_response.status_code == 404

    client.force_authenticate(learner)
    create_response = client.post(
        reverse("reviews-api:create", args=(booking.public_id,)),
        payload,
        format="json",
    )
    assert create_response.status_code == 201
    client.force_authenticate(user=None)
    list_response = client.get(
        reverse("reviews-api:list", args=(teacher.teacher_profile.public_id,))
    )
    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
