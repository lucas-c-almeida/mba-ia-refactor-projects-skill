from sqlalchemy import case, delete, func, or_, select

from models.repository import Repository
from models.task import FINISHED_STATUSES, STATUS_DONE, Task


def _overdue_conditions(now):
    return (
        Task.due_date.is_not(None),
        Task.due_date < now,
        or_(Task.status.is_(None), Task.status.notin_(FINISHED_STATUSES)),
    )


class TaskRepository(Repository):
    def get(self, task_id):
        return self._session.get(Task, task_id)

    def list_all(self):
        return self._session.scalars(select(Task)).all()

    def for_user(self, user_id):
        return self._session.scalars(select(Task).where(Task.user_id == user_id)).all()

    def delete_for_user(self, user_id):
        self._session.execute(delete(Task).where(Task.user_id == user_id))

    def search(self, text='', status='', priority=None, user_id=None):
        query = select(Task)
        if text:
            query = query.where(or_(Task.title.like(f'%{text}%'), Task.description.like(f'%{text}%')))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return self._session.scalars(query).all()

    def count(self):
        return self._session.scalar(select(func.count()).select_from(Task))

    def count_by_status(self):
        rows = self._session.execute(select(Task.status, func.count()).group_by(Task.status))
        return {status: total for status, total in rows}

    def count_by_priority(self):
        rows = self._session.execute(select(Task.priority, func.count()).group_by(Task.priority))
        return {priority: total for priority, total in rows}

    def count_overdue(self, now):
        query = select(func.count()).select_from(Task).where(*_overdue_conditions(now))
        return self._session.scalar(query)

    def list_overdue(self, now):
        return self._session.scalars(select(Task).where(*_overdue_conditions(now)).order_by(Task.id)).all()

    def count_created_since(self, moment):
        return self._session.scalar(select(func.count()).select_from(Task).where(Task.created_at >= moment))

    def count_done_updated_since(self, moment):
        query = select(func.count()).select_from(Task).where(Task.status == STATUS_DONE, Task.updated_at >= moment)
        return self._session.scalar(query)

    def counts_by_user(self):
        """user_id -> (total tasks, done tasks), one query for every user."""
        done = func.sum(case((Task.status == STATUS_DONE, 1), else_=0))
        rows = self._session.execute(
            select(Task.user_id, func.count(), done).where(Task.user_id.is_not(None)).group_by(Task.user_id)
        )
        return {user_id: (total, int(finished or 0)) for user_id, total, finished in rows}

    def counts_by_category(self):
        rows = self._session.execute(
            select(Task.category_id, func.count()).where(Task.category_id.is_not(None)).group_by(Task.category_id)
        )
        return {category_id: total for category_id, total in rows}
