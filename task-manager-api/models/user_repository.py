"""User persistence."""
from models.user import User


class UserRepository:
    def __init__(self, db):
        self._db = db

    def get(self, user_id):
        return self._db.session.get(User, user_id)

    def list_all(self):
        return self._db.session.query(User).all()

    def count(self):
        return self._db.session.query(User).count()

    def find_by_email(self, email):
        return self._db.session.query(User).filter_by(email=email).first()

    def add(self, user):
        self._db.session.add(user)

    def delete(self, user):
        self._db.session.delete(user)
