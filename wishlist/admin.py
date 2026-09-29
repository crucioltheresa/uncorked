from django.contrib import admin

from .models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    """Wines customers have saved to their favourites."""

    list_display = ("user", "wine", "added_at")
    list_filter = ("added_at", "wine__wine_type")
    search_fields = ("user__email", "wine__name")
    list_select_related = ("user", "wine")
    readonly_fields = ("added_at",)
