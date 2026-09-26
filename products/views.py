from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Wine, Region


def wine_list(request):
    wines = Wine.objects.filter(is_available=True)
    wine_type = request.GET.get("type")
    region = request.GET.get("region")
    country = request.GET.get("country")
    search_query = request.GET.get("q", "").strip()

    if wine_type:
        wines = wines.filter(wine_type=wine_type)
    if region:
        wines = wines.filter(region__slug=region)
    if country:
        wines = wines.filter(region__country__iexact=country)

    if search_query:
        wines = wines.filter(
            Q(name__icontains=search_query) |
            Q(producer__icontains=search_query) |
            Q(region__name__icontains=search_query) |
            Q(region__country__icontains=search_query)
        )

    paginator = Paginator(wines, 12)
    page_number = request.GET.get("page")
    wines_page = paginator.get_page(page_number)

    regions = Region.objects.all()
    context = {
        "wines": wines_page,
        "regions": regions,
        "selected_type": wine_type,
        "selected_region": region,
        "selected_country": country,
        "search_query": search_query,
        "total_wines": wines.count(),
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


