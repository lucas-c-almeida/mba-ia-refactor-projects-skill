"""Reporting use cases: aggregates computed by the datastore, not by loops in Python."""
from models.category import Category
from models.task import (STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, Task,
                         completion_rate, recent_activity_start)
from models.user import User


class ReportController:
    def __init__(self, clock):
        self._clock = clock

    def summary(self):
        now = self._clock()
        since = recent_activity_start(now)
        per_user = Task.counts_per_user()
        users = []
        for user in User.list_all():
            total, done = per_user.get(user.id, (0, 0))
            users.append({'user': user, 'total': total, 'done': done,
                          'completion_rate': completion_rate(done, total)})
        return {
            'now': now,
            'total_tasks': Task.count_all(),
            'total_users': User.count_all(),
            'total_categories': Category.count_all(),
            'by_status': Task.count_by_status(),
            'by_priority': Task.count_by_priority(),
            'overdue_tasks': Task.list_overdue(now),
            'created_recently': Task.count_created_since(since),
            'done_recently': Task.count_done_since(since),
            'users': users,
        }

    def user_report(self, user_id):
        now = self._clock()
        user = User.get_or_fail(user_id)
        total = Task.count_for_user(user_id)
        by_status = Task.count_by_status(user_id=user_id)
        return {
            'user': user,
            'total': total,
            'done': by_status[STATUS_DONE],
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'cancelled': by_status[STATUS_CANCELLED],
            'overdue': Task.count_overdue_for_user(user_id, now),
            'high_priority': Task.count_high_priority_for_user(user_id),
            'completion_rate': completion_rate(by_status[STATUS_DONE], total),
        }
