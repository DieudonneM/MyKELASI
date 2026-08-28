from django.urls import path

from .admin_api_views import (
    ConfigurationVersionListCreateAPIView,
    ReferentialDetailAPIView,
    ReferentialListCreateAPIView,
)

app_name = "profiles-admin-api"

urlpatterns = [
    path(
        "internal/referentials/<str:kind>/",
        ReferentialListCreateAPIView.as_view(),
        name="referential-list",
    ),
    path(
        "internal/referentials/<str:kind>/<int:pk>/",
        ReferentialDetailAPIView.as_view(),
        name="referential-detail",
    ),
    path(
        "internal/configurations/",
        ConfigurationVersionListCreateAPIView.as_view(),
        name="configuration-list",
    ),
]
