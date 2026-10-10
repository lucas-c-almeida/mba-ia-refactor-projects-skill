import logging
from datetime import datetime

from controllers import validation as v
from models.clock import utc_now
from models.constants import (DATE_FORMAT, DEFAULT_PRIORITY, PRIORITY_MAX, PRIORITY_MIN,
                              STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING,
                              TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH)
from models.errors import NotFoundError, ValidationError
from models.task import Task

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = 'Task não encontrada'


class TaskController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    # --- queries ---------------------------------------------------------------------------

    def list_tasks(self):
        return self._tasks.list_with_relations()

    def get_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def search(self, text, status, priority, user_id):
        return self._tasks.search(text, status,
                                  self._int_param(priority, 'priority'),
                                  self._int_param(user_id, 'user_id'))

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
            'overdue': self._tasks.count_overdue(self._clock()),
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }

    # --- commands --------------------------------------------------------------------------

    def create(self, data):
        v.require_object(data)

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        v.require_text(title, 'Título inválido')
        self._check_title_length(title)

        description = v.reject_structured(data.get('description', ''), 'Descrição inválida')
        status = data.get('status', STATUS_PENDING)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if status not in TASK_STATUSES:
            raise ValidationError('Status inválido')
        self._check_priority(priority)
        if user_id:
            self._require_user(user_id)
        if category_id:
            self._require_category(category_id)

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
            task.tags = v.tags_to_storage(tags)

        self._tasks.add(task)
        self._tasks.save('Erro ao criar task')
        logger.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update(self, task_id, data):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        v.require_object(data)

        if 'title' in data:
            v.require_text(data['title'], 'Título inválido')
            self._check_title_length(data['title'])
            task.title = data['title']

        if 'description' in data:
            task.description = v.reject_structured(data['description'], 'Descrição inválida')

        if 'status' in data:
            if data['status'] not in TASK_STATUSES:
                raise ValidationError('Status inválido')
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
                task.due_date = self._parse_date(data['due_date'], 'Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            task.tags = v.tags_to_storage(data['tags'])

        task.updated_at = self._clock()
        self._tasks.save('Erro ao atualizar')
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError(TASK_NOT_FOUND)
        self._tasks.delete(task)
        self._tasks.save('Erro ao deletar')
        logger.info('Task deletada: %s', task_id)

    # --- rules -----------------------------------------------------------------------------

    @staticmethod
    def _check_title_length(title):
        if len(title) < TITLE_MIN_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > TITLE_MAX_LENGTH:
            raise ValidationError('Título muito longo')

    @staticmethod
    def _check_priority(priority):
        v.require_number(priority, 'Prioridade inválida')
        if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
            raise ValidationError('Prioridade deve ser entre 1 e 5')

    @staticmethod
    def _parse_date(value, message):
        try:
            return datetime.strptime(value, DATE_FORMAT)
        except Exception:
            raise ValidationError(message)

    @staticmethod
    def _int_param(raw, name):
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            raise ValidationError(f'Parâmetro {name} inválido')

    def _require_user(self, user_id):
        v.reject_structured(user_id, 'user_id inválido')
        if not self._users.get(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _require_category(self, category_id):
        v.reject_structured(category_id, 'category_id inválido')
        if not self._categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')
