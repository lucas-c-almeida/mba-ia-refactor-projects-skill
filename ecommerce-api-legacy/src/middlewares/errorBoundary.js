'use strict';

const { AppError } = require('../errors');

/**
 * The one centralized error-handling boundary in the application — resolves AP-09 (original:
 * every handler in src/AppManager.js repeated its own `if (err) return
 * res.status(500).send(...)`, and one handler — DELETE /api/users/:id — skipped this
 * entirely; see the separate finding on that route, which stays `PROPOSED, NOT APPLIED`).
 *
 * Also resolves AP-18 (original: no error middleware was registered at all, so Express's
 * own default handler answered with a full HTML stack trace — observed directly in Phase 2;
 * see reports/audit-latest.md). Replacing that default page is safe *only* because the
 * status code Express itself already chose (e.g. 400 for a malformed JSON body) is
 * preserved — see `04-architecture-guidelines.md` §6, "the error contract".
 *
 * Every application error keeps the exact status and body text the original sent for that
 * case (`res.send(<text>)`, not JSON — the original never returned JSON error bodies, and
 * changing that would be a contract change nobody asked for). Only the previously-unhandled
 * path — the framework's own default page — is replaced, with a generic body, at whatever
 * status the failure already carries.
 */
module.exports = function errorBoundary(err, req, res, _next) { // eslint-disable-line no-unused-vars
  if (err instanceof AppError) {
    res.status(err.status).send(err.message);
    return;
  }

  // Anything else — including body-parser's JSON SyntaxError, which carries its own status —
  // is something this application did not raise on purpose. Log full detail internally
  // (left to the process's own stdout/stderr here, as the original did); disclose nothing
  // internal externally.
  const status = err.status || err.statusCode || 500;
  console.error(`[error] ${req.method} ${req.originalUrl}: ${err.message}`);
  res.status(status).send(status === 400 ? 'Bad Request' : 'Internal Server Error');
};
