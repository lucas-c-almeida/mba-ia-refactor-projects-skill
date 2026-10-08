// Pure payment rules: no I/O, no framework.

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// The card prefix the (simulated) gateway approves.
const APPROVED_CARD_PREFIX = '4';

function decidePayment(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

const CENTS_PER_UNIT = 100;
const toAmount = (cents) => cents / CENTS_PER_UNIT;

module.exports = { PAYMENT_STATUS, decidePayment, toAmount };
