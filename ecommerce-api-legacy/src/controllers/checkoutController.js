// Checkout use case (AP-05 — RP-05): plain values in, plain values out; no request/response objects.
// The order of checks and every client-visible outcome are those of the original handler.

const { authorizePayment, maskCardNumber, PaymentStatus } = require('../models/payment');
const { hashPassword } = require('../models/password');
const {
    NotFoundError, PaymentDeclinedError, DependencyError, GENERIC_DB_ERROR,
} = require('../models/errors');

// PROPOSED, NOT APPLIED (AP-08): an account created without `pwd` still receives this fixed
// password, because rejecting such requests would make an optional field required.
const PASSWORD_WHEN_OMITTED = '123456';

// Runs a datastore step; a driver failure becomes the step's own client-facing 500 message.
async function step(promise, failureMessage) {
    try {
        return await promise;
    } catch (err) {
        throw new DependencyError(failureMessage, err);
    }
}

class CheckoutController {
    constructor({ db, courses, users, enrollments, logger }) {
        this.db = db;
        this.courses = courses;
        this.users = users;
        this.enrollments = enrollments;
        this.logger = logger;
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        let course;
        try {
            course = await this.courses.findActiveById(courseId);
        } catch (err) {
            // Preserved contract: a failed course lookup has always answered 404, like a missing
            // course. The failure is logged rather than dropped.
            this.logger.error('course lookup failed', err.stack);
            course = null;
        }
        if (!course) throw new NotFoundError('Curso não encontrado');

        const existing = await step(this.users.findIdByEmail(email), GENERIC_DB_ERROR);
        const userId = existing
            ? existing.id
            : await this.createUser({ name, email, password });

        this.logger.info(`Processando pagamento do curso ${courseId} com cartão ${maskCardNumber(cardNumber)}`);
        const status = authorizePayment(cardNumber);
        if (status === PaymentStatus.DENIED) throw new PaymentDeclinedError();

        // Enrollment, payment and audit are one unit: all persisted, or none (AP-09).
        const enrollmentId = await this.db.transaction(async (tx) => {
            const id = await step(this.enrollments.create(tx, { userId, courseId }), 'Erro Matrícula');
            await step(this.enrollments.recordPayment(tx, { enrollmentId: id, amount: course.price, status }),
                'Erro Pagamento');
            await step(this.enrollments.recordAudit(tx, `Checkout curso ${courseId} por ${userId}`), GENERIC_DB_ERROR);
            return id;
        });

        return { enrollmentId };
    }

    async createUser({ name, email, password }) {
        const passwordHash = await hashPassword(password || PASSWORD_WHEN_OMITTED);
        return step(this.users.create({ name, email, passwordHash }), 'Erro ao criar usuário');
    }
}

module.exports = { CheckoutController };
