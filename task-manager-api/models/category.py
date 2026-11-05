"""Category entity and queries."""
from database import db, get_by_id
from models.clock import utc_now
from models.errors import NotFoundError

DEFAULT_COLOR = '#000000'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': str(self.created_at),
        }

    @classmethod
    def find(cls, category_id):
        return get_by_id(cls, category_id)

    @classmethod
    def get_or_404(cls, category_id):
        category = cls.find(category_id)
        if category is None:
            raise NotFoundError('Categoria não encontrada')
        return category

    @classmethod
    def all_ordered(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return db.session.query(db.func.count(cls.id)).scalar()

    @classmethod
    def names_by_id(cls, ids):
        ids = [i for i in ids if i is not None]
        if not ids:
            return {}
        return dict(db.session.query(cls.id, cls.name).filter(cls.id.in_(set(ids))).all())
