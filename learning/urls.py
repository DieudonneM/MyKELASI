from django.urls import path

from .views import (
    DetailedLearningRequestCreateView,
    LearningRequestCreateView,
    LearningRequestDetailView,
    LearningRequestListView,
    ProposalActionView,
    ProposalCreateView,
)

app_name = "learning"

urlpatterns = [
    path("demandes/", LearningRequestListView.as_view(), name="request-list"),
    path("demandes/nouvelle/", LearningRequestCreateView.as_view(), name="request-create"),
    path(
        "demandes/nouvelle/detaillee/",
        DetailedLearningRequestCreateView.as_view(),
        name="request-create-detailed",
    ),
    path("demandes/<uuid:public_id>/", LearningRequestDetailView.as_view(), name="request-detail"),
    path(
        "demandes/<uuid:public_id>/proposition/",
        ProposalCreateView.as_view(),
        name="proposal-create",
    ),
    path(
        "propositions/<uuid:public_id>/<str:action>/",
        ProposalActionView.as_view(),
        name="proposal-action",
    ),
]
