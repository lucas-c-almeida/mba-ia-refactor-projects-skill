'use strict';

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Stand-in for a real gateway: cards starting with this prefix are approved.
const APPROVED_CARD_PREFIX = '4';

/** Decides the payment outcome for a card number. Pure: no I/O. */
function decidePaymentStatus(card) {
  return card.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

module.exports = { PAYMENT_STATUS, decidePaymentStatus };
