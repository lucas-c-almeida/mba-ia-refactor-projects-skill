"""User use cases, including sign-in."""
import logging
import re

from controllers.validation import reject_containers
from models.clock import utc_now
from models.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PersistenceError,
    UnauthorizedError,
    ValidationError,
)
from models.user import EMAIL_PATTERN, PASSWORD_MIN_LENGTH, USER_ROLES, DEFAULT_ROLE, User

logger = logging.getLogger(__name__)

PLACEHOLDER_TOKEN_PREFIX = 'fake-jwt-token-'
NAME_INVALID_MESSAGE = 'Nome inválido'
ACTIVE_INVALID_MESSAGE = 'Valor de active inválido'


class UserController:
    def __init__(self, users, tasks, clock=utc_now):
        self._users = users
        self._tasks = tasks
        self._clock = clock

    # ---- reads -------------------------------------------------------------------------

    def list_users(self):
        task_counts = self._tasks.counts_by_user()
        result = []
        for user in self._users.list_all():
            result.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'active': user.active,
                'created_at': str(user.created_at),
                'task_count': task_counts.get(user.id, (0, 0))[0],
            })
        return result

    def get_user(self, user_id):
        user = self._find(user_id)
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in self._tasks.for_user(user_id)]
        return data

    def user_tasks(self, user_id):
        self._find(user_id)
        now = self._clock()
        result = []
        for task in self._tasks.for_user(user_id):
            result.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': str(task.created_at),
                'due_date': str(task.due_date) if task.due_date else None,
                'overdue': task.is_overdue(now),
            })
        return result

    # ---- writes ------------------------------------------------------------------------

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

        self._check_email(email)
        self._check_password(password, 'Senha deve ter no mínimo 4 caracteres')

        if self._users.find_by_email(email):
            raise ConflictError('Email já cadastrado')

        self._check_role(role)
        reject_containers(name, NAME_INVALID_MESSAGE)

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        self._users.add(user)
        self._users.commit('Erro ao criar usuário')
        logger.info('user created: %s - %s', user.id, user.name)
        return user.to_dict()

    def update_user(self, user_id, read_body):
        user = self._find(user_id)

        data = read_body()
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            self._check_email(data['email'])
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            self._check_password(data['password'], 'Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            self._check_role(data['role'])
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        # Wrong-typed values are refused last, so the order of the intentional errors above
        # stays what clients have always seen.
        reject_containers(data.get('name'), NAME_INVALID_MESSAGE)
        self._check_active(data.get('active'))

        self._users.commit('Erro ao atualizar')
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._find(user_id)
        self._tasks.delete_for_user(user_id)
        self._users.delete(user)
        self._users.commit('Erro ao deletar')
        logger.info('user deleted: %s', user_id)
        return {'message': 'Usuário deletado com sucesso'}

    def login(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self._users.find_by_email(email)
        if not user or not isinstance(password, str) or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')

        if not user.active:
            raise ForbiddenError('Usuário inativo')

        self._upgrade_legacy_digest(user, password)

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': PLACEHOLDER_TOKEN_PREFIX + str(user.id)
        }

    # ---- helpers -----------------------------------------------------------------------

    def _find(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def _check_email(self, email):
        if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
            raise ValidationError('Email inválido')

    def _check_password(self, password, too_short_message):
        if not isinstance(password, str):
            raise ValidationError('Senha inválida')
        if len(password) < PASSWORD_MIN_LENGTH:
            raise ValidationError(too_short_message)

    def _check_role(self, role):
        if role not in USER_ROLES:
            raise ValidationError('Role inválido')

    def _check_active(self, active):
        """The column is a boolean: anything the datastore driver cannot read as one is refused."""
        if active is not None and active not in (0, 1):
            raise ValidationError(ACTIVE_INVALID_MESSAGE)

    def _upgrade_legacy_digest(self, user, password):
        """Transparent upgrade: an old unsalted digest is replaced after a successful sign-in."""
        if not user.has_legacy_digest():
            return
        user.set_password(password)
        try:
            self._users.commit('Erro ao atualizar')
        except PersistenceError:
            logger.warning('could not upgrade the password hash of user %s', user.id)
