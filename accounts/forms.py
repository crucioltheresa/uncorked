from django import forms
from .models import UserProfile


class ProfileForm(forms.ModelForm):
    """Form to update user profile delivery details."""

    class Meta:
        model = UserProfile
        fields = ["full_name", "email", "address_line1", "address_line2", "city", "postcode", "country"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email Address"}),
            "address_line1": forms.TextInput(attrs={"placeholder": "Address Line 1"}),
            "address_line2": forms.TextInput(attrs={"placeholder": "Address Line 2 (optional)"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
            "postcode": forms.TextInput(attrs={"placeholder": "Postcode"}),
            "country": forms.TextInput(attrs={"placeholder": "Country"}),
        }
