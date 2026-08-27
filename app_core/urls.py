"""
URL configuration for app_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from app_core.views import (
    AboutView,
    AcademicIntegrityView,
    ContactView,
    HomeView,
    PrivacyView,
    TermsView,
    api_root,
    api_schema,
    health,
    ready,
)
from profiles.api_views import TeacherPublicDetailAPIView, TeacherSearchAPIView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("a-propos/", AboutView.as_view(), name="about"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("politique-confidentialite/", PrivacyView.as_view(), name="privacy"),
    path("conditions-utilisation/", TermsView.as_view(), name="terms"),
    path("integrite-academique/", AcademicIntegrityView.as_view(), name="academic-integrity"),
    path("admin/", admin.site.urls),
    path("compte/", include("accounts.urls")),
    path("profils/", include("profiles.urls")),
    path("verification/", include("verification.urls")),
    path("apprentissage/", include("learning.urls")),
    path("reservations/", include("bookings.urls")),
    path("notifications/", include("notifications.urls")),
    path("messages/", include("messaging.urls")),
    path("avis/", include("reviews.urls")),
    path("paiements/", include("payments.urls")),
    path("interne/analytics/", include("analytics.urls")),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),
    path("api/v1/schema/", api_schema, name="openapi-schema"),
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/auth/", include("accounts.api_urls")),
    path("api/v1/search/", include("profiles.api_urls")),
    path("api/v1/teachers/", TeacherSearchAPIView.as_view(), name="api-teacher-search"),
    path(
        "api/v1/teachers/<uuid:public_id>/",
        TeacherPublicDetailAPIView.as_view(),
        name="api-teacher-detail",
    ),
    path("api/v1/", include("profiles.api_teacher_urls")),
    path("api/v1/", include("verification.api_urls")),
    path("api/v1/", include("profiles.api_learner_urls")),
    path("api/v1/", include("learning.api_urls")),
    path("api/v1/", include("bookings.api_urls")),
    path("api/v1/", include("messaging.api_urls")),
    path("api/v1/", include("notifications.api_urls")),
    path("api/v1/", include("reviews.api_urls")),
    path("api/v1/", include("payments.api_urls")),
    path("api/v1/", include("analytics.api_urls")),
]
