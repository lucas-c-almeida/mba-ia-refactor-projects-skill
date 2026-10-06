"""Input checks and messages shared by every controller (one definition each, AP-12/AP-15)."""
from models.errors import ValidationError

MSG_INVALID_DATA = 'Dados inválidos'
MSG_UPDATE_FAILED = 'Erro ao atualizar'
MSG_DELETE_FAILED = 'Erro ao deletar'


def require_object(data, allow_empty=False):
    """The request body must be a JSON object; an empty one only where the operation allows it."""
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(MSG_INVALID_DATA)
    return data


def optional_text(value, message):
    """A text field that may be absent or null, but never another type."""
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def required_text(value, missing_message, invalid_message):
    if not value:
        raise ValidationError(missing_message)
    if not isinstance(value, str):
        raise ValidationError(invalid_message)
    return value
