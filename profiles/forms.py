from django import forms
from django.core.exceptions import ValidationError

from .models import TeacherProfile


class TeacherIdentityForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    headline = forms.CharField(label="Titre professionnel", max_length=160)
    bio = forms.CharField(label="Présentation", widget=forms.Textarea, max_length=2000)
    years_experience = forms.IntegerField(label="Années d'expérience", min_value=0, max_value=80)
    languages = forms.CharField(label="Langues", max_length=250)


class TeacherOfferForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = (
            "hourly_rate",
            "subjects",
            "levels",
            "teaching_modes",
            "service_areas",
        )
        widgets = {
            "subjects": forms.CheckboxSelectMultiple,
            "levels": forms.CheckboxSelectMultiple,
            "teaching_modes": forms.CheckboxSelectMultiple,
            "service_areas": forms.CheckboxSelectMultiple,
        }


class TeacherPublishForm(forms.Form):
    confirm = forms.BooleanField(label="Je confirme la publication de mon profil")

    def __init__(self, *args, profile, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_confirm(self):
        confirm = self.cleaned_data["confirm"]
        if confirm and not self.profile.can_publish:
            raise ValidationError("Complétez toutes les informations et vérifiez votre email.")
        return confirm
