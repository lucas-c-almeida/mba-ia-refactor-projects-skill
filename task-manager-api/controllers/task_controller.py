"""Task use cases. Plain values in, domain objects out; no request objects, no queries."""
import logging

from models.errors import NotFoundError, PersistenceError, ValidationError
from models.task import Task, completion_rate, join_tags, parse_due_date, STATUS_CANCELLED, \
    STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'
USER_NOT_FOUND = 'Usuário não encontrado'
CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class TaskController:
    def __init__(self, tasks, users, categories, clock):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def list_tasks(self):
        now = self._clock.now()
        return [(task, user_name, category_name, task.is_overdue(now))
                for task, user_name, category_name in self._tasks.list_with_names()]

    def require_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def get_task(self, task_id):
        task = self.require_task(task_id)
        return task, task.is_overdue(self._clock.now())

    def _check_references(self, user_id, category_id):
        if user_id is not None and not self._users.get(user_id):
            raise NotFoundError(USER_NOT_FOUND)
        if category_id is not None and not self._categories.get(category_id):
            raise NotFoundError(CATEGORY_NOT_FOUND)

    def create_task(self, fields):
        self._check_references(fields['user_id'], fields['category_id'])
        task = Task()
        task.title = fields['title']
        task.description = fields['description']
        task.status = fields['status']
        task.priority = fields['priority']
        task.user_id = fields['user_id']
        task.category_id = fields['category_id']
        if fields['due_date']:
            try:
                task.due_date = parse_due_date(fields['due_date'])
            except ValueError:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
        if fields['tags']:
            task.tags = join_tags(fields['tags'])
        try:
            self._tasks.add(task)
            self._tasks.commit()
        except Exception:
            self._tasks.rollback()
            logger.exception('Erro ao criar task')
            raise PersistenceError('Erro ao criar task')
        logger.info('Task criada: %s', task.id)
        return task

    def update_task(self, task_id, changes):
        task = self.require_task(task_id)
        self._check_references(changes.get('user_id'), changes.get('category_id'))
        for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
            if field in changes:
                setattr(task, field, changes[field])
        if 'due_date' in changes:
            if changes['due_date']:
                try:
                    task.due_date = parse_due_date(changes['due_date'])
                except ValueError:
                    raise ValidationError('Formato de data inválido')
            else:
                task.due_date = None
        if 'tags' in changes:
            task.tags = join_tags(changes['tags'])
        task.updated_at = self._clock.now()
        try:
            self._tasks.commit()
        except Exception:
            self._tasks.rollback()
            logger.exception('Erro ao atualizar task %s', task_id)
            raise PersistenceError('Erro ao atualizar')
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self.require_task(task_id)
        try:
            self._tasks.delete(task)
            self._tasks.commit()
        except Exception:
            self._tasks.rollback()
            logger.exception('Erro ao deletar task %s', task_id)
            raise PersistenceError('Erro ao deletar')
        logger.info('Task deletada: %s', task_id)

    def search(self, text, status, priority, user_id):
        return self._tasks.search(text=text, status=status, priority=priority, user_id=user_id)

    def stats(self):
        by_status = self._tasks.count_by_status()
        total = self._tasks.count()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': self._tasks.count_overdue(self._clock.now()),
            'completion_rate': completion_rate(done, total),
        }
