"""Category entity: columns and persistence queries."""
from sqlalchemy import func

from database import db
from models.clock import utcnow
from models.errors import NotFoundError

DEFAULT_COLOR = '#000000'

MSG_NOT_FOUND = 'Categoria não encontrada'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utcnow)

    @staticmethod
    def find(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def get_or_fail(category_id):
        category = Category.find(category_id)
        if not category:
            raise NotFoundError(MSG_NOT_FOUND)
        return category

    @staticmethod
    def list_all():
        return Category.query.order_by(Category.id).all()

    @staticmethod
    def count_all():
        return db.session.query(func.count(Category.id)).scalar()
