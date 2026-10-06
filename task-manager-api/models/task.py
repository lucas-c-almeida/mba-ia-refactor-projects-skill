"""Task entity: columns, domain rules and persistence queries."""
from datetime import datetime, timedelta
from numbers import Number

from sqlalchemy import case, func
from sqlalchemy.orm import selectinload

from database import db
from models.clock import utcnow
from models.errors import NotFoundError, ValidationError

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2            # priorities 1 and 2 count as "high priority" in reports

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

DUE_DATE_FORMAT = '%Y-%m-%d'
TAG_SEPARATOR = ','
RECENT_ACTIVITY_DAYS = 7

MSG_NOT_FOUND = 'Task não encontrada'
MSG_TITLE_REQUIRED = 'Título é obrigatório'
MSG_TITLE_INVALID = 'Título inválido'
MSG_TITLE_TOO_SHORT = 'Título muito curto'
MSG_TITLE_TOO_LONG = 'Título muito longo'
MSG_DESCRIPTION_INVALID = 'Descrição inválida'
MSG_STATUS_INVALID = 'Status inválido'
MSG_PRIORITY_INVALID = 'Prioridade deve ser entre 1 e 5'
MSG_TAGS_INVALID = 'Tags inválidas'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(MAX_TITLE_LENGTH), nullable=False)
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

    # --- domain rules -------------------------------------------------------------------

    def is_overdue(self, now):
        """The one definition of "overdue": past its due date and not closed."""
        return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

    def tag_list(self):
        return self.tags.split(TAG_SEPARATOR) if self.tags else []

    # --- persistence --------------------------------------------------------------------

    @staticmethod
    def find(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def get_or_fail(task_id):
        task = Task.find(task_id)
        if not task:
            raise NotFoundError(MSG_NOT_FOUND)
        return task

    @staticmethod
    def list_with_relations():
        """Every task with its user and category loaded in two extra queries, not 2 per task."""
        return (Task.query
                .options(selectinload(Task.user), selectinload(Task.category))
                .order_by(Task.id)
                .all())

    @staticmethod
    def list_for_user(user_id):
        return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()

    @staticmethod
    def search(text=None, status=None, priority=None, user_id=None):
        query = Task.query
        if text:
            query = query.filter(db.or_(Task.title.like(f'%{text}%'),
                                        Task.description.like(f'%{text}%')))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.order_by(Task.id).all()

    @staticmethod
    def overdue_filter(now):
        return db.and_(Task.due_date.isnot(None), Task.due_date < now,
                       Task.status.notin_(CLOSED_STATUSES))

    @staticmethod
    def count_all():
        return db.session.query(func.count(Task.id)).scalar()

    @staticmethod
    def count_by_status(user_id=None):
        query = db.session.query(Task.status, func.count(Task.id))
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        counts = dict(query.group_by(Task.status).all())
        return {status: counts.get(status, 0) for status in TASK_STATUSES}

    @staticmethod
    def count_for_user(user_id):
        return db.session.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar()

    @staticmethod
    def count_high_priority_for_user(user_id):
        return (db.session.query(func.count(Task.id))
                .filter(Task.user_id == user_id, Task.priority <= HIGH_PRIORITY_MAX).scalar())

    @staticmethod
    def count_overdue_for_user(user_id, now):
        return (db.session.query(func.count(Task.id))
                .filter(Task.user_id == user_id, Task.overdue_filter(now)).scalar())

    @staticmethod
    def count_by_priority():
        rows = db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        counts = dict(rows)
        return {p: counts.get(p, 0) for p in range(MIN_PRIORITY, MAX_PRIORITY + 1)}

    @staticmethod
    def count_overdue(now):
        return db.session.query(func.count(Task.id)).filter(Task.overdue_filter(now)).scalar()

    @staticmethod
    def list_overdue(now):
        return Task.query.filter(Task.overdue_filter(now)).order_by(Task.id).all()

    @staticmethod
    def count_created_since(moment):
        return db.session.query(func.count(Task.id)).filter(Task.created_at >= moment).scalar()

    @staticmethod
    def count_done_since(moment):
        return (db.session.query(func.count(Task.id))
                .filter(Task.status == STATUS_DONE, Task.updated_at >= moment).scalar())

    @staticmethod
    def counts_per_user():
        """{user_id: (total, done)} in one grouped query."""
        rows = (db.session.query(Task.user_id, func.count(Task.id),
                                 func.sum(case((Task.status == STATUS_DONE, 1), else_=0)))
                .group_by(Task.user_id).all())
        return {user_id: (total, int(done or 0)) for user_id, total, done in rows}

    @staticmethod
    def counts_per_category():
        rows = db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
        return dict(rows)

    @staticmethod
    def delete_for_user(user_id):
        for task in Task.query.filter_by(user_id=user_id).all():
            db.session.delete(task)


def recent_activity_start(now):
    return now - timedelta(days=RECENT_ACTIVITY_DAYS)


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


# --- input rules shared by create and update (AP-11, AP-12) -------------------------------

def validate_title(title):
    if not isinstance(title, str):
        raise ValidationError(MSG_TITLE_INVALID)
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_TOO_SHORT)
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError(MSG_TITLE_TOO_LONG)
    return title


def validate_description(description):
    if description is not None and not isinstance(description, str):
        raise ValidationError(MSG_DESCRIPTION_INVALID)
    return description


def validate_status(status):
    if status not in TASK_STATUSES:
        raise ValidationError(MSG_STATUS_INVALID)
    return status


def validate_priority(priority):
    # bool is accepted as before (it is a number to the comparison the API always used).
    if not isinstance(priority, Number) or priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError(MSG_PRIORITY_INVALID)
    return priority


def parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(error_message)


def normalize_tags(tags):
    """Tags arrive as a list of strings or as one comma-separated string (or null)."""
    if isinstance(tags, list):
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError(MSG_TAGS_INVALID)
        return TAG_SEPARATOR.join(tags)
    if tags is not None and not isinstance(tags, str):
        raise ValidationError(MSG_TAGS_INVALID)
    return tags
