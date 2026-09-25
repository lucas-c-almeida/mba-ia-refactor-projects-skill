"""
Configuration — the only module that reads the environment.

Fixes AP-01 (hardcoded secret key), part of AP-06 (configuration read at the point of
use) and part of AP-18 (debug mode / bind address hardcoded in source). Everything else
in the application receives a Settings object; nothing else reads os.environ.
"""
import os
import secrets


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    def __init__(self):
        # No literal secret in source. If the operator does not provide one, an
        # ephemeral key is generated for this process only, and a warning is printed
        # at startup so the gap is visible rather than silently "working" forever.
        env_secret = os.environ.get("SECRET_KEY")
        self.secret_key = env_secret or secrets.token_hex(32)
        self.secret_key_is_ephemeral = env_secret is None

        # Same default path as before ("loja.db"), now overridable — a fixed literal
        # in source was itself part of AP-06 ("configuration read at point of use").
        self.db_path = os.environ.get("DB_PATH", "loja.db")

        # The original hardcoded DEBUG = True unconditionally (AP-18). The safe
        # default is now False; an operator opts IN to debug, never out of it.
        self.debug = _bool_env("APP_DEBUG", False)

        self.host = os.environ.get("APP_HOST", "0.0.0.0")
        self.port = int(os.environ.get("APP_PORT", "5000"))

        # CORS stays wide open, matching the original CORS(app) with no restriction.
        # Narrowing it to a specific origin allow-list is a contract change for any
        # browser client that currently relies on the open policy — see the audit
        # report's "Proposed, Not Applied" section. The value is still centralized
        # here (rather than hardcoded at the call site) so applying that decision
        # later is a one-line change.
        self.cors_allow_all = _bool_env("APP_CORS_ALLOW_ALL", True)


def load_settings() -> Settings:
    return Settings()
