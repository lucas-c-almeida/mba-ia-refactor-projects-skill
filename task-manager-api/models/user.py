import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utc_now
from models.constants import DEFAULT_ROLE, REDACTED_SECRET

# Digests written before the move to a password KDF: an unsalted MD5 hex string.
_LEGACY_DIGEST = re.compile(r'^[0-9a-f]{32}$')


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
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            # The field and its type stay; the stored hash is never returned.
            'password': REDACTED_SECRET,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if not isinstance(pwd, str):
            return False
        stored = self.password or ''
        if _LEGACY_DIGEST.match(stored):
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            return hmac.compare_digest(stored, legacy)
        return check_password_hash(stored, pwd)

    def needs_rehash(self):
        """True when the stored value is a legacy digest to upgrade on login."""
        return bool(_LEGACY_DIGEST.match(self.password or ''))
