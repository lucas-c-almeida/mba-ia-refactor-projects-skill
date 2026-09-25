'use strict';

/**
 * Checkout business rules — pure, no I/O, no framework. Resolves AP-03/AP-05 (original:
 * src/AppManager.js mixed this decision into the route handler) and AP-15 (original:
 * AppManager.js:46, the "4" literal had no name).
 *
 * The heuristic itself — approve when the card number starts with the Visa BIN prefix — is
 * preserved exactly as the original implemented it. It is not a real payment gateway
 * integration (there is no gateway to integrate against in this exercise); naming the
 * literal is the applied fix, and replacing the heuristic with a real integration is a
 * product decision outside this refactor's scope (see the AP-15 finding's Contract field).
 */

const VISA_BIN_PREFIX = '4';

const PAID = 'PAID';
const DENIED = 'DENIED';

function decidePaymentStatus(cardNumber) {
  return String(cardNumber).startsWith(VISA_BIN_PREFIX) ? PAID : DENIED;
}

module.exports = { decidePaymentStatus, PAID, DENIED, VISA_BIN_PREFIX };
