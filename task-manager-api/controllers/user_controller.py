"""User and authentication use cases. Plain values in, domain objects out."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from controllers.common import MSG_DELETE_FAILED, MSG_UPDATE_FAILED, require_object, required_text
from database import commit_or_fail, db
from models.errors import AuthenticationError, ConflictError, ForbiddenError, ValidationError
from models.task import Task
from models.user import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, USER_ROLES, User, is_valid_email

logger = logging.getLogger(__name__)

MSG_NAME_REQUIRED = 'Nome é obrigatório'
MSG_NAME_INVALID = 'Nome inválido'
MSG_EMAIL_REQUIRED = 'Email é obrigatório'
MSG_PASSWORD_REQUIRED = 'Senha é obrigatória'
MSG_EMAIL_INVALID = 'Email inválido'
MSG_PASSWORD_TOO_SHORT_CREATE = 'Senha deve ter no mínimo 4 caracteres'
MSG_PASSWORD_TOO_SHORT_UPDATE = 'Senha muito curta'
MSG_EMAIL_TAKEN = 'Email já cadastrado'
MSG_ROLE_INVALID = 'Role inválido'
MSG_ACTIVE_INVALID = 'Valor inválido para active'
MSG_CREDENTIALS_REQUIRED = 'Email e senha são obrigatórios'
MSG_BAD_CREDENTIALS = 'Credenciais inválidas'
MSG_INACTIVE = 'Usuário inativo'
MSG_CREATE_FAILED = 'Erro ao criar usuário'

# The token format is part of today's contract. Replacing it with a signed, expiring token
# is proposed (AP-04), not applied: it needs an identity model the application lacks.
LEGACY_TOKEN_PREFIX = 'fake-jwt-token-'


def _validate_password(password, too_short_message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(too_short_message)
    return password


class UserController:
    def list_users(self):
        counts = Task.counts_per_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in User.list_all()]

    def get_user(self, user_id):
        user = User.get_or_fail(user_id)
        return user, Task.list_for_user(user_id)

    def user_tasks(self, user_id):
        User.get_or_fail(user_id)
        return Task.list_for_user(user_id)

    def create(self, data):
        data = require_object(data)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        required_text(name, MSG_NAME_REQUIRED, MSG_NAME_INVALID)
        if not email:
            raise ValidationError(MSG_EMAIL_REQUIRED)
        if not password:
            raise ValidationError(MSG_PASSWORD_REQUIRED)
        if not is_valid_email(email):
            raise ValidationError(MSG_EMAIL_INVALID)
        _validate_password(password, MSG_PASSWORD_TOO_SHORT_CREATE)
        if User.find_by_email(email):
            raise ConflictError(MSG_EMAIL_TAKEN)
        # The role is still taken from the request: restricting it needs an identity model
        # (AP-04, proposed). Only the closed set is enforced here.
        if role not in USER_ROLES:
            raise ValidationError(MSG_ROLE_INVALID)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        commit_or_fail(MSG_CREATE_FAILED)
        logger.info('Usuário criado: %s - %s', user.id, user.name)
        return user

    def update(self, user_id, data):
        user = User.get_or_fail(user_id)
        data = require_object(data)
        changes = {}
        if 'name' in data:
            changes['name'] = required_text(data['name'], MSG_NAME_REQUIRED, MSG_NAME_INVALID)
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError(MSG_EMAIL_INVALID)
            existing = User.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError(MSG_EMAIL_TAKEN)
            changes['email'] = data['email']
        new_password = None
        if 'password' in data:
            new_password = _validate_password(data['password'], MSG_PASSWORD_TOO_SHORT_UPDATE)
        if 'role' in data:
            if data['role'] not in USER_ROLES:
                raise ValidationError(MSG_ROLE_INVALID)
            changes['role'] = data['role']
        if 'active' in data:
            if data['active'] not in (True, False):        # also accepts 0 and 1, as before
                raise ValidationError(MSG_ACTIVE_INVALID)
            changes['active'] = data['active']

        for field, value in changes.items():
            setattr(user, field, value)
        if new_password is not None:
            user.set_password(new_password)
        commit_or_fail(MSG_UPDATE_FAILED)
        return user

    def delete(self, user_id):
        user = User.get_or_fail(user_id)
        Task.delete_for_user(user_id)
        db.session.delete(user)
        commit_or_fail(MSG_DELETE_FAILED)
        logger.info('Usuário deletado: %s', user_id)

    def login(self, data):
        data = require_object(data)
        email = data.get('email')
        password = data.get('password')
        if not email or not password or not isinstance(email, str) or not isinstance(password, str):
            raise ValidationError(MSG_CREDENTIALS_REQUIRED)

        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError(MSG_BAD_CREDENTIALS)
        if not user.active:
            raise ForbiddenError(MSG_INACTIVE)
        if user.has_legacy_password_hash():
            self._upgrade_password_hash(user, password)
        return user, LEGACY_TOKEN_PREFIX + str(user.id)

    @staticmethod
    def _upgrade_password_hash(user, password):
        """Best-effort re-hash of a legacy MD5 credential. Deliberately narrow: a failure here
        must not fail a login that already succeeded; it is logged and retried on the next one."""
        user.set_password(password)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.warning('password hash upgrade failed for user %s; will retry on next login',
                           user.id, exc_info=True)
