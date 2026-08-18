from django.urls import path

from .api_views import TeacherSearchAPIView

app_name = "profiles-api"

urlpatterns = [
    path("teachers/", TeacherSearchAPIView.as_view(), name="teacher-search"),
]
