// Use case: buy a course. Validated plain values in, plain values out; no HTTP here.
const { NotFoundError, PaymentDeclinedError, DependencyError } = require('../models/errors');
const { PAYMENT_STATUS, decidePayment } = require('../models/payment');
const { hashPassword, generatePassword } = require('../models/password');

// Runs one persistence step; a driver failure becomes the error body the application has always
// answered for that step.
async function step(work, failureMessage) {
    try {
        return await work();
    } catch (err) {
        if (err instanceof DependencyError) throw err;
        throw new DependencyError(failureMessage, err);
    }
}

function createCheckoutController({ db, users, courses, enrollments, logger }) {
    return {
        async checkout({ name, email, password, courseId, cardNumber }) {
            const course = await step(() => courses.findActiveById(courseId), 'Erro DB');
            if (!course) throw new NotFoundError('Curso não encontrado');

            // The payment is decided before anything is written: a declined card leaves no trace.
            const status = decidePayment(cardNumber);
            if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeclinedError();

            const existing = await step(() => users.findIdByEmail(email), 'Erro DB');
            const passwordHash = existing ? null : await hashPassword(password || generatePassword());

            logger.info(`Processando pagamento do curso ${course.id}`);

            return db.transaction(async () => {
                // Looked up again inside the transaction: another checkout may have created it.
                const current = await step(() => users.findIdByEmail(email), 'Erro DB');
                const userId = current
                    ? current.id
                    : await step(async () => users.create({
                        name,
                        email,
                        passwordHash: passwordHash || await hashPassword(password || generatePassword()),
                    }), 'Erro ao criar usuário');

                const enrollmentId = await step(() => enrollments.create(userId, course.id), 'Erro Matrícula');
                await step(() => enrollments.recordPayment(enrollmentId, course.priceCents, status), 'Erro Pagamento');
                await step(() => enrollments.recordAudit(`Checkout curso ${course.id} por ${userId}`), 'Erro DB');
                return { enrollmentId };
            });
        },
    };
}

module.exports = { createCheckoutController };
