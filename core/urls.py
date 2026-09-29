from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import SITEMAPS

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("newsletter/signup/", views.newsletter_signup, name="newsletter_signup"),
    path("favicon.ico", views.favicon, name="favicon"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("shipping-returns/", views.shipping_returns, name="shipping_returns"),
    path("privacy/", views.privacy, name="privacy"),
    path("contact/", views.contact, name="contact"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": SITEMAPS},
        name="sitemap",
    ),
]
