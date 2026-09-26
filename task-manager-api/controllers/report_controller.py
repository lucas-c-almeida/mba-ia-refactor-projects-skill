"""Reporting use cases (AP-05: was inline in routes/report_routes.py).

AP-10 (N+1): the per-user loop that used to issue one `Task.query.filter_by(user_id=...)`
per user is replaced by two grouped aggregate queries.
"""
from datetime import timedelta

from sqlalchemy import func

from database import db, utcnow
from middlewares.errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User


class ReportController:

    def summary(self):
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        by_status = {
            status: Task.query.filter_by(status=status).count()
            for status in ('pending', 'in_progress', 'done', 'cancelled')
        }
        by_priority_counts = {p: Task.query.filter_by(priority=p).count() for p in range(1, 6)}

        overdue_list = []
        for t in Task.query.all():
            if t.is_overdue():
                overdue_list.append({
                    'id': t.id, 'title': t.title, 'due_date': str(t.due_date),
                    'days_overdue': (utcnow() - t.due_date).days,
                })

        seven_days_ago = utcnow() - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(Task.status == 'done',
                                        Task.updated_at >= seven_days_ago).count()

        # RP-10: one grouped total-per-user and one grouped completed-per-user query,
        # instead of one Task query per user (AP-10).
        totals = dict(db.session.query(Task.user_id, func.count(Task.id))
                      .group_by(Task.user_id).all())
        completed = dict(db.session.query(Task.user_id, func.count(Task.id))
                         .filter(Task.status == 'done').group_by(Task.user_id).all())
        user_stats = []
        for u in User.query.all():
            total = totals.get(u.id, 0)
            done = completed.get(u.id, 0)
            user_stats.append({
                'user_id': u.id, 'user_name': u.name, 'total_tasks': total,
                'completed_tasks': done,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': str(utcnow()),
            'overview': {'total_tasks': total_tasks, 'total_users': total_users,
                        'total_categories': total_categories},
            'tasks_by_status': by_status,
            'tasks_by_priority': {
                'critical': by_priority_counts[1], 'high': by_priority_counts[2],
                'medium': by_priority_counts[3], 'low': by_priority_counts[4],
                'minimal': by_priority_counts[5],
            },
            'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
            'recent_activity': {'tasks_created_last_7_days': recent_tasks,
                               'tasks_completed_last_7_days': recent_done},
            'user_productivity': user_stats,
        }

    def user_report(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        by_status = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            if t.status in by_status:
                by_status[t.status] += 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total, 'done': by_status['done'],
                'pending': by_status['pending'], 'in_progress': by_status['in_progress'],
                'cancelled': by_status['cancelled'], 'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((by_status['done'] / total) * 100, 2) if total > 0 else 0,
            },
        }
