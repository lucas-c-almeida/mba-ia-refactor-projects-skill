"""Boundary validation (RP-11): type and range of every value read from the request, before a
controller sees it. Domain rules (email format, password length, referenced rows existing)
stay in the controllers and models."""
from models.errors import ValidationError
from models.task import DEFAULT_PRIORITY, PRIORITY_MAX, PRIORITY_MIN, STATUS_PENDING, \
    TITLE_MAX_LENGTH, TITLE_MIN_LENGTH, VALID_STATUSES
from models.category import DEFAULT_COLOR
from models.user import ROLE_USER

INT64_MAX = 2 ** 63 - 1          # the widest integer the database driver accepts
INVALID_BODY = 'Dados inválidos'
INVALID_PRIORITY = 'Prioridade deve ser entre {0} e {1}'.format(PRIORITY_MIN, PRIORITY_MAX)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _require_object(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(INVALID_BODY)
    return data


def _optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def _reference_id(value, message):
    """An optional row id: null, or an integer the driver can bind."""
    if value is None:
        return None
    if not _is_int(value) or abs(value) > INT64_MAX:
        raise ValidationError(message)
    return value


def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if not isinstance(value, str) or value not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    if not _is_int(value) or not PRIORITY_MIN <= value <= PRIORITY_MAX:
        raise ValidationError(INVALID_PRIORITY)
    return value


def _due_date(value, message):
    if value is None or value == '':
        return None
    if not isinstance(value, str):
        raise ValidationError(message)
    return value


def _tags(value):
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, list) and all(isinstance(tag, str) for tag in value):
        return value
    raise ValidationError('Tags inválidas')


def _query_int(raw, message):
    if raw == '':
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(message)
    if abs(value) > INT64_MAX:
        raise ValidationError(message)
    return value


# --- tasks -------------------------------------------------------------------------------

def parse_task_create(data):
    data = _require_object(data)
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')
    return {
        'title': _title(data['title']),
        'description': _optional_text(data.get('description', ''), 'Descrição inválida'),
        'status': _status(data.get('status', STATUS_PENDING)),
        'priority': _priority(data.get('priority', DEFAULT_PRIORITY)),
        'user_id': _reference_id(data.get('user_id'), 'ID de usuário inválido'),
        'category_id': _reference_id(data.get('category_id'), 'ID de categoria inválido'),
        'due_date': _due_date(data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD'),
        'tags': _tags(data.get('tags')),
    }


def parse_task_update(data):
    data = _require_object(data)
    changes = {}
    if 'title' in data:
        changes['title'] = _title(data['title'])
    if 'description' in data:
        changes['description'] = _optional_text(data['description'], 'Descrição inválida')
    if 'status' in data:
        changes['status'] = _status(data['status'])
    if 'priority' in data:
        changes['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        changes['user_id'] = _reference_id(data['user_id'], 'ID de usuário inválido')
    if 'category_id' in data:
        changes['category_id'] = _reference_id(data['category_id'], 'ID de categoria inválido')
    if 'due_date' in data:
        changes['due_date'] = _due_date(data['due_date'], 'Formato de data inválido')
    if 'tags' in data:
        changes['tags'] = _tags(data['tags'])
    return changes


def parse_task_search(args):
    return {
        'text': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': _query_int(args.get('priority', ''), 'Prioridade inválida'),
        'user_id': _query_int(args.get('user_id', ''), 'ID de usuário inválido'),
    }


# --- users -------------------------------------------------------------------------------

def parse_user_create(data):
    data = _require_object(data)
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    if not isinstance(email, str):
        raise ValidationError('Email inválido')
    if not isinstance(password, str):
        raise ValidationError('Senha inválida')
    return {'name': name, 'email': email, 'password': password,
            'role': data.get('role', ROLE_USER)}


def parse_user_update(data):
    data = _require_object(data)
    changes = {}
    for field, message in (('name', 'Nome inválido'), ('email', 'Email inválido'),
                           ('password', 'Senha inválida'), ('role', 'Role inválido')):
        if field in data:
            if not isinstance(data[field], str):
                raise ValidationError(message)
            changes[field] = data[field]
    if 'active' in data:
        if not isinstance(data['active'], bool):
            raise ValidationError('Valor de active inválido')
        changes['active'] = data['active']
    return changes


def parse_login(data):
    data = _require_object(data)
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError(INVALID_BODY)
    return email, password


# --- categories --------------------------------------------------------------------------

def parse_category_create(data):
    data = _require_object(data)
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not isinstance(name, str):
        raise ValidationError('Nome inválido')
    return {
        'name': name,
        'description': _optional_text(data.get('description', ''), 'Descrição inválida'),
        'color': _optional_text(data.get('color', DEFAULT_COLOR), 'Cor inválida'),
    }


def parse_category_update(data):
    if not isinstance(data, dict):
        raise ValidationError(INVALID_BODY)
    changes = {}
    if 'name' in data:
        if not isinstance(data['name'], str):
            raise ValidationError('Nome inválido')
        changes['name'] = data['name']
    if 'description' in data:
        changes['description'] = _optional_text(data['description'], 'Descrição inválida')
    if 'color' in data:
        changes['color'] = _optional_text(data['color'], 'Cor inválida')
    return changes
