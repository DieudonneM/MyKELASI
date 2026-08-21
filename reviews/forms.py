from django import forms

from .models import Review, ReviewResponse

SCORE_CHOICES = tuple((value, str(value)) for value in range(1, 6))


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "punctuality", "communication", "quality", "comment")
        widgets = {
            "rating": forms.Select(choices=SCORE_CHOICES),
            "punctuality": forms.Select(choices=SCORE_CHOICES),
            "communication": forms.Select(choices=SCORE_CHOICES),
            "quality": forms.Select(choices=SCORE_CHOICES),
            "comment": forms.Textarea(attrs={"rows": 4}),
        }


class ReviewResponseForm(forms.ModelForm):
    class Meta:
        model = ReviewResponse
        fields = ("content",)
        widgets = {"content": forms.Textarea(attrs={"rows": 4})}
