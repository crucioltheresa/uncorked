from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls")),
    path("", include("core.urls")),
    path("", include("products.urls")),
]
