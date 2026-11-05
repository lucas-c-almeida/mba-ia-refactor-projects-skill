'use strict';

const crypto = require('crypto');
const { ForbiddenError } = require('../models/errors');

const OPERATOR_TOKEN_HEADER = 'x-operator-token';

const digest = (value) => crypto.createHash('sha256').update(value).digest();

/**
 * Guard for privileged operations (RP-04): the caller must present the operator credential
 * configured in OPERATOR_TOKEN. Closed by default — with no token configured, every call is
 * refused. The comparison is constant-time.
 */
function requireOperator(operatorToken) {
  const expected = operatorToken ? digest(operatorToken) : null;
  return (req, res, next) => {
    const presented = req.get(OPERATOR_TOKEN_HEADER);
    const allowed = expected !== null
      && typeof presented === 'string'
      && crypto.timingSafeEqual(digest(presented), expected);
    next(allowed ? undefined : new ForbiddenError());
  };
}

module.exports = { requireOperator, OPERATOR_TOKEN_HEADER };
