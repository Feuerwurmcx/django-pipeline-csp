# django-pipeline-csp

CSP nonce support for [django-pipeline](https://github.com/jazzband/django-pipeline) script tags.

Under a nonce-based Content Security Policy with `'strict-dynamic'`, browsers ignore host allowlists, so every
`<script>` needs the request's nonce. django-pipeline renders its tags without one
([jazzband/django-pipeline#771](https://github.com/jazzband/django-pipeline/issues/771)). `django-pipeline-csp` provides a
drop-in `{% javascript %}` tag that adds it.

## Installation

```bash
pip install django-pipeline-csp
```

```python
INSTALLED_APPS = [
    # ...
    "pipeline",
    "pipeline_csp",
]
```

## Usage

Replace `{% load pipeline %}` with `{% load pipeline_csp %}`:

```django
{% load pipeline_csp %}
{% stylesheet "base" %}
{% javascript "polyfills" %}
```

Every `<script>` rendered by `{% javascript %}` gets `nonce="..."` — individual source files
(`PIPELINE_ENABLED = False`), the compressed bundle and inline JavaScript templates alike. `{% stylesheet %}` is
passed through unchanged, so one `load` is enough.

Do not load both libraries in one template: the library loaded last wins, and with
`{% load pipeline_csp pipeline %}` the nonce is silently missing.

## Nonce sources

The nonce is taken from, in this order:

1. Django's built-in CSP (Django >= 6.0): `django.middleware.csp.ContentSecurityPolicyMiddleware`
2. [django-csp](https://github.com/mozilla/django-csp) >= 4.0: `csp.middleware.CSPMiddleware` (`pip install django-pipeline-csp[django-csp]`)

Your policy must include the nonce in `script-src`, e.g. `CSP.NONCE` (Django) or `csp.constants.NONCE` (django-csp).
Without an active middleware the output is identical to django-pipeline's.

`request` must be in the template context (`django.template.context_processors.request`).

The tag must render before the CSP middleware writes the response header — normal template rendering already
satisfies this. Accessing the nonce after the header was written raises `CSPNonceError` with django-csp; with
Django's built-in CSP a late nonce is simply not included in the header and the scripts it was meant to allow are
blocked. This matters mainly for streaming responses, where content can be produced after the headers are sent.

## Not covered

- Jinja2 templates
- Nonces on `<link rel="stylesheet">`
- Scripts injected via `document.write` (`'strict-dynamic'` does not trust parser-inserted scripts)
- Inline event handlers such as `onclick="..."`

## Compatibility

Python 3.10–3.14, Django 4.2 / 5.0 / 5.1 / 5.2 / 6.0 / 6.1, django-pipeline >= 4.1.

## License

MIT
