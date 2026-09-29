from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("wine", "quantity", "price_at_purchase")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "status",
        "grand_total",
        "created_at",
    )
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


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Order lines are purchase history: listed and searchable, not edited."""

    list_display = ("order", "wine", "quantity", "price_at_purchase")
    list_filter = ("wine__wine_type", "order__status")
    search_fields = ("order__email", "order__full_name", "wine__name")
    list_select_related = ("order", "wine")
    readonly_fields = ("order", "wine", "quantity", "price_at_purchase")

    def has_add_permission(self, request):
        return False
