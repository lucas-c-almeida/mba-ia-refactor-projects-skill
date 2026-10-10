"""Task use cases. Plain values in, domain objects or plain values out."""
import logging

from models.clock import utc_now
from models.constants import (
    DEFAULT_PRIORITY,
    DEFAULT_STATUS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from models.errors import NotFoundError, ValidationError
from models.statistics import completion_rate
from models.task import Task
from models.validation import (
    check_priority,
    check_reference_id,
    check_status,
    check_title,
    join_tags,
    parse_due_date,
    parse_optional_int,
)

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, tasks, users, categories, unit_of_work, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._uow = unit_of_work
        self._clock = clock

    # ---- queries -------------------------------------------------------

    def list_tasks(self):
        now = self._clock()
        tasks = self._tasks.all()
        user_names = self._users.names_by_ids(t.user_id for t in tasks)
        category_names = self._categories.names_by_ids(t.category_id for t in tasks)
        result = []
        for task in tasks:
            data = task.to_dict()
            data['overdue'] = task.is_overdue(now)
            data['user_name'] = user_names.get(task.user_id) if task.user_id else None
            data['category_name'] = category_names.get(task.category_id) if task.category_id else None
            result.append(data)
        return result

    def find_task(self, task_id):
        task = self._tasks.get(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')
        return task

    def get_task(self, task_id):
        task = self.find_task(task_id)
        data = task.to_dict()
        data['overdue'] = task.is_overdue(self._clock())
        return data

    def search(self, text, status, priority, user_id):
        priority_value = parse_optional_int(priority, 'Prioridade inválida')
        user_id_value = parse_optional_int(user_id, 'user_id inválido')
        return [t.to_dict() for t in self._tasks.search(text, status, priority_value, user_id_value)]

    def stats(self):
        total = self._tasks.count()
        done = self._tasks.count_by_status(STATUS_DONE)
        return {
            'total': total,
            'pending': self._tasks.count_by_status(STATUS_PENDING),
            'in_progress': self._tasks.count_by_status(STATUS_IN_PROGRESS),
            'done': done,
            'cancelled': self._tasks.count_by_status(STATUS_CANCELLED),
            'overdue': self._tasks.count_overdue(self._clock()),
            'completion_rate': completion_rate(done, total),
        }

    # ---- commands ------------------------------------------------------

    def _require_user(self, user_id):
        check_reference_id(user_id, 'user_id inválido')
        if user_id and not self._users.get(user_id):
            raise NotFoundError('Usuário não encontrado')

    def _require_category(self, category_id):
        check_reference_id(category_id, 'category_id inválido')
        if category_id and not self._categories.get(category_id):
            raise NotFoundError('Categoria não encontrada')

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        if not title:
            raise ValidationError('Título é obrigatório')
        check_title(title)

        description = data.get('description', '')
        status = data.get('status', DEFAULT_STATUS)
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        check_status(status)
        check_priority(priority)
        self._require_user(user_id)
        self._require_category(category_id)

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date:
            task.due_date = parse_due_date(due_date, 'Formato de data inválido. Use YYYY-MM-DD')

        if tags:
            task.tags = join_tags(tags)

        self._tasks.add(task)
        self._uow.commit_or_raise('Erro ao criar task')
        logger.info('Task criada: %s - %s', task.id, task.title)
        return task

    def update_task(self, task, data):
        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            task.title = check_title(data['title'])

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            task.status = check_status(data['status'])

        if 'priority' in data:
            task.priority = check_priority(data['priority'])

        if 'user_id' in data:
            self._require_user(data['user_id'])
            task.user_id = data['user_id']

        if 'category_id' in data:
            self._require_category(data['category_id'])
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                task.due_date = parse_due_date(data['due_date'], 'Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            task.tags = join_tags(data['tags'])

        task.updated_at = self._clock()

        self._uow.commit_or_raise('Erro ao atualizar')
        logger.info('Task atualizada: %s', task.id)
        return task

    def delete_task(self, task_id):
        task = self.find_task(task_id)
        self._tasks.delete(task)
        self._uow.commit_or_raise('Erro ao deletar')
        logger.info('Task deletada: %s', task_id)
        return {'message': 'Task deletada com sucesso'}
