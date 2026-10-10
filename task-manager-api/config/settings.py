"""Runtime configuration, read from the environment once.

Everything that differs between environments, or that must not live in source,
is resolved here. Nothing else in the application reads the environment.
Unsafe values (debug mode) are opt-in; the operator credential is closed by default.
"""
import os
import secrets
from dataclasses import dataclass
from typing import Optional

_TRUE_VALUES = ('1', 'true', 'yes', 'on')


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is absent."""


def required(name, env=None):
    """Return a required variable or fail loudly, at startup, not at first use."""
    env = os.environ if env is None else env
    value = env.get(name)
    if not value:
        raise ConfigError(f"missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    database_uri: str
    secret_key: str
    debug: bool
    host: str
    port: int
    operator_token: Optional[str]


def load_settings(env=None):
    env = os.environ if env is None else env
    return Settings(
        database_uri=env.get('DATABASE_URI', 'sqlite:///tasks.db'),
        # The application keeps no sessions, so an unset key falls back to a
        # per-process random value instead of a literal in the source.
        secret_key=env.get('SECRET_KEY') or secrets.token_hex(32),
        debug=env.get('APP_DEBUG', 'false').strip().lower() in _TRUE_VALUES,
        host=env.get('APP_BIND', '0.0.0.0'),
        port=int(env.get('APP_PORT', '5000')),
        # Unset by default: the operator-only operations answer 403.
        operator_token=env.get('OPERATOR_TOKEN') or None,
    )
