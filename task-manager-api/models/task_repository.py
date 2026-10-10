from sqlalchemy import case, func, or_, select

from models.constants import FINAL_STATUSES, STATUS_DONE
from models.task import Task


class TaskRepository:
    """Persistence for tasks. All queries use bound parameters."""

    def __init__(self, session):
        self._session = session

    def get(self, task_id):
        return self._session.get(Task, task_id)

    def all(self):
        return list(self._session.scalars(select(Task)))

    def for_user(self, user_id):
        return list(self._session.scalars(select(Task).where(Task.user_id == user_id)))

    def add(self, task):
        self._session.add(task)

    def delete(self, task):
        self._session.delete(task)

    def search(self, text, status, priority, user_id):
        query = select(Task)
        if text:
            query = query.where(
                or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%'))
            )
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return list(self._session.scalars(query))

    def count(self):
        return self._session.scalar(select(func.count()).select_from(Task))

    def count_by_status(self, status):
        return self._session.scalar(
            select(func.count()).select_from(Task).where(Task.status == status)
        )

    def count_by_priority(self, priority):
        return self._session.scalar(
            select(func.count()).select_from(Task).where(Task.priority == priority)
        )

    def _overdue_condition(self, now):
        return (
            Task.due_date.is_not(None),
            Task.due_date < now,
            or_(Task.status.is_(None), Task.status.not_in(FINAL_STATUSES)),
        )

    def count_overdue(self, now):
        return self._session.scalar(
            select(func.count()).select_from(Task).where(*self._overdue_condition(now))
        )

    def overdue(self, now):
        query = select(Task).where(*self._overdue_condition(now)).order_by(Task.id)
        return list(self._session.scalars(query))

    def count_created_since(self, cutoff):
        return self._session.scalar(
            select(func.count()).select_from(Task).where(Task.created_at >= cutoff)
        )

    def count_done_updated_since(self, cutoff):
        return self._session.scalar(
            select(func.count()).select_from(Task).where(
                Task.status == STATUS_DONE, Task.updated_at >= cutoff
            )
        )

    def totals_by_user(self):
        """{user_id: (total tasks, done tasks)} in one grouped query."""
        done = func.sum(case((Task.status == STATUS_DONE, 1), else_=0))
        rows = self._session.execute(
            select(Task.user_id, func.count(Task.id), done)
            .where(Task.user_id.is_not(None))
            .group_by(Task.user_id)
        )
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    def totals_by_category(self):
        """{category_id: number of tasks} in one grouped query."""
        rows = self._session.execute(
            select(Task.category_id, func.count(Task.id))
            .where(Task.category_id.is_not(None))
            .group_by(Task.category_id)
        )
        return {category_id: total for category_id, total in rows}
