from controllers import validation as v
from models.category import Category
from models.constants import DEFAULT_CATEGORY_COLOR
from models.errors import NotFoundError, ValidationError

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


class CategoryController:
    def __init__(self, categories, tasks):
        self._categories = categories
        self._tasks = tasks

    def list_categories(self):
        """Categories with their task counts, counted in one grouped query."""
        counts = self._tasks.counts_per_category()
        return [(category, counts.get(category.id, 0)) for category in self._categories.list_all()]

    def create(self, data):
        v.require_object(data)
        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = v.reject_structured(name, 'Nome inválido')
        category.description = v.reject_structured(data.get('description', ''), 'Descrição inválida')
        category.color = v.reject_structured(data.get('color', DEFAULT_CATEGORY_COLOR), 'Cor inválida')

        self._categories.add(category)
        self._categories.save('Erro ao criar categoria')
        return category

    def update(self, category_id, data):
        category = self._require(category_id)
        if not isinstance(data, dict):
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            category.name = v.reject_structured(data['name'], 'Nome inválido')
        if 'description' in data:
            category.description = v.reject_structured(data['description'], 'Descrição inválida')
        if 'color' in data:
            category.color = v.reject_structured(data['color'], 'Cor inválida')

        self._categories.save('Erro ao atualizar')
        return category

    def delete(self, category_id):
        category = self._require(category_id)
        self._categories.delete(category)
        self._categories.save('Erro ao deletar')

    def get_category(self, category_id):
        return self._require(category_id)

    def _require(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category
