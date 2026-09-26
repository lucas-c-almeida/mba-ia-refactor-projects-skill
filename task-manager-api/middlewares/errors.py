"""Small domain error taxonomy, owned by the application, not by any one route.

Fixes AP-09 (swallowed / uncentralized error handling). Each class carries the exact
status code the original code returned for the equivalent situation, so registering
one handler for all of them (middlewares/error_handler.py) preserves every existing
status code and the `{"error": "..."}` body shape — see reports/audit-latest.md,
AP-09 finding, Contract: safe.
"""


class AppError(Exception):
    status = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status = 400


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409
