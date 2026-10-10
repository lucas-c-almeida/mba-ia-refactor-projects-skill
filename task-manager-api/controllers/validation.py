"""Pure helpers for type checks at the use-case boundary.

They reject only values that are invalid on their face (wrong type): requests that used to
crash a handler. Every request that was answered before is answered the same way.
"""
from models.errors import ValidationError


def require_object(data):
    """The request body must be a non-empty JSON object (the historical 'Dados inválidos')."""
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')
    return data


def reject_structured(value, message):
    """A scalar field must not receive a list or an object."""
    if isinstance(value, (list, dict)):
        raise ValidationError(message)
    return value


def require_text(value, message):
    if not isinstance(value, str):
        raise ValidationError(message)
    return value


def require_number(value, message):
    if not isinstance(value, (int, float)):
        raise ValidationError(message)
    return value


def tags_to_storage(tags, message='Tags inválidas'):
    """A list of strings is stored comma-joined; any other scalar is stored as given."""
    if isinstance(tags, list):
        if not all(isinstance(item, str) for item in tags):
            raise ValidationError(message)
        return ','.join(tags)
    return reject_structured(tags, message)
