from django.shortcuts import render
from django.urls import path

from tests.forms import MediaForm, PipelineMediaForm


def page(request, name):
    return render(request, f"{name}.html", {"form": MediaForm(), "pipeline_form": PipelineMediaForm()})


urlpatterns = [path("<str:name>/", page)]
