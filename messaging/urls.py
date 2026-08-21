from django.urls import path

from .views import (
    ConversationDetailView,
    ConversationListView,
    ConversationStartView,
    ModerationReportDetailView,
    ModerationReportListView,
    ReportCreateView,
    TargetReportCreateView,
)

app_name = "messaging"

urlpatterns = [
    path("", ConversationListView.as_view(), name="list"),
    path("demarrer/<uuid:proposal_id>/", ConversationStartView.as_view(), name="start"),
    path("<uuid:public_id>/", ConversationDetailView.as_view(), name="detail"),
    path("<uuid:public_id>/signaler/", ReportCreateView.as_view(), name="report"),
    path(
        "<uuid:public_id>/signaler/<uuid:message_id>/",
        ReportCreateView.as_view(),
        name="report-message",
    ),
    path(
        "signaler/<str:target_type>/<uuid:public_id>/",
        TargetReportCreateView.as_view(),
        name="report-target",
    ),
    path("moderation/signalements/", ModerationReportListView.as_view(), name="moderation-list"),
    path(
        "moderation/signalements/<uuid:public_id>/",
        ModerationReportDetailView.as_view(),
        name="moderation-detail",
    ),
]
