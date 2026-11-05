'use strict';

const DEFAULT_PORT = 3000;

/**
 * Reads the environment once and returns an immutable object.
 * Nothing else in the codebase reads process.env.
 *
 * OPERATOR_TOKEN guards the privileged operations (financial report, account
 * removal). It is unset by default, which keeps those operations closed.
 */
function loadConfig(env = process.env) {
  const port = Number.parseInt(env.PORT, 10);
  return Object.freeze({
    port: Number.isInteger(port) && port > 0 ? port : DEFAULT_PORT,
    operatorToken: env.OPERATOR_TOKEN || null,
  });
}

module.exports = { loadConfig };
