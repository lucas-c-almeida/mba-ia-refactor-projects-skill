"""One-way password storage with a standard-library KDF (PBKDF2-HMAC-SHA256)."""
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000
SALT_BYTES = 16
# Stored for an account that must not be able to sign in (e.g. a seeded account
# whose password was not configured). It is not the output of any hash.
UNUSABLE = "!"


def hash_password(password):
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), ITERATIONS)
    return "{0}${1}${2}${3}".format(ALGORITHM, ITERATIONS, salt, digest.hex())


def is_hashed(stored):
    return isinstance(stored, str) and stored.startswith(ALGORITHM + "$")


def verify_password(stored, given):
    """Returns (matches, needs_rehash).

    Rows written before this module existed hold the password as given; they are
    verified in constant time and flagged for re-hashing on this successful sign-in.
    """
    if not isinstance(stored, str) or stored == "" or stored == UNUSABLE:
        return False, False
    if is_hashed(stored):
        try:
            _, iterations, salt, expected = stored.split("$")
            digest = hashlib.pbkdf2_hmac("sha256", given.encode("utf-8"), salt.encode("ascii"), int(iterations))
        except (ValueError, UnicodeError):
            return False, False
        matches = hmac.compare_digest(digest.hex(), expected)
        return matches, matches and int(iterations) != ITERATIONS
    matches = hmac.compare_digest(stored.encode("utf-8"), given.encode("utf-8"))
    return matches, matches
