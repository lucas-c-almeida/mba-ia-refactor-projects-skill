"""Use-case orchestration for tasks (AP-05: this logic used to live in routes/task_routes.py).

Persistence lives on the model classes themselves (ActiveRecord-style ORM — `Task.query`
IS the model layer's own data access, so calling it here is not bypassing a repository;
04-architecture-guidelines.md §2 endorses this as the default for a project this size).
No framework request/response object is imported here (04-architecture-guidelines.md §2,
Controllers).
"""
from datetime import datetime

from sqlalchemy.orm import joinedload

from database import db, utcnow
from middlewares.errors import BadRequestError, NotFoundError
from models.category import Category
from models.task import MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, Task
from models.user import User


class TaskController:

    def list_all(self):
        # RP-10: one query with the two relations eagerly joined, instead of one extra
        # query per task per relation (AP-10 — was O(2N) round trips for N tasks).
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        return [
            t.to_dict(include_overdue=True,
                      user_name=t.user.name if t.user else None,
                      category_name=t.category.name if t.category else None)
            for t in tasks
        ]

    def get(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task.to_dict(include_overdue=True)

    def create(self, data):
        if not data:
            raise BadRequestError('Dados inválidos')

        title = self._validate_title(data.get('title'))
        status = self._validate_status(data.get('status', 'pending'))
        priority = self._validate_priority(data.get('priority', 3))
        user_id = self._validate_user_id(data.get('user_id'))
        category_id = self._validate_category_id(data.get('category_id'))
        due_date = self._parse_due_date(data.get('due_date'))

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id
        task.due_date = due_date
        task.tags = self._normalize_tags(data.get('tags'))

        db.session.add(task)
        db.session.commit()
        return task.to_dict()

    def update(self, task_id, data):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        if not data:
            raise BadRequestError('Dados inválidos')

        if 'title' in data:
            task.title = self._validate_title(data['title'])
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = self._validate_status(data['status'])
        if 'priority' in data:
            task.priority = self._validate_priority(data['priority'])
        if 'user_id' in data:
            task.user_id = self._validate_user_id(data['user_id'])
        if 'category_id' in data:
            task.category_id = self._validate_category_id(data['category_id'])
        if 'due_date' in data:
            task.due_date = self._parse_due_date(data['due_date']) if data['due_date'] else None
        if 'tags' in data:
            task.tags = self._normalize_tags(data['tags'])

        task.updated_at = utcnow()
        db.session.commit()
        return task.to_dict()

    def delete(self, task_id):
        task = Task.query.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        db.session.delete(task)
        db.session.commit()
        return {'message': 'Task deletada com sucesso'}

    def search(self, query, status, priority, user_id):
        tasks = Task.query
        if query:
            tasks = tasks.filter(db.or_(Task.title.like('%{0}%'.format(query)),
                                        Task.description.like('%{0}%'.format(query))))
        if status:
            tasks = tasks.filter(Task.status == status)
        if priority:
            tasks = tasks.filter(Task.priority == self._parse_int(priority, 'priority'))
        if user_id:
            tasks = tasks.filter(Task.user_id == self._parse_int(user_id, 'user_id'))
        return [t.to_dict() for t in tasks.all()]

    def stats(self):
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()
        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
        return {
            'total': total, 'pending': pending, 'in_progress': in_progress,
            'done': done, 'cancelled': cancelled, 'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }

    # -- boundary validation (AP-11): rejects only values no legitimate client sends --

    def _validate_title(self, title):
        if not title:
            raise BadRequestError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise BadRequestError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise BadRequestError('Título muito longo')
        return title

    def _validate_status(self, status):
        if not Task.is_valid_status(status):
            raise BadRequestError('Status inválido')
        return status

    def _validate_priority(self, priority):
        try:
            priority = int(priority)
        except (TypeError, ValueError):
            raise BadRequestError('Prioridade inválida')
        if not Task.is_valid_priority(priority):
            raise BadRequestError('Prioridade deve ser entre {0} e {1}'.format(
                MIN_PRIORITY, MAX_PRIORITY))
        return priority

    def _validate_user_id(self, user_id):
        if user_id and not User.query.get(user_id):
            raise NotFoundError('Usuário não encontrado')
        return user_id

    def _validate_category_id(self, category_id):
        if category_id and not Category.query.get(category_id):
            raise NotFoundError('Categoria não encontrada')
        return category_id

    def _parse_due_date(self, due_date):
        if not due_date:
            return None
        try:
            return datetime.strptime(due_date, '%Y-%m-%d')
        except (TypeError, ValueError):
            raise BadRequestError('Formato de data inválido. Use YYYY-MM-DD')

    def _normalize_tags(self, tags):
        if not tags:
            return tags
        return ','.join(tags) if isinstance(tags, list) else tags

    def _parse_int(self, value, field_name):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise BadRequestError('{0} deve ser um número'.format(field_name))
