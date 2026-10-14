'use strict';

const { centsToAmount } = require('./money');
const { PAYMENT_STATUS } = require('./payment');

/**
 * Persistence for the domain. Every write accepts an `executor`: the database
 * itself, or the `tx` handle of an open transaction.
 */
class UserRepository {
  constructor(db) {
    this.db = db;
  }

  findByEmail(email) {
    return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
  }

  async insert(executor, { name, email, passwordHash }) {
    const { lastID } = await executor.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
    return lastID;
  }

  deleteById(id) {
    return this.db.run('DELETE FROM users WHERE id = ?', [id]);
  }
}

class CourseRepository {
  constructor(db) {
    this.db = db;
  }

  findActiveById(id) {
    return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
  }
}

class EnrollmentRepository {
  async insert(executor, { userId, courseId }) {
    const { lastID } = await executor.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
    return lastID;
  }
}

class PaymentRepository {
  async insert(executor, { enrollmentId, amountCents, status }) {
    const { lastID } = await executor.run('INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)', [enrollmentId, amountCents, status]);
    return lastID;
  }
}

class AuditLogRepository {
  insert(executor, action) {
    return executor.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
  }
}

/** One set-based query for the financial report, ordered explicitly. */
class FinancialReportRepository {
  constructor(db) {
    this.db = db;
  }

  async build() {
    const rows = await this.db.all(
      `SELECT c.id AS course_id, c.title AS title, e.id AS enrollment_id,
              u.name AS student, p.amount_cents AS amount_cents, p.status AS status
         FROM courses c
         LEFT JOIN enrollments e ON e.course_id = c.id
         LEFT JOIN users u ON u.id = e.user_id
         LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
        ORDER BY c.id, e.id`,
    );

    const byCourse = new Map();
    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.title, revenueCents: 0, students: [] });
      }
      if (row.enrollment_id === null) continue;
      const entry = byCourse.get(row.course_id);
      if (row.status === PAYMENT_STATUS.PAID) entry.revenueCents += row.amount_cents;
      entry.students.push({
        student: row.student === null ? 'Unknown' : row.student,
        paid: row.amount_cents === null ? 0 : centsToAmount(row.amount_cents),
      });
    }

    return [...byCourse.values()].map((entry) => ({
      course: entry.course,
      revenue: centsToAmount(entry.revenueCents),
      students: entry.students,
    }));
  }
}

module.exports = { UserRepository, CourseRepository, EnrollmentRepository, PaymentRepository, AuditLogRepository, FinancialReportRepository };
