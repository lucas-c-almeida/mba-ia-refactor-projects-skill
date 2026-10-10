from database import db
from models.clock import utc_now
from models.constants import CLOSED_STATUSES, DEFAULT_PRIORITY, STATUS_PENDING


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now=None):
        """The single definition of 'overdue': past due and not closed."""
        if not self.due_date:
            return False
        if self.status in CLOSED_STATUSES:
            return False
        return self.due_date < (now or utc_now())

    @staticmethod
    def overdue_clause(now):
        """SQL form of is_overdue, for set-based queries."""
        return db.and_(
            Task.due_date.isnot(None),
            Task.due_date < now,
            db.or_(Task.status.is_(None), Task.status.notin_(CLOSED_STATUSES)),
        )
