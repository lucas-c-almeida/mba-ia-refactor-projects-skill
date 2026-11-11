"""Account use cases."""
import logging

from models.errors import (AuthenticationError, ConflictError, ForbiddenError, NotFoundError,
                           PersistenceError, ValidationError)
from models.user import PASSWORD_MIN_LENGTH, PRIVILEGED_FIELDS, VALID_ROLES, User, is_valid_email

logger = logging.getLogger(__name__)

USER_NOT_FOUND = 'Usuário não encontrado'
INVALID_CREDENTIALS = 'Credenciais inválidas'
FORBIDDEN = 'Acesso negado'
SESSION_TOKEN_PREFIX = 'fake-jwt-token-'


class UserController:
    def __init__(self, users, tasks, clock):
        self._users = users
        self._tasks = tasks
        self._clock = clock

    def list_users(self):
        counts = self._tasks.count_by_user()
        return [(user, counts.get(user.id, 0)) for user in self._users.list_all()]

    def require_user(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    def get_user(self, user_id):
        user = self.require_user(user_id)
        return user, self._tasks.list_for_user(user_id)

    def user_tasks(self, user_id):
        self.require_user(user_id)
        now = self._clock.now()
        return [(task, task.is_overdue(now)) for task in self._tasks.list_for_user(user_id)]

    def create_user(self, name, email, password, role):
        if not is_valid_email(email):
            raise ValidationError('Email inválido')
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError('Senha deve ter no mínimo {0} caracteres'.format(PASSWORD_MIN_LENGTH))
        if self._users.find_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role
        try:
            self._users.add(user)
            self._users.commit()
        except Exception:
            self._users.rollback()
            logger.exception('Erro ao criar usuário')
            raise PersistenceError('Erro ao criar usuário')
        logger.info('Usuário criado: %s', user.id)
        return user

    def update_user(self, user_id, changes, operator_authorized):
        user = self.require_user(user_id)
        # Taking over or locking an account is operator-only; refuse before writing anything.
        changing_privileged = [field for field in PRIVILEGED_FIELDS
                               if field in changes and user.differs_from(field, changes[field])]
        if changing_privileged and not operator_authorized:
            raise ForbiddenError(FORBIDDEN)

        if 'name' in changes:
            user.name = changes['name']
        if 'email' in changes:
            if not is_valid_email(changes['email']):
                raise ValidationError('Email inválido')
            existing = self._users.find_by_email(changes['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = changes['email']
        if 'password' in changes:
            if len(changes['password']) < PASSWORD_MIN_LENGTH:
                raise ValidationError('Senha muito curta')
            if 'password' in changing_privileged:
                user.set_password(changes['password'])
        if 'role' in changes:
            if changes['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = changes['role']
        if 'active' in changes:
            user.active = changes['active']
        try:
            self._users.commit()
        except Exception:
            self._users.rollback()
            logger.exception('Erro ao atualizar usuário %s', user_id)
            raise PersistenceError('Erro ao atualizar')
        return user

    def delete_user(self, user_id):
        user = self.require_user(user_id)
        for task in self._tasks.list_for_user(user_id):
            self._tasks.delete(task)
        try:
            self._users.delete(user)
            self._users.commit()
        except Exception:
            self._users.rollback()
            logger.exception('Erro ao deletar usuário %s', user_id)
            raise PersistenceError('Erro ao deletar')
        logger.info('Usuário deletado: %s', user_id)

    def login(self, email, password):
        user = self._users.find_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.uses_legacy_digest():
            self._upgrade_digest(user, password)
        # Unverified token, kept as the contract had it; an identity model is proposed.
        return user, SESSION_TOKEN_PREFIX + str(user.id)

    def _upgrade_digest(self, user, password):
        """Replace a legacy digest at a successful sign-in. Best effort: sign-in still succeeds."""
        user.set_password(password)
        try:
            self._users.commit()
        except Exception:
            self._users.rollback()
            logger.warning('could not upgrade the password digest of user %s', user.id)
