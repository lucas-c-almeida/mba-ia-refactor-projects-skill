from database import db
from models.persistence import commit
from models.task import Task
from models.user import User


class UserRepository:
    def get(self, user_id):
        return db.session.get(User, user_id)

    def list_all(self):
        return User.query.order_by(User.id).all()

    def find_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def count(self):
        return User.query.count()

    def task_counts(self):
        """{user_id: number of tasks}, in one grouped query."""
        rows = (db.session.query(Task.user_id, db.func.count(Task.id))
                .filter(Task.user_id.isnot(None)).group_by(Task.user_id).all())
        return {user_id: n for user_id, n in rows}

    def add(self, user):
        db.session.add(user)

    def delete_with_tasks(self, user, tasks):
        for task in tasks:
            db.session.delete(task)
        db.session.delete(user)

    def save(self, failure_message):
        commit(failure_message)
