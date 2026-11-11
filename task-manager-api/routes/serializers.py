"""Response shapes (the view layer). One function per representation, so every endpoint that
shows a resource the same way uses the same code (RP-12)."""
from models.task import PRIORITY_LABELS

PASSWORD_MASK = '********'


def _timestamp(value):
    return str(value)


def _optional_timestamp(value):
    return str(value) if value else None


def task(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': _timestamp(task.created_at),
        'updated_at': _timestamp(task.updated_at),
        'due_date': _optional_timestamp(task.due_date),
        'tags': task.tag_list(),
    }


def task_with_overdue(task_obj, overdue):
    data = task(task_obj)
    data['overdue'] = overdue
    return data


def task_list_item(task_obj, user_name, category_name, overdue):
    data = task_with_overdue(task_obj, overdue)
    data['user_name'] = user_name
    data['category_name'] = category_name
    return data


def user_task_item(task_obj, overdue):
    """The narrower task representation of GET /users/<id>/tasks."""
    return {
        'id': task_obj.id,
        'title': task_obj.title,
        'description': task_obj.description,
        'status': task_obj.status,
        'priority': task_obj.priority,
        'created_at': _timestamp(task_obj.created_at),
        'due_date': _optional_timestamp(task_obj.due_date),
        'overdue': overdue,
    }


def user(user_obj):
    return {
        'id': user_obj.id,
        'name': user_obj.name,
        'email': user_obj.email,
        # The field is kept for compatibility; its value is never the stored digest (RP-08).
        'password': PASSWORD_MASK,
        'role': user_obj.role,
        'active': user_obj.active,
        'created_at': _timestamp(user_obj.created_at),
    }


def user_list_item(user_obj, task_count):
    return {
        'id': user_obj.id,
        'name': user_obj.name,
        'email': user_obj.email,
        'role': user_obj.role,
        'active': user_obj.active,
        'created_at': _timestamp(user_obj.created_at),
        'task_count': task_count,
    }


def category(category_obj):
    return {
        'id': category_obj.id,
        'name': category_obj.name,
        'description': category_obj.description,
        'color': category_obj.color,
        'created_at': _timestamp(category_obj.created_at),
    }


def category_list_item(category_obj, task_count):
    data = category(category_obj)
    data['task_count'] = task_count
    return data


def summary_report(report):
    return {
        'generated_at': _timestamp(report['generated_at']),
        'overview': {
            'total_tasks': report['total_tasks'],
            'total_users': report['total_users'],
            'total_categories': report['total_categories'],
        },
        'tasks_by_status': dict(report['by_status']),
        'tasks_by_priority': {label: report['by_priority'][label] for label in PRIORITY_LABELS.values()},
        'overdue': {
            'count': len(report['overdue']),
            'tasks': [{'id': t.id, 'title': t.title, 'due_date': _timestamp(t.due_date),
                       'days_overdue': days} for t, days in report['overdue']],
        },
        'recent_activity': {
            'tasks_created_last_7_days': report['created_recently'],
            'tasks_completed_last_7_days': report['completed_recently'],
        },
        'user_productivity': [{
            'user_id': row['user'].id,
            'user_name': row['user'].name,
            'total_tasks': row['total'],
            'completed_tasks': row['done'],
            'completion_rate': row['rate'],
        } for row in report['productivity']],
    }


def user_report(report):
    user_obj = report['user']
    counts = report['by_status']
    return {
        'user': {'id': user_obj.id, 'name': user_obj.name, 'email': user_obj.email},
        'statistics': {
            'total_tasks': report['total'],
            'done': counts['done'],
            'pending': counts['pending'],
            'in_progress': counts['in_progress'],
            'cancelled': counts['cancelled'],
            'overdue': report['overdue'],
            'high_priority': report['high_priority'],
            'completion_rate': report['rate'],
        },
    }
