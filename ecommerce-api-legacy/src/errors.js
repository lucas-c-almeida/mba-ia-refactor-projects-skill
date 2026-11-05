'use strict';

/**
 * An error the application raises on purpose. `message` is the body sent to
 * the client and `status` the HTTP status; both are part of the public contract.
 */
class AppError extends Error {
  constructor(message, status, options) {
    super(message, options);
    this.status = status;
  }
}

/**
 * Awaits a promise and, if it rejects, raises the intentional error the
 * original API answered with. The underlying cause is kept for the log.
 */
async function orFail(promise, message, status = 500) {
  try {
    return await promise;
  } catch (cause) {
    throw new AppError(message, status, { cause });
  }
}

module.exports = { AppError, orFail };
