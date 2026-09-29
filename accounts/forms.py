from django import forms
from orders.pricing import DELIVERY_COUNTRY, normalise_eircode
from .models import UserProfile


class ProfileForm(forms.ModelForm):
    """
    Form to update user profile delivery details. Delivery is Ireland only,
    so the postcode is an Eircode and the country is always Ireland.
    """

    class Meta:
        model = UserProfile
        fields = ["full_name", "email", "address_line1", "address_line2", "city", "postcode"]
        labels = {"postcode": "Eircode"}
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email Address"}),
            "address_line1": forms.TextInput(attrs={"placeholder": "Address Line 1"}),
            "address_line2": forms.TextInput(attrs={"placeholder": "Address Line 2 (optional)"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
            "postcode": forms.TextInput(
                attrs={
                    "placeholder": "Eircode",
                    "aria-label": "Eircode",
                    "autocapitalize": "characters",
                }
            ),
        }

    def clean_postcode(self):
        """Optional, but if given it must be a valid Eircode, e.g. D02 X285."""
        value = self.cleaned_data["postcode"].strip()
        if not value:
            return ""
        eircode = normalise_eircode(value)
        if eircode is None:
            raise forms.ValidationError(
                "Please enter a valid Eircode, e.g. D02 X285 or A65 F4E2."
            )
        return eircode

    def save(self, commit=True):
        self.instance.country = DELIVERY_COUNTRY
        return super().save(commit=commit)
