from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("cart/", include("cart.urls")),
    path("reviews/", include("reviews.urls")),
    path("sommelier/", include("sommelier.urls")),
    path("wishlist/", include("wishlist.urls")),
    path("", include("core.urls")),
    path("", include("products.urls")),
    path("", include("orders.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
