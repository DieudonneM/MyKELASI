from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.models import User
from accounts.roles import has_internal_role
from accounts.services import record_audit
from bookings.models import Booking
from learning.models import Proposal
from profiles.models import TeacherProfile
from reviews.models import Review

from .models import Conversation, Message, Report, ReportAction

MESSAGE_LIMIT_PER_MINUTE = 30
REPORT_LIMIT_PER_HOUR = 5


def _enforce_quota(*, key, limit, timeout, error_message):
    if cache.add(key, 1, timeout=timeout):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=timeout)
        return
    if count > limit:
        raise ValidationError(error_message)


def conversations_for_user(user):
    if not user.is_authenticated:
        return Conversation.objects.none()
    participant_filter = Q(learner=user) | Q(teacher=user)
    if has_internal_role(user, "MODERATION"):
        moderated_filter = Q(reports__status__in=(Report.Status.OPEN, Report.Status.IN_REVIEW))
        return Conversation.objects.filter(participant_filter | moderated_filter).distinct()
    return Conversation.objects.filter(participant_filter)


@transaction.atomic
def create_conversation(*, proposal, actor):
    proposal = (
        Proposal.objects.select_for_update()
        .select_related("learning_request__learner", "teacher__user")
        .get(pk=proposal.pk)
    )
    learning_request = proposal.learning_request
    teacher = proposal.teacher.user
    if actor.pk not in (learning_request.learner_id, teacher.pk):
        raise PermissionDenied("Action réservée aux participants.")
    booking = getattr(proposal, "booking", None)
    conversation, _ = Conversation.objects.get_or_create(
        learning_request=learning_request,
        learner=learning_request.learner,
        teacher=teacher,
        defaults={"booking": booking},
    )
    if booking and conversation.booking_id is None:
        conversation.booking = booking
        conversation.save(update_fields=("booking", "updated_at"))
    return conversation


@transaction.atomic
def send_message(*, conversation, author, content):
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    if author.pk not in (conversation.learner_id, conversation.teacher_id):
        raise PermissionDenied("Action réservée aux participants.")
    _enforce_quota(
        key=f"messages:{conversation.public_id}:{author.pk}",
        limit=MESSAGE_LIMIT_PER_MINUTE,
        timeout=60,
        error_message="Trop de messages envoyés. Réessayez dans une minute.",
    )
    content = content.strip()
    if not content:
        raise ValidationError("Le message ne peut pas être vide.")
    message = Message.objects.create(
        conversation=conversation,
        author=author,
        content=content,
    )
    conversation.last_message_at = message.created_at
    conversation.save(update_fields=("last_message_at", "updated_at"))
    return message


@transaction.atomic
def create_report(*, conversation, reporter, reason, description="", message=None):
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    if reporter.pk not in (conversation.learner_id, conversation.teacher_id):
        raise PermissionDenied("Signalement réservé aux participants.")
    _enforce_quota(
        key=f"reports:{conversation.public_id}:{reporter.pk}",
        limit=REPORT_LIMIT_PER_HOUR,
        timeout=3600,
        error_message="Trop de signalements. Réessayez plus tard.",
    )
    if message and message.conversation_id != conversation.pk:
        raise ValidationError("Ce message n'appartient pas à la conversation.")
    return Report.objects.create(
        reporter=reporter,
        conversation=conversation,
        message=message,
        reason=reason,
        description=description.strip(),
    )


def get_reportable_target(*, target_type, public_id, user):
    if target_type == "profile":
        return get_object_or_404(
            TeacherProfile.objects.filter(is_public=True, user__is_active=True),
            public_id=public_id,
        )
    if target_type == "proposal":
        return get_object_or_404(
            Proposal.objects.filter(
                Q(learning_request__learner=user) | Q(teacher__user=user)
            ).distinct(),
            public_id=public_id,
        )
    if target_type == "booking":
        return get_object_or_404(
            Booking.objects.filter(Q(learner=user) | Q(teacher=user)),
            public_id=public_id,
        )
    if target_type == "review":
        return get_object_or_404(
            Review.objects.filter(status=Review.Status.PUBLISHED),
            public_id=public_id,
        )
    raise ValidationError("Type de signalement inconnu.")


@transaction.atomic
def create_target_report(*, target_type, target, reporter, reason, description=""):
    target_fields = {
        "profile": "teacher_profile",
        "proposal": "proposal",
        "booking": "booking",
        "review": "review",
    }
    try:
        target_field = target_fields[target_type]
    except KeyError:
        raise ValidationError("Type de signalement inconnu.") from None
    _enforce_quota(
        key=f"reports:{target_type}:{target.pk}:{reporter.pk}",
        limit=REPORT_LIMIT_PER_HOUR,
        timeout=3600,
        error_message="Trop de signalements. Réessayez plus tard.",
    )
    return Report.objects.create(
        reporter=reporter,
        reason=reason,
        description=description.strip(),
        **{target_field: target},
    )


def record_moderator_view(*, conversation, moderator):
    if not moderator.groups.filter(name="MODERATION").exists():
        return
    report = conversation.reports.filter(
        status__in=(Report.Status.OPEN, Report.Status.IN_REVIEW)
    ).first()
    if report:
        ReportAction.objects.create(
            report=report,
            actor=moderator,
            action=ReportAction.Action.VIEWED,
        )


@transaction.atomic
def transition_report(*, report, moderator, action, note=""):
    if not has_internal_role(moderator, "MODERATION"):
        raise PermissionDenied("Action réservée à la modération.")
    report = Report.objects.select_for_update().get(pk=report.pk)
    transitions = {
        "review": (Report.Status.IN_REVIEW, ReportAction.Action.IN_REVIEW),
        "resolve": (Report.Status.RESOLVED, ReportAction.Action.RESOLVED),
        "dismiss": (Report.Status.DISMISSED, ReportAction.Action.DISMISSED),
        "close": (Report.Status.RESOLVED, ReportAction.Action.RESOLVED),
        "warn": (Report.Status.IN_REVIEW, ReportAction.Action.WARNED),
        "suspend": (Report.Status.IN_REVIEW, ReportAction.Action.SUSPENDED),
        "restore": (Report.Status.IN_REVIEW, ReportAction.Action.RESTORED),
    }
    try:
        status, audit_action = transitions[action]
    except KeyError:
        raise ValidationError("Action de modération inconnue.") from None
    if report.status in (Report.Status.RESOLVED, Report.Status.DISMISSED):
        raise ValidationError("Ce signalement est déjà fermé.")
    report.status = status
    report.save(update_fields=("status", "updated_at"))
    target_user = _report_target_user(report)
    if action == "suspend" and target_user:
        target_user.status = User.Status.SUSPENDED
        target_user.save(update_fields=("status", "updated_at"))
        if hasattr(target_user, "teacher_profile"):
            target_user.teacher_profile.is_public = False
            target_user.teacher_profile.save(update_fields=("is_public", "updated_at"))
    elif action == "restore" and target_user and target_user.status == User.Status.SUSPENDED:
        target_user.status = User.Status.ACTIVE
        target_user.save(update_fields=("status", "updated_at"))
    if target_user and action in {"warn", "suspend", "restore"}:
        from notifications.models import Notification

        Notification.objects.create(
            user=target_user,
            kind=Notification.Kind.MODERATION_UPDATED,
            title="Mise à jour de modération",
            body=note.strip() or "Une action de modération a été appliquée à votre compte.",
        )
    ReportAction.objects.create(
        report=report,
        actor=moderator,
        action=audit_action,
        note=note.strip(),
    )
    record_audit(
        actor=moderator,
        action="moderation.report_transition",
        target=report,
        metadata={"action": action, "status": status},
    )
    return report


def _report_target_user(report):
    if report.teacher_profile_id:
        return report.teacher_profile.user
    if report.proposal_id:
        return report.proposal.teacher.user
    if report.conversation_id:
        return report.conversation.teacher
    if report.booking_id:
        return report.booking.teacher
    if report.review_id:
        return report.review.subject
    return None


@transaction.atomic
def mark_messages_read(*, conversation, reader):
    if reader.pk not in (conversation.learner_id, conversation.teacher_id):
        return 0
    return (
        conversation.messages.exclude(author=reader)
        .filter(read_at__isnull=True)
        .update(read_at=timezone.now())
    )
