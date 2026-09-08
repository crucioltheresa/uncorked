from django.urls import path
from . import views

urlpatterns = [
    path("", views.wishlist_detail, name="wishlist_detail"),
    path("add/<int:wine_id>/", views.wishlist_add, name="wishlist_add"),
    path("remove/<int:wine_id>/", views.wishlist_remove, name="wishlist_remove"),
]
