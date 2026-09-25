'use strict';

const express = require('express');
const sqlite3 = require('sqlite3').verbose();

const { loadSettings } = require('./config/settings');
const { initSchema } = require('./models/db');
const {
  UserRepository, CourseRepository, EnrollmentRepository, PaymentRepository, AuditLogRepository,
} = require('./models/repositories');
const { CheckoutController } = require('./controllers/checkoutController');
const { FinancialReportController } = require('./controllers/financialReportController');
const { UserController } = require('./controllers/userController');
const { checkoutRoutes } = require('./routes/checkoutRoutes');
const { financialReportRoutes } = require('./routes/financialReportRoutes');
const { userRoutes } = require('./routes/userRoutes');
const errorBoundary = require('./middlewares/errorBoundary');

/**
 * Composition root — resolves AP-06 (original: src/AppManager.js's constructor opened its
 * own database connection, and src/app.js wired the class directly with no factory). This
 * is the only place that names concrete implementations; nothing else in the codebase
 * constructs its own infrastructure or has a side effect at import time.
 */
async function createApp() {
  const settings = loadSettings();

  const db = new sqlite3.Database(':memory:');
  await initSchema(db);

  const users = new UserRepository(db);
  const courses = new CourseRepository(db);
  const enrollments = new EnrollmentRepository(db);
  const payments = new PaymentRepository(db);
  const auditLogs = new AuditLogRepository(db);

  const checkoutController = new CheckoutController({
    users, courses, enrollments, payments, auditLogs,
  });
  const financialReportController = new FinancialReportController({
    courses, enrollments, users, payments,
  });
  const userController = new UserController({ users });

  const app = express();
  app.use(express.json());
  app.use(checkoutRoutes(checkoutController));
  app.use(financialReportRoutes(financialReportController));
  app.use(userRoutes(userController));
  app.use(errorBoundary); // registered last, per Express convention

  return { app, settings, db };
}

/* istanbul ignore next -- exercised by booting the process, not by a unit test */
if (require.main === module) {
  createApp().then(({ app, settings }) => {
    app.listen(settings.port, () => {
      console.log(`Frankenstein LMS rodando na porta ${settings.port}...`);
    });
  }).catch((err) => {
    console.error('failed to start:', err);
    process.exitCode = 1;
  });
}

module.exports = { createApp };
