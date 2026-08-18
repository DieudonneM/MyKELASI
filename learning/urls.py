from django.urls import path

from .views import (
    LearningRequestCreateView,
    LearningRequestDetailView,
    LearningRequestListView,
    ProposalCreateView,
)

app_name = "learning"

urlpatterns = [
    path("demandes/", LearningRequestListView.as_view(), name="request-list"),
    path("demandes/nouvelle/", LearningRequestCreateView.as_view(), name="request-create"),
    path("demandes/<uuid:public_id>/", LearningRequestDetailView.as_view(), name="request-detail"),
    path(
        "demandes/<uuid:public_id>/proposition/",
        ProposalCreateView.as_view(),
        name="proposal-create",
    ),
]
