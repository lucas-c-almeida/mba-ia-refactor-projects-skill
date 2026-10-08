"""Domain error taxonomy.

The domain says what went wrong; the outermost layer (middlewares/error_handler.py) decides the
status code. Nothing in the domain or in the controllers knows that HTTP exists.
"""


class DomainError(Exception):
    """Base class. `failure_flag` marks the responses that carry `"sucesso": false` today."""

    def __init__(self, message: str, *, failure_flag: bool = False):
        super().__init__(message)
        self.message = message
        self.failure_flag = failure_flag


class ValidationError(DomainError):
    """The input is invalid on its face."""


class BusinessRuleError(DomainError):
    """A well-formed request that a business rule refuses (unknown product, short stock)."""


class AuthenticationError(DomainError):
    """The credentials do not identify an account."""


class AccessDeniedError(DomainError):
    """The caller may not use an operator-only operation."""


class NotFoundError(DomainError):
    """The referenced record does not exist."""


class ConflictError(DomainError):
    """The request collides with existing data."""
