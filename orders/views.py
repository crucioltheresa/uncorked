import stripe
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from cart.cart import Cart
from .models import Order, OrderItem
from .forms import CheckoutForm

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("wine_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,
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

            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(cart.get_total_price() * 100),
                currency="eur",
                metadata={"order_id": order.id},
            )
            order.stripe_payment_intent = intent.id
            order.save()

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
        # Pre-fill email if logged in
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {
            "cart": cart,
            "form": form,
        },
    )


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    Cart(request).clear()
    return render(request, "orders/success.html", {"order": order})


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
        order_id = intent["metadata"].get("order_id")
        try:
            order = Order.objects.get(id=order_id)
            order.status = "paid"
            order.save()
            # Reduce stock
            for item in order.items.all():
                item.wine.stock -= item.quantity
                item.wine.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)
