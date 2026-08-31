import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from learning.models import LearningRequest, Proposal
from profiles.models import Level, ServiceArea, Subject, TeachingMode


def request_payload():
    return {
        "subject": Subject.objects.first().pk,
        "level": Level.objects.first().pk,
        "teaching_mode": TeachingMode.objects.first().pk,
        "service_area": ServiceArea.objects.first().pk,
        "budget_max": "20000.00",
        "frequency": "ONCE",
        "description": "Demande de test negative.",
    }


def request_model_values():
    return {
        "subject": Subject.objects.first(),
        "level": Level.objects.first(),
        "teaching_mode": TeachingMode.objects.first(),
        "service_area": ServiceArea.objects.first(),
        "budget_max": "20000.00",
        "description": "Demande de test negative.",
    }


def create_learner(*, email, verified=True):
    return get_user_model().objects.create_user(
        email=email,
        password="Strong-password-2026",
        account_type="LEARNER",
        email_verified=verified,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("verified", "status", "is_active"),
    (
        (False, "ACTIVE", True),
        (True, "SUSPENDED", True),
        (True, "DEACTIVATED", False),
    ),
)
def test_unverified_suspended_or_deactivated_learner_cannot_create_request(
    verified, status, is_active
):
    learner = create_learner(email=f"blocked-{verified}-{status}@example.com", verified=verified)
    learner.status = status
    learner.is_active = is_active
    learner.save(update_fields=("status", "is_active"))
    client = APIClient()
    client.force_authenticate(learner)

    response = client.post("/api/v1/requests/", request_payload(), format="json")

    assert response.status_code == 403
    assert not LearningRequest.objects.filter(learner=learner).exists()


@pytest.mark.django_db
def test_teacher_cannot_create_a_learner_request():
    teacher = get_user_model().objects.create_user(
        email="teacher-negative@example.com",
        password="Strong-password-2026",
        account_type="TEACHER",
        email_verified=True,
    )
    client = APIClient()
    client.force_authenticate(teacher)

    response = client.post("/api/v1/requests/", request_payload(), format="json")

    assert response.status_code == 403
    assert not LearningRequest.objects.exists()


@pytest.mark.django_db
def test_learner_cannot_read_or_modify_another_learners_request():
    owner = create_learner(email="owner-negative@example.com")
    outsider = create_learner(email="outsider-negative@example.com")
    learning_request = LearningRequest.objects.create(learner=owner, **request_model_values())
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=get_user_model()
        .objects.create_user(email="proposal-teacher-negative@example.com", account_type="TEACHER")
        .teacher_profile,
        amount=20000,
        message="Proposition privee.",
    )
    client = APIClient()
    client.force_authenticate(outsider)

    read_response = client.get(f"/api/v1/requests/{learning_request.public_id}/")
    modify_response = client.post(f"/api/v1/proposals/{proposal.public_id}/reject/")

    assert read_response.status_code == 404
    assert modify_response.status_code == 403
    proposal.refresh_from_db()
    assert proposal.status == Proposal.Status.SENT


@pytest.mark.django_db
def test_internal_role_cannot_access_another_teams_endpoint():
    support = get_user_model().objects.create_user(
        email="support-negative@example.com", password="Strong-password-2026", is_internal=True
    )
    support.groups.add(Group.objects.get(name="SUPPORT"))
    client = APIClient()
    client.force_authenticate(support)

    response = client.get("/api/v1/verification/queue/")

    assert response.status_code == 403
