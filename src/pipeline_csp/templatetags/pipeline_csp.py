"""django-pipeline-Tags mit CSP-Nonce.

`{% load pipeline_csp %}` ersetzt `{% load pipeline %}`. Nicht beide laden:
die zuletzt geladene Bibliothek gewinnt, und bei `{% load pipeline_csp pipeline %}`
fehlt das Nonce ohne Fehlermeldung.
"""

from django import template
from django.utils.safestring import mark_safe
from pipeline.templatetags.pipeline import JavascriptNode, stylesheet
from pipeline.templatetags.pipeline import javascript as pipeline_javascript

from pipeline_csp.nonce import add_nonce, get_nonce

register = template.Library()

# Unveraendert weitergereicht, damit Templates nur `pipeline_csp` laden muessen.
register.tag("stylesheet", stylesheet)


class NonceJavascriptNode(JavascriptNode):
    """`JavascriptNode`, dessen `<script>`-Tags das Nonce des Requests tragen.

    Das Nonce wird bei jedem Rendern aus dem Kontext gelesen und nicht am Node
    gespeichert: Template-Nodes werden zwischen Requests und Threads geteilt.
    """

    def render(self, context):
        html = super().render(context)
        nonce = get_nonce(context.get("request"))
        if nonce is None:
            return html
        return mark_safe(add_nonce(html, nonce))


@register.tag
def javascript(parser, token):
    return NonceJavascriptNode(pipeline_javascript(parser, token).name)
