from django.shortcuts import render
from django.urls import path


def page(request, name):
    return render(request, f"{name}.html")


urlpatterns = [path("<str:name>/", page)]
