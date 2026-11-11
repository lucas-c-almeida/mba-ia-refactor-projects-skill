## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        .worktrees/r8-p2/ecommerce-api-legacy
Language:      JavaScript (Node.js; no `engines` field — runtime version undeclared; host has v24.12.0)
Framework:     Express 4.22.1 (resolved, package-lock.json)
Dependencies:  express ^4.18.2 (4.22.1), sqlite3 ^5.1.6 (5.1.7)
Domain:        LMS course sales — users buy courses via checkout (enrollment + payment), with an admin financial report
App type:      HTTP service
Architecture:  None — one class (src/AppManager.js) holds schema/seed, routing, business rules and persistence; src/utils.js is a grab-bag of config, cache and hashing
Source files:  3 files analyzed (src/*.js; excluded: node_modules/, .claude/, reports/, lockfile, README.md, api.http)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite in-memory, created and seeded at boot)
Boot:          node src/app.js (from `npm start`), working dir = target root
Port:          3000, fixed literal in src/utils.js:6 (no override read)
Runtime env:   Node 24.12.0 image; dependencies installed with `npm ci` from package-lock.json inside the container
Isolation:     container (docker 28.5.2, image node:24.12.0)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1 + sqlite3 5.1.7
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-10 22:57
Mode:    full
Confirmation: human-confirmed: y (no classification decisions were pending)
Tree:    clean at 62f5e63
Runtime: installed the declared dependencies from package-lock.json (`npm ci`) inside container refactor-arch-ecommerce-api-legacy-202611110153-d896c00a-1, in run copy run-1/ of the snapshot (outside the target)
Isolation: container (docker 28.5.2, image node:24.12.0)
Scratch: environment scratch directory — C:\Users\lucas\AppData\Local\Temp\claude\b247d7bb4f414394\ba923cae-119c-41c1-b0ad-d78f9f1be3ab\scratchpad\refactor-arch-ecommerce-api-legacy-202611110153-d896c00a  (protocol §1.1)

## Summary
CRITICAL: 9 | HIGH: 5 | MEDIUM: 2 | LOW: 5

## Findings

### [CRITICAL] Known-Vulnerable Dependency — express request-parsing tree   (AP-19)
File: package-lock.json:228-251
Description: `npm audit` (GitHub Advisory Database, looked up 2026-11-10) reports, for packages express 4.22.1 pulls in at run time: body-parser 1.20.4 (GHSA-27r3-jxmh-p828, high — DoS via trailing bytes after a compressed request body; GHSA-v422-hmwv-36x6, low), qs 6.14.2 (four moderate advisories incl. GHSA-x5fp-wj9c-mxmx, array-limit bypass in parsing), path-to-regexp 0.1.12 (GHSA-37ch-88jc-xwx2, high, ReDoS via multiple route parameters) and proxy-addr 2.0.7 (GHSA-jqcg-44mw-7w3h, critical, IP spoofing via trust subnet). Escalated from HIGH to CRITICAL because the high body-parser advisory is reachable: src/app.js:6 registers `express.json()` globally, so every anonymous POST body goes through the vulnerable parser (inflation enabled by default). proxy-addr is not reachable (the app never sets `trust proxy`) and path-to-regexp is not (no route has more than one parameter); they ride along with the same fix.
Impact: An anonymous client can send a crafted request body to `/api/checkout` and take the parser down — denial of service for every client of a single-process server.
Recommendation: Update the lockfile within the express 4 major (`npm outdated` 2026-11-10: wanted 4.22.3; `npm audit` marks the fix as available without `--force`), then re-run `npm audit` and confirm body-parser ≥ 1.20.9, qs > 6.16.0, path-to-regexp ≥ 0.1.13, proxy-addr fixed. See RP-18.
Contract: safe (upgrade within the same major version)

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:1-141
Description: One class holds schema creation and seed data (10-23), HTTP route registration and request parsing (25-35, 80, 131), business rules — payment approval by card prefix (46), revenue aggregation (108-110), account auto-creation with a default password (66-72) — persistence for every table (37-57, 83-106, 133), and response formatting (60, 112-115, 135), for three unrelated concepts (checkout, financial reporting, account administration). Filed as AP-03 by the precedence rule, so the handlers' business logic (AP-05) is named here rather than filed separately.
Impact: Nothing can be tested without an Express app and a live database; every change to any route risks all others; the payment rule cannot be reused or tested on its own.
Recommendation: Split into config, database/schema, models (repositories), services (checkout, reporting, users), controllers and routes, wired in one composition root. See RP-03, RP-05.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — checkout acts on an existing account by email   (AP-04)
File: src/AppManager.js:40-75
Description: Checkout looks up the user by the request's `eml` (40) and, when the account exists, enrolls and charges on its behalf (73-74) without verifying `pwd` or any credential; the application has no identity model (no operation verifies a presented credential). Checkout is a business operation (§6).
Impact: Anyone who knows a user's email can attach enrollments and payments to that account; nothing distinguishes it from the account holder's own purchase.
Recommendation: Introduce an identity model (sign-in, verified session/token) and bind checkout of an existing account to the authenticated principal. See RP-04.
Contract: contract-changing: every current client checks out anonymously; requiring a credential would reject all of them — proposed, not applied

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — card number and gateway key logged   (AP-08)
File: src/AppManager.js:45-45
Description: `console.log` writes the full card number from the request (`cc`) together with `config.paymentGatewayKey` on every checkout. Escalated from HIGH to CRITICAL: payment card data and a live payment credential reach the process log.
Impact: Anyone with access to logs (or their aggregation pipeline) obtains full card numbers and the gateway key; this is a payment-data breach by design.
Recommendation: Remove the line, or log only a masked card suffix and never the key. See RP-08.
Contract: safe (stdout is not part of the HTTP contract)

### [CRITICAL] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:57-61
Description: The audit-log insert's error is ignored and `200 Sucesso` is returned regardless (57-61); the user delete ignores its error and always reports success (133-135); report callbacks ignore `err` at 92, 104 and 106 (92 then dereferences `enrollments.length`, crashing on error); no error middleware exists, so unhandled errors reach Express's default handler (observed: stack trace page, see AP-18). Escalated from HIGH to CRITICAL: a failed persisted write (audit record, delete) is reported as success.
Impact: Operators cannot see failures; a delete or an audit entry can silently not happen while the client is told it did; a DB error in the report crashes the process.
Recommendation: Check every callback error, propagate to one centralized error middleware that keeps the application's own status codes and bodies, and never send success on a failed write. See RP-09.
Contract: safe (only failure paths change; intentional error statuses and bodies are kept)

### [CRITICAL] Missing or Bypassable Authorization — unguarded management financial report   (AP-04)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` returns revenue per course and every student's name with the amount paid, with no credential of any kind. Privileged by §6: administrative namespace and a management aggregate with financial figures and per-principal rollups.
Impact: Any anonymous caller reads the business's revenue and the payment history of every customer by name.
Recommendation: Guard it with an operator credential read from configuration (environment), compared in constant time, closed by default (403 when unset/empty). See RP-04.
Contract: safe (privileged operation: only non-operators are rejected)

### [CRITICAL] Missing or Bypassable Authorization — anonymous account deletion   (AP-04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes the row from `users` (the table holding credentials) by the path id, with no check, in an application with no identity model. Privileged by §6 (account deletion by request id). The response itself admits enrollments and payments are left orphaned (see AP-20).
Impact: Any anonymous caller can delete any account by enumerating ids.
Recommendation: Guard it with the same operator credential, closed by default. See RP-04.
Contract: safe (privileged operation: only non-operators are rejected)

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: The `config` object holds literal `dbPass: "senha_super_secreta_prod_123"`, `dbUser: "admin_master"` and a live-prefixed `paymentGatewayKey: "pk_live_1234567890abcdef"`, plus the port. Further credential literals reach the runtime datastore: the seed inserts a user with password `'123'` (src/AppManager.js:18), and checkout falls back to the literal default password `"123456"` when `pwd` is absent (src/AppManager.js:68).
Impact: Everyone with repository access holds the payment gateway key and DB password; every environment boots with a known account password; every account created without `pwd` shares one known password.
Recommendation: Read secrets from the environment (empty by default, fail closed where needed), remove unused ones, seed password from configuration, and replace the default password with a random one. See RP-01.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password storage   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` "hashes" a password by base64-encoding it, keeping its first two characters, repeating them and truncating to 10 — a reversible encoding of the password's first characters, so all passwords with the same prefix collide; it is used for new accounts (src/AppManager.js:68-69), and the seed stores its password in plain text (src/AppManager.js:18). Escalated from HIGH to CRITICAL: stored passwords are recoverable/plain.
Impact: A single read of `users` reveals the seed password and the prefix of every other one; reused passwords compromise other systems.
Recommendation: Use a purpose-built KDF from the runtime (Node's built-in `crypto.scrypt` with a per-user random salt), and hash the seed password too. See RP-08.
Contract: safe (no response returns the stored value)

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:5-8
Description: The constructor opens its own `sqlite3.Database(':memory:')`; configuration is imported from a module and read at the point of use (45); routes are bound by passing the Express app into the class, so there is no single place assembling database, services and routes.
Impact: No unit can be tested with a substitute database; the order of `new`, `initDb`, `setupRoutes` in app.js is an implicit protocol.
Recommendation: Create the database and config once in the entry point and inject them into repositories, services and controllers. See RP-06.
Contract: safe

### [HIGH] Missing Boundary Validation   (AP-11)
File: src/AppManager.js:29-35
Description: Checkout reads `usr`, `eml`, `pwd`, `c_id`, `card` and only checks truthiness (35); `card` is then used as a string (`cc.startsWith`, 46). Observed: a checkout with a numeric `card` closed the connection with no reply and the process exited — one anonymous request takes the whole server down. `DELETE /api/users/:id` passes the path id unchecked (132). Escalated from MEDIUM to HIGH because the malformed value terminates the process for every client.
Impact: Denial of service by a single malformed request; wrong-typed values reach the datastore.
Recommendation: Validate type and range of every request field at the boundary and answer 400 (`Bad Request`, the app's existing message) for wrong types. See RP-11.
Contract: safe (only values no legitimate client sends are rejected)

### [HIGH] Swallowed or Uncentralized Error Handling — non-atomic checkout   (AP-09)
File: src/AppManager.js:50-72
Description: Checkout performs up to four writes — user (69), enrollment (50), payment (54), audit log (57) — with no transaction; a failure midway leaves the earlier writes. The account is created before the payment decision, so a declined card still creates the user (observed on the run copy: the denied checkout answered 400 after the user insert).
Impact: Enrollments without payments, users created by failed purchases, audit records missing for completed sales.
Recommendation: Decide payment before any write and wrap the writes in one transaction. See RP-09.
Contract: safe

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: src/app.js:5-6
Description: No error middleware is registered and `NODE_ENV` is never set, so Express's default handler answers in development mode. Observed: a malformed JSON body to `/api/checkout` returned `400` with an HTML page containing the stack trace and internal paths (`/app/node_modules/body-parser/lib/types/json.js:92:19`, …). `X-Powered-By: Express` is sent on every response.
Impact: Internals (framework, file layout, library versions) are disclosed to any anonymous caller, mapping the next attack.
Recommendation: Register a centralized error handler that keeps the status and returns a generic body; disable `x-powered-by`. See RP-17.
Contract: safe (framework default error page, status kept)

### [HIGH] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: Module-level `globalCache` is mutated by `logAndCache` on every successful checkout (src/AppManager.js:59) and never read anywhere, never bounded; `totalRevenue` is a module-level `let` exported and imported but never used (see AP-17).
Impact: Memory grows with every distinct buyer for the process lifetime; the "cache" suggests a second source of truth that does not exist; it cannot survive more than one process.
Recommendation: Remove the write-only cache (keep the log line if wanted) and the unused global. See RP-07.
Contract: safe

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-16
Description: `users.email` is used as the account identity (lookup at 40 takes the first row) with no UNIQUE constraint; `enrollments.user_id/course_id` and `payments.enrollment_id` have no FOREIGN KEY; deleting a user leaves its enrollments and payments (observed: after `DELETE /api/users/1` the report lists the student as `Unknown` with the payment still counted); `price` and `amount` are `REAL` (binary float money); `status` is free text. Escalation (orphaned charges observed) and de-escalation (in-memory store rebuilt at every start) both apply and offset: kept at the MEDIUM default.
Impact: Duplicate accounts per email under concurrent checkouts; payments attached to deleted customers; revenue sums drift in floating point.
Recommendation: UNIQUE on email, foreign keys enabled per connection, integer cents for money, CHECK on status; decide the delete rule for children. See RP-19.
Contract: contract-changing in part: the UNIQUE/FK declarations and integer cents are safe; choosing what happens to a deleted user's enrollments and payments (cascade, refuse, keep) changes what the report shows after a delete — proposed

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-128
Description: The report reads all courses, then per course queries enrollments (92), and per enrollment queries the user (104) and the payment (106): 1 + C + 2E round trips, all unbounded reads of whole tables with no pagination (AP-13 signal, folded here).
Impact: Latency and load grow linearly with sales; the nested callbacks and counters make the endpoint fragile (an error mid-way never answers).
Recommendation: One joined query aggregated in the service, preserving the output shape. See RP-10.
Contract: safe (shape unchanged; order of elements was never guaranteed)

### [LOW] Deprecated or End-of-Life API Usage — deprecated install-time packages under sqlite3   (AP-14)
File: package-lock.json:1569-1573
Description: The npm registry marks as deprecated (Tier B, `npm ci` deprecation notices, 2026-11-10) packages sqlite3 5.1.7 pulls in for its install/build step: prebuild-install 7.1.3 ("No longer maintained… alternatives are available" — no successor named upstream), inflight 1.0.6 (upstream names lru-cache), @npmcli/move-file 1.1.2 (moved to @npmcli/fs), glob 7.2.3 and rimraf 3.0.2 (upstream: update to the current version), npmlog 6.0.2, gauge 4.0.4, are-we-there-yet 3.0.1 (no successor named). tar 6.2.1 is also deprecated and is reported under AP-19. LOW: install-time only; the direct packages themselves are not deprecated (`npm view express@4.22.1 deprecated`, `npm view sqlite3@5.1.7 deprecated`: empty, 2026-11-10).
Impact: The native-addon install chain is unmaintained; it will break at a future Node/npm upgrade, on the project's schedule rather than its own.
Recommendation: Evaluate sqlite3 6.0.1 (latest, `npm outdated` 2026-11-10) and verify at upgrade time whether it drops these packages; no successor for prebuild-install is named upstream. See RP-14.
Contract: safe only if the full replay passes on the new major (§6 dependency rule); otherwise proposed

### [LOW] Known-Vulnerable Dependency — sqlite3 install/build tree   (AP-19)
File: package-lock.json:2113-2130
Description: `npm audit` (2026-11-10) reports tar 6.2.1 (12 advisories, up to critical — e.g. GHSA-34x7-hfp2-rc4v, GHSA-23hp-3jrh-7fpw), brace-expansion 1.1.12 (high), ip-address 10.1.0 (high), @tootallnate/once (low), all under sqlite3 → node-gyp / tar. De-escalated to LOW: these run only at install/build time — in the installed sqlite3, `tar` is required only by deps/extract.js (build), and its `install` script is `prebuild-install -r napi || node-gyp rebuild`; nothing in the runtime path loads them.
Impact: Risk is confined to building the native module (a malicious archive during install), not to request handling.
Recommendation: `npm audit fix` resolves brace-expansion and ip-address within range; tar requires sqlite3 6.0.1 (major, per npm audit). See RP-18.
Contract: safe for the in-range fixes; the sqlite3 major is safe only if the full replay passes (§6), otherwise proposed

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/AppManager.js:2-2
Description: `totalRevenue` is imported and never used; in src/utils.js, `totalRevenue` (10) and `globalCache` (25) are exported and never read by any importer, and `config.dbUser`, `config.dbPass`, `config.smtpUser` (2, 3, 5) are never read (there is no DB user/password with an in-memory SQLite, and no mail code). The `audit_logs` table is written and never read: discarded as an audit trail by design.
Impact: Readers assume a DB login and SMTP integration exist; dead secrets stay in the tree.
Recommendation: Delete the unused imports, exports and config keys. See RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: Single-letter or cryptic locals (`u`, `e`, `p`, `cid`, `cc`); `badCrypto` names a password function after its flaw; `logAndCache` does two unrelated things; `AppManager` names nothing; `self` and `this` used interchangeably (26, 54); Portuguese messages next to English identifiers. The request field names (`usr`, `eml`, `pwd`, `c_id`, `card`) are part of the public contract and stay.
Impact: Readers must open every call to know what it does; the password function's name hides that it must be replaced.
Recommendation: Rename internal identifiers by intent (`courseId`, `cardNumber`, `hashPassword`). See RP-16.
Contract: safe (internal identifiers only)

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-48
Description: Payment approval is the literal rule `cc.startsWith("4")`; statuses `"PAID"`/`"DENIED"` are bare strings repeated at 21, 46, 48 and 108; the hashing loop uses 10000 and 10 (src/utils.js:19, 22); the port 3000 is a literal (src/utils.js:6).
Impact: The payment rule and status vocabulary are agreed by memory; a typo creates a new status silently.
Recommendation: Named constants for statuses and the approval rule; port from configuration with 3000 as default. See RP-15.
Contract: safe

## Signal Ledger

| Entry | Signal | Examined | Occurrences | Outcome |
|---|---|---|---|---|
| AP-01 | literal assigned to secret-named identifier | all source files | 3: src/utils.js:3, 4, (2 user name) | finding: [CRITICAL] Hardcoded Secrets |
| AP-01 | credential literal in seed/bootstrap data | src/AppManager.js:10-23 (boot seed) | 1: src/AppManager.js:18 | finding: [CRITICAL] Hardcoded Secrets (also AP-08) |
| AP-01 | connection URL with inline credentials | all source files | 0 | none |
| AP-01 | high-entropy / credential-prefixed literal | all source files | 1: src/utils.js:4 (`pk_live_`) | finding: [CRITICAL] Hardcoded Secrets |
| AP-01 | framework signing/session key literal | all source files | 0 (no sessions) | none |
| AP-01 | credential-bearing file committed | target tree | 0 | none |
| AP-01 | default value that is a working credential | all source files | 1: src/AppManager.js:68 (`"123456"`) | finding: [CRITICAL] Hardcoded Secrets |
| AP-02 | input reaching driver via concatenation/interpolation | all 9 driver calls in src/AppManager.js | 0 — all use `?` with a parameter array; the template literal at 57 is a bound value | none |
| AP-02 | interpolation markers inside statement strings | src/AppManager.js | 0 | none |
| AP-02 | ORM escape hatch with built string | all source files | 0 (no ORM) | none |
| AP-02 | dynamic identifiers from input | all source files | 0 | none |
| AP-02 | shell/process execution with input | all source files | 0 | none |
| AP-02 | unsafe deserialization / template injection | all source files | 0 (JSON body parser only) | none |
| AP-02 | path traversal | all source files | 0 | none |
| AP-03 | ≥3 responsibility categories in one module | src/AppManager.js, src/utils.js | 2: AppManager (a,b,c,d,e), utils (config, state, crypto, logging) | finding: [CRITICAL] God Module (AppManager); utils covered by AP-01/07/08/17 findings |
| AP-03 | >300–400 lines with ≥2 categories | all source files | 0 (largest 141 lines) | none |
| AP-03 | unit >50 lines / nesting >3 / >5 params | src/AppManager.js | 2: checkout handler 28-78 (51 lines, 6 nested callbacks); report 80-129 | finding: [CRITICAL] God Module |
| AP-03 | several unrelated domain concepts in one file | src/AppManager.js | 1 (checkout, reporting, account admin) | finding: [CRITICAL] God Module |
| AP-03 | low-cohesion class | src/AppManager.js | 1 | finding: [CRITICAL] God Module |
| AP-03 | utilities/manager grab-bag | src/utils.js, src/AppManager.js | 2 | finding: [CRITICAL] God Module (AppManager); utils: discarded as AP-03 (25 lines), its members are filed under AP-01/07/08/17 |
| AP-03 | very high afferent coupling | import graph | 0 | none |
| AP-04 | principal resource with no authn/ownership check | all 3 routes | 1: checkout on existing account (40-75) | finding: [CRITICAL] checkout acts on an existing account |
| AP-04 | lookup filtered only by input id (IDOR) | all routes | 2: src/AppManager.js:40, 133 | findings: checkout (40); delete (133) |
| AP-04 | check only on one door | all routes | 0 (no checks exist) | none |
| AP-04 | role/admin flag trusted from request | all routes | 0 | none |
| AP-04 | token decoded not verified | all source files | 0 (no tokens) | none |
| AP-04 | check written but unreachable | all source files | 0 | none |
| AP-04 | commented-out/disabled guard | all source files | 0 | none |
| AP-04 | privileged operation with no guard | all routes | 2: report (80-129), account delete (131-137) | findings: both [CRITICAL] AP-04 |
| AP-05 | domain decisions in handlers | src/AppManager.js | 2: payment rule 46, revenue 108-110 | folded into AP-03 (precedence rule) |
| AP-05 | persistence directly in handlers | src/AppManager.js | all handlers | folded into AP-03 |
| AP-05 | handler >30 lines not just mapping | src/AppManager.js | 2 | folded into AP-03 |
| AP-05 | request objects deep in call stack | src/AppManager.js | 0 (res used only in handler closures) | none |
| AP-05 | same rule in two handlers | src/AppManager.js | 0 | none |
| AP-05 | pass-through service layer | tree | 0 (no layers) | none |
| AP-06 | unit constructs its collaborators | src/AppManager.js | 1: 7 | finding: [HIGH] Hard-Wired Dependencies |
| AP-06 | import-time side effects | all modules | 1: src/app.js:5-14 (entry point binds port) | discarded: it is the entry point, where wiring belongs |
| AP-06 | no single composition root | tree | 1 | finding: [HIGH] Hard-Wired Dependencies |
| AP-06 | no seam for DB/clock in rules | src/AppManager.js | 1 | finding: [HIGH] Hard-Wired Dependencies |
| AP-06 | concrete driver in domain | src/AppManager.js | 1 | finding: [HIGH] Hard-Wired Dependencies |
| AP-06 | configuration read at point of use | src/AppManager.js:45 | 1 | finding: [HIGH] Hard-Wired Dependencies |
| AP-07 | module-level variable mutated from several places | src/utils.js | 1: globalCache (9, 14) | finding: [HIGH] Mutable Global State |
| AP-07 | request-scoped data stored globally | all source files | 0 | none |
| AP-07 | in-memory collection as store of record | all source files | 1: globalCache; (SQLite `:memory:` at src/AppManager.js:7) | finding for globalCache; SQLite `:memory:` discarded: an embedded database engine, not an application collection, and documented in README as the intended datastore |
| AP-07 | mutable default / exported mutable object | src/utils.js:25 | 1: globalCache exported | finding: [HIGH] Mutable Global State |
| AP-07 | cache with no lifecycle | src/utils.js | 1 | finding: [HIGH] Mutable Global State |
| AP-07 | monkey-patched built-in | all source files | 0 | none |
| AP-07 | in-memory id counter | all source files | 0 (ids from SQLite) | none |
| AP-08 | password stored reversibly/plain | src/utils.js, src/AppManager.js | 2: 18 (plain), utils 17-23 (encoding) | finding: [CRITICAL] password storage |
| AP-08 | fast digest for passwords | src/utils.js | 0 (not even a digest) | covered by the finding above |
| AP-08 | shared/missing salt | src/utils.js | 1 (no salt) | finding: [CRITICAL] password storage |
| AP-08 | non-constant-time comparison | all source files | 0 (no comparison) | none |
| AP-08 | sensitive values logged | all source files | 1: src/AppManager.js:45 | finding: [CRITICAL] card and key logged |
| AP-08 | whole record serialized in response | all responses | 0 (report selects name only) | none |
| AP-08 | transport/cert verification disabled | all source files | 0 | none |
| AP-08 | token without expiry/rotation | all source files | 0 (no tokens) | none |
| AP-09 | empty/log-only catch or success on failure | src/AppManager.js | 3: 57, 92/104/106, 133 | finding: [CRITICAL] Swallowed Error Handling |
| AP-09 | over-broad catch | all source files | 0 | none |
| AP-09 | same error mapping repeated per handler | src/AppManager.js | 6 (`res.status(500).send(...)`) | finding: [CRITICAL] Swallowed Error Handling |
| AP-09 | no centralized handler | src/app.js | 1 (observed default page) | finding: [CRITICAL] Swallowed Error Handling; leak filed as AP-18 |
| AP-09 | internals in response body | observed at runtime | 1 (stack trace) | finding: [HIGH] Insecure Runtime Configuration |
| AP-09 | inconsistent error convention | src/AppManager.js | text errors vs JSON success | discarded: intentional error contract, kept |
| AP-09 | multi-write with no transaction | src/AppManager.js:50-72 | 1 | finding: [HIGH] non-atomic checkout |
| AP-09 | exceptions for control flow | all source files | 0 | none |
| AP-10 | driver call inside loop | src/AppManager.js | 3: 92, 104, 106 | finding: [MEDIUM] N+1 |
| AP-10 | per-element FK fetch | src/AppManager.js | 2: 104, 106 | finding: [MEDIUM] N+1 |
| AP-10 | lazy relation in iteration | all source files | 0 (no ORM) | none |
| AP-10 | same read repeated per argument | src/AppManager.js | 3 | finding: [MEDIUM] N+1 |
| AP-10 | remote call in loop | all source files | 0 | none |
| AP-10 | whole table read to aggregate in code | src/AppManager.js:83, 108-110 | 1 | finding: [MEDIUM] N+1 |
| AP-10 | write loop per element | all source files | 0 | none |
| AP-11 | field used with no type/range check | all routes | 6: usr, eml, pwd, c_id, card (29-33), :id (132) | finding: [HIGH] Missing Boundary Validation |
| AP-11 | optional input dereferenced without check | src/AppManager.js:46 | 1 (`cc.startsWith` on non-string; observed crash) | finding: [HIGH] Missing Boundary Validation |
| AP-11 | unconstrained pagination | all routes | 0 (no pagination) | none |
| AP-11 | numeric parsing without failure path | all source files | 0 | none |
| AP-11 | validation on one door only | all routes | 0 | none |
| AP-11 | validation after use / after side effect | src/AppManager.js | 0 | none |
| AP-11 | domain invariants enforced nowhere | src/AppManager.js | 1: user created before payment decision | covered by [HIGH] non-atomic checkout |
| AP-11 | no upper bound on body | src/app.js:6 | 0 (express.json default limit applies) | none |
| AP-11 | ad-hoc scattered validation | src/AppManager.js:35 | 1 | finding: [HIGH] Missing Boundary Validation |
| AP-12 | ≥10-line structurally identical blocks | src/AppManager.js | 0 (closest: 95-99 vs 117-122, 4 lines) | discarded: below threshold; removed by the AP-10 rewrite |
| AP-12 | same business rule in several places | all source files | 0 | none |
| AP-12 | repeated validation/error mapping | src/AppManager.js | 6 error sends | covered by [CRITICAL] Swallowed Error Handling |
| AP-12 | hand-written mapping in several places | all source files | 0 | none |
| AP-12 | copy-and-modify lineage | all source files | 0 | none |
| AP-12 | constant literal repeated across files | all source files | statuses 'PAID'/'DENIED' | covered by [LOW] Magic Values |
| AP-12 | repeated condition at call sites | all source files | 0 | none |
| AP-13 | paired acquire/release | all source files | 0 | none |
| AP-13 | handle without release on failure | all source files | 0 (one process-lifetime DB) | none |
| AP-13 | connection per call / unbounded pool | all source files | 0 | none |
| AP-13 | outbound call without timeout | all source files | 0 (no outbound calls) | none |
| AP-13 | missing/unbounded retry | all source files | 0 | none |
| AP-13 | unbounded read | src/AppManager.js:83, 92 | 1 | folded into [MEDIUM] N+1 |
| AP-13 | unbounded accumulator/cache | src/utils.js:9 | 1 | folded into [HIGH] Mutable Global State |
| AP-13 | background task without shutdown | all source files | 0 | none |
| AP-13 | unbounded recursion | all source files | 0 | none |
| AP-14 | Layer 1: forced runtime deprecation warnings | boot (incl. seed in initDb) + every route: checkout ok, checkout denied, malformed body, financial report ×2, delete user, wrong-typed card — `node --pending-deprecation --trace-deprecation --trace-warnings --redirect-warnings` | 0 (warnings file never created) | none |
| AP-14 | deprecated flag in manifest/lockfile/registry | package-lock.json, `npm ci` output | 9 transitive (sqlite3 install tree) | finding: [LOW] AP-14; tar reported under AP-19 |
| AP-14 | version marked unsupported by manifest | package.json | 0 (no engines field) | none |
| AP-14 | structurally superseded construct (callback API) | src/AppManager.js | callback driver API throughout | discarded: no Tier A/B/C evidence that the driver's callback API is deprecated at 5.1.7; the nesting is addressed by AP-03/AP-10 |
| AP-14 | Layer 2: registry deprecation of direct deps | `npm view express@4.22.1 deprecated`, `npm view sqlite3@5.1.7 deprecated` | 0 | none |
| AP-14 | Layer 2: native tooling distance | `npm outdated` | express 4.22.1 → wanted 4.22.3, latest 5.3.0; sqlite3 5.1.7 → latest 6.0.1 | informs AP-19 recommendations; no end-of-life evidence for express 4 found — not a finding |
| AP-15 | unexplained numeric literal in decision | src/AppManager.js, src/utils.js | 3: utils 19, 22; card prefix 46 | finding: [LOW] Magic Values |
| AP-15 | duration/size without unit | all source files | 0 | none |
| AP-15 | string enum repeated | src/AppManager.js | 4: 21, 46, 48, 108 | finding: [LOW] Magic Values |
| AP-15 | literal repeated in several places | all source files | 'PAID' ×3 | finding: [LOW] Magic Values |
| AP-15 | numeric code compared directly | all source files | 0 | none |
| AP-15 | unnamed index/offset | src/utils.js:20 (`substring(0, 2)`) | 1 | finding: [LOW] Magic Values (goes with badCrypto) |
| AP-15 | environment literal inline | src/utils.js:6 (port) | 1 | finding: [LOW] Magic Values |
| AP-16 | name contradicts behaviour | src/utils.js | 1: `logAndCache` | finding: [LOW] Misleading Names |
| AP-16 | non-descriptive identifiers | src/AppManager.js:29-33 | 5 | finding: [LOW] Misleading Names |
| AP-16 | several names for one concept | src/AppManager.js | `self`/`this` for the instance | finding: [LOW] Misleading Names |
| AP-16 | how-not-what names | src/utils.js | `badCrypto` | finding: [LOW] Misleading Names |
| AP-16 | mixed naming conventions | all source files | request fields snake/short vs camelCase | discarded for request fields (public contract); internal ones in the finding |
| AP-16 | mixed human languages | all source files | Portuguese messages, English identifiers | finding: [LOW] Misleading Names (messages are contract and stay) |
| AP-16 | misplaced files | tree | utils.js holds config | covered by AP-03 restructuring |
| AP-16 | comment contradicts code | all source files | 0 (no comments) | none |
| AP-16 | boolean parameters at call sites | all source files | 0 | none |
| AP-17 | commented-out code | all source files | 0 | none |
| AP-17 | unreachable branch | all source files | 0 | none |
| AP-17 | defined, never referenced | all source files | 5: totalRevenue, globalCache export, dbUser, dbPass, smtpUser | finding: [LOW] Dead Code |
| AP-17 | unused import / undeclared-unused dependency | all source files, package.json | 1: totalRevenue import (AppManager.js:2) | finding: [LOW] Dead Code |
| AP-17 | parameter never read / value never used | all source files | 0 | none |
| AP-17 | constant feature flag | all source files | 0 | none |
| AP-17 | unregistered endpoint | all source files | 0 | none |
| AP-17 | old/backup copy kept | tree | 0 | none |
| AP-17 | written-never-read by design | src/AppManager.js:16, 57 (audit_logs) | 1 | discarded: audit trail with declared purpose |
| AP-18 | debug mode by literal | src/app.js | 0 literal; NODE_ENV unset → Express development error mode | finding: [HIGH] Insecure Runtime Configuration |
| AP-18 | dev server as production server | src/app.js | 0 (Node HTTP server is the production server) | none |
| AP-18 | listener on all interfaces + debug | src/app.js:12 | 1 (default bind, no debug console) | discarded: no debug console or diagnostic endpoint combined with it |
| AP-18 | error output exposing internals | observed at runtime | 1 (stack trace, internal paths) | finding: [HIGH] Insecure Runtime Configuration |
| AP-18 | permissive CORS | all source files | 0 (no CORS configured) | none |
| AP-18 | unrestricted admin/diagnostic surface | routes | 1: /api/admin/financial-report | filed as AP-04 (privileged) |
| AP-18 | protective defaults off | src/app.js | 1: `X-Powered-By` left on | finding: [HIGH] Insecure Runtime Configuration |
| AP-19 | advisory for direct dependency's runtime tree | `npm audit` 2026-11-10; OSV.dev query for express 4.22.1 and sqlite3 5.1.7 (both `{}`) | 4 packages under express | finding: [CRITICAL] AP-19 express tree |
| AP-19 | advisory in transitive install-time tree | `npm audit`, `npm ls` | 5 packages under sqlite3 | finding: [LOW] AP-19 sqlite3 tree |
| AP-19 | lockfile pins vulnerable version the range would fix | package.json vs package-lock.json | express range allows 4.22.3 | finding: [CRITICAL] AP-19 (fix is a lockfile update) |
| AP-19 | no lockfile with ranges | target | 0 (lockfile present) | none |
| AP-19 | no lockfile, exact pins | target | 0 | none |
| AP-20 | identity column without UNIQUE | src/AppManager.js:12, 40 | 1: users.email | finding: [MEDIUM] Missing Schema Constraints |
| AP-20 | reference column without FK | src/AppManager.js:14-15 | 3 | finding: [MEDIUM] Missing Schema Constraints |
| AP-20 | parent delete with no child rule | src/AppManager.js:133 | 1 (orphans observed) | finding: [MEDIUM] Missing Schema Constraints |
| AP-20 | money in binary float | src/AppManager.js:13, 15 | 2: price REAL, amount REAL | finding: [MEDIUM] Missing Schema Constraints |
| AP-20 | nullable required column / free-text enum | src/AppManager.js:12-16 | status TEXT, all columns nullable | finding: [MEDIUM] Missing Schema Constraints |

## Classification Decisions
none — both privileged operations are unambiguous under §6 (administrative path with a financial, per-principal aggregate; deletion of the credential-holding account by request id with no identity model), and checkout is a business operation by §6's explicit list.

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| runtime deprecation warnings (boot + all 4 routes) | Node 24.12.0 | deprecation | A (none emitted) | `node --pending-deprecation --trace-deprecation --redirect-warnings` | n/a — local | no issue found |
| express | 4.22.1 | deprecation | B | `npm view express@4.22.1 deprecated` | 2026-11-10 | no issue found |
| sqlite3 | 5.1.7 | deprecation | B | `npm view sqlite3@5.1.7 deprecated` | 2026-11-10 | no issue found |
| express | 4.22.1 | advisory (package itself) | B | OSV.dev `/v1/query` | 2026-11-10 | no issue found |
| sqlite3 | 5.1.7 | advisory (package itself) | B | OSV.dev `/v1/query` | 2026-11-10 | no issue found |
| body-parser (via express) | 1.20.4 | advisory | B | npm audit: GHSA-27r3-jxmh-p828, GHSA-v422-hmwv-36x6 | 2026-11-10 | [CRITICAL] AP-19 express tree |
| qs (via express) | 6.14.2 | advisory | B | npm audit: GHSA-x5fp-wj9c-mxmx and 3 others | 2026-11-10 | [CRITICAL] AP-19 express tree |
| path-to-regexp (via express) | 0.1.12 | advisory | B | npm audit: GHSA-37ch-88jc-xwx2 | 2026-11-10 | [CRITICAL] AP-19 express tree (not reachable) |
| proxy-addr (via express) | 2.0.7 | advisory | B | npm audit: GHSA-jqcg-44mw-7w3h | 2026-11-10 | [CRITICAL] AP-19 express tree (not reachable) |
| tar (via sqlite3) | 6.2.1 | advisory + deprecation | B | npm audit (12 GHSA ids); registry deprecation | 2026-11-10 | [LOW] AP-19 sqlite3 tree |
| brace-expansion, ip-address, @tootallnate/once (via sqlite3 → node-gyp) | 1.1.12, 10.1.0, — | advisory | B | npm audit | 2026-11-10 | [LOW] AP-19 sqlite3 tree |
| prebuild-install, inflight, @npmcli/move-file, glob, rimraf, npmlog, gauge, are-we-there-yet (via sqlite3) | 7.1.3, 1.0.6, 1.1.2, 7.2.3, 3.0.2, 6.0.2, 4.0.4, 3.0.1 | deprecation | B | npm registry deprecation notices (`npm ci`) | 2026-11-10 | [LOW] AP-14 |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-ecommerce-api-legacy-202611110153-d896c00a-1 | `docker run -d ... node:24.12.0 sleep infinity` (run-1 mounted at /app); `docker exec ... npm ci`; `docker exec -d ... node --pending-deprecation --trace-deprecation --trace-warnings --redirect-warnings=/app/node-warnings.log src/app.js` | first `proc wait --port 3000 --timeout 30` returned exit 4; process was alive (ps); second wait ready immediately on port 3000 |
| 2 | 2 | (exit) | container | same | — | the node process exited on its own after the wrong-typed `card` request (curl exit 52, empty reply; ps shows no node) — the observed AP-11 crash, not a stop by this run |
| 3 | 2 | stop | container | refactor-arch-ecommerce-api-legacy-202611110153-d896c00a-1 | `docker rm -f <exact name>` | removed |

## Verification Coverage
Full — all planned checks executed, with these limits stated:
  - The crash on a wrong-typed `card` was observed (empty reply, process gone); its stack trace was not captured because a detached `exec` keeps no stdout/stderr. The cited line (src/AppManager.js:46) is from reading the code.
  - The AP-08 logging finding (src/AppManager.js:45) is from reading the code; the application's stdout was not captured for the same reason.
  - The first readiness wait timed out (exit 4) although the process was running; a second wait succeeded at once. Cause not determined.
  - Node runtime version is undeclared by the project; the image node:24.12.0 was chosen to match the host.
  - Scratch root: the environment's scratch directory. Snapshot: …\refactor-arch-ecommerce-api-legacy-202611110153-d896c00a\pristine (node_modules excluded); run copy run-1 (dependencies installed there by the container).

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
>

Answer at the gate: y (human, relayed by the coordinator). Scope applied: all findings, contract gate on.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
ecommerce-api-legacy/
├── .gitignore                       (new: node_modules/, .env, logs, db files)
├── README.md                        (run instructions + variables to export)
├── api.http                         (operator header on the privileged requests)
├── package.json                     (express ^4.22.3)
├── package-lock.json                (regenerated by npm: express 4.22.3, body-parser 1.20.9, qs 6.16.2, ...)
├── reports/
│   ├── audit-20261110-2257.md       (Phase 2, as at the gate)
│   ├── audit-latest.md              (this file)
│   ├── surface.json
│   ├── baseline.json                (gate baseline, original)
│   ├── baseline-recheck.json        (second capture of the original, contract + value entries)
│   ├── replay.json                  (first full replay)
│   ├── replay-2.json                (second full replay, after the fix loop)
│   ├── baseline-values.json         (order-insensitive value entry, captured against the original)
│   └── replay-values.json           (same entry, live replay against the refactored app)
└── src/
    ├── app.js                       composition root
    ├── config/
    │   └── index.js                 environment, read once (PORT, OPERATOR_TOKEN, SEED_USER_PASSWORD)
    ├── models/
    │   ├── database.js              connection, promise helpers, write queue, transactions
    │   ├── schema.js                DDL with constraints + seed
    │   ├── errors.js                domain error taxonomy
    │   ├── payment.js               payment rule, statuses, cents
    │   ├── password.js              scrypt hashing
    │   ├── userRepository.js
    │   ├── courseRepository.js
    │   ├── enrollmentRepository.js
    │   └── reportRepository.js      single joined query
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── routes/
    │   ├── index.js                 the three routes (View layer)
    │   └── validators.js            boundary checks
    └── middlewares/
        ├── requireOperator.js       operator guard, closed by default
        ├── requestId.js             X-Request-Id
        └── errorHandler.js          error boundary
```
Removed: src/AppManager.js, src/utils.js (content migrated; git history is the backup).
Layout: MVC with repositories inside `models/` (persistence lives in the model layer, uniformly).

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 8 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 1 UNVERIFIED
    Security entries: 3 FIXED, 0 NOT FIXED
  ✓ Malformed input: 57 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 3 operations
  ✓ Values: 1 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 15/21  (6 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 7 proposed-not-applied, 0 unresolved  (re-audit: 7 findings)
    Re-audit passes: 2; fixed after re-audit: 1 (0 of them missed-in-phase-2)
  ✓ Processes: 22 started, 22 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

Notes on the lines above:
- Replay counts are from the second full replay (replay-2.json vs baseline.json); the first full replay gave the same counts. The 1 UNVERIFIED is the security entry `post-checkout-malformed-json` (AP-18): the original already answered 400, so the harness cannot demonstrate the fix by status. Its recorded text skeleton changed from the framework's stack-trace page (baseline.json) to `Bad Request` (replay-2.json).
- Values: the line counts the replacement entry `get-financial-report-membership` (baseline-values.json vs replay-values.json: HOLDS).
  - **Why it was replaced.** The first value entry, `get-financial-report-values`, compared `$[*].course`, `$[*].revenue`, `$[*].students[*].student` and `$[*].students[*].paid` with positional `sameAsBaseline`. The original builds the report through nested async callbacks, so its course and student order is not deterministic. Evidence: the original's second capture vs its own gate baseline (baseline-recheck.json vs baseline.json) is VIOLATED. The refactor returns an ordered JOIN. Comparing an order the original does not guarantee breaks protocol §5 (D6.5), so that entry's VIOLATED came from the entry, not the code.
  - **Retired entry.** It is no longer in surface.json and is not counted here. Its old results stay in baseline.json, replay.json and replay-2.json, unedited. In those files it reads VIOLATED against baseline.json and HOLDS against baseline-recheck.json, the capture whose order happened to match.
  - **What the replacement asserts.** It uses only operators the probe supports (`matches` with `[*]`, every value must match): every course title is one of the catalog's titles, and every student name is one of the names the seed and the inventory's requests create (or `Unknown`).
  - **When it was captured.** Against the ORIGINAL, from a fresh copy of the commit the audit read (62f5e63, exported with `git archive`), after the four checkout entries that populate the report. It was then replayed live against the refactored app.
  - **What it cannot verify.** The probe has no keyed, sorted or set comparison, and `matches` accepts only string values. The per-course numbers (`revenue`, `paid`) and the pairing of a course with its revenue therefore cannot be asserted order-insensitively. They are UNVERIFIED (see Verification Coverage). No probe feature was added.

## Findings by bucket
Resolved (15): AP-19 express tree [CRITICAL]; AP-03 God Module [CRITICAL]; AP-08 card/key logging [CRITICAL]; AP-09 swallowed errors [CRITICAL]; AP-04 financial report guard [CRITICAL]; AP-04 account deletion guard [CRITICAL]; AP-08 password storage [CRITICAL]; AP-06 composition root [HIGH]; AP-11 boundary validation [HIGH]; AP-09 non-atomic checkout [HIGH]; AP-18 runtime config [HIGH]; AP-07 global cache [HIGH]; AP-17 dead code [LOW]; AP-16 names [LOW]; AP-15 magic values [LOW].
Proposed (6): AP-01 hardcoded secrets [CRITICAL] (code fixed; operator residue: rotation); AP-04 checkout identity [CRITICAL]; AP-20 schema constraints [MEDIUM] (applied in part; delete rule held); AP-10 N+1 [MEDIUM] (N+1 removed — one joined query; the remaining unbounded read needs pagination, a product decision → proposed); AP-14 sqlite3 install-time deprecations [LOW]; AP-19 sqlite3 install-time advisories [LOW] (in-range part applied; major held).
Unresolved (0).

Decided at the gate: no classification decisions were pending. The privileged operations were guarded per §6:
- `GET /api/admin/financial-report` and `DELETE /api/users/:id` require header `X-Operator-Token` equal to `OPERATOR_TOKEN`. That variable is **unset by default**, so both routes answer 403 until the operator sets it.

## Re-audit (3d)
Pass 1 (over replay-1 code): 8 findings.
- proposed-not-applied (5): AP-01 secret rotation residue; AP-04 checkout identity model; AP-20 user→children delete rule; AP-14 sqlite3 deprecated install chain; AP-19 sqlite3 install-time advisories (tar via sqlite3 6.x major).
- unresolved (3):
  - [MEDIUM] AP-10 — origin `failed`: see above.
  - [LOW] AP-17 Dead Code — origin `introduced`: src/models/database.js exported a `close` helper nothing called; src/config/index.js exported `ConfigError` and src/middlewares/requireOperator.js exported `OPERATOR_HEADER`, neither imported; a lint-suppression comment for a linter the project does not have (src/middlewares/errorHandler.js). Fixed after re-audit (counted as fixed-after-re-audit).
  - [HIGH] AP-14 Deprecated or End-of-Life API Usage — origin `missed-in-phase-2`: the direct dependency sqlite3 is marked unmaintained by its own repository (PR #1844 "marked the repository as unmaintained"; repository archived 2026-07-01, read-only) — Tier C, https://github.com/TryGhost/node-sqlite3/releases, looked up 2026-11-10. No successor named upstream (same source). File: package.json:11-11. Replacing the driver is a new runtime dependency → recorded under PROPOSED, NOT APPLIED, tag kept. Ledger row that missed it: AP-14 "Layer 2: official documentation or changelog" was never queried in Phase 2 (only registry `deprecated` flag and `npm outdated`).
Pass 2 (after the fix loop, over replay-2 code): 7 findings, all proposed-not-applied — the 5 above, AP-14 sqlite3 unmaintained (`missed-in-phase-2`, proposed: replacing the driver is a new dependency) and the AP-10 remainder (the report is still an unbounded read of every enrollment; bounding it needs pagination, which changes the response contract and needs a product decision → proposed per D14.1, not `unresolved`; its value check now HOLDS with the order-insensitive entry). 0 unresolved. No `introduced` item remains. Layer 1 on the refactored app (boot + full surface with `--pending-deprecation --trace-deprecation`): no warning emitted, both passes. `npm audit` on the refactored lockfile (2026-11-10): express tree clean; remaining advisories are only the sqlite3 install-time chain (tar, node-gyp, make-fetch-happen, cacache, http-proxy-agent, @tootallnate/once).

## Proposed, Not Applied
### [CRITICAL] Hardcoded Secrets and Credentials — operator residue   (AP-01)
File: src/utils.js:1-7 (original; removed)
Reason not applied: the code part is done (no secret in source; the unused DB password and the gateway key, which was only ever logged, were removed). What remains is history: `pk_live_1234567890abcdef` and `senha_super_secreta_prod_123` are in every clone of the repository.
Proposed change: the owner rotates the payment gateway key and the database password at their providers now, and treats the old values as public. If a real gateway is integrated later, its key is read from the environment through src/config/index.js.

### [CRITICAL] Missing or Bypassable Authorization — checkout acts on an existing account by email   (AP-04)
File: src/controllers/checkoutController.js:28-38 (was src/AppManager.js:40-75)
Reason not applied: the application has no identity model; requiring a credential at checkout would reject every current client.
Proposed change: introduce sign-in and a verified session/token, then bind checkout of an existing account to the authenticated principal (RP-04). Needs a product decision on principals and policy.

### [MEDIUM] Missing Schema-Level Integrity Constraints — delete rule for a user's enrollments and payments   (AP-20)
File: src/models/schema.js:20-26
Reason not applied: a foreign key on `enrollments.user_id` (with or without `ON DELETE`) changes what `DELETE /api/users/:id` does today (refuse, cascade or detach) and what the report shows afterwards.
Applied: UNIQUE on `users.email`, FKs `enrollments.course_id` and `payments.enrollment_id` (enforced with `PRAGMA foreign_keys = ON`), money as integer cents with the same JSON numbers at the boundary, CHECK on payment status, NOT NULL on required columns.
Proposed change: choose the rule, then add `REFERENCES users (id) ON DELETE <rule>`. Count the rows the constraint would reject first: `SELECT e.id FROM enrollments e LEFT JOIN users u ON u.id = e.user_id WHERE u.id IS NULL;`.

### [MEDIUM] N+1 and Query-Inside-Loop Access — remaining unbounded read   (AP-10)
File: src/models/reportRepository.js:8-41
Reason not applied: the N+1 is gone (one joined query instead of 1 + C + 2E round trips). What remains is that the report reads every course, enrollment and payment in one response. Bounding it needs pagination or a date filter, which changes the response contract (array shape and completeness) and is a product decision.
Proposed change: add `limit`/`cursor` (or a period filter) to `GET /api/admin/financial-report` with a documented default, and version the response if clients rely on receiving all courses.

### [LOW] Deprecated or End-of-Life API Usage — deprecated install-time packages under sqlite3   (AP-14)
File: package-lock.json (sqlite3 install tree)
Reason not applied: the only move is the sqlite3 6.x major line. Its release notes (2026-11-10) state only "bump all dependencies, SQLite, and modernise CI", with no behaviour list. 6.0.1 still depends on prebuild-install (`npm view sqlite3@6.0.1`), so the upgrade would not clear this finding.
Proposed change: replace the driver (see the sqlite3-unmaintained item below). No successor for prebuild-install is named upstream.

### [LOW] Known-Vulnerable Dependency — sqlite3 install/build tree   (AP-19)
File: package-lock.json (tar 6.2.1 under sqlite3)
Reason not applied: brace-expansion (→1.1.21) and ip-address (→10.7.6) were fixed in range by `npm audit fix --package-lock-only`. tar is fixable only through sqlite3 6.0.1, a major whose behaviour changes are not documented beyond a bundled-SQLite bump. The replay covers the queries this app runs, not the engine changes.
Proposed change: upgrade to sqlite3 ^6.0.1 in a dedicated change, then run the full replay plus `npm audit`. Or replace the driver.

### [HIGH] Deprecated or End-of-Life API Usage — sqlite3 unmaintained   (AP-14, missed-in-phase-2)
File: package.json:11-11
Reason not applied: replacing the database driver adds a runtime dependency (or a runtime feature) the application does not use today.
Proposed change: evaluate maintained alternatives (no successor named upstream). The swap is confined to src/models/database.js, because every repository goes through its `run`/`get`/`all`/`transaction` helpers.

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - AP-08 card/key logging: the fix changes stdout only, which no surface entry observes → verified by the re-audit's reading of the code, not by the replay (UNVERIFIED by harness).
  - AP-08 password storage (scrypt): the stored hash is never returned by any operation → not observable through the surface (UNVERIFIED by harness); verified by the re-audit's reading of src/models/password.js and schema.js.
  - AP-09 transaction rollback and DB-failure paths: no entry can make the datastore fail on demand → UNVERIFIED.
  - AP-20 UNIQUE/FK/CHECK constraints: no legitimate or hostile request reaches a violation (checkout reuses an existing email; course and enrollment ids are always resolved first), so no security entry could exercise them → UNVERIFIED.
  - AP-18 error page: security entry UNVERIFIED by rule (the original already answered 400). The body change is visible in the recorded text skeletons (baseline.json vs replay-2.json).
  - Report values: per-course `revenue` and `paid` amounts, and the pairing of each course with its revenue, are UNVERIFIED. The probe has no keyed, sorted or set comparison, and `matches` accepts only strings, so these numbers cannot be asserted without depending on an order the original does not guarantee. The replacement entry `get-financial-report-membership` checks only membership of course titles and student names. Supplementary, not counted: the retired positional entry HOLDS against baseline-recheck.json, a capture of the original whose order happened to match.
  - Retired value entry `get-financial-report-values`: removed from surface.json because it compared a nondeterministic order (protocol §5, D6.5). Its results stay, unedited, in baseline.json, baseline-recheck.json, replay.json and replay-2.json. A compare of those files still lists it as VIOLATED (against baseline.json) or HOLDS (against baseline-recheck.json). Neither result is counted.
Additional facts:
  - Baseline crash cascade (§3.1): `post-checkout-robustness#card=number` crashed the original (transport error). The later variants were recaptured, each crashing variant alone on its own fresh boot (card=boolean, list, empty-object, nested-object each crashed the original too). The report and delete robustness entries were recaptured together.
  - Container 15 (refactored-4, destructive replay of `post-checkout-card-not-string`) was booted and became ready, then the session was interrupted by an API rate limit before any request. On resume it was found alive and removed by its exact name; the entry was replayed on a new copy (refactored-5, container 16). No request ever reached container 15.
  - Express was upgraded 4.22.1 → 4.22.3 (same major), with the lockfile regenerated by npm (`npm audit fix --package-lock-only`, then `npm install express@^4.22.3 --package-lock-only`). The replay covers the routes; no contract header changed.
  - The scratch root was the environment's scratch directory. The snapshot directory was deleted at the end of the run, after confirming that no container with label `refactor-arch.run=202611110153-d896c00a` existed.
  - Follow-up run 202611111951-7cb55aaa (value-entry replacement, user decision B):
    - The original snapshot had already been deleted, so the original was re-created from the commit the audit read (`git archive 62f5e63 ecommerce-api-legacy`, the same 7 files; the tree was clean at that commit) and copied to a fresh run copy.
    - Two containers: the original (capture into baseline-values.json) and the refactored app (live compare into replay-values.json). Both were removed by exact name.
    - `docker ps -a --filter name=refactor-arch-` was empty before the run and after it, and the follow-up scratch directory was deleted.
Fixtures by reference: OPERATOR_TOKEN, CHECKOUT_PASSWORD
================================

## Execution Log — Phase 3

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 4 | 3a | start | container | …-d896c00a-2 | run-2: `npm ci`; `exec -d node src/app.js` | ready on 3000; full capture; crashed at card=number (transport error) |
| 5 | 3a | stop | container | …-d896c00a-2 | `docker rm -f` exact name | removed |
| 6–17 | 3a | start/stop ×6 | container | …-3 … …-8 | run-3 … run-8: fresh boot each; `--only` recaptures (report+delete robustness; card=boolean; card=list; card=empty-object; card=nested-object; delete-user-operator) | each removed by exact name |
| 18–21 | 3a | start/stop ×2 | container | …-9, …-10 | run-9, run-10: delete-user-anonymous; post-checkout-card-not-string | removed |
| 22–23 | 3c | start/stop | container | …-11 | refactored-1: first full replay, deprecation detectors on | removed |
| 24–25 | 3c | start/stop | container | …-12 | run-11 (original): recapture of contract + value entries → baseline-recheck.json | removed |
| 26–29 | 3c | start/stop ×2 | container | …-13, …-14 | refactored-2, -3: delete-user-operator; delete-user-anonymous | removed |
| 30–31 | 3c | start/stop | container | …-15 | refactored-4: ready, interrupted before any request | found alive on resume, removed by exact name |
| 32–33 | 3c | start/stop | container | …-16 | refactored-5: post-checkout-card-not-string | removed |
| 34–41 | 3d | start/stop ×4 | container | …-17 … …-20 | refactored-6 … -9: second full replay (detectors on in -17) + 3 destructive entries | removed |
| 42–43 | 3c (follow-up) | start/stop | container | refactor-arch-ecommerce-api-legacy-202611111951-7cb55aaa-1 | run-1 of the original (from `git archive 62f5e63`): checkouts + `get-financial-report-membership` → baseline-values.json | HOLDS; removed by exact name |
| 44–45 | 3c (follow-up) | start/stop | container | refactor-arch-ecommerce-api-legacy-202611111951-7cb55aaa-2 | refactored-1: live compare → replay-values.json | membership HOLDS; removed by exact name |
Total: 22 containers started (1 in Phase 2, 19 in Phase 3, 2 in the follow-up), 22 removed by exact name, 0 left running.
