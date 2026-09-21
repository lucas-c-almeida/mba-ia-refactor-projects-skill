"""Domain error taxonomy. Mapped to HTTP responses in one place: middlewares/error_handler.py."""


class AppError(Exception):
    """Base class for expected, domain-level failures."""


class ValidationError(AppError):
    """The input is malformed or violates an invariant."""


class BusinessRuleError(AppError):
    """The input is well-formed but the operation is not allowed (e.g. insufficient stock)."""


class AuthenticationError(AppError):
    """Credentials did not match."""


class DependencyError(AppError):
    """An infrastructure dependency (e.g. the database) is unavailable."""
