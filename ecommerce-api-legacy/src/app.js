'use strict';

const express = require('express');
const { loadConfig } = require('./config');
const { Database } = require('./models/database');
const { initSchema } = require('./models/schema');
const {
  UserRepository, CourseRepository, EnrollmentRepository, PaymentRepository, AuditLogRepository, FinancialReportRepository,
} = require('./models/repositories');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const { createOperatorGuard } = require('./middlewares/operatorGuard');
const { errorBoundary } = require('./middlewares/errorBoundary');
const { registerRoutes } = require('./routes');

const DATABASE_FILE = ':memory:';

/** Composition root: the only place that names concrete implementations and wires them. */
async function createApp(config) {
  const db = await Database.open(DATABASE_FILE);
  await initSchema(db);

  const users = new UserRepository(db);
  const courses = new CourseRepository(db);
  const controllers = {
    checkout: new CheckoutController({
      db, users, courses, enrollments: new EnrollmentRepository(), payments: new PaymentRepository(), auditLogs: new AuditLogRepository(),
    }),
    reports: new ReportController({ reports: new FinancialReportRepository(db) }),
    users: new UserController({ users }),
  };

  const app = express();
  app.use(express.json());
  registerRoutes(app, { ...controllers, requireOperator: createOperatorGuard(config.operatorToken) });
  app.use(errorBoundary());
  return app;
}

async function main() {
  const config = loadConfig();
  const app = await createApp(config);
  app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
  });
}

if (require.main === module) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { createApp };
