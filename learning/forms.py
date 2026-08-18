from django import forms

from .models import LearningRequest, Proposal


class LearningRequestForm(forms.ModelForm):
    class Meta:
        model = LearningRequest
        fields = (
            "subject",
            "level",
            "teaching_mode",
            "service_area",
            "budget_max",
            "preferred_date",
            "preferred_start_time",
            "frequency",
            "description",
        )
        widgets = {
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "preferred_start_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ("amount", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
