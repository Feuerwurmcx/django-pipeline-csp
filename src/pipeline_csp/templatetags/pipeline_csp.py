"""django-pipeline-Tags mit CSP-Nonce.

`{% load pipeline_csp %}` ersetzt `{% load pipeline %}`. Nicht beide laden:
die zuletzt geladene Bibliothek gewinnt, und bei `{% load pipeline_csp pipeline %}`
fehlt das Nonce ohne Fehlermeldung.
"""

from contextvars import ContextVar

from django import template
from django.forms import Media
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from pipeline.templatetags.pipeline import JavascriptNode, StylesheetNode
from pipeline.templatetags.pipeline import javascript as pipeline_javascript
from pipeline.templatetags.pipeline import stylesheet as pipeline_stylesheet

from pipeline_csp.media import render_media
from pipeline_csp.nonce import add_nonce, get_nonce

register = template.Library()

# Traegt das Nonce waehrend eines `render()`-Aufrufs zu den Rendering-Hooks
# (`render_js`/`render_css`/`render_inline`/`render_error_*`), die
# django-pipeline ohne `context` aufruft. Eine ContextVar ist pro Thread bzw.
# pro Async-Task isoliert (im Gegensatz zu einem Attribut auf `self`, das
# zwischen Requests und Threads geteilte Node-Objekte verunreinigen wuerde).
_current_nonce: ContextVar[str | None] = ContextVar("_current_nonce", default=None)


class NonceNodeMixin:
    """Liest das Nonce beim Rendern aus dem Request-Kontext.

    Das Nonce wird bei jedem Rendern aus dem Request-Kontext gelesen, waehrend
    des Renderns in einer `contextvars.ContextVar` gehalten (siehe
    `_current_nonce`) und nicht am Node gespeichert: Template-Nodes werden
    zwischen Requests und Threads geteilt, eine ContextVar dagegen nicht.
    """

    def render(self, context):
        nonce = get_nonce(context.get("request"))
        if nonce is None:
            return super().render(context)
        token = _current_nonce.set(nonce)
        try:
            return mark_safe(super().render(context))
        finally:
            _current_nonce.reset(token)

    @staticmethod
    def with_nonce(html, *, count=0):
        nonce = _current_nonce.get()
        if nonce is None:
            return html
        return add_nonce(html, nonce, count=count)


class NonceJavascriptNode(NonceNodeMixin, JavascriptNode):
    """`JavascriptNode`, dessen `<script>`-Tags das Nonce des Requests tragen.

    Das Nonce wird nur auf oeffnende Tags gesetzt, nie auf deren Inhalt:
    `render_js` bekommt das Nonce auf allen von ihm gerenderten Tags,
    `render_inline` und `render_error_js` nur auf ihrem jeweils ersten Tag,
    damit JST-Quelltext oder Fehlertexte, die selbst `<script` enthalten
    koennen, unveraendert bleiben.
    """

    def render_js(self, package, path):
        return self.with_nonce(super().render_js(package, path))

    def render_inline(self, package, js):
        return self.with_nonce(super().render_inline(package, js), count=1)

    def render_error_js(self, package_name, e):
        return self.with_nonce(super().render_error_js(package_name, e), count=1)


class NonceStylesheetNode(NonceNodeMixin, StylesheetNode):
    """`StylesheetNode`, dessen `<link>`-Tags das Nonce des Requests tragen.

    `render_error_css` rendert django-pipelines Fehler-Template mit einem
    `<script>`; es bekommt das Nonce nur auf diesem ersten Tag.
    """

    def render_css(self, package, path):
        return self.with_nonce(super().render_css(package, path))

    def render_error_css(self, package_name, e):
        return self.with_nonce(super().render_error_css(package_name, e), count=1)


@register.tag
def javascript(parser, token):
    return NonceJavascriptNode(pipeline_javascript(parser, token).name)


@register.tag
def stylesheet(parser, token):
    return NonceStylesheetNode(pipeline_stylesheet(parser, token).name)


@register.filter
def csp_nonce(media, request):
    """`{{ form.media|csp_nonce:request }}`: Media mit Nonce in allen `<script>`- und `<link>`-Tags.

    Fuer Templates, in denen man `{{ form.media }}` selbst schreibt. Fremde
    Templates deckt `MediaNonceMiddleware` ab. Ohne Media, Request oder Nonce
    bleibt der Wert unveraendert.
    """
    if not isinstance(media, Media) or not isinstance(request, HttpRequest):
        return media
    nonce = get_nonce(request)
    if nonce is None:
        return media
    return render_media(media, nonce)
