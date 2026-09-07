from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"placeholder": "Full Name"})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"placeholder": "Email Address"})
    )
    address_line1 = forms.CharField(
        max_length=255, widget=forms.TextInput(attrs={"placeholder": "Address Line 1"})
    )
    address_line2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Address Line 2 (optional)"}),
    )
    city = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"placeholder": "City"})
    )
    postcode = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={"placeholder": "Postcode"})
    )
    country = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"placeholder": "Country"})
    )
