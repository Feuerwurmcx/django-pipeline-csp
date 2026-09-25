# Changelog

## [Unreleased]

### Added

- `MediaNonceMiddleware` adds the request's CSP nonce to every `<script>` rendered by Django `Media`
  (`{{ form.media }}`, widget media, `PipelineFormMedia`, the admin), including in third-party templates.
- `{{ form.media|csp_nonce:request }}` filter for the same per template.

## [0.1.0] - 2026-09-17

### Added

- `{% javascript %}` adds the request's CSP nonce to every `<script>` rendered by django-pipeline.
- Nonce from Django's built-in CSP (Django >= 6.0) or django-csp >= 4.0.
- `{% stylesheet %}` passthrough, so templates only load `pipeline_csp`.

### Notes

- Requires django-pipeline >= 4.1.
- Tested against Django 4.2, 5.0, 5.1, 5.2, 6.0 and 6.1.
