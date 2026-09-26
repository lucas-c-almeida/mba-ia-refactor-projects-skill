"""Configuration — the only module that reads the environment.

Every value the application needs at runtime is resolved once, here, into an
immutable Settings object. Nothing else in the codebase reads os.environ.
Fixes AP-01 (SECRET_KEY), AP-18 (debug mode, CORS policy) — see reports/audit-latest.md.
"""
import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is missing."""


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise ConfigError("missing required environment variable: {0}".format(name))
    return value


def _bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    cors_origins: str          # "*" preserves today's behaviour; a comma list narrows it


def load_settings():
    return Settings(
        secret_key=_required("SECRET_KEY"),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        # Default is False: AP-18 (debug mode must never be the default on the path the
        # application is started with). Same instantiation the original used otherwise.
        debug=_bool("DEBUG", False),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        # Default "*" is the ORIGINAL, unchanged behaviour (flask-cors' own wildcard default).
        # Narrowing this is proposed, not applied — see reports/audit-latest.md,
        # "Proposed, Not Applied" (AP-18, permissive CORS).
        cors_origins=os.environ.get("CORS_ORIGINS", "*"),
    )
