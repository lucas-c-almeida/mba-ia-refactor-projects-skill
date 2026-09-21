"""Response representations. The only place that decides what a client sees.

Every function is an explicit field list, so adding a column never leaks it by accident.
"""


def _timestamp(value):
    return str(value)


def _optional_timestamp(value):
    return str(value) if value else None


def task(entity):
    return {
        'id': entity.id,
        'title': entity.title,
        'description': entity.description,
        'status': entity.status,
        'priority': entity.priority,
        'user_id': entity.user_id,
        'category_id': entity.category_id,
        'created_at': _timestamp(entity.created_at),
        'updated_at': _timestamp(entity.updated_at),
        'due_date': _optional_timestamp(entity.due_date),
        'tags': entity.tag_list(),
    }


def task_with_overdue(entity, overdue):
    data = task(entity)
    data['overdue'] = overdue
    return data


def task_list_item(entity, overdue):
    """Row of the task listing: the task, its overdue flag and related names."""
    data = task_with_overdue(entity, overdue)
    data['user_name'] = entity.user.name if entity.user_id and entity.user else None
    data['category_name'] = (entity.category.name
                             if entity.category_id and entity.category else None)
    return data


def user_task_item(entity, overdue):
    """Row of a user's task list: a reduced task representation."""
    return {
        'id': entity.id,
        'title': entity.title,
        'description': entity.description,
        'status': entity.status,
        'priority': entity.priority,
        'created_at': _timestamp(entity.created_at),
        'due_date': _optional_timestamp(entity.due_date),
        'overdue': overdue,
    }


def user(entity):
    # NOTE: 'password' (the stored hash) is still emitted because existing clients may
    # read the field. Removing it is contract-changing and is recorded in the audit
    # report under "Proposed, Not Applied" (AP-08).
    return {
        'id': entity.id,
        'name': entity.name,
        'email': entity.email,
        'password': entity.password,
        'role': entity.role,
        'active': entity.active,
        'created_at': _timestamp(entity.created_at),
    }


def user_list_item(entity, task_count):
    return {
        'id': entity.id,
        'name': entity.name,
        'email': entity.email,
        'role': entity.role,
        'active': entity.active,
        'created_at': _timestamp(entity.created_at),
        'task_count': task_count,
    }


def category(entity):
    return {
        'id': entity.id,
        'name': entity.name,
        'description': entity.description,
        'color': entity.color,
        'created_at': _timestamp(entity.created_at),
    }


def category_list_item(entity, task_count):
    data = category(entity)
    data['task_count'] = task_count
    return data
