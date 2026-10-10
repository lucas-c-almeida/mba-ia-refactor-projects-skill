"""User use cases and sign-in. Plain values in, domain objects or plain values out."""
import logging

from models.clock import utc_now
from models.constants import DEFAULT_ROLE, LOGIN_TOKEN_PREFIX
from models.errors import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from models.user import User
from models.validation import check_email, check_password_text, check_role

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, users, tasks, unit_of_work, clock=utc_now):
        self._users = users
        self._tasks = tasks
        self._uow = unit_of_work
        self._clock = clock

    # ---- queries -------------------------------------------------------

    def list_users(self):
        totals = self._tasks.totals_by_user()
        result = []
        for u in self._users.all():
            result.append({
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': totals.get(u.id, (0, 0))[0],
            })
        return result

    def find_user(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def get_user(self, user_id):
        user = self.find_user(user_id)
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in self._tasks.for_user(user_id)]
        return data

    def get_user_tasks(self, user_id):
        self.find_user(user_id)
        now = self._clock()
        result = []
        for t in self._tasks.for_user(user_id):
            result.append({
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(now),
            })
        return result

    # ---- commands ------------------------------------------------------

    def create_user(self, data):
        if not data:
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

        check_email(email)
        check_password_text(password, 'Senha deve ter no mínimo 4 caracteres')

        if self._users.find_by_email(email):
            raise ConflictError('Email já cadastrado')

        check_role(role)

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self._users.add(user)
        self._uow.commit_or_raise('Erro ao criar usuário')
        logger.info('Usuário criado: %s - %s', user.id, user.name)
        return user

    def update_user(self, user, data):
        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            check_email(data['email'])
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user.id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            check_password_text(data['password'], 'Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            user.role = check_role(data['role'])

        if 'active' in data:
            user.active = data['active']

        self._uow.commit_or_raise('Erro ao atualizar')
        return user

    def delete_user(self, user_id):
        user = self.find_user(user_id)
        for task in self._tasks.for_user(user_id):
            self._tasks.delete(task)
        self._users.delete(user)
        self._uow.commit_or_raise('Erro ao deletar')
        logger.info('Usuário deletado: %s', user_id)
        return {'message': 'Usuário deletado com sucesso'}

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self._users.find_by_email(email)
        if not user:
            raise AuthenticationError('Credenciais inválidas')

        if not user.check_password(password):
            raise AuthenticationError('Credenciais inválidas')

        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.needs_rehash():
            self._upgrade_hash(user, password)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': LOGIN_TOKEN_PREFIX + str(user.id),
        }

    def _upgrade_hash(self, user, password):
        """Re-hash a legacy digest with the current KDF after a successful sign-in.

        Best effort on purpose: a failed upgrade must not fail a valid sign-in. The
        legacy digest stays valid and the upgrade is retried at the next sign-in.
        """
        user.set_password(password)
        try:
            self._uow.commit()
        except Exception:
            self._uow.rollback()
            logger.exception('Could not upgrade the password hash of user %s', user.id)
