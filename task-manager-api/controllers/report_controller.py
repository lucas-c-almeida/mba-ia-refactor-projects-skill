"""Reporting use cases. Every figure comes from a set-based query (RP-10)."""
from datetime import timedelta

from models.category import Category
from models.clock import utc_now
from models.task import (HIGH_PRIORITY_THRESHOLD, MAX_PRIORITY, MIN_PRIORITY, STATUS_CANCELLED,
                         STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, VALID_STATUSES, Task,
                         completion_rate)
from models.user import User

RECENT_ACTIVITY_DAYS = 7


class ReportController:
    def __init__(self, clock=utc_now):
        self._now = clock

    def summary(self):
        now = self._now()
        since = now - timedelta(days=RECENT_ACTIVITY_DAYS)
        by_status = Task.counts_by(Task.status)
        by_priority = Task.counts_by(Task.priority)
        per_user = Task.counts_per_user()
        overdue = Task.overdue(now)
        return {
            'generated_at': now,
            'totals': {'tasks': Task.count_all(), 'users': User.count_all(),
                       'categories': Category.count_all()},
            'by_status': {status: by_status.get(status, 0) for status in VALID_STATUSES},
            'by_priority': {priority: by_priority.get(priority, 0)
                            for priority in range(MIN_PRIORITY, MAX_PRIORITY + 1)},
            'overdue': [(task, (now - task.due_date).days) for task in overdue],
            'created_recently': Task.count_created_since(since),
            'done_recently': Task.count_done_since(since),
            'per_user': [self._productivity(user, *per_user.get(user.id, (0, 0)))
                         for user in User.all_ordered()],
        }

    @staticmethod
    def _productivity(user, total, done):
        return user, total, done, completion_rate(done, total)

    def user_report(self, user_id):
        user = User.get_or_404(user_id)
        now = self._now()
        tasks = Task.for_user(user_id)
        counts = {status: 0 for status in VALID_STATUSES}
        for task in tasks:
            if task.status in counts:
                counts[task.status] += 1
        total = len(tasks)
        return user, {
            'total_tasks': total,
            'done': counts[STATUS_DONE],
            'pending': counts[STATUS_PENDING],
            'in_progress': counts[STATUS_IN_PROGRESS],
            'cancelled': counts[STATUS_CANCELLED],
            'overdue': sum(1 for task in tasks if task.is_overdue(now)),
            'high_priority': sum(1 for task in tasks if task.priority <= HIGH_PRIORITY_THRESHOLD),
            'completion_rate': completion_rate(counts[STATUS_DONE], total),
        }
