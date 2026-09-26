from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from products.models import Wine
from products.utils import get_countries_with_wine_counts
from .models import NewsletterSubscriber


def homepage(request):
    featured_wines = Wine.objects.filter(is_featured=True, is_available=True)[:8]
    countries = get_countries_with_wine_counts()

    return render(
        request,
        "core/index.html",
        {
            "featured_wines": featured_wines,
            "countries": countries,
        },
    )


def newsletter_signup(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
        else:
            _, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                messages.success(request, "Thanks for subscribing!")
            else:
                messages.info(request, "You're already subscribed!")
    return redirect("homepage")
