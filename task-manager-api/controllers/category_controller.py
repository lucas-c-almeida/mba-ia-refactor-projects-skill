"""Category use cases. Plain values in, domain objects or plain values out."""
from models.category import Category
from models.constants import DEFAULT_CATEGORY_COLOR
from models.errors import NotFoundError, ValidationError


class CategoryController:
    def __init__(self, categories, tasks, unit_of_work):
        self._categories = categories
        self._tasks = tasks
        self._uow = unit_of_work

    def list_categories(self):
        totals = self._tasks.totals_by_category()
        result = []
        for c in self._categories.all():
            data = c.to_dict()
            data['task_count'] = totals.get(c.id, 0)
            result.append(data)
        return result

    def find_category(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_CATEGORY_COLOR)

        self._categories.add(category)
        self._uow.commit_or_raise('Erro ao criar categoria')
        return category

    def update_category(self, category, data):
        if data is None:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        self._uow.commit_or_raise('Erro ao atualizar')
        return category

    def delete_category(self, category_id):
        category = self.find_category(category_id)
        self._categories.delete(category)
        self._uow.commit_or_raise('Erro ao deletar')
        return {'message': 'Categoria deletada'}
