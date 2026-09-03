from django.contrib import admin
from .models import Region, Wine


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "slug")
    prepopulated_fields = {"slug": ("name", "country")}


@admin.register(Wine)
class WineAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "producer",
        "region",
        "wine_type",
        "price",
        "stock",
        "is_available",
    )
    list_filter = ("wine_type", "region", "is_featured", "is_available")
    search_fields = ("name", "producer", "region__name")
    prepopulated_fields = {"slug": ("name", "vintage")}
