from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Customer reviews; staff can read, filter and delete them."""

    list_display = (
        "wine", "user", "rating", "verified_purchase", "created_at",
    )
    list_filter = ("rating", "verified_purchase", "created_at")
    search_fields = ("wine__name", "user__email", "title", "body")
    list_select_related = ("wine", "user")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
