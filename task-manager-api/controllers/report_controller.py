"""Reporting use cases. Returns plain values; the response layout belongs to the view."""
from datetime import timedelta

from models.errors import USER_NOT_FOUND, NotFoundError
from models.task import (HIGH_PRIORITY_MAX, PRIORITY_LABELS, STATUS_DONE, TASK_STATUSES,
                         completion_rate)

RECENT_ACTIVITY_DAYS = 7


class ReportController:
    def __init__(self, tasks, users, categories, clock):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def summary(self):
        now = self._clock()
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        totals = self._tasks.totals_by_user()

        productivity = []
        for user in self._users.list_all():
            total, done = totals.get(user.id, (0, 0))
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': completion_rate(done, total),
            })

        return {
            'generated_at': now,
            'total_tasks': self._tasks.count(),
            'total_users': self._users.count(),
            'total_categories': self._categories.count(),
            'by_status': {status: by_status.get(status, 0) for status in TASK_STATUSES},
            'by_priority': {label: by_priority.get(level, 0)
                            for level, label in PRIORITY_LABELS.items()},
            'overdue': [(t, (now - t.due_date).days) for t in self._tasks.list_overdue(now)],
            'created_recently': self._tasks.count_created_since(since),
            'completed_recently': self._tasks.count_completed_since(since),
            'productivity': productivity,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(USER_NOT_FOUND)

        now = self._clock()
        tasks = self._tasks.list_by_user(user_id)
        counts = {status: 0 for status in TASK_STATUSES}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        done = counts[STATUS_DONE]
        return {
            'user': user,
            'total': len(tasks),
            'by_status': counts,
            'overdue': sum(1 for t in tasks if t.is_overdue(now)),
            'high_priority': sum(1 for t in tasks if t.priority <= HIGH_PRIORITY_MAX),
            'completion_rate': completion_rate(done, len(tasks)),
        }
