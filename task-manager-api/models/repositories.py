"""Persistence for the domain entities. Every query of the application lives here.

Repositories stay inside the model layer (04-architecture-guidelines.md section 2): the project is
small, and one module per concern would be ceremony.
"""
from database import db
from models.category import Category
from models.task import STATUS_DONE, Task
from models.user import User


class _Repository:
    def add(self, entity):
        db.session.add(entity)

    def delete(self, entity):
        db.session.delete(entity)

    def commit(self):
        db.session.commit()

    def rollback(self):
        db.session.rollback()


class TaskRepository(_Repository):
    def get(self, task_id):
        return db.session.get(Task, task_id)

    def list_with_names(self):
        """Every task with its user's and category's names, in one query (RP-10)."""
        query = (db.select(Task, User.name, Category.name)
                 .outerjoin(User, Task.user_id == User.id)
                 .outerjoin(Category, Task.category_id == Category.id)
                 .order_by(Task.id))
        return db.session.execute(query).all()

    def list_for_user(self, user_id):
        query = db.select(Task).where(Task.user_id == user_id).order_by(Task.id)
        return db.session.execute(query).scalars().all()

    def search(self, text=None, status=None, priority=None, user_id=None):
        query = db.select(Task)
        if text:
            query = query.where(db.or_(Task.title.like('%{0}%'.format(text)),
                                       Task.description.like('%{0}%'.format(text))))
        if status:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if user_id is not None:
            query = query.where(Task.user_id == user_id)
        return db.session.execute(query.order_by(Task.id)).scalars().all()

    def count(self):
        return db.session.execute(db.select(db.func.count(Task.id))).scalar_one()

    def count_by_status(self):
        query = db.select(Task.status, db.func.count(Task.id)).group_by(Task.status)
        return dict(db.session.execute(query).all())

    def count_by_priority(self):
        query = db.select(Task.priority, db.func.count(Task.id)).group_by(Task.priority)
        return dict(db.session.execute(query).all())

    def count_overdue(self, now):
        query = db.select(db.func.count(Task.id)).where(Task.overdue_clause(now))
        return db.session.execute(query).scalar_one()

    def list_overdue(self, now):
        query = db.select(Task).where(Task.overdue_clause(now)).order_by(Task.id)
        return db.session.execute(query).scalars().all()

    def count_created_since(self, moment):
        query = db.select(db.func.count(Task.id)).where(Task.created_at >= moment)
        return db.session.execute(query).scalar_one()

    def count_done_updated_since(self, moment):
        query = db.select(db.func.count(Task.id)).where(Task.status == STATUS_DONE,
                                                        Task.updated_at >= moment)
        return db.session.execute(query).scalar_one()

    def totals_by_user(self):
        """{user_id: (total tasks, done tasks)} in one grouped query (RP-10)."""
        done = db.func.sum(db.case((Task.status == STATUS_DONE, 1), else_=0))
        query = (db.select(Task.user_id, db.func.count(Task.id), done)
                 .where(Task.user_id.isnot(None)).group_by(Task.user_id))
        return {user_id: (total, int(done_count or 0))
                for user_id, total, done_count in db.session.execute(query).all()}

    def count_by_user(self):
        query = (db.select(Task.user_id, db.func.count(Task.id))
                 .where(Task.user_id.isnot(None)).group_by(Task.user_id))
        return dict(db.session.execute(query).all())

    def count_by_category(self):
        query = (db.select(Task.category_id, db.func.count(Task.id))
                 .where(Task.category_id.isnot(None)).group_by(Task.category_id))
        return dict(db.session.execute(query).all())


class UserRepository(_Repository):
    def get(self, user_id):
        return db.session.get(User, user_id)

    def list_all(self):
        return db.session.execute(db.select(User).order_by(User.id)).scalars().all()

    def find_by_email(self, email):
        query = db.select(User).where(User.email == email).limit(1)
        return db.session.execute(query).scalars().first()

    def count(self):
        return db.session.execute(db.select(db.func.count(User.id))).scalar_one()


class CategoryRepository(_Repository):
    def get(self, category_id):
        return db.session.get(Category, category_id)

    def list_all(self):
        return db.session.execute(db.select(Category).order_by(Category.id)).scalars().all()

    def count(self):
        return db.session.execute(db.select(db.func.count(Category.id))).scalar_one()
