'use strict';

const { PaymentStatus } = require('./payment');
const { fromCents } = require('./money');

const UNKNOWN_STUDENT = 'Unknown';

/**
 * One set-based query for the whole report (RP-10): every course, each of its enrollments with the
 * student and the enrollment's first payment. Ordered by course, then enrollment.
 */
const REPORT_QUERY = `
  SELECT c.id AS course_id, c.title AS course_title,
         e.id AS enrollment_id, u.name AS student_name,
         p.amount_cents AS amount_cents, p.status AS payment_status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.id = (SELECT MIN(id) FROM payments WHERE enrollment_id = e.id)
   ORDER BY c.id, e.id`;

class FinancialReportRepository {
  constructor(db) {
    this.db = db;
  }

  rows() {
    return this.db.all(REPORT_QUERY);
  }
}

/** Revenue counts PAID payments only; each enrollment lists what was paid (0 when no payment). */
function buildFinancialReport(rows) {
  const courses = new Map();
  for (const row of rows) {
    if (!courses.has(row.course_id)) {
      courses.set(row.course_id, { title: row.course_title, revenueCents: 0, students: [] });
    }
    const course = courses.get(row.course_id);
    if (row.enrollment_id === null) continue;
    const hasPayment = row.amount_cents !== null;
    if (hasPayment && row.payment_status === PaymentStatus.PAID) {
      course.revenueCents += row.amount_cents;
    }
    course.students.push({
      student: row.student_name ?? UNKNOWN_STUDENT,
      paidCents: hasPayment ? row.amount_cents : 0,
    });
  }
  return [...courses.values()].map((course) => ({
    course: course.title,
    revenue: fromCents(course.revenueCents),
    students: course.students.map((s) => ({ student: s.student, paid: fromCents(s.paidCents) })),
  }));
}

module.exports = { FinancialReportRepository, buildFinancialReport };
