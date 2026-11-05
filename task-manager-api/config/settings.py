"""Configuration: read from the environment once, validated, immutable (RP-01, RP-17).

Nothing else in the application reads the environment. A `.env` file at the project root is
loaded first when present (python-dotenv, already a dependency of the project); variables that
are already set in the environment win over the file.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'   # relative SQLite paths resolve inside <project>/instance/
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
DEFAULT_CORS_ORIGINS = '*'

_TRUE_VALUES = {'1', 'true', 'yes', 'on'}


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is present but invalid."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str | None
    debug: bool
    host: str
    port: int
    cors_origins: str | list[str]
    operator_token: str | None


def _optional_secret(environ, name):
    """An empty value counts as not configured: the feature it protects stays closed."""
    value = (environ.get(name) or '').strip()
    return value or None


def _port(environ):
    raw = (environ.get('APP_PORT') or '').strip()
    if not raw:
        return DEFAULT_PORT
    if not raw.isdigit() or not 0 < int(raw) < 65536:
        raise ConfigError(f'APP_PORT must be a TCP port number, got {raw!r}')
    return int(raw)


def _origins(environ):
    raw = (environ.get('CORS_ORIGINS') or DEFAULT_CORS_ORIGINS).strip()
    if raw == '*':
        return '*'
    return [origin.strip() for origin in raw.split(',') if origin.strip()]


def load_settings(environ=None):
    if environ is None:
        load_dotenv(PROJECT_ROOT / '.env')
        environ = os.environ
    return Settings(
        database_url=(environ.get('DATABASE_URL') or DEFAULT_DATABASE_URL).strip(),
        secret_key=_optional_secret(environ, 'SECRET_KEY'),
        debug=(environ.get('APP_DEBUG') or '').strip().lower() in _TRUE_VALUES,
        host=(environ.get('APP_HOST') or DEFAULT_HOST).strip(),
        port=_port(environ),
        cors_origins=_origins(environ),
        operator_token=_optional_secret(environ, 'OPERATOR_TOKEN'),
    )
