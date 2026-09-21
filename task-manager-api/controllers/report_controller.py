"""Reporting use cases: aggregate figures computed by the datastore where possible."""
from datetime import timedelta

from controllers import messages
from models.clock import utc_now
from models.errors import NotFoundError
from models.task import (HIGH_PRIORITY_THRESHOLD, PRIORITY_LABELS, STATUS_CANCELLED, STATUS_DONE,
                         STATUS_IN_PROGRESS, STATUS_PENDING, completion_rate)

RECENT_ACTIVITY_DAYS = 7


class ReportController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def summary(self):
        now = self._clock()
        by_status = self._tasks.count_by_status()
        by_priority = self._tasks.count_by_priority()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        overdue_tasks = self._tasks.list_overdue(now)
        totals = self._tasks.totals_per_user()
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
            'generated_at': str(now),
            'overview': {
                'total_tasks': self._tasks.count(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {
                'pending': by_status[STATUS_PENDING],
                'in_progress': by_status[STATUS_IN_PROGRESS],
                'done': by_status[STATUS_DONE],
                'cancelled': by_status[STATUS_CANCELLED],
            },
            'tasks_by_priority': {label: by_priority[priority]
                                  for priority, label in PRIORITY_LABELS.items()},
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [{
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date).days,
                } for task in overdue_tasks],
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(since),
                'tasks_completed_last_7_days': self._tasks.count_done_updated_since(since),
            },
            'user_productivity': productivity,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError(messages.USER_NOT_FOUND)

        tasks = self._tasks.list_by_user(user_id)
        now = self._clock()
        counts = {STATUS_DONE: 0, STATUS_PENDING: 0, STATUS_IN_PROGRESS: 0, STATUS_CANCELLED: 0}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        total = len(tasks)

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counts[STATUS_DONE],
                'pending': counts[STATUS_PENDING],
                'in_progress': counts[STATUS_IN_PROGRESS],
                'cancelled': counts[STATUS_CANCELLED],
                'overdue': sum(1 for task in tasks if task.is_overdue(now)),
                'high_priority': sum(1 for task in tasks
                                     if task.priority <= HIGH_PRIORITY_THRESHOLD),
                'completion_rate': completion_rate(counts[STATUS_DONE], total),
            },
        }
