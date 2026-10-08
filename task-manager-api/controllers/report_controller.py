"""Report use cases. Aggregation is done by the datastore, not by loading whole tables."""
from datetime import timedelta

from models.clock import utc_now
from models.errors import NotFoundError
from models.statistics import completion_rate
from models.task import (
    HIGH_PRIORITY_MAX,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)

RECENT_ACTIVITY_DAYS = 7
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


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

        overdue_tasks = [
            {
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (now - task.due_date).days,
            }
            for task in self._tasks.list_overdue(now)
        ]

        window_start = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        per_user = self._tasks.counts_by_user()
        user_stats = []
        for user in self._users.list_all():
            total, completed = per_user.get(user.id, (0, 0))
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': completion_rate(completed, total),
            })

        return {
            'generated_at': str(now),
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
            'tasks_by_priority': {
                label: by_priority.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': overdue_tasks,
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(window_start),
                'tasks_completed_last_7_days': self._tasks.count_done_updated_since(window_start),
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self._tasks.for_user(user_id)
        now = self._clock()
        counts = {STATUS_DONE: 0, STATUS_PENDING: 0, STATUS_IN_PROGRESS: 0, STATUS_CANCELLED: 0}
        overdue = 0
        high_priority = 0
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
            if task.priority <= HIGH_PRIORITY_MAX:
                high_priority += 1
            if task.is_overdue(now):
                overdue += 1

        total = len(tasks)
        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': counts[STATUS_DONE],
                'pending': counts[STATUS_PENDING],
                'in_progress': counts[STATUS_IN_PROGRESS],
                'cancelled': counts[STATUS_CANCELLED],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': completion_rate(counts[STATUS_DONE], total),
            }
        }
