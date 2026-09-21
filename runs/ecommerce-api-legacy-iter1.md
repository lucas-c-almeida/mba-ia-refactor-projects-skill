# Run ecommerce-api-legacy/iter1 — `/refactor-arch ecommerce-api-legacy --yes`

Date: 2026-09-21 · Executed by a subagent session (fresh context) on branch `round1` · Confirmation mode: `--yes` (auto-approved, not human-reviewed) · Boot port for baseline/replay: 5102 (via `PORT` env; the original hardcoded 3000, so the baseline boot used a scratchpad preload that overrode the in-memory config object — no project file touched).

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        ecommerce-api-legacy
Language:      JavaScript (CommonJS) — Node.js v24.12.0 (installed runtime; no engines field)
Framework:     Express 4.22.1 (resolved in package-lock.json; manifest range ^4.18.2)
Dependencies:  express ^4.18.2 (4.22.1), sqlite3 ^5.1.6 (5.1.7) — runtime only, no devDependencies
Domain:        LMS course sales — checkout (buyer find-or-create, simulated card payment, enrollment), admin financial report, user deletion
App type:      HTTP service — POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id
Architecture:  None — one class (src/AppManager.js) holds schema/seed, queries, business rules and route registration; src/utils.js is a grab-bag of config, cache and "crypto"
Source files:  3 files analyzed (src/*.js, 180 lines; excluded node_modules/, lockfile, api.http, README)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite :memory:, DDL + seed at boot)
================================
Boot command:  npm start → node src/app.js (cwd = target); port hardcoded 3000 in src/utils.js; in-memory DB seeded on boot
```

## Phase 2 + Phase 3 output (verbatim copy of ecommerce-api-legacy/reports/audit-latest.md)

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v24.12.0) + Express 4.22.1 (lockfile) + sqlite3 5.1.7 (lockfile)
Files:   3 analyzed | ~180 lines of code
Date:    2026-09-21 00:07
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: A module-level `config` object holds string literals for `dbPass` ("senha_super_secreta_prod_123"), `paymentGatewayKey` (a `pk_live_`-prefixed literal), `dbUser` and `smtpUser`, plus the listening port. The gateway key is also interpolated into a log line at src/AppManager.js:45-45. There is no environment read anywhere in the codebase.
Impact: Anyone with read access to the repository holds a live-looking payment-gateway key and a production-named database password; rotation requires a code change and redeploy, and the values remain in git history forever.
Recommendation: Move every secret and environment-specific value to a single config module that reads the environment once and fails at startup when a required secret is absent; add `.env.example` with placeholders; rotate the committed values (owner action). See RP-01.
Contract: safe

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:4-139
Description: One class holds (a) persistence — connection creation (L7), DDL and seed data (L10-23), every query; (b) business rules — payment approval, find-or-create user, enrollment/payment/audit workflow, revenue aggregation (L28-129); (c) delivery — route registration and request parsing for all three endpoints (L25-137); (d) presentation — response strings and JSON shaping. Escalated context: it also contains the sensitive-data handling of AP-08 and every request passes through it.
Impact: No rule can be tested without a live database and an Express app; any change to any endpoint has a blast radius covering the whole application.
Recommendation: Split by responsibility into config / models (repositories) / controllers / routes / middlewares with a composition root. See RP-03.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/AppManager.js:80-137
Description: `GET /api/admin/financial-report` (L80-129) returns every student's name and amount paid per course, and `DELETE /api/users/:id` (L131-137) deletes any user by path id; neither has any authentication or authorization check, and no auth mechanism exists anywhere in the codebase. Flagged maximum urgency: one operation is destructive, the other exposes personal and financial data.
Impact: Any anonymous caller can read the revenue report with student names, or delete arbitrary accounts by iterating ids.
Recommendation: Introduce an authentication mechanism and an admin guard on both routes. See RP-04. There is no principal model in the code to derive a policy from, so the policy cannot be applied without inventing one.
Contract: contract-changing: currently-anonymous callers of both routes would start receiving 401/403.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data (password storage)   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` "hashes" a password by repeating the first two base64 characters of the input and truncating to 10 characters — the result depends only on the first ~1.5 bytes of the password and is trivially reversible for that prefix; the 10000-iteration loop adds cost but no security. It is used at src/AppManager.js:68-68, which also silently assigns the literal default password "123456" when `pwd` is absent, and the seed row stores the plaintext password '123' (src/AppManager.js:18-18). Escalated from HIGH to CRITICAL: passwords are stored recoverably.
Impact: A single read of the users table reveals password prefixes and makes any two passwords with the same first characters collide; accounts created without a password share a known credential.
Recommendation: Replace with a purpose-built password KDF from the runtime's standard library (e.g. salted scrypt via `node:crypto`), stored with its salt. See RP-08. Removing the default-password fallback would require making `pwd` mandatory — proposed separately.
Contract: safe (hash format is never returned by any endpoint); the default-password removal is contract-changing (a previously accepted request without `pwd` would be rejected).

### [CRITICAL] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:50-61
Description: The checkout issues three dependent writes (enrollment L50, payment L54, audit log L57) with no transaction: a failure after the first leaves an enrollment without payment. The audit-log callback ignores its `err` and returns 200 regardless (L57-60). The delete handler ignores `err` and always reports success (L133-135). In the report, nested query errors are ignored (L92, L104, L106) and `enrollments.length` on an errored query throws inside a driver callback, which crashes the process. No error middleware exists; every handler hand-maps errors to text. Escalated from HIGH to CRITICAL: swallowed failures silently discard persisted writes.
Impact: The API reports success while writes are lost or half-applied; one database error in the report path takes the whole server down.
Recommendation: Wrap the checkout writes in one transaction, propagate every driver error, and centralize error-to-response mapping in one Express error middleware preserving the existing status codes and messages. See RP-09.
Contract: safe (success paths and existing status/body shapes preserved; only previously swallowed failures become visible 500s)

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: src/AppManager.js:28-78
Description: The `POST /api/checkout` route closure contains the payment-approval rule (`cc.startsWith("4")`, L46), the find-or-create-user decision (L66-75), password hashing and the enrollment→payment→audit workflow, issuing driver calls directly from the handler. The financial-report handler (L80-129) likewise computes revenue in the route.
Impact: The checkout rule cannot be tested or reused (e.g. from a batch job) without an HTTP server; changing transport means rewriting business rules.
Recommendation: Extract a checkout use case and a report use case into controllers that take plain values; routes become parse → call → render. See RP-05.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:1-8
Description: The class constructs its own database connection (`new sqlite3.Database(':memory:')`, L7) and reads configuration by importing the module-level `config` singleton (L2). src/app.js:1-14 mixes wiring and start-up with no seam; the store location is a literal.
Impact: No unit can be instantiated with a test double; swapping the datastore means editing the class.
Recommendation: A composition root that loads config, opens the database, constructs repositories and controllers, and registers routes. See RP-06.
Contract: safe

### [HIGH] Unsafe Handling of Credentials and Sensitive Data (logging)   (AP-08)
File: src/AppManager.js:45-45
Description: Every checkout logs the full card number and the payment-gateway key: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`. Kept at HIGH (not escalated): no evidence in the code that stdout is shipped off-host.
Impact: Full card numbers and the gateway secret end up in whatever collects stdout, with weaker access control than the database.
Recommendation: Remove the secret from the log and mask the card number (last 4 digits only). See RP-08.
Contract: safe (logs are not part of the public surface)

### [HIGH] Missing Boundary Validation (process crash on malformed input)   (AP-11)
File: src/AppManager.js:29-46
Description: Request fields are only truthiness-checked (L35). A non-string `card` makes `cc.startsWith` (L46) throw, and a non-string `pwd` makes `Buffer.from` inside `badCrypto` throw, both inside driver callbacks, where the exception is uncaught and terminates the process. Escalated from MEDIUM to HIGH: a single malformed request is a denial of service for all clients.
Impact: Any client can crash the server with `{"card": 4111...}` (a JSON number).
Recommendation: Validate types at the boundary and reject unambiguously invalid input (non-string card/password) with the existing 400 "Bad Request" response. See RP-11. Stricter rules (email format, positive integer course id) would reject requests currently accepted and are proposed only.
Contract: safe for type checks (the request previously got no response at all); contract-changing for stricter format rules.

### [HIGH] Missing Boundary Validation (domain invariant: orphaned records)   (AP-11)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes the user row but leaves that user's enrollments and payments — the response text itself says so ("as matrículas e pagamentos ficaram sujos no banco"). It also reports success for an id that does not exist. Escalated from MEDIUM to HIGH: the missing invariant persists corrupt domain state (the financial report then shows "Unknown" students).
Impact: Referential integrity is violated on every delete; financial history references non-existent users.
Recommendation: Decide the business rule (cascade, soft-delete, or refuse deletion while payments exist) and enforce it in one transaction; return 404 for unknown ids. See RP-11/RP-09.
Contract: contract-changing: the report's student list and revenue would change after a delete, and unknown ids would get 404 instead of 200 — a product/accounting decision.

### [HIGH] Deprecated or End-of-Life API Usage (runtime dependency advisories)   (AP-14)
File: package.json:10-13
Description: Evidence tier B (npm audit against the GitHub Advisory Database, looked up 2026-09-21): express 4.22.1 resolves runtime transitives with open advisories — path-to-regexp 0.1.12 (high, ReDoS, GHSA-37ch-88jc-xwx2), qs 6.14.2 (moderate, several DoS advisories), body-parser 1.20.4 (low, GHSA-v422-hmwv-36x6). The direct packages themselves are not flagged: `npm view express@4.22.1 deprecated` and OSV.dev for express@4.22.1 returned nothing. Escalated from MEDIUM to HIGH: advisories on code in the request path.
Impact: Request-path libraries with known DoS advisories stay exploitable until the lockfile is refreshed.
Recommendation: `npm audit fix` (non-breaking, within the declared `^4.18.2` range) to move to the patched path-to-regexp/qs/body-parser releases. See RP-14.
Contract: safe when replay confirms identical behaviour

### [MEDIUM] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: A module-level `globalCache` object is written on every successful checkout (`last_checkout_<userId>`) and never read, evicted or bounded; `totalRevenue` is a module-level mutable exported alongside it. De-escalated from HIGH to MEDIUM: nothing reads the cache, so no behaviour depends on execution history; the remaining impact is unbounded growth (AP-13) and dead state.
Impact: Memory grows with every distinct buyer for the life of the process; the exported mutable invites future order-dependent bugs.
Recommendation: Delete the write-only cache and counter. See RP-07 / RP-16.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-127
Description: The financial report reads all courses, then per course queries enrollments (L92), then per enrollment queries the user (L104) and the payment (L106): 1 + C + 2E round trips, coordinated with hand-maintained pending counters. The whole dataset is read with no bound (pagination would be a contract change and is not recommended here).
Impact: Latency grows linearly with enrollments; the counter-based coordination is fragile (see AP-09).
Recommendation: One set-based query with LEFT JOINs, aggregated in a model function. See RP-10.
Contract: safe (same shape)

### [MEDIUM] Deprecated or End-of-Life API Usage (install-time toolchain)   (AP-14)
File: package.json:12-12
Description: Evidence tier B (npm registry deprecation metadata emitted during `npm ci`, and npm audit, looked up 2026-09-21): sqlite3 5.1.7 pulls a build/install chain with registry-deprecated packages — tar 6.2.1 ("Old versions of tar are not supported… contain widely publicized security vulnerabilities"), glob 7.2.3, inflight 1.0.6, rimraf 3.0.2, npmlog 6.0.2, gauge 4.0.4, are-we-there-yet 3.0.1, prebuild-install 7.1.3, @npmcli/move-file 1.1.2 — and tar 6.2.1 carries critical advisories (e.g. GHSA-34x7-hfp2-rc4v). `npm view sqlite3@5.1.7 deprecated` and OSV.dev for sqlite3@5.1.7 returned nothing for the package itself. Kept at MEDIUM: these run at install time, not in the request path.
Impact: Every install extracts downloaded archives with a tar version under critical path-traversal advisories.
Recommendation: Upgrade sqlite3 to 6.0.1, the version npm audit names as the fix (major bump; verify by replay). See RP-14.
Contract: safe when replay confirms identical behaviour

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-48
Description: The approval rule is the bare literal `"4"` prefix; payment status strings `'PAID'`/`'DENIED'` are repeated literals (L18-21 seed, L46, L48, L108); default password `"123456"` (L68); `10000`/`10` in src/utils.js:19-22; port `3000` in src/utils.js:6.
Impact: The approval rule and status vocabulary are maintained by memory across sites.
Recommendation: Named constants for payment statuses and the approval rule; port to configuration. See RP-15.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:26-33
Description: Single-letter locals (`u`, `e`, `p`, `cid`, `cc`), `self`/`this` mixed in the same closure chain (L26, L54), `logAndCache` doing two things, `badCrypto`/`AppManager` naming, and mixed Portuguese/English identifiers and messages. (The request field names `usr`/`eml`/`pwd`/`c_id` are public contract and out of scope.)
Impact: Readers must trace every variable to know what it holds.
Recommendation: Rename internals for intent. See RP-16.
Contract: safe (internals only)

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/utils.js:10-25
Description: `totalRevenue` is exported (L25) and imported in src/AppManager.js:2 but never used; `config.dbUser`, `config.dbPass` and `config.smtpUser` are never read; `globalCache` is exported and never imported; the report query selects `email` (src/AppManager.js:104) and never uses it.
Impact: Readers assume these values matter (e.g. that a DB password is used somewhere).
Recommendation: Delete. See RP-16.
Contract: safe

## Deprecated API Verification

| Item | Version in use | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|
| Node runtime deprecations (boot + all surface requests) | v24.12.0 | A (detectors forced on) | `node --pending-deprecation --trace-deprecation --trace-warnings` | n/a — local | no warning emitted |
| express | 4.22.1 | B | `npm view express@4.22.1 deprecated`; OSV.dev `/v1/query` | 2026-09-21 | not deprecated; no direct advisory |
| express transitives (path-to-regexp 0.1.12, qs 6.14.2, body-parser 1.20.4) | as listed | B | npm audit (GitHub Advisory DB) | 2026-09-21 | AP-14 (HIGH) |
| sqlite3 | 5.1.7 | B | `npm view sqlite3@5.1.7 deprecated`; OSV.dev `/v1/query` | 2026-09-21 | not deprecated; no direct advisory |
| sqlite3 install chain (tar 6.2.1 et al.) | as listed | B | npm registry deprecation metadata (`npm ci`); npm audit | 2026-09-21 | AP-14 (MEDIUM) |

## Verification Coverage
Full — all planned checks executed. Layer-1 forced deprecation warnings covered boot and every request path in the surface inventory (the baseline capture ran with `--pending-deprecation --trace-deprecation --trace-warnings`): no runtime deprecation warning was emitted. Layer-2 live lookups (npm registry, OSV.dev, npm audit) ran on 2026-09-21.
Note: `npm ci` was run inside the target to obtain installed metadata and boot the app; node_modules/ is ignored by the repository root .gitignore, and package-lock.json was not modified by it.
Note: the AP-11 (HIGH) process crash was also observed at runtime during baseline capture (TypeError: cc.startsWith is not a function, src/AppManager.js:46).

## Proposed, Not Applied
To be determined in Phase 3.

================================
Total: 17 findings
================================

Phase 2 complete. Confirmation: --yes passed — proceeding as `y` without prompting.

---

# Phase 3 — Final Report (appended after refactoring)

Confirmation: --yes (auto-approved, not human-reviewed) · Scope applied: all findings (as `y`), contract gate enforced.
Layout chosen: `src/` with `config/`, `models/` (repositories live inside the model layer), `controllers/`, `routes/` (the View layer of this JSON/plain-text API), `middlewares/`, and `src/app.js` as composition root (kept at the path `package.json` `main`/`start` already name).

## Finding → transformation map

| # | Finding | Transformation | Status |
|---|---|---|---|
| 1 | [CRITICAL] AP-01 Hardcoded secrets (src/utils.js:1-7) | RP-01 — `src/config/index.js` reads `PORT`/`DB_PATH` once; unused secret literals deleted; `.env.example` added | Resolved. **Owner action: rotate the committed DB password and gateway key — they remain in git history.** |
| 2 | [CRITICAL] AP-03 God Class (src/AppManager.js) | RP-03 — split into models / controllers / routes / middlewares | Resolved; file removed |
| 3 | [CRITICAL] AP-04 Missing authorization | RP-04 | PROPOSED, NOT APPLIED |
| 4 | [CRITICAL] AP-08 Password storage | RP-08 — salted scrypt (`src/models/password.js`), seed password hashed | Resolved; default-password removal PROPOSED |
| 5 | [CRITICAL] AP-09 Swallowed errors / no transaction | RP-09 — `src/middlewares/errorHandler.js`, domain errors in `src/models/errors.js`, checkout writes in one transaction (`Database.transaction`) | Resolved; course-lookup 404-on-DB-error PROPOSED |
| 6 | [HIGH] AP-05 Logic in delivery layer | RP-05 — `CheckoutController`, `ReportController`, `UserController` | Resolved |
| 7 | [HIGH] AP-06 No composition root | RP-06 — `src/app.js` `buildApp({ db, logger })` | Resolved |
| 8 | [HIGH] AP-08 Card number + key logged | RP-08 — log shows `****<last4>` only | Resolved |
| 9 | [HIGH] AP-11 Crash on non-string input | RP-11 — non-string card (and non-string pwd for a new buyer) → existing 400 "Bad Request" | Resolved; stricter rules PROPOSED |
| 10 | [HIGH] AP-11 Orphaned records on delete | RP-11 | PROPOSED, NOT APPLIED |
| 11 | [HIGH] AP-14 Runtime transitive advisories | RP-14 — express `^4.22.3` (path-to-regexp 0.1.13, qs 6.16.0, body-parser 1.20.8); `npm audit`: 0 vulnerabilities (2026-09-21) | Resolved |
| 12 | [MEDIUM] AP-07 Global cache/counter | RP-07/RP-16 — deleted | Resolved |
| 13 | [MEDIUM] AP-10 N+1 report | RP-10 — one LEFT JOIN query + pure `buildFinancialReport` | Resolved |
| 14 | [MEDIUM] AP-14 Install-time deprecated chain | RP-14 — sqlite3 `^6.0.1` (tar 7.5.22; glob/inflight/rimraf/npmlog/gauge/are-we-there-yet/@npmcli/move-file gone) | Partially resolved — `prebuild-install@7.1.3` (still required by sqlite3 6.0.1, the latest release) remains registry-deprecated → unresolved |
| 15 | [LOW] AP-15 Magic values | RP-15 — `PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`, `DEFAULT_PASSWORD`, `SALT_BYTES`/`KEY_BYTES`, `DEFAULT_PORT` | Resolved |
| 16 | [LOW] AP-16 Names | RP-16 — intent-revealing internals; public field names untouched | Resolved |
| 17 | [LOW] AP-17 Dead code | RP-16 — `totalRevenue`, `globalCache`, unused config keys, unused `email` column removed | Resolved |

Additional issue found during refactoring (not in the Phase 2 list — an audit miss): a malformed JSON body reached the framework's default error page, which returns a stack trace with absolute server paths in the 400 body (observed on the original with curl). The central error boundary now answers the same 400 / text/html with "Bad Request". Resolved.

Preserved on purpose (behaviour, not defects): a new user is created even when the card is then declined; an existing buyer's `usr`/`pwd` are ignored; the report lists inactive courses too; plain-text error bodies and their Portuguese messages are unchanged. The original's report ordering depended on callback completion order; the new query orders by course id then enrollment id (order is not part of the compared contract).

## Proposed, Not Applied

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/routes/adminRoutes.js:5-17, src/routes/userRoutes.js:8-21
Reason not applied: adding authentication makes today's anonymous callers receive 401/403 on both routes; and the codebase has no principal model, so any policy would be invented.
Proposed change: introduce an authentication mechanism (token or session) and an admin guard middleware on `/api/admin/*` and `DELETE /api/users/:id`; coordinate with every consumer of these routes.

### [HIGH] Unsafe Handling of Credentials — default password for new buyers   (AP-08)
File: src/controllers/checkoutController.js:9-11
Reason not applied: removing the "123456" fallback means a checkout without `pwd` for a new email is rejected (400) — a previously optional parameter becomes required.
Proposed change: require `pwd` for new buyers, or create the account with no usable credential and send a set-password flow.

### [HIGH] Missing Boundary Validation — orphaned records on user delete   (AP-11)
File: src/controllers/userController.js:10-18
Reason not applied: cascading or blocking the delete changes the financial report's student list/revenue after a delete, and answering 404 for unknown ids changes a 200 into a 404. Deleting payment records is also an accounting decision.
Proposed change: decide cascade vs. soft-delete vs. refuse-while-paid; enforce it in the existing transaction; return 404 for unknown ids.

### [MEDIUM] Swallowed or Uncentralized Error Handling — lookup failure reported as not found   (AP-09)
File: src/controllers/checkoutController.js:44-51
Reason not applied: the original answers 404 "Curso não encontrado" when the course lookup itself fails; changing it to 500 changes an observed status code.
Proposed change: map a failed course lookup to DependencyError (500 "Erro DB").

### [MEDIUM] Missing Boundary Validation — format rules   (AP-11)
File: src/routes/checkoutRoutes.js:6-18
Reason not applied: validating `eml` format, `c_id` as a positive integer and `card` as digits would reject requests the API accepts today.
Proposed change: a declarative boundary schema with these rules, rolled out with client coordination.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── README.md
├── api.http
├── package.json
├── package-lock.json
├── reports/
│   ├── audit-20260921-0007.md
│   ├── audit-latest.md
│   ├── baseline.json
│   ├── replay.json
│   └── surface.json
└── src/
    ├── app.js                      composition root
    ├── config/
    │   └── index.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── middlewares/
    │   └── errorHandler.js
    ├── models/
    │   ├── auditLog.js
    │   ├── course.js
    │   ├── database.js
    │   ├── enrollment.js
    │   ├── errors.js
    │   ├── financialReport.js
    │   ├── password.js
    │   ├── payment.js
    │   ├── schema.js
    │   └── user.js
    └── routes/
        ├── adminRoutes.js
        ├── checkoutRoutes.js
        └── userRoutes.js

## Validation
  ✓ Application boots without errors  (PORT=5102 node src/app.js; deprecation detectors forced on: no warnings)
  ✓ Public surface replayed: 11 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 1 UNVERIFIED
  ✓ Findings resolved: 14/17  (2 proposed, not applied — see report; 1 partially resolved: AP-14 install-time)
  ○ Anti-patterns remaining: 5 proposed-not-applied, 1 unresolved  (re-audit: 6 findings)

## Proposed, Not Applied
- [CRITICAL] AP-04 — authentication/authorization on the admin report and user delete routes
- [HIGH] AP-08 — remove the default password for new buyers (makes `pwd` required)
- [HIGH] AP-11 — referential integrity / 404 on user delete
- [MEDIUM] AP-09 — course-lookup failure answered as 404
- [MEDIUM] AP-11 — stricter format validation on checkout fields

## Verification Coverage
Re-audit: complete — Layer-1 (forced runtime deprecation warnings on boot and on every surface request) and Layer-2 lookups (npm registry, OSV.dev, npm audit, 2026-09-21) both ran.
DEGRADED — the following checks did not run, and the results above do not cover them:
  - Surface entry "POST /api/checkout (non-string card, last: crashes original)": the original process crashed on it, so the baseline is a transport error and the harness records it UNVERIFIED (neither PRE-EXISTING FAILURE nor "improved"). Replay observed 400 text/html and the process stayed up — reported here, not counted as a pass.
  - Graceful shutdown on SIGINT/SIGTERM was not exercised (Windows host; processes were force-stopped).
Supplementary evidence beyond the protocol: plain-text bodies are opaque to the shape comparison, so a value snapshot (scratchpad script) was taken before and after — all 11 observed entries returned identical status, content type and body (JSON compared after normalising array order). Transaction rollback was verified by a one-off script (audit table dropped → 500 "Erro DB", no enrollment/payment persisted).
================================

## Re-audit (Phase 3d) — 6 findings

| Severity | Finding | File | Set |
|---|---|---|---|
| CRITICAL | AP-04 Missing authorization (admin report, user delete) | src/routes/adminRoutes.js:5-17 | proposed-not-applied |
| HIGH | AP-08 Known default password for new buyers | src/controllers/checkoutController.js:9-11 | proposed-not-applied |
| HIGH | AP-11 Orphaned enrollments/payments on user delete; 200 for unknown id | src/controllers/userController.js:10-18 | proposed-not-applied |
| MEDIUM | AP-09 Course-lookup failure reported as 404 | src/controllers/checkoutController.js:44-51 | proposed-not-applied |
| MEDIUM | AP-11 No format validation for `eml`, `c_id`, `card` | src/routes/checkoutRoutes.js:6-18 | proposed-not-applied |
| LOW | AP-14 prebuild-install@7.1.3 registry-deprecated ("No longer maintained…"), required by sqlite3@6.0.1 (latest release) — tier B, `npm view`, 2026-09-21; no advisory (`npm audit`: 0 vulnerabilities). De-escalated from MEDIUM to LOW: install-time only, no advisory. | package.json:10-13 | unresolved — the refactoring failed to eliminate it (no upstream fix exists yet). The runtime's built-in SQLite module was checked as a replacement and is not recommended yet: on v24.12.0 it emits `ExperimentalWarning: SQLite is an experimental feature` (observed). |

Re-audit checks that returned nothing: AP-01, AP-02, AP-03, AP-05, AP-06, AP-07, AP-10, AP-12, AP-13, AP-15, AP-16, AP-17. During the re-audit, a literal 'Erro DB' repeated across three controllers (introduced by the refactoring) was noticed and consolidated into `DB_ERROR_MESSAGE` before the final replay; the replay above is the post-fix run.
