from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from bookings.services import create_booking
from learning.models import LearningRequest, Proposal
from messaging.models import Report, ReportAction
from messaging.services import (
    conversations_for_user,
    create_conversation,
    create_report,
    record_moderator_view,
    send_message,
    transition_report,
)
from profiles.models import Level, ServiceArea, Subject, TeachingMode


@pytest.fixture
def conversation_data(db):
    user_model = get_user_model()
    learner = user_model.objects.create_user(
        email="message-learner@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    teacher = user_model.objects.create_user(
        email="message-teacher@example.com",
        password="test-password",
        account_type="TEACHER",
    )
    outsider = user_model.objects.create_user(
        email="message-outsider@example.com",
        password="test-password",
        account_type="LEARNER",
    )
    moderator = user_model.objects.create_user(
        email="moderator@example.com",
        password="test-password",
        is_staff=True,
    )
    moderator.groups.add(Group.objects.get(name="MODERATION"))
    learning_request = LearningRequest.objects.create(
        learner=learner,
        subject=Subject.objects.first(),
        level=Level.objects.first(),
        teaching_mode=TeachingMode.objects.first(),
        service_area=ServiceArea.objects.first(),
        budget_max=25000,
        description="Besoin avec conversation.",
    )
    proposal = Proposal.objects.create(
        learning_request=learning_request,
        teacher=teacher.teacher_profile,
        amount=20000,
        message="Disponible.",
    )
    conversation = create_conversation(
        proposal=proposal,
        actor=learner,
    )
    return learner, teacher, outsider, moderator, proposal, conversation


@pytest.mark.django_db
def test_conversation_access_requires_participation_or_open_report(conversation_data):
    learner, teacher, outsider, moderator, _, conversation = conversation_data

    assert conversations_for_user(learner).get() == conversation
    assert conversations_for_user(teacher).get() == conversation
    assert not conversations_for_user(outsider).exists()
    assert not conversations_for_user(moderator).exists()
    with pytest.raises(PermissionDenied):
        send_message(conversation=conversation, author=outsider, content="Intrusion")

    message = send_message(conversation=conversation, author=teacher, content="Bonjour")
    report = create_report(
        conversation=conversation,
        reporter=learner,
        message=message,
        reason=Report.Reason.HARASSMENT,
        description="À examiner.",
    )

    assert conversations_for_user(moderator).get() == conversation
    record_moderator_view(conversation=conversation, moderator=moderator)
    assert ReportAction.objects.filter(
        report=report,
        actor=moderator,
        action=ReportAction.Action.VIEWED,
    ).exists()


@pytest.mark.django_db
def test_web_conversation_is_private_and_allows_participant_messages(client, conversation_data):
    learner, teacher, outsider, _, _, conversation = conversation_data
    client.force_login(learner)

    response = client.post(
        reverse("messaging:detail", args=(conversation.public_id,)),
        {"content": "Bonjour, ce créneau est-il disponible ?"},
    )

    assert response.status_code == 302
    assert conversation.messages.filter(author=learner).exists()
    client.force_login(teacher)
    assert client.get(conversation.get_absolute_url()).status_code == 200
    client.force_login(outsider)
    assert client.get(conversation.get_absolute_url()).status_code == 404


@pytest.mark.django_db
def test_api_does_not_expose_phone_and_rejects_outsider(conversation_data):
    learner, teacher, outsider, _, _, conversation = conversation_data
    learner.phone_number = "+243810000001"
    learner.save(update_fields=("phone_number",))
    teacher.phone_number = "+243810000002"
    teacher.save(update_fields=("phone_number",))
    send_message(conversation=conversation, author=teacher, content="Message API")
    client = APIClient()
    client.force_authenticate(learner)

    list_response = client.get(reverse("messaging-api:list"))
    messages_response = client.get(
        reverse("messaging-api:messages", args=(conversation.public_id,))
    )

    assert list_response.status_code == 200
    assert messages_response.status_code == 200
    assert "+243" not in str(list_response.data)
    assert "+243" not in str(messages_response.data)
    client.force_authenticate(outsider)
    assert (
        client.get(reverse("messaging-api:messages", args=(conversation.public_id,))).status_code
        == 404
    )


@pytest.mark.django_db
def test_api_report_grants_audited_moderator_read_access(conversation_data):
    learner, teacher, _, moderator, _, conversation = conversation_data
    message = send_message(conversation=conversation, author=teacher, content="À signaler")
    client = APIClient()
    client.force_authenticate(learner)

    report_response = client.post(
        reverse("messaging-api:reports", args=(conversation.public_id,)),
        {
            "message_id": str(message.public_id),
            "reason": Report.Reason.INAPPROPRIATE,
            "description": "Contenu à examiner.",
        },
        format="json",
    )
    assert report_response.status_code == 201

    client.force_authenticate(moderator)
    read_response = client.get(
        reverse("messaging-api:messages", args=(conversation.public_id,))
    )
    assert read_response.status_code == 200
    assert ReportAction.objects.filter(
        report__public_id=report_response.data["public_id"],
        actor=moderator,
        action=ReportAction.Action.VIEWED,
    ).exists()


@pytest.mark.django_db
def test_message_quota_also_protects_service_and_web(conversation_data, monkeypatch):
    learner, _, _, _, _, conversation = conversation_data
    monkeypatch.setattr("messaging.services.MESSAGE_LIMIT_PER_MINUTE", 2)

    send_message(conversation=conversation, author=learner, content="Message 1")
    send_message(conversation=conversation, author=learner, content="Message 2")

    with pytest.raises(ValidationError, match="Trop de messages"):
        send_message(conversation=conversation, author=learner, content="Message 3")


@pytest.mark.django_db
def test_moderation_queue_is_restricted_and_actions_are_audited(client, conversation_data):
    learner, _, outsider, moderator, _, conversation = conversation_data
    report = create_report(
        conversation=conversation,
        reporter=learner,
        reason=Report.Reason.SPAM,
    )
    client.force_login(outsider)
    assert client.get(reverse("messaging:moderation-list")).status_code == 403

    client.force_login(moderator)
    assert client.get(reverse("messaging:moderation-list")).status_code == 200
    detail_response = client.get(
        reverse("messaging:moderation-detail", args=(report.public_id,))
    )
    assert detail_response.status_code == 200
    action_response = client.post(
        reverse("messaging:moderation-detail", args=(report.public_id,)),
        {"action": "resolve", "note": "Contenu examiné."},
    )
    assert action_response.status_code == 302
    report.refresh_from_db()
    assert report.status == Report.Status.RESOLVED
    assert report.actions.filter(
        actor=moderator,
        action=ReportAction.Action.VIEWED,
    ).exists()
    assert report.actions.filter(
        actor=moderator,
        action=ReportAction.Action.RESOLVED,
        note="Contenu examiné.",
    ).exists()

    with pytest.raises(PermissionDenied):
        transition_report(report=report, moderator=outsider, action="dismiss")


@pytest.mark.django_db
def test_moderation_can_warn_suspend_and_restore_report_target(conversation_data):
    learner, teacher, _, moderator, _, conversation = conversation_data
    report = create_report(
        conversation=conversation,
        reporter=learner,
        reason=Report.Reason.HARASSMENT,
    )

    transition_report(report=report, moderator=moderator, action="warn", note="Rappel des règles.")
    assert teacher.notifications.filter(kind="MODERATION_UPDATED").exists()
    transition_report(report=report, moderator=moderator, action="suspend", note="Suspension temporaire.")
    teacher.refresh_from_db()
    assert teacher.status == teacher.Status.SUSPENDED
    assert not teacher.teacher_profile.is_public
    transition_report(report=report, moderator=moderator, action="restore", note="Compte rétabli.")
    teacher.refresh_from_db()
    assert teacher.status == teacher.Status.ACTIVE


@pytest.mark.django_db
def test_external_report_targets_enforce_target_permissions(client, conversation_data):
    learner, teacher, outsider, _, proposal, _ = conversation_data
    teacher.teacher_profile.is_public = True
    teacher.teacher_profile.save(update_fields=("is_public",))
    client.force_login(outsider)

    profile_response = client.post(
        reverse(
            "messaging:report-target",
            args=("profile", teacher.teacher_profile.public_id),
        ),
        {"reason": Report.Reason.OTHER, "description": "Profil à vérifier."},
    )
    assert profile_response.status_code == 302
    assert Report.objects.filter(
        reporter=outsider,
        teacher_profile=teacher.teacher_profile,
    ).exists()
    assert (
        client.get(
            reverse("messaging:report-target", args=("proposal", proposal.public_id))
        ).status_code
        == 404
    )

    start_at = timezone.now() + timedelta(days=2)
    booking = create_booking(
        proposal=proposal,
        learner=learner,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
    )
    assert (
        client.get(
            reverse("messaging:report-target", args=("booking", booking.public_id))
        ).status_code
        == 404
    )

    client.force_login(learner)
    proposal_response = client.post(
        reverse("messaging:report-target", args=("proposal", proposal.public_id)),
        {"reason": Report.Reason.FRAUD, "description": "Proposition à vérifier."},
    )
    booking_response = client.post(
        reverse("messaging:report-target", args=("booking", booking.public_id)),
        {"reason": Report.Reason.OTHER, "description": "Réservation à vérifier."},
    )
    assert proposal_response.status_code == 302
    assert booking_response.status_code == 302
    assert Report.objects.filter(reporter=learner, proposal=proposal).exists()
    assert Report.objects.filter(reporter=learner, booking=booking).exists()
