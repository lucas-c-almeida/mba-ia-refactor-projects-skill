'use strict';

const { PersistenceError } = require('./errors');

class EnrollmentRepository {
  constructor(db) {
    this.db = db;
  }

  /**
   * Records an enrollment, its payment and the audit entry as one unit: either all three are
   * stored, or none is (the original stored them one by one, so a failure left an enrollment
   * without a payment).
   */
  createWithPayment({ userId, courseId, amountCents, status, auditAction }) {
    return this.db.transaction(async (tx) => {
      const enrollment = await this.step('Erro Matrícula', () => tx.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId],
      ));
      await this.step('Erro Pagamento', () => tx.run(
        'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
        [enrollment.lastId, amountCents, status],
      ));
      await this.step('Erro Pagamento', () => tx.run(
        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [auditAction],
      ));
      return enrollment.lastId;
    });
  }

  // Each write keeps the message the original answered with when that write failed.
  async step(failureMessage, write) {
    try {
      return await write();
    } catch (err) {
      throw new PersistenceError(failureMessage, err);
    }
  }
}

module.exports = { EnrollmentRepository };
