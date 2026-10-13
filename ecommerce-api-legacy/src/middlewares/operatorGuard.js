'use strict';

const crypto = require('crypto');

const OPERATOR_HEADER = 'x-operator-token';

/**
 * Guards a privileged operation with an operator credential taken from
 * configuration. Closed by default: with no token configured, nothing passes.
 */
function createOperatorGuard(operatorToken) {
  const expected = Buffer.from(operatorToken || '');
  return function requireOperator(req, res, next) {
    const given = Buffer.from(req.get(OPERATOR_HEADER) || '');
    const allowed = expected.length > 0 && given.length === expected.length && crypto.timingSafeEqual(given, expected);
    if (!allowed) return res.status(403).send('Forbidden');
    return next();
  };
}

module.exports = { createOperatorGuard };
