from datetime import timedelta

from models.clock import utc_now
from models.constants import (HIGH_PRIORITY_MAX, RECENT_WINDOW_DAYS, STATUS_CANCELLED, STATUS_DONE,
                              STATUS_IN_PROGRESS, STATUS_PENDING)
from models.errors import NotFoundError


class ReportController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def summary(self):
        """Management aggregate. Datetimes are returned raw; the view formats them."""
        now = self._clock()
        by_status = self._tasks.count_by_status()
        overdue = self._tasks.overdue(now)
        since = now - timedelta(days=RECENT_WINDOW_DAYS)
        per_user = self._tasks.counts_per_user()

        user_stats = []
        for user in self._users.list_all():
            total, completed = per_user.get(user.id, (0, 0))
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': now,
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {
                'pending': by_status.get(STATUS_PENDING, 0),
                'in_progress': by_status.get(STATUS_IN_PROGRESS, 0),
                'done': by_status.get(STATUS_DONE, 0),
                'cancelled': by_status.get(STATUS_CANCELLED, 0),
            },
            'tasks_by_priority': self._tasks.count_by_priority(),
            'overdue': {
                'count': len(overdue),
                'tasks': [{'id': t.id, 'title': t.title, 'due_date': t.due_date,
                           'days_overdue': (now - t.due_date).days} for t in overdue],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(since),
                'tasks_completed_last_7_days': self._tasks.count_done_updated_since(since),
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        now = self._clock()
        tasks = self._tasks.for_user(user_id)
        total = len(tasks)
        count = lambda status: sum(1 for t in tasks if t.status == status)  # noqa: E731
        done = count(STATUS_DONE)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': count(STATUS_PENDING),
                'in_progress': count(STATUS_IN_PROGRESS),
                'cancelled': count(STATUS_CANCELLED),
                'overdue': sum(1 for t in tasks if t.is_overdue(now)),
                'high_priority': sum(1 for t in tasks
                                     if t.priority is not None and t.priority <= HIGH_PRIORITY_MAX),
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            },
        }
