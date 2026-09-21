// Payment entity: status vocabulary, approval rule and persistence. (AP-05 -> RP-05, AP-15 -> RP-15)

const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Simulated gateway rule preserved from the original: cards starting with this prefix are approved.
const APPROVED_CARD_PREFIX = '4';

function decidePaymentStatus(cardNumber) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

function maskCardNumber(cardNumber) {
    return `****${cardNumber.slice(-4)}`;
}

class PaymentRepository {
    constructor(db) {
        this.db = db;
    }

    async create({ enrollmentId, amount, status }) {
        const { lastID } = await this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
        );
        return lastID;
    }
}

module.exports = { PAYMENT_STATUS, decidePaymentStatus, maskCardNumber, PaymentRepository };
