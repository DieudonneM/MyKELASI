from datetime import timedelta

from django import forms
from django.utils import timezone


class BookingCreateForm(forms.Form):
    start_at = forms.DateTimeField(
        label="Date et heure de début",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=("%Y-%m-%dT%H:%M",),
    )
    duration_minutes = forms.IntegerField(
        label="Durée en minutes",
        min_value=30,
        max_value=480,
        initial=60,
        step_size=30,
    )

    def clean_start_at(self):
        start_at = self.cleaned_data["start_at"]
        if start_at <= timezone.now():
            raise forms.ValidationError("Choisissez une date future.")
        return start_at

    def get_end_at(self):
        return self.cleaned_data["start_at"] + timedelta(
            minutes=self.cleaned_data["duration_minutes"]
        )


class BookingActionForm(forms.Form):
    reason = forms.CharField(
        label="Motif",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
