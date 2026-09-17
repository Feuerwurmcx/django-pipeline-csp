import pytest
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
