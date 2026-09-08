from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Wine
from orders.models import Order
from .models import Review
from .forms import ReviewForm


@login_required
def add_review(request, wine_id):
    wine = get_object_or_404(Wine, id=wine_id)

    # Check if already reviewed
    if Review.objects.filter(wine=wine, user=request.user).exists():
        messages.warning(request, "You have already reviewed this wine.")
        return redirect("wine_detail", slug=wine.slug)

    # Check verified purchase
    verified = Order.objects.filter(
        user=request.user, status="paid", items__wine=wine
    ).exists()

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.wine = wine
            review.user = request.user
            review.verified_purchase = verified
            review.save()
            messages.success(request, "Your review has been submitted!")
            return redirect("wine_detail", slug=wine.slug)
    else:
        form = ReviewForm()

    return render(
        request,
        "reviews/add_review.html",
        {
            "form": form,
            "wine": wine,
            "verified": verified,
        },
    )


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    wine_slug = review.wine.slug
    review.delete()
    messages.success(request, "Review deleted.")
    return redirect("wine_detail", slug=wine_slug)
