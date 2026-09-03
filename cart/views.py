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
    quantity = int(request.POST.get("quantity", 1))
    cart.add(wine=wine, quantity=quantity)
    messages.success(request, f'"{wine.name}" added to your cart.')
    return redirect("cart_detail")


@require_POST
def cart_remove(request, wine_id):
    cart = Cart(request)
    wine = get_object_or_404(Wine, id=wine_id)
    cart.remove(wine)
    messages.success(request, f'"{wine.name}" removed from your cart.')
    return redirect("cart_detail")
