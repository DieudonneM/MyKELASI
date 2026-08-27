from django.urls import path

from .api_views import (
    NotificationListAPIView,
    NotificationPreferencesAPIView,
    NotificationReadAllAPIView,
    NotificationReadAPIView,
)

app_name = "notifications-api"

urlpatterns = [
    path("notifications/", NotificationListAPIView.as_view(), name="list"),
    path("notifications/<int:pk>/read/", NotificationReadAPIView.as_view(), name="read"),
    path("notifications/read-all/", NotificationReadAllAPIView.as_view(), name="read-all"),
    path("notification-preferences/", NotificationPreferencesAPIView.as_view(), name="preferences"),
]