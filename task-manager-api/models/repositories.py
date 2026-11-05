"""Persistence for the domain entities. Every query of the application lives here."""
from sqlalchemy import case, func, or_, select

from database import db
from models.category import Category
from models.constants import CLOSED_STATUSES, STATUS_DONE
from models.task import Task
from models.user import User


class UnitOfWork:
    """Transaction boundary shared by the controllers."""

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()


def _all(statement):
    return db.session.execute(statement).scalars().all()


class TaskRepository:
    def get(self, task_id):
        return db.session.get(Task, task_id)

    def list_all(self):
        return _all(select(Task).order_by(Task.id))

    def for_user(self, user_id):
        return _all(select(Task).where(Task.user_id == user_id).order_by(Task.id))

    def search(self, text, status, priority, user_id):
        statement = select(Task)
        if text:
            pattern = f'%{text}%'  # bound as a parameter, never part of the statement text
            statement = statement.where(
                or_(Task.title.like(pattern), Task.description.like(pattern)))
        if status:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        if user_id is not None:
            statement = statement.where(Task.user_id == user_id)
        return _all(statement.order_by(Task.id))

    def add(self, task):
        db.session.add(task)

    def delete(self, task):
        db.session.delete(task)

    def total(self):
        return db.session.scalar(select(func.count()).select_from(Task))

    def count_by_status(self):
        rows = db.session.execute(select(Task.status, func.count()).group_by(Task.status)).all()
        return {status: count for status, count in rows}

    def count_by_priority(self):
        rows = db.session.execute(select(Task.priority, func.count()).group_by(Task.priority)).all()
        return {priority: count for priority, count in rows}

    @staticmethod
    def _overdue_condition(now):
        # Set-based form of Task.is_overdue: the two must stay in step.
        return (Task.due_date.isnot(None), Task.due_date < now,
                or_(Task.status.is_(None), Task.status.notin_(CLOSED_STATUSES)))

    def overdue(self, now):
        return _all(select(Task).where(*self._overdue_condition(now)).order_by(Task.id))

    def count_overdue(self, now):
        return db.session.scalar(
            select(func.count()).select_from(Task).where(*self._overdue_condition(now)))

    def count_created_since(self, since):
        return db.session.scalar(
            select(func.count()).select_from(Task).where(Task.created_at >= since))

    def count_done_updated_since(self, since):
        return db.session.scalar(
            select(func.count()).select_from(Task)
            .where(Task.status == STATUS_DONE, Task.updated_at >= since))

    def totals_by_user(self):
        """{user_id: (total tasks, done tasks)} for every user that has tasks."""
        done = func.sum(case((Task.status == STATUS_DONE, 1), else_=0))
        rows = db.session.execute(
            select(Task.user_id, func.count(), done)
            .where(Task.user_id.isnot(None)).group_by(Task.user_id)).all()
        return {user_id: (total, int(completed or 0)) for user_id, total, completed in rows}

    def counts_by_category(self):
        rows = db.session.execute(
            select(Task.category_id, func.count())
            .where(Task.category_id.isnot(None)).group_by(Task.category_id)).all()
        return {category_id: count for category_id, count in rows}

    def counts_by_user(self):
        return {user_id: total for user_id, (total, _) in self.totals_by_user().items()}


class UserRepository:
    def get(self, user_id):
        return db.session.get(User, user_id)

    def get_by_email(self, email):
        return db.session.execute(select(User).where(User.email == email)).scalars().first()

    def list_all(self):
        return _all(select(User).order_by(User.id))

    def names_by_id(self, user_ids):
        if not user_ids:
            return {}
        rows = db.session.execute(select(User.id, User.name).where(User.id.in_(user_ids))).all()
        return {user_id: name for user_id, name in rows}

    def count(self):
        return db.session.scalar(select(func.count()).select_from(User))

    def add(self, user):
        db.session.add(user)

    def delete(self, user):
        db.session.delete(user)


class CategoryRepository:
    def get(self, category_id):
        return db.session.get(Category, category_id)

    def list_all(self):
        return _all(select(Category).order_by(Category.id))

    def names_by_id(self, category_ids):
        if not category_ids:
            return {}
        rows = db.session.execute(
            select(Category.id, Category.name).where(Category.id.in_(category_ids))).all()
        return {category_id: name for category_id, name in rows}

    def count(self):
        return db.session.scalar(select(func.count()).select_from(Category))

    def add(self, category):
        db.session.add(category)

    def delete(self, category):
        db.session.delete(category)
