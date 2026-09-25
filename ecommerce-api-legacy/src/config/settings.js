'use strict';

/**
 * Configuration — the only module in this codebase that reads process.env.
 * Everything else receives configuration; nothing else reads the environment.
 *
 * Resolves AP-01 (src/utils.js:1-7, original): no secret literal remains in source.
 * `PORT` is optional and defaults to the value the original application always used (3000),
 * so booting with no environment configured preserves the original's observable behaviour.
 *
 * The original config object also carried `dbUser`, `dbPass`, `smtpUser` and
 * `paymentGatewayKey` — none of them were ever read by any real integration. `dbUser`/
 * `dbPass` were never used at all (the app uses an in-memory sqlite3 database).
 * `paymentGatewayKey` was read only to be logged alongside the caller's full card number
 * (AppManager.js:45, original) — the separate AP-08 finding on that line; there is no
 * actual payment-gateway call anywhere in this codebase (see AP-15's finding on the
 * card-prefix heuristic that stands in for one). None of the four are carried forward:
 * keeping an unused field "required" would only fabricate a new deployment requirement,
 * and keeping it as a literal would leave the underlying finding unresolved under a
 * different name. If a real payment integration is added later, its credential belongs
 * here, required and read nowhere else — this module is exactly where it should be added.
 */

function loadSettings() {
  return Object.freeze({
    port: process.env.PORT ? Number(process.env.PORT) : 3000,
  });
}

module.exports = { loadSettings };
