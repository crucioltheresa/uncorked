"""
All pricing rules in one place: bulk discount, delivery rates and the
free-delivery threshold. The cart, the checkout and the Stripe payment all
calculate totals with calculate_totals(), so they always agree.

Order of calculation: subtotal -> discount -> delivery (on the discounted
subtotal) -> grand total. Every amount is a Decimal rounded to the cent.
"""
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

# Bulk discount: "10% off if you buy 8 bottles of wine or more"
BULK_DISCOUNT_MIN_BOTTLES = 8
BULK_DISCOUNT_RATE = Decimal("0.10")

# Delivery (Ireland only), charged on the discounted subtotal
DELIVERY_COUNTRY = "Ireland"
DUBLIN_DELIVERY_COST = Decimal("5.95")
IRELAND_DELIVERY_COST = Decimal("9.95")
FREE_DELIVERY_THRESHOLD = Decimal("100.00")

# Eircode: a routing key (a letter and two digits, or D6W) followed by a
# 4-character unique identifier, with or without a space, any case
EIRCODE_LETTERS = "ACDEFHKNPRTVWXY"
EIRCODE_PATTERN = re.compile(
    rf"^(?P<routing_key>[{EIRCODE_LETTERS}]\d{{2}}|D6W)"
    rf"\s?(?P<identifier>[{EIRCODE_LETTERS}\d]{{4}})$"
)


def normalise_eircode(value):
    """Return the Eircode as "D02 X285", or None if it isn't valid."""
    match = EIRCODE_PATTERN.match((value or "").strip().upper())
    if match is None:
        return None
    return f"{match['routing_key']} {match['identifier']}"


def delivery_cost_for(eircode):
    """Delivery for a valid Eircode: Dublin (routing key D..) or elsewhere."""
    if eircode.upper().startswith("D"):
        return DUBLIN_DELIVERY_COST
    return IRELAND_DELIVERY_COST


@dataclass(frozen=True)
class Totals:
    subtotal: Decimal
    discount: Decimal
    # None when the Eircode isn't known yet and delivery isn't free
    delivery_cost: Decimal | None
    grand_total: Decimal
    bottle_count: int

    @property
    def discounted_subtotal(self):
        return self.subtotal - self.discount

    @property
    def has_discount(self):
        return self.discount > 0

    @property
    def free_delivery(self):
        return self.discounted_subtotal >= FREE_DELIVERY_THRESHOLD


def calculate_totals(subtotal, bottle_count, eircode=None):
    """
    Work out discount, delivery and grand total for a subtotal.

    Without an Eircode, delivery is only known if it's free; otherwise
    delivery_cost is None and the grand total excludes delivery.
    """
    subtotal = Decimal(subtotal).quantize(CENT, ROUND_HALF_UP)
    discount = Decimal("0.00")
    if bottle_count >= BULK_DISCOUNT_MIN_BOTTLES:
        discount = (subtotal * BULK_DISCOUNT_RATE).quantize(
            CENT, ROUND_HALF_UP
        )
    discounted = subtotal - discount

    if discounted >= FREE_DELIVERY_THRESHOLD:
        delivery = Decimal("0.00")
    elif eircode:
        delivery = delivery_cost_for(eircode)
    else:
        delivery = None

    return Totals(
        subtotal=subtotal,
        discount=discount,
        delivery_cost=delivery,
        grand_total=discounted + (delivery or Decimal("0.00")),
        bottle_count=bottle_count,
    )
