"""Category persistence."""
from models.category import Category


class CategoryRepository:
    def __init__(self, db):
        self._db = db

    def get(self, category_id):
        return self._db.session.get(Category, category_id)

    def list_all(self):
        return self._db.session.query(Category).all()

    def count(self):
        return self._db.session.query(Category).count()

    def add(self, category):
        self._db.session.add(category)

    def delete(self, category):
        self._db.session.delete(category)
