'use strict';

const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Approval rule preserved verbatim from the original implementation: a card number starting with
// this prefix is approved, any other is denied. Whether it is a simulation stub or a business
// rule is not stated anywhere in the project; it is kept as it was.
const APPROVED_CARD_PREFIX = '4';

const LAST_DIGITS_SHOWN = 4;

function decidePayment(cardNumber) {
  return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
}

/** The only form of a card number that may reach a log. */
function maskCardNumber(cardNumber) {
  return `****${cardNumber.slice(-LAST_DIGITS_SHOWN)}`;
}

module.exports = { PaymentStatus, decidePayment, maskCardNumber };
