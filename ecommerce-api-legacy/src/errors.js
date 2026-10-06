'use strict';

// Error taxonomy. `message` is the exact text the application has always answered with,
// so the observable status and body of every intentional error are unchanged.
class AppError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') { super(message, 400); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') { super(message, 400); }
}

// A datastore failure at a step whose failure text is part of the contract.
class PersistenceError extends AppError {
    constructor(message, cause) {
        super(message, 500);
        this.cause = cause;
    }
}

module.exports = { AppError, ValidationError, NotFoundError, PaymentDeclinedError, PersistenceError };
