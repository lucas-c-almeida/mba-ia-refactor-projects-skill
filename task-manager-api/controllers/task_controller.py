"""Task use cases. Plain values in, domain objects or plain values out; no HTTP here."""
import logging

from sqlalchemy.exc import SQLAlchemyError

from controllers import messages
from controllers.transaction import commit
from controllers.validation import reject_container, require_object
from models.clock import utc_now
from models.errors import NotFoundError, PersistenceError, ValidationError
from models.task import (DEFAULT_PRIORITY, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY,
                         MIN_TITLE_LENGTH, STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS,
                         STATUS_PENDING, Task, completion_rate, is_number, is_valid_priority,
                         is_valid_status, is_valid_tags, parse_due_date, serialize_tags)

logger = logging.getLogger(__name__)

MSG_TASK_NOT_FOUND = 'Task não encontrada'
MSG_TITLE_REQUIRED = 'Título é obrigatório'
MSG_TITLE_INVALID = 'Título inválido'
MSG_TITLE_TOO_SHORT = 'Título muito curto'
MSG_TITLE_TOO_LONG = 'Título muito longo'
MSG_STATUS_INVALID = 'Status inválido'
MSG_PRIORITY_INVALID = 'Prioridade inválida'
MSG_PRIORITY_RANGE = f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}'
MSG_USER_ID_INVALID = 'Usuário inválido'
MSG_CATEGORY_ID_INVALID = 'Categoria inválida'
MSG_DESCRIPTION_INVALID = 'Descrição inválida'
MSG_TAGS_INVALID = 'Tags inválidas'


class TaskController:
    def __init__(self, session, tasks, users, categories, clock=utc_now):
        self._session = session
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    # -- queries ---------------------------------------------------------------

    def list_tasks(self):
        """Every task with its related user/category loaded, plus the overdue flag."""
        try:
            tasks = self._tasks.list_with_relations()
        except SQLAlchemyError:
            logger.exception('listing tasks failed')
            raise PersistenceError('Erro interno')
        now = self._clock()
        return [(task, task.is_overdue(now)) for task in tasks]

    def get_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(MSG_TASK_NOT_FOUND)
        return task, task.is_overdue(self._clock())

    def search(self, text, status, priority, user_id):
        return self._tasks.search(text=text or None,
                                  status=status or None,
                                  priority=_parse_int_param(priority, MSG_PRIORITY_INVALID),
                                  user_id=_parse_int_param(user_id, MSG_USER_ID_INVALID))

    def stats(self):
        total = self._tasks.count()
        by_status = self._tasks.count_by_status()
        done = by_status[STATUS_DONE]
        return {
            'total': total,
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'done': done,
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': self._tasks.count_overdue(self._clock()),
            'completion_rate': completion_rate(done, total),
        }

    # -- commands --------------------------------------------------------------

    def create_task(self, data):
        require_object(data)

        title = data.get('title')
        if not title:
            raise ValidationError(MSG_TITLE_REQUIRED)
        _check_title(title)

        description = reject_container(data.get('description', ''), MSG_DESCRIPTION_INVALID)
        status = data.get('status', STATUS_PENDING)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if not is_valid_status(status):
            raise ValidationError(MSG_STATUS_INVALID)
        _check_priority(priority)
        self._check_references(user_id, category_id)

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id
        if due_date:
            task.due_date = _parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
        if tags:
            _check_tags(tags)
            task.tags = serialize_tags(tags)

        self._tasks.add(task)
        commit(self._session, 'Erro ao criar task')
        logger.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update_task(self, task_id, data):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(MSG_TASK_NOT_FOUND)
        if not data:
            raise ValidationError(messages.INVALID_DATA)

        # Validate in the established order; apply only once everything has passed.
        changes = {}
        if 'title' in data:
            _check_title(data['title'])
            changes['title'] = data['title']
        if 'description' in data:
            changes['description'] = reject_container(data['description'], MSG_DESCRIPTION_INVALID)
        if 'status' in data:
            if not is_valid_status(data['status']):
                raise ValidationError(MSG_STATUS_INVALID)
            changes['status'] = data['status']
        if 'priority' in data:
            _check_priority(data['priority'])
            changes['priority'] = data['priority']
        if 'user_id' in data:
            self._check_references(data['user_id'], None)
            changes['user_id'] = data['user_id']
        if 'category_id' in data:
            self._check_references(None, data['category_id'])
            changes['category_id'] = data['category_id']
        if 'due_date' in data:
            raw = data['due_date']
            changes['due_date'] = _parse_due_date(raw, 'Formato de data inválido') if raw else None
        if 'tags' in data:
            _check_tags(data['tags'])
            changes['tags'] = serialize_tags(data['tags'])

        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = self._clock()

        commit(self._session, messages.UPDATE_FAILED)
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(MSG_TASK_NOT_FOUND)
        self._tasks.delete(task)
        commit(self._session, messages.DELETE_FAILED)
        logger.info('Task deletada: %s', task_id)

    # -- helpers ---------------------------------------------------------------

    def _check_references(self, user_id, category_id):
        reject_container(user_id, MSG_USER_ID_INVALID)
        reject_container(category_id, MSG_CATEGORY_ID_INVALID)
        if user_id and not self._users.get(user_id):
            raise NotFoundError(messages.USER_NOT_FOUND)
        if category_id and not self._categories.get(category_id):
            raise NotFoundError(messages.CATEGORY_NOT_FOUND)


def _check_title(title):
    if not isinstance(title, str):
        raise ValidationError(MSG_TITLE_INVALID)
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_TOO_SHORT)
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_TOO_LONG)


def _check_priority(priority):
    if not is_number(priority):
        raise ValidationError(MSG_PRIORITY_INVALID)
    if not is_valid_priority(priority):
        raise ValidationError(MSG_PRIORITY_RANGE)


def _check_tags(tags):
    if not is_valid_tags(tags):
        raise ValidationError(MSG_TAGS_INVALID)


def _parse_due_date(raw, message):
    try:
        return parse_due_date(raw)
    except (ValueError, TypeError):
        raise ValidationError(message)


def _parse_int_param(raw, message):
    if not raw:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise ValidationError(message)
