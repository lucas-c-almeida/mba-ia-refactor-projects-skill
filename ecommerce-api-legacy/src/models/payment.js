'use strict';

// Domain rules for payments. No I/O, no framework.

const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulated gateway rule kept from the original behaviour: card numbers starting with this
// prefix are approved, every other one is denied.
const APPROVED_CARD_PREFIX = '4';

function decidePaymentStatus(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
}

module.exports = { PaymentStatus, APPROVED_CARD_PREFIX, decidePaymentStatus };
