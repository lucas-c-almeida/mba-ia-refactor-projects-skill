"""Configuration: the only module that reads the process environment (RP-01, RP-17)."""
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Same location the application always used: Flask-SQLAlchemy resolves a relative SQLite
# path against the application's instance folder (<project root>/instance), never the CWD.
DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
TRUE_VALUES = ('1', 'true', 'yes', 'on')


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is present but unusable."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    operator_token: Optional[str]
    debug: bool
    host: str
    port: int


def _secret(raw: Optional[str]) -> Optional[str]:
    """An empty value counts as "not configured" (fail closed)."""
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _port(raw: Optional[str]) -> int:
    if raw is None or not raw.strip():
        return DEFAULT_PORT
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigError('APP_PORT must be an integer') from exc
    if not 0 < port < 65536:
        raise ConfigError('APP_PORT must be between 1 and 65535')
    return port


def load_settings(environ: Mapping[str, str] = os.environ) -> Settings:
    return Settings(
        database_url=environ.get('DATABASE_URL') or DEFAULT_DATABASE_URL,
        # Unset: a random per-process key, so nothing is ever signed with a published value.
        secret_key=_secret(environ.get('SECRET_KEY')) or secrets.token_hex(32),
        # Unset: every operator-guarded operation answers 403.
        operator_token=_secret(environ.get('OPERATOR_TOKEN')),
        debug=(environ.get('APP_DEBUG') or 'false').strip().lower() in TRUE_VALUES,
        host=environ.get('APP_HOST') or DEFAULT_HOST,
        port=_port(environ.get('APP_PORT')),
    )
