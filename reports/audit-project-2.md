================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v24.12.0) + Express 4.22.1 (resolved from package-lock.json; manifest ^4.18.2) + sqlite3 5.1.7
Files:   3 analyzed | ~140 lines of code (180 physical lines)
Date:    2026-09-21 17:31
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    clean at 1f550f1
Runtime: installed the declared dependencies from package-lock.json (`npm ci`) into <snapshot>/deps/node_modules, outside the target; run copies resolve them through NODE_PATH

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:4-141
Description: The single class `AppManager` holds schema DDL and seed data (lines 10-23), route registration and request parsing (25-35, 80, 131), business rules (payment approval at 46, account auto-creation at 66-72, revenue computation at 108-110), persistence (every `db.run/get/all`), and response formatting (60, 112-115, 135) — five responsibility categories in one unit; `setupRoutes` alone spans 113 lines and nests callbacks seven levels deep. Kept at the CRITICAL default; escalation conditions also hold (every request passes through it; it logs a credential, see the AP-08 finding at line 45).
Impact: Nothing can be tested without an Express app and a live SQLite connection; every change to checkout, reporting or user deletion lands in the same method, so any edit is a global risk.
Recommendation: Split by responsibility into config / models (repositories + domain rules) / controllers / routes with a composition root — see RP-03, RP-05, RP-06.
Contract: safe

### [CRITICAL] Business Logic in the Delivery Layer   (AP-05)
File: src/AppManager.js:28-78
Description: The `POST /api/checkout` route handler decides payment approval (`cc.startsWith("4")`, line 46), creates accounts with a default password (66-72), and runs the enroll → pay → audit workflow with driver calls inline (37-63); the `GET /api/admin/financial-report` handler (80-129) computes revenue (`status === 'PAID'`, 108-110) inside the same callbacks that query. Escalated from HIGH to CRITICAL because the handlers also perform persistence and formatting inside the God Class (AP-03 escalation condition).
Impact: The checkout and revenue rules cannot be exercised or reused without HTTP; a second entry point (a batch job, an admin CLI) would have to copy them.
Recommendation: Extract checkout and report use cases into controllers and the rules into models; handlers become parse → call → render — see RP-05.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — card data and gateway key logged   (AP-08)
File: src/AppManager.js:45-45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` writes the full card number from the request body and the live payment-gateway key to stdout on every checkout (observed in the run-1 log of the original: `Processando cartão 4111222233334444 na chave pk_live_...`). Escalated from HIGH to CRITICAL: payment card data and a credential written to a log.
Impact: Anyone with log access (log shipper, aggregation service, support staff) obtains full card numbers and the gateway key; logs are retained and replicated far beyond the database's access control.
Recommendation: Remove the card number and key from the log; log only a masked reference if anything — see RP-08.
Contract: safe

### [CRITICAL] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:50-63
Description: The checkout's three writes (enrollment 50, payment 54, audit log 57) run with no transaction; a payment-insert failure leaves an enrollment with no payment, and the audit-log callback ignores its `err` and answers 200 regardless (57-60). Other sites: `DELETE /api/users/:id` ignores the driver error and always reports success (133-135); the report's inner callbacks ignore `err` and dereference `enrollments.length` on it (92-93), which throws inside a driver callback and kills the process; every handler hand-writes its own `res.status(500).send(...)` mapping (38, 41, 51, 55, 70, 84) and no error middleware is registered. Escalated from HIGH to CRITICAL: a swallowed failure silently discards a persisted write (the audit record).
Impact: The system reports success while losing the audit trail and can persist half a purchase; any unexpected exception in a callback terminates the whole server for every client.
Recommendation: Domain error taxonomy + one error boundary; a transaction around enrollment+payment+audit; propagate driver errors instead of ignoring them — see RP-09.
Contract: safe (status codes and bodies on every non-failure path are preserved; only failure paths that currently lie or crash change)

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes any user by path id with no authentication or ownership check; `GET /api/admin/financial-report` (line 80) exposes every student's name and amount paid to any anonymous caller; and `POST /api/checkout` acts on an existing account identified only by `eml` — the `pwd` field is never checked for existing users (40, 73-75). The application has no identity model at all. Kept at CRITICAL, maximum urgency: the unprotected operations are destructive and expose personal and financial data.
Impact: Any caller can delete any account, read the whole revenue/student ledger, and enroll purchases into someone else's account by knowing their email.
Recommendation: Introduce an identity model (authentication middleware), an admin role for the report and deletion, and require the account password (or a session) at checkout — see RP-04.
Contract: contract-changing: there is no identity model, so every current client would start receiving 401/403 on these routes (legitimate-use test, 04 §6).

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: The exported `config` object carries literal credentials: `dbPass: "senha_super_secreta_prod_123"` (line 3), `paymentGatewayKey: "pk_live_1234567890abcdef"` (4, a live-key prefix), plus `dbUser` and `smtpUser` identities, all committed to source. Aggravating: the gateway key is also printed to the log (AP-08 finding above).
Impact: Everyone with read access to the repository, any fork, and every log reader holds a production database password and a live payment key; rotation requires a code change and they stay in git history forever.
Recommendation: Move secrets to environment configuration read once by a config module, ship a `.env.example`, ignore `.env`, and rotate the committed values — see RP-01.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password storage   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` "hashes" a password by repeating the first two base64 characters of the password 10000 times and truncating to 10 characters — no salt, no work factor, and the output reveals the password's first characters while colliding for every password with the same prefix. Other sites: the seed stores the account password `'123'` in plain text in the runtime datastore (src/AppManager.js:18); checkout assigns the fixed fallback password `"123456"` when `pwd` is omitted (src/AppManager.js:68). Escalated from HIGH to CRITICAL: passwords are stored recoverably (the seed row).
Impact: One read of the users table yields the seeded password outright and the prefix of every other one; every account created without a password shares a known credential.
Recommendation: Use a purpose-built password KDF from the runtime's standard library (scrypt, per-credential salt) and hash the seed; the fallback password requires a product decision — see RP-08.
Contract: contract-changing (partly): replacing the digest and hashing the seed are safe (the stored value is never returned); removing the `"123456"` fallback means making `pwd` required for new accounts, which rejects requests clients send today.

### [HIGH] Known-Vulnerable Dependency — sqlite3 (deprecated upstream)   (AP-19)
File: package.json:9-9
Description: `sqlite3` resolves to 5.1.7. Upstream marks the package deprecated and unmaintained — README headed "[DEPRECATED] node-sqlite3 … currently unmaintained", repository archived (Tier C, github.com/TryGhost/node-sqlite3, looked up 2026-09-21) — and its install-time toolchain carries 7 of the 12 `npm audit` advisories, including critical GHSA-34x7-hfp2-rc4v / GHSA-8qq5-rm4j-mr97 et al. in `tar` 6.2.1, plus `ip-address` GHSA-mwp4-54f8-5fhr, `brace-expansion` GHSA-mh99-v99m-4gvg, `@tootallnate/once` GHSA-vpq2-c234-7xj6 (Tier B, npm audit / GitHub Advisory DB, 2026-09-21); the lockfile also flags `tar`, `glob`, `inflight`, `rimraf`, `npmlog`, `gauge`, `are-we-there-yet`, `prebuild-install`, `@npmcli/move-file` as deprecated. Severity set by the deprecation (unsupported package with no maintained upgrade line: HIGH), not by the advisories, which alone would be LOW (the vulnerable packages run only at install/build time: node-gyp, prebuild-install, tar). Reported once here per the AP-14/AP-19 overlap rule.
Impact: The application's only datastore driver will receive no further fixes; the install step pulls a toolchain with a critical path-traversal advisory into every build machine.
Recommendation: Upgrade to sqlite3 6.0.1 (fixes the tar/node-gyp chain per npm audit; major upgrade — apply only if the replay covers the driver behaviour) and plan a replacement driver; upstream names no successor — candidate: the runtime's built-in `node:sqlite` module (present on v24.12.0 but emitting an ExperimentalWarning, observed 2026-09-21) — see RP-18, RP-14.
Contract: contract-changing for the driver replacement (upstream names no successor; RP-14 step 5 → propose); the 6.0.1 upgrade is safe only if the replay passes.

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:5-8
Description: The constructor opens its own `new sqlite3.Database(':memory:')`; the module imports the global `config` from `utils` at load time (line 2); `src/app.js:5-14` binds the port as an import-time side effect (`app.listen` at module top level) and exports nothing, so the application cannot be constructed without listening.
Impact: No unit can be tested with a substitute database; the app cannot be created twice in one process or started on another port without editing source.
Recommendation: Composition root that loads config, creates the connection, constructs repositories/controllers and registers routes; export a factory — see RP-06.
Contract: safe

### [HIGH] Missing Boundary Validation — wrong-typed input crashes the process   (AP-11)
File: src/AppManager.js:29-35
Description: The checkout reads `usr/eml/pwd/c_id/card` from the body and checks only truthiness (35). A numeric `card` reaches `cc.startsWith` (46) and throws inside a driver callback — observed: the original process exited with `TypeError: cc.startsWith is not a function` after a request with `"card": 4111`, having already inserted the user row. A numeric `pwd` for a new user reaches `Buffer.from(pwd)` (utils.js:20) with the same failure mode. Escalated from MEDIUM to HIGH: the unvalidated value reaches the datastore and a single anonymous request takes the service down.
Impact: Any client can stop the server with one malformed request, and each attempt leaves an orphan user row behind.
Recommendation: A boundary schema at the checkout: string fields must be strings; reject with the existing 400 "Bad Request" — see RP-11.
Contract: safe (a value of the wrong type is invalid on its face — legitimate-use test); covered by security entries.

### [HIGH] Insecure Runtime Configuration — framework default error output   (AP-18)
File: src/app.js:5-10
Description: No error middleware is registered and nothing sets the runtime mode (`npm start` = `node src/app.js`, no `NODE_ENV`). Observed: a malformed JSON body to `POST /api/checkout` returns 400 with the framework's default HTML page containing the full stack trace and absolute filesystem paths of the server's dependency tree.
Impact: Every malformed request maps the server's internals (paths, module layout, library versions) for an attacker.
Recommendation: Register a centralized error boundary that keeps the status code and returns a generic body, logging details internally — see RP-17, RP-09.
Contract: safe (status code preserved; internals in an error body are not something a legitimate client relies on — RP-17)

### [MEDIUM] Known-Vulnerable Dependency — express transitive advisories   (AP-19)
File: package.json:8-8
Description: `express` 4.22.1 (lockfile) pulls `path-to-regexp` 0.1.12 (GHSA-37ch-88jc-xwx2, HIGH), `qs` 6.14.2 (GHSA-4mjr-xmp4-gh2g, GHSA-x5fp-wj9c-mxmx, GHSA-q8mj-m7cp-5q26, MODERATE) and `body-parser` 1.20.4 (GHSA-v422-hmwv-36x6, LOW) — Tier B, OSV.dev and npm audit, 2026-09-21. OSV reports no advisory on express 4.22.1 itself. De-escalated from HIGH to MEDIUM: none of the vulnerable features is reachable — the only parameterized route has one parameter per segment (the ReDoS needs three), the app never calls `qs.stringify` and express parses queries with `allowPrototypes` only, not `comma` (node_modules/express/lib/utils.js:289-290), and `express.json()` is called with no `limit` (default 100kb applies).
Impact: The advisories are dormant today but become live the moment someone adds a multi-parameter route or a body-size option.
Recommendation: Upgrade express within the 4.x line to 4.22.3, which requires path-to-regexp ~0.1.13, qs ~6.16.0, body-parser ~1.20.5 (npm registry, 2026-09-21); regenerate the lockfile with npm — see RP-18.
Contract: safe (same major version)

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-128
Description: The financial report reads all courses, then per course queries enrollments (92), then per enrollment queries the user (104) and the payment (106): 1 + C + 2E round trips, with revenue summed in application code (108-110) instead of in the datastore.
Impact: Report latency grows linearly with enrollments; on a file or networked database this becomes the slowest endpoint, reachable anonymously (AP-04).
Recommendation: One set-based query with LEFT JOINs, preserving the 'Unknown'/0 fallbacks — see RP-10.
Contract: safe

### [MEDIUM] Missing Boundary Validation — deletion leaves orphaned records   (AP-11)
File: src/AppManager.js:133-135
Description: `DELETE FROM users WHERE id = ?` runs with no check or cascade for the user's enrollments and payments; the response text itself says so ("as matrículas e pagamentos ficaram sujos no banco"). The schema declares no foreign keys (12-15). The financial report then lists the orphaned enrollment as student 'Unknown'.
Impact: Deleted users' payments keep counting in revenue under an anonymous name; the domain relationship user → enrollment → payment is enforced nowhere.
Recommendation: Decide the policy (cascade, soft-delete or refuse while enrollments exist) and enforce it in the model — see RP-11.
Contract: contract-changing: any policy changes the report's content for deleted users and/or the DELETE response (the current body announces the orphaning).

### [MEDIUM] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: Module-level `globalCache` is mutated by `logAndCache` on every successful checkout (AppManager.js:59) and never read, never bounded, never evicted; `let totalRevenue` is exported as a mutable module variable. De-escalated from HIGH to MEDIUM: nothing reads the state, so behaviour does not depend on it; the remaining impact is an unbounded accumulator (AP-13, folded here).
Impact: Memory grows with the number of distinct buyers for the process's lifetime; the exported variables invite future code to share state across requests.
Recommendation: Remove the write-only cache and the unused counter — see RP-07, RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: Single-letter locals `u, e, p, cid, cc` hold the whole checkout input across a 50-line scope; `badCrypto` (utils.js:17) names how rather than what; `logAndCache` does two unrelated things; `AppManager` is a "manager" name for a class with no single concept; identifiers are English while all log and response strings are Portuguese. (The request fields `usr/eml/pwd/c_id/card` are public contract and are not in scope.)
Impact: Readers cannot tell what a variable holds without tracing it back; misleading unit names hide their risk.
Recommendation: Rename internals for intent while splitting the module — see RP-16.
Contract: safe (internal names only)

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-48
Description: The approval rule `cc.startsWith("4")`, the payment states `"PAID"`/`"DENIED"` repeated as bare strings (21, 46, 48, 108), the fallback password `"123456"` (68), the hash parameters `10000`/`2`/`10` (utils.js:19-22) and the port `3000` inline in config (utils.js:6).
Impact: The simulated payment rule and the status vocabulary are agreed by memory across seed, checkout and report; a typo silently creates a new status.
Recommendation: Named constants for payment status and approval rule; port from configuration — see RP-15.
Contract: safe

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/utils.js:2-5
Description: `config.dbUser`, `config.dbPass` and `config.smtpUser` are never read anywhere; `totalRevenue` is imported into AppManager.js (line 2) and never used; `self` (AppManager.js:26) exists only to reach `db` inside `function` callbacks.
Impact: Readers assume a database login and SMTP integration exist; they do not.
Recommendation: Delete the unused members and imports — see RP-16.
Contract: safe

## Catalog Coverage

| Entry | Result |
|---|---|
| AP-01 | 1 finding: [CRITICAL] src/utils.js:1-7 (seed and fallback passwords filed under AP-08) |
| AP-02 | none — all 11 SQL statements that take input pass `?` placeholders with a separate parameter array (the 9 DDL/seed statements are constant strings); no shell, filesystem path, deserialization or template construction from input |
| AP-03 | 1 finding: [CRITICAL] src/AppManager.js:4-141 |
| AP-04 | 1 finding: [CRITICAL] src/AppManager.js:131-137 (covers the report route and the checkout account takeover) |
| AP-05 | 1 finding: [CRITICAL] src/AppManager.js:28-78 |
| AP-06 | 1 finding: [HIGH] src/AppManager.js:5-8 |
| AP-07 | 1 finding: [MEDIUM] src/utils.js:9-15 |
| AP-08 | 2 findings: [CRITICAL] src/AppManager.js:45-45 (logging), [CRITICAL] src/utils.js:17-23 (password storage) |
| AP-09 | 1 finding: [CRITICAL] src/AppManager.js:50-63; default handler behaviour observed from the snapshot and filed as AP-18 |
| AP-10 | 1 finding: [MEDIUM] src/AppManager.js:83-128 |
| AP-11 | 2 findings: [HIGH] src/AppManager.js:29-35, [MEDIUM] src/AppManager.js:133-135 |
| AP-12 | none — the report's completion-counter block repeats (95-99, 117-122) but is under the ~10-line threshold; the repeated 500 mappings are counted in AP-09 |
| AP-13 | folded — the unbounded accumulator is in the AP-07 finding; whole-table reads in AP-10; no outbound network calls exist, so no timeout gap |
| AP-14 | none as a separate finding — Layer 1 (node --pending-deprecation --trace-deprecation, boot + exercised routes) emitted no warning; the sqlite3 upstream deprecation is reported under AP-19 per the overlap rule |
| AP-15 | 1 finding: [LOW] src/AppManager.js:46-48 |
| AP-16 | 1 finding: [LOW] src/AppManager.js:29-33 |
| AP-17 | 1 finding: [LOW] src/utils.js:2-5 |
| AP-18 | 1 finding: [HIGH] src/app.js:5-10 |
| AP-19 | 2 findings: [HIGH] package.json:9-9 (sqlite3), [MEDIUM] package.json:8-8 (express) |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Runtime deprecation warnings (boot + all routes) | node v24.12.0 | deprecation | A | `node --pending-deprecation --trace-deprecation` run of the original, run-1 | n/a — local | no warning emitted |
| express | 4.22.1 | deprecation | B | `npm view express@4.22.1 deprecated` | 2026-09-21 | no issue found |
| express | 4.22.1 | advisory | B | OSV.dev query | 2026-09-21 | no advisory on express itself |
| path-to-regexp (via express) | 0.1.12 | advisory | B | OSV.dev GHSA-37ch-88jc-xwx2 | 2026-09-21 | AP-19 [MEDIUM] express |
| qs (via express) | 6.14.2 | advisory | B | OSV.dev GHSA-4mjr-xmp4-gh2g, GHSA-x5fp-wj9c-mxmx, GHSA-q8mj-m7cp-5q26 | 2026-09-21 | AP-19 [MEDIUM] express |
| body-parser (via express) | 1.20.4 | advisory | B | OSV.dev GHSA-v422-hmwv-36x6 | 2026-09-21 | AP-19 [MEDIUM] express |
| sqlite3 | 5.1.7 | deprecation | C | github.com/TryGhost/node-sqlite3 README ("[DEPRECATED] … unmaintained"), repository archived; v6.0.0 release notes "Mark repository as unmaintained" | 2026-09-21 | AP-19 [HIGH] sqlite3 |
| sqlite3 | 5.1.7 | deprecation (registry) | B | `npm view sqlite3@5.1.7 deprecated` | 2026-09-21 | not flagged in the registry |
| sqlite3 | 5.1.7 | advisory | B | OSV.dev query | 2026-09-21 | no advisory on sqlite3 itself |
| tar, node-gyp, cacache, make-fetch-happen, http-proxy-agent, @tootallnate/once, ip-address, brace-expansion (via sqlite3) | 6.2.1, 8.4.1, 15.3.0, 9.1.0, 4.0.1, 1.1.2, 10.1.0, 1.1.12 | advisory | B | npm audit (GitHub Advisory Database) | 2026-09-21 | AP-19 [HIGH] sqlite3 |
| tar, glob, inflight, rimraf, npmlog, gauge, are-we-there-yet, prebuild-install, @npmcli/move-file (via sqlite3) | per lockfile | deprecation | B | `deprecated` field in package-lock.json / npm ci warnings | 2026-09-21 | AP-19 [HIGH] sqlite3 |
| Distance from current | express 4.22.1 → 4.22.3 (latest-4), 5.2.1 (latest); sqlite3 5.1.7 → 6.0.1 | outdated | B | `npm outdated`, `npm view <pkg> dist-tags` | 2026-09-21 | informs AP-19 recommendations |

## Verification Coverage
Full — all planned checks executed (Layer 1 forced-deprecation run of the original from the snapshot; Layer 2 OSV.dev, npm registry, npm audit, npm outdated and upstream repository lookups).

## Proposed, Not Applied
To be determined in Phase 3.

================================
Total: 18 findings
================================

Phase 2 complete. --yes was passed: the confirmation prompt is skipped and Phase 3 proceeds as `y`
(apply all findings; contract-changing items will be proposed, not applied).

---

# Phase 3 — Final Report (appended 2026-09-21 17:45)

Gate answer: `--yes` (auto-approved, not human-reviewed) — behaved as `y`: all severities in scope.
Layout: HTTP service → literal MVC under `src/`: `config/`, `models/` (entities, rules and their
repositories — persistence kept inside the model layer, uniformly), `controllers/`, `routes/` (the
View layer: this API renders JSON/plain text, so routes are its views), `middlewares/`, and
`src/app.js` as composition root. `npm start` (`node src/app.js`) is unchanged.

## Resolution per Phase 2 finding

| Phase 2 finding | Transformation | Outcome |
|---|---|---|
| [CRITICAL] AP-03 src/AppManager.js:4-141 | RP-03 | resolved — class split into config / models / controllers / routes / middlewares; file removed |
| [CRITICAL] AP-05 src/AppManager.js:28-78 | RP-05 | resolved — handlers are parse → call → render; rules in models/payment.js, use cases in controllers |
| [CRITICAL] AP-08 src/AppManager.js:45-45 | RP-08 | resolved — log carries only the masked card (`****1234`); key not logged; error boundary logs stacks, never the raw request body |
| [CRITICAL] AP-09 src/AppManager.js:50-63 | RP-09 | resolved — enrollment+payment+audit in one transaction; delete/report/audit failures propagate; single error boundary |
| [CRITICAL] AP-04 src/AppManager.js:131-137 | RP-04 | **proposed** — see below |
| [CRITICAL] AP-01 src/utils.js:1-7 | RP-01 | resolved — literals removed (dbUser/dbPass/smtpUser were never read; the gateway key was only logged); config module reads env; `.env.example` + `.gitignore` added. **Owner action: rotate the committed database password and payment key — they remain in git history.** |
| [CRITICAL] AP-08 src/utils.js:17-23 | RP-08 | **proposed** (partly fixed) — fixed: scrypt KDF with per-credential salt (models/password.js), seed password hashed and taken from `SEED_USER_PASSWORD` or random; held back: the `"123456"` fallback for accounts created without `pwd` |
| [HIGH] AP-19 package.json:9-9 (sqlite3) | RP-18, RP-14 | **proposed** (partly fixed) — fixed: sqlite3 5.1.7 → 6.0.1 (major; applied because the replay exercises every driver call the app makes — DDL, insert/lastID, get, all, transactions — and passed); npm audit now 0 vulnerabilities; held back: replacing the deprecated/archived driver |
| [HIGH] AP-06 src/AppManager.js:5-8 | RP-06 | resolved — composition root builds the graph; `createApp()` factory; no import-time side effect |
| [HIGH] AP-11 src/AppManager.js:29-35 | RP-11 | resolved — boundary schema rejects non-string usr/eml/card/pwd with the existing 400 "Bad Request"; 3 security entries FIXED |
| [HIGH] AP-18 src/app.js:5-10 | RP-17 | resolved — error boundary keeps status codes, returns generic bodies; verified manually (see Verification Coverage) |
| [MEDIUM] AP-19 package.json:8-8 (express) | RP-18 | resolved — express 4.22.1 → 4.22.3 (same major); path-to-regexp 0.1.13, qs 6.16.0, body-parser 1.20.8; OSV/npm audit clean |
| [MEDIUM] AP-10 src/AppManager.js:83-128 | RP-10 | resolved — two set-based queries (models/repositories.js ReportRepository), first-payment rule preserved |
| [MEDIUM] AP-11 src/AppManager.js:133-135 | RP-11 | **proposed** — see below |
| [MEDIUM] AP-07 src/utils.js:9-15 | RP-07 | resolved — write-only cache and exported counter deleted |
| [LOW] AP-16 src/AppManager.js:29-33 | RP-16 | resolved — internal names for intent; request field names untouched (contract) |
| [LOW] AP-15 src/AppManager.js:46-48 | RP-15 | resolved — `PaymentStatus`, `APPROVED_CARD_PREFIX`, `DEFAULT_PORT`, `GENERIC_DB_ERROR`, KDF sizes named |
| [LOW] AP-17 src/utils.js:2-5 | RP-16 | resolved — unused config members, import and alias removed |

Behaviour notes (preserved on purpose, not findings): an account created during a checkout whose
payment is then declined is still persisted, as before; a failed course lookup still answers 404;
`DELETE` of a non-existent id still answers 200 with the same text. The financial report's array
order is now deterministic (by course id, then enrollment id); before, it followed callback
completion order, which the original did not guarantee — values were checked identical outside the
protocol (see Verification Coverage).

## Re-audit (3d) — same catalog, same thresholds, complete (Layer 1 and Layer 2 both ran)

| # | Re-audit finding | Partition |
|---|---|---|
| 1 | [CRITICAL] AP-04 src/routes/adminRoutes.js:8-23 — admin report and user deletion unauthenticated; checkout still acts on an existing account by email alone | proposed-not-applied |
| 2 | [CRITICAL] AP-08 src/controllers/checkoutController.js:10-12 — fixed fallback password for accounts created without `pwd` | proposed-not-applied |
| 3 | [HIGH] AP-19 package.json:11-11 — sqlite3 6.0.1 still deprecated/archived upstream (Tier C); lockfile still flags `prebuild-install` 7.1.3 deprecated; no advisories (OSV, npm audit, 2026-09-21) | proposed-not-applied |
| 4 | [MEDIUM] AP-11 src/routes/adminRoutes.js:16-23 — user deletion still orphans enrollments/payments | proposed-not-applied |
| 5 | [MEDIUM] AP-11 src/models/schema.js:9-9 — `users.email` has no uniqueness constraint; checkout does look-up-then-insert (src/controllers/checkoutController.js:44-47), so concurrent checkouts with a new email create duplicate accounts | unresolved — origin `missed-in-phase-2` (the original had the same look-up-then-insert at src/AppManager.js:40-72 with the same schema) |

Counts: 5 findings — 4 proposed-not-applied, 1 unresolved (0 failed, 0 introduced, 1 missed-in-phase-2).

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── .gitignore
├── api.http
├── package.json
├── package-lock.json
├── README.md
├── reports/
│   ├── audit-20260921-1731.md
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
    │   └── errorBoundary.js
    ├── models/
    │   ├── database.js
    │   ├── errors.js
    │   ├── password.js
    │   ├── payment.js
    │   ├── repositories.js
    │   └── schema.js
    └── routes/
        ├── adminRoutes.js
        └── checkoutRoutes.js

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 13 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 3 FIXED, 0 NOT FIXED
  ○ Findings resolved: 14/18  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 4 proposed-not-applied, 1 unresolved  (re-audit: 5 findings)

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/AppManager.js:131-137 (now src/routes/adminRoutes.js:8-23 and src/controllers/checkoutController.js:44-47)
Reason not applied: the application has no identity model; any authentication or admin check would answer 401/403 to every current client of `GET /api/admin/financial-report` and `DELETE /api/users/:id`, and requiring the account password at checkout for existing emails would reject requests clients send today.
Proposed change: define principals and an admin role; add an authentication middleware; enforce the admin policy in the report and user controllers (RP-04); verify `pwd` (or a session) before acting on an existing account. Needs a product decision and client coordination.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password storage   (AP-08)
File: src/utils.js:17-23 (remaining part now at src/controllers/checkoutController.js:10-12)
Reason not applied: applied — scrypt KDF and hashed seed. Held back — removing the `"123456"` fallback means making `pwd` required for new accounts (a previously optional field becomes required: clients that omit it would start receiving 400).
Proposed change: require `pwd` for new accounts, or create them with no usable credential plus a reset flow; decide with the product owner.

### [HIGH] Known-Vulnerable Dependency — sqlite3 (deprecated upstream)   (AP-19)
File: package.json:9-9 (now package.json:11-11)
Reason not applied: applied — upgrade to 6.0.1 closed every advisory (npm audit: 0). Held back — the package itself is deprecated and archived upstream and upstream names no successor (RP-14 step 5: propose). The runtime's built-in `node:sqlite` exists on v24.12.0 but emitted an ExperimentalWarning when loaded (observed 2026-09-21), and its API is synchronous, so the swap is a rewrite of models/database.js, not a drop-in.
Proposed change: choose a maintained SQLite binding (or `node:sqlite` once stable on the deployed runtime); only models/database.js and app.js need to change; re-run this replay.

### [MEDIUM] Missing Boundary Validation — deletion leaves orphaned records   (AP-11)
File: src/AppManager.js:133-135 (now src/routes/adminRoutes.js:16-23)
Reason not applied: any policy (cascade, soft-delete, refuse while enrolled) changes observable output — deleted users' rows would vanish from, or stay differently in, the financial report, and the DELETE body currently announces the orphaning.
Proposed change: pick the policy, add foreign keys (`PRAGMA foreign_keys = ON`) and enforce it in UserController; update the DELETE message accordingly.

## Verification Coverage
Full — every planned check ran: Layer 1 forced-deprecation runs of the original (snapshot run copies) and of the refactored app (no warning either time); Layer 2 lookups (OSV.dev, npm registry, npm audit, upstream repository) in Phase 2 and again in the re-audit; baseline capture and replay of all 16 inventory entries, none skipped. Notes that define what was verified:
  - AP-18 (default error page with stack trace) was verified outside the harness: the harness always sends JSON-encoded bodies, so a malformed body cannot be expressed as an entry, and its intended effect (no internals in a 400 body) is not a rejection, so it cannot be a security entry (06 §2.1). Manual check with curl: original → 400 text/html with stack trace and absolute paths; refactored → 400 text/html "Bad Request", and the log line carries no request body.
  - Text bodies were compared as masked line skeletons (06 §5.1–5.2: ISO timestamps, UUIDs, hex runs ≥16 and digit runs masked).
  - Response values (beyond shapes) were additionally compared for every contract entry with a scratch script against a fresh original: identical except the report's array order, which the original did not guarantee.
  - Two security entries crashed the original; per 06 §3.1 the second was recaptured on a fresh run copy (`--only … --merge`), so both baseline states are the real crash (`ERROR`).
  - Two entries were added after the first capture (`post-api-checkout-without-json-body`, `post-api-checkout-email-wrong-type`) and captured against the original first (06 §4.3).
Snapshot directory deleted at the end of Phase 3 (`<scratchpad>/refactor-arch-ecommerce-api-legacy-20260921-1723`).
================================
