"""Runtime configuration, read from the environment exactly once (RP-01, RP-17).

Nothing else in the code base reads the environment. Unsafe values are opt-in:
debug is off unless APP_DEBUG says otherwise, and the operator guard stays
closed unless OPERATOR_TOKEN is set.
"""
import os
import secrets
from dataclasses import dataclass
from typing import List, Optional, Union

from dotenv import load_dotenv

DEFAULT_DATABASE_URI = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'  # same bind address the application always used
DEFAULT_PORT = 5000
ANY_ORIGIN = '*'  # the cross-origin policy the application always had
SECRET_KEY_BYTES = 32
TRUE_VALUES = ('1', 'true', 'yes', 'on')


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is unusable."""


@dataclass(frozen=True)
class Settings:
    database_uri: str
    secret_key: str
    debug: bool
    host: str
    port: int
    operator_token: Optional[str]
    cors_origins: Union[str, List[str]]
    cors_allow_private_network: bool


def _read_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def _read_port() -> int:
    raw = os.environ.get('APP_PORT', str(DEFAULT_PORT))
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f'APP_PORT must be an integer, got {raw!r}') from exc


def _read_origins() -> Union[str, List[str]]:
    raw = os.environ.get('CORS_ORIGINS', '').strip()
    if not raw:
        return ANY_ORIGIN
    return [origin.strip() for origin in raw.split(',') if origin.strip()]


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        database_uri=os.environ.get('DATABASE_URL', DEFAULT_DATABASE_URI),
        # No literal key: without SECRET_KEY a random per-process key is used.
        secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(SECRET_KEY_BYTES),
        debug=_read_flag('APP_DEBUG'),
        host=os.environ.get('APP_HOST', DEFAULT_HOST),
        port=_read_port(),
        # Unset by default: operator-only routes answer 403 until it is configured.
        operator_token=os.environ.get('OPERATOR_TOKEN') or None,
        # Defaults keep today's behaviour; narrowing them is the team's decision (see the report).
        cors_origins=_read_origins(),
        cors_allow_private_network=_read_flag('CORS_ALLOW_PRIVATE_NETWORK', default=True),
    )
