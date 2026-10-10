"""Domain error taxonomy. Mapped to protocol responses in one place (middlewares/error_handler.py)."""


class AppError(Exception):
    status = 500


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
