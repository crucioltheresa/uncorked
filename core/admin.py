from django.contrib import admin

from .models import ContactMessage, NewsletterSubscriber


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact form messages, newest first, filterable by status and topic."""

    list_display = ("name", "email", "subject", "created_at", "handled")
    list_filter = ("handled", "subject", "created_at")
    list_editable = ("handled",)
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    date_hierarchy = "created_at"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Newsletter sign-ups; untick "active" to stop sending to someone."""

    list_display = ("email", "subscribed_at", "active")
    list_filter = ("active", "subscribed_at")
    list_editable = ("active",)
    search_fields = ("email",)
    readonly_fields = ("subscribed_at",)
