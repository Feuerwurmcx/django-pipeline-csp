import django
import pytest
from django.test import RequestFactory

from pipeline_csp.nonce import add_nonce, get_nonce

requires_django_csp_builtin = pytest.mark.skipif(
    django.VERSION < (6, 0), reason="Djangos eigene CSP gibt es erst ab Django 6.0"
)


def test_get_nonce_ohne_request():
    assert get_nonce(None) is None


def test_get_nonce_ohne_middleware():
    assert get_nonce(RequestFactory().get("/")) is None


def test_get_nonce_aus_django_csp():
    from csp.middleware import CSPMiddleware

    request = RequestFactory().get("/")
    CSPMiddleware(lambda r: None).process_request(request)

    nonce = get_nonce(request)

    assert isinstance(nonce, str)
    assert nonce
    # Dasselbe Nonce bei jedem Zugriff innerhalb eines Requests.
    assert get_nonce(request) == nonce == str(request.csp_nonce)


@requires_django_csp_builtin
def test_get_nonce_aus_django():
    from django.middleware.csp import ContentSecurityPolicyMiddleware
    from django.middleware.csp import get_nonce as django_get_nonce

    request = RequestFactory().get("/")
    ContentSecurityPolicyMiddleware(lambda r: None).process_request(request)

    nonce = get_nonce(request)

    assert isinstance(nonce, str)
    assert nonce
    assert nonce == str(django_get_nonce(request))


@requires_django_csp_builtin
def test_get_nonce_bevorzugt_django_vor_django_csp():
    from csp.middleware import CSPMiddleware
    from django.middleware.csp import ContentSecurityPolicyMiddleware
    from django.middleware.csp import get_nonce as django_get_nonce

    request = RequestFactory().get("/")
    ContentSecurityPolicyMiddleware(lambda r: None).process_request(request)
    CSPMiddleware(lambda r: None).process_request(request)

    assert get_nonce(request) == str(django_get_nonce(request))


def test_add_nonce_setzt_nonce_in_jedes_script():
    html = '<script src="/a.js"></script>\n<script type="text/javascript">x()</script>'

    assert add_nonce(html, "abc") == (
        '<script nonce="abc" src="/a.js"></script>\n<script nonce="abc" type="text/javascript">x()</script>'
    )


def test_add_nonce_laesst_vorhandenes_nonce_stehen():
    html = '<script nonce="alt" src="/a.js"></script>'

    assert add_nonce(html, "neu") == html


def test_add_nonce_verwechselt_data_nonce_nicht_mit_nonce():
    html = '<script data-nonce="x" src="/a.js"></script>'

    assert add_nonce(html, "abc") == '<script nonce="abc" data-nonce="x" src="/a.js"></script>'


def test_add_nonce_escaped_den_wert():
    assert add_nonce("<script></script>", 'a"b') == '<script nonce="a&quot;b"></script>'


def test_add_nonce_aendert_anderes_markup_nicht():
    html = '<link href="/a.css" rel="stylesheet"><scripts></scripts>'

    assert add_nonce(html, "abc") == html


def test_add_nonce_laesst_custom_elements_unveraendert():
    """F3: `<script\\b` matcht auch `<script-widget>`; die Grenze muss auf
    Whitespace, `>` oder `/` geprueft werden, nicht auf einer Wortgrenze."""
    html = "<script-widget></script-widget>"

    assert add_nonce(html, "abc") == html


def test_add_nonce_count_eins_setzt_nur_das_erste_script():
    html = '<script src="/a.js"></script><script src="/b.js"></script>'

    assert add_nonce(html, "abc", count=1) == ('<script nonce="abc" src="/a.js"></script><script src="/b.js"></script>')
