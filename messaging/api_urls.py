from django.urls import path

from .api_views import (
    ConversationListCreateAPIView,
    InternalConversationAccessAPIView,
    InternalReportActionAPIView,
    InternalReportAssignmentAPIView,
    InternalReportDetailAPIView,
    InternalReportListAPIView,
    MessageListCreateAPIView,
    ReportCreateAPIView,
)

app_name = "messaging-api"

urlpatterns = [
    path("conversations/", ConversationListCreateAPIView.as_view(), name="list"),
    path(
        "conversations/<uuid:public_id>/messages/",
        MessageListCreateAPIView.as_view(),
        name="messages",
    ),
    path(
        "conversations/<uuid:public_id>/reports/",
        ReportCreateAPIView.as_view(),
        name="reports",
    ),
    path(
        "internal/moderation/reports/", InternalReportListAPIView.as_view(), name="internal-reports"
    ),
    path(
        "internal/moderation/reports/<uuid:public_id>/",
        InternalReportDetailAPIView.as_view(),
        name="internal-report-detail",
    ),
    path(
        "internal/moderation/reports/<uuid:public_id>/assignment/",
        InternalReportAssignmentAPIView.as_view(),
        name="internal-report-assignment",
    ),
    path(
        "internal/moderation/reports/<uuid:public_id>/actions/",
        InternalReportActionAPIView.as_view(),
        name="internal-report-action",
    ),
    path(
        "internal/moderation/reports/<uuid:public_id>/conversation-access/",
        InternalConversationAccessAPIView.as_view(),
        name="internal-report-conversation-access",
    ),
]
