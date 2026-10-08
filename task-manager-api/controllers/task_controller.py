"""Task use cases. Plain values in, plain values out; no web framework in sight."""
import logging
from datetime import datetime

from controllers.validation import reject_containers
from models.clock import utc_now
from models.errors import NotFoundError, ValidationError
from models.statistics import completion_rate
from models.task import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    PRIORITY_MAX,
    PRIORITY_MIN,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    TASK_STATUSES,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    Task,
)

logger = logging.getLogger(__name__)

DUE_DATE_FORMAT = '%Y-%m-%d'
PRIORITY_RANGE_MESSAGE = f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}'
DESCRIPTION_MESSAGE = 'Descrição inválida'
USER_INVALID_MESSAGE = 'Usuário inválido'
CATEGORY_INVALID_MESSAGE = 'Categoria inválida'


class TaskController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    # ---- reads -------------------------------------------------------------------------

    def list_tasks(self):
        now = self._clock()
        tasks = self._tasks.list_all()
        user_names = self._users.names_by_ids({t.user_id for t in tasks if t.user_id})
        category_names = self._categories.names_by_ids({t.category_id for t in tasks if t.category_id})
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = user_names.get(task.user_id) if task.user_id else None
            data['category_name'] = category_names.get(task.category_id) if task.category_id else None
            result.append(data)
        return result

    def get_task(self, task_id):
        task = self._find(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue(self._clock())
        return data

    def search(self, text='', status='', priority='', user_id=''):
        priority_value = self._parse_int(priority, 'Prioridade inválida')
        user_value = self._parse_int(user_id, 'Usuário inválido')
        tasks = self._tasks.search(text, status, priority_value, user_value)
        return [task.to_dict() for task in tasks]

    def stats(self):
        now = self._clock()
        total = self._tasks.count()
        by_status = self._tasks.count_by_status()
        done = by_status.get(STATUS_DONE, 0)
        return {
            'total': total,
            'pending': by_status.get(STATUS_PENDING, 0),
            'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
            'done': done,
            'cancelled': by_status.get(STATUS_CANCELLED, 0),
            'overdue': self._tasks.count_overdue(now),
            'completion_rate': completion_rate(done, total),
        }

    # ---- writes ------------------------------------------------------------------------

    def create_task(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        self._check_title(title)

        description = data.get('description', '')
        status = data.get('status', DEFAULT_STATUS)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        self._check_status(status)
        self._check_priority(priority)
        self._check_references(user_id, category_id)
        reject_containers(description, DESCRIPTION_MESSAGE)

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date:
            task.due_date = self._parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')

        if tags:
            self._check_tags(tags)
            task.tags = Task.tags_to_storage(tags)

        self._tasks.add(task)
        self._tasks.commit('Erro ao criar task')
        logger.info('task created: %s - %s', task.id, task.title)
        return task.to_dict()

    def update_task(self, task_id, read_body):
        task = self._find(task_id)

        data = read_body()
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            self._check_title(data['title'])
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            self._check_status(data['status'])
            task.status = data['status']

        if 'priority' in data:
            self._check_priority(data['priority'])
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id']:
                self._require_user(data['user_id'])
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id']:
                self._require_category(data['category_id'])
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                task.due_date = self._parse_due_date(data['due_date'], 'Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            self._check_tags(data['tags'])
            task.tags = Task.tags_to_storage(data['tags'])

        # Wrong-typed values are refused last, so the order of the intentional errors above
        # stays what clients have always seen.
        reject_containers(data.get('description'), DESCRIPTION_MESSAGE)
        reject_containers(data.get('user_id'), USER_INVALID_MESSAGE)
        reject_containers(data.get('category_id'), CATEGORY_INVALID_MESSAGE)

        task.updated_at = self._clock()

        self._tasks.commit('Erro ao atualizar')
        logger.info('task updated: %s', task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._find(task_id)
        self._tasks.delete(task)
        self._tasks.commit('Erro ao deletar')
        logger.info('task deleted: %s', task_id)
        return {'message': 'Task deletada com sucesso'}

    # ---- helpers -----------------------------------------------------------------------

    def _find(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def _check_title(self, title):
        if not isinstance(title, str):
            raise ValidationError('Título inválido')
        if len(title) < TITLE_MIN_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > TITLE_MAX_LENGTH:
            raise ValidationError('Título muito longo')

    def _check_status(self, status):
        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')

    def _check_priority(self, priority):
        if not Task.is_number(priority):
            raise ValidationError('Prioridade inválida')
        if not Task.priority_in_range(priority):
            raise ValidationError(PRIORITY_RANGE_MESSAGE)

    def _check_tags(self, tags):
        if isinstance(tags, dict):
            raise ValidationError('Tags inválidas')
        if isinstance(tags, list) and not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')

    def _check_references(self, user_id, category_id):
        if user_id:
            self._require_user(user_id)
        if category_id:
            self._require_category(category_id)

    def _require_user(self, user_id):
        reject_containers(user_id, USER_INVALID_MESSAGE)
        if not self._users.get(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _require_category(self, category_id):
        reject_containers(category_id, CATEGORY_INVALID_MESSAGE)
        if not self._categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')

    def _parse_due_date(self, value, message):
        try:
            return datetime.strptime(value, DUE_DATE_FORMAT)
        except (ValueError, TypeError):
            raise ValidationError(message)

    def _parse_int(self, raw, message):
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            raise ValidationError(message)
