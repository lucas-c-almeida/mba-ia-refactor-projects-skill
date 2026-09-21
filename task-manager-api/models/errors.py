"""Domain error taxonomy.

Controllers raise these; the single error boundary (middlewares/error_handler.py)
maps them to responses. The message is the client-facing text.
"""


class AppError(Exception):
    status = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status = 400


class AuthenticationError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409


class PersistenceError(AppError):
    status = 500
