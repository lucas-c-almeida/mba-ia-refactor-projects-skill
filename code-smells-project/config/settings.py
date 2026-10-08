"""Application settings, read from the environment once.

Nothing else in the codebase reads the environment. Every value has a safe default; the unsafe
choice (debug mode, an operator credential) is something the environment opts in to.
"""

import os
from dataclasses import dataclass
from typing import Optional

_TRUE_VALUES = ("1", "true", "yes", "on")
_GENERATED_SECRET_KEY_BYTES = 32


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE_VALUES


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    environment: str
    operator_token: Optional[str]


def load_settings() -> Settings:
    # SECRET_KEY: when unset, a random per-process key is used; nothing is ever hardcoded.
    secret_key = os.environ.get("SECRET_KEY") or os.urandom(_GENERATED_SECRET_KEY_BYTES).hex()
    # OPERATOR_TOKEN: unset means the operator-only endpoints stay closed (answer 403).
    operator_token = os.environ.get("OPERATOR_TOKEN") or None
    return Settings(
        secret_key=secret_key,
        debug=_flag("APP_DEBUG"),
        host=os.environ.get("APP_HOST", "0.0.0.0"),
        port=int(os.environ.get("APP_PORT", "5000")),
        db_path=os.environ.get("DB_PATH", "loja.db"),
        environment=os.environ.get("APP_ENV", "producao"),
        operator_token=operator_token,
    )
