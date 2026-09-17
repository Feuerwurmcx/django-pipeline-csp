import pytest
from django.template import engines
from django.test import Client

from tests.conftest import header_nonce, html_nonces


@pytest.mark.parametrize("enabled", [False, True])
def test_javascript_setzt_nonce_des_headers_in_jedes_script(csp, pipeline_enabled, enabled):
    pipeline_enabled(enabled)

    response = Client().get("/js/")

    body = response.content.decode()
    scripts = body.count("<script")
    assert scripts == (1 if enabled else 2)
    assert html_nonces(response) == [header_nonce(response)] * scripts


def test_javascript_rendert_einzeldateien_ohne_pipeline(csp, pipeline_enabled):
    pipeline_enabled(False)

    body = Client().get("/js/").content.decode()

    assert "/static/vendor/a.js" in body
    assert "/static/vendor/b.js" in body


def test_javascript_rendert_bundle_mit_pipeline(csp, pipeline_enabled):
    pipeline_enabled(True)

    body = Client().get("/js/").content.decode()

    assert "/static/js/polyfills.js" in body


def test_jst_inline_skript_bekommt_nonce(csp, pipeline_enabled):
    pipeline_enabled(False)

    response = Client().get("/jst/")

    body = response.content.decode()
    assert "window.JST" in body
    assert html_nonces(response) == [header_nonce(response)] * body.count("<script")


def test_zwei_requests_bekommen_verschiedene_nonces(csp):
    first = Client().get("/js/")
    second = Client().get("/js/")

    assert header_nonce(first) != header_nonce(second)
    assert set(html_nonces(first)) == {header_nonce(first)}
    assert set(html_nonces(second)) == {header_nonce(second)}


@pytest.mark.parametrize("enabled", [False, True])
def test_ohne_csp_middleware_identisch_zu_django_pipeline(settings, pipeline_enabled, enabled):
    settings.MIDDLEWARE = []
    pipeline_enabled(enabled)

    ours = Client().get("/js/").content
    theirs = Client().get("/js_pipeline/").content

    assert ours == theirs
    assert b"nonce" not in ours


def test_stylesheet_ueber_pipeline_csp(csp):
    body = Client().get("/css/").content.decode()

    assert '<link href="/static/css/base.css" rel="stylesheet"' in body


def test_jst_mit_script_im_quelltext_bleibt_unveraendert(csp, pipeline_enabled):
    """Regression fuer F1: der Inhalt des Inline-Scripts (JST-Quelltext) darf
    nicht als eigener `<script>`-Tag behandelt werden, auch wenn er `<script`
    enthaelt. Eigenes Paket/Template, damit die bestehende JST-Fixture und
    `test_jst_inline_skript_bekommt_nonce` unveraendert bleiben.
    """
    pipeline_enabled(False)

    response = Client().get("/jst_with_script/")

    body = response.content.decode()
    nonce = header_nonce(response)
    assert '<script type="text/template"></script>' in body
    assert html_nonces(response) == [nonce]


def test_render_error_js_bekommt_nonce_nur_am_aeusseren_tag(csp, pipeline_enabled, settings):
    pipeline_enabled(False)
    settings.PIPELINE = {
        **settings.PIPELINE,
        "SHOW_ERRORS_INLINE": True,
        "COMPILERS": ["tests.compilers.FailingCompiler"],
    }

    response = Client().get("/broken/")

    body = response.content.decode()
    nonce = header_nonce(response)
    assert "kaputt" in body
    assert html_nonces(response) == [nonce]


def test_jst_mit_script_im_quelltext_ohne_middleware_kein_nonce(settings, pipeline_enabled):
    settings.MIDDLEWARE = []
    pipeline_enabled(False)

    body = Client().get("/jst_with_script/").content.decode()

    assert '<script type="text/template"></script>' in body
    assert "nonce" not in body


def test_render_error_js_ohne_middleware_kein_nonce(settings, pipeline_enabled):
    settings.MIDDLEWARE = []
    pipeline_enabled(False)
    settings.PIPELINE = {
        **settings.PIPELINE,
        "SHOW_ERRORS_INLINE": True,
        "COMPILERS": ["tests.compilers.FailingCompiler"],
    }

    body = Client().get("/broken/").content.decode()

    assert "kaputt" in body
    assert "nonce" not in body


def test_javascript_ohne_request_im_context_hat_kein_nonce(pipeline_enabled):
    pipeline_enabled(False)
    django_template = engines["django"].from_string('{% load pipeline_csp %}{% javascript "polyfills" %}')

    html = django_template.render({})

    assert "nonce" not in html
