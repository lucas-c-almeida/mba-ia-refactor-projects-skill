// Small error taxonomy owned by the domain. The messages are the bodies the API has always sent.

class AppError extends Error {
    constructor(message, status, cause) {
        super(message, cause === undefined ? undefined : { cause });
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class BusinessRuleError extends AppError {
    constructor(message) { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

// A failed dependency (the datastore). The original error travels as `cause` and is logged at the boundary.
class DependencyError extends AppError {
    constructor(message, cause) { super(message, 500, cause); }
}

module.exports = { AppError, ValidationError, BusinessRuleError, NotFoundError, DependencyError };
