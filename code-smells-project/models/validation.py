"""Small input predicates shared by the product rules and the order use case. Pure."""


def is_number(value) -> bool:
    """A real number; booleans are not numbers here even though Python says they are."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)
