"""Use-case orchestration for users, including authentication (AP-05).

AP-04 (missing/bypassable authorization) is NOT fixed here: this application has no
identity model a fix could hook into (the login token below is never verified by any
route). Per the legitimate-use test (04-architecture-guidelines.md §6) that makes a real
fix contract-changing — every current client is anonymous and would receive the new
401 — so it is filed under `## Proposed, Not Applied` in reports/audit-latest.md rather
than applied here. `authenticate()` still exists and is unchanged: it is the login use
case, not the authorization gate.
"""
import re

from sqlalchemy import func

from database import db
from middlewares.errors import BadRequestError, ConflictError, ForbiddenError, \
    NotFoundError, UnauthorizedError
from models.task import Task
from models.user import MIN_PASSWORD_LENGTH, VALID_ROLES, User

_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


class UserController:

    def list_all(self):
        # RP-10: one grouped-count query instead of one `len(u.tasks)` lazy load per user
        # (AP-10 — was one extra query per user). Shape matches the original custom dict
        # exactly: no password field, unlike User.to_dict() (see get()/create()/update()).
        counts = dict(db.session.query(Task.user_id, func.count(Task.id))
                     .group_by(Task.user_id).all())
        return [
            {
                'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role,
                'active': u.active, 'created_at': str(u.created_at),
                'task_count': counts.get(u.id, 0),
            }
            for u in User.query.all()
        ]

    def get(self, user_id):
        user = self._require(user_id)
        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
        return data

    def create(self, data):
        if not data:
            raise BadRequestError('Dados inválidos')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise BadRequestError('Nome é obrigatório')
        if not email:
            raise BadRequestError('Email é obrigatório')
        if not password:
            raise BadRequestError('Senha é obrigatória')
        if not _EMAIL_PATTERN.match(email):
            raise BadRequestError('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise BadRequestError('Senha deve ter no mínimo {0} caracteres'.format(
                MIN_PASSWORD_LENGTH))
        if User.query.filter_by(email=email).first():
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise BadRequestError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role
        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    def update(self, user_id, data):
        user = self._require(user_id)
        if not data:
            raise BadRequestError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            if not _EMAIL_PATTERN.match(data['email']):
                raise BadRequestError('Email inválido')
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']
        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise BadRequestError('Senha muito curta')
            user.set_password(data['password'])
        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise BadRequestError('Role inválido')
            user.role = data['role']
        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    def delete(self, user_id):
        user = self._require(user_id)
        for task in Task.query.filter_by(user_id=user_id).all():
            db.session.delete(task)
        db.session.delete(user)
        db.session.commit()
        return {'message': 'Usuário deletado com sucesso'}

    def get_tasks(self, user_id):
        self._require(user_id)
        tasks = Task.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': t.id, 'title': t.title, 'description': t.description,
                'status': t.status, 'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(),
            }
            for t in tasks
        ]

    def authenticate(self, email, password):
        if not email or not password:
            raise BadRequestError('Email e senha são obrigatórios')
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id),
        }

    def _require(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user
