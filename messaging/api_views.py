from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.roles import has_internal_role
from accounts.services import record_audit

from .models import Report
from .serializers import (
    ConversationAccessSerializer,
    ConversationCreateSerializer,
    ConversationSerializer,
    InternalReportActionSerializer,
    InternalReportSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ReportActionRequestSerializer,
    ReportAssignmentSerializer,
    ReportCreateSerializer,
)
from .services import (
    conversations_for_user,
    create_conversation,
    create_report,
    grant_temporary_conversation_access,
    mark_messages_read,
    record_moderator_view,
    send_message,
    transition_report,
)


class ConversationListCreateAPIView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        return conversations_for_user(self.request.user).select_related(
            "learner", "teacher", "learning_request__subject"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            conversation = create_conversation(
                proposal=serializer.validated_data["proposal"],
                actor=request.user,
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        return Response(
            ConversationSerializer(conversation, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class MessageListCreateAPIView(generics.ListCreateAPIView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "messages"

    def get_conversation(self):
        return get_object_or_404(
            conversations_for_user(self.request.user),
            public_id=self.kwargs["public_id"],
        )

    def get_serializer_class(self):
        return MessageCreateSerializer if self.request.method == "POST" else MessageSerializer

    def get_queryset(self):
        conversation = self.get_conversation()
        record_moderator_view(conversation=conversation, moderator=self.request.user)
        mark_messages_read(conversation=conversation, reader=self.request.user)
        return conversation.messages.select_related("author")

    def create(self, request, *args, **kwargs):
        conversation = self.get_conversation()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            message = send_message(
                conversation=conversation,
                author=request.user,
                content=serializer.validated_data["content"],
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response(
            MessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ReportCreateAPIView(APIView):
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "reports"

    def post(self, request, public_id):
        conversation = get_object_or_404(
            conversations_for_user(request.user),
            public_id=public_id,
        )
        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report = create_report(
                conversation=conversation,
                reporter=request.user,
                **serializer.validated_data,
            )
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response({"public_id": report.public_id}, status=status.HTTP_201_CREATED)


def _can_moderate(user):
    return has_internal_role(user, "MODERATION", "SUPER_ADMIN")


class InternalReportListAPIView(APIView):
    def get(self, request):
        if not _can_moderate(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        reports = Report.objects.select_related("assignee")
        for field in ("status", "priority"):
            if value := request.query_params.get(field):
                reports = reports.filter(**{field: value})
        record_audit(actor=request.user, action="moderation.report_list_view", target=request.user)
        return Response({"results": InternalReportSerializer(reports, many=True).data})


class InternalReportDetailAPIView(APIView):
    def get_report(self):
        return get_object_or_404(
            Report.objects.select_related("assignee", "conversation"),
            public_id=self.kwargs["public_id"],
        )

    def get(self, request, public_id):
        if not _can_moderate(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        report = self.get_report()
        record_audit(actor=request.user, action="moderation.report_detail_view", target=report)
        return Response(
            {
                "report": InternalReportSerializer(report).data,
                "actions": InternalReportActionSerializer(
                    report.actions.select_related("actor"), many=True
                ).data,
                "has_conversation": report.conversation_id is not None,
            }
        )


class InternalReportAssignmentAPIView(InternalReportDetailAPIView):
    def patch(self, request, public_id):
        if not _can_moderate(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = self.get_report()
        assignee = None
        if (assignee_id := serializer.validated_data.get("assignee_id")) is not None:
            assignee = get_object_or_404(get_user_model(), pk=assignee_id)
            if not _can_moderate(assignee):
                raise ValidationError({"assignee_id": "Agent de modération invalide."})
        report.assignee = assignee
        report.priority = serializer.validated_data["priority"]
        report.save(update_fields=("assignee", "priority", "updated_at"))
        record_audit(actor=request.user, action="moderation.report_assigned", target=report)
        return Response(InternalReportSerializer(report).data)


class InternalReportActionAPIView(InternalReportDetailAPIView):
    def post(self, request, public_id):
        if not _can_moderate(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ReportActionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            report = transition_report(
                report=self.get_report(),
                moderator=request.user,
                action=serializer.validated_data["action"],
                note=serializer.validated_data["note"],
            )
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        return Response(InternalReportSerializer(report).data)


class InternalConversationAccessAPIView(InternalReportDetailAPIView):
    def post(self, request, public_id):
        if not _can_moderate(request.user):
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ConversationAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            grant_temporary_conversation_access(
                report=self.get_report(),
                moderator=request.user,
                minutes=serializer.validated_data["minutes"],
            )
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response({"detail": "Accès temporaire accordé."})
