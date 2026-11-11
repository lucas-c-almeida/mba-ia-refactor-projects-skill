"""Category use cases (split out of the former reports module, RP-03)."""
import logging

from models.category import Category
from models.errors import NotFoundError, PersistenceError

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryController:
    def __init__(self, categories, tasks):
        self._categories = categories
        self._tasks = tasks

    def list_categories(self):
        counts = self._tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in self._categories.list_all()]

    def require_category(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category

    def create_category(self, name, description, color):
        category = Category()
        category.name = name
        category.description = description
        category.color = color
        try:
            self._categories.add(category)
            self._categories.commit()
        except Exception:
            self._categories.rollback()
            logger.exception('Erro ao criar categoria')
            raise PersistenceError('Erro ao criar categoria')
        return category

    def update_category(self, category_id, changes):
        category = self.require_category(category_id)
        for field in ('name', 'description', 'color'):
            if field in changes:
                setattr(category, field, changes[field])
        try:
            self._categories.commit()
        except Exception:
            self._categories.rollback()
            logger.exception('Erro ao atualizar categoria %s', category_id)
            raise PersistenceError('Erro ao atualizar')
        return category

    def delete_category(self, category_id):
        category = self.require_category(category_id)
        try:
            # The ORM detaches the category's tasks (sets their category_id to NULL), as before.
            self._categories.delete(category)
            self._categories.commit()
        except Exception:
            self._categories.rollback()
            logger.exception('Erro ao deletar categoria %s', category_id)
            raise PersistenceError('Erro ao deletar')
