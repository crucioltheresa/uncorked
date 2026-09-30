from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from core.decorators import can_manage_store
from products.models import Wine
from .models import WishlistItem


@login_required
def wishlist_detail(request):
    """
    The user's favourites, each with a quantity and add-to-cart. Store
    managers have no favourites: their account area is the dashboard.
    """
    if can_manage_store(request.user) and not request.user.is_superuser:
        return redirect("dashboard:overview")
    items = WishlistItem.objects.filter(user=request.user).select_related(
        "wine", "wine__region"
    )
    return render(request, "wishlist/wishlist.html", {"items": items})


@login_required
@require_POST
def wishlist_add(request, wine_id):
    wine = get_object_or_404(Wine, id=wine_id)
    _, created = WishlistItem.objects.get_or_create(
        user=request.user, wine=wine
    )
    if created:
        messages.success(request, f'"{wine.name}" added to your wishlist.')
    else:
        messages.info(request, f'"{wine.name}" is already in your wishlist.')
    return redirect("wine_detail", slug=wine.slug)


@login_required
@require_POST
def wishlist_remove(request, wine_id):
    """Remove a wine (always removes, unlike the toggle). JSON for fetch."""
    wine = get_object_or_404(Wine, id=wine_id)
    WishlistItem.objects.filter(user=request.user, wine=wine).delete()
    message = f'"{wine.name}" removed from your favourites.'
    if _wants_json(request):
        return JsonResponse({
            "wine_id": wine.id,
            "in_wishlist": False,
            "message": message,
            "count": WishlistItem.objects.filter(user=request.user).count(),
        })
    messages.success(request, message)
    return redirect("wishlist_detail")


def _wants_json(request):
    """True for fetch requests from wishlist.js, which ask for JSON."""
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _safe_next_url(request):
    """The page to go back to after a form post, if it's on this site."""
    next_url = request.POST.get("next") or request.headers.get("referer")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


@login_required
@require_POST
def wishlist_toggle(request, wine_id):
    """
    Add the wine to the wishlist, or remove it if it's already there.
    Fetch requests get JSON; plain form posts are redirected back.
    """
    wine = get_object_or_404(Wine, id=wine_id)
    deleted, _ = WishlistItem.objects.filter(
        user=request.user, wine=wine
    ).delete()
    in_wishlist = not deleted
    if in_wishlist:
        WishlistItem.objects.create(user=request.user, wine=wine)
        message = f'"{wine.name}" added to your favourites.'
    else:
        message = f'"{wine.name}" removed from your favourites.'

    if _wants_json(request):
        return JsonResponse({
            "wine_id": wine.id,
            "in_wishlist": in_wishlist,
            "message": message,
            "count": WishlistItem.objects.filter(user=request.user).count(),
        })

    messages.success(request, message)
    return redirect(_safe_next_url(request) or "wine_list")
