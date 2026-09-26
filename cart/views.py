from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from products.models import Wine
from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/cart.html", {"cart": cart})


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
