from sqlalchemy import func, select

from models.repository import Repository
from models.user import User


class UserRepository(Repository):
    def get(self, user_id):
        return self._session.get(User, user_id)

    def list_all(self):
        return self._session.scalars(select(User)).all()

    def find_by_email(self, email):
        return self._session.scalars(select(User).where(User.email == email)).first()

    def count(self):
        return self._session.scalar(select(func.count()).select_from(User))

    def names_by_ids(self, ids):
        if not ids:
            return {}
        rows = self._session.execute(select(User.id, User.name).where(User.id.in_(ids)))
        return {user_id: name for user_id, name in rows}
