'use strict';

/** The financial report use case. */
class ReportController {
  constructor({ reports }) {
    this.reports = reports;
  }

  financialReport() {
    return this.reports.build();
  }
}

module.exports = { ReportController };
