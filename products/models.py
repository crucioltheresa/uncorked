from django.db import models
from django.utils.text import slugify


class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.country}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.country}"


class Wine(models.Model):
    TYPE_CHOICES = [
        ("red", "Red"),
        ("white", "White"),
        ("rose", "Rosé"),
        ("sparkling", "Sparkling"),
        ("orange", "Orange"),
        ("natural", "Natural"),
    ]
    name = models.CharField(max_length=100)
    producer = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, blank=True)
    wine_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    vintage = models.PositiveIntegerField()
    abv = models.DecimalField(max_digits=4, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    character = models.TextField(blank=True)
    tasting_notes = models.TextField(blank=True)
    food_pairing = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="wines/", null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.vintage or ''}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.vintage})"
