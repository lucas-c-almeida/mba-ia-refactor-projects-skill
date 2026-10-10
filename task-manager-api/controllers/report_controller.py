"""Report use cases: aggregates computed in the datastore, shaped for the delivery layer."""
from datetime import timedelta

from models.clock import utc_now
from models.constants import (
    HIGH_PRIORITY_MAX,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
)
from models.errors import NotFoundError
from models.statistics import completion_rate


class ReportController:
    def __init__(self, tasks, users, categories, clock=utc_now):
        self._tasks = tasks
        self._users = users
        self._categories = categories
        self._clock = clock

    def summary(self):
        now = self._clock()
        recent_cutoff = now - timedelta(days=RECENT_ACTIVITY_DAYS)

        overdue_tasks = self._tasks.overdue(now)
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (now - t.due_date).days,
            }
            for t in overdue_tasks
        ]

        totals = self._tasks.totals_by_user()
        user_stats = []
        for u in self._users.all():
            total, completed = totals.get(u.id, (0, 0))
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
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
                'pending': self._tasks.count_by_status(STATUS_PENDING),
                'in_progress': self._tasks.count_by_status(STATUS_IN_PROGRESS),
                'done': self._tasks.count_by_status(STATUS_DONE),
                'cancelled': self._tasks.count_by_status(STATUS_CANCELLED),
            },
            'tasks_by_priority': {
                label: self._tasks.count_by_priority(priority)
                for priority, label in PRIORITY_LABELS
            },
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': self._tasks.count_created_since(recent_cutoff),
                'tasks_completed_last_7_days': self._tasks.count_done_updated_since(recent_cutoff),
            },
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        now = self._clock()
        tasks = self._tasks.for_user(user_id)
        counts = {STATUS_DONE: 0, STATUS_PENDING: 0, STATUS_IN_PROGRESS: 0, STATUS_CANCELLED: 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            if t.status in counts:
                counts[t.status] += 1
            if t.priority <= HIGH_PRIORITY_MAX:
                high_priority += 1
            if t.is_overdue(now):
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
            },
        }
