"""CSP-Nonce fuer die `<link>`- und `<script>`-Tags von Django-`Media` (`class Media`)."""

from __future__ import annotations

from contextvars import ContextVar
from itertools import chain

from django.forms import Media
from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from pipeline_csp.nonce import add_nonce, get_nonce

# Der Request, waehrend `MediaNonceMiddleware` ihn bearbeitet. `Media.render_css`
# und `Media.render_js` bekommen keinen Kontext; ueber diese ContextVar findet der Patch das Nonce.
_current_request: ContextVar[HttpRequest | None] = ContextVar("_current_request", default=None)

# Die Original-Methoden von `Media`, sobald `install()` sie umhuellt hat.
_originals: dict[str, object] = {}


def add_nonce_to_tags(tags, nonce: str) -> list[SafeString]:
    """Setzt das Nonce auf das jeweils erste Tag jedes Eintrags.

    `count=1`, damit auch eigene Assets mit `__html__`, deren Inhalt `<script`
    enthalten kann, nur am oeffnenden Tag veraendert werden.
    """
    return [mark_safe(add_nonce(tag, nonce, count=1)) for tag in tags]


def render_media(media: Media, nonce: str) -> SafeString:
    """Wie `Media.render()`, aber mit Nonce in allen `<link>`- und `<script>`-Tags.

    Die Reihenfolge (erst CSS, dann JS) entspricht `Media.render()`.
    """
    tags = chain(media.render_css(), media.render_js())
    return mark_safe("\n".join(add_nonce_to_tags(tags, nonce)))


def _wrap(original):
    def render_with_nonce(self, *args, **kwargs):
        tags = list(original(self, *args, **kwargs))
        if not tags:
            return tags
        # Erst hier lesen: django-csp erzeugt das Nonce beim ersten Zugriff, und
        # das soll nur passieren, wenn tatsaechlich ein Tag gerendert wird.
        nonce = get_nonce(_current_request.get())
        if nonce is None:
            return tags
        return add_nonce_to_tags(tags, nonce)

    return render_with_nonce


def install() -> None:
    """Umhuellt `Media.render_css` und `Media.render_js` (idempotent).

    Ohne aktive `MediaNonceMiddleware` ist `_current_request` leer und die
    Ausgabe identisch zu Django. `*args, **kwargs` reicht `attrs` aus Django
    >= 6.1 durch.
    """
    for name in ("render_css", "render_js"):
        if name not in _originals:
            _originals[name] = getattr(Media, name)
            setattr(Media, name, _wrap(_originals[name]))
