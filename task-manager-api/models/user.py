"""User entity, its rules and credential storage (RP-08)."""
import hashlib
import hmac
import re
import secrets

from database import db
from models.clock import utc_now

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER

MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

# Password KDF from the standard library: salted, iterated, compared in constant time.
PASSWORD_SCHEME = 'pbkdf2_sha256'
PASSWORD_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16


def hash_password(password):
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, PASSWORD_ITERATIONS)
    return f'{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}'


def _verify_kdf(stored, password):
    try:
        _scheme, iterations, salt_hex, digest_hex = stored.split('$')
        candidate = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex),
                                        int(iterations))
    except ValueError:
        return False
    return hmac.compare_digest(candidate.hex(), digest_hex)


def _verify_legacy_md5(stored, password):
    # Accounts created before the KDF migration; re-hashed on their next successful login.
    return hmac.compare_digest(stored, hashlib.md5(password.encode()).hexdigest())


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, password):
        self.password = hash_password(password)

    def check_password(self, password):
        if not isinstance(password, str) or not self.password:
            return False
        if self.password.startswith(PASSWORD_SCHEME + '$'):
            return _verify_kdf(self.password, password)
        return _verify_legacy_md5(self.password, password)

    def has_legacy_password_hash(self):
        return not (self.password or '').startswith(PASSWORD_SCHEME + '$')


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_role(role):
    return role in USER_ROLES


def is_acceptable_password(password):
    return isinstance(password, str) and len(password) >= MIN_PASSWORD_LENGTH
