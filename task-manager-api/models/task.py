from database import db
from models.clock import utc_now

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
FINISHED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)
DEFAULT_STATUS = STATUS_PENDING
DEFAULT_PRIORITY = 3
PRIORITY_MIN = 1
PRIORITY_MAX = 5
HIGH_PRIORITY_MAX = 2
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
TAG_SEPARATOR = ','


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(TITLE_MAX_LENGTH), nullable=False)
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
        data = {}
        data['id'] = self.id
        data['title'] = self.title
        data['description'] = self.description
        data['status'] = self.status
        data['priority'] = self.priority
        data['user_id'] = self.user_id
        data['category_id'] = self.category_id
        data['created_at'] = str(self.created_at)
        data['updated_at'] = str(self.updated_at)
        data['due_date'] = str(self.due_date) if self.due_date else None
        data['tags'] = self.tags.split(TAG_SEPARATOR) if self.tags else []
        return data

    def is_overdue(self, now=None):
        """The one definition of "overdue": past its due date and not finished."""
        if not self.due_date:
            return False
        if self.due_date >= (now or utc_now()):
            return False
        return self.status not in FINISHED_STATUSES

    @staticmethod
    def is_number(value):
        return isinstance(value, (int, float))

    @staticmethod
    def priority_in_range(value):
        return PRIORITY_MIN <= value <= PRIORITY_MAX

    @staticmethod
    def tags_to_storage(tags):
        if isinstance(tags, list):
            return TAG_SEPARATOR.join(tags)
        return tags
