from django import forms

from .models import Message, Report


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("content",)
        widgets = {"content": forms.Textarea(attrs={"rows": 3})}
        labels = {"content": "Message"}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("reason", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}
