"""Boundary parsing (RP-11): every value read from a request is type-checked here, as sent, with
no silent coercion. A wrong type answers the application's own 400; the domain rules (length,
range, existence) stay in the models and controllers."""
from flask import request

from database import MAX_ID
from models.errors import ValidationError

INVALID_BODY = 'Dados inválidos'


def json_object(allow_empty=False):
    """The JSON body as a dict. `allow_empty` keeps `{}` acceptable where it always was."""
    data = request.get_json()
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(INVALID_BODY)
    return data


def is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def pick(data, spec):
    """Validate the fields present in `data` against `spec` = {name: (check, message)} and return
    only those present, in a new dict."""
    fields = {}
    for name, (check, message) in spec.items():
        if name in data:
            if not check(data[name]):
                raise ValidationError(message)
            fields[name] = data[name]
    return fields


def string(value):
    return isinstance(value, str)


def string_or_null(value):
    return value is None or isinstance(value, str)


def integer(value):
    return is_integer(value)


def id_or_null(value):
    """A record reference: an integer (looked up by the caller) or null."""
    return value is None or is_integer(value)


def boolean(value):
    return isinstance(value, bool)


def tags(value):
    """Tags travel as a list of strings or as one comma-separated string (or null)."""
    if value is None or isinstance(value, str):
        return True
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def query_integer(name, message):
    """An optional integer query parameter; None when absent or empty."""
    raw = request.args.get(name, '')
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(message) from None
    if not -MAX_ID - 1 <= value <= MAX_ID:
        raise ValidationError(message)
    return value
