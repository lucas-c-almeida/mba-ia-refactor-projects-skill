// One set-based query instead of a query per course, per enrollment and per payment (RP-10).
const REPORT_ROWS_SQL = `
    SELECT c.id AS course_id, c.title AS course_title,
           e.id AS enrollment_id, u.name AS user_name,
           p.amount AS payment_amount, p.status AS payment_status
      FROM courses c
      LEFT JOIN enrollments e ON e.course_id = c.id
      LEFT JOIN users u ON u.id = e.user_id
      LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
     ORDER BY c.id, e.id
`;

class ReportRepository {
    constructor(db) { this.db = db; }

    financialRows() {
        return this.db.all(REPORT_ROWS_SQL);
    }
}

module.exports = { ReportRepository };
