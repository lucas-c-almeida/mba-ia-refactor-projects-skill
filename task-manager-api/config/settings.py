"""Configuration: the only module that reads the process environment (RP-01, RP-17).

Required values fail loudly at startup. Optional values default to what the application
used before the refactoring, so behaviour is unchanged unless the environment opts in.
"""
import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is absent."""


def _required(name):
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"missing required environment variable: {name}")
    return value


def _flag(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _list(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items[0] if items == ["*"] else items


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    cors_origins: object  # "*" or a list of origins


def load_settings():
    return Settings(
        secret_key=_required("SECRET_KEY"),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        debug=_flag("APP_DEBUG", False),              # unsafe value is opt-in, never the default
        host=os.environ.get("APP_HOST", "0.0.0.0"),   # same bind address as before, now visible
        port=int(os.environ.get("APP_PORT", "5000")),
        cors_origins=_list("CORS_ORIGINS", "*"),      # same policy as before; narrowing is proposed
    )
