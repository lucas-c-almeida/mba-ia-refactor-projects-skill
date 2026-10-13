"""Application configuration: the only module that reads the environment."""
import os
import secrets
from dataclasses import dataclass
from typing import Mapping, Optional

_VERDADEIROS = ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    environment: str
    operator_token: Optional[str]


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Read the environment once and return an immutable configuration object.

    - SECRET_KEY: when absent, a random per-process key is generated (never a literal).
    - APP_DEBUG: off unless explicitly enabled.
    - OPERATOR_TOKEN: unset by default; operator-only routes answer 403 until configured.
    """
    env = os.environ if env is None else env
    return Settings(
        secret_key=env.get("SECRET_KEY") or secrets.token_hex(32),
        debug=env.get("APP_DEBUG", "").strip().lower() in _VERDADEIROS,
        host=env.get("HOST", "0.0.0.0"),
        port=int(env.get("PORT", "5000")),
        db_path=env.get("DB_PATH", "loja.db"),
        environment=env.get("APP_ENV", "producao"),
        operator_token=env.get("OPERATOR_TOKEN") or None,
    )
