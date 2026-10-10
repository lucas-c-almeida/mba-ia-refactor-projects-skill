"""One-way password storage with the standard library (a salted, work-factor key derivation)."""
import base64
import hashlib
import hmac
import os

_SCHEME = "scrypt"
_N, _R, _P = 2 ** 14, 8, 1
_SALT_BYTES = 16
_KEY_BYTES = 32


def _derive(password, salt, n, r, p):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=_KEY_BYTES)


def hash_password(password):
    salt = os.urandom(_SALT_BYTES)
    key = _derive(password, salt, _N, _R, _P)
    return "$".join([
        _SCHEME, str(_N), str(_R), str(_P),
        base64.b64encode(salt).decode("ascii"), base64.b64encode(key).decode("ascii"),
    ])


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(_SCHEME + "$")


def verify_password(password, stored):
    """Return (matches, needs_rehash). Rows written before hashing existed hold the plain text."""
    if not isinstance(stored, str):
        return False, False
    if not is_hashed(stored):
        return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8")), True
    try:
        _, n, r, p, salt, key = stored.split("$")
        expected = base64.b64decode(key)
        actual = _derive(password, base64.b64decode(salt), int(n), int(r), int(p))
    except ValueError:
        return False, False
    return hmac.compare_digest(actual, expected), False
