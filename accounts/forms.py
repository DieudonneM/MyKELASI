from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Adresse email")
    account_type = forms.ChoiceField(label="Je suis", choices=User.AccountType.choices)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "account_type")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte utilise déjà cette adresse email.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.status != User.Status.ACTIVE:
            raise forms.ValidationError("Ce compte n'est pas disponible.", code="inactive")
        if not user.email_verified:
            raise forms.ValidationError(
                "Vérifiez votre adresse email avant de vous connecter.",
                code="email_unverified",
            )
