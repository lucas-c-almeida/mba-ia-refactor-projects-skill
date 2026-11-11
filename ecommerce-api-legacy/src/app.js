// Composition root: load configuration, build the object graph, start the server.
const express = require('express');
const { loadConfig } = require('./config');
const { openDatabase } = require('./models/database');
const { initializeSchema } = require('./models/schema');
const { createUserRepository } = require('./models/userRepository');
const { createCourseRepository } = require('./models/courseRepository');
const { createEnrollmentRepository } = require('./models/enrollmentRepository');
const { createReportRepository } = require('./models/reportRepository');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRouter } = require('./routes');
const { requestId } = require('./middlewares/requestId');
const { createErrorHandler } = require('./middlewares/errorHandler');

// The datastore is in memory and seeded at every boot, as documented in the README.
const DATABASE_FILENAME = ':memory:';

async function main() {
    const config = loadConfig(process.env);
    const logger = console;

    const db = openDatabase(DATABASE_FILENAME);
    await initializeSchema(db, { seedUserPassword: config.seedUserPassword });

    const users = createUserRepository(db);
    const courses = createCourseRepository(db);
    const enrollments = createEnrollmentRepository(db);
    const reports = createReportRepository(db);

    const app = express();
    app.disable('x-powered-by');
    app.use(requestId);
    app.use(express.json());
    app.use(createRouter({
        checkout: createCheckoutController({ db, users, courses, enrollments, logger }),
        reports: createReportController({ reports }),
        users: createUserController({ users }),
        operatorToken: config.operatorToken,
    }));
    app.use(createErrorHandler(logger));

    app.listen(config.port, () => {
        logger.info(`LMS API rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    console.error(`Falha ao iniciar a aplicação: ${err.message}`);
    process.exit(1);
});
