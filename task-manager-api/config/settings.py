"""Configuration: read the environment once, validate it, expose an immutable object.

Nothing else in the application reads the environment (AP-01, AP-06, AP-18).
"""
import os
from dataclasses import dataclass

DEFAULT_DATABASE_URL = 'sqlite:///tasks.db'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000
TRUE_VALUES = ('1', 'true', 'yes', 'on')


class ConfigError(RuntimeError):
    """Raised at startup when required configuration is absent or malformed."""


def _required(env, name):
    value = env.get(name)
    if not value:
        raise ConfigError(f'missing required environment variable: {name}')
    return value


def _flag(env, name, default):
    raw = env.get(name)
    if raw is None or raw == '':
        return default
    return raw.strip().lower() in TRUE_VALUES


def _port(env, name, default):
    raw = env.get(name)
    if raw is None or raw == '':
        return default
    try:
        return int(raw)
    except ValueError as err:
        raise ConfigError(f'{name} must be an integer, got {raw!r}') from err


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    cors_allow_private_network: bool


@dataclass(frozen=True)
class SeedPasswords:
    """Passwords of the accounts seed.py creates. Required only by that script."""
    admin: str
    user: str
    manager: str


def load_seed_passwords(env=None):
    env = os.environ if env is None else env
    return SeedPasswords(
        admin=_required(env, 'SEED_ADMIN_PASSWORD'),
        user=_required(env, 'SEED_USER_PASSWORD'),
        manager=_required(env, 'SEED_MANAGER_PASSWORD'),
    )


def load_settings(env=None):
    env = os.environ if env is None else env
    return Settings(
        secret_key=_required(env, 'SECRET_KEY'),
        database_url=env.get('DATABASE_URL') or DEFAULT_DATABASE_URL,
        # Unsafe values are opt-in: debug (and its interactive debugger) is off unless asked for.
        debug=_flag(env, 'APP_DEBUG', False),
        host=env.get('APP_HOST') or DEFAULT_HOST,
        port=_port(env, 'APP_PORT', DEFAULT_PORT),
        # Same value the application used before (flask-cors 4.x default), now explicit.
        # Turning it off is proposed, not applied: it narrows the cross-origin policy.
        cors_allow_private_network=_flag(env, 'CORS_ALLOW_PRIVATE_NETWORK', True),
    )
