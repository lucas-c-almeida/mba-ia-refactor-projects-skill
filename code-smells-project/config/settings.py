"""Application settings, read once from the environment (AP-01, AP-18).

Unsafe values are opt-in: debug mode is off unless APP_DEBUG asks for it. No secret lives in the
source; when SECRET_KEY is absent a random per-process key is generated (the application issues no
sessions today, so nothing depends on the key surviving a restart).
"""

import logging
import os
import secrets
from dataclasses import dataclass

APP_VERSION = "1.0.0"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_DB_PATH = "loja.db"
DEFAULT_ENVIRONMENT = "producao"

_TRUE_VALUES = {"1", "true", "yes", "on"}

logger = logging.getLogger(__name__)


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is present but unusable."""


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    environment: str


def _flag(environ, name, default=False):
    raw = environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in _TRUE_VALUES


def _port(environ):
    raw = environ.get("APP_PORT")
    if raw is None or raw.strip() == "":
        return DEFAULT_PORT
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError("APP_PORT must be an integer, got {0!r}".format(raw)) from exc


def load_settings(environ=None):
    env = os.environ if environ is None else environ

    secret_key = env.get("SECRET_KEY")
    if not secret_key:
        logger.warning("SECRET_KEY not set: using a random key for this process only")
        secret_key = secrets.token_hex(32)

    return Settings(
        secret_key=secret_key,
        debug=_flag(env, "APP_DEBUG", default=False),
        host=env.get("APP_HOST") or DEFAULT_HOST,
        port=_port(env),
        db_path=env.get("DB_PATH") or DEFAULT_DB_PATH,
        environment=env.get("APP_ENV") or DEFAULT_ENVIRONMENT,
    )
