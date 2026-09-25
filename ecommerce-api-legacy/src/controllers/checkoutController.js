'use strict';

const { NotFoundError, PaymentDeniedError } = require('../errors');
const { decidePaymentStatus, PAID } = require('../models/checkoutPolicy');
const { hashPassword, randomCredential } = require('../models/password');

/**
 * The checkout use case — resolves AP-03/AP-05 (original: this orchestration lived inline
 * inside the POST /api/checkout route handler in src/AppManager.js:28-78, mixed with
 * parsing and persistence). Accepts and returns plain values only: it can be called from a
 * test, a second entry point or a scheduled job with no HTTP request in sight (the
 * second-caller test, `04-architecture-guidelines.md` §5).
 */
class CheckoutController {
  constructor({
    users, courses, enrollments, payments, auditLogs,
  }) {
    this.users = users;
    this.courses = courses;
    this.enrollments = enrollments;
    this.payments = payments;
    this.auditLogs = auditLogs;
  }

  async checkout({
    userName, email, password, courseId, cardNumber,
  }) {
    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    let user = await this.users.findByEmail(email);
    if (!user) {
      // AP-01 (original: badCrypto(p || "123456")): no fixed fallback credential.
      const plainCredential = password || randomCredential();
      const userId = await this.users.create({
        name: userName,
        email,
        passHash: hashPassword(plainCredential),
      });
      user = { id: userId };
    }

    const status = decidePaymentStatus(cardNumber);
    if (status !== PAID) throw new PaymentDeniedError('Pagamento recusado');

    const enrollmentId = await this.enrollments.create({ userId: user.id, courseId: course.id });
    await this.payments.create({ enrollmentId, amountCents: course.price_cents, status });
    await this.auditLogs.record(`Checkout curso ${course.id} por ${user.id}`);

    return { enrollmentId, courseTitle: course.title };
  }
}

module.exports = { CheckoutController };
