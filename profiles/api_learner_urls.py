from django.urls import path

from .api_views import LearnerProfileAPIView, LearnerProfileCatalogAPIView

app_name = "profiles-learner-api"

urlpatterns = [
    path("learner/profile/", LearnerProfileAPIView.as_view(), name="learner-profile"),
    path(
        "learner/profile/catalog/",
        LearnerProfileCatalogAPIView.as_view(),
        name="learner-profile-catalog",
    ),
]
