// Payment rules and money representation.

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Rule preserved verbatim from the original code: there is no real gateway, and a card number
// starting with this prefix is approved.
const APPROVED_CARD_PREFIX = '4';

const CENTS_PER_UNIT = 100;

function decidePayment(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

// Money is stored and summed as integer cents; it crosses the boundary as a decimal number,
// as it always has.
function toCents(amount) {
    return Math.round(amount * CENTS_PER_UNIT);
}

function fromCents(cents) {
    return cents / CENTS_PER_UNIT;
}

module.exports = { PAYMENT_STATUS, decidePayment, toCents, fromCents };
