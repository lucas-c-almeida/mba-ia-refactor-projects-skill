import logging
import re

from models.constants import DEFAULT_ROLE, EMAIL_PATTERN, MIN_PASSWORD_LENGTH, USER_ROLES
from models.errors import (
    AuthenticationError, ConflictError, ForbiddenError, NotFoundError, PersistenceError, ValidationError,
)
from models.user import User

logger = logging.getLogger(__name__)


def is_valid_email(email):
    return isinstance(email, str) and re.match(EMAIL_PATTERN, email) is not None


class UserController:
    def __init__(self, users, tasks, uow, clock):
        self._users = users
        self._tasks = tasks
        self._uow = uow
        self._clock = clock

    def _require_user(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def list_users(self):
        task_counts = self._tasks.counts_by_user()
        return [
            {
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': task_counts.get(u.id, 0),
            }
            for u in self._users.list_all()
        ]

    def get_user(self, user_id):
        user = self._require_user(user_id)
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in self._tasks.for_user(user_id)]
        return data

    def create_user(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

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
        if not is_valid_email(email):
            raise ValidationError('Email inválido')
        if not isinstance(password, str):
            raise ValidationError('Senha inválida')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        if self._users.get_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in USER_ROLES:
            raise ValidationError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        try:
            self._users.add(user)
            self._uow.commit()
            logger.info('Usuário criado: %s - %s', user.id, user.name)
            return user.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao criar usuário')
            raise PersistenceError('Erro ao criar usuário')

    def update_user(self, user_id, data):
        user = self._require_user(user_id)
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            if not is_valid_email(data['email']):
                raise ValidationError('Email inválido')
            existing = self._users.get_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            if not isinstance(data['password'], str):
                raise ValidationError('Senha inválida')
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if data['role'] not in USER_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        try:
            self._uow.commit()
            return user.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao atualizar usuário %s', user_id)
            raise PersistenceError('Erro ao atualizar')

    def delete_user(self, user_id):
        user = self._require_user(user_id)
        for task in self._tasks.for_user(user_id):
            self._tasks.delete(task)
        try:
            self._users.delete(user)
            self._uow.commit()
            logger.info('Usuário deletado: %s', user_id)
            return {'message': 'Usuário deletado com sucesso'}
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao deletar usuário %s', user_id)
            raise PersistenceError('Erro ao deletar')

    def list_user_tasks(self, user_id):
        self._require_user(user_id)
        now = self._clock()
        return [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(now),
            }
            for t in self._tasks.for_user(user_id)
        ]

    def login(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValidationError('Dados inválidos')

        user = self._users.get_by_email(email)
        if not user:
            raise AuthenticationError('Credenciais inválidas')
        if not user.check_password(password):
            raise AuthenticationError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.needs_password_upgrade():
            # Transparent upgrade: re-hash the legacy digest with the salted KDF.
            try:
                user.set_password(password)
                self._uow.commit()
            except Exception:
                self._uow.rollback()
                logger.warning('Não foi possível atualizar o hash da senha do usuário %s', user.id)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id),
        }
