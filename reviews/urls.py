from django.urls import path

from .views import (
    ReviewCreateView,
    ReviewModerationDetailView,
    ReviewModerationListView,
    ReviewResponseCreateView,
)

app_name = "reviews"

urlpatterns = [
    path("reservation/<uuid:booking_id>/", ReviewCreateView.as_view(), name="create"),
    path("<uuid:public_id>/repondre/", ReviewResponseCreateView.as_view(), name="respond"),
    path("moderation/", ReviewModerationListView.as_view(), name="moderation-list"),
    path(
        "moderation/<uuid:public_id>/",
        ReviewModerationDetailView.as_view(),
        name="moderation-detail",
    ),
]
