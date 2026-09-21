"""Category entity and its persistence."""
from database import db
from models.clock import utc_now

DEFAULT_COLOR = '#000000'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)


class CategoryRepository:
    def __init__(self, session):
        self._session = session

    def get(self, category_id):
        return self._session.get(Category, category_id)

    def list_all(self):
        return self._session.query(Category).order_by(Category.id).all()

    def count(self):
        return self._session.query(db.func.count(Category.id)).scalar()

    def add(self, category):
        self._session.add(category)

    def delete(self, category):
        self._session.delete(category)
