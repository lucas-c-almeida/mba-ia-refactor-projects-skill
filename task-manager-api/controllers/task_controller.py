"""Task use cases. Plain values in, domain objects out; no request or response objects."""
import logging

from controllers.common import MSG_DELETE_FAILED, MSG_UPDATE_FAILED, require_object
from database import commit_or_fail, db
from models.category import Category
from models.errors import ValidationError
from models.task import (DEFAULT_PRIORITY, MSG_TITLE_REQUIRED, STATUS_DONE, STATUS_PENDING, Task,
                         completion_rate, normalize_tags, parse_due_date, validate_description,
                         validate_priority, validate_status, validate_title)
from models.user import User

logger = logging.getLogger(__name__)

MSG_CREATE_DATE_INVALID = 'Formato de data inválido. Use YYYY-MM-DD'
MSG_UPDATE_DATE_INVALID = 'Formato de data inválido'
MSG_CREATE_FAILED = 'Erro ao criar task'


class TaskController:
    def __init__(self, clock):
        self._clock = clock

    def now(self):
        return self._clock()

    def list_tasks(self):
        return Task.list_with_relations()

    def get_task(self, task_id):
        return Task.get_or_fail(task_id)

    def search(self, text, status, priority, user_id):
        return Task.search(text=text, status=status, priority=priority, user_id=user_id)

    def create(self, data):
        data = require_object(data)
        title = data.get('title')
        if not title:
            raise ValidationError(MSG_TITLE_REQUIRED)
        validate_title(title)
        description = validate_description(data.get('description', ''))
        status = validate_status(data.get('status', STATUS_PENDING))
        priority = validate_priority(data.get('priority', DEFAULT_PRIORITY))
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        if user_id:
            User.get_or_fail(user_id)
        if category_id:
            Category.get_or_fail(category_id)

        task = Task(title=title, description=description, status=status, priority=priority,
                    user_id=user_id, category_id=category_id)
        due_date = data.get('due_date')
        if due_date:
            task.due_date = parse_due_date(due_date, MSG_CREATE_DATE_INVALID)
        tags = data.get('tags')
        if tags:
            task.tags = normalize_tags(tags)

        db.session.add(task)
        commit_or_fail(MSG_CREATE_FAILED)
        logger.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update(self, task_id, data):
        task = Task.get_or_fail(task_id)
        data = require_object(data)
        changes = {}
        if 'title' in data:
            changes['title'] = validate_title(data['title'])
        if 'description' in data:
            changes['description'] = validate_description(data['description'])
        if 'status' in data:
            changes['status'] = validate_status(data['status'])
        if 'priority' in data:
            changes['priority'] = validate_priority(data['priority'])
        if 'user_id' in data:
            if data['user_id']:
                User.get_or_fail(data['user_id'])
            changes['user_id'] = data['user_id']
        if 'category_id' in data:
            if data['category_id']:
                Category.get_or_fail(data['category_id'])
            changes['category_id'] = data['category_id']
        if 'due_date' in data:
            changes['due_date'] = (parse_due_date(data['due_date'], MSG_UPDATE_DATE_INVALID)
                                   if data['due_date'] else None)
        if 'tags' in data:
            changes['tags'] = normalize_tags(data['tags'])

        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = self.now()
        commit_or_fail(MSG_UPDATE_FAILED)
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete(self, task_id):
        task = Task.get_or_fail(task_id)
        db.session.delete(task)
        commit_or_fail(MSG_DELETE_FAILED)
        logger.info('Task deletada: %s', task_id)

    def stats(self):
        now = self.now()
        total = Task.count_all()
        by_status = Task.count_by_status()
        return {
            'total': total,
            'by_status': by_status,
            'overdue': Task.count_overdue(now),
            'completion_rate': completion_rate(by_status[STATUS_DONE], total),
        }
