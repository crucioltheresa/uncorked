import logging

import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from cart.cart import Cart
from products.models import Wine
from reviews.models import Review
from .models import Order, OrderItem
from .forms import CheckoutForm
from .pricing import DELIVERY_COUNTRY, normalise_eircode

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("wine_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        save_to_profile = (
            request.user.is_authenticated
            and request.POST.get("save_to_profile") == "on"
        )
        if form.is_valid():
            # Totals come from the server-side cart and the validated
            # Eircode only, never from values posted by the browser
            eircode = form.cleaned_data["eircode"]
            totals = cart.get_totals(eircode)
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                address_line1=form.cleaned_data["address_line1"],
                address_line2=form.cleaned_data["address_line2"],
                city=form.cleaned_data["city"],
                postcode=eircode,
                country=DELIVERY_COUNTRY,
                subtotal=totals.subtotal,
                discount=totals.discount,
                delivery_cost=totals.delivery_cost,
                grand_total=totals.grand_total,
                status="pending",
            )
            # Create order items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    wine=item["wine"],
                    quantity=item["quantity"],
                    price_at_purchase=item["price"],
                )

            # Save to profile if requested
            if save_to_profile:
                profile = request.user.profile
                profile.full_name = form.cleaned_data["full_name"]
                profile.email = form.cleaned_data["email"]
                profile.address_line1 = form.cleaned_data["address_line1"]
                profile.address_line2 = form.cleaned_data["address_line2"]
                profile.city = form.cleaned_data["city"]
                profile.postcode = eircode
                profile.country = DELIVERY_COUNTRY
                profile.save()

            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(order.grand_total * 100),
                currency="eur",
                metadata={"order_number": str(order.order_number)},
            )
            order.stripe_payment_intent = intent.id
            order.save()

            # Store order number in session for guests
            if not request.user.is_authenticated:
                request.session["guest_order_number"] = str(order.order_number)

            return render(
                request,
                "orders/payment.html",
                {
                    "order": order,
                    "client_secret": intent.client_secret,
                    "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
                    "form": form,
                },
            )
    else:
        # Pre-fill from profile if logged in
        initial = {}
        if request.user.is_authenticated:
            profile = request.user.profile
            initial = {
                "full_name": profile.full_name,
                "email": profile.email or request.user.email,
                "address_line1": profile.address_line1,
                "address_line2": profile.address_line2,
                "city": profile.city,
                # Only pre-fill a saved postcode that is a valid Eircode
                "eircode": normalise_eircode(profile.postcode) or "",
            }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "form": form,
            "totals": cart.get_totals(),
        },
    )


def order_success(request, order_number):
    """
    Show the order success page. Only the order's owner, or a guest with
    the order number in their session, can see it.
    """
    if request.user.is_authenticated:
        order = get_object_or_404(
            Order, order_number=order_number, user=request.user
        )
    else:
        # Guest can only view if order_number is in their session
        if request.session.get("guest_order_number") != str(order_number):
            return get_object_or_404(Order, order_number=None)  # Force 404
        order = get_object_or_404(Order, order_number=order_number)
    Cart(request).clear()
    return render(request, "orders/success.html", {"order": order})


@login_required
def order_detail(request, order_number):
    """
    View order details. User can only see their own orders. Paid, shipped
    and delivered orders let the customer review each wine (one review per
    wine, so an existing review shows as "Edit your review").
    """
    order = get_object_or_404(
        Order, order_number=order_number, user=request.user
    )
    items = list(order.items.select_related("wine", "wine__region"))
    can_review = order.status in Order.PURCHASED_STATUSES
    if can_review:
        reviews = {
            review.wine_id: review
            for review in Review.objects.filter(
                user=request.user, wine__in=[item.wine_id for item in items]
            )
        }
        for item in items:
            item.user_review = reviews.get(item.wine_id)
    return render(
        request,
        "orders/detail.html",
        {"order": order, "items": items, "can_review": can_review},
    )


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning("Stripe webhook rejected: invalid payload or signature")
        return HttpResponse(status=400)

    # Stripe objects are not dicts (no .get), so work with a plain copy
    event = event.to_dict()
    logger.info(
        "Stripe webhook received: %s (%s)", event["type"], event.get("id")
    )
    if event["type"] != "payment_intent.succeeded":
        return HttpResponse(status=200)

    intent = event["data"]["object"]
    order_number = (intent.get("metadata") or {}).get("order_number")
    with transaction.atomic():
        order = _find_order_for_intent(order_number, intent.get("id"))
        if order is None:
            logger.warning(
                "Stripe webhook: no order for payment intent %s "
                "(order_number=%s)",
                intent.get("id"),
                order_number,
            )
            return HttpResponse(status=200)
        if order.status == "paid":
            logger.info(
                "Stripe webhook: order %s already paid, skipping",
                order.order_number,
            )
            return HttpResponse(status=200)

        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])
        for item in order.items.all():
            Wine.objects.filter(pk=item.wine_id).update(
                stock=F("stock") - item.quantity
            )
    logger.info("Stripe webhook: order %s marked paid", order.order_number)

    try:
        _send_order_confirmation_email(order)
    except Exception:
        logger.exception(
            "Stripe webhook: confirmation email failed for order %s",
            order.order_number,
        )
    else:
        logger.info(
            "Stripe webhook: confirmation email sent for order %s to %s",
            order.order_number,
            order.email,
        )
    return HttpResponse(status=200)


def _find_order_for_intent(order_number, payment_intent_id):
    """Find and lock the order by metadata order number, then intent id."""
    orders = Order.objects.select_for_update()
    if order_number:
        try:
            return orders.get(order_number=order_number)
        except (Order.DoesNotExist, ValidationError):
            pass
    if payment_intent_id:
        return orders.filter(
            stripe_payment_intent=payment_intent_id
        ).first()
    return None


def _send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    context = {
        "order_number": order.order_number,
        "order": order,
        "items": order.items.all(),
        "subtotal": order.subtotal,
        "discount": order.discount,
        "delivery_cost": order.delivery_cost,
        "total": order.grand_total,
        "full_name": order.full_name,
        "address_line1": order.address_line1,
        "address_line2": order.address_line2,
        "city": order.city,
        "postcode": order.postcode,
        "country": order.country,
    }
    subject = f"Order Confirmation #{order.order_number}"
    html_message = render_to_string(
        "orders/email/confirmation.html", context
    )
    from_email = settings.DEFAULT_FROM_EMAIL or "noreply@uncorked.local"
    send_mail(
        subject,
        render_to_string("orders/email/confirmation.txt", context),
        from_email,
        [order.email],
        html_message=html_message,
    )
