// Payment domain rules (AP-05, AP-15 — RP-05, RP-15). No I/O, no framework.

const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

// Simulated gateway rule, preserved exactly: a card number starting with this prefix is approved.
const APPROVED_CARD_PREFIX = '4';

function authorizePayment(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
}

// For logs: never the full card number (AP-08).
function maskCardNumber(cardNumber) {
    return `****${cardNumber.slice(-4)}`;
}

module.exports = { PaymentStatus, authorizePayment, maskCardNumber };
