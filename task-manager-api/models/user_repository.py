from sqlalchemy import func, select

from models.user import User


class UserRepository:
    def __init__(self, session):
        self._session = session

    def get(self, user_id):
        return self._session.get(User, user_id)

    def all(self):
        return list(self._session.scalars(select(User)))

    def find_by_email(self, email):
        return self._session.scalars(select(User).where(User.email == email).limit(1)).first()

    def names_by_ids(self, ids):
        """{id: name} for the given ids, in one query."""
        ids = {i for i in ids if i}
        if not ids:
            return {}
        rows = self._session.execute(select(User.id, User.name).where(User.id.in_(ids)))
        return {user_id: name for user_id, name in rows}

    def add(self, user):
        self._session.add(user)

    def delete(self, user):
        self._session.delete(user)

    def count(self):
        return self._session.scalar(select(func.count()).select_from(User))
