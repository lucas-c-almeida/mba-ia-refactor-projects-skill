from sqlalchemy import func, select

from models.category import Category


class CategoryRepository:
    def __init__(self, session):
        self._session = session

    def get(self, category_id):
        return self._session.get(Category, category_id)

    def all(self):
        return list(self._session.scalars(select(Category)))

    def names_by_ids(self, ids):
        """{id: name} for the given ids, in one query."""
        ids = {i for i in ids if i}
        if not ids:
            return {}
        rows = self._session.execute(select(Category.id, Category.name).where(Category.id.in_(ids)))
        return {category_id: name for category_id, name in rows}

    def add(self, category):
        self._session.add(category)

    def delete(self, category):
        self._session.delete(category)

    def count(self):
        return self._session.scalar(select(func.count()).select_from(Category))
