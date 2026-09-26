"""Use-case orchestration for categories (AP-05: was inline in routes/report_routes.py).

AP-20 (category deletion orphans referencing tasks, with SQLite FK enforcement never
turned on) is NOT fixed here: any of restrict/cascade/set-null changes what today's
`delete()` call observes (success vs. rejection, or a different task state) — a product
decision, filed under `## Proposed, Not Applied` in reports/audit-latest.md rather than
picked here.
"""
from sqlalchemy import func

from database import db
from middlewares.errors import BadRequestError, NotFoundError
from models.category import DEFAULT_COLOR, Category
from models.task import Task


class CategoryController:

    def list_all(self):
        # RP-10: one grouped-count query instead of one `Task.query...count()` per
        # category (AP-10 — this exact instance was missed on the first pass of this
        # refactor and caught during the Phase 3d re-audit self-review before it ran).
        counts = dict(db.session.query(Task.category_id, func.count(Task.id))
                     .group_by(Task.category_id).all())
        return [dict(c.to_dict(), task_count=counts.get(c.id, 0)) for c in Category.query.all()]

    def create(self, data):
        if not data:
            raise BadRequestError('Dados inválidos')
        name = data.get('name')
        if not name:
            raise BadRequestError('Nome é obrigatório')
        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_COLOR)
        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    def update(self, category_id, data):
        category = self._require(category_id)
        if not data:
            raise BadRequestError('Dados inválidos')
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']
        db.session.commit()
        return category.to_dict()

    def delete(self, category_id):
        category = self._require(category_id)
        db.session.delete(category)
        db.session.commit()
        return {'message': 'Categoria deletada'}

    def _require(self, category_id):
        category = Category.query.get(category_id)
        if not category:
            raise NotFoundError('Categoria não encontrada')
        return category
