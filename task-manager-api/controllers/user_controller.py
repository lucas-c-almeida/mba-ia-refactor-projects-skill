"""User and authentication use cases. Plain values in, domain objects out; no HTTP here."""
import logging

from controllers import messages
from controllers.transaction import commit
from controllers.validation import (reject_container, require_boolean, require_object,
                                    require_present_scalar)
from models.clock import utc_now
from models.errors import (AuthenticationError, ConflictError, ForbiddenError, NotFoundError,
                           ValidationError)
from models.user import (DEFAULT_ROLE, MIN_PASSWORD_LENGTH, User, is_long_enough_password,
                         is_valid_email, is_valid_role)

logger = logging.getLogger(__name__)

MSG_EMAIL_INVALID = 'Email inválido'
MSG_EMAIL_TAKEN = 'Email já cadastrado'
MSG_ROLE_INVALID = 'Role inválido'
MSG_PASSWORD_INVALID = 'Senha inválida'
MSG_BAD_CREDENTIALS = 'Credenciais inválidas'
MSG_NAME_INVALID = 'Nome inválido'
MSG_ACTIVE_INVALID = 'Valor inválido para active'

# The login response keeps the token format existing clients receive. It is NOT a
# verifiable credential -- see the report, "Proposed, Not Applied" (AP-04).
LEGACY_TOKEN_PREFIX = 'fake-jwt-token-'


class UserController:
    def __init__(self, session, users, tasks, clock=utc_now):
        self._session = session
        self._users = users
        self._tasks = tasks
        self._clock = clock

    # -- queries ---------------------------------------------------------------

    def list_users(self):
        """Every user with the number of tasks assigned to them (one grouped query)."""
        totals = self._tasks.totals_per_user()
        return [(user, totals.get(user.id, (0, 0))[0]) for user in self._users.list_all()]

    def get_user(self, user_id):
        user = self._require(user_id)
        return user, self._tasks.list_by_user(user_id)

    def list_user_tasks(self, user_id):
        """A user's tasks, each with its overdue flag."""
        self._require(user_id)
        now = self._clock()
        return [(task, task.is_overdue(now)) for task in self._tasks.list_by_user(user_id)]

    # -- commands --------------------------------------------------------------

    def create_user(self, data):
        require_object(data)

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        if not name:
            raise ValidationError(messages.NAME_REQUIRED)
        reject_container(name, MSG_NAME_INVALID)
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not is_valid_email(email):
            raise ValidationError(MSG_EMAIL_INVALID)
        _check_password(password, f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if self._users.find_by_email(email):
            raise ConflictError(MSG_EMAIL_TAKEN)
        if not is_valid_role(role):
            raise ValidationError(MSG_ROLE_INVALID)

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self._users.add(user)
        commit(self._session, 'Erro ao criar usuário')
        logger.info('Usuário criado: %s', user.id)
        return user

    def update_user(self, user_id, data):
        user = self._require(user_id)
        if not data:
            raise ValidationError(messages.INVALID_DATA)

        # Validate in the established order; apply only once everything has passed.
        changes = {}
        new_password = None
        if 'name' in data:
            changes['name'] = require_present_scalar(data['name'], MSG_NAME_INVALID)
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError(MSG_EMAIL_INVALID)
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError(MSG_EMAIL_TAKEN)
            changes['email'] = data['email']
        if 'password' in data:
            _check_password(data['password'], 'Senha muito curta')
            new_password = data['password']
        if 'role' in data:
            if not is_valid_role(data['role']):
                raise ValidationError(MSG_ROLE_INVALID)
            changes['role'] = data['role']
        if 'active' in data:
            changes['active'] = require_boolean(data['active'], MSG_ACTIVE_INVALID)

        for field, value in changes.items():
            setattr(user, field, value)
        if new_password is not None:
            user.set_password(new_password)

        commit(self._session, messages.UPDATE_FAILED)
        return user

    def delete_user(self, user_id):
        user = self._require(user_id)
        self._tasks.delete_by_user(user_id)
        self._users.delete(user)
        commit(self._session, messages.DELETE_FAILED)
        logger.info('Usuário deletado: %s', user_id)

    def login(self, data):
        require_object(data)
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        if not isinstance(email, str) or not isinstance(password, str):
            raise AuthenticationError(MSG_BAD_CREDENTIALS)

        user = self._users.find_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError(MSG_BAD_CREDENTIALS)
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.password_needs_upgrade():
            # Transparent migration off the legacy digest, on the only occasion the
            # plaintext is legitimately available.
            user.set_password(password)
            commit(self._session, messages.UPDATE_FAILED)

        return user, LEGACY_TOKEN_PREFIX + str(user.id)

    # -- helpers ---------------------------------------------------------------

    def _require(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(messages.USER_NOT_FOUND)
        return user


def _check_password(password, too_short_message):
    if not isinstance(password, str):
        raise ValidationError(MSG_PASSWORD_INVALID)
    if not is_long_enough_password(password):
        raise ValidationError(too_short_message)
