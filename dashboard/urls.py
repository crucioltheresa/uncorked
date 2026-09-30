from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("wines/", views.wines, name="wines"),
    path(
        "wines/<int:wine_id>/toggle-available/",
        views.wine_toggle_available,
        name="wine_toggle_available",
    ),
    path("orders/", views.orders, name="orders"),
    path(
        "orders/<uuid:order_number>/",
        views.order_detail,
        name="order_detail",
    ),
    path(
        "orders/<uuid:order_number>/status/",
        views.order_status,
        name="order_status",
    ),
    path("messages/", views.contact_messages, name="messages"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),
    path(
        "messages/<int:pk>/handled/",
        views.message_handled,
        name="message_handled",
    ),
    path("reviews/", views.reviews, name="reviews"),
    path(
        "reviews/<int:pk>/delete/",
        views.review_delete,
        name="review_delete",
    ),
    path("regions/", views.regions, name="regions"),
    path("regions/add/", views.region_add, name="region_add"),
    path("regions/<int:pk>/edit/", views.region_edit, name="region_edit"),
]
