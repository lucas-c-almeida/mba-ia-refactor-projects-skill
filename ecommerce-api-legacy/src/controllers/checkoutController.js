const { BusinessRuleError, DependencyError, NotFoundError, ValidationError } = require('../errors');
const { PAYMENT_STATUS, decidePayment } = require('../models/paymentPolicy');

const isText = (value) => typeof value === 'string';

// One use case: plain values in, plain values out. No request or response objects.
class CheckoutController {
    constructor({ users, courses, enrollments, passwords, logger = console }) {
        this.users = users;
        this.courses = courses;
        this.enrollments = enrollments;
        this.passwords = passwords;
        this.logger = logger;
    }

    async checkout({ usr, eml, pwd, c_id: courseId, card }) {
        if (!usr || !eml || !courseId || !card) throw new ValidationError();
        // Values of the wrong type are invalid on their face (they used to crash the process).
        const typesOk = isText(usr) && isText(eml) && isText(card)
            && (pwd === undefined || pwd === null || isText(pwd))
            && (isText(courseId) || typeof courseId === 'number');
        if (!typesOk) throw new ValidationError();

        // Kept as the API has always answered: a failed course lookup reads as "not found".
        const course = await this.courses.findActiveById(courseId).catch((err) => {
            this.logger.error(err);
            return null;
        });
        if (!course) throw new NotFoundError('Curso não encontrado');

        let user;
        try {
            user = await this.users.findIdByEmail(eml);
        } catch (err) {
            throw new DependencyError('Erro DB', err);
        }

        let userId;
        if (user) {
            userId = user.id;
        } else {
            const passwordHash = await this.passwords.hash(pwd || this.passwords.generateSecret());
            try {
                userId = await this.users.insert({ name: usr, email: eml, passwordHash });
            } catch (err) {
                throw new DependencyError('Erro ao criar usuário', err);
            }
        }

        // The card number and gateway credentials are never logged.
        const status = decidePayment(card);
        if (status === PAYMENT_STATUS.DENIED) throw new BusinessRuleError('Pagamento recusado');

        let enrollmentId;
        try {
            enrollmentId = await this.enrollments.insertEnrollment(userId, courseId);
        } catch (err) {
            throw new DependencyError('Erro Matrícula', err);
        }
        try {
            await this.enrollments.insertPayment(enrollmentId, course.price, status);
        } catch (err) {
            throw new DependencyError('Erro Pagamento', err);
        }

        // Best-effort audit trail: a failure is logged and does not undo a completed purchase.
        try {
            await this.enrollments.insertAuditLog(`Checkout curso ${courseId} por ${userId}`);
        } catch (err) {
            this.logger.warn(`audit log not written: ${err.message}`);
        }

        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    }
}

module.exports = { CheckoutController };
