from .cart import CART_SESSION_ID


def cart_bottle_count(request):
    """
    Total number of bottles in the cart for the nav badge. Reads the
    session directly so pages don't create an empty cart for every visitor.
    """
    cart = request.session.get(CART_SESSION_ID) or {}
    return {
        "cart_bottle_count": sum(
            item.get("quantity", 0) for item in cart.values()
        )
    }
