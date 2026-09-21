// Financial report use case. (AP-05 -> RP-05)
const { buildFinancialReport } = require('../models/financialReport');
const { DependencyError, DB_ERROR_MESSAGE } = require('../models/errors');

class ReportController {
    constructor({ financialReports }) {
        this.financialReports = financialReports;
    }

    async financialReport() {
        let rows;
        try {
            rows = await this.financialReports.fetchRows();
        } catch (err) {
            throw new DependencyError(DB_ERROR_MESSAGE, err);
        }
        return buildFinancialReport(rows);
    }
}

module.exports = { ReportController };
