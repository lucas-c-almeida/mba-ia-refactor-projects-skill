class EnrollmentRepository {
    constructor(db) { this.db = db; }

    async insertEnrollment(userId, courseId) {
        const result = await this.db.run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
        );
        return result.lastID;
    }

    insertPayment(enrollmentId, amountCents, status) {
        return this.db.run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amountCents, status],
        );
    }

    insertAuditLog(action) {
        return this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
    }
}

module.exports = { EnrollmentRepository };
