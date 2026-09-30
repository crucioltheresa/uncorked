from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from core.decorators import can_manage_store, store_manager_required
from orders.models import OrderItem
from .forms import WineForm
from .models import Wine, Region


def wine_list(request):
    wines = Wine.objects.filter(is_available=True).order_by("id")
    wine_type = request.GET.get("type")
    region = request.GET.get("region")
    country = request.GET.get("country")
    search_query = request.GET.get("q", "").strip()

    valid_types = [value for value, _ in Wine.TYPE_CHOICES]
    if wine_type in valid_types:
        wines = wines.filter(wine_type=wine_type)
    else:
        wine_type = None
    if region:
        wines = wines.filter(region__slug=region)
    if country:
        wines = wines.filter(region__country__iexact=country)

    if search_query:
        wines = wines.filter(
            Q(name__icontains=search_query) |
            Q(producer__icontains=search_query) |
            Q(region__name__icontains=search_query) |
            Q(region__country__icontains=search_query)
        )

    paginator = Paginator(wines, 12)
    page_number = request.GET.get("page")
    wines_page = paginator.get_page(page_number)

    regions = Region.objects.all()
    context = {
        "wines": wines_page,
        "regions": regions,
        "selected_type": wine_type,
        "selected_region": region,
        "selected_country": country,
        "search_query": search_query,
        "total_wines": wines.count(),
    }
    return render(request, "products/wine_list.html", context)


def wine_detail(request, slug):
    # Store managers can still open unavailable wines to edit or re-enable
    wines = Wine.objects.all()
    if not can_manage_store(request.user):
        wines = wines.filter(is_available=True)
    wine = get_object_or_404(wines, slug=slug)
    related_wines = Wine.objects.filter(
        wine_type=wine.wine_type, is_available=True
    ).exclude(id=wine.id)[:4]
    context = {
        "wine": wine,
        "related_wines": related_wines,
        # Author and profile in one query, for the reviewers' public names
        "reviews": wine.reviews.select_related("user", "user__profile"),
    }
    return render(request, "products/wine_detail.html", context)


@store_manager_required
def wine_add(request):
    """Add a new wine to the catalogue."""
    if request.method == "POST":
        form = WineForm(request.POST, request.FILES)
        if form.is_valid():
            wine = form.save()
            messages.success(request, f'"{wine.name}" was added.')
            return redirect("wine_detail", slug=wine.slug)
        messages.error(request, "Please correct the errors below.")
    else:
        form = WineForm()
    return render(
        request, "products/wine_form.html", {"form": form, "wine": None}
    )


@store_manager_required
def wine_edit(request, slug):
    """Edit an existing wine, including replacing its image."""
    wine = get_object_or_404(Wine, slug=slug)
    if request.method == "POST":
        form = WineForm(request.POST, request.FILES, instance=wine)
        if form.is_valid():
            wine = form.save()
            messages.success(request, f'"{wine.name}" was updated.')
            return redirect("wine_detail", slug=wine.slug)
        messages.error(request, "Please correct the errors below.")
    else:
        form = WineForm(instance=wine)
    return render(
        request, "products/wine_form.html", {"form": form, "wine": wine}
    )


@store_manager_required
def wine_delete(request, slug):
    """
    Ask for confirmation, then delete on POST. Wines that appear in orders
    are kept for the order history and marked unavailable instead.
    """
    wine = get_object_or_404(Wine, slug=slug)
    has_orders = OrderItem.objects.filter(wine=wine).exists()
    if request.method != "POST":
        return render(
            request,
            "products/wine_confirm_delete.html",
            {"wine": wine, "has_orders": has_orders},
        )

    if has_orders:
        wine.is_available = False
        wine.save(update_fields=["is_available"])
        messages.warning(
            request,
            f'"{wine.name}" is part of existing orders, so it was not '
            "deleted. It has been marked unavailable instead.",
        )
        return redirect("wine_detail", slug=wine.slug)

    name = wine.name
    wine.delete()
    messages.success(request, f'"{name}" was deleted.')
    return redirect("wine_list")
