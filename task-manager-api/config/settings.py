"""Configuration: the only module that reads the process environment."""
import os
import secrets
from dataclasses import dataclass
from typing import Optional

DEFAULT_DATABASE_URI = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000


class ConfigError(RuntimeError):
    """Raised at startup when configuration is invalid."""


def _flag(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_uri: str
    debug: bool
    host: str
    port: int
    # Credential for privileged operations. Unset by default: those operations stay closed.
    operator_token: Optional[str]


def load_settings(environ=None):
    env = os.environ if environ is None else environ
    try:
        port = int(env.get('APP_PORT', DEFAULT_PORT))
    except ValueError:
        raise ConfigError('APP_PORT must be an integer')
    return Settings(
        # The application keeps no sessions today; without SECRET_KEY a random per-process key is used.
        secret_key=env.get('SECRET_KEY') or secrets.token_hex(32),
        database_uri=env.get('DATABASE_URL', DEFAULT_DATABASE_URI),
        debug=_flag('APP_DEBUG', False),
        host=env.get('APP_HOST', DEFAULT_HOST),
        port=port,
        operator_token=env.get('OPERATOR_TOKEN') or None,
    )
