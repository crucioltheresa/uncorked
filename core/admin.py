from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact form messages, newest first, filterable by status and topic."""

    list_display = ("name", "email", "subject", "created_at", "handled")
    list_filter = ("handled", "subject", "created_at")
    list_editable = ("handled",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    date_hierarchy = "created_at"
