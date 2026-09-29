from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("wine", "quantity", "price_at_purchase")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "email", "status", "grand_total", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name", "email")
    readonly_fields = (
        "stripe_payment_intent",
        "subtotal",
        "discount",
        "delivery_cost",
        "grand_total",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]
