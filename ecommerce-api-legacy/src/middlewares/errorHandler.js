'use strict';

const { AppError } = require('../models/errors');

const BAD_REQUEST = 'Bad Request';
const INTERNAL_ERROR = 'Erro interno';
const HTTP_INTERNAL_ERROR = 500;

const isClientErrorStatus = (status) => Number.isInteger(status) && status >= 400 && status < 500;

/**
 * The single error boundary (RP-09, RP-17), registered after every route. Application errors keep
 * the status and text they always had; anything else is logged in full and answered without
 * internals — never a stack trace or a path.
 */
function errorHandler(logger) {
  // Express recognizes an error middleware by its four parameters.
  // eslint-disable-next-line no-unused-vars
  return (err, req, res, next) => {
    if (err instanceof AppError) {
      if (err.status >= HTTP_INTERNAL_ERROR) logger.error(err.message, err.cause ?? err);
      return res.status(err.status).send(err.message);
    }
    // Errors raised by the framework itself for a bad request (malformed JSON, oversized body).
    if (isClientErrorStatus(err && err.status)) {
      return res.status(err.status).send(BAD_REQUEST);
    }
    logger.error('unhandled error', err);
    return res.status(HTTP_INTERNAL_ERROR).send(INTERNAL_ERROR);
  };
}

module.exports = { errorHandler };
