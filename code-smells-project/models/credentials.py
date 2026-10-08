"""Password storage: salted one-way hashes, with transparent upgrade of legacy plain-text rows."""

import hmac

from werkzeug.security import check_password_hash, generate_password_hash

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def is_hashed(stored) -> bool:
    return isinstance(stored, str) and stored.startswith(_HASH_PREFIXES)


def verify_password(plain: str, stored) -> bool:
    """True when `plain` matches `stored`.

    Rows written before hashing existed hold the password as typed; they are compared in
    constant time here and re-hashed by the caller on success.
    """
    if is_hashed(stored):
        return check_password_hash(stored, plain)
    return hmac.compare_digest((stored or "").encode("utf-8"), plain.encode("utf-8"))
