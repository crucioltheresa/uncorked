from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "title": forms.TextInput(attrs={"placeholder": "Review title"}),
            "body": forms.Textarea(
                attrs={"placeholder": "Share your thoughts...", "rows": 4}
            ),
        }
