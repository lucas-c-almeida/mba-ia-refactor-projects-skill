from sqlalchemy.orm import joinedload

from database import db
from models.constants import PRIORITY_LABELS, STATUS_DONE
from models.persistence import commit
from models.task import Task


class TaskRepository:
    def get(self, task_id):
        return db.session.get(Task, task_id)

    def list_with_relations(self):
        """All tasks with their user and category loaded in the same query, in id order."""
        return (Task.query
                .options(joinedload(Task.user), joinedload(Task.category))
                .order_by(Task.id)
                .all())

    def for_user(self, user_id):
        return Task.query.filter_by(user_id=user_id).order_by(Task.id).all()

    def search(self, text, status, priority, user_id):
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

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def save(self, failure_message):
        commit(failure_message)

    # --- aggregates -------------------------------------------------------------------------

    def count(self):
        return Task.query.count()

    def count_by_status(self):
        rows = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
        return {status: n for status, n in rows}

    def count_by_priority(self):
        rows = db.session.query(Task.priority, db.func.count(Task.id)).group_by(Task.priority).all()
        counts = {priority: n for priority, n in rows}
        return {label: counts.get(value, 0) for value, label in PRIORITY_LABELS}

    def count_overdue(self, now):
        return Task.query.filter(Task.overdue_clause(now)).count()

    def overdue(self, now):
        return Task.query.filter(Task.overdue_clause(now)).order_by(Task.id).all()

    def count_created_since(self, since):
        return Task.query.filter(Task.created_at >= since).count()

    def count_done_updated_since(self, since):
        return Task.query.filter(Task.status == STATUS_DONE, Task.updated_at >= since).count()

    def counts_per_user(self):
        """{user_id: (total, completed)} computed in the datastore."""
        done = db.func.sum(db.case((Task.status == STATUS_DONE, 1), else_=0))
        rows = (db.session.query(Task.user_id, db.func.count(Task.id), done)
                .filter(Task.user_id.isnot(None)).group_by(Task.user_id).all())
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    def counts_per_category(self):
        rows = (db.session.query(Task.category_id, db.func.count(Task.id))
                .filter(Task.category_id.isnot(None)).group_by(Task.category_id).all())
        return {category_id: n for category_id, n in rows}
