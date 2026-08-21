from django import forms


class ContactForm(forms.Form):
    SUBJECT_CHOICES = (
        ("learner", "Trouver un enseignant"),
        ("teacher", "Devenir enseignant"),
        ("partnership", "Partenariat"),
        ("support", "Aide et assistance"),
        ("other", "Autre demande"),
    )

    name = forms.CharField(
        label="Nom complet",
        max_length=120,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    subject = forms.ChoiceField(label="Sujet", choices=SUBJECT_CHOICES)
    message = forms.CharField(
        label="Votre message",
        min_length=20,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 6}),
    )
