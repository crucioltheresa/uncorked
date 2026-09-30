from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import superuser_required
from core.models import ContactMessage
from orders.models import Order
from products.models import Region, Wine
from reviews.models import Review

from .forms import OrderStatusForm, RegionForm

# Wines with this many bottles or fewer count as low stock
LOW_STOCK_THRESHOLD = 5
# Orders that have been paid for (and may since have shipped)
PAID_STATUSES = ("paid", "shipped", "delivered")
PER_PAGE = 20


def _page(request, queryset):
    """Paginate a queryset, keeping the other query parameters."""
    page = Paginator(queryset, PER_PAGE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return page, params.urlencode()


def _paid_summary(orders):
    """Number of paid orders and their revenue."""
    totals = orders.filter(status__in=PAID_STATUSES).aggregate(
        count=Count("id"), revenue=Sum("grand_total")
    )
    return {
        "count": totals["count"],
        "revenue": totals["revenue"] or Decimal("0.00"),
    }


@superuser_required
def overview(request):
    """Store at a glance: sales, orders to ship, stock, messages, reviews."""
    since = timezone.now() - timedelta(days=30)
    available = Wine.objects.filter(is_available=True)
    context = {
        "section": "overview",
        "sales_30_days": _paid_summary(
            Order.objects.filter(created_at__gte=since)
        ),
        "sales_all_time": _paid_summary(Order.objects.all()),
        "to_ship_count": Order.objects.filter(status="paid").count(),
        "low_stock_count": available.filter(
            stock__gt=0, stock__lte=LOW_STOCK_THRESHOLD
        ).count(),
        "out_of_stock_count": available.filter(stock__lte=0).count(),
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "unhandled_count": ContactMessage.objects.filter(
            handled=False
        ).count(),
        "latest_reviews": Review.objects.select_related("wine", "user")[:5],
    }
    return render(request, "dashboard/overview.html", context)


@superuser_required
def wines(request):
    """All wines with search and filters by type, availability and stock."""
    queryset = Wine.objects.select_related("region").order_by("name")
    query = request.GET.get("q", "").strip()
    wine_type = request.GET.get("type", "")
    availability = request.GET.get("available", "")
    stock = request.GET.get("stock", "")

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(producer__icontains=query)
        )
    if wine_type in dict(Wine.TYPE_CHOICES):
        queryset = queryset.filter(wine_type=wine_type)
    if availability == "yes":
        queryset = queryset.filter(is_available=True)
    elif availability == "no":
        queryset = queryset.filter(is_available=False)
    if stock == "low":
        queryset = queryset.filter(stock__lte=LOW_STOCK_THRESHOLD)
    elif stock == "out":
        queryset = queryset.filter(stock__lte=0)

    page, querystring = _page(request, queryset)
    return render(request, "dashboard/wines.html", {
        "section": "wines",
        "page": page,
        "querystring": querystring,
        "query": query,
        "type_choices": Wine.TYPE_CHOICES,
        "selected_type": wine_type,
        "selected_available": availability,
        "selected_stock": stock,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
    })


@superuser_required
@require_POST
def wine_toggle_available(request, wine_id):
    """Show or hide a wine in the shop, then go back to the list."""
    wine = get_object_or_404(Wine, pk=wine_id)
    wine.is_available = not wine.is_available
    wine.save(update_fields=["is_available"])
    state = "is now available" if wine.is_available else "is now hidden"
    messages.success(request, f'"{wine.name}" {state}.')
    next_url = request.POST.get("next", "")
    if next_url.startswith("/dashboard/"):
        return redirect(next_url)
    return redirect("dashboard:wines")


@superuser_required
def orders(request):
    """All orders, newest first, filterable by status and searchable."""
    queryset = Order.objects.order_by("-created_at")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    if status in dict(Order.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    if query:
        queryset = queryset.filter(
            Q(email__icontains=query)
            | Q(full_name__icontains=query)
            | Q(order_number__icontains=query.replace("-", ""))
        )
    page, querystring = _page(request, queryset)
    return render(request, "dashboard/orders.html", {
        "section": "orders",
        "page": page,
        "querystring": querystring,
        "query": query,
        "status_choices": Order.STATUS_CHOICES,
        "selected_status": status,
    })


@superuser_required
def order_detail(request, order_number):
    """One order: items, totals, delivery details and status."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__wine"),
        order_number=order_number,
    )
    return render(request, "dashboard/order_detail.html", {
        "section": "orders",
        "order": order,
        "status_form": OrderStatusForm(instance=order),
    })


@superuser_required
@require_POST
def order_status(request, order_number):
    """Change an order's status (POST only)."""
    order = get_object_or_404(Order, order_number=order_number)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(
            request, f"Order status changed to {order.get_status_display()}."
        )
    else:
        messages.error(request, "Please choose a valid status.")
    return redirect("dashboard:order_detail", order_number=order.order_number)


@superuser_required
def contact_messages(request):
    """Contact form messages, filterable by handled / not handled."""
    queryset = ContactMessage.objects.order_by("-created_at")
    handled = request.GET.get("handled", "")
    if handled == "no":
        queryset = queryset.filter(handled=False)
    elif handled == "yes":
        queryset = queryset.filter(handled=True)
    page, querystring = _page(request, queryset)
    return render(request, "dashboard/messages.html", {
        "section": "messages",
        "page": page,
        "querystring": querystring,
        "selected_handled": handled,
    })


@superuser_required
def message_detail(request, pk):
    """One contact message, with a reply link and "mark as handled"."""
    message = get_object_or_404(ContactMessage, pk=pk)
    return render(request, "dashboard/message_detail.html", {
        "section": "messages",
        "contact": message,
    })


@superuser_required
@require_POST
def message_handled(request, pk):
    """Mark a contact message as handled (or not handled again)."""
    message = get_object_or_404(ContactMessage, pk=pk)
    message.handled = request.POST.get("handled", "1") == "1"
    message.save(update_fields=["handled"])
    if message.handled:
        messages.success(request, "Message marked as handled.")
    else:
        messages.info(request, "Message marked as not handled.")
    return redirect("dashboard:message_detail", pk=message.pk)


@superuser_required
def reviews(request):
    """Customer reviews, newest first, filterable by rating."""
    queryset = Review.objects.select_related("wine", "user")
    rating = request.GET.get("rating", "")
    if rating in {"1", "2", "3", "4", "5"}:
        queryset = queryset.filter(rating=int(rating))
    page, querystring = _page(request, queryset)
    return render(request, "dashboard/reviews.html", {
        "section": "reviews",
        "page": page,
        "querystring": querystring,
        "selected_rating": rating,
        "ratings": ["5", "4", "3", "2", "1"],
    })


@superuser_required
def review_delete(request, pk):
    """Confirmation page on GET; deletes the review on POST."""
    review = get_object_or_404(
        Review.objects.select_related("wine", "user"), pk=pk
    )
    if request.method == "POST":
        wine_name = review.wine.name
        review.delete()
        messages.success(request, f'Review of "{wine_name}" deleted.')
        return redirect("dashboard:reviews")
    return render(request, "dashboard/review_confirm_delete.html", {
        "section": "reviews",
        "review": review,
    })


@superuser_required
def regions(request):
    """All regions with how many wines each has."""
    queryset = Region.objects.annotate(wine_count=Count("wine")).order_by(
        "country", "name"
    )
    return render(request, "dashboard/regions.html", {
        "section": "regions",
        "regions": queryset,
    })


def _region_form(request, region=None):
    """Shared add / edit handling for regions."""
    form = RegionForm(request.POST or None, instance=region)
    if request.method == "POST":
        if form.is_valid():
            saved = form.save()
            verb = "updated" if region else "added"
            messages.success(request, f'Region "{saved}" {verb}.')
            return redirect("dashboard:regions")
        messages.error(request, "Please correct the errors below.")
    return render(request, "dashboard/region_form.html", {
        "section": "regions",
        "form": form,
        "region": region,
    })


@superuser_required
def region_add(request):
    """Add a region."""
    return _region_form(request)


@superuser_required
def region_edit(request, pk):
    """Edit a region's name or country."""
    return _region_form(request, get_object_or_404(Region, pk=pk))
