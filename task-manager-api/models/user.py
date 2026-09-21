"""User entity, its credential rules, and its persistence."""
import hashlib
import hmac
import re
import string

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utc_now

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER

MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')
_LEGACY_MD5_HEX_LENGTH = 32


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def set_password(self, raw_password):
        # Salted, work-factored password KDF (Werkzeug, already a Flask dependency).
        self.password = generate_password_hash(raw_password)

    def _has_legacy_hash(self):
        stored = self.password or ''
        return (len(stored) == _LEGACY_MD5_HEX_LENGTH
                and all(c in string.hexdigits for c in stored))

    def check_password(self, raw_password):
        if self._has_legacy_hash():
            # Hashes written before the KDF migration: verified once, in constant time,
            # then replaced on successful login (see UserController.login).
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, raw_password)

    def password_needs_upgrade(self):
        return self._has_legacy_hash()


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def is_valid_role(role):
    return role in USER_ROLES


def is_long_enough_password(password):
    return len(password) >= MIN_PASSWORD_LENGTH


class UserRepository:
    def __init__(self, session):
        self._session = session

    def get(self, user_id):
        return self._session.get(User, user_id)

    def list_all(self):
        return self._session.query(User).order_by(User.id).all()

    def find_by_email(self, email):
        return self._session.query(User).filter(User.email == email).first()

    def count(self):
        return self._session.query(db.func.count(User.id)).scalar()

    def add(self, user):
        self._session.add(user)

    def delete(self, user):
        self._session.delete(user)
