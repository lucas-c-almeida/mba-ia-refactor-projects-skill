const { DependencyError } = require('../errors');
const { PAYMENT_STATUS, toAmount } = require('../models/paymentPolicy');

const UNKNOWN_STUDENT = 'Unknown';

class ReportController {
    constructor({ reports }) { this.reports = reports; }

    async financialReport() {
        let rows;
        try {
            rows = await this.reports.financialRows();
        } catch (err) {
            throw new DependencyError('Erro DB', err);
        }

        const byCourse = new Map();
        for (const row of rows) {
            if (!byCourse.has(row.course_id)) {
                byCourse.set(row.course_id, { course: row.course_title, revenueCents: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const entry = byCourse.get(row.course_id);
            if (row.payment_status === PAYMENT_STATUS.PAID) entry.revenueCents += row.payment_amount;
            entry.students.push({
                student: row.user_name === null ? UNKNOWN_STUDENT : row.user_name,
                paid: row.payment_amount === null ? 0 : toAmount(row.payment_amount),
            });
        }

        return Array.from(byCourse.values(), (entry) => ({
            course: entry.course,
            revenue: toAmount(entry.revenueCents),
            students: entry.students,
        }));
    }
}

module.exports = { ReportController };
