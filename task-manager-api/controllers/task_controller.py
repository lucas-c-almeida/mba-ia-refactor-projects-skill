"""Task use cases. Plain values in, domain objects out; no request or response objects."""
import logging

from models.errors import (CATEGORY_NOT_FOUND, DELETE_FAILED, INVALID_DATA, TASK_NOT_FOUND,
                           UPDATE_FAILED, USER_NOT_FOUND, NotFoundError, ValidationError)
from models.task import (DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING, TASK_STATUSES, Task,
                         completion_rate, is_number, is_valid_priority, is_valid_reference,
                         is_valid_status, is_valid_tags, normalize_tags, parse_due_date,
                         title_length_error)

logger = logging.getLogger(__name__)

INVALID_STATUS = 'Status inválido'
PRIORITY_OUT_OF_RANGE = 'Prioridade deve ser entre 1 e 5'
INVALID_PRIORITY = 'Prioridade inválida'
INVALID_TITLE = 'Título inválido'
INVALID_DESCRIPTION = 'Descrição inválida'
INVALID_TAGS = 'Tags inválidas'
INVALID_REFERENCE = 'Referência inválida'


class TaskController:
    def __init__(self, tasks, users, categories, unit_of_work, clock):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._uow = unit_of_work
        self._clock = clock

    # --- queries -------------------------------------------------------------------------

    def list_tasks(self):
        """[(task, overdue)] with owner and category loaded."""
        now = self._clock()
        return [(t, t.is_overdue(now)) for t in self._tasks.list_all_with_owner_and_category()]

    def get_task(self, task_id):
        task = self._require_task(task_id)
        return task, task.is_overdue(self._clock())

    def search(self, text, status, priority, user_id):
        return self._tasks.search(text=text, status=status, priority=priority, user_id=user_id)

    def stats(self):
        total = self._tasks.count()
        by_status = self._tasks.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        result = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        result.update({
            'total': total,
            'overdue': self._tasks.count_overdue(self._clock()),
            'completion_rate': completion_rate(done, total),
        })
        return result

    # --- commands ------------------------------------------------------------------------
    # The checks run in the same order as before, so the same request gets the same answer.

    def create_task(self, data):
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        if not isinstance(title, str):
            raise ValidationError(INVALID_TITLE)
        length_error = title_length_error(title)
        if length_error:
            raise ValidationError(length_error)

        status = data.get('status', STATUS_PENDING)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        description = data.get('description', '')

        if not is_valid_status(status):
            raise ValidationError(INVALID_STATUS)
        self._check_priority(priority)
        self._check_description(description)
        if user_id:
            self._require_user(user_id)
        if category_id:
            self._require_category(category_id)
        if tags and not is_valid_tags(tags):
            raise ValidationError(INVALID_TAGS)

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id
        if due_date:
            task.due_date = self._parse_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
        if tags:
            task.tags = normalize_tags(tags)

        self._tasks.add(task)
        self._uow.commit('Erro ao criar task')
        logger.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update_task(self, task_id, data):
        task = self._require_task(task_id)
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)

        changes = {}
        if 'title' in data:
            if not isinstance(data['title'], str):
                raise ValidationError(INVALID_TITLE)
            length_error = title_length_error(data['title'])
            if length_error:
                raise ValidationError(length_error)
            changes['title'] = data['title']
        if 'description' in data:
            self._check_description(data['description'])
            changes['description'] = data['description']
        if 'status' in data:
            if not is_valid_status(data['status']):
                raise ValidationError(INVALID_STATUS)
            changes['status'] = data['status']
        if 'priority' in data:
            self._check_priority(data['priority'])
            changes['priority'] = data['priority']
        if 'user_id' in data:
            if data['user_id']:
                self._require_user(data['user_id'])
            changes['user_id'] = data['user_id']
        if 'category_id' in data:
            if data['category_id']:
                self._require_category(data['category_id'])
            changes['category_id'] = data['category_id']
        if 'due_date' in data:
            changes['due_date'] = (self._parse_date(data['due_date'], 'Formato de data inválido')
                                   if data['due_date'] else None)
        if 'tags' in data:
            if data['tags'] is not None and not is_valid_tags(data['tags']):
                raise ValidationError(INVALID_TAGS)
            changes['tags'] = normalize_tags(data['tags'])

        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = self._clock()

        self._uow.commit(UPDATE_FAILED)
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self._require_task(task_id)
        self._tasks.delete(task)
        self._uow.commit(DELETE_FAILED)
        logger.info('Task deletada: %s', task_id)

    # --- helpers -------------------------------------------------------------------------

    def _require_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def _require_user(self, user_id):
        if not is_valid_reference(user_id):
            raise ValidationError(INVALID_REFERENCE)
        if not self._users.get(user_id):
            raise NotFoundError(USER_NOT_FOUND)

    def _require_category(self, category_id):
        if not is_valid_reference(category_id):
            raise ValidationError(INVALID_REFERENCE)
        if not self._categories.get(category_id):
            raise NotFoundError(CATEGORY_NOT_FOUND)

    @staticmethod
    def _check_priority(priority):
        if not is_number(priority):
            raise ValidationError(INVALID_PRIORITY)
        if not is_valid_priority(priority):
            raise ValidationError(PRIORITY_OUT_OF_RANGE)

    @staticmethod
    def _check_description(description):
        if description is not None and not isinstance(description, str):
            raise ValidationError(INVALID_DESCRIPTION)

    @staticmethod
    def _parse_date(value, message):
        try:
            return parse_due_date(value)
        except (TypeError, ValueError):
            raise ValidationError(message)
