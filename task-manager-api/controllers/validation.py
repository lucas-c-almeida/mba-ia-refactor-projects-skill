"""Boundary checks shared by the use cases.

Each check rejects only input that the datastore or the domain cannot accept at all
(input that used to end in a server error), never input that is accepted today.
"""
from models.errors import ValidationError

from controllers import messages


def require_object(data):
    """A create/login payload must be a non-empty JSON object."""
    if not isinstance(data, dict) or not data:
        raise ValidationError(messages.INVALID_DATA)
    return data


def reject_container(value, message):
    """Scalar text columns cannot store lists or objects."""
    if isinstance(value, (list, dict)):
        raise ValidationError(message)
    return value


def require_present_scalar(value, message):
    """A NOT NULL column: null or a container is rejected."""
    if value is None:
        raise ValidationError(message)
    return reject_container(value, message)


def require_boolean(value, message):
    # Boolean columns accept True/False (and values equal to them, such as 0/1) or null.
    if value not in (True, False, None):
        raise ValidationError(message)
    return value
