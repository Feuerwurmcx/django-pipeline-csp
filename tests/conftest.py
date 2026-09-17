import re

import django
import pytest
from csp.constants import NONCE

NONCE_IN_HEADER = re.compile(r"'nonce-([^']+)'")
NONCE_IN_HTML = re.compile(r'<script nonce="([^"]+)"')


@pytest.fixture(params=["django-csp", "django"])
def csp(request, settings):
    """Aktiviert eine CSP-Middleware mit Nonce in `script-src`."""
    if request.param == "django":
        if django.VERSION < (6, 0):
            pytest.skip("Djangos eigene CSP gibt es erst ab Django 6.0")
        from django.utils.csp import CSP

        settings.MIDDLEWARE = ["django.middleware.csp.ContentSecurityPolicyMiddleware"]
        settings.SECURE_CSP = {"script-src": [CSP.SELF, CSP.NONCE, CSP.STRICT_DYNAMIC]}
    else:
        settings.MIDDLEWARE = ["csp.middleware.CSPMiddleware"]
        settings.CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"script-src": ["'self'", NONCE, "'strict-dynamic'"]}}
    return request.param


@pytest.fixture
def pipeline_enabled(settings):
    def set_enabled(enabled):
        settings.PIPELINE = {**settings.PIPELINE, "PIPELINE_ENABLED": enabled}

    return set_enabled


def header_nonce(response):
    """Das Nonce aus dem Content-Security-Policy-Header der Response."""
    match = NONCE_IN_HEADER.search(response["Content-Security-Policy"])
    assert match, response["Content-Security-Policy"]
    return match.group(1)


def html_nonces(response):
    return NONCE_IN_HTML.findall(response.content.decode())
