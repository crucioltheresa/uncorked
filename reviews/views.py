from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from orders.models import Order
from products.models import Wine

from .forms import ReviewForm
from .models import Review


def _has_bought(user, wine):
    """True if the user has a paid (or shipped/delivered) order with it."""
    return Order.objects.filter(
        user=user,
        status__in=Order.PURCHASED_STATUSES,
        items__wine=wine,
    ).exists()


def _wants_json(request):
    """True for fetch requests from reviews_modal.js."""
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )


def _safe_next(request, default):
    """Where to go after saving: a same-site "next" URL, or the default."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


def _form_errors_json(form):
    """400 JSON with the form's errors, for the review modal."""
    return JsonResponse(
        {
            "ok": False,
            "form_errors": list(form.non_field_errors()),
            "errors": {
                name: list(errors)
                for name, errors in form.errors.items()
                if name != "__all__"
            },
        },
        status=400,
    )


def _saved_json(review, message):
    """JSON after a review is saved, so the page can update its button."""
    return JsonResponse({
        "ok": True,
        "message": message,
        "review": {
            "id": review.id,
            "wine_id": review.wine_id,
            "rating": review.rating,
            "title": review.title,
            "body": review.body,
            "verified_purchase": review.verified_purchase,
            "edit_url": reverse("edit_review", args=[review.id]),
        },
    })


@login_required
def add_review(request, wine_id):
    """Write a review from the wine page (or the no-JavaScript fallback)."""
    wine = get_object_or_404(Wine, id=wine_id)
    wine_url = reverse("wine_detail", args=[wine.slug])

    # Check if already reviewed
    if Review.objects.filter(wine=wine, user=request.user).exists():
        messages.warning(request, "You have already reviewed this wine.")
        return redirect(_safe_next(request, wine_url))

    verified = _has_bought(request.user, wine)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.wine = wine
            review.user = request.user
            review.verified_purchase = verified
            review.save()
            messages.success(request, "Your review has been submitted!")
            return redirect(_safe_next(request, wine_url))
    else:
        form = ReviewForm()

    return render(
        request,
        "reviews/add_review.html",
        {
            "form": form,
            "wine": wine,
            "verified": verified,
            "next": _safe_next(request, ""),
        },
    )


@login_required
@require_POST
def order_review(request, order_number, wine_id):
    """
    Write a review from the order page. Only for a wine in one of the
    user's paid, shipped or delivered orders; the review is verified.
    """
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
        status__in=Order.PURCHASED_STATUSES,
    )
    wine = get_object_or_404(Wine, id=wine_id)
    if not order.items.filter(wine=wine).exists():
        raise Http404("This wine isn't in that order.")

    order_url = reverse("order_detail", args=[order.order_number])
    existing = Review.objects.filter(wine=wine, user=request.user).first()
    if existing:
        message = "You have already reviewed this wine."
        if _wants_json(request):
            return JsonResponse(
                {"ok": False, "form_errors": [message], "errors": {}},
                status=400,
            )
        messages.warning(request, message)
        return redirect(order_url)

    form = ReviewForm(request.POST)
    if not form.is_valid():
        if _wants_json(request):
            return _form_errors_json(form)
        messages.error(request, "Please correct the errors in your review.")
        return redirect(
            f'{reverse("add_review", args=[wine.id])}?next={order_url}'
        )

    review = form.save(commit=False)
    review.wine = wine
    review.user = request.user
    review.verified_purchase = True
    review.save()
    message = f'Thanks! Your review of "{wine.name}" is saved.'
    if _wants_json(request):
        return _saved_json(review, message)
    messages.success(request, message)
    return redirect(order_url)


@login_required
def edit_review(request, review_id):
    """
    Edit your own review (owners only). POST saves; GET shows the form,
    which is the fallback when JavaScript isn't available.
    """
    review = get_object_or_404(
        Review.objects.select_related("wine"), id=review_id, user=request.user
    )
    default_url = reverse("wine_detail", args=[review.wine.slug])

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            # A purchase made since the first review now counts
            review.verified_purchase = (
                review.verified_purchase
                or _has_bought(request.user, review.wine)
            )
            review.save()
            message = f'Your review of "{review.wine.name}" is updated.'
            if _wants_json(request):
                return _saved_json(review, message)
            messages.success(request, message)
            return redirect(_safe_next(request, default_url))
        if _wants_json(request):
            return _form_errors_json(form)
    else:
        form = ReviewForm(instance=review)

    return render(
        request,
        "reviews/add_review.html",
        {
            "form": form,
            "wine": review.wine,
            "verified": review.verified_purchase,
            "review": review,
            "next": _safe_next(request, ""),
        },
    )


@login_required
def delete_review(request, review_id):
    """
    Delete your own review. GET shows a confirmation page; POST deletes
    and goes back to "next" (e.g. the profile) or the wine page.
    """
    review = get_object_or_404(
        Review.objects.select_related("wine"), id=review_id, user=request.user
    )
    default_url = reverse("wine_detail", args=[review.wine.slug])
    if request.method != "POST":
        return render(request, "reviews/confirm_delete.html", {
            "review": review,
            "next": _safe_next(request, ""),
            "cancel_url": _safe_next(request, default_url),
        })
    review.delete()
    messages.success(request, "Review deleted.")
    return redirect(_safe_next(request, default_url))
