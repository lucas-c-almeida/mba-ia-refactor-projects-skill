'use strict';

/** Forwards a rejected promise from an async route handler to the error boundary. */
const asyncHandler = (handler) => (req, res, next) => {
  Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = { asyncHandler };
