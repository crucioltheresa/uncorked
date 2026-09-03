from decimal import Decimal
from django.conf import settings
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

    def remove(self, wine):
        wine_id = str(wine.id)
        if wine_id in self.cart:
            del self.cart[wine_id]
            self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        wine_ids = self.cart.keys()
        wines = Wine.objects.filter(id__in=wine_ids)
        cart = self.cart.copy()
        for wine in wines:
            cart[str(wine.id)]["wine"] = wine
        for item in cart.values():
            item["price"] = Decimal(item["price"])
            item["total_price"] = item["price"] * item["quantity"]
            yield item

    def __len__(self):
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def clear(self):
        del self.session[CART_SESSION_ID]
        self.save()
