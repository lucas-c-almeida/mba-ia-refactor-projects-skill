"""Configuration: the only module that reads the process environment.

Every value is read once, at startup, into an immutable Settings object that the
composition root (app.py) hands to whoever needs it. Unsafe behaviour (debug mode,
an open operator route) is opt-in: the defaults are the safe values.
"""
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Values an example file could carry that must still count as "not configured".
# The example file ships these keys empty, so the empty string is the placeholder.
_UNSET_MARKERS = frozenset({""})

_TRUE_WORDS = frozenset({"1", "true", "yes", "on"})
_FALSE_WORDS = frozenset({"0", "false", "no", "off"})


class ConfigError(RuntimeError):
    """Raised at startup when a configuration value is present but invalid."""


def _text(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def _secret(name):
    value = os.environ.get(name, "").strip()
    return "" if value in _UNSET_MARKERS else value


def _flag(name, default):
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    word = raw.strip().lower()
    if word in _TRUE_WORDS:
        return True
    if word in _FALSE_WORDS:
        return False
    raise ConfigError("invalid boolean for {0}: {1!r}".format(name, raw))


def _port(name, default):
    raw = _text(name, str(default))
    if not raw.isdigit() or not 0 < int(raw) < 65536:
        raise ConfigError("invalid port for {0}: {1!r}".format(name, raw))
    return int(raw)


def _origins(name, default):
    raw = _text(name, default)
    if raw == "*":
        return "*"
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if not origins:
        raise ConfigError("{0} must be '*' or a comma-separated list of origins".format(name))
    return origins


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_file: str
    database_path: Path
    environment: str
    cors_origins: object
    operator_token: str
    seed_admin_password: str
    seed_customer_password: str


def load_settings():
    database_file = _text("DATABASE_FILE", "loja.db")
    return Settings(
        secret_key=_secret("SECRET_KEY"),
        debug=_flag("APP_DEBUG", False),
        host=_text("APP_HOST", "0.0.0.0"),
        port=_port("APP_PORT", 5000),
        database_file=database_file,
        # Resolved against the project root, never the working directory.
        database_path=(PROJECT_ROOT / database_file).resolve(),
        environment=_text("APP_ENV", "producao"),
        cors_origins=_origins("CORS_ORIGINS", "*"),
        operator_token=_secret("OPERATOR_TOKEN"),
        seed_admin_password=_secret("SEED_ADMIN_PASSWORD"),
        seed_customer_password=_secret("SEED_CUSTOMER_PASSWORD"),
    )
