'use strict';

const { decidePayment, maskCardNumber, PaymentStatus } = require('../models/payment');
const { hashPassword, unusablePasswordHash } = require('../models/password');
const {
  NotFoundError, PaymentDeclinedError, PersistenceError,
} = require('../models/errors');

const COURSE_NOT_FOUND = 'Curso não encontrado';

class CheckoutController {
  constructor({ users, courses, enrollments, logger }) {
    this.users = users;
    this.courses = courses;
    this.enrollments = enrollments;
    this.logger = logger;
  }

  /**
   * Buys a course: finds or creates the account by e-mail, decides the payment and records
   * enrollment + payment + audit entry together. Returns the new enrollment id.
   */
  async checkout({ name, email, password, courseId, cardNumber }) {
    const course = await this.findCourse(courseId);
    const userId = await this.findOrCreateUser({ name, email, password });

    this.logger.log(`Processando cartão ${maskCardNumber(cardNumber)}`);
    const status = decidePayment(cardNumber);
    if (status === PaymentStatus.DENIED) throw new PaymentDeclinedError();

    return this.enrollments.createWithPayment({
      userId,
      courseId,
      amountCents: course.priceCents,
      status,
      auditAction: `Checkout curso ${courseId} por ${userId}`,
    });
  }

  async findCourse(courseId) {
    let course;
    try {
      course = await this.courses.findActiveById(courseId);
    } catch (err) {
      // The original answered a failed course lookup like a missing course (404); that answer is
      // kept, and the cause is logged instead of discarded.
      this.logger.error('course lookup failed', err);
      throw new NotFoundError(COURSE_NOT_FOUND);
    }
    if (!course) throw new NotFoundError(COURSE_NOT_FOUND);
    return course;
  }

  async findOrCreateUser({ name, email, password }) {
    let userId;
    try {
      userId = await this.users.findIdByEmail(email);
    } catch (err) {
      throw new PersistenceError('Erro DB', err);
    }
    if (userId !== null) return userId;

    const passwordHash = password ? await hashPassword(password) : unusablePasswordHash();
    try {
      return await this.users.create({ name, email, passwordHash });
    } catch (err) {
      throw new PersistenceError('Erro ao criar usuário', err);
    }
  }
}

module.exports = { CheckoutController };
