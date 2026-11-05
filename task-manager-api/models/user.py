import hashlib
import hmac
import os

from database import db
from models.clock import utc_now
from models.constants import DEFAULT_ROLE, USER_ROLES

PASSWORD_SCHEME = 'pbkdf2_sha256'
PASSWORD_ITERATIONS = 600_000
SALT_BYTES = 16
LEGACY_DIGEST_LENGTH = 32  # an unsalted MD5 hex digest written by earlier versions
MASKED_PASSWORD = '********'


def _derive(password, salt, iterations):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)


class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.CheckConstraint(
            'role IN (%s)' % ', '.join("'%s'" % r for r in USER_ROLES), name='ck_users_role'),
    )

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
            # The stored credential is never returned; the field and its type are kept.
            'password': MASKED_PASSWORD,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        salt = os.urandom(SALT_BYTES)
        digest = _derive(pwd, salt, PASSWORD_ITERATIONS)
        self.password = '%s$%d$%s$%s' % (PASSWORD_SCHEME, PASSWORD_ITERATIONS, salt.hex(), digest.hex())

    def _is_legacy_digest(self):
        return len(self.password) == LEGACY_DIGEST_LENGTH and '$' not in self.password

    def check_password(self, pwd):
        if self._is_legacy_digest():
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        try:
            _, iterations, salt_hex, digest_hex = self.password.split('$')
            expected = _derive(pwd, bytes.fromhex(salt_hex), int(iterations))
            return hmac.compare_digest(expected.hex(), digest_hex)
        except ValueError:
            return False

    def needs_password_upgrade(self):
        """True while the stored credential is still the legacy unsalted digest."""
        return self._is_legacy_digest()
