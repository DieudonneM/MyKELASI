from django import forms
from django.core.exceptions import ValidationError

from .models import LearnerProfile, TeacherProfile


class LearnerProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)

    class Meta:
        model = LearnerProfile
        fields = (
            "first_name",
            "last_name",
            "levels",
            "interests",
            "preferred_service_area",
        )
        widgets = {
            "levels": forms.CheckboxSelectMultiple,
            "interests": forms.CheckboxSelectMultiple,
            "preferred_service_area": forms.Select,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=commit)
        user = profile.user
        first_name = self.cleaned_data.get("first_name", "")
        last_name = self.cleaned_data.get("last_name", "")
        if user.first_name != first_name or user.last_name != last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save(update_fields=("first_name", "last_name", "updated_at"))
        return profile


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
