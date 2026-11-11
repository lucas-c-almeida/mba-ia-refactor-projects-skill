// Use case: the management financial report.
const { DependencyError } = require('../models/errors');

function createReportController({ reports }) {
    return {
        async financialReport() {
            try {
                return await reports.financialReport();
            } catch (err) {
                throw new DependencyError('Erro DB', err);
            }
        },
    };
}

module.exports = { createReportController };
