"""Formulare mit `class Media` fuer die Media-Tests."""

from django import forms
from pipeline.forms import PipelineFormMedia


class MediaWidget(forms.TextInput):
    class Media:
        css = {"all": ["css/base.css"]}
        js = ["vendor/a.js", "https://cdn.example.com/x.js"]


class MediaForm(forms.Form):
    name = forms.CharField(widget=MediaWidget)


class PipelineMediaWidget(forms.TextInput):
    class Media(PipelineFormMedia):
        js_packages = ("polyfills",)


class PipelineMediaForm(forms.Form):
    name = forms.CharField(widget=PipelineMediaWidget)
