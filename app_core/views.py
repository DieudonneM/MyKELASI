from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from profiles.models import TeacherProfile


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_teachers"] = (
            TeacherProfile.objects.filter(is_public=True, user__is_active=True)
            .select_related("user")
            .prefetch_related("subjects", "teaching_modes")[:3]
        )
        return context


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    return Response({"name": "MyKELASI API", "version": "v1"})
