'use strict';

const { buildFinancialReport } = require('../models/financialReport');
const { PersistenceError } = require('../models/errors');

class ReportController {
  constructor({ reports }) {
    this.reports = reports;
  }

  async financialReport() {
    let rows;
    try {
      rows = await this.reports.rows();
    } catch (err) {
      throw new PersistenceError('Erro DB', err);
    }
    return buildFinancialReport(rows);
  }
}

module.exports = { ReportController };
