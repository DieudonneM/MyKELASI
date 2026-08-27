from django.urls import path

from .api_views import (
    LearningRequestDetailAPIView,
    LearningRequestListCreateAPIView,
    MatchListAPIView,
    ProposalListCreateAPIView,
    ProposalActionAPIView,
    TeacherMatchedRequestListAPIView,
    TeacherProposalListCreateAPIView,
)

app_name = "learning-api"

urlpatterns = [
    path("requests/", LearningRequestListCreateAPIView.as_view(), name="request-list"),
    path(
        "requests/<uuid:public_id>/",
        LearningRequestDetailAPIView.as_view(),
        name="request-detail",
    ),
    path("requests/<uuid:public_id>/matches/", MatchListAPIView.as_view(), name="matches"),
    path(
        "requests/<uuid:public_id>/proposals/",
        ProposalListCreateAPIView.as_view(),
        name="proposals",
    ),
    path("proposals/<uuid:public_id>/<str:action>/", ProposalActionAPIView.as_view(), name="proposal-action"),
    path("teacher/matched-requests/", TeacherMatchedRequestListAPIView.as_view(), name="teacher-matched-requests"),
    path("teacher/proposals/<int:request_id>/", TeacherProposalListCreateAPIView.as_view(), name="teacher-proposal-create"),
    path("teacher/proposals/", TeacherProposalListCreateAPIView.as_view(), name="teacher-proposals"),
]
