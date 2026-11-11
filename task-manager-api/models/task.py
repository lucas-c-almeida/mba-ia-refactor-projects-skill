from datetime import datetime

from database import db
from models.clock import utcnow

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2          # priorities 1 and 2 count as "high priority" in reports
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


def _in_list(column, values):
    return '{0} IN ({1})'.format(column, ', '.join("'{0}'".format(v) for v in values))


class Task(db.Model):
    __tablename__ = 'tasks'
    __table_args__ = (
        db.CheckConstraint(_in_list('status', VALID_STATUSES), name='ck_tasks_status'),
        db.CheckConstraint('priority BETWEEN {0} AND {1}'.format(PRIORITY_MIN, PRIORITY_MAX),
                           name='ck_tasks_priority'),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=STATUS_PENDING)
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def is_overdue(self, now):
        """The overdue rule, in one place (RP-12)."""
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    @staticmethod
    def overdue_clause(now):
        """The same rule as a query condition, for counts done in the database (RP-10)."""
        return db.and_(Task.due_date.isnot(None), Task.due_date < now,
                       Task.status.notin_(CLOSED_STATUSES))

    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []


def parse_due_date(value):
    """Parse the API's date format; ValueError when it does not match."""
    return datetime.strptime(value, DUE_DATE_FORMAT)


def join_tags(tags):
    return TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0
