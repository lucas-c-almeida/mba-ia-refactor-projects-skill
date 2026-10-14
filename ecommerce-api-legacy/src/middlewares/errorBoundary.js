'use strict';

const { STATUS_CODES } = require('http');
const { AppError } = require('../errors');

const SERVER_ERROR = 500;
const FIRST_CLIENT_ERROR = 400;
const FIRST_SERVER_ERROR = 500;

/**
 * The single place that turns errors into responses. Intentional errors keep
 * their status and text; anything unexpected is logged in full and answered
 * with a generic message, never with a stack trace.
 */
function errorBoundary(logger = console) {
  // Express identifies an error handler by its four parameters.
  // eslint-disable-next-line no-unused-vars
  return function handleError(err, req, res, next) {
    if (res.headersSent) return next(err);

    if (err instanceof AppError) {
      if (err.cause) logger.error(err.cause);
      return res.status(err.status).send(err.message);
    }

    // Client errors raised by the framework (malformed JSON, payload too large) keep their status.
    const isClientError = Number.isInteger(err.status) && err.status >= FIRST_CLIENT_ERROR && err.status < FIRST_SERVER_ERROR;
    const status = isClientError ? err.status : SERVER_ERROR;
    if (!isClientError) logger.error(err);
    return res.status(status).send(STATUS_CODES[status]);
  };
}

module.exports = { errorBoundary };
