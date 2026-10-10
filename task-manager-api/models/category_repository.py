from database import db
from models.category import Category
from models.persistence import commit


class CategoryRepository:
    def get(self, category_id):
        return db.session.get(Category, category_id)

    def list_all(self):
        return Category.query.order_by(Category.id).all()

    def count(self):
        return Category.query.count()

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)

    def save(self, failure_message):
        commit(failure_message)
