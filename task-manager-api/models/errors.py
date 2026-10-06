"""The application's error taxonomy, owned by the domain (AP-09).

Each error carries the message the API already returns; the mapping from `code` to an HTTP
status lives in one place, middlewares/error_handler.py.
"""


class AppError(Exception):
    code = 'internal_error'

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    code = 'invalid_input'


class NotFoundError(AppError):
    code = 'not_found'


class ConflictError(AppError):
    code = 'conflict'


class AuthenticationError(AppError):
    code = 'not_authenticated'


class ForbiddenError(AppError):
    code = 'forbidden'


class PersistenceError(AppError):
    code = 'persistence_failure'
