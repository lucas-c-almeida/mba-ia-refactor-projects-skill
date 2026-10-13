from datetime import timedelta

from models.constants import (
    HIGH_PRIORITY_MAX, PRIORITY_LABELS, RECENT_ACTIVITY_DAYS, STATUS_DONE, TASK_STATUSES,
)
from models.errors import NotFoundError


def completion_rate(done, total):
    return round((done / total) * 100, 2) if total > 0 else 0


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
        overdue = self._tasks.overdue(now)
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        totals = self._tasks.totals_by_user()

        user_stats = []
        for user in self._users.list_all():
            total, completed = totals.get(user.id, (0, 0))
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
                'total_tasks': self._tasks.total(),
                'total_users': self._users.count(),
                'total_categories': self._categories.count(),
            },
            'tasks_by_status': {
                'pending': by_status.get('pending', 0),
                'in_progress': by_status.get('in_progress', 0),
                'done': by_status.get(STATUS_DONE, 0),
                'cancelled': by_status.get('cancelled', 0),
            },
            'tasks_by_priority': {
                label: by_priority.get(level, 0) for level, label in PRIORITY_LABELS.items()
            },
            'overdue': {
                'count': len(overdue),
                'tasks': [
                    {
                        'id': t.id,
                        'title': t.title,
                        'due_date': str(t.due_date),
                        'days_overdue': (now - t.due_date).days,
                    }
                    for t in overdue
                ],
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
        counts = dict.fromkeys(TASK_STATUSES, 0)
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
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counts[STATUS_DONE],
                'pending': counts['pending'],
                'in_progress': counts['in_progress'],
                'cancelled': counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': completion_rate(counts[STATUS_DONE], total),
            },
        }
