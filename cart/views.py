from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from orders.pricing import BULK_DISCOUNT_MIN_BOTTLES
from products.models import Wine
from .cart import CART_SESSION_ID, Cart


def cart_detail(request):
    cart = Cart(request)
    return render(
        request,
        "cart/cart.html",
        {"cart": cart, "totals": cart.get_totals()},
    )


@require_POST
def cart_add(request, wine_id):
    cart = Cart(request)
    wine = get_object_or_404(Wine, id=wine_id)
    if not wine.is_available:
        messages.error(request, f'Sorry, "{wine.name}" is not available.')
        return redirect("cart_detail")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 0
    if quantity < 1:
        messages.error(request, "Please choose a quantity of at least 1.")
        return redirect("cart_detail")

    available = wine.stock - cart.get_quantity(wine)
    if available <= 0:
        messages.warning(request, f'Sorry, no more "{wine.name}" in stock.')
        return redirect("cart_detail")

    if quantity > available:
        quantity = available
        messages.warning(
            request,
            f'Only {wine.stock} of "{wine.name}" in stock. '
            f"Your cart now has {wine.stock}.",
        )
    else:
        messages.success(request, f'"{wine.name}" added to your cart.')
    cart.add(wine=wine, quantity=quantity)
    return redirect("cart_detail")


@require_POST
def cart_remove(request, wine_id):
    cart = Cart(request)
    wine = get_object_or_404(Wine, id=wine_id)
    cart.remove(wine)
    messages.success(request, f'"{wine.name}" removed from your cart.')
    return redirect("cart_detail")


def _wants_json(request):
    """True for fetch requests from cart.js."""
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _update_response(request, cart, wine, level, message, status=200):
    """
    Answer a quantity update. Fetch requests get JSON with the new line and
    cart totals (and the totals block as HTML, so it matches the page);
    everything else gets a flash message and goes back to the cart.
    """
    if not _wants_json(request):
        getattr(messages, level)(request, message)
        return redirect("cart_detail")

    totals = cart.get_totals()
    totals_html = render_to_string(
        "includes/order_totals.html",
        {
            "subtotal": totals.subtotal,
            "discount": totals.discount,
            "delivery": totals.delivery_cost,
            "total": totals.grand_total,
        },
    )
    delivery = totals.delivery_cost
    return JsonResponse(
        {
            "ok": status == 200,
            "level": level,
            "message": message,
            "wine_id": wine.id,
            "quantity": cart.get_quantity(wine),
            "max": wine.stock,
            "line_total": str(cart.get_line_total(wine)),
            "subtotal": str(totals.subtotal),
            "discount": str(totals.discount),
            "delivery": None if delivery is None else str(delivery),
            "total": str(totals.grand_total),
            "bottle_count": len(cart),
            "totals_html": totals_html,
        },
        status=status,
    )


@require_POST
def cart_update(request, wine_id):
    """
    Set one cart line to an exact quantity (the cart page's stepper).

    0 removes the wine; more than the stock is capped at the stock with a
    message; anything that isn't a whole number of 0 or more is rejected
    and the cart is left as it was.
    """
    cart = Cart(request)
    wine = get_object_or_404(Wine, id=wine_id)
    if not cart.get_quantity(wine):
        return _update_response(
            request, cart, wine, "error",
            f'"{wine.name}" is not in your cart.', status=400,
        )

    try:
        quantity = int(request.POST.get("quantity", "").strip())
    except ValueError:
        quantity = -1
    if quantity < 0:
        return _update_response(
            request, cart, wine, "error",
            "Please enter a whole number of bottles (0 removes the wine).",
            status=400,
        )

    if quantity == 0:
        cart.remove(wine)
        return _update_response(
            request, cart, wine, "success",
            f'"{wine.name}" removed from your cart.',
        )

    if wine.stock <= 0:
        cart.remove(wine)
        return _update_response(
            request, cart, wine, "warning",
            f'Sorry, "{wine.name}" is out of stock and was removed '
            "from your cart.",
        )

    if quantity > wine.stock:
        cart.add(wine=wine, quantity=wine.stock, override_quantity=True)
        return _update_response(
            request, cart, wine, "warning",
            f'Only {wine.stock} of "{wine.name}" in stock. '
            f"Your cart now has {wine.stock}.",
        )

    cart.add(wine=wine, quantity=quantity, override_quantity=True)
    bottles = "bottle" if quantity == 1 else "bottles"
    return _update_response(
        request, cart, wine, "success",
        f'"{wine.name}" updated to {quantity} {bottles}.',
    )


PREVIEW_MAX_ITEMS = 4


@never_cache
@require_GET
def cart_preview(request):
    """
    HTML fragment for the nav cart preview, loaded by cart_preview.js on
    first hover or focus. Only ever reads this visitor's own session, and
    doesn't create an empty cart for visitors who don't have one.
    """
    if not request.session.get(CART_SESSION_ID):
        return render(request, "cart/preview.html", {"items": []})
    cart = Cart(request)
    items = list(cart)
    return render(
        request,
        "cart/preview.html",
        {
            "items": items[:PREVIEW_MAX_ITEMS],
            "more_count": max(0, len(items) - PREVIEW_MAX_ITEMS),
            "totals": cart.get_totals(),
            "discount_bottles": BULK_DISCOUNT_MIN_BOTTLES,
        },
    )
