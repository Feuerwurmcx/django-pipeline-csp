# Changelog

## [0.1.0] - 2026-09-17

### Added

- `{% javascript %}` adds the request's CSP nonce to every `<script>` rendered by django-pipeline.
- Nonce from Django's built-in CSP (Django >= 6.0) or django-csp >= 4.0.
- `{% stylesheet %}` passthrough, so templates only load `pipeline_csp`.

### Notes

- Tested against Django 4.2, 5.2, 6.0 and 6.1.
- django-pipeline 4.0 only works with Django 4.2; use django-pipeline 4.1 for Django >= 5.2.
