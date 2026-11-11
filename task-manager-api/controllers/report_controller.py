"""Report use cases. Figures are computed in the database, not by loading tables (RP-10)."""
from datetime import timedelta

from models.errors import NotFoundError
from models.task import (HIGH_PRIORITY_MAX, PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE,
                         STATUS_IN_PROGRESS, STATUS_PENDING, completion_rate)

RECENT_ACTIVITY_DAYS = 7
USER_NOT_FOUND = 'Usuário não encontrado'


class ReportController:
    def __init__(self, tasks, users, categories, clock):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def summary(self):
        now = self._clock.now()
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        overdue = self._tasks.list_overdue(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        totals = self._tasks.totals_by_user()

        productivity = []
        for user in self._users.list_all():
            total, done = totals.get(user.id, (0, 0))
            productivity.append({'user': user, 'total': total, 'done': done,
                                 'rate': completion_rate(done, total)})

        return {
            'generated_at': now,
            'total_tasks': self._tasks.count(),
            'total_users': self._users.count(),
            'total_categories': self._categories.count(),
            'by_status': {status: by_status.get(status, 0) for status in
                          (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)},
            'by_priority': {label: by_priority.get(priority, 0)
                            for priority, label in PRIORITY_LABELS.items()},
            'overdue': [(task, (now - task.due_date).days) for task in overdue],
            'created_recently': self._tasks.count_created_since(since),
            'completed_recently': self._tasks.count_done_updated_since(since),
            'productivity': productivity,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)
        now = self._clock.now()
        tasks = self._tasks.list_for_user(user_id)
        counts = {STATUS_DONE: 0, STATUS_PENDING: 0, STATUS_IN_PROGRESS: 0, STATUS_CANCELLED: 0}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        return {
            'user': user,
            'total': len(tasks),
            'by_status': counts,
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_MAX),
            'rate': completion_rate(counts[STATUS_DONE], len(tasks)),
        }
