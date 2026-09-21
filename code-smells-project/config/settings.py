"""Application configuration: the only module that reads the process environment.

Resolved once at startup by the composition root (app.py) and injected everywhere else.
"""
import logging
import os
import secrets
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUE_VALUES


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_path: str
    debug: bool
    host: str
    port: int
    environment: str


def load_settings():
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        # No literal fallback: an ephemeral key is generated so nothing signed survives a
        # restart, and the gap is announced instead of hidden.
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY is not set; using an ephemeral random key for this process.")

    return Settings(
        secret_key=secret_key,
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
        debug=_env_bool("APP_DEBUG", False),
        host=os.environ.get("APP_HOST", "127.0.0.1"),
        port=int(os.environ.get("APP_PORT", "5000")),
        environment=os.environ.get("APP_ENV", "producao"),
    )
