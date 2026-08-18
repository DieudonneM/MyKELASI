from django.urls import path

from .views import (
    TeacherIdentityView,
    TeacherOfferView,
    TeacherPublicDetailView,
    TeacherPublishView,
    TeacherSearchView,
)

app_name = "profiles"

urlpatterns = [
    path("enseignants/", TeacherSearchView.as_view(), name="teacher-search"),
    path(
        "enseignant/onboarding/identite/",
        TeacherIdentityView.as_view(),
        name="onboarding-identity",
    ),
    path("enseignant/onboarding/offre/", TeacherOfferView.as_view(), name="onboarding-offer"),
    path(
        "enseignant/onboarding/publication/",
        TeacherPublishView.as_view(),
        name="onboarding-publish",
    ),
    path("enseignants/<uuid:public_id>/", TeacherPublicDetailView.as_view(), name="teacher-detail"),
]
