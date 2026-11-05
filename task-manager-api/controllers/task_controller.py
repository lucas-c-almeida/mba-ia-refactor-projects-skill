import logging
from datetime import datetime

from models.constants import (
    DUE_DATE_FORMAT, MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, TASK_STATUSES,
    DEFAULT_PRIORITY, DEFAULT_STATUS, STATUS_DONE,
)
from models.errors import NotFoundError, PersistenceError, ValidationError
from models.task import Task

logger = logging.getLogger(__name__)


def is_number(value):
    return isinstance(value, (int, float))


def parse_due_date(raw, message):
    try:
        return datetime.strptime(raw, DUE_DATE_FORMAT)
    except (ValueError, TypeError):
        raise ValidationError(message)


def normalize_tags(tags):
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    return tags


def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')


def validate_priority(priority):
    if not is_number(priority):
        raise ValidationError('Prioridade inválida')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')


def optional_int(raw, message):
    """Query-string number: absent or empty means "no filter"; anything else must parse."""
    if raw is None or raw == '':
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(message)


class TaskController:
    def __init__(self, tasks, users, categories, uow, clock):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._uow = uow
        self._clock = clock

    def _require_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _require_user(self, user_id):
        if not isinstance(user_id, (int, float, str)):
            raise ValidationError('Usuário inválido')
        if self._users.get(user_id) is None:
            raise NotFoundError('Usuário não encontrado')

    def _require_category(self, category_id):
        if not isinstance(category_id, (int, float, str)):
            raise ValidationError('Categoria inválida')
        if self._categories.get(category_id) is None:
            raise NotFoundError('Categoria não encontrada')

    def list_tasks(self):
        now = self._clock()
        tasks = self._tasks.list_all()
        user_names = self._users.names_by_id({t.user_id for t in tasks if t.user_id})
        category_names = self._categories.names_by_id({t.category_id for t in tasks if t.category_id})
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = user_names.get(task.user_id) if task.user_id else None
            data['category_name'] = category_names.get(task.category_id) if task.category_id else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = self._require_task(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue(self._clock())
        return data

    def create_task(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        validate_title(title)

        status = data.get('status', DEFAULT_STATUS)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        validate_priority(priority)
        if user_id is not None:
            self._require_user(user_id)
        if category_id is not None:
            self._require_category(category_id)

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id
        if due_date:
            task.due_date = parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')
        if tags:
            task.tags = normalize_tags(tags)

        try:
            self._tasks.add(task)
            self._uow.commit()
            logger.info('Task criada: %s - %s', task.id, task.title)
            return task.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao criar task')
            raise PersistenceError('Erro ao criar task')

    def update_task(self, task_id, data):
        task = self._require_task(task_id)
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            validate_title(data['title'])
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            if data['status'] not in TASK_STATUSES:
                raise ValidationError('Status inválido')
            task.status = data['status']
        if 'priority' in data:
            validate_priority(data['priority'])
            task.priority = data['priority']
        if 'user_id' in data:
            if data['user_id'] is not None:
                self._require_user(data['user_id'])
            task.user_id = data['user_id']
        if 'category_id' in data:
            if data['category_id'] is not None:
                self._require_category(data['category_id'])
            task.category_id = data['category_id']
        if 'due_date' in data:
            if data['due_date']:
                task.due_date = parse_due_date(data['due_date'], 'Formato de data inválido')
            else:
                task.due_date = None
        if 'tags' in data:
            task.tags = normalize_tags(data['tags'])

        task.updated_at = self._clock()

        try:
            self._uow.commit()
            logger.info('Task atualizada: %s', task.id)
            return task.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao atualizar task %s', task_id)
            raise PersistenceError('Erro ao atualizar')

    def delete_task(self, task_id):
        task = self._require_task(task_id)
        try:
            self._tasks.delete(task)
            self._uow.commit()
            logger.info('Task deletada: %s', task_id)
            return {'message': 'Task deletada com sucesso'}
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao deletar task %s', task_id)
            raise PersistenceError('Erro ao deletar')

    def search_tasks(self, text, status, priority, user_id):
        priority = optional_int(priority, 'Prioridade inválida')
        user_id = optional_int(user_id, 'Usuário inválido')
        return [t.to_dict() for t in self._tasks.search(text, status, priority, user_id)]

    def stats(self):
        now = self._clock()
        total = self._tasks.total()
        by_status = self._tasks.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': done,
            'cancelled': by_status.get('cancelled', 0),
            'overdue': self._tasks.count_overdue(now),
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
