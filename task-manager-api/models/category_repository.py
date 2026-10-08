from sqlalchemy import func, select

from models.category import Category
from models.repository import Repository


class CategoryRepository(Repository):
    def get(self, category_id):
        return self._session.get(Category, category_id)

    def list_all(self):
        return self._session.scalars(select(Category)).all()

    def count(self):
        return self._session.scalar(select(func.count()).select_from(Category))

    def names_by_ids(self, ids):
        if not ids:
            return {}
        rows = self._session.execute(select(Category.id, Category.name).where(Category.id.in_(ids)))
        return {category_id: name for category_id, name in rows}
