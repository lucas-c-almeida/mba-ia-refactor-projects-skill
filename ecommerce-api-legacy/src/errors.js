'use strict';

/**
 * Domain error taxonomy — resolves part of AP-09 (src/AppManager.js, original): a small,
 * named set of errors the domain can raise, mapped to protocol responses in exactly one
 * place (middlewares/errorBoundary.js) instead of a repeated ad hoc `if (err) return
 * res.status(...)` in every handler.
 *
 * Status codes and body text below reproduce exactly what the original application sent for
 * each case (see reports/baseline.json) — centralizing the mapping is safe only because the
 * observable status and body are unchanged.
 */

class AppError extends Error {
  constructor(message, { status }) {
    super(message);
    this.status = status;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Bad Request') {
    super(message, { status: 400 });
  }
}

class NotFoundError extends AppError {
  constructor(message = 'Not found') {
    super(message, { status: 404 });
  }
}

class PaymentDeniedError extends AppError {
  constructor(message = 'Pagamento recusado') {
    super(message, { status: 400 });
  }
}

class DatabaseError extends AppError {
  constructor(message = 'Erro DB') {
    super(message, { status: 500 });
  }
}

module.exports = {
  AppError, ValidationError, NotFoundError, PaymentDeniedError, DatabaseError,
};
