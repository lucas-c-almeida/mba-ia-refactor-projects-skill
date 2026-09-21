"""Task entity, its business rules, and its persistence."""
from datetime import datetime

from sqlalchemy import case, func, or_
from sqlalchemy.orm import joinedload

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
HIGH_PRIORITY_THRESHOLD = 2          # priorities <= this count as "high priority"
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
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
        """Past its due date and still open."""
        if not self.due_date:
            return False
        now = now or utc_now()
        return self.due_date < now and self.status not in CLOSED_STATUSES

    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []


def is_valid_status(status):
    return status in TASK_STATUSES


def is_number(value):
    # bool is accepted as before (it is an int subclass); strings, None and containers are not.
    return isinstance(value, (int, float))


def is_valid_priority(priority):
    return MIN_PRIORITY <= priority <= MAX_PRIORITY


def parse_due_date(raw):
    """Parse the due-date wire format. Raises ValueError/TypeError when malformed."""
    return datetime.strptime(raw, DUE_DATE_FORMAT)


def completion_rate(done, total):
    """Percentage of done tasks, two decimals; 0 when there are no tasks."""
    return round((done / total) * 100, 2) if total > 0 else 0


def is_valid_tags(tags):
    """Tags arrive as a list of strings or as an already separated string (or null)."""
    if isinstance(tags, list):
        return all(isinstance(tag, str) for tag in tags)
    return tags is None or isinstance(tags, str)


def serialize_tags(tags):
    return TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags


class TaskRepository:
    def __init__(self, session):
        self._session = session

    def get(self, task_id):
        return self._session.get(Task, task_id)

    def list_with_relations(self):
        return (self._session.query(Task)
                .options(joinedload(Task.user), joinedload(Task.category))
                .order_by(Task.id)
                .all())

    def list_by_user(self, user_id):
        return self._session.query(Task).filter(Task.user_id == user_id).order_by(Task.id).all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        query = self._session.query(Task)
        if text:
            # Bound parameters: the ORM hands the pattern to the driver as data.
            pattern = '%' + text + '%'
            query = query.filter(or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.order_by(Task.id).all()

    def count(self):
        return self._session.query(func.count(Task.id)).scalar()

    def count_by_status(self):
        rows = self._session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        counts = dict.fromkeys(TASK_STATUSES, 0)
        counts.update({status: n for status, n in rows if status in counts})
        return counts

    def count_by_priority(self):
        rows = self._session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        counts = dict.fromkeys(PRIORITY_LABELS, 0)
        counts.update({priority: n for priority, n in rows if priority in counts})
        return counts

    @staticmethod
    def _overdue_filter(now):
        return (Task.due_date.isnot(None),
                Task.due_date < now,
                or_(Task.status.is_(None), Task.status.notin_(CLOSED_STATUSES)))

    def count_overdue(self, now):
        return self._session.query(func.count(Task.id)).filter(*self._overdue_filter(now)).scalar()

    def list_overdue(self, now):
        return self._session.query(Task).filter(*self._overdue_filter(now)).order_by(Task.id).all()

    def count_created_since(self, since):
        return self._session.query(func.count(Task.id)).filter(Task.created_at >= since).scalar()

    def count_done_updated_since(self, since):
        return (self._session.query(func.count(Task.id))
                .filter(Task.status == STATUS_DONE, Task.updated_at >= since)
                .scalar())

    def totals_per_user(self):
        """{user_id: (total, done)} in one grouped query."""
        done_flag = case((Task.status == STATUS_DONE, 1), else_=0)
        rows = (self._session.query(Task.user_id, func.count(Task.id),
                                    func.coalesce(func.sum(done_flag), 0))
                .group_by(Task.user_id)
                .all())
        return {user_id: (int(total), int(done)) for user_id, total, done in rows}

    def count_per_category(self):
        rows = (self._session.query(Task.category_id, func.count(Task.id))
                .group_by(Task.category_id)
                .all())
        return dict(rows)

    def delete_by_user(self, user_id):
        (self._session.query(Task)
         .filter(Task.user_id == user_id)
         .delete(synchronize_session='fetch'))

    def add(self, task):
        self._session.add(task)

    def delete(self, task):
        self._session.delete(task)
