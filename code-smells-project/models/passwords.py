"""One-way password storage with a purpose-built KDF and a transparent legacy upgrade path."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def hash_password(plain):
    return generate_password_hash(plain)


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(_HASH_PREFIXES)


def verify_password(stored, plain):
    """Return True when `plain` matches `stored`.

    Rows written before hashing was introduced hold the password as given; they are compared
    in constant time and must be re-hashed by the caller (see needs_rehash).
    """
    if stored is None:
        return False
    if is_hashed(stored):
        return check_password_hash(stored, plain)
    return hmac.compare_digest(str(stored).encode("utf-8"), plain.encode("utf-8"))


def needs_rehash(stored):
    return not is_hashed(stored)
