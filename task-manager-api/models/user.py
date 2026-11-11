import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utcnow

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
PASSWORD_MIN_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

# Fields whose change takes over or locks an account: operator-only (RP-04).
PRIVILEGED_FIELDS = ('email', 'password', 'role', 'active')

# Digests written by the previous implementation (unsalted MD5, 32 hex characters).
# They are verified once at sign-in and replaced; see the report for the reset window.
_LEGACY_DIGEST = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.CheckConstraint('role IN ({0})'.format(', '.join("'{0}'".format(r) for r in VALID_ROLES)),
                           name='ck_users_role'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, pwd):
        # A purpose-built password KDF with a per-credential salt (RP-08).
        self.password = generate_password_hash(pwd)

    def uses_legacy_digest(self):
        return bool(_LEGACY_DIGEST.match(self.password or ''))

    def check_password(self, pwd):
        if self.uses_legacy_digest():
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)

    def differs_from(self, field, value):
        """Whether setting `field` to `value` would change the stored account."""
        if field == 'password':
            return not self.check_password(value)
        return getattr(self, field) != value


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email))
