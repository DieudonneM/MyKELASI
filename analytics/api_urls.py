from django.urls import path

from .views import AnalyticsDashboardAPIView

app_name = "analytics-api"

urlpatterns = [
    path("analytics/", AnalyticsDashboardAPIView.as_view(), name="dashboard"),
]
