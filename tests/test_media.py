import django
import pytest
from asgiref.sync import async_to_sync
from django import forms
from django.template import VariableDoesNotExist, engines
from django.test import AsyncClient, Client, RequestFactory

from pipeline_csp.middleware import MediaNonceMiddleware
from pipeline_csp.nonce import get_nonce
from tests.conftest import header_nonce, html_nonces
from tests.forms import MediaForm

requires_script_asset = pytest.mark.skipif(django.VERSION < (5, 2), reason="forms.Script gibt es erst ab Django 5.2")
requires_media_attrs = pytest.mark.skipif(django.VERSION < (6, 1), reason="Media.render(attrs=) gibt es erst ab 6.1")


def request_with_nonce(csp):
    """Ein Request, den die CSP-Middleware aus dem `csp`-Fixture vorbereitet hat."""
    request = RequestFactory().get("/")
    if csp == "django":
        from django.middleware.csp import ContentSecurityPolicyMiddleware as Middleware
    else:
        from csp.middleware import CSPMiddleware as Middleware
    Middleware(lambda r: None).process_request(request)
    return request


def django_media_html():
    """`{{ form.media }}`, wie Django es ausserhalb eines Requests rendert."""
    return str(MediaForm().media)


# --- MediaNonceMiddleware -------------------------------------------------------


def test_middleware_setzt_nonce_in_media_eines_fremden_templates(media_middleware):
    response = Client().get("/media/")

    body = response.content.decode()
    assert body.count("<script") == 2
    assert html_nonces(response) == [header_nonce(response)] * 2
    assert "/static/vendor/a.js" in body
    assert "https://cdn.example.com/x.js" in body


def test_middleware_laesst_css_unveraendert(media_middleware):
    body = Client().get("/media/").content.decode()

    assert '<link href="/static/css/base.css" media="all" rel="stylesheet">' in body


def test_middleware_setzt_nonce_bei_pipeline_form_media(media_middleware, pipeline_enabled):
    pipeline_enabled(False)

    response = Client().get("/media_pipeline/")

    body = response.content.decode()
    assert "/static/vendor/a.js" in body
    assert "/static/vendor/b.js" in body
    assert html_nonces(response) == [header_nonce(response)] * body.count("<script")


def test_middleware_unter_asgi(media_middleware):
    async def fetch():
        return await AsyncClient().get("/media/")

    response = async_to_sync(fetch)()

    assert html_nonces(response) == [header_nonce(response)] * 2


def test_ohne_media_middleware_kein_nonce_in_media(csp):
    body = Client().get("/media/").content.decode()

    assert "nonce" not in body


def test_media_middleware_ohne_csp_middleware_identisch_zu_django(settings):
    settings.MIDDLEWARE = ["pipeline_csp.middleware.MediaNonceMiddleware"]

    body = Client().get("/media/").content.decode()

    assert django_media_html() in body
    assert "nonce" not in body


def test_media_ausserhalb_eines_requests_bleibt_unveraendert(media_middleware):
    Client().get("/media/")  # Middleware geladen, Patch installiert

    assert "nonce" not in django_media_html()


def test_middleware_patcht_nur_einmal(media_middleware):
    Client().get("/media/")
    patched = forms.Media.render_js

    MediaNonceMiddleware(lambda request: None)

    assert forms.Media.render_js is patched


def test_media_ohne_js_erzeugt_kein_nonce(media_middleware):
    media = forms.Media(css={"all": ["css/base.css"]})
    request = request_with_nonce(media_middleware)
    if media_middleware == "django":
        from django.middleware.csp import get_nonce as lazy_nonce
    else:

        def lazy_nonce(request):
            return request.csp_nonce

    MediaNonceMiddleware(lambda request: media.render())(request)

    # Beide Lazy-Objekte sind falsy, solange niemand das Nonce gelesen hat.
    assert not lazy_nonce(request)


@requires_script_asset
def test_middleware_setzt_nonce_bei_script_asset_mit_attributen(media_middleware):
    media = forms.Media(js=[forms.Script("app.js", type="module")])
    seen = {}

    def view(request):
        seen["html"] = media.render()

    request = request_with_nonce(media_middleware)
    MediaNonceMiddleware(view)(request)

    assert seen["html"].startswith(f'<script nonce="{get_nonce(request)}"')
    assert seen["html"].startswith('<script nonce="')
    assert 'type="module"' in seen["html"]


@requires_media_attrs
def test_vorhandenes_nonce_aus_media_attrs_bleibt_stehen(media_middleware):
    media = forms.Media(js=["app.js"])
    seen = {}

    def view(request):
        seen["html"] = media.render(attrs={"nonce": "vorher"})

    MediaNonceMiddleware(view)(request_with_nonce(media_middleware))

    assert seen["html"].count("nonce=") == 1
    assert 'nonce="vorher"' in seen["html"]


# --- Filter csp_nonce -----------------------------------------------------------


def test_filter_setzt_nonce_nur_in_scripts(csp):
    response = Client().get("/media_filter/")

    body = response.content.decode()
    assert html_nonces(response) == [header_nonce(response)] * 2
    assert '<link href="/static/css/base.css" media="all" rel="stylesheet">' in body


def test_filter_behaelt_reihenfolge_von_django(csp):
    body = Client().get("/media_filter/").content.decode()

    assert body.index("<link") < body.index("<script")


def test_filter_auf_media_js(csp):
    response = Client().get("/media_filter_js/")

    body = response.content.decode()
    assert "<link" not in body
    assert html_nonces(response) == [header_nonce(response)] * 2


def test_filter_und_middleware_setzen_nonce_nur_einmal(media_middleware):
    response = Client().get("/media_filter/")

    body = response.content.decode()
    assert body.count("nonce=") == 2
    assert html_nonces(response) == [header_nonce(response)] * 2


def test_filter_ohne_csp_middleware_identisch_zu_django(settings):
    settings.MIDDLEWARE = []

    body = Client().get("/media_filter/").content.decode()

    assert django_media_html() in body
    assert "nonce" not in body


def test_filter_mit_request_none():
    template = engines["django"].from_string("{% load pipeline_csp %}{{ form.media|csp_nonce:request }}")

    html = template.render({"form": MediaForm(), "request": None})

    assert html.strip() == django_media_html()


def test_filter_ignoriert_werte_ohne_media(csp):
    template = engines["django"].from_string("{% load pipeline_csp %}[{{ missing|csp_nonce:request }}]")

    assert template.render({"request": request_with_nonce(csp)}) == "[]"


def test_filter_ohne_request_im_context_ist_ein_template_fehler():
    """Django loest Filter-Argumente strikt auf. Dokumentiert in der README."""
    template = engines["django"].from_string("{% load pipeline_csp %}{{ form.media|csp_nonce:request }}")

    with pytest.raises(VariableDoesNotExist):
        template.render({"form": MediaForm()})
