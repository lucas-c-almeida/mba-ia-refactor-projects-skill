from database import db
from models.clock import utc_now
from models.constants import (
    CLOSED_STATUSES, DEFAULT_PRIORITY, DEFAULT_STATUS, MAX_PRIORITY, MIN_PRIORITY, TASK_STATUSES,
)


def _sql_list(values):
    return ', '.join("'%s'" % v for v in values)


class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = (
        db.CheckConstraint('status IN (%s)' % _sql_list(TASK_STATUSES), name='ck_tasks_status'),
        db.CheckConstraint(
            'priority BETWEEN %d AND %d' % (MIN_PRIORITY, MAX_PRIORITY), name='ck_tasks_priority'),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def is_overdue(self, now):
        """A task is overdue when its due date has passed and it is not closed."""
        if not self.due_date:
            return False
        return self.due_date < now and self.status not in CLOSED_STATUSES
