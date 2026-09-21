// Financial report: one set-based query instead of 1 + C + 2E round trips. (AP-10 -> RP-10)
const { PAYMENT_STATUS } = require('./payment');

const UNKNOWN_STUDENT = 'Unknown';

// One row per (course, enrollment); a course without enrollments yields one row with NULL enrollment.
// For each enrollment, only its first payment is considered — the original read a single payment row.
const REPORT_QUERY = `
    SELECT c.id AS course_id, c.title AS course_title,
           e.id AS enrollment_id, u.name AS student_name,
           p.amount AS payment_amount, p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.id = (
            SELECT MIN(p2.id) FROM payments p2 WHERE p2.enrollment_id = e.id)
     ORDER BY c.id, e.id`;

class FinancialReportRepository {
    constructor(db) {
        this.db = db;
    }

    fetchRows() {
        return this.db.all(REPORT_QUERY);
    }
}

// Pure aggregation, testable without a database.
function buildFinancialReport(rows) {
    const byCourse = new Map();
    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue;
        const entry = byCourse.get(row.course_id);
        const hasPayment = row.payment_amount !== null;
        if (hasPayment && row.payment_status === PAYMENT_STATUS.PAID) {
            entry.revenue += row.payment_amount;
        }
        entry.students.push({
            student: row.student_name !== null ? row.student_name : UNKNOWN_STUDENT,
            paid: hasPayment ? row.payment_amount : 0,
        });
    }
    return [...byCourse.values()];
}

module.exports = { FinancialReportRepository, buildFinancialReport };
