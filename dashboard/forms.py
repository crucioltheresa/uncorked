from django import forms
from django.utils.text import slugify

from orders.models import Order
from products.models import Region


class RegionForm(forms.ModelForm):
    """
    Add or edit a region. Like the wine form, a new region's slug comes from
    its name and country and must be free, and no two regions can share the
    same name and country.
    """

    class Meta:
        model = Region
        fields = ["name", "country"]
        labels = {"name": "Region name"}
        error_messages = {
            "name": {"required": "Please enter the region's name."},
            "country": {"required": "Please enter the country."},
        }

    def clean(self):
        cleaned_data = super().clean()
        name = (cleaned_data.get("name") or "").strip()
        country = (cleaned_data.get("country") or "").strip()
        if not name or not country:
            return cleaned_data

        others = Region.objects.exclude(pk=self.instance.pk)
        duplicate = others.filter(
            name__iexact=name, country__iexact=country
        ).exists()
        slug_taken = (
            self.instance.pk is None
            and others.filter(slug=slugify(f"{name}-{country}")).exists()
        )
        if duplicate or slug_taken:
            raise forms.ValidationError(
                "A region with this name and country already exists."
            )
        cleaned_data["name"] = name
        cleaned_data["country"] = country
        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    """Change an order's status (pending, paid, shipped, ...)."""

    class Meta:
        model = Order
        fields = ["status"]
        labels = {"status": "Order status"}
