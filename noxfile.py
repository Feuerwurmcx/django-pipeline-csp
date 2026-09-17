import nox

nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "tests"]

# Nur Kombinationen, die Django selbst unterstuetzt. django-pipeline kommt aus
# der Abhaengigkeit (>=4.1,<5).
COMBINATIONS = [
    ("3.10", "4.2"),
    ("3.11", "4.2"),
    ("3.12", "4.2"),
    ("3.10", "5.0"),
    ("3.11", "5.0"),
    ("3.12", "5.0"),
    ("3.10", "5.1"),
    ("3.11", "5.1"),
    ("3.12", "5.1"),
    ("3.13", "5.1"),
    ("3.10", "5.2"),
    ("3.11", "5.2"),
    ("3.12", "5.2"),
    ("3.13", "5.2"),
    ("3.12", "6.0"),
    ("3.13", "6.0"),
    ("3.14", "6.0"),
    ("3.12", "6.1"),
    ("3.13", "6.1"),
    ("3.14", "6.1"),
]


@nox.session(python=False)
def lint(session):
    session.run("uvx", "ruff@0.15", "check", "src", "tests", external=True)
    session.run("uvx", "ruff@0.15", "format", "--check", "src", "tests", external=True)


@nox.session
@nox.parametrize("python,django", COMBINATIONS)
def tests(session, django):
    session.install("-e", ".[test]", f"django~={django}.0")
    session.run("coverage", "run", "-m", "pytest", *session.posargs)
    session.run("coverage", "report")
