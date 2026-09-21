"""Response shapes (the View layer). One serializer per shape the API already returns."""


def _date(value):
    return str(value) if value else None


def task_to_dict(task):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'user_id': task.user_id,
        'category_id': task.category_id,
        'created_at': str(task.created_at),
        'updated_at': str(task.updated_at),
        'due_date': _date(task.due_date),
        'tags': task.tag_list,
    }


def task_detail(task, overdue):
    data = task_to_dict(task)
    data['overdue'] = overdue
    return data


def task_list_item(task, overdue):
    data = task_detail(task, overdue)
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def user_task_item(task, overdue):
    return {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'created_at': str(task.created_at),
        'due_date': _date(task.due_date),
        'overdue': overdue,
    }


def user_to_dict(user):
    # NOTE: 'password' (the stored hash) is still returned because removing it changes the
    # response contract; its removal is recorded under PROPOSED, NOT APPLIED (AP-08).
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'password': user.password,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
    }


def user_list_item(user, task_count):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'active': user.active,
        'created_at': str(user.created_at),
        'task_count': task_count,
    }


def category_to_dict(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'color': category.color,
        'created_at': str(category.created_at),
    }


def category_list_item(category, task_count):
    data = category_to_dict(category)
    data['task_count'] = task_count
    return data


def summary_report(summary):
    return {
        'generated_at': str(summary['generated_at']),
        'overview': {
            'total_tasks': summary['total_tasks'],
            'total_users': summary['total_users'],
            'total_categories': summary['total_categories'],
        },
        'tasks_by_status': summary['by_status'],
        'tasks_by_priority': summary['by_priority'],
        'overdue': {
            'count': len(summary['overdue']),
            'tasks': [{'id': t.id, 'title': t.title, 'due_date': str(t.due_date),
                       'days_overdue': days} for t, days in summary['overdue']],
        },
        'recent_activity': {
            'tasks_created_last_7_days': summary['created_recently'],
            'tasks_completed_last_7_days': summary['completed_recently'],
        },
        'user_productivity': summary['productivity'],
    }


def user_report(report):
    user = report['user']
    statistics = {'total_tasks': report['total']}
    statistics.update(report['by_status'])
    statistics.update({
        'overdue': report['overdue'],
        'high_priority': report['high_priority'],
        'completion_rate': report['completion_rate'],
    })
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': statistics,
    }
