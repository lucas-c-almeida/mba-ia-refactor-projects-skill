"""Category use cases."""
from models.category import DEFAULT_COLOR, Category
from models.errors import (CATEGORY_NOT_FOUND, DELETE_FAILED, INVALID_DATA, UPDATE_FAILED,
                           NotFoundError, ValidationError)

INVALID_FIELD = 'Campo inválido'


class CategoryController:
    def __init__(self, categories, tasks, unit_of_work):
        self._categories = categories
        self._tasks = tasks
        self._uow = unit_of_work

    def list_categories(self):
        """[(category, task_count)] — counts from one grouped query."""
        counts = self._tasks.count_by_category()
        return [(c, counts.get(c.id, 0)) for c in self._categories.list_all()]

    def create_category(self, data):
        if not data or not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        description = data.get('description', '')
        color = data.get('color', DEFAULT_COLOR)
        self._check_text_fields(name, description, color)

        category = Category()
        category.name = name
        category.description = description
        category.color = color

        self._categories.add(category)
        self._uow.commit('Erro ao criar categoria')
        return category

    def update_category(self, category_id, data):
        category = self._require_category(category_id)
        if not isinstance(data, dict):
            raise ValidationError(INVALID_DATA)

        self._check_text_fields(data.get('name'), data.get('description'), data.get('color'))
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        self._uow.commit(UPDATE_FAILED)
        return category

    def delete_category(self, category_id):
        category = self._require_category(category_id)
        self._categories.delete(category)
        self._uow.commit(DELETE_FAILED)

    @staticmethod
    def _check_text_fields(*values):
        # Wrong-type values only; format rules (e.g. a colour pattern) would be a product decision.
        if any(value is not None and not isinstance(value, str) for value in values):
            raise ValidationError(INVALID_FIELD)

    def _require_category(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category
