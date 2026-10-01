"""Category use cases. Plain values in, domain objects out."""
import logging

from controllers.common import (MSG_DELETE_FAILED, MSG_UPDATE_FAILED, optional_text, require_object,
                                required_text)
from database import commit_or_fail, db
from models.category import DEFAULT_COLOR, Category
from models.task import Task

logger = logging.getLogger(__name__)

MSG_NAME_REQUIRED = 'Nome é obrigatório'
MSG_NAME_INVALID = 'Nome inválido'
MSG_DESCRIPTION_INVALID = 'Descrição inválida'
MSG_COLOR_INVALID = 'Cor inválida'
MSG_CREATE_FAILED = 'Erro ao criar categoria'


class CategoryController:
    def list_categories(self):
        counts = Task.counts_per_category()
        return [(category, counts.get(category.id, 0)) for category in Category.list_all()]

    def create(self, data):
        data = require_object(data)
        name = required_text(data.get('name'), MSG_NAME_REQUIRED, MSG_NAME_INVALID)
        category = Category(
            name=name,
            description=optional_text(data.get('description', ''), MSG_DESCRIPTION_INVALID),
            color=optional_text(data.get('color', DEFAULT_COLOR), MSG_COLOR_INVALID),
        )
        db.session.add(category)
        commit_or_fail(MSG_CREATE_FAILED)
        return category

    def update(self, category_id, data):
        category = Category.get_or_fail(category_id)
        # An empty object is a valid no-op update, as before; a non-object body is not.
        data = require_object(data, allow_empty=True)
        changes = {}
        if 'name' in data:
            changes['name'] = required_text(data['name'], MSG_NAME_REQUIRED, MSG_NAME_INVALID)
        if 'description' in data:
            changes['description'] = optional_text(data['description'], MSG_DESCRIPTION_INVALID)
        if 'color' in data:
            changes['color'] = optional_text(data['color'], MSG_COLOR_INVALID)
        for field, value in changes.items():
            setattr(category, field, value)
        commit_or_fail(MSG_UPDATE_FAILED)
        return category

    def delete(self, category_id):
        category = Category.get_or_fail(category_id)
        # What happens to this category's tasks is unchanged (they keep the reference):
        # choosing refuse / cascade / detach is proposed, not applied (AP-20).
        db.session.delete(category)
        commit_or_fail(MSG_DELETE_FAILED)
        logger.info('Categoria deletada: %s', category_id)
