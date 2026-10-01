"""User entity: columns, credential rules and persistence queries."""
import hashlib
import hmac
import re

from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.clock import utcnow
from models.errors import NotFoundError

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
USER_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER

MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

# Value returned in place of the stored credential: the field and its type are kept for
# existing clients, the secret is not (AP-08). Removing the field is proposed, not applied.
MASKED_SECRET = '********'

_LEGACY_MD5_PATTERN = re.compile(r'^[0-9a-f]{32}$')

MSG_NOT_FOUND = 'Usuário não encontrado'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    # --- credential rules ---------------------------------------------------------------

    def set_password(self, plain_password):
        """Store a salted, slow, one-way hash (Werkzeug's password KDF)."""
        self.password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        if self.has_legacy_password_hash():
            legacy = hashlib.md5(plain_password.encode()).hexdigest()
            return hmac.compare_digest(self.password, legacy)
        return check_password_hash(self.password, plain_password)

    def has_legacy_password_hash(self):
        """Hashes written before the KDF migration: unsalted MD5, upgraded on the next login."""
        return bool(self.password) and bool(_LEGACY_MD5_PATTERN.match(self.password))

    # --- persistence --------------------------------------------------------------------

    @staticmethod
    def find(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_or_fail(user_id):
        user = User.find(user_id)
        if not user:
            raise NotFoundError(MSG_NOT_FOUND)
        return user

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def list_all():
        return User.query.order_by(User.id).all()

    @staticmethod
    def count_all():
        return db.session.query(func.count(User.id)).scalar()


def is_valid_email(email):
    return isinstance(email, str) and bool(EMAIL_PATTERN.match(email))
