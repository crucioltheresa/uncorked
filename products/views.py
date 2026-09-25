from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Wine, Region
from .utils import get_countries_with_wine_counts


def wine_list(request):
    wines = Wine.objects.filter(is_available=True)
    wine_type = request.GET.get("type")
    region = request.GET.get("region")
    country = request.GET.get("country")

    if wine_type:
        wines = wines.filter(wine_type=wine_type)
    if region:
        wines = wines.filter(region__slug=region)
    if country:
        wines = wines.filter(region__country__iexact=country)

    paginator = Paginator(wines, 12)
    page_number = request.GET.get("page")
    wines = paginator.get_page(page_number)

    regions = Region.objects.all()
    context = {
        "wines": wines,
        "regions": regions,
        "selected_type": wine_type,
        "selected_region": region,
        "selected_country": country,
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


def explore_countries(request):
    countries = get_countries_with_wine_counts()
    context = {
        "countries": countries,
    }
    return render(request, "products/explore_countries.html", context)
