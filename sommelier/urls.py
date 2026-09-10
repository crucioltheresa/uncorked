from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz, name="quiz_start"),
    path("submit/", views.quiz_submit, name="quiz_submit"),
]
