from django import forms

from .pricing import normalise_eircode


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Full Name"}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email Address"})
    )
    address_line1 = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Address Line 1"}),
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Address Line 2 (optional)"}
        ),
    )
    city = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"placeholder": "City"})
    )
    eircode = forms.CharField(
        label="Eircode",
        max_length=8,
        help_text="We deliver in Ireland only, e.g. D02 X285.",
        widget=forms.TextInput(
            attrs={"placeholder": "Eircode", "autocapitalize": "characters"}
        ),
    )

    def clean_eircode(self):
        """Accept any case, with or without the space; store "D02 X285"."""
        eircode = normalise_eircode(self.cleaned_data["eircode"])
        if eircode is None:
            raise forms.ValidationError(
                "Please enter a valid Eircode, e.g. D02 X285 or A65 F4E2."
            )
        return eircode
