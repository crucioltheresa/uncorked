import stripe
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

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
            # Create order
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                address_line1=form.cleaned_data["address_line1"],
                address_line2=form.cleaned_data["address_line2"],
                city=form.cleaned_data["city"],
                postcode=form.cleaned_data["postcode"],
                country=form.cleaned_data["country"],
                total_price=cart.get_total_price(),
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
                profile.postcode = form.cleaned_data["postcode"]
                profile.country = form.cleaned_data["country"]
                profile.save()

            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(cart.get_total_price() * 100),
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
                "postcode": profile.postcode,
                "country": profile.country,
            }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "form": form,
        },
    )


def order_success(request, order_number):
    """Show order success page. Access controlled by user ownership or session."""
    if request.user.is_authenticated:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    else:
        # Guest can only view if order_number is in their session
        if request.session.get("guest_order_number") != str(order_number):
            return get_object_or_404(Order, order_number=None)  # Force 404
        order = get_object_or_404(Order, order_number=order_number)
    Cart(request).clear()
    return render(request, "orders/success.html", {"order": order})


@login_required
def order_detail(request, order_number):
    """View order details. User can only see their own orders."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/detail.html", {"order": order})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_number = intent["metadata"].get("order_number")
        try:
            order = Order.objects.get(order_number=order_number)
            order.status = "paid"
            order.save()
            # Reduce stock
            for item in order.items.all():
                item.wine.stock -= item.quantity
                item.wine.save()
            # Send order confirmation email
            _send_order_confirmation_email(order)
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


def _send_order_confirmation_email(order):
    """Send order confirmation email to customer."""
    context = {
        "order_number": order.order_number,
        "order": order,
        "items": order.items.all(),
        "total": order.total_price,
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
