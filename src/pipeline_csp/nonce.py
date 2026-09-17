"""Das CSP-Nonce eines Requests lesen und in `<script>`-Tags setzen."""

from __future__ import annotations

import re

from django.http import HttpRequest
from django.utils.html import escape

try:  # Django >= 6.0
    from django.middleware.csp import get_nonce as _django_get_nonce
except ImportError:  # pragma: no cover - nur unter Django < 6.0
    _django_get_nonce = None

# `<script` als Tag-Anfang, dessen Attribute noch kein `nonce=` enthalten.
# `(?=[\s>/])` verlangt Whitespace, `>` oder `/` direkt nach `script` (statt
# einer Wortgrenze), damit `<script-widget>` (Custom Element) nicht matcht.
# `\s` vor `nonce=` haelt `data-nonce=` auseinander.
_SCRIPT_WITHOUT_NONCE = re.compile(r"<script(?=[\s>/])(?![^>]*\snonce=)", re.IGNORECASE)


def get_nonce(request: HttpRequest | None) -> str | None:
    """Das Nonce des Requests oder `None`.

    Zuerst Djangos eigene CSP (`ContentSecurityPolicyMiddleware`, ab Django
    6.0), dann django-csp (`CSPMiddleware`). Beide legen ein Lazy-Objekt ab.
    Es wird mit `str()` gelesen: django-csps `CheckableLazyObject` ist
    `False`, solange niemand das Nonce abgerufen hat, und erst das Lesen
    sorgt dafuer, dass die Middleware es in den Header schreibt.
    """
    if request is None:
        return None
    lazy = _django_get_nonce(request) if _django_get_nonce is not None else None
    if lazy is None:
        lazy = getattr(request, "csp_nonce", None)
    if lazy is None:
        return None
    return str(lazy) or None


def add_nonce(html: str, nonce: str, *, count: int = 0) -> str:
    """Setzt `nonce="<nonce>"` in `<script`-Tags ohne eigenes Nonce.

    `count` wird an `re.sub` durchgereicht: `0` (Default) ersetzt alle
    Treffer, `1` nur den ersten (z.B. um nur das aeussere `<script>` eines
    Inline-Blocks zu treffen, ohne dessen Textinhalt zu untersuchen).
    """
    return _SCRIPT_WITHOUT_NONCE.sub(f'<script nonce="{escape(nonce)}"', html, count=count)
