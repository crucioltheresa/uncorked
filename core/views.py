import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.templatetags.static import static
from products.models import Wine
from products.utils import get_countries_with_wine_counts
from orders import pricing
from .forms import ContactForm
from .models import NewsletterSubscriber

logger = logging.getLogger(__name__)

STORE_CONTACT_EMAIL = "uncorked.store@gmail.com"


def homepage(request):
    featured_wines = Wine.objects.filter(
        is_featured=True, is_available=True
    )[:8]
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
            _, created = NewsletterSubscriber.objects.get_or_create(
                email=email
            )
            if created:
                messages.success(request, "Thanks for subscribing!")
            else:
                messages.info(request, "You're already subscribed!")
    return redirect("homepage")


def favicon(request):
    """
    Send /favicon.ico requests (e.g. from admin pages) to the SVG icon.
    Not permanent, because the static URL changes when the icon does.
    """
    return redirect(static("img/favicon.svg"))


def about(request):
    """About Uncorked."""
    return render(request, "core/about.html")


def faq(request):
    """Frequently asked questions, as an accessible accordion."""
    return render(
        request,
        "core/faq.html",
        {"discount_bottles": pricing.BULK_DISCOUNT_MIN_BOTTLES},
    )


def shipping_returns(request):
    """Delivery and returns, with rates taken from orders.pricing."""
    context = {
        "delivery_country": pricing.DELIVERY_COUNTRY,
        "dublin_cost": pricing.DUBLIN_DELIVERY_COST,
        "ireland_cost": pricing.IRELAND_DELIVERY_COST,
        "free_threshold": pricing.FREE_DELIVERY_THRESHOLD,
        "discount_percent": (
            pricing.BULK_DISCOUNT_RATE * 100
        ).normalize(),
        "discount_bottles": pricing.BULK_DISCOUNT_MIN_BOTTLES,
    }
    return render(request, "core/shipping_returns.html", context)


def privacy(request):
    """Privacy policy in plain language."""
    return render(
        request,
        "core/privacy.html",
        {"contact_email": STORE_CONTACT_EMAIL},
    )


def _send_contact_emails(contact):
    """
    Notify the store and confirm to the sender. A failure is logged, never
    raised: the message is already saved, so nothing is lost.
    """
    context = {"contact": contact}
    emails = [
        EmailMessage(
            subject=f"New contact message: {contact.get_subject_display()}",
            body=render_to_string(
                "core/email/contact_notification.txt", context
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.DEFAULT_FROM_EMAIL],
            reply_to=[contact.email],
        ),
        EmailMessage(
            subject="We've got your message - Uncorked",
            body=render_to_string(
                "core/email/contact_confirmation.txt", context
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact.email],
        ),
    ]
    for email in emails:
        try:
            email.send()
        except Exception:
            logger.exception(
                "Contact email to %s failed (message %s)", email.to, contact.pk
            )


def contact(request):
    """Contact form: saves the message, then emails the store and sender."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if form.is_spam:
                # Look like success so bots don't learn to skip the field
                logger.info("Contact form honeypot triggered; message dropped")
            else:
                contact_message = form.save()
                _send_contact_emails(contact_message)
            messages.success(
                request,
                "Thanks for getting in touch! "
                "We'll reply within two working days.",
            )
            return redirect("contact")
        messages.error(request, "Please correct the errors below.")
    else:
        initial = {}
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            initial = {
                "name": (profile.full_name if profile else "")
                or request.user.get_full_name(),
                "email": request.user.email,
            }
        form = ContactForm(initial=initial)
    return render(
        request,
        "core/contact.html",
        {"form": form, "contact_email": STORE_CONTACT_EMAIL},
    )


@require_GET
def robots_txt(request):
    """robots.txt: keep private and admin pages out, point to the sitemap."""
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    return render(
        request,
        "core/robots.txt",
        {"sitemap_url": sitemap_url},
        content_type="text/plain",
    )
