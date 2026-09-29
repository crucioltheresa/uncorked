from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from products.models import Wine


class StaticViewSitemap(Sitemap):
    """Homepage, catalogue and the information pages."""

    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return [
            "homepage",
            "wine_list",
            "about",
            "faq",
            "shipping_returns",
            "privacy",
            "contact",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return {"homepage": 1.0, "wine_list": 0.9}.get(item, 0.5)


class WineSitemap(Sitemap):
    """Every wine customers can buy; unavailable wines are left out."""

    protocol = "https"
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Wine.objects.filter(is_available=True).order_by("id")

    def location(self, wine):
        return reverse("wine_detail", args=[wine.slug])

    def lastmod(self, wine):
        return wine.created_at


SITEMAPS = {"static": StaticViewSitemap, "wines": WineSitemap}
