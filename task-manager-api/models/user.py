import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utc_now

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
PASSWORD_MIN_LENGTH = 4
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
MASKED_PASSWORD = '********'
LEGACY_DIGEST_PATTERN = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # The stored hash never leaves the model: the field stays (clients may read the key),
        # its value is masked (RP-08).
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': MASKED_PASSWORD,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        # Purpose-built password KDF with a per-credential salt (RP-08).
        self.password = generate_password_hash(pwd)

    def has_legacy_digest(self):
        return bool(LEGACY_DIGEST_PATTERN.match(self.password or ''))

    def check_password(self, pwd):
        if self.has_legacy_digest():
            # Accounts created before the KDF still hold an unsalted digest. It is only verified
            # here, never written; the controller replaces it after a successful login.
            legacy = hashlib.md5(pwd.encode(), usedforsecurity=False).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, pwd)
