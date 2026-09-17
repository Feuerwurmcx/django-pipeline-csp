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
    },
    "STYLESHEETS": {
        "base": {
            "source_filenames": ["css/base.css"],
            "output_filename": "css/base.min.css",
        },
    },
}
