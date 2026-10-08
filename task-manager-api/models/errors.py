"""Domain error taxonomy (RP-09). One mapping to HTTP lives in middlewares/error_handler.py."""


class AppError(Exception):
    """An error the application raises on purpose, with a message safe to show."""

    status = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status = 400


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409


class PersistenceError(AppError):
    status = 500
