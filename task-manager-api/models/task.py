"""Task entity and its rules. No framework request/response objects here."""
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.ext.hybrid import hybrid_method

from database import db
from models.clock import utc_now

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2          # priorities 1 and 2 count as "high priority" in reports
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


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

    @property
    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []

    # The single definition of "overdue": past its due date and still open. The expression
    # form lets repositories count and filter in SQL with exactly the same rule.
    @hybrid_method
    def is_overdue(self, now):
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    @is_overdue.expression
    def is_overdue(cls, now):
        return and_(cls.due_date.isnot(None), cls.due_date < now,
                    cls.status.notin_(CLOSED_STATUSES))


def is_valid_status(status):
    return status in TASK_STATUSES


def is_number(value):
    # bool is accepted as it always was (it compares as 0/1).
    return isinstance(value, (int, float))


def is_valid_priority(priority):
    return MIN_PRIORITY <= priority <= MAX_PRIORITY


def title_length_error(title):
    """The error message for a title of the wrong length, or None."""
    if len(title) < MIN_TITLE_LENGTH:
        return 'Título muito curto'
    if len(title) > MAX_TITLE_LENGTH:
        return 'Título muito longo'
    return None


def parse_due_date(value):
    """Raises ValueError or TypeError on anything that is not a YYYY-MM-DD string."""
    return datetime.strptime(value, DUE_DATE_FORMAT)


def is_valid_tags(tags):
    """A string, or a list of strings."""
    if isinstance(tags, list):
        return all(isinstance(tag, str) for tag in tags)
    return isinstance(tags, str)


def is_valid_reference(value):
    """A related-record id as clients send it: a number or a numeric-looking string."""
    return isinstance(value, (int, str)) and not isinstance(value, bool)


def normalize_tags(tags):
    return TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0
