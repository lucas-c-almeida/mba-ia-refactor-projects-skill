// Read model for the financial report: one query, aggregated in memory.
const { PAYMENT_STATUS, fromCents } = require('./payment');

const UNKNOWN_STUDENT = 'Unknown';

function createReportRepository(db) {
    return {
        async financialReport() {
            const rows = await db.all(
                `SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
                        u.id AS user_id, u.name AS student,
                        p.id AS payment_id, p.amount_cents, p.status
                   FROM courses c
                   LEFT JOIN enrollments e ON e.course_id = c.id
                   LEFT JOIN users u ON u.id = e.user_id
                   LEFT JOIN payments p ON p.id = (
                        SELECT MIN(p2.id) FROM payments p2 WHERE p2.enrollment_id = e.id)
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
                    // An enrollment whose user was deleted is still listed, as before.
                    student: row.user_id === null ? UNKNOWN_STUDENT : row.student,
                    paid: row.payment_id === null ? 0 : fromCents(row.amount_cents),
                });
            }

            return [...byCourse.values()].map(({ course, revenueCents, students }) => ({
                course,
                revenue: fromCents(revenueCents),
                students,
            }));
        },
    };
}

module.exports = { createReportRepository };
