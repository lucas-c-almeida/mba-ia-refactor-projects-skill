"""Response shapes (the View). Each function renders one representation, in one place (RP-12)."""
from models.task import PRIORITY_LABELS


def task(task_obj, overdue=None):
    data = task_obj.to_dict()
    if overdue is not None:
        data['overdue'] = overdue
    return data


def task_listing(task_obj, overdue, user_name, category_name):
    data = task(task_obj, overdue)
    data['user_name'] = user_name
    data['category_name'] = category_name
    return data


def user_task_item(task_obj, overdue):
    """The per-user task list carries a narrower field set than the full task."""
    return {
        'id': task_obj.id,
        'title': task_obj.title,
        'description': task_obj.description,
        'status': task_obj.status,
        'priority': task_obj.priority,
        'created_at': str(task_obj.created_at),
        'due_date': str(task_obj.due_date) if task_obj.due_date else None,
        'overdue': overdue,
    }


def user_listing(user, task_count):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
        'task_count': task_count,
    }


def user_with_tasks(user, tasks):
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in tasks]
    return data


def category_with_count(category, task_count):
    data = category.to_dict()
    data['task_count'] = task_count
    return data


def summary_report(figures):
    return {
        'generated_at': str(figures['generated_at']),
        'overview': {
            'total_tasks': figures['totals']['tasks'],
            'total_users': figures['totals']['users'],
            'total_categories': figures['totals']['categories'],
        },
        'tasks_by_status': dict(figures['by_status']),
        'tasks_by_priority': {PRIORITY_LABELS[priority]: count
                              for priority, count in figures['by_priority'].items()},
        'overdue': {
            'count': len(figures['overdue']),
            'tasks': [{'id': t.id, 'title': t.title, 'due_date': str(t.due_date),
                       'days_overdue': days} for t, days in figures['overdue']],
        },
        'recent_activity': {
            'tasks_created_last_7_days': figures['created_recently'],
            'tasks_completed_last_7_days': figures['done_recently'],
        },
        'user_productivity': [{
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': done,
            'completion_rate': rate,
        } for user, total, done, rate in figures['per_user']],
    }


def user_report(user, statistics):
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': dict(statistics),
    }
