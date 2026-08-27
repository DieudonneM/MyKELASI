from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.models import ServiceArea, Subject

from .services import product_kpis


class AnalyticsAccessMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.groups.filter(
            name__in=("ADMIN", "SUPER_ADMIN")
        ).exists():
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return super().dispatch(request, *args, **kwargs)


def _date_filter(value, end=False):
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
    boundary = datetime.combine(parsed, datetime.min.time())
    if end:
        boundary += timedelta(days=1)
    return timezone.make_aware(boundary)


class AnalyticsDashboardView(AnalyticsAccessMixin, TemplateView):
    template_name = "analytics/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kpis"] = product_kpis(
            start=_date_filter(self.request.GET.get("from")),
            end=_date_filter(self.request.GET.get("to"), end=True),
            subject_id=self.request.GET.get("subject") or None,
            service_area_id=self.request.GET.get("service_area") or None,
        )
        context["subjects"] = Subject.objects.filter(is_active=True)
        context["service_areas"] = ServiceArea.objects.filter(is_active=True)
        return context


class AnalyticsDashboardAPIView(APIView):
    def get(self, request):
        if not request.user.is_authenticated or not (
            request.user.is_superuser
            or request.user.groups.filter(name__in=("ADMIN", "SUPER_ADMIN")).exists()
        ):
            return Response({"detail": "Accès refusé."}, status=403)
        return Response(
            product_kpis(
                start=_date_filter(request.query_params.get("from")),
                end=_date_filter(request.query_params.get("to"), end=True),
                subject_id=request.query_params.get("subject") or None,
                service_area_id=request.query_params.get("service_area") or None,
            )
        )
