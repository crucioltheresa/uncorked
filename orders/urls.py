from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<uuid:order_number>/", views.order_success, name="order_success"),
    path("order/<uuid:order_number>/", views.order_detail, name="order_detail"),
    path("webhook/", views.stripe_webhook, name="stripe_webhook"),
]
