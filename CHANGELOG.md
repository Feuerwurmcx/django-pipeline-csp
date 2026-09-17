# Changelog

## [0.1.0] - 2026-09-17

### Added

- `{% javascript %}` adds the request's CSP nonce to every `<script>` rendered by django-pipeline.
- Nonce from Django's built-in CSP (Django >= 6.0) or django-csp >= 4.0.
- `{% stylesheet %}` passthrough, so templates only load `pipeline_csp`.
