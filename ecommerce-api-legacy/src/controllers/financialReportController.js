'use strict';

const { fromCents } = require('../models/money');
const { PAID } = require('../models/checkoutPolicy');

/**
 * The financial report use case — resolves AP-10 (original: src/AppManager.js:80-129, a
 * query per course, then a query per enrollment, then two more queries per enrollment,
 * nested three loops deep). Three set-based queries total, regardless of how many courses
 * or enrollments exist, assembled here into the same shape the original returned (see
 * reports/baseline.json, entry `financial-report`).
 *
 * No authorization is added here — see the AP-04 finding in reports/audit-latest.md: this
 * route has no identity model to check against, so a new rejection would reject every
 * current (anonymous) caller. That fix is `PROPOSED, NOT APPLIED`.
 */
class FinancialReportController {
  constructor({
    courses, enrollments, users, payments,
  }) {
    this.courses = courses;
    this.enrollments = enrollments;
    this.users = users;
    this.payments = payments;
  }

  async report() {
    const courses = await this.courses.findAll();
    const courseIds = courses.map((c) => c.id);

    const enrollments = await this.enrollments.findByCourseIds(courseIds);
    const enrollmentIds = enrollments.map((e) => e.id);

    const [users, payments] = await Promise.all([
      this.users.findByIds([...new Set(enrollments.map((e) => e.user_id))]),
      this.payments.findByEnrollmentIds(enrollmentIds),
    ]);

    const userById = new Map(users.map((u) => [u.id, u]));
    const paymentByEnrollmentId = new Map(payments.map((p) => [p.enrollment_id, p]));
    const enrollmentsByCourseId = new Map();
    for (const enrollment of enrollments) {
      const list = enrollmentsByCourseId.get(enrollment.course_id) || [];
      list.push(enrollment);
      enrollmentsByCourseId.set(enrollment.course_id, list);
    }

    return courses.map((course) => {
      const courseEnrollments = enrollmentsByCourseId.get(course.id) || [];
      let revenueCents = 0;
      const students = courseEnrollments.map((enrollment) => {
        const user = userById.get(enrollment.user_id);
        const payment = paymentByEnrollmentId.get(enrollment.id);
        if (payment && payment.status === PAID) revenueCents += payment.amount_cents;
        return {
          student: user ? user.name : 'Unknown',
          paid: payment ? fromCents(payment.amount_cents) : 0,
        };
      });
      return { course: course.title, revenue: fromCents(revenueCents), students };
    });
  }
}

module.exports = { FinancialReportController };
