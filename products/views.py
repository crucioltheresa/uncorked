from django.shortcuts import render, get_object_or_404
from .models import Wine, Region


def wine_list(request):
    wines = Wine.objects.filter(is_available=True)
    wine_type = request.GET.get("type")
    region = request.GET.get("region")

    if wine_type:
        wines = wines.filter(wine_type=wine_type)
    if region:
        wines = wines.filter(region__slug=region)

    regions = Region.objects.all()
    context = {
        "wines": wines,
        "regions": regions,
        "selected_type": wine_type,
        "selected_region": region,
    }
    return render(request, "products/wine_list.html", context)


def wine_detail(request, slug):
    wine = get_object_or_404(Wine, slug=slug, is_available=True)
    related_wines = Wine.objects.filter(
        wine_type=wine.wine_type, is_available=True
    ).exclude(id=wine.id)[:4]
    context = {
        "wine": wine,
        "related_wines": related_wines,
    }
    return render(request, "products/wine_detail.html", context)
