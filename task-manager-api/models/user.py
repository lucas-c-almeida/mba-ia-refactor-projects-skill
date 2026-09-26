from werkzeug.security import check_password_hash, generate_password_hash

from database import db, utcnow

# AP-15: role whitelist named once instead of repeated as a bare list literal.
VALID_ROLES = ('user', 'admin', 'manager')
MIN_PASSWORD_LENGTH = 4

_MASKED_PASSWORD = '********'   # AP-08: never serialize the real hash — see to_dict() below.


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # AP-08: the original serialized the real password hash to every caller, with no
        # authentication at all in front of it (AP-04). The field is kept (removing it would
        # be a contract change — 04-architecture-guidelines.md §6) but its value is masked;
        # no legitimate client ever reads a password back.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': _MASKED_PASSWORD,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        # AP-08: was hashlib.md5(pwd).hexdigest() — a fast, unsalted, general-purpose
        # digest. werkzeug's generate_password_hash is a purpose-built, salted, tunable
        # password KDF (PBKDF2 by default) and is already a transitive Flask dependency,
        # so this adds no new runtime dependency.
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        if self._is_legacy_hash():
            import hashlib
            if self.password != hashlib.md5(pwd.encode()).hexdigest():
                return False
            # Transparent upgrade-on-login (RP-08): a correct legacy password rehashes
            # itself with the new KDF so the weak digest is never stored again, with no
            # forced reset and no observable change for the legitimate client.
            self.set_password(pwd)
            db.session.commit()
            return True
        return check_password_hash(self.password, pwd)

    def _is_legacy_hash(self):
        # werkzeug hashes are "<method>:<...>$<salt>$<hash>"; a bare 32-char hex string
        # is the old MD5 output. Never guess from memory which prefix werkzeug uses —
        # this only checks the *shape* (has a werkzeug-style separator or not).
        return '$' not in self.password and ':' not in self.password

    def is_admin(self):
        return self.role == 'admin'
