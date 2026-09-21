// Checkout use case: find-or-create the buyer, charge, enroll, audit. (AP-05 -> RP-05)
// Plain values in, plain values out; no request/response objects.
const { decidePaymentStatus, maskCardNumber, PAYMENT_STATUS } = require('../models/payment');
const { hashPassword } = require('../models/password');
const {
    InvalidInputError, NotFoundError, PaymentDeclinedError, DependencyError, DB_ERROR_MESSAGE,
} = require('../models/errors');

// Preserved from the original: a new buyer who sends no password gets this one. (See report:
// removing it is PROPOSED, NOT APPLIED — it would make `pwd` mandatory.)
const DEFAULT_PASSWORD = '123456';

const MESSAGES = Object.freeze({
    badRequest: 'Bad Request',
    courseNotFound: 'Curso não encontrado',
    paymentDeclined: 'Pagamento recusado',
    dbError: DB_ERROR_MESSAGE,
    userCreateError: 'Erro ao criar usuário',
    enrollmentError: 'Erro Matrícula',
    paymentError: 'Erro Pagamento',
});

// Re-throws a datastore failure as a DependencyError carrying the client-facing message.
async function orFail(promise, message) {
    try {
        return await promise;
    } catch (err) {
        throw new DependencyError(message, err);
    }
}

class CheckoutController {
    constructor({ transaction, users, courses, enrollments, payments, auditLogs, logger }) {
        this.transaction = transaction;
        this.users = users;
        this.courses = courses;
        this.enrollments = enrollments;
        this.payments = payments;
        this.auditLogs = auditLogs;
        this.logger = logger;
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        let course;
        try {
            course = await this.courses.findActiveById(courseId);
        } catch (err) {
            // Preserved: the original answered 404 on a lookup failure too (see report, PROPOSED).
            throw new NotFoundError(MESSAGES.courseNotFound, err);
        }
        if (!course) throw new NotFoundError(MESSAGES.courseNotFound);

        const existing = await orFail(this.users.findByEmail(email), MESSAGES.dbError);

        // Inputs that used to crash the process are rejected before any write. (AP-11 -> RP-11)
        if (typeof cardNumber !== 'string') throw new InvalidInputError(MESSAGES.badRequest);
        if (!existing && password && typeof password !== 'string') {
            throw new InvalidInputError(MESSAGES.badRequest);
        }

        const userId = existing
            ? existing.id
            : await orFail(
                this.transaction(() => this.users.create({
                    name, email, passwordHash: hashPassword(password || DEFAULT_PASSWORD),
                })),
                MESSAGES.userCreateError,
            );

        this.logger.info(`Processando cartão ${maskCardNumber(cardNumber)}`);
        const status = decidePaymentStatus(cardNumber);
        if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeclinedError(MESSAGES.paymentDeclined);

        // Enrollment, payment and audit entry succeed or fail together. (AP-09 -> RP-09)
        const enrollmentId = await this.transaction(async () => {
            const newEnrollmentId = await orFail(
                this.enrollments.create({ userId, courseId }), MESSAGES.enrollmentError);
            await orFail(
                this.payments.create({ enrollmentId: newEnrollmentId, amount: course.price, status }),
                MESSAGES.paymentError);
            await orFail(
                this.auditLogs.record(`Checkout curso ${courseId} por ${userId}`), MESSAGES.dbError);
            return newEnrollmentId;
        });

        return { enrollmentId };
    }
}

module.exports = { CheckoutController };
