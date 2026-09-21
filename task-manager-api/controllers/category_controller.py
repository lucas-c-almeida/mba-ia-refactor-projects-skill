"""Category use cases. Plain values in, domain objects out; no HTTP here."""
from controllers import messages
from controllers.transaction import commit
from controllers.validation import reject_container, require_object, require_present_scalar
from models.category import DEFAULT_COLOR, Category
from models.errors import NotFoundError, ValidationError

MSG_FIELD_INVALID = 'Valor inválido para {field}'
_NULLABLE_FIELDS = ('description', 'color')


class CategoryController:
    def __init__(self, session, categories, tasks):
        self._session = session
        self._categories = categories
        self._tasks = tasks

    def list_categories(self):
        """Every category with its task count (one grouped query)."""
        counts = self._tasks.count_per_category()
        return [(category, counts.get(category.id, 0)) for category in self._categories.list_all()]

    def create_category(self, data):
        require_object(data)
        name = data.get('name')
        if not name:
            raise ValidationError(messages.NAME_REQUIRED)

        category = Category()
        category.name = reject_container(name, _invalid('name'))
        category.description = reject_container(data.get('description', ''), _invalid('description'))
        category.color = reject_container(data.get('color', DEFAULT_COLOR), _invalid('color'))

        self._categories.add(category)
        commit(self._session, 'Erro ao criar categoria')
        return category

    def update_category(self, category_id, data):
        category = self._require(category_id)
        if data is None:
            raise ValidationError(messages.INVALID_DATA)
        changes = {}
        if 'name' in data:
            changes['name'] = require_present_scalar(data['name'], _invalid('name'))
        for field in _NULLABLE_FIELDS:
            if field in data:
                changes[field] = reject_container(data[field], _invalid(field))
        for field, value in changes.items():
            setattr(category, field, value)
        commit(self._session, messages.UPDATE_FAILED)
        return category

    def delete_category(self, category_id):
        category = self._require(category_id)
        self._categories.delete(category)
        commit(self._session, messages.DELETE_FAILED)

    def _require(self, category_id):
        category = self._categories.get(category_id)
        if not category:
            raise NotFoundError(messages.CATEGORY_NOT_FOUND)
        return category


def _invalid(field):
    return MSG_FIELD_INVALID.format(field=field)
