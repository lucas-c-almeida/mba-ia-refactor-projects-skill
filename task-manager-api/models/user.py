"""User entity, credential storage and queries (RP-08)."""
import hashlib
import hmac
import re
import secrets

from database import db, get_by_id
from models.clock import utc_now
from models.errors import NotFoundError, ValidationError

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
DEFAULT_ROLE = ROLE_USER

MIN_PASSWORD_LENGTH = 4
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')

# Responses keep the `password` field (a string) but never its value.
MASKED_SECRET = '********'

# scrypt: salted, memory-hard password KDF from the standard library.
_SCHEME = 'scrypt'
_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32
_SCRYPT_MAXMEM = 64 * 1024 * 1024
_LEGACY_MD5_LENGTH = 32


def _scrypt(password, salt, n, r, p):
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p,
                          dklen=_KEY_BYTES, maxmem=_SCRYPT_MAXMEM)


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
            'password': MASKED_SECRET,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    # --- credentials -----------------------------------------------------------------------

    def set_password(self, password):
        salt = secrets.token_bytes(_SALT_BYTES)
        digest = _scrypt(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P)
        self.password = '$'.join([_SCHEME, str(_SCRYPT_N), str(_SCRYPT_R), str(_SCRYPT_P),
                                  salt.hex(), digest.hex()])

    def check_password(self, password):
        stored = self.password or ''
        if stored.startswith(_SCHEME + '$'):
            try:
                _, n, r, p, salt_hex, digest_hex = stored.split('$')
                candidate = _scrypt(password, bytes.fromhex(salt_hex), int(n), int(r), int(p))
            except ValueError:
                return False
            return hmac.compare_digest(candidate.hex(), digest_hex)
        if len(stored) == _LEGACY_MD5_LENGTH:
            # Hashes written before the KDF: verified once, then replaced (needs_rehash).
            legacy = hashlib.md5(password.encode()).hexdigest()
            return hmac.compare_digest(legacy, stored)
        return False

    def needs_rehash(self):
        return not (self.password or '').startswith(_SCHEME + '$')

    # --- rules -----------------------------------------------------------------------------

    @staticmethod
    def check_email(email):
        if not EMAIL_PATTERN.match(email):
            raise ValidationError('Email inválido')

    @staticmethod
    def check_role(role):
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

    # --- queries ---------------------------------------------------------------------------

    @classmethod
    def find(cls, user_id):
        return get_by_id(cls, user_id)

    @classmethod
    def get_or_404(cls, user_id):
        user = cls.find(user_id)
        if user is None:
            raise NotFoundError('Usuário não encontrado')
        return user

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def all_ordered(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return db.session.query(db.func.count(cls.id)).scalar()

    @classmethod
    def names_by_id(cls, ids):
        ids = [i for i in ids if i is not None]
        if not ids:
            return {}
        return dict(db.session.query(cls.id, cls.name).filter(cls.id.in_(set(ids))).all())
