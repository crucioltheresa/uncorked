from django.urls import path
from . import views

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("newsletter/signup/", views.newsletter_signup, name="newsletter_signup"),
]
