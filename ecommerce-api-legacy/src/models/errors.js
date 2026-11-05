'use strict';

// Error taxonomy owned by the domain (RP-09). The error boundary maps each one to a response;
// the messages below are the bodies the application has always answered with.

class AppError extends Error {
  constructor(message, status, options = {}) {
    super(message, options);
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
  constructor() { super('Pagamento recusado', 400); }
}

class ForbiddenError extends AppError {
  constructor() { super('Forbidden', 403); }
}

/** A datastore failure. `message` is the safe text returned; `cause` is logged, never returned. */
class PersistenceError extends AppError {
  constructor(message, cause) { super(message, 500, { cause }); }
}

module.exports = {
  AppError, ValidationError, NotFoundError, PaymentDeclinedError, ForbiddenError, PersistenceError,
};
