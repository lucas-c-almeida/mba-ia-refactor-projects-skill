// Financial report use case (AP-05, AP-10 — RP-05, RP-10). Two queries regardless of data size;
// assembly of the report lines is pure and has no I/O.

const { DependencyError, GENERIC_DB_ERROR } = require('../models/errors');

const UNKNOWN_STUDENT = 'Unknown';

function toStudentLine(row) {
    return {
        student: row.user_id !== null ? row.user_name : UNKNOWN_STUDENT,
        paid: row.payment_id !== null ? row.payment_amount : 0,
    };
}

class ReportController {
    constructor({ reports }) {
        this.reports = reports;
    }

    async financialReport() {
        let courses;
        let lines;
        try {
            [courses, lines] = await Promise.all([
                this.reports.courseRevenue(),
                this.reports.enrollmentLines(),
            ]);
        } catch (err) {
            throw new DependencyError(GENERIC_DB_ERROR, err);
        }

        const byCourse = new Map(courses.map((c) => [c.id, { course: c.title, revenue: c.revenue, students: [] }]));
        for (const line of lines) {
            const entry = byCourse.get(line.course_id);
            if (entry) entry.students.push(toStudentLine(line));
        }
        return [...byCourse.values()];
    }
}

module.exports = { ReportController };
