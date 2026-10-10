import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utc_now
from models.constants import DEFAULT_ROLE

_PASSWORD_METHOD = 'pbkdf2:sha256'
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

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd, method=_PASSWORD_METHOD)

    def check_password(self, pwd):
        """Verify a password. A digest stored by the previous scheme is still accepted once,
        and replaced by a salted hash (the caller commits): no flag day for existing accounts."""
        if _LEGACY_DIGEST.match(self.password or ''):
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            if hmac.compare_digest(self.password, legacy):
                self.set_password(pwd)
                return True
            return False
        return check_password_hash(self.password, pwd)
