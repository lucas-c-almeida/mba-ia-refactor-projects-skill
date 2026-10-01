"""Response shapes. The View layer: every body the API returns is built here, once (AP-12)."""
from models.task import (STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING)
from models.user import MASKED_SECRET

# Report labels for the numeric priorities, as the summary report has always named them.
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def _text(value):
    return str(value)


def _optional_text(value):
    return str(value) if value else None


def task_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': _text(task.created_at),
        'updated_at': _text(task.updated_at),
        'due_date': _optional_text(task.due_date),
        'tags': task.tag_list(),
    }


def task_detail(task, now):
    data = task_dict(task)
    data['overdue'] = task.is_overdue(now)
    return data


def task_list_item(task, now):
    data = task_detail(task, now)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def user_task_item(task, now):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': _text(task.created_at),
        'due_date': _optional_text(task.due_date),
        'overdue': task.is_overdue(now),
    }


def user_dict(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'password': MASKED_SECRET,
        'role': user.role,
        'active': user.active,
        'created_at': _text(user.created_at),
    }


def user_list_item(user, task_count):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': _text(user.created_at),
        'task_count': task_count,
    }


def category_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': _text(category.created_at),
    }


def task_stats(stats):
    by_status = stats['by_status']
    return {
        'total': stats['total'],
        'pending': by_status[STATUS_PENDING],
        'in_progress': by_status[STATUS_IN_PROGRESS],
        'done': by_status[STATUS_DONE],
        'cancelled': by_status[STATUS_CANCELLED],
        'overdue': stats['overdue'],
        'completion_rate': stats['completion_rate'],
    }


def summary_report(summary):
    now = summary['now']
    by_status = summary['by_status']
    overdue = [{
        'id': task.id,
        'title': task.title,
        'due_date': _text(task.due_date),
        'days_overdue': (now - task.due_date).days,
    } for task in summary['overdue_tasks']]
    return {
        'generated_at': _text(now),
        'overview': {
            'total_tasks': summary['total_tasks'],
            'total_users': summary['total_users'],
            'total_categories': summary['total_categories'],
        },
        'tasks_by_status': {
            'pending': by_status[STATUS_PENDING],
            'in_progress': by_status[STATUS_IN_PROGRESS],
            'done': by_status[STATUS_DONE],
            'cancelled': by_status[STATUS_CANCELLED],
        },
        'tasks_by_priority': {label: summary['by_priority'][priority]
                              for priority, label in PRIORITY_LABELS.items()},
        'overdue': {
            'count': len(overdue),
            'tasks': overdue,
        },
        'recent_activity': {
            'tasks_created_last_7_days': summary['created_recently'],
            'tasks_completed_last_7_days': summary['done_recently'],
        },
        'user_productivity': [{
            'user_id': row['user'].id,
            'user_name': row['user'].name,
            'total_tasks': row['total'],
            'completed_tasks': row['done'],
            'completion_rate': row['completion_rate'],
        } for row in summary['users']],
    }


def user_report(report):
    user = report['user']
    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': report['total'],
            'done': report['done'],
            'pending': report['pending'],
            'in_progress': report['in_progress'],
            'cancelled': report['cancelled'],
            'overdue': report['overdue'],
            'high_priority': report['high_priority'],
            'completion_rate': report['completion_rate'],
        },
    }
