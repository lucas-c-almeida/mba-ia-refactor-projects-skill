// Persistence for enrollments, their payments and the checkout audit trail.

function createEnrollmentRepository(db) {
    return {
        async create(userId, courseId) {
            const result = await db.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId],
            );
            return result.lastID;
        },

        async recordPayment(enrollmentId, amountCents, status) {
            await db.run(
                'INSERT INTO payments (enrollment_id, amount_cents, status) VALUES (?, ?, ?)',
                [enrollmentId, amountCents, status],
            );
        },

        // Append-only audit trail, read by operators outside the application.
        async recordAudit(action) {
            await db.run(
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [action],
            );
        },
    };
}

module.exports = { createEnrollmentRepository };
