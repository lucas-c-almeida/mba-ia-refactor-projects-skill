"""Application configuration: read from the environment once, validated, immutable.

Nothing else in the codebase reads the environment. The composition root (app.py)
calls load_settings() and hands the resulting object to whoever needs it.
"""
import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
DEFAULT_LOG_LEVEL = 'INFO'
_TRUTHY = {'1', 'true', 'yes', 'on'}


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is absent or malformed."""


def _required(environ, name):
    value = environ.get(name)
    if not value:
        # Fail at startup, loudly -- not lazily at first use.
        raise ConfigError(f'missing required environment variable: {name}')
    return value


def _flag(environ, name, default=False):
    raw = environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def _int(environ, name, default):
    raw = environ.get(name)
    if raw is None or raw == '':
        return default
    try:
        return int(raw)
    except ValueError as err:
        raise ConfigError(f'environment variable {name} must be an integer, got {raw!r}') from err


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    log_level: str


def load_settings(environ=None):
    environ = os.environ if environ is None else environ
    return Settings(
        secret_key=_required(environ, 'SECRET_KEY'),
        database_url=environ.get('DATABASE_URL') or DEFAULT_DATABASE_URL,
        debug=_flag(environ, 'FLASK_DEBUG', default=False),
        host=environ.get('HOST') or DEFAULT_HOST,
        port=_int(environ, 'PORT', DEFAULT_PORT),
        log_level=(environ.get('LOG_LEVEL') or DEFAULT_LOG_LEVEL).upper(),
    )
