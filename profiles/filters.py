import django_filters
from django import forms
from django.db.models import Q

from .models import Level, ServiceArea, Subject, TeacherProfile, TeachingMode


class TeacherSearchFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_query",
        label="Recherche",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Mathématiques, anglais, informatique...",
                "autocomplete": "off",
            }
        ),
    )
    subject = django_filters.ModelChoiceFilter(
        field_name="subjects",
        queryset=Subject.objects.filter(is_active=True),
        label="Matière",
    )
    level = django_filters.ModelChoiceFilter(
        field_name="levels",
        queryset=Level.objects.filter(is_active=True),
        label="Niveau",
    )
    mode = django_filters.ModelChoiceFilter(
        field_name="teaching_modes",
        queryset=TeachingMode.objects.filter(is_active=True),
        label="Mode",
    )
    area = django_filters.ModelChoiceFilter(
        field_name="service_areas",
        queryset=ServiceArea.objects.filter(is_active=True),
        label="Commune",
    )
    max_rate = django_filters.NumberFilter(
        field_name="hourly_rate",
        lookup_expr="lte",
        label="Budget maximum (CDF/heure)",
        min_value=0,
    )
    ordering = django_filters.OrderingFilter(
        fields=(
            ("hourly_rate", "hourly_rate"),
            ("years_experience", "experience"),
            ("user__first_name", "name"),
        ),
        field_labels={
            "hourly_rate": "Prix",
            "years_experience": "Expérience",
            "user__first_name": "Nom",
        },
        label="Trier par",
    )

    class Meta:
        model = TeacherProfile
        fields = ()

    def filter_query(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
            | Q(headline__icontains=value)
            | Q(bio__icontains=value)
            | Q(subjects__name__icontains=value)
        )

    @property
    def qs(self):
        return super().qs.distinct()
