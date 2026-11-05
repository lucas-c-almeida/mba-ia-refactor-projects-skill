"""Category use cases."""
from database import commit, db
from models.category import DEFAULT_COLOR, Category
from models.errors import ValidationError
from models.task import Task

CATEGORY_FIELDS = ('name', 'description', 'color')


class CategoryController:
    def list_categories(self):
        """[(category, task_count)] in two queries."""
        counts = Task.counts_per_category()
        return [(category, counts.get(category.id, 0)) for category in Category.all_ordered()]

    def create_category(self, fields):
        """`fields` holds only what the request sent; absent optional fields take defaults."""
        if not fields.get('name'):
            raise ValidationError('Nome é obrigatório')
        category = Category(name=fields['name'],
                            description=fields.get('description', ''),
                            color=fields.get('color', DEFAULT_COLOR))
        db.session.add(category)
        commit('Erro ao criar categoria')
        return category

    def require_category(self, category_id):
        return Category.get_or_404(category_id)

    def update_category(self, category, fields):
        for key in CATEGORY_FIELDS:
            if key in fields:
                setattr(category, key, fields[key])
        commit('Erro ao atualizar')
        return category

    def delete_category(self, category_id):
        category = Category.get_or_404(category_id)
        db.session.delete(category)
        commit('Erro ao deletar')
