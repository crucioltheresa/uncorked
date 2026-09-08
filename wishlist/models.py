from django.db import models
from django.conf import settings
from products.models import Wine


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist"
    )
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "wine")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.email} — {self.wine.name}"
