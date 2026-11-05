"""Configuration: the only module that reads the process environment.

Read once at startup, validated, and exposed as an immutable object. Every unsafe
value is opt-in: debug is off unless APP_DEBUG=true, the operator credential is unset
(and the operator-only route closed) unless OPERATOR_TOKEN is set.
"""
import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_DATABASE_FILE = "loja.db"
DEFAULT_ENVIRONMENT = "producao"

_TRUE_VALUES = ("1", "true", "yes", "on")

logger = logging.getLogger(__name__)


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is present but invalid."""


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_file: str
    database_path: Path
    environment: str
    operator_token: Optional[str]
    seed_admin_password: Optional[str]
    seed_joao_password: Optional[str]
    seed_maria_password: Optional[str]


def _optional_secret(environ: Mapping[str, str], name: str) -> Optional[str]:
    """An empty value is the same as an unset one: the feature stays closed."""
    value = environ.get(name, "").strip()
    return value or None


def _port(environ: Mapping[str, str]) -> int:
    raw = environ.get("APP_PORT", "").strip()
    if not raw:
        return DEFAULT_PORT
    if not raw.isdigit() or not 0 < int(raw) < 65536:
        raise ConfigError(f"APP_PORT must be a TCP port number, got {raw!r}")
    return int(raw)


def load_settings(environ: Mapping[str, str] = os.environ) -> Settings:
    secret_key = _optional_secret(environ, "SECRET_KEY")
    if secret_key is None:
        # No known value ever: an unset key becomes a random per-process key.
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY is not set; using a random per-process key")

    database_file = environ.get("DATABASE_FILE", "").strip() or DEFAULT_DATABASE_FILE
    return Settings(
        secret_key=secret_key,
        debug=environ.get("APP_DEBUG", "").strip().lower() in _TRUE_VALUES,
        host=environ.get("APP_HOST", "").strip() or DEFAULT_HOST,
        port=_port(environ),
        database_file=database_file,
        # Resolved against the project root, so starting from another directory
        # opens the same store instead of creating an empty one.
        database_path=PROJECT_ROOT / database_file,
        environment=environ.get("APP_ENV", "").strip() or DEFAULT_ENVIRONMENT,
        operator_token=_optional_secret(environ, "OPERATOR_TOKEN"),
        seed_admin_password=_optional_secret(environ, "SEED_ADMIN_PASSWORD"),
        seed_joao_password=_optional_secret(environ, "SEED_JOAO_PASSWORD"),
        seed_maria_password=_optional_secret(environ, "SEED_MARIA_PASSWORD"),
    )
