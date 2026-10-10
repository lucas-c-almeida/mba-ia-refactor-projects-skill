"""Configuration: the only module that reads the process environment.

Everything else receives a ``Settings`` object. Unsafe values are opt-in: debug is off unless
``APP_DEBUG`` says otherwise, and the operator guard stays closed while ``OPERATOR_TOKEN`` is unset.
"""
import os
import secrets
from dataclasses import dataclass
from typing import Mapping, Optional

_TRUE_VALUES = {"1", "true", "yes", "on"}

APP_VERSION = "1.0.0"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_DB_PATH = "loja.db"
DEFAULT_ENVIRONMENT = "producao"


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    environment: str
    operator_token: Optional[str]


def _flag(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in _TRUE_VALUES


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    env = os.environ if env is None else env
    return Settings(
        # Nothing in the application uses signed sessions, so an unset key falls back to a random
        # per-process one instead of a literal that every clone of the repository shares.
        secret_key=env.get("SECRET_KEY") or secrets.token_hex(32),
        debug=_flag(env.get("APP_DEBUG")),
        host=env.get("APP_HOST", DEFAULT_HOST),
        port=int(env.get("PORT", str(DEFAULT_PORT))),
        db_path=env.get("DB_PATH", DEFAULT_DB_PATH),
        environment=env.get("APP_ENV", DEFAULT_ENVIRONMENT),
        # Unset by default: the guarded operations answer 403 until an operator configures it.
        operator_token=env.get("OPERATOR_TOKEN") or None,
    )
