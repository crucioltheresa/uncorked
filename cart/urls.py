from django.urls import path
from . import views

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("preview/", views.cart_preview, name="cart_preview"),
    path("add/<int:wine_id>/", views.cart_add, name="cart_add"),
    path("remove/<int:wine_id>/", views.cart_remove, name="cart_remove"),
    path("update/<int:wine_id>/", views.cart_update, name="cart_update"),
]
