"""User and sign-in use cases."""
import logging

from database import commit, db
from models.clock import utc_now
from models.errors import (AuthenticationError, ConflictError, ForbiddenError, ValidationError)
from models.task import Task
from models.user import DEFAULT_ROLE, MIN_PASSWORD_LENGTH, User

logger = logging.getLogger(__name__)

# The sign-in token is kept exactly as clients receive it today; a verified token is part of the
# identity-model proposal (AP-04, proposed).
LEGACY_TOKEN_PREFIX = 'fake-jwt-token-'


class UserController:
    def __init__(self, clock=utc_now):
        self._now = clock

    def list_users(self):
        """[(user, task_count)] in two queries."""
        counts = Task.counts_per_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in User.all_ordered()]

    def get_user(self, user_id):
        user = User.get_or_404(user_id)
        return user, Task.for_user(user_id)

    def require_user(self, user_id):
        return User.get_or_404(user_id)

    def create_user(self, name, email, password, role):
        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        User.check_email(email)
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if User.find_by_email(email):
            raise ConflictError('Email já cadastrado')
        role = DEFAULT_ROLE if role is None else role
        User.check_role(role)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        commit('Erro ao criar usuário')
        logger.info('user created: %s', user.id)
        return user

    def update_user(self, user, fields, is_operator):
        """Validate every field, then apply. Changing `role` or `active` to a value different
        from the stored one is an operator action (gate decision D2); resending the stored
        values is an ordinary profile update."""
        if 'email' in fields:
            User.check_email(fields['email'])
            existing = User.find_by_email(fields['email'])
            if existing and existing.id != user.id:
                raise ConflictError('Email já cadastrado')
        if 'password' in fields and len(fields['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        if 'role' in fields:
            User.check_role(fields['role'])

        changes_role = 'role' in fields and fields['role'] != user.role
        changes_active = 'active' in fields and fields['active'] != user.active
        if (changes_role or changes_active) and not is_operator:
            raise ForbiddenError('Operação restrita ao operador')

        if 'name' in fields:
            user.name = fields['name']
        if 'email' in fields:
            user.email = fields['email']
        if 'password' in fields:
            user.set_password(fields['password'])
        if 'role' in fields:
            user.role = fields['role']
        if 'active' in fields:
            user.active = fields['active']
        commit('Erro ao atualizar')
        return user

    def delete_user(self, user_id):
        """Operator-only (guarded at the route). Removes the account and its tasks."""
        user = User.get_or_404(user_id)
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.delete(user)
        commit('Erro ao deletar')
        logger.info('user deleted: %s', user_id)

    def user_tasks(self, user_id):
        User.get_or_404(user_id)
        now = self._now()
        return [(task, task.is_overdue(now)) for task in Task.for_user(user_id)]

    def login(self, email, password):
        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')
        if not isinstance(email, str) or not isinstance(password, str):
            raise AuthenticationError('Credenciais inválidas')
        user = User.find_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        if user.needs_rehash():
            self._upgrade_hash(user, password)
        return user, LEGACY_TOKEN_PREFIX + str(user.id)

    @staticmethod
    def _upgrade_hash(user, password):
        """Replace a legacy digest with the KDF on a successful sign-in. Best effort, on
        purpose: the sign-in already succeeded, and a failure here only postpones the upgrade
        to the next sign-in — it is logged, never hidden."""
        user.set_password(password)
        try:
            commit('Erro ao atualizar')
        except Exception:  # noqa: BLE001 — deliberate and narrow in effect; see docstring
            logger.warning('password hash upgrade failed for user %s; will retry at next login',
                           user.id, exc_info=True)
