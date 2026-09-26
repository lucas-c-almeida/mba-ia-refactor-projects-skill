from database import db, utcnow

# Named invariants (AP-15: these bounds used to be repeated as bare literals in
# routes/task_routes.py, utils/helpers.py and here). One definition, used everywhere.
VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
MIN_PRIORITY = 1
MAX_PRIORITY = 5
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self, include_overdue=False, user_name=None, category_name=None):
        data = {
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
        if include_overdue:
            data['overdue'] = self.is_overdue()
        if user_name is not None:
            data['user_name'] = user_name
        if category_name is not None:
            data['category_name'] = category_name
        return data

    @staticmethod
    def is_valid_status(value):
        return value in VALID_STATUSES

    @staticmethod
    def is_valid_priority(value):
        return MIN_PRIORITY <= value <= MAX_PRIORITY

    def is_overdue(self):
        """The single definition of "overdue" (AP-12): this rule used to be reimplemented,
        identically, at six other call sites across the route files. They now all call
        this method instead."""
        if not self.due_date:
            return False
        return self.due_date < utcnow() and self.status not in ('done', 'cancelled')
