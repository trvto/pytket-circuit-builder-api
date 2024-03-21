"""Noxfile for performing various code checks."""
import tempfile

import nox

locations = "src", "tests", "noxfile.py", "docs/conf.py"
nox.options.sessions = "lint", "type_checking", "safety", "tests"


"""Nox sessions."""


@nox.session(python=["3.11", "3.10", "3.9"])
def tests(session: nox.sessions.Session) -> None:
    """Run the test suite."""
    session.run("poetry", "install", "--only=main,tests", external=True)
    session.run("pytest", "tests", "--cov")


@nox.session(python=["3.11", "3.10", "3.9"])
def lint(session: nox.sessions.Session) -> None:
    """Lint using ruff, black, and darglint."""
    args = session.posargs or locations
    session.run("poetry", "install", "--only=linting", external=True)
    session.run("ruff", "--fix", *args)
    session.run("black", *args)
    session.run("darglint", "-v", "2", *args)


@nox.session(python=["3.11"])
def type_checking(session: nox.sessions.Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    session.run("poetry", "install", "--only=main,type-checking", external=True)
    session.run("mypy", *args)


@nox.session(python="3.11")
def docs(session: nox.sessions.Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--only=main,docs", external=True)
    session.run("sphinx-build", "-E", "docs", "docs/_build")


@nox.session(python="3.11")
def safety(session: nox.sessions.Session) -> None:
    """Scan dependencies for security vulnerabilities."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--with=dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        session.install("safety")
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")
