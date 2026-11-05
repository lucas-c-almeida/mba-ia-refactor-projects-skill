'use strict';

const { AppError, orFail } = require('../errors');
const { PAYMENT_STATUS, decidePaymentStatus } = require('../models/payment');
const { hashPassword, generateSecret } = require('../models/passwordHasher');

/** The checkout use case: plain values in, plain values out, no HTTP objects. */
class CheckoutController {
  constructor({ db, users, courses, enrollments, payments, auditLogs }) {
    this.db = db;
    this.users = users;
    this.courses = courses;
    this.enrollments = enrollments;
    this.payments = payments;
    this.auditLogs = auditLogs;
  }

  async checkout({ name, email, password, courseId, card }) {
    const course = await orFail(this.courses.findActiveById(courseId), 'Curso não encontrado', 404);
    if (!course) throw new AppError('Curso não encontrado', 404);

    const existingUser = await orFail(this.users.findByEmail(email), 'Erro DB');

    if (decidePaymentStatus(card) === PAYMENT_STATUS.DENIED) {
      throw new AppError('Pagamento recusado', 400);
    }

    // A new account with no password gets a generated secret nobody knows.
    const passwordHash = existingUser ? null : await hashPassword(password || generateSecret());

    const enrollmentId = await this.db.transaction(async (tx) => {
      const userId = existingUser
        ? existingUser.id
        : await orFail(this.users.insert(tx, { name, email, passwordHash }), 'Erro ao criar usuário');

      const newEnrollmentId = await orFail(this.enrollments.insert(tx, { userId, courseId }), 'Erro Matrícula');
      await orFail(
        this.payments.insert(tx, { enrollmentId: newEnrollmentId, amountCents: course.price_cents, status: PAYMENT_STATUS.PAID }),
        'Erro Pagamento',
      );
      await this.auditLogs.insert(tx, `Checkout curso ${courseId} por ${userId}`);
      return newEnrollmentId;
    });

    return { enrollmentId };
  }
}

module.exports = { CheckoutController };
