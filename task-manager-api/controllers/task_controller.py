"""Task use cases. Plain values in, domain objects out; no HTTP here."""
import logging

from database import commit, db
from models.category import Category
from models.clock import utc_now
from models.task import (DEFAULT_PRIORITY, DEFAULT_STATUS, STATUS_CANCELLED, STATUS_DONE,
                         STATUS_IN_PROGRESS, STATUS_PENDING, Task, completion_rate)
from models.user import User

logger = logging.getLogger(__name__)

CREATE_DATE_ERROR = 'Formato de data inválido. Use YYYY-MM-DD'
UPDATE_DATE_ERROR = 'Formato de data inválido'


class TaskController:
    def __init__(self, clock=utc_now):
        self._now = clock

    def list_tasks(self):
        """[(task, overdue, user_name, category_name)] — names resolved in two set queries."""
        now = self._now()
        tasks = Task.all_ordered()
        user_names = User.names_by_id(t.user_id for t in tasks)
        category_names = Category.names_by_id(t.category_id for t in tasks)
        return [(task, task.is_overdue(now),
                 user_names.get(task.user_id) if task.user_id else None,
                 category_names.get(task.category_id) if task.category_id else None)
                for task in tasks]

    def get_task(self, task_id):
        task = Task.get_or_404(task_id)
        return task, task.is_overdue(self._now())

    def require_task(self, task_id):
        return Task.get_or_404(task_id)

    def create_task(self, fields):
        title = fields['title']
        Task.check_title(title)
        status = fields.get('status', DEFAULT_STATUS)
        Task.check_status(status)
        priority = fields.get('priority', DEFAULT_PRIORITY)
        Task.check_priority(priority)
        user_id = fields.get('user_id')
        if user_id is not None:
            User.get_or_404(user_id)
        category_id = fields.get('category_id')
        if category_id is not None:
            Category.get_or_404(category_id)

        task = Task(title=title, description=fields.get('description', ''), status=status,
                    priority=priority, user_id=user_id, category_id=category_id)
        if fields.get('due_date'):
            task.due_date = Task.parse_due_date(fields['due_date'], CREATE_DATE_ERROR)
        if fields.get('tags'):
            task.tags = Task.join_tags(fields['tags'])

        db.session.add(task)
        commit('Erro ao criar task')
        logger.info('task created: %s', task.id)
        return task

    def update_task(self, task, fields):
        if 'title' in fields:
            Task.check_title(fields['title'])
            task.title = fields['title']
        if 'description' in fields:
            task.description = fields['description']
        if 'status' in fields:
            Task.check_status(fields['status'])
            task.status = fields['status']
        if 'priority' in fields:
            Task.check_priority(fields['priority'])
            task.priority = fields['priority']
        if 'user_id' in fields:
            if fields['user_id'] is not None:
                User.get_or_404(fields['user_id'])
            task.user_id = fields['user_id']
        if 'category_id' in fields:
            if fields['category_id'] is not None:
                Category.get_or_404(fields['category_id'])
            task.category_id = fields['category_id']
        if 'due_date' in fields:
            task.due_date = (Task.parse_due_date(fields['due_date'], UPDATE_DATE_ERROR)
                             if fields['due_date'] else None)
        if 'tags' in fields:
            task.tags = Task.join_tags(fields['tags'])
        task.updated_at = self._now()

        commit('Erro ao atualizar')
        logger.info('task updated: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = Task.get_or_404(task_id)
        db.session.delete(task)
        commit('Erro ao deletar')
        logger.info('task deleted: %s', task_id)

    def search(self, text, status, priority, user_id):
        return Task.search(text=text, status=status, priority=priority, user_id=user_id)

    def stats(self):
        now = self._now()
        total = Task.count_all()
        by_status = Task.counts_by(Task.status)
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': Task.count_overdue(now),
            'completion_rate': completion_rate(done, total),
        }
