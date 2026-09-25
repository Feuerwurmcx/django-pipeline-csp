"""CSP-Nonce fuer die `<script>`-Tags von Django-`Media` (`class Media`)."""

from __future__ import annotations

from contextvars import ContextVar
from itertools import chain

from django.forms import Media
from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from pipeline_csp.nonce import add_nonce, get_nonce

# Der Request, waehrend `MediaNonceMiddleware` ihn bearbeitet. `Media.render_js`
# bekommt keinen Kontext; ueber diese ContextVar findet der Patch das Nonce.
_current_request: ContextVar[HttpRequest | None] = ContextVar("_current_request", default=None)

_original_render_js = None


def add_nonce_to_js(tags, nonce: str) -> list[SafeString]:
    """Setzt das Nonce auf das jeweils einzige aeussere `<script>` jedes Tags.

    `count=1`, damit auch eigene Assets mit `__html__`, deren Inhalt `<script`
    enthalten kann, nur am oeffnenden Tag veraendert werden.
    """
    return [mark_safe(add_nonce(tag, nonce, count=1)) for tag in tags]


def render_media(media: Media, nonce: str) -> SafeString:
    """Wie `Media.render()`, aber mit Nonce in allen `<script>`-Tags.

    Die Reihenfolge (erst CSS, dann JS) entspricht `Media.render()`.
    """
    return mark_safe("\n".join(chain(media.render_css(), add_nonce_to_js(media.render_js(), nonce))))


def _render_js_with_nonce(self, *args, **kwargs):
    tags = _original_render_js(self, *args, **kwargs)
    if not tags:
        return tags
    # Erst hier lesen: django-csp erzeugt das Nonce beim ersten Zugriff, und das
    # soll nur passieren, wenn tatsaechlich ein `<script>` gerendert wird.
    nonce = get_nonce(_current_request.get())
    if nonce is None:
        return tags
    return add_nonce_to_js(tags, nonce)


def install() -> None:
    """Umhuellt `Media.render_js` (idempotent).

    Ohne aktive `MediaNonceMiddleware` ist `_current_request` leer und die
    Ausgabe identisch zu Django. `*args, **kwargs` reicht `attrs` aus Django
    >= 6.1 durch.
    """
    global _original_render_js
    if _original_render_js is not None:
        return
    _original_render_js = Media.render_js
    Media.render_js = _render_js_with_nonce
