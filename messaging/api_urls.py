from django.urls import path

from .api_views import ConversationListCreateAPIView, MessageListCreateAPIView, ReportCreateAPIView

app_name = "messaging-api"

urlpatterns = [
    path("conversations/", ConversationListCreateAPIView.as_view(), name="list"),
    path(
        "conversations/<uuid:public_id>/messages/",
        MessageListCreateAPIView.as_view(),
        name="messages",
    ),
    path(
        "conversations/<uuid:public_id>/reports/",
        ReportCreateAPIView.as_view(),
        name="reports",
    ),
]
