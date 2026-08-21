from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .serializers import (
    ConversationCreateSerializer,
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
    ReportCreateSerializer,
)
from .services import (
    conversations_for_user,
    create_conversation,
    create_report,
    mark_messages_read,
    record_moderator_view,
    send_message,
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
