from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Wine
from .models import WishlistItem


@login_required
def wishlist_detail(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("wine")
    return render(request, "wishlist/wishlist.html", {"items": items})


@login_required
def wishlist_add(request, wine_id):
    wine = get_object_or_404(Wine, id=wine_id)
    _, created = WishlistItem.objects.get_or_create(user=request.user, wine=wine)
    if created:
        messages.success(request, f'"{wine.name}" added to your wishlist.')
    else:
        messages.info(request, f'"{wine.name}" is already in your wishlist.')
    return redirect("wine_detail", slug=wine.slug)


@login_required
def wishlist_remove(request, wine_id):
    wine = get_object_or_404(Wine, id=wine_id)
    WishlistItem.objects.filter(user=request.user, wine=wine).delete()
    messages.success(request, f'"{wine.name}" removed from your wishlist.')
    return redirect("wishlist_detail")
