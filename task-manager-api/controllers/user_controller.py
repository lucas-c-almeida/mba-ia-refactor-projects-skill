"""User and login use cases."""
import logging

from models.errors import (DELETE_FAILED, INVALID_DATA, UPDATE_FAILED, USER_NOT_FOUND,
                           ConflictError, Forbidden, NotAuthenticated, NotFoundError,
                           ValidationError)
from models.user import (DEFAULT_ROLE, MIN_PASSWORD_LENGTH, User, is_acceptable_password,
                         is_valid_email, is_valid_role)

logger = logging.getLogger(__name__)

INVALID_EMAIL = 'Email inválido'
EMAIL_TAKEN = 'Email já cadastrado'
INVALID_ROLE = 'Role inválido'
INVALID_CREDENTIALS = 'Credenciais inválidas'
INVALID_NAME = 'Nome inválido'


class UserController:
    def __init__(self, users, tasks, unit_of_work, clock):
        self._users = users
        self._tasks = tasks
        self._uow = unit_of_work
        self._clock = clock

    # --- queries -------------------------------------------------------------------------

    def list_users(self):
        """[(user, task_count)] — task counts from one grouped query."""
        totals = self._tasks.totals_by_user()
        return [(u, totals.get(u.id, (0, 0))[0]) for u in self._users.list_all()]

    def get_user(self, user_id):
        user = self._require_user(user_id)
        return user, self._tasks.list_by_user(user_id)

    def user_tasks(self, user_id):
        self._require_user(user_id)
        now = self._clock()
        return [(t, t.is_overdue(now)) for t in self._tasks.list_by_user(user_id)]

    # --- commands ------------------------------------------------------------------------

    def create_user(self, data):
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not isinstance(name, str):
            raise ValidationError(INVALID_NAME)
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not is_valid_email(email):
            raise ValidationError(INVALID_EMAIL)
        if not is_acceptable_password(password):
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if self._users.find_by_email(email):
            raise ConflictError(EMAIL_TAKEN)
        if not is_valid_role(role):
            raise ValidationError(INVALID_ROLE)

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self._users.add(user)
        self._uow.commit('Erro ao criar usuário')
        logger.info('Usuário criado: %s', user.id)
        return user

    def update_user(self, user_id, data):
        user = self._require_user(user_id)
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)

        if 'name' in data:
            if not isinstance(data['name'], str):
                raise ValidationError(INVALID_NAME)
            user.name = data['name']
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError(INVALID_EMAIL)
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError(EMAIL_TAKEN)
            user.email = data['email']
        if 'password' in data:
            if not is_acceptable_password(data['password']):
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if not is_valid_role(data['role']):
                raise ValidationError(INVALID_ROLE)
            user.role = data['role']
        if 'active' in data:
            if not isinstance(data['active'], bool):
                raise ValidationError('Campo active inválido')
            user.active = data['active']

        self._uow.commit(UPDATE_FAILED)
        return user

    def delete_user(self, user_id):
        user = self._require_user(user_id)
        self._tasks.delete_by_user(user_id)
        self._users.delete(user)
        self._uow.commit(DELETE_FAILED)
        logger.info('Usuário deletado: %s', user_id)

    def login(self, data):
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self._users.find_by_email(email)
        if not user or not user.check_password(password):
            raise NotAuthenticated(INVALID_CREDENTIALS)
        if not user.active:
            raise Forbidden('Usuário inativo')

        if user.has_legacy_password_hash():
            # Transparent migration off the legacy digest (RP-08).
            user.set_password(password)
            self._uow.commit(UPDATE_FAILED)
        return user

    # --- helpers -------------------------------------------------------------------------

    def _require_user(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user
