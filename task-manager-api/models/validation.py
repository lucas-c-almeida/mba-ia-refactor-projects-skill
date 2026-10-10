"""Pure validation rules: no I/O, no framework. Each raises a domain error."""
import re
from datetime import datetime

from models.constants import (
    DATE_INPUT_FORMAT,
    EMAIL_PATTERN,
    PASSWORD_MIN_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    TITLE_MAX_LENGTH,
    TITLE_MIN_LENGTH,
    VALID_ROLES,
    VALID_STATUSES,
)
from models.errors import ValidationError


def _is_number(value):
    return isinstance(value, (int, float))


def check_title(title):
    if not isinstance(title, str):
        raise ValidationError('Título inválido')
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError('Título muito longo')
    return title


def check_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')
    return status


def check_priority(priority):
    if not _is_number(priority):
        raise ValidationError('Prioridade inválida')
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError(f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}')
    return priority


def parse_due_date(value, message):
    try:
        return datetime.strptime(value, DATE_INPUT_FORMAT)
    except (ValueError, TypeError):
        raise ValidationError(message)


def join_tags(tags):
    if type(tags) == list:
        if not all(isinstance(tag, str) for tag in tags):
            raise ValidationError('Tags inválidas')
        return ','.join(tags)
    return tags


def check_reference_id(value, message):
    """A reference to another record is a scalar; a list or an object can never match."""
    if isinstance(value, (list, dict)):
        raise ValidationError(message)
    return value


def check_email(email):
    if not isinstance(email, str) or not re.match(EMAIL_PATTERN, email):
        raise ValidationError('Email inválido')
    return email


def check_password_text(password, too_short_message):
    if not isinstance(password, str):
        raise ValidationError('Senha inválida')
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(too_short_message)
    return password


def check_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    return role


def parse_optional_int(raw, message):
    """Query-string integer: empty means 'not given'; anything unparseable is a 400."""
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(message)
