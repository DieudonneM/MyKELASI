from django.urls import path

from .api_views import (
    LearningRequestDetailAPIView,
    LearningRequestListCreateAPIView,
    MatchListAPIView,
    ProposalListCreateAPIView,
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
]
