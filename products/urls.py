from django.urls import path
from . import views

urlpatterns = [
    path("wines/", views.wine_list, name="wine_list"),
    path("wines/<slug:slug>/", views.wine_detail, name="wine_detail"),
]
