"""Application configuration: the only module that reads the environment."""
import os
import secrets
from dataclasses import dataclass
from typing import Mapping, Optional

DEFAULT_DATABASE_URI = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000


@dataclass(frozen=True)
class Settings:
    database_uri: str
    secret_key: str
    debug: bool
    host: str
    port: int
    # Credential of the operator-only operations. None means the guard stays closed.
    operator_token: Optional[str]


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    env = os.environ if env is None else env
    return Settings(
        database_uri=env.get('DATABASE_URL', DEFAULT_DATABASE_URI),
        # No literal fallback: without SECRET_KEY a random per-process key is used.
        secret_key=env.get('SECRET_KEY') or secrets.token_hex(32),
        debug=env.get('APP_DEBUG', 'false').lower() == 'true',
        host=env.get('APP_HOST', DEFAULT_HOST),
        port=int(env.get('APP_PORT', str(DEFAULT_PORT))),
        operator_token=env.get('OPERATOR_TOKEN') or None,
    )
