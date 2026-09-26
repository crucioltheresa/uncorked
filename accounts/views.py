from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.models import Order
from .models import UserProfile
from .forms import ProfileForm


@login_required(login_url="account_login")
def profile(request):
    """User profile view with order history and delivery details."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

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
        },
    )
