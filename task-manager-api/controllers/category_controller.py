import logging

from models.category import Category
from models.constants import DEFAULT_CATEGORY_COLOR
from models.errors import NotFoundError, PersistenceError, ValidationError

logger = logging.getLogger(__name__)


class CategoryController:
    def __init__(self, categories, tasks, uow):
        self._categories = categories
        self._tasks = tasks
        self._uow = uow

    def _require_category(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def list_categories(self):
        counts = self._tasks.counts_by_category()
        result = []
        for category in self._categories.list_all():
            data = category.to_dict()
            data['task_count'] = counts.get(category.id, 0)
            result.append(data)
        return result

    def create_category(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_CATEGORY_COLOR)

        try:
            self._categories.add(category)
            self._uow.commit()
            return category.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao criar categoria')
            raise PersistenceError('Erro ao criar categoria')

    def update_category(self, category_id, data):
        category = self._require_category(category_id)
        if not isinstance(data, dict):
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        try:
            self._uow.commit()
            return category.to_dict()
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao atualizar categoria %s', category_id)
            raise PersistenceError('Erro ao atualizar')

    def delete_category(self, category_id):
        category = self._require_category(category_id)
        try:
            self._categories.delete(category)
            self._uow.commit()
            return {'message': 'Categoria deletada'}
        except Exception:
            self._uow.rollback()
            logger.exception('Erro ao deletar categoria %s', category_id)
            raise PersistenceError('Erro ao deletar')
