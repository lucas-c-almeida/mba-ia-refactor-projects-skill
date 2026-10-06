'use strict';

class ReportController {
    constructor({ reports }) {
        this.reports = reports;
    }

    financialReport() {
        return this.reports.revenueByCourse();
    }
}

module.exports = { ReportController };
