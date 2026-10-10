"""Response shapes (the view layer). Field names and formats are the public contract."""

MASKED_SECRET = '********'


def _text(value):
    return str(value)


def _optional_date(value):
    return str(value) if value else None


def task(t):
    return {
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'user_id': t.user_id,
        'category_id': t.category_id,
        'created_at': _text(t.created_at),
        'updated_at': _text(t.updated_at),
        'due_date': _optional_date(t.due_date),
        'tags': t.tags.split(',') if t.tags else [],
    }


def task_detail(t):
    data = task(t)
    data['overdue'] = t.is_overdue()
    return data


def task_list_item(t):
    data = task(t)
    data['overdue'] = t.is_overdue()
    data['user_name'] = t.user.name if t.user else None
    data['category_name'] = t.category.name if t.category else None
    return data


def user_task_item(t):
    return {
        'id': t.id,
        'title': t.title,
        'description': t.description,
        'status': t.status,
        'priority': t.priority,
        'created_at': _text(t.created_at),
        'due_date': _optional_date(t.due_date),
        'overdue': t.is_overdue(),
    }


def user(u):
    return {
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'password': MASKED_SECRET,
        'role': u.role,
        'active': u.active,
        'created_at': _text(u.created_at),
    }


def user_list_item(u, task_count):
    return {
        'id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'active': u.active,
        'created_at': _text(u.created_at),
        'task_count': task_count,
    }


def user_with_tasks(u, tasks):
    data = user(u)
    data['tasks'] = [task(t) for t in tasks]
    return data


def category(c):
    return {
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'color': c.color,
        'created_at': _text(c.created_at),
    }


def category_with_count(c, task_count):
    data = category(c)
    data['task_count'] = task_count
    return data


def summary_report(report):
    out = dict(report)
    out['generated_at'] = _text(report['generated_at'])
    out['overdue'] = {
        'count': report['overdue']['count'],
        'tasks': [dict(item, due_date=_text(item['due_date'])) for item in report['overdue']['tasks']],
    }
    return out
