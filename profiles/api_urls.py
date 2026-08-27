from django.urls import path

from .api_views import TeacherPublicDetailAPIView, TeacherSearchAPIView

app_name = "profiles-api"

urlpatterns = [
    path("teachers/", TeacherSearchAPIView.as_view(), name="teacher-search"),
    path(
        "teachers/<uuid:public_id>/",
        TeacherPublicDetailAPIView.as_view(),
        name="teacher-detail",
    ),
]
