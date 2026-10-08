"""Category use cases."""
from controllers.validation import reject_containers
from models.category import DEFAULT_CATEGORY_COLOR, Category
from models.errors import NotFoundError, ValidationError

FIELD_INVALID_MESSAGE = 'Campo inválido'


class CategoryController:
    def __init__(self, categories, tasks):
        self._categories = categories
        self._tasks = tasks

    def list_categories(self):
        task_counts = self._tasks.counts_by_category()
        result = []
        for category in self._categories.list_all():
            data = category.to_dict()
            data['task_count'] = task_counts.get(category.id, 0)
            result.append(data)
        return result

    def create_category(self, data):
        if not isinstance(data, dict) or not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        description = data.get('description', '')
        color = data.get('color', DEFAULT_CATEGORY_COLOR)
        for value in (name, description, color):
            reject_containers(value, FIELD_INVALID_MESSAGE)

        category = Category()
        category.name = name
        category.description = description
        category.color = color

        self._categories.add(category)
        self._categories.commit('Erro ao criar categoria')
        return category.to_dict()

    def update_category(self, category_id, read_body):
        category = self._find(category_id)

        data = read_body()
        if not isinstance(data, dict):
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']

        for field in ('name', 'description', 'color'):
            reject_containers(data.get(field), FIELD_INVALID_MESSAGE)

        self._categories.commit('Erro ao atualizar')
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._find(category_id)
        self._categories.delete(category)
        self._categories.commit('Erro ao deletar')
        return {'message': 'Categoria deletada'}

    def _find(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category
