from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "pipeline-csp-tests"
DEBUG = False
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "tests.urls"
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "pipeline",
    "pipeline_csp",
]

# Jeder Test setzt die CSP-Middleware selbst (siehe tests/conftest.py).
MIDDLEWARE = []

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    }
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_FINDERS = ["pipeline.finders.PipelineFinder"]

PIPELINE = {
    "PIPELINE_ENABLED": False,
    "PIPELINE_COLLECTOR_ENABLED": False,
    "JS_COMPRESSOR": None,
    "CSS_COMPRESSOR": None,
    "JAVASCRIPT": {
        "polyfills": {
            "source_filenames": ["vendor/*.js"],
            "output_filename": "js/polyfills.js",
        },
        "templates": {
            "source_filenames": ["jst/*.jst"],
            "output_filename": "js/templates.js",
        },
        # Eigenes Verzeichnis (nicht "jst/"), damit das Glob-Pattern
        # "jst/*.jst" des "templates"-Pakets diese Fixture nicht mit erfasst
        # und `test_jst_inline_skript_bekommt_nonce` unveraendert bleibt.
        "templates_with_script": {
            "source_filenames": ["jst_with_script/*.jst"],
            "output_filename": "js/templates_with_script.js",
        },
        "broken": {
            "source_filenames": ["broken/*.fail"],
            "output_filename": "js/broken.js",
        },
    },
    "STYLESHEETS": {
        "base": {
            "source_filenames": ["css/base.css"],
            "output_filename": "css/base.min.css",
        },
    },
}
