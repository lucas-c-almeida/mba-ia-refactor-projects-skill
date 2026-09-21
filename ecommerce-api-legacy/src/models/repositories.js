// Persistence for the LMS entities (AP-03, AP-05 — RP-03). Every statement binds its values;
// no query is built from input. Repositories receive the Database; they never open one (AP-06).

const { PaymentStatus } = require('./payment');

class CourseRepository {
    constructor(db) { this.db = db; }

    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

class UserRepository {
    constructor(db) { this.db = db; }

    findIdByEmail(email) {
        return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return lastID;
    }

    deleteById(id) {
        return this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

// Enrollment, payment and audit record written as one unit of work (tx = transaction executor).
class EnrollmentRepository {
    async create(tx, { userId, courseId }) {
        const { lastID } = await tx.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
        return lastID;
    }

    recordPayment(tx, { enrollmentId, amount, status }) {
        return tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status]);
    }

    recordAudit(tx, action) {
        return tx.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
    }
}

// The financial report in two set-based queries, whatever the number of enrollments (AP-10 — RP-10).
// As before, each enrollment is matched with its first payment row only.
const FIRST_PAYMENT = 'p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)';

class ReportRepository {
    constructor(db) { this.db = db; }

    courseRevenue() {
        return this.db.all(
            `SELECT c.id, c.title,
                    COALESCE(SUM(CASE WHEN p.status = ? THEN p.amount END), 0) AS revenue
               FROM courses c
               LEFT JOIN enrollments e ON e.course_id = c.id
               LEFT JOIN payments p ON ${FIRST_PAYMENT}
              GROUP BY c.id
              ORDER BY c.id`,
            [PaymentStatus.PAID]);
    }

    enrollmentLines() {
        return this.db.all(
            `SELECT e.course_id, u.id AS user_id, u.name AS user_name,
                    p.id AS payment_id, p.amount AS payment_amount
               FROM enrollments e
               LEFT JOIN users u ON u.id = e.user_id
               LEFT JOIN payments p ON ${FIRST_PAYMENT}
              ORDER BY e.course_id, e.id`);
    }
}

module.exports = { CourseRepository, UserRepository, EnrollmentRepository, ReportRepository };
