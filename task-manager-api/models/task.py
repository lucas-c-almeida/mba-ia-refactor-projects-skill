"""Task entity, its rules and its queries."""
from datetime import datetime

from sqlalchemy import func

from database import db, get_by_id
from models.clock import utc_now
from models.errors import NotFoundError, ValidationError

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)   # a closed task is never overdue
DEFAULT_STATUS = STATUS_PENDING

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_THRESHOLD = 2   # priorities 1 and 2 count as "high priority" in reports
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200

DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','

PERCENT = 100
RATE_DECIMALS = 2


def completion_rate(done, total):
    """Share of done tasks, in percent with two decimals; 0 when there are no tasks."""
    return round((done / total) * PERCENT, RATE_DECIMALS) if total > 0 else 0


class Task(db.Model):
    __tablename__ = 'tasks'

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
            'tags': self.tags.split(TAG_SEPARATOR) if self.tags else [],
        }

    def is_overdue(self, now):
        """Past its due date and still open."""
        return bool(self.due_date and self.due_date < now and self.status not in CLOSED_STATUSES)

    # --- rules -----------------------------------------------------------------------------

    @staticmethod
    def check_title(title):
        if len(title) < TITLE_MIN_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > TITLE_MAX_LENGTH:
            raise ValidationError('Título muito longo')

    @staticmethod
    def check_status(status):
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')

    @staticmethod
    def check_priority(priority):
        if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')

    @staticmethod
    def parse_due_date(text, error_message):
        try:
            return datetime.strptime(text, DUE_DATE_FORMAT)
        except ValueError:
            raise ValidationError(error_message) from None

    @staticmethod
    def join_tags(tags):
        return TAG_SEPARATOR.join(tags) if isinstance(tags, list) else tags

    # --- queries ---------------------------------------------------------------------------

    @staticmethod
    def overdue_condition(now):
        return db.and_(Task.due_date.isnot(None), Task.due_date < now,
                       Task.status.notin_(CLOSED_STATUSES))

    @classmethod
    def find(cls, task_id):
        return get_by_id(cls, task_id)

    @classmethod
    def get_or_404(cls, task_id):
        task = cls.find(task_id)
        if task is None:
            raise NotFoundError('Task não encontrada')
        return task

    @classmethod
    def all_ordered(cls):
        return cls.query.order_by(cls.id).all()

    @classmethod
    def for_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).order_by(cls.id).all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        query = cls.query
        if text:
            # The pattern is a bound parameter; the driver never sees it as SQL.
            query = query.filter(db.or_(cls.title.like(f'%{text}%'),
                                        cls.description.like(f'%{text}%')))
        if status:
            query = query.filter(cls.status == status)
        if priority is not None:
            query = query.filter(cls.priority == priority)
        if user_id is not None:
            query = query.filter(cls.user_id == user_id)
        return query.order_by(cls.id).all()

    @classmethod
    def count_all(cls):
        return db.session.query(func.count(cls.id)).scalar()

    @classmethod
    def counts_by(cls, column):
        """{value: count} for one column, in a single grouped query."""
        rows = db.session.query(column, func.count(cls.id)).group_by(column).all()
        return {value: count for value, count in rows}

    @classmethod
    def count_overdue(cls, now):
        return db.session.query(func.count(cls.id)).filter(cls.overdue_condition(now)).scalar()

    @classmethod
    def overdue(cls, now):
        return cls.query.filter(cls.overdue_condition(now)).order_by(cls.id).all()

    @classmethod
    def count_created_since(cls, since):
        return db.session.query(func.count(cls.id)).filter(cls.created_at >= since).scalar()

    @classmethod
    def count_done_since(cls, since):
        return db.session.query(func.count(cls.id)).filter(
            cls.status == STATUS_DONE, cls.updated_at >= since).scalar()

    @classmethod
    def counts_per_user(cls):
        """{user_id: (total, done)} for every user that has tasks, in one query."""
        done = func.sum(db.case((cls.status == STATUS_DONE, 1), else_=0))
        rows = db.session.query(cls.user_id, func.count(cls.id), done).group_by(cls.user_id).all()
        return {user_id: (total, int(done_count or 0)) for user_id, total, done_count in rows}

    @classmethod
    def counts_per_category(cls):
        rows = db.session.query(cls.category_id, func.count(cls.id)).group_by(cls.category_id).all()
        return dict(rows)
