'use strict';

const { DatabaseError } = require('../errors');

/**
 * Persistence, one repository per entity — resolves AP-03 (original: src/AppManager.js,
 * every query issued inline inside route handlers) and AP-06 (original: the database
 * connection was opened inside the class that also held routing and rules). Every
 * repository receives its connection; none of them opens one.
 *
 * Kept as small classes in one file rather than five near-empty files, per
 * `04-architecture-guidelines.md` §4: "If a layer directory would hold a single small file,
 * keep the file and skip the ceremony" — this project has five tables and none of the
 * repositories is more than a handful of methods.
 */

class UserRepository {
  constructor(db) { this.db = db; }

  findByEmail(email) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email], (err, row) => {
        if (err) reject(new DatabaseError('Erro DB'));
        else resolve(row || null);
      });
    });
  }

  create({ name, email, passHash }) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passHash],
        function insertUserCallback(err) {
          if (err) reject(new DatabaseError('Erro ao criar usuário'));
          else resolve(this.lastID);
        },
      );
    });
  }

  /**
   * Faithfully reproduces the original's behaviour on src/AppManager.js:131-137: the driver
   * error is not surfaced to the caller. That is AP-09, and its fix is `PROPOSED, NOT
   * APPLIED` (see reports/audit-latest.md) because today's DELETE /api/users/:id has exactly
   * one observable outcome no matter what the database reports; changing that is a contract
   * change. This method therefore never rejects.
   */
  deleteById(id) {
    return new Promise((resolve) => {
      this.db.run('DELETE FROM users WHERE id = ?', [id], () => {
        resolve();
      });
    });
  }
}

class CourseRepository {
  constructor(db) { this.db = db; }

  findActiveById(id) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT id, title, price_cents, active FROM courses WHERE id = ? AND active = 1', [id], (err, row) => {
        if (err) reject(new DatabaseError('Erro DB'));
        else resolve(row || null);
      });
    });
  }

  findAll() {
    return new Promise((resolve, reject) => {
      this.db.all('SELECT id, title, price_cents, active FROM courses', [], (err, rows) => {
        if (err) reject(new DatabaseError('Erro DB'));
        else resolve(rows || []);
      });
    });
  }
}

class EnrollmentRepository {
  constructor(db) { this.db = db; }

  create({ userId, courseId }) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId],
        function insertEnrollmentCallback(err) {
          if (err) reject(new DatabaseError('Erro Matrícula'));
          else resolve(this.lastID);
        },
      );
    });
  }

  /** One set-based query for every course at once — resolves AP-10 (original: a query per course, inside a loop). */
  findByCourseIds(courseIds) {
    if (courseIds.length === 0) return Promise.resolve([]);
    const placeholders = courseIds.map(() => '?').join(', ');
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT id, user_id, course_id FROM enrollments WHERE course_id IN (${placeholders})`,
        courseIds,
        (err, rows) => {
          if (err) reject(new DatabaseError('Erro DB'));
          else resolve(rows || []);
        },
      );
    });
  }
}

class PaymentRepository {
  constructor(db) { this.db = db; }

  create({ enrollmentId, amountCents, status }) {
    return new Promise((resolve, reject) => {
      this.db.run(
        'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
        [enrollmentId, amountCents, status],
        function insertPaymentCallback(err) {
          if (err) reject(new DatabaseError('Erro Pagamento'));
          else resolve(this.lastID);
        },
      );
    });
  }

  /** One set-based query for every enrollment at once — resolves AP-10 (original: a query per enrollment, inside a loop). */
  findByEnrollmentIds(enrollmentIds) {
    if (enrollmentIds.length === 0) return Promise.resolve([]);
    const placeholders = enrollmentIds.map(() => '?').join(', ');
    return new Promise((resolve, reject) => {
      this.db.all(
        `SELECT id, enrollment_id, amount_cents, status FROM payments WHERE enrollment_id IN (${placeholders})`,
        enrollmentIds,
        (err, rows) => {
          if (err) reject(new DatabaseError('Erro DB'));
          else resolve(rows || []);
        },
      );
    });
  }
}

class AuditLogRepository {
  constructor(db) { this.db = db; }

  record(action) {
    return new Promise((resolve, reject) => {
      this.db.run(
        "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
        [action],
        (err) => {
          if (err) reject(new DatabaseError('Erro DB'));
          else resolve();
        },
      );
    });
  }
}

/** One set-based query for every user at once — resolves AP-10 alongside EnrollmentRepository/PaymentRepository above. */
UserRepository.prototype.findByIds = function findByIds(ids) {
  if (ids.length === 0) return Promise.resolve([]);
  const placeholders = ids.map(() => '?').join(', ');
  return new Promise((resolve, reject) => {
    this.db.all(`SELECT id, name, email FROM users WHERE id IN (${placeholders})`, ids, (err, rows) => {
      if (err) reject(new DatabaseError('Erro DB'));
      else resolve(rows || []);
    });
  });
};

module.exports = {
  UserRepository, CourseRepository, EnrollmentRepository, PaymentRepository, AuditLogRepository,
};
