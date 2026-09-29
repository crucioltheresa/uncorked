from datetime import date

from django import forms
from django.utils.text import slugify

from .models import Region, Wine


class WineForm(forms.ModelForm):
    """Add or edit a wine from the front-end product management pages."""

    # Rendered across the whole form width instead of in the two-column grid
    full_width_fields = (
        "character",
        "tasting_notes",
        "food_pairing",
        "description",
        "image",
    )

    region = forms.ModelChoiceField(
        queryset=Region.objects.order_by("country", "name"),
        required=False,
        empty_label="No region",
    )

    class Meta:
        model = Wine
        fields = [
            "name",
            "producer",
            "region",
            "wine_type",
            "vintage",
            "abv",
            "price",
            "stock",
            "character",
            "tasting_notes",
            "food_pairing",
            "description",
            "image",
            "is_featured",
            "is_available",
        ]
        labels = {
            "abv": "ABV (%)",
            "price": "Price (€)",
            "food_pairing": "Food match",
            "description": "About the producer",
            "is_featured": "Featured on the homepage",
            "is_available": "Available in the shop",
        }
        widgets = {
            "character": forms.Textarea(attrs={"rows": 2}),
            "tasting_notes": forms.Textarea(attrs={"rows": 3}),
            "food_pairing": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be more than 0.")
        return price

    def clean_stock(self):
        stock = self.cleaned_data["stock"]
        if stock < 0:
            raise forms.ValidationError("Stock can't be negative.")
        return stock

    def clean_abv(self):
        abv = self.cleaned_data["abv"]
        if not 0 <= abv <= 25:
            raise forms.ValidationError("ABV must be between 0 and 25%.")
        return abv

    def clean_vintage(self):
        vintage = self.cleaned_data.get("vintage")
        if vintage and not 1900 <= vintage <= date.today().year:
            raise forms.ValidationError(
                f"Vintage must be between 1900 and {date.today().year}."
            )
        return vintage

    def clean(self):
        """New wines get their slug from name and vintage; it must be free."""
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        if self.instance.pk is None and name:
            slug = slugify(f"{name}-{cleaned_data.get('vintage') or ''}")
            if Wine.objects.filter(slug=slug).exists():
                raise forms.ValidationError(
                    "A wine with this name and vintage already exists."
                )
        return cleaned_data
