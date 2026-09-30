from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.decorators import can_manage_store
from orders.models import Order
from reviews.models import Review
from .models import UserProfile
from .forms import ProfileForm


@login_required(login_url="account_login")
def profile(request):
    """
    User profile view with delivery details, order history and the
    user's reviews.
    Store managers (dashboard access without being a superuser) have no
    customer profile: their account area is the Store Dashboard.
    """
    if can_manage_store(request.user) and not request.user.is_superuser:
        return redirect("dashboard:overview")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    # Newest first (Review.Meta.ordering), with each wine in the same query
    reviews = Review.objects.filter(user=request.user).select_related("wine")

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "orders": orders,
            "profile": profile,
            "reviews": reviews,
        },
    )
