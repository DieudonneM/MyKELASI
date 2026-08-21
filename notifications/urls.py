from django.urls import path

from .views import NotificationListView, NotificationReadView

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("<int:pk>/lire/", NotificationReadView.as_view(), name="read"),
]
