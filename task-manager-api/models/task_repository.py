"""Task persistence: every task query lives here (RP-03, RP-10)."""
from sqlalchemy import case, func
from sqlalchemy.orm import selectinload

from models.task import STATUS_DONE, Task


class TaskRepository:
    def __init__(self, db):
        self._db = db

    def _query(self):
        return self._db.session.query(Task)

    def get(self, task_id):
        return self._db.session.get(Task, task_id)

    def list_all_with_owner_and_category(self):
        # Eager-load both relations: two extra queries in total instead of two per task.
        return self._query().options(selectinload(Task.user), selectinload(Task.category)).all()

    def list_by_user(self, user_id):
        return self._query().filter_by(user_id=user_id).all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        query = self._query()
        if text:
            # The pattern is a bound parameter, never part of the SQL text.
            pattern = f'%{text}%'
            query = query.filter(self._db.or_(Task.title.like(pattern),
                                              Task.description.like(pattern)))
        if status:
            query = query.filter(Task.status == status)
        if priority is not None:
            query = query.filter(Task.priority == priority)
        if user_id is not None:
            query = query.filter(Task.user_id == user_id)
        return query.all()

    def count(self):
        return self._query().count()

    def count_by_status(self):
        rows = self._db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        return dict(rows)

    def count_by_priority(self):
        rows = self._db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
        return dict(rows)

    def _overdue_query(self, now):
        return self._query().filter(Task.is_overdue(now))

    def list_overdue(self, now):
        return self._overdue_query(now).order_by(Task.id).all()

    def count_overdue(self, now):
        return self._overdue_query(now).count()

    def count_created_since(self, since):
        return self._query().filter(Task.created_at >= since).count()

    def count_completed_since(self, since):
        return self._query().filter(Task.status == STATUS_DONE, Task.updated_at >= since).count()

    def totals_by_user(self):
        """{user_id: (total, done)} in one grouped query."""
        rows = (self._db.session.query(
                    Task.user_id,
                    func.count(Task.id),
                    func.sum(case((Task.status == STATUS_DONE, 1), else_=0)))
                .group_by(Task.user_id).all())
        return {user_id: (total, int(done or 0)) for user_id, total, done in rows}

    def count_by_category(self):
        rows = (self._db.session.query(Task.category_id, func.count(Task.id))
                .group_by(Task.category_id).all())
        return dict(rows)

    def add(self, task):
        self._db.session.add(task)

    def delete(self, task):
        self._db.session.delete(task)

    def delete_by_user(self, user_id):
        self._query().filter_by(user_id=user_id).delete(synchronize_session='fetch')
