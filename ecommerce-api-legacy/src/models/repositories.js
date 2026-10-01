'use strict';

const { fromCents } = require('./money');
const { PaymentStatus } = require('./payment');

// Data access, one small repository per concept. Every statement binds its values.

class CourseRepository {
    constructor(db) { this.db = db; }

    async findActiveById(id) {
        const row = await this.db.get(
            'SELECT id, title, price_cents FROM courses WHERE id = ? AND active = 1',
            [id],
        );
        return row ? { id: row.id, title: row.title, priceCents: row.price_cents } : undefined;
    }
}

class UserRepository {
    constructor(db) { this.db = db; }

    findIdByEmail(email) {
        return this.db.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
        );
        return lastID;
    }

    async deleteById(id) {
        await this.db.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

class EnrollmentRepository {
    constructor(db) { this.db = db; }

    async create(userId, courseId) {
        const { lastID } = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return lastID;
    }
}

class PaymentRepository {
    constructor(db) { this.db = db; }

    async create(enrollmentId, amountCents, status) {
        await this.db.run(
            'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
            [enrollmentId, amountCents, status],
        );
    }
}

class AuditLogRepository {
    constructor(db) { this.db = db; }

    async record(action) {
        await this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
    }
}

class FinancialReportRepository {
    constructor(db) { this.db = db; }

    // One set-based query instead of 1 + C + 2E round trips (AP-10, RP-10).
    async revenueByCourse() {
        const rows = await this.db.all(`
            SELECT c.id AS course_id, c.title AS course_title,
                   e.id AS enrollment_id, u.name AS student_name,
                   p.amount_cents AS amount_cents, p.status AS payment_status
              FROM courses c
              LEFT JOIN enrollments e ON e.course_id = c.id
              LEFT JOIN users u ON u.id = e.user_id
              LEFT JOIN payments p ON p.enrollment_id = e.id
             ORDER BY c.id, e.id`);

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { title: row.course_title, revenueCents: 0, students: [] });
            }
            const course = byCourse.get(row.course_id);
            if (row.enrollment_id === null) continue;
            const hasPayment = row.amount_cents !== null;
            if (hasPayment && row.payment_status === PaymentStatus.PAID) {
                course.revenueCents += row.amount_cents;
            }
            course.students.push({
                name: row.student_name,
                paidCents: hasPayment ? row.amount_cents : 0,
            });
        }
        return [...byCourse.values()].map((course) => ({
            title: course.title,
            revenue: fromCents(course.revenueCents),
            students: course.students.map((s) => ({ name: s.name, paid: fromCents(s.paidCents) })),
        }));
    }
}

module.exports = {
    CourseRepository,
    UserRepository,
    EnrollmentRepository,
    PaymentRepository,
    AuditLogRepository,
    FinancialReportRepository,
};
