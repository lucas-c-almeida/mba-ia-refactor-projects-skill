## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        ecommerce-api-legacy
Language:      JavaScript (Node.js; no `engines` declared — host runtime v24.12.0)
Framework:     Express 4.22.1 (resolved from package-lock.json; manifest range ^4.18.2)
Dependencies:  express ^4.18.2 (4.22.1), sqlite3 ^5.1.6 (5.1.7) — runtime; no dev dependencies
Domain:        LMS course sales — checkout of courses (users, courses, enrollments, payments) with an admin financial report
App type:      HTTP service (3 routes: POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
Architecture:  None — one class holds schema/seed, persistence, business rules and route handlers; config, cache and hashing in a utils grab-bag
Source files:  3 files analyzed (src/*.js; excluded: node_modules/, .claude/, reports/, lockfile, docs, .gitignore matches)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite in-memory, DDL + seed at boot)
Boot:          node src/app.js (from `npm start` script body), cwd = target root
Port:          3000 — fixed in source (src/utils.js config.port), no override read
Runtime env:   Node 24 (no version declared); express/sqlite3 installed with `npm ci` from package-lock.json inside the run container
Isolation:     container (docker 28.5.2, image node:24); container commands from PowerShell (native shell)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js 24) + Express 4.22.1 + sqlite3 5.1.7
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-01 15:50
Mode:    full
Confirmation: human-confirmed: y
Tree:    clean at 78195c9
Runtime: installed the declared dependencies from package-lock.json (`npm ci`) inside each run container (run copies in the scratch root, outside the target); the container's Node is 24.21.0 (image node:24), the host's 24.12.0
Isolation: container (docker 28.5.2, image node:24)
Scratch: environment scratch directory  (protocol §1.1)

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:1-141
Description: One class holds several unrelated domain concepts (checkout, financial reporting, user administration) and four responsibility categories: schema DDL and seed data (10-23), persistence (driver calls throughout 37-133), business rules — payment approval by card prefix (46), user auto-creation with a default password (66-72), revenue aggregation (108-110) — and delivery: route registration, request parsing and status/response selection (25-138). The checkout handler nests callbacks seven levels deep (28-78) and is ~50 lines; the report handler builds the presentation shape inline (89-127). Business logic in the handlers (AP-05) is filed here, per the precedence rule.
Impact: Nothing can be tested without a live database and an Express app; every change to any of the three use cases touches the same file and the same callback pyramid; the payment rule cannot be reused or changed without editing a route.
Recommendation: Split into models (repositories per table group + domain rules), controllers (checkout, report, user admin use cases), routes, config, and a composition root — see RP-03 and RP-05.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — card number and gateway key logged   (AP-08)
File: src/AppManager.js:45-45
Description: The checkout handler logs the full card number (`cc`) together with the payment gateway key on every checkout (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`), observed in the run log of the original. Escalated from HIGH to CRITICAL: payment-card data and a live credential are written recoverably to the process log.
Impact: Anyone with access to the logs (or wherever stdout is shipped) obtains full card numbers and the gateway key; this alone puts the system out of PCI scope compliance.
Recommendation: Remove the card number and the key from the log; log a masked last-four and an opaque correlation id at most — see RP-08.
Contract: safe

### [CRITICAL] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:50-63
Description: Checkout performs three dependent writes (enrollment, payment, audit log) with no transaction; a failure of the second leaves an enrollment without payment, and the audit-log insert's error is ignored and the request still answers success (57-61). DELETE /api/users/:id ignores its error argument and always answers 200 "deleted" (133-135). The report handler ignores `err` and dereferences `enrollments.length` (92-93), so a query error crashes the process. No error middleware is registered anywhere (src/app.js:5-10); each handler hand-formats its own error text. Escalated from HIGH to CRITICAL: a swallowed failure silently discards a persisted write (the audit row, the delete) while reporting success.
Impact: The system reports success for writes that did not happen, leaves half-applied checkouts, and an unexpected DB error terminates the whole service.
Recommendation: Wrap the checkout writes in one transaction, propagate driver errors to a single error middleware that keeps the application's own status codes and texts — see RP-09.
Contract: safe (the application's own error statuses and texts are kept; only unhandled failures change from crash/false success to a 500)

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/AppManager.js:131-137
Description: DELETE /api/users/:id deletes any user by the path id with no authentication or ownership check; GET /api/admin/financial-report (80-129) exposes every student's name and payment amounts to any caller. The application has no identity model at all (no login, session or token). Flagged at maximum urgency: the unprotected operations are destructive and expose personal and financial data.
Impact: Any anonymous client can delete accounts and read the full revenue report with student names.
Recommendation: Introduce an identity model and an admin policy, enforced on the operations — see RP-04.
Contract: contract-changing — with no identity model, every current client (all anonymous) would start receiving 401/403 on both routes; this requires a product decision on principals and policy.

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: The config object holds literal credentials: `dbPass: "senha_super_secreta_prod_123"`, `dbUser`, and a live-prefixed `paymentGatewayKey: "pk_live_1234567890abcdef"`, plus `smtpUser`. Further sites: the boot seed creates a user with the literal password `'123'` stored in plain text in the runtime database (src/AppManager.js:18), and checkout falls back to the working password `"123456"` when none is sent (src/AppManager.js:68).
Impact: Anyone with repository access holds the database password and the payment key; rotation needs a code change; every environment boots with an account whose password is known.
Recommendation: Move secrets to environment-read configuration that fails loudly when a required secret is missing, ship a `.env.example` with placeholders, and remove the known-password defaults — see RP-01.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — reversible password "hash"   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` base64-encodes the password, keeps its first two characters, repeats them, and truncates to 10 characters — no salt, no KDF; the result depends only on the first ~1.5 characters of the password, so it is reversible to that prefix and collides massively. It is the only password storage path (src/AppManager.js:68-69). Escalated from HIGH to CRITICAL: passwords are stored recoverably.
Impact: A single read of the users table discloses password prefixes and makes all passwords sharing a prefix equivalent; reused passwords on other systems are exposed.
Recommendation: Replace with a purpose-built KDF available in the runtime's standard library (salted scrypt), no new dependency — see RP-08.
Contract: safe (no response returns the stored hash)

### [HIGH] Known-Vulnerable Dependency — sqlite3 install toolchain   (AP-19)
File: package.json:11-11
Description: `npm audit` (GitHub Advisory Database, 2026-10-01) reports, through sqlite3 5.1.7, `tar` 6.2.1 (<=7.5.20: GHSA-23hp-3jrh-7fpw rated critical, GHSA-34x7-hfp2-rc4v / GHSA-8qq5-rm4j-mr97 / GHSA-r292-9mhp-454m and others rated high — path traversal and DoS during extraction), plus `node-gyp`, `cacache`, `make-fetch-happen`, `http-proxy-agent`, `@tootallnate/once`, `brace-expansion` (high) and `ip-address` (high) in the same install toolchain. The registry also flags as deprecated, at install time on 2026-10-01: `prebuild-install@7.1.3` ("No longer maintained"), `tar@6.2.1`, `glob@7.2.3`, `rimraf@3.0.2`, `inflight@1.0.6`, `npmlog@6.0.2`, `gauge@4.0.4`, `are-we-there-yet@3.0.1`, `@npmcli/move-file@1.1.2` (AP-14, reported here once). These packages run at install/build time (extracting the prebuilt binary), and the tar advisories concern exactly that phase, so no LOW de-escalation; reachability from a malicious archive could not be established either way → HIGH (default).
Impact: Installing the application extracts a downloaded archive with a tar implementation that has published path-traversal advisories; the toolchain is unmaintained and receives no fixes.
Recommendation: The fix named by npm audit is sqlite3 6.0.1 — a major upgrade (registry: engines node >=20.17.0, depends on tar ^7.5.10) — see RP-18.
Contract: safe only if the replay covers it (major upgrade, guidelines §6): applied in Phase 3 if the full replay passes on 6.x, proposed otherwise.

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:5-8
Description: The class opens its own database (`new sqlite3.Database(':memory:')`) in its constructor and imports the module-level config object directly (line 2); handlers reach the shared `this.db` and `config` instead of receiving collaborators. src/app.js does partial wiring but also constructs, seeds and binds in one top-level script.
Impact: No use case can be tested with a substitute repository or configuration; swapping the datastore means editing the class that also holds routes and rules.
Recommendation: A composition root that loads config, creates the DB, builds repositories, controllers and routes, and injects them — see RP-06.
Contract: safe

### [HIGH] Missing Boundary Validation   (AP-11)
File: src/AppManager.js:29-46
Description: Checkout only checks presence of `usr`, `eml`, `c_id`, `card` (35). A non-string `card` (a JSON number) reaches `cc.startsWith` (46) and throws inside a driver callback — observed: the original process exited with `TypeError: cc.startsWith is not a function` on one request. `c_id`, `eml` and the DELETE path id are never type- or format-checked and go to the datastore. The user is created (66-72) before the payment decision, so a denied payment still persists a new account (validation after a side effect). Escalated from MEDIUM to HIGH: the unvalidated values reach the datastore, and one malformed request terminates the service for every client.
Impact: Any client can take the service down with one request; invalid identities are persisted.
Recommendation: Validate types at the boundary and reject values invalid on their face with the existing 400 — see RP-11.
Contract: safe (rejects only values no legitimate client sends — a non-string card number; legitimate requests keep their behaviour)

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: src/app.js:5-14
Description: No error handler is registered and NODE_ENV is never set, so Express's default handler runs in development mode. Observed: a truncated JSON body to POST /api/checkout answers 400 with an HTML page containing the full stack trace, including absolute paths inside node_modules.
Impact: Every malformed request maps the server's internals (framework, versions by path, file layout) for an attacker.
Recommendation: Register the centralized error middleware (RP-09) that answers the same status with a safe body — see RP-17.
Contract: safe (the framework's default error page is replaced keeping its status; guidelines §6, error contract)

### [HIGH] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: `globalCache` is a module-level object exported and mutated on every successful checkout (`logAndCache`, called at src/AppManager.js:59), never read, never evicted; `totalRevenue` is an exported mutable `let`. The cache is also an unbounded in-memory accumulator (AP-13).
Impact: Memory grows with every checkout for the life of the process; state is shared invisibly between requests and is lost on restart or with more than one process.
Recommendation: Remove the write-only global cache and the mutable export; any real cache must be an injected, bounded component — see RP-07.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency — express transitive packages   (AP-19)
File: package.json:10-10
Description: `npm audit` (GitHub Advisory Database, 2026-10-01) reports through express 4.22.1: `path-to-regexp` 0.1.12 (<0.1.13, GHSA-37ch-88jc-xwx2, high — ReDoS via multiple route parameters), `qs` 6.14.2 (GHSA-q8mj-m7cp-5q26, GHSA-x5fp-wj9c-mxmx, GHSA-4mjr-xmp4-gh2g, moderate), `body-parser` 1.20.4 (<1.20.6, GHSA-v422-hmwv-36x6, low). De-escalated from HIGH to MEDIUM: the path-to-regexp advisory needs several parameters in one route, and the only parameterised route has one (`/api/users/:id`); qs parses every query string, so its moderate advisories are reachable; body-parser's needs an invalid `limit` option, which the app never sets.
Impact: Request parsing on every route runs a dependency with published, reachable moderate DoS advisories.
Recommendation: Update the lockfile within express 4.x (npm audit marks the fix non-breaking; `npm outdated` shows wanted 4.22.3) — see RP-18.
Contract: safe (within the same major version)

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-16
Description: `users.email` has no UNIQUE constraint although checkout looks users up by email and takes the first row (40); `enrollments.user_id/course_id` and `payments.enrollment_id` have no foreign keys; deleting a user has no rule for children — observed: after DELETE /api/users/1 the report lists the orphan as `"student":"Unknown"` with its payment still counted; `price` and `amount` are binary floating point (`REAL`). Escalation (charges attached to a deleted customer) and de-escalation (the store is in-memory and rebuilt at every start) both apply; kept at the MEDIUM default.
Impact: Revenue figures drift with float arithmetic and include payments of deleted users; a second account per email is possible from any other write path.
Recommendation: Declare UNIQUE(email) and foreign keys, store money as integer cents, and decide the delete rule — see RP-19.
Contract: safe for UNIQUE(email) and the money representation; contract-changing for the delete rule — cascading or refusing the delete changes what DELETE or the report returns, which is a product decision.

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-127
Description: The financial report reads all courses, then per course queries its enrollments (92), and per enrollment queries the user (104) and the payment (106): 1 + C + 2E round trips, coordinated with hand-written pending counters. The whole result is built in memory with no limit (AP-13, unbounded read).
Impact: Latency and DB load grow linearly with enrollments; the endpoint degrades as the business grows.
Recommendation: One set-based query joining courses, enrollments, users and payments, aggregated in a repository — see RP-10.
Contract: safe (same response shape)

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/AppManager.js:2-2
Description: `totalRevenue` is imported and never used; utils exports `totalRevenue` and `globalCache` that no module reads (src/utils.js:25); `config.dbUser`, `dbPass` and `smtpUser` are never read anywhere (src/utils.js:2-5) — dead configuration that carries a credential (AP-01).
Impact: Readers assume a database user, an SMTP sender and a revenue total exist and matter; none is used.
Recommendation: Delete the unused import, exports and configuration keys — see RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: Single-letter and abbreviated identifiers carry the whole checkout (`u`, `e`, `p`, `cid`, `cc`); `badCrypto` and `logAndCache` name the implementation, not the purpose; `this` and `self` are mixed for the same object (26, 50-57); the class name `AppManager` says nothing about the domain. The request field names (`usr`, `eml`, `pwd`, `c_id`, `card`) are contract and stay.
Impact: The checkout flow cannot be read without tracing each abbreviation.
Recommendation: Rename internal identifiers to domain names while keeping the request field names — see RP-16.
Contract: safe (internal identifiers only)

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-46
Description: The payment approval rule is the bare literal `"4"` card prefix; status strings `'PAID'`/`'DENIED'` are repeated free text (21, 46, 48, 108); the hashing loop uses unexplained `10000`, `2` and `10` (src/utils.js:19-22); the port `3000` is an environment literal in source (src/utils.js:6).
Impact: The approval rule and statuses are maintained by memory; a typo creates a new status silently.
Recommendation: Named constants for the statuses and the approval rule; port from configuration with the same default — see RP-15.
Contract: safe

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-named identifiers with literals; credential literals in seed/bootstrap data; URLs with inline credentials; high-entropy / prefixed literals; framework signing keys as literals; committed credential files (.env, keys); working-credential fallbacks | 1 finding: src/utils.js:1-7 (sites also at src/AppManager.js:18, 68) |
| AP-02 | input reaching driver calls by concatenation; interpolation markers in statements; ORM escape hatches; dynamic identifiers; shell execution; unsafe deserialization / template injection; path traversal | none — every statement uses `?` placeholders with a separate parameter array |
| AP-03 | ≥3 responsibility categories; size + mixed categories; units >50 lines / >3 nesting / many params / mixed return shapes; several domain concepts per file; low-cohesion class; leftover-bin utils module; high afferent coupling | 1 finding: src/AppManager.js:1-141 (utils.js also a leftover bin, addressed by AP-01/07/08/17 findings) |
| AP-04 | unprotected principal-scoped operations; IDOR lookups by input id; check only on one door; role/admin from request; unverified tokens; unreachable checks; disabled guards | 1 finding: src/AppManager.js:131-137 (+80-129) |
| AP-05 | domain decisions in handlers; persistence in handlers; long handlers; request objects deep in stack; rule duplicated across handlers; pass-through service layer | filed under AP-03 (precedence rule 1) |
| AP-06 | self-constructed collaborators; import-time side effects; no composition root; no seams for clock/random/fs/DB; concrete driver in domain; config read at point of use | 1 finding: src/AppManager.js:5-8 |
| AP-07 | module-level mutable variables; request data in globals; in-memory store of record; mutable defaults/exports; lifecycle-less caches; monkey-patching; in-process id counters | 1 finding: src/utils.js:9-15 |
| AP-08 | reversible password storage; fast digests; salt problems; non-constant-time comparison; sensitive values in logs; whole-record serialization; disabled TLS verification; token lifecycle | 2 findings: src/AppManager.js:45-45, src/utils.js:17-23 |
| AP-09 | empty/log-only catches; over-broad catches; repeated error mapping; no central handler (default handler observed); internals in responses; inconsistent error conventions; multi-write without transaction; exceptions for control flow | 1 finding: src/AppManager.js:50-63 (default handler leak filed as AP-18) |
| AP-10 | driver call in loop body / via helper; per-element FK fetch; lazy relation in iteration; repeated read with different args; remote call in loop; whole-table filtering in app code; per-element write loop | 1 finding: src/AppManager.js:83-127 |
| AP-11 | input used without type/format checks; optional input dereferenced; unbounded pagination; unsafe numeric parsing; validation on one door only; validation after side effect; domain invariants; body size bounds; scattered ad-hoc validation | 1 finding: src/AppManager.js:29-46 (body size bounded by express.json's default limit) |
| AP-12 | ≥10-line structural clones; rule in several places; repeated validation/error mapping; hand-written mappings; diverged copies; repeated constants; repeated guards | none — the repeated pending-counter blocks (95-99, 117-122) are under 10 lines; repeated status literals filed under AP-15 |
| AP-13 | paired acquire/release; leaked handles on failure; per-call connections / unbounded pools; outbound calls without timeout; retries; unbounded reads; unbounded accumulators; tasks without shutdown; unbounded recursion | folded into AP-10 (unbounded report read) and AP-07 (unbounded cache); no outbound calls exist |
| AP-14 | Layer 1: boot with `node --pending-deprecation --trace-deprecation --trace-warnings`, seed at boot (initDb), every non-destructive surface entry (10) in run-1, DELETE /api/users/1 in run-2; manifest/lockfile deprecation flags; superseded constructs. Layer 2: `npm view <pkg>@<ver> deprecated` for both direct deps, registry deprecation notices printed by `npm ci`, `npm outdated` | no runtime warning emitted; direct deps not deprecated; transitive deprecations reported once under AP-19 (sqlite3) |
| AP-15 | numeric literals in decisions; unit-less durations/sizes; string enums repeated; repeated literals; bare numeric codes; positional indexes; environment literals | 1 finding: src/AppManager.js:46-46 |
| AP-16 | names contradicting behaviour; non-descriptive identifiers; several names per concept; how-not-what names; mixed conventions; mixed human languages; misplaced files; stale comments; boolean params | 1 finding: src/AppManager.js:29-33 (Portuguese user-facing texts are contract and not filed) |
| AP-17 | commented-out code; unreachable branches; unreferenced units; unused imports / undeclared-unused deps; unused params/values; constant flags; unregistered endpoints; backup copies | 1 finding: src/AppManager.js:2-2 |
| AP-18 | literal debug mode; dev server as production; any-interface bind + debug; internals in error output (observed); permissive CORS; unrestricted diagnostic/admin surfaces; protective defaults off | 1 finding: src/app.js:5-14 (unrestricted admin route filed under AP-04) |
| AP-19 | npm audit (advisory DB) on the lockfile for direct and transitive deps; manifest range vs locked fixed versions; lockfile present | 2 findings: package.json:11-11, package.json:10-10 |
| AP-20 | identity column without UNIQUE; FK-like columns without FK; parent delete without child rule (observed orphan); money in REAL; nullable required columns / free-text enums | 1 finding: src/AppManager.js:12-16 |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Node runtime warnings (deprecation, pending) | node 24.21.0 | deprecation | A (none emitted) | `--pending-deprecation --trace-deprecation` run log | n/a — local | no issue found |
| express | 4.22.1 | deprecation | B | `npm view express@4.22.1 deprecated` | 2026-10-01 | no issue found |
| express (→ path-to-regexp 0.1.12, qs 6.14.2, body-parser 1.20.4) | 4.22.1 | advisory | B | npm audit (GitHub Advisory DB) | 2026-10-01 | AP-19 [MEDIUM] package.json:10-10 |
| sqlite3 | 5.1.7 | deprecation | B | `npm view sqlite3@5.1.7 deprecated` | 2026-10-01 | no issue found |
| sqlite3 (→ tar 6.2.1, node-gyp, cacache, make-fetch-happen, http-proxy-agent, @tootallnate/once, brace-expansion, ip-address) | 5.1.7 | advisory | B | npm audit (GitHub Advisory DB) | 2026-10-01 | AP-19 [HIGH] package.json:11-11 |
| sqlite3 transitive toolchain (prebuild-install, tar, glob, rimraf, inflight, npmlog, gauge, are-we-there-yet, @npmcli/move-file) | as locked | deprecation | B | registry deprecation notices printed by `npm ci` | 2026-10-01 | reported once under AP-19 [HIGH] |
| distance from current release | express 4.22.1 (wanted 4.22.3, latest 5.2.1); sqlite3 5.1.7 (latest 6.0.1) | outdated | B | `npm outdated` | 2026-10-01 | informs AP-19 recommendations |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-ecommerce-api-legacy-20261001-1550-1 | `docker run -d ... node:24 sleep infinity` on run-1; `npm ci`; `docker exec -d ... sh -c "node --pending-deprecation --trace-deprecation --trace-warnings src/app.js > /work/app.log 2>&1"` | ready on port 3000 (proc wait, 0 s); the app process exited on entry post-checkout-card-not-string (TypeError) |
| 2 | 2 | stop | container | refactor-arch-ecommerce-api-legacy-20261001-1550-1 | `docker rm -f` by exact name | removed |
| 3 | 2 | start | container | refactor-arch-ecommerce-api-legacy-20261001-1550-2 | `docker run -d ... node:24 sleep infinity` on run-2; `npm ci`; `docker exec -d ... node --pending-deprecation --trace-deprecation --trace-warnings src/app.js` | ready on port 3000 (proc wait, 2.1 s); destructive entry delete-user-1 exercised alone |
| 4 | 2 | stop | container | refactor-arch-ecommerce-api-legacy-20261001-1550-2 | `docker rm -f` by exact name | removed |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - AP-14 Layer 1 output for DELETE /api/users/:id: the second boot was detached with a plain argv, and `docker exec -d` output does not reach `docker logs` → whether that route emits a runtime deprecation warning is unobserved (the route was exercised; its response was captured).
  - OSV.dev was not queried separately: advisories come from `npm audit` (GitHub Advisory Database), an allowed ecosystem audit source; findings cite it.
Notes:
  - Scratch root: the environment's scratch directory (`C:\Users\lucas\AppData\Local\Temp\claude\D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill\d2004b79-894d-46db-979b-1fbb52811091\scratchpad\refactor-arch-ecommerce-api-legacy-20261001-1550\`); `node_modules/` excluded from every copy and installed with `npm ci` inside each container.
  - Protocol deviation (§1.4, "inside a container, pass an argv"): execution #1 booted through `sh -c "... > /work/app.log 2>&1"` to capture the warning stream into the scratch root. It contains no directory change and no chain; it is recorded here rather than hidden. Execution #3 used a plain argv.
  - The Phase 1 block names the host Node (24.12.0); every execution ran in the container's Node 24.21.0.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
> y   (answered by a human; recorded in the header as human-confirmed: y)

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
ecommerce-api-legacy/
├── .env.example                   every configuration key, placeholder values (RP-01)
├── README.md
├── api.http
├── package.json                   express ^4.22.3 (was ^4.18.2); sqlite3 ^5.1.6 unchanged
├── package-lock.json              regenerated with npm: express 4.22.3, body-parser 1.20.8, path-to-regexp 0.1.13, qs 6.16.0
├── reports/                       audit-20261001-1550.md, audit-latest.md, surface.json,
│                                  baseline.json, replay.json, compare.json, replay-2.json, compare-2.json
└── src/
    ├── app.js                     composition root and entry point (createApp, start)
    ├── errors.js                  error taxonomy, carrying the application's own status + text
    ├── config/
    │   └── index.js               the only environment reader (PORT, DATABASE_FILE), frozen
    ├── models/
    │   ├── database.js            promise wrapper over one sqlite3 connection, queued transactions
    │   ├── schema.js              DDL (UNIQUE email, integer cents, CHECK on status) and seed
    │   ├── repositories.js        Course/User/Enrollment/Payment/AuditLog/FinancialReport repositories
    │   ├── payment.js             payment statuses and the approval rule
    │   ├── password.js            salted scrypt storage, generated passwords
    │   └── money.js               cents conversion
    ├── controllers/
    │   ├── checkoutController.js  checkout use case: decide payment first, then one transaction
    │   ├── reportController.js    financial report use case
    │   └── userController.js      user deletion use case
    ├── routes/                    the View layer: parse → call one controller → render
    │   ├── checkoutRoutes.js      POST /api/checkout, boundary validation
    │   ├── reportRoutes.js        GET /api/admin/financial-report, response shape
    │   └── userRoutes.js          DELETE /api/users/:id, id validation
    └── middlewares/
        └── errorHandler.js        single error boundary, no stack traces in responses
```
Layout: MVC with the repositories kept inside the model layer (guidelines §2); `routes/` is the View layer. Removed: `src/AppManager.js`, `src/utils.js` (in-place rewrite; git history is the backup).

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 9 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 1 UNVERIFIED
    Security entries: 2 FIXED, 0 NOT FIXED
  ○ Findings resolved: 12/17  (3 proposed, 2 unresolved)
  ○ Anti-patterns remaining: 3 proposed-not-applied, 3 unresolved  (re-audit: 6 findings)
    Re-audit passes: 2; fixed after re-audit: 1 (0 of them missed-in-phase-2)
  ✓ Processes: 10 started, 10 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

### Findings, by bucket
Resolved (12): AP-03 God Class · AP-08 card number and key logged · AP-09 swallowed/uncentralized errors · AP-01 hardcoded secrets · AP-08 reversible password hash · AP-06 no composition root · AP-18 default error page leaking the stack · AP-07 mutable global cache · AP-19 express transitive advisories (npm audit no longer reports the express chain) · AP-17 dead code · AP-16 names · AP-15 magic values.
Proposed (3): AP-04 authorization · AP-19 sqlite3 toolchain · AP-20 foreign keys and the delete rule (UNIQUE(email), integer cents and the status CHECK were applied; what remains is the part the gate held).
Unresolved (2):
  - AP-11 [HIGH], origin `failed`: fixed the non-string card that crashed the process (security entry FIXED), the type checks on every field, the user-before-payment ordering, and (after re-audit 1) the non-numeric DELETE id (security entry FIXED). Still open: `eml` has no format check. A format rule could reject addresses clients send today, so it is a product decision, now listed under Proposed.
  - AP-10 [MEDIUM], origin `failed`: the N+1 is gone (one JOIN query, src/models/repositories.js:78-110). The unbounded read that the Phase 2 description folded in (AP-13) remains, because pagination changes the response contract. It is now listed under Proposed.

### Re-audit
Pass 1 (7 findings): AP-04, AP-19 sqlite3 and AP-20 (match recorded proposals); AP-11 email format and AP-13 unbounded report (`failed`); AP-09 course-lookup failure answered as 404 (`missed-in-phase-2`); AP-17 unused `Database.close()` (`introduced`).
Fixed between passes: the unused `Database.close()` (AP-17, introduced); the non-numeric DELETE id (part of AP-11: the finding stays unresolved because of the email format).
Pass 2 (6 findings):
  - proposed-not-applied (3): AP-04, AP-19 sqlite3, AP-20.
  - unresolved (3):
    - [HIGH] Missing Boundary Validation (AP-11), `failed`. File: src/routes/checkoutRoutes.js:11-24. `eml` is accepted with no format check.
    - [MEDIUM] Unbounded Resources (AP-13, the unbounded part of Phase 2 AP-10), `failed`. File: src/models/repositories.js:78-110. The report loads every course, enrollment and payment, with no limit.
    - [MEDIUM] Swallowed or Uncentralized Error Handling (AP-09), `missed-in-phase-2`. File: src/controllers/checkoutController.js:25-34. A datastore failure during the course lookup is logged and then answered as `404 Curso não encontrado`, which is indistinguishable from a missing course. The original did the same (`if (err || !course)`); Phase 2 did not report it. De-escalated from HIGH to MEDIUM: the swallow is now deliberate, narrow, logged and commented.
Both passes swept all 20 catalog entries. AP-14 Layer 1 ran on the refactored app with `--pending-deprecation --trace-deprecation --redirect-warnings` over boot, every surface entry and the destructive one, and no warnings file was produced. Layer 2: `npm audit` on the refactored lockfile (2026-10-01) reports only the sqlite3 chain.

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: src/routes/userRoutes.js:15-23
Reason not applied: the application has no identity model, so every client is anonymous today. Authentication on DELETE /api/users/:id and on GET /api/admin/financial-report (src/routes/reportRoutes.js:20-27) would answer 401/403 to every current client.
Proposed change: introduce an identity model (who the principals are, how they authenticate) and an admin policy enforced in the controllers (RP-04). This needs a product decision and coordination with every client.

### [HIGH] Known-Vulnerable Dependency — sqlite3 install toolchain   (AP-19)
File: package.json:11-11
Reason not applied: the only fix is sqlite3 6.0.1, a major version. It was applied and replayed. The refactored app then failed to boot in the run's runtime image (node:24, Debian bookworm) with `Error: /lib/x86_64-linux-gnu/libm.so.6: version 'GLIBC_2.38' not found (required by .../node_sqlite3.node)`. So the upgrade changes which platforms the application can be deployed on, and it was reverted (RP-18 step 4). Also found in Phase 3: the upstream release notes of v6.0.0 say "Mark repository as unmaintained" (github.com/TryGhost/node-sqlite3/releases, Tier C, looked up 2026-10-01). No successor is named upstream. Phase 2 missed this fact; it is reported here once, with the advisories.
Proposed change: either move the deployment base to glibc ≥ 2.38 and upgrade to sqlite3 6.0.1 (verify with this replay), or evaluate a maintained SQLite binding. Replacing the package adds a new runtime dependency, which is a team decision.

### [MEDIUM] Missing Schema-Level Integrity Constraints — foreign keys and delete rule   (AP-20)
File: src/models/schema.js:24-34
Reason not applied: with enforced foreign keys, deleting a user who has enrollments must cascade, refuse or detach. Each choice changes what DELETE /api/users/:id or the financial report returns today; the report currently still lists the orphan as "Unknown" with its payment counted.
Proposed change: declare the `user_id`, `course_id` and `enrollment_id` foreign keys, enable `PRAGMA foreign_keys`, and choose the delete rule. Retaining payment records for accounting likely favours refusing the delete or anonymizing the user. The response text "matrículas e pagamentos ficaram sujos" should then change too.

### [HIGH] Missing Boundary Validation — email format   (AP-11, unresolved: failed)
File: src/routes/checkoutRoutes.js:11-24
Reason not applied: an email format rule may reject addresses that clients send today, so it is a product decision.
Proposed change: agree on a format rule, then enforce it in `parseCheckout`, answering the existing `400 Bad Request`.

### [MEDIUM] Unbounded Resources — financial report   (AP-13, unresolved: failed)
File: src/models/repositories.js:78-110
Reason not applied: paginating or limiting the report changes the response contract; the report would no longer contain every course.
Proposed change: add an optional limit/cursor with the current behaviour as the default, or aggregate revenue in SQL and paginate the student lists (RP-13).

### [MEDIUM] Swallowed or Uncentralized Error Handling — course lookup   (AP-09, unresolved: missed-in-phase-2)
File: src/controllers/checkoutController.js:25-34
Reason not applied: the application itself answers `404 Curso não encontrado` when the course lookup fails. That is an intentional error of the application, and changing it to 500 changes the error contract.
Proposed change: answer a datastore failure with 500 and keep the 404 for a missing course.

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Surface entry `post-checkout-malformed-json` is UNVERIFIED in the replay. It was skipped in the inventory because its body is the framework's default error page with a stack trace, which the AP-18 fix replaces on purpose. It was verified out of band instead: the original answered 400 text/html with the stack trace (Phase 2 capture); the refactored app answered `400 text/html; charset=utf-8` with body `Bad Request`, on both replay instances (one-off `fetch` from inside the container).
  - Phase 2 only: the AP-14 Layer 1 output of DELETE /api/users/:id was not observed on the original (see the Phase 2 block above). On the refactored app it was observed, with no warning.
  - AP-20 UNIQUE(email) has no security entry: no request can create a duplicate through the API (checkout looks the email up first). The constraint was verified by reading the DDL (src/models/schema.js:15).
Notes:
  - Behaviour changes that the replay classes as PASS or FIXED and that are named here: a card number that is not a string, a non-numeric DELETE id, and object-typed fields are now answered `400 Bad Request` (before: a process crash or a 200). A declined payment no longer creates the user account. A checkout with no `pwd` now stores a random password instead of the shared `123456`. The seeded account no longer has the literal password `123`. A request with no JSON body now gets 400 instead of the framework's 500 page. Two concurrent first checkouts with the same new email now fail the second with `500 Erro ao criar usuário` (UNIQUE) instead of creating a duplicate user.
  - Owner action required: the database password and the `pk_live_` gateway key that were in src/utils.js stay in git history. Rotate them; deleting them from the code does not revoke them.
  - The lockfile was regenerated with the container's npm (11.19.0): the host npm (11.6.2) produced a lockfile that `npm ci` rejected as out of sync. The result was copied back into the target with a literal Copy-Item. The pre-existing `node_modules/` inside the target was never touched; it predates this run and is now stale against the lockfile, so reinstall it with `npm ci`.
  - Every execution ran in its own container from a fresh copy: run-3/4/5 for the original, refactored-1…5 for the refactored app. Dependencies were installed with `npm ci` inside each container; `node_modules/` and `reports/` were excluded from the copies. Nothing executed inside the target.
  - Scratch root: the environment's scratch directory. The snapshot directory `refactor-arch-ecommerce-api-legacy-20261001-1550` was deleted after re-audit pass 2. Before that, a listing of containers labelled `refactor-arch.run=20261001-1550` was empty.
  - Replay comparisons use the text skeleton of protocol §5.1 for text bodies: lines masked for timestamps, UUIDs, hex runs and digit runs, then compared as a sorted set. Contract headers (§5.3) were compared; none were present.
  - Validation ran on the shipped probe.mjs and proc.mjs (container `wait` and copies).

## Execution Log — Phase 3
| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 5 | 3a | start | container | refactor-arch-ecommerce-api-legacy-20261001-1550-3 | original, run-3: `npm ci`; `exec -d node src/app.js` | ready on 3000 (1.3 s); baseline captured; app process exited on the security entry (pre-existing crash) |
| 6 | 3a | stop | container | …-3 | `docker rm -f` by exact name | removed |
| 7 | 3a | start | container | …-4 | original, run-4 | ready (2.4 s); destructive `delete-user-1` captured alone |
| 8 | 3a | stop | container | …-4 | `docker rm -f` by exact name | removed |
| 9 | 3c | start | container | …-5 | refactored-1 (sqlite3 6.0.1): `exec -d node --pending-deprecation --trace-deprecation src/app.js`; then `exec timeout 8 node src/app.js` to read the error | not ready (wait exit 4); boot error GLIBC_2.38 not found → sqlite3 upgrade reverted |
| 10 | 3c | stop | container | …-5 | `docker rm -f` by exact name | removed |
| 11 | 3c | start | container | …-6 | refactored-2: `exec timeout 5 node --pending-deprecation --trace-deprecation src/app.js` (listening line, no warnings, exit 124 by its own timeout); `exec -d node src/app.js` | ready (2.3 s); replay 1 captured |
| 12 | 3c | stop | container | …-6 | `docker rm -f` by exact name | removed |
| 13 | 3c | start | container | …-7 | refactored-3 | ready; destructive `delete-user-1` replayed alone |
| 14 | 3c | stop | container | …-7 | `docker rm -f` by exact name | removed |
| 15 | 3d | start | container | …-8 | original, run-5 (late entry, protocol §4.3) | ready (2.4 s); `delete-user-non-numeric-id` captured against the original |
| 16 | 3d | stop | container | …-8 | `docker rm -f` by exact name | removed |
| 17 | 3d | start | container | …-9 | refactored-4: `exec -d node --pending-deprecation --trace-deprecation --redirect-warnings=/app/warnings.log src/app.js` | ready (2.6 s); replay 2 captured; no warnings file |
| 18 | 3d | stop | container | …-9 | `docker rm -f` by exact name | removed |
| 19 | 3d | start | container | …-10 | refactored-5, same detectors | ready; destructive entry replayed alone; no warnings file |
| 20 | 3d | stop | container | …-10 | `docker rm -f` by exact name | removed |
================================
