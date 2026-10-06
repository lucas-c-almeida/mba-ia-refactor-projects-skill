'use strict';

const { decidePaymentStatus, PaymentStatus } = require('../models/payment');
const { hashPassword, generatePassword } = require('../models/password');
const { NotFoundError, PaymentDeclinedError, PersistenceError } = require('../errors');

const COURSE_NOT_FOUND = 'Curso não encontrado';

// Wraps a datastore step so its failure answers with the text that step always answered with.
async function step(failureMessage, work) {
    try {
        return await work();
    } catch (err) {
        throw new PersistenceError(failureMessage, err);
    }
}

class CheckoutController {
    constructor({ db, courses, users, enrollments, payments, auditLog, logger }) {
        Object.assign(this, { db, courses, users, enrollments, payments, auditLog, logger });
    }

    // Plain values in, plain values out: callable from any entry point.
    async checkout({ name, email, password, courseId, cardNumber }) {
        let course;
        try {
            course = await this.courses.findActiveById(courseId);
        } catch (err) {
            // The original answered a failed course lookup with the same 404 as a missing
            // course; that observable behaviour is preserved verbatim.
            this.logger.error('course lookup failed', err);
            course = undefined;
        }
        if (!course) throw new NotFoundError(COURSE_NOT_FOUND);

        const existing = await step('Erro DB', () => this.users.findIdByEmail(email));

        // Decide the payment before anything is written, so a declined card leaves no trace.
        const status = decidePaymentStatus(cardNumber);
        if (status === PaymentStatus.DENIED) throw new PaymentDeclinedError();

        const passwordHash = existing ? null : await hashPassword(password || generatePassword());

        return this.db.transaction(async () => {
            const userId = existing
                ? existing.id
                : await step('Erro ao criar usuário', () => this.users.create({ name, email, passwordHash }));
            const enrollmentId = await step('Erro Matrícula', () => this.enrollments.create(userId, courseId));
            await step('Erro Pagamento', () => this.payments.create(enrollmentId, course.priceCents, status));
            await this.auditLog.record(`Checkout curso ${courseId} por ${userId}`);
            this.logger.info(`checkout completed: enrollment ${enrollmentId}`);
            return { enrollmentId };
        });
    }
}

module.exports = { CheckoutController };
