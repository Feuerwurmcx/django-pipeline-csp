"""django-pipeline-Tags mit CSP-Nonce.

`{% load pipeline_csp %}` ersetzt `{% load pipeline %}`. Nicht beide laden:
die zuletzt geladene Bibliothek gewinnt, und bei `{% load pipeline_csp pipeline %}`
fehlt das Nonce ohne Fehlermeldung.
"""

from contextvars import ContextVar

from django import template
from django.utils.safestring import mark_safe
from pipeline.templatetags.pipeline import JavascriptNode, stylesheet
from pipeline.templatetags.pipeline import javascript as pipeline_javascript

from pipeline_csp.nonce import add_nonce, get_nonce

register = template.Library()

# Unveraendert weitergereicht, damit Templates nur `pipeline_csp` laden muessen.
register.tag("stylesheet", stylesheet)

# Traegt das Nonce waehrend eines `NonceJavascriptNode.render()`-Aufrufs zu den
# Rendering-Hooks (`render_js`/`render_inline`/`render_error_js`), die
# django-pipeline ohne `context` aufruft. Eine ContextVar ist pro Thread bzw.
# pro Async-Task isoliert (im Gegensatz zu einem Attribut auf `self`, das
# zwischen Requests und Threads geteilte Node-Objekte verunreinigen wuerde).
_current_nonce: ContextVar[str | None] = ContextVar("_current_nonce", default=None)


class NonceJavascriptNode(JavascriptNode):
    """`JavascriptNode`, dessen `<script>`-Tags das Nonce des Requests tragen.

    Das Nonce wird bei jedem Rendern aus dem Request-Kontext gelesen, waehrend
    des Renderns in einer `contextvars.ContextVar` gehalten (siehe
    `_current_nonce`) und nicht am Node gespeichert: Template-Nodes werden
    zwischen Requests und Threads geteilt, eine ContextVar dagegen nicht.

    Das Nonce wird nur auf oeffnende `<script`-Tags gesetzt, nie auf deren
    Inhalt: `render_js` bekommt das Nonce auf allen von ihm gerenderten Tags,
    `render_inline` und `render_error_js` nur auf ihrem jeweils einzigen
    aeusseren Tag, damit JST-Quelltext oder Fehlertexte, die selbst `<script`
    enthalten koennen, unveraendert bleiben.
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

    def render_js(self, package, path):
        html = super().render_js(package, path)
        nonce = _current_nonce.get()
        if nonce is None:
            return html
        return add_nonce(html, nonce)

    def render_inline(self, package, js):
        html = super().render_inline(package, js)
        nonce = _current_nonce.get()
        if nonce is None:
            return html
        return add_nonce(html, nonce, count=1)

    def render_error_js(self, package_name, e):
        html = super().render_error_js(package_name, e)
        nonce = _current_nonce.get()
        if nonce is None:
            return html
        return add_nonce(html, nonce, count=1)


@register.tag
def javascript(parser, token):
    return NonceJavascriptNode(pipeline_javascript(parser, token).name)
