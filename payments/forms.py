from django import forms


class PaymentCreateForm(forms.Form):
    idempotency_key = forms.CharField(widget=forms.HiddenInput, max_length=100)


class FinanceActionForm(forms.Form):
    ACTIONS = (
        ("refund", "Rembourser"),
        ("payout", "Verser à l'enseignant"),
        ("reconcile_match", "Rapprocher sans écart"),
        ("reconcile_mismatch", "Signaler un écart"),
    )

    action = forms.ChoiceField(choices=ACTIONS)
    note = forms.CharField(widget=forms.Textarea, max_length=2000, required=False)
