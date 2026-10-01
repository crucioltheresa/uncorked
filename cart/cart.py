from decimal import Decimal
from orders.pricing import calculate_totals
from products.models import Wine

CART_SESSION_ID = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, wine, quantity=1, override_quantity=False):
        wine_id = str(wine.id)
        if wine_id not in self.cart:
            self.cart[wine_id] = {
                "quantity": 0,
                "price": str(wine.price),
            }
        if override_quantity:
            self.cart[wine_id]["quantity"] = quantity
        else:
            self.cart[wine_id]["quantity"] += quantity
        self.save()

    def get_quantity(self, wine):
        return self.cart.get(str(wine.id), {}).get("quantity", 0)

    def get_line_total(self, wine):
        """Price times quantity for one wine; 0.00 if it isn't in the cart."""
        stored = self.cart.get(str(wine.id))
        if not stored:
            return Decimal("0.00")
        return Decimal(stored["price"]) * stored["quantity"]

    def remove(self, wine):
        wine_id = str(wine.id)
        if wine_id in self.cart:
            del self.cart[wine_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        # Build new dicts so the session only ever holds JSON-safe strings
        # and ints; Decimals and Wine objects exist only on the way out.
        wines = Wine.objects.filter(id__in=self.cart.keys())
        for wine in wines:
            stored = self.cart[str(wine.id)]
            price = Decimal(stored["price"])
            yield {
                "wine": wine,
                "quantity": stored["quantity"],
                "price": price,
                "total_price": price * stored["quantity"],
            }

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """Wine subtotal before any discount or delivery."""
        return sum(
            (Decimal(item["price"]) * item["quantity"]
             for item in self.cart.values()),
            Decimal("0.00"),
        )

    def get_totals(self, eircode=None):
        """Subtotal, bulk discount, delivery and grand total for the cart."""
        return calculate_totals(self.get_total_price(), len(self), eircode)

    def clear(self):
        del self.session[CART_SESSION_ID]
        self.save()
