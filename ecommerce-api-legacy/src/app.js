'use strict';

// Composition root (RP-06): the only place that names concrete implementations, wires them
// together and starts the server. Importing this module has no side effects.

const express = require('express');
const { loadConfig } = require('./config');
const { Database } = require('./models/database');
const { initializeSchema } = require('./models/schema');
const { UserRepository } = require('./models/userRepository');
const { CourseRepository } = require('./models/courseRepository');
const { EnrollmentRepository } = require('./models/enrollmentRepository');
const { FinancialReportRepository } = require('./models/financialReport');
const { CheckoutController } = require('./controllers/checkoutController');
const { ReportController } = require('./controllers/reportController');
const { UserController } = require('./controllers/userController');
const { buildRouter } = require('./views/routes');
const { requireOperator } = require('./middlewares/requireOperator');
const { errorHandler } = require('./middlewares/errorHandler');

function createApp({ config, db, logger = console }) {
  const users = new UserRepository(db);

  const app = express();
  app.use(express.json());
  app.use(buildRouter({
    checkout: new CheckoutController({
      users,
      courses: new CourseRepository(db),
      enrollments: new EnrollmentRepository(db),
      logger,
    }),
    reports: new ReportController({ reports: new FinancialReportRepository(db) }),
    users: new UserController({ users }),
    requireOperator: requireOperator(config.operatorToken),
  }));
  app.use(errorHandler(logger));
  return app;
}

async function start() {
  const config = loadConfig();
  const db = await Database.open(config.databaseFile);
  await initializeSchema(db);
  const app = createApp({ config, db });
  app.listen(config.port, () => {
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
  });
}

if (require.main === module) {
  start().catch((err) => {
    console.error('startup failed', err);
    process.exitCode = 1;
  });
}

module.exports = { createApp };
