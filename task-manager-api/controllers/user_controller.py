import logging
import re

from controllers import validation as v
from models.constants import DEFAULT_ROLE, EMAIL_PATTERN, PASSWORD_MIN_LENGTH, USER_ROLES
from models.errors import (AuthenticationError, ConflictError, ForbiddenError, NotFoundError,
                           PersistenceError, ValidationError)
from models.user import User

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
_ACTIVE_VALUES = (True, False, 0, 1)


class UserController:
    def __init__(self, users, tasks):
        self._users = users
        self._tasks = tasks

    # --- queries ---------------------------------------------------------------------------

    def list_users(self):
        """Users with their task counts, counted in one grouped query."""
        counts = self._users.task_counts()
        return [(user, counts.get(user.id, 0)) for user in self._users.list_all()]

    def get_user(self, user_id):
        user = self._require(user_id)
        return user, self._tasks.for_user(user_id)

    def user_tasks(self, user_id):
        self._require(user_id)
        return self._tasks.for_user(user_id)

    # --- commands --------------------------------------------------------------------------

    def create(self, data):
        v.require_object(data)
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', DEFAULT_ROLE)

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')

        v.reject_structured(name, 'Nome inválido')
        self._check_email(email)
        v.require_text(password, 'Senha inválida')
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')

        if self._users.find_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in USER_ROLES:
            raise ValidationError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self._users.add(user)
        self._users.save('Erro ao criar usuário')
        logger.info('Usuário criado: %s - %s', user.id, user.name)
        return user

    def update(self, user_id, data):
        user = self._require(user_id)
        v.require_object(data)

        if 'name' in data:
            user.name = v.reject_structured(data['name'], 'Nome inválido')

        if 'email' in data:
            self._check_email(data['email'])
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            v.require_text(data['password'], 'Senha inválida')
            if len(data['password']) < PASSWORD_MIN_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in USER_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            active = data['active']
            if active is not None and active not in _ACTIVE_VALUES:
                raise ValidationError('Valor de active inválido')
            user.active = active

        self._users.save('Erro ao atualizar')
        return user

    def delete(self, user_id):
        user = self._require(user_id)
        tasks = self._tasks.for_user(user_id)
        self._users.delete_with_tasks(user, tasks)
        self._users.save('Erro ao deletar')
        logger.info('Usuário deletado: %s', user_id)

    def login(self, data):
        v.require_object(data)
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        v.reject_structured(email, 'Dados inválidos')

        user = self._users.find_by_email(email)
        if not user:
            raise AuthenticationError('Credenciais inválidas')

        v.require_text(password, 'Dados inválidos')
        stored = user.password
        if not user.check_password(password):
            raise AuthenticationError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.password != stored:
            # A legacy digest was replaced by a salted hash; failing to persist it must not fail the login.
            try:
                self._users.save('Erro ao atualizar')
            except PersistenceError:
                logger.warning('password upgrade not persisted for user %s', user.id)
        return user

    # --- rules -----------------------------------------------------------------------------

    def _require(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    @staticmethod
    def _check_email(email):
        v.require_text(email, 'Email inválido')
        if not re.match(EMAIL_PATTERN, email):
            raise ValidationError('Email inválido')
