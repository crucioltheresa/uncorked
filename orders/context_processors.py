from decimal import Decimal

from . import pricing


def _euros(amount):
    """€100 for whole amounts, €99.50 otherwise."""
    if amount == amount.to_integral_value():
        return f"€{amount:.0f}"
    return f"€{amount:.2f}"


def promotions(request):
    """Promo bar messages, built from the pricing rules in orders.pricing."""
    percent = (pricing.BULK_DISCOUNT_RATE * Decimal(100)).normalize()
    discount = (
        f"{percent:f}% off if you buy "
        f"{pricing.BULK_DISCOUNT_MIN_BOTTLES} Bottles Of Wine or More!"
    )
    delivery = (
        "Free National Delivery on orders of "
        f"{_euros(pricing.FREE_DELIVERY_THRESHOLD)}+"
    )
    return {
        "promo_discount_message": discount,
        "promo_delivery_message": delivery,
        "promo_messages": [discount, delivery],
    }
