from django.db import models
from django.conf import settings
from products.models import Wine


class Review(models.Model):
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=100)
    body = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wine", "user")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.wine.name} ({self.rating}★)"
