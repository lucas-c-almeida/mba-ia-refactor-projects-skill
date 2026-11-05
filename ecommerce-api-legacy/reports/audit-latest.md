## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        .worktrees/r7-p2/ecommerce-api-legacy
Language:      JavaScript (Node.js; no `engines` field — runtime version undetermined from the project, host has v24.12.0)
Framework:     Express 4.22.1 (resolved in package-lock.json; manifest range ^4.18.2)
Dependencies:  express (^4.18.2 → 4.22.1), sqlite3 (^5.1.6 → 5.1.7)
Domain:        LMS course sales — users, courses, enrollments, payments via a checkout flow, plus an admin financial report
App type:      HTTP service
Architecture:  None — one class holds schema/seed, persistence, business rules and route registration; a utils module holds config, secrets, a global cache and hashing
Source files:  3 files analyzed (src/**/*.js; excluded node_modules, .claude/, reports/, .gitignore matches; api.http/README/manifests not counted)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite in-memory, DDL + seed at boot)
Boot:          node src/app.js  (npm start → "node src/app.js"), cwd = run copy
Port:          3000, fixed in source (src/utils.js config.port); no override read
Runtime env:   Node from official image; dependencies from package-lock.json via `npm ci` inside the container
Isolation:     container (docker 28.5.2, image node:24.12.0)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1 + sqlite3 5.1.7
Files:   3 analyzed | ~180 lines of code
Date:    2026-11-05 01:30 (UTC)
Mode:    full
Confirmation: human-confirmed: y
Tree:    clean at b90300c
Runtime: installed the declared dependencies from package-lock.json (`npm ci`) inside each run container, in the run copy outside the target
Isolation: container (docker 28.5.2, image node:24.12.0)
Scratch: environment scratch directory — C:\Users\lucas\AppData\Local\Temp\claude\b247d7bb4f414394\805dbf78-3ef5-40ce-9aab-ca850a1feaef\scratchpad\refactor-arch-ecommerce-api-legacy-202611050130-5d509d26  (protocol §1.1)

## Summary
CRITICAL: 8 | HIGH: 5 | MEDIUM: 1 | LOW: 5

## Findings

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:1-141
Description: One class holds the database connection (5-8), the schema DDL and seed data (10-23), route registration and request parsing (25-35, 80, 131), the payment approval rule and checkout workflow (43-75), the financial-report aggregation (80-129) and user deletion (131-137) — persistence, business rules, delivery and presentation for three unrelated concerns (sales, finance reporting, account administration). It also carries the card/key logging of AP-08 (45). AP-05 (rules and persistence in handlers) is folded in here by the catalog's precedence rule.
Impact: Nothing can be tested without an Express app and a live SQLite connection; every change to checkout, reporting or user administration touches the same 140-line class and the same deeply nested callbacks.
Recommendation: Split into models (repositories per table group), controllers (checkout, report, users), routes, config and an error middleware, with a composition root in the entry point — see RP-03, RP-05.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — checkout attaches purchases to any existing account   (AP-04)
File: src/AppManager.js:40-75
Description: The checkout looks up the account by the e-mail in the body (40) and, when it exists, enrolls and charges under that account (73-75) without checking the submitted `pwd` against the stored one; the password is only used when a new account is created (66-72). This is a business operation in an application with no identity model (no operation verifies a presented credential).
Impact: Anyone who knows a customer's e-mail can create enrollments and payment records under that customer's account; nothing distinguishes it from the customer's own purchase.
Recommendation: Introduce an identity model (verify the password, or a session/token, before using an existing account) — see RP-04. Requires a product decision on who may buy for whom.
Contract: contract-changing: a client that today checks out with an existing e-mail and any (or no) password would start receiving a rejection.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — card number and gateway key logged   (AP-08)
File: src/AppManager.js:45-45
Description: Every checkout writes the full card number from the request and the payment gateway key from configuration to the process log (`console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`). Escalated to CRITICAL: payment-card data and a live credential reach the log.
Impact: Anyone with log access (log shipping, container logs, support staff) obtains full card numbers and the gateway's live key.
Recommendation: Remove the card number and the key from the log line; log a non-sensitive reference at most (last four digits) — see RP-08.
Contract: safe

### [CRITICAL] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:50-63
Description: The checkout performs three dependent writes (enrollment 50, payment 54, audit log 57) with no transaction: a failure of the second leaves an enrollment with no payment. The audit-log insert's error is ignored and success returned (57-60). Elsewhere errors are dropped: the report ignores `err` on lines 92, 104 and 106 (an error on 92 dereferences `enrollments.length` of undefined), and the delete ignores `err` and reports success (133-135). There is no error middleware; an exception thrown inside a driver callback is uncaught and terminates the process — observed in the deprecation run: a checkout with a numeric `card` produced a transport error and the process exited. Escalated to CRITICAL: a failed persisted write is reported as success.
Impact: The service reports success while writes were lost or half-applied, and one malformed request takes the whole API down for every client.
Recommendation: Promise-wrap the driver, run checkout writes in one transaction, let errors propagate to one Express error middleware that maps them to the existing status/body — see RP-09.
Contract: safe (intentional status codes and bodies preserved; only failure paths that today crash or lie change)

### [CRITICAL] Missing or Bypassable Authorization — open financial report   (AP-04)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` returns revenue per course and every student's name and amount paid, with no credential of any kind. It is a privileged operation (management aggregate with financial figures and per-principal rollups, under an `admin` path).
Impact: Any anonymous caller reads the company's revenue and the list of paying customers with their amounts.
Recommendation: Guard the route with an operator credential read from configuration, compared in constant time, failing closed when unset — see RP-04.
Contract: safe (privileged operation: only non-operators are rejected)

### [CRITICAL] Missing or Bypassable Authorization — anonymous account deletion   (AP-04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` deletes the account (the table holding credentials) whose id is in the path, with no credential, in an application with no identity model — a privileged operation.
Impact: Any caller can delete any customer account by iterating ids.
Recommendation: Guard the route with an operator credential from configuration, failing closed — see RP-04.
Contract: safe (privileged operation: only non-operators are rejected)

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: The configuration object holds literal credentials: `dbPass: "senha_super_secreta_prod_123"`, `dbUser: "admin_master"`, and `paymentGatewayKey: "pk_live_1234567890abcdef"` (a live-key prefix). The seed also creates a runtime account with the known password `'123'` (src/AppManager.js:18-18).
Impact: Everyone with repository access holds the gateway key and database credentials; rotating them requires a code change, and history keeps them forever.
Recommendation: Read secrets from the environment through one config module, with empty defaults and fail-closed behaviour; rotate the committed values — see RP-01.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password "hash"   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` base64-encodes the password, keeps its first two characters and repeats them; the stored value is 10 characters derived from roughly the first byte and a half of the password — a reversible, collision-heavy encoding, not a hash. The seed stores `'123'` in clear (src/AppManager.js:18), and an absent `pwd` silently becomes the password `"123456"` (src/AppManager.js:68). Escalated to CRITICAL: passwords are stored recoverably.
Impact: A database read reveals the start of every password, and any password sharing its first character matches the stored value; accounts created without a password share a well-known one.
Recommendation: Use a purpose-built KDF available in the runtime (scrypt from the built-in crypto module) with a per-user salt; store an unusable value when no password is given — see RP-08.
Contract: safe (no response returns the stored value; no login operation exists)

### [HIGH] Known-Vulnerable Dependency — express transitive advisories   (AP-19)
File: package.json:9-12
Description: `npm audit` (GitHub Advisory Database, 2026-11-05) reports, for packages pulled by express@4.22.1: body-parser 1.20.4 (GHSA-27r3-jxmh-p828 high, GHSA-v422-hmwv-36x6 low), proxy-addr 2.0.7 (GHSA-jqcg-44mw-7w3h critical), path-to-regexp 0.1.12 (GHSA-37ch-88jc-xwx2 high), qs 6.14.2 (four moderate advisories). Reachability: proxy-addr matters only with `trust proxy` configured (not set) and path-to-regexp's ReDoS needs multiple route parameters (only `/:id` exists); body-parser's JSON parser is registered globally (src/app.js:6) but reachability of the compressed-body path was not established — kept at HIGH.
Impact: Published, scannable denial-of-service paths in the request parser every request goes through.
Recommendation: Update the lockfile within the express 4 line (`npm audit fix`, no `--force`; npm reports express 4.22.3 as wanted) — see RP-18.
Contract: safe (within the same major version)

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:4-8
Description: The class opens its own `sqlite3.Database(':memory:')` in its constructor and pulls the configuration singleton and helpers from `./utils` (line 2); the entry point (src/app.js:8-10) only calls `initDb()`/`setupRoutes()`, so no place assembles the object graph and nothing can be substituted.
Impact: No unit can be exercised without a real database and an Express app; tests would be integration tests or nothing.
Recommendation: Create the DB connection and config in the composition root and inject them into repositories and controllers — see RP-06.
Contract: safe

### [HIGH] Missing Boundary Validation   (AP-11)
File: src/AppManager.js:29-35
Description: Checkout checks only presence of `usr`, `eml`, `c_id`, `card`; no type or format check. `card` is used with `cc.startsWith` (46) — a numeric `card` threw a TypeError that killed the process (observed, deprecation run, entry checkout-card-number-type: transport error, process gone). `c_id` and `eml` reach the driver unchecked; the delete's `:id` (132) is unchecked. Escalated to HIGH: unvalidated values reach the datastore and one malformed request is a denial of service for the whole API.
Impact: Malformed input becomes a crash instead of a 400, and an anonymous caller can stop the service with one request.
Recommendation: Validate type and range of every input at the boundary and answer 400 — see RP-11.
Contract: safe (only values no legitimate client sends are newly rejected)

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: src/app.js:5-14
Description: No error handler is registered and `NODE_ENV` is never set, so Express's default handler answers errors with a full stack trace and internal paths — observed: a malformed JSON body on `/api/checkout` returned status 400 with an HTML page containing `SyntaxError ... at parse (/app/node_modules/body-parser/lib/types/json.js:92:19)` and further frames.
Impact: Every malformed request maps the server's internals (dependency versions, paths) for the next attack.
Recommendation: Register a centralized error middleware that keeps the status and returns a safe body — see RP-17, RP-09.
Contract: safe (framework default error page replaced, status kept)

### [HIGH] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: `globalCache` is a module-level object that `logAndCache` mutates on every successful checkout (key per user, src/AppManager.js:59) and that is exported for others to mutate; it is never read, never bounded, never evicted (also AP-13). `totalRevenue` is an exported mutable module variable.
Impact: Memory grows with every customer for the process's lifetime, and any importer can change shared state; behaviour depends on history and cannot scale beyond one process.
Recommendation: Remove the write-only cache and the unused global; if caching is needed, inject a bounded cache — see RP-07.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-128
Description: The financial report reads all courses (83), then per course queries enrollments (92), and per enrollment queries the user (104) and the payment (106) — 1 + C + 2E round trips, with whole tables loaded and summed in application code.
Impact: Report latency grows linearly with enrollments; the hand-counted completion callbacks are also fragile.
Recommendation: One set-based query joining courses, enrollments, users and payments, aggregated per course in the model — see RP-10.
Contract: safe

### [LOW] Known-Vulnerable Dependency — sqlite3 install-time chain   (AP-19)
File: package.json:11-11
Description: `npm audit` (2026-11-05) reports tar 6.2.1 (several critical/high advisories, e.g. GHSA-23hp-3jrh-7fpw, GHSA-34x7-hfp2-rc4v), brace-expansion 1.1.12, ip-address 10.1.0 and @tootallnate/once, all pulled by sqlite3@5.1.7 through node-gyp, which runs only at install/build time. `npm ci` also printed registry deprecation notices (Tier B, 2026-11-05) for tar@6.2.1, glob@7.2.3, rimraf@3.0.2, inflight@1.0.6, npmlog@6.0.2, prebuild-install@7.1.3 and others in the same chain (AP-14 reported here, once). De-escalated to LOW: install/build-time only, never loaded at run time.
Impact: A build that compiles sqlite3 from source runs vulnerable, unmaintained tooling.
Recommendation: npm names sqlite3@6.0.1 as the fix (`npm audit fix --force`, major upgrade) — see RP-18; apply only if the replay covers the persistence behaviour, otherwise propose.
Contract: safe only if the replay covers the major upgrade (§6, dependency upgrades); otherwise proposed

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/AppManager.js:2-2
Description: `totalRevenue` and `config.dbUser/dbPass/smtpUser` are declared (src/utils.js:2-5, 10) and `totalRevenue` imported here but never read; `globalCache` is written and never read (src/utils.js:9-15, see AP-07).
Impact: Readers assume these values matter (a DB login that does not exist for an in-memory database, a revenue counter that is never updated).
Recommendation: Delete the unused members and import — see RP-16.
Contract: safe

### [LOW] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-16
Description: `users.email` is used as the account identity (lookup at 40 takes the first row) with no UNIQUE constraint; `enrollments.user_id/course_id` and `payments.enrollment_id` have no FOREIGN KEY, and deleting a user leaves orphan enrollments and payments (the response at 135 says so); prices and amounts are `REAL`. De-escalated to LOW: the database is `:memory:`, rebuilt at every start, so no corrupt state outlives the process.
Impact: Within a process lifetime, duplicate e-mails can attach to different rows and the report shows "Unknown" students for deleted accounts.
Recommendation: Declare UNIQUE on email and the foreign keys (with `PRAGMA foreign_keys = ON`) — see RP-19; changing what a delete does to children is a behaviour change to propose.
Contract: safe for UNIQUE/FK declarations; contract-changing for cascading deletes (the report's content for deleted users would change)

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: Single-letter locals `u`, `e`, `p`, `cid`, `cc` for the request fields; `badCrypto` names how it is bad rather than what it does; `AppManager` and `utils` are leftover-bin names; identifiers in English with messages and logs in Portuguese.
Impact: The checkout's 50-line nested callback is hard to follow when its variables carry no meaning.
Recommendation: Rename internal identifiers (request field names are contract and stay) — see RP-16.
Contract: safe

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-46
Description: The payment decision is `cc.startsWith("4")`, an unexplained rule; the status strings `'PAID'`/`'DENIED'` are repeated literals (21, 46, 48, 108); `badCrypto` uses 10000, 2 and 10 unexplained (src/utils.js:19-22).
Impact: Nobody can tell whether the approval rule is a stub or a business decision, or change a status string safely.
Recommendation: Named constants for the approval rule and payment statuses — see RP-15.
Contract: safe

## Signal Ledger

| Entry | Signal | Examined | Occurrences | Outcome |
|---|---|---|---|---|
| AP-01 | Literal assigned to secret-named identifier | all source files | 2: src/utils.js:3, 4 | finding: Hardcoded Secrets (AP-01) |
| AP-01 | Credential literals in seed/runtime data | src/AppManager.js:18-21 | 1: AppManager.js:18 (`pass '123'`) | finding: AP-01 (named in description), AP-08 |
| AP-01 | Connection URL with inline credentials | all source files | 0 | none |
| AP-01 | High-entropy / credential-prefixed literal | all source files | 1: utils.js:4 (`pk_live_`) | finding: AP-01 |
| AP-01 | Framework signing/session key literal | all source files | 0 | none |
| AP-01 | Credential-bearing file committed | target tree | 0 | none |
| AP-01 | Real secret as default fallback | all source files | 1: AppManager.js:68 (`"123456"`) | finding: AP-08 (password) |
| AP-02 | Input reaching driver by concatenation | all driver calls in AppManager.js | 0 (all 12 statements use `?` with a parameter array) | none |
| AP-02 | Interpolation markers inside statements | AppManager.js | 0 (template literal at 57 is a bound value, not SQL) | none |
| AP-02 | ORM escape hatch with input | all source files | 0 | none |
| AP-02 | Dynamic identifiers from input | all source files | 0 | none |
| AP-02 | Shell/process execution with input | all source files | 0 | none |
| AP-02 | Unsafe deserialization / template injection | all source files | 0 | none |
| AP-02 | Path traversal | all source files | 0 | none |
| AP-03 | ≥3 responsibility categories in one module | all source files | 2: AppManager.js (persistence, rules, delivery, presentation); utils.js (config, state, crypto, logging) | finding: AP-03 (AppManager.js); utils.js discarded as a separate God Module: 25 lines, covered by AP-01/AP-07/AP-08/AP-17 |
| AP-03 | >300-400 lines with ≥2 categories | all source files | 0 (largest 141 lines) | none |
| AP-03 | Unit >50 lines / nesting >3 / >5 params | AppManager.js | 2: setupRoutes 25-138; checkout handler 28-78 nested 6 deep | finding: AP-03 |
| AP-03 | Several unrelated domain concepts in one file | AppManager.js | 1 | finding: AP-03 |
| AP-03 | Low-cohesion class | AppManager.js | 1 | finding: AP-03 |
| AP-03 | Grab-bag utils/manager module | utils.js, AppManager.js | 2 | finding: AP-03 (AppManager); utils.js named in AP-07/AP-17 |
| AP-03 | Very high afferent coupling | all source files | 0 (3 files) | none |
| AP-04 | Principal-scoped resource without auth/ownership | all routes | 1: checkout using existing account 40-75 | finding: AP-04 checkout |
| AP-04 | IDOR: lookup by input id only | all routes | 1: DELETE /api/users/:id 131-137 | finding: AP-04 delete |
| AP-04 | Authorization only on one door | all routes | 0 (no authorization anywhere) | none |
| AP-04 | Role/admin flag from request | all routes | 0 | none |
| AP-04 | Token decoded not verified | all source files | 0 | none |
| AP-04 | Check written but unreachable | all source files | 0 | none |
| AP-04 | Commented-out/flag-disabled guard | all source files | 0 | none |
| AP-04 | Privileged operation with no guard | all routes | 2: financial report 80-129; account delete 131-137 | findings: AP-04 report, AP-04 delete |
| AP-05 | Domain decisions in handler | AppManager.js | 2: payment approval 46; revenue aggregation 108-110 | folded into AP-03 (precedence rule) |
| AP-05 | Persistence calls inside handler | AppManager.js | 9 driver calls in handlers | folded into AP-03 |
| AP-05 | Handler >30 lines not mapping | AppManager.js | 2: 28-78, 80-129 | folded into AP-03 |
| AP-05 | Request/response objects deep in stack | AppManager.js | 1: `res` used inside nested closures 43-63 | folded into AP-03 |
| AP-05 | Same rule in two handlers | all source files | 0 | none |
| AP-05 | Pass-through service layer | all source files | 0 (no service layer) | none |
| AP-06 | Unit constructs its own collaborators | AppManager.js | 1: constructor 5-8 | finding: AP-06 |
| AP-06 | Import-time side effects | all source files | 1: app.js 5-14 (builds and listens at load) | finding: AP-06 (composition root missing; named in AP-18 file range) |
| AP-06 | No single composition root | all source files | 1 | finding: AP-06 |
| AP-06 | No seam for clock/random/fs in rules | AppManager.js | 1: `datetime('now')` in SQL 57 | discarded: clock read inside SQL for an audit timestamp, no rule depends on it |
| AP-06 | Concrete driver referenced by domain | AppManager.js:1 | 1 | finding: AP-06 |
| AP-06 | Configuration read at point of use | AppManager.js:45 | 1 | finding: AP-06 / AP-08 (card log) |
| AP-07 | Module-level variable mutated after init | utils.js | 1: globalCache 9, 14 | finding: AP-07 |
| AP-07 | Request-scoped data stored globally | all source files | 0 | none |
| AP-07 | In-memory collection as store of record | utils.js | 1: globalCache | finding: AP-07 |
| AP-07 | Mutable default / exported mutable object | utils.js:25 | 2: globalCache, totalRevenue | finding: AP-07 |
| AP-07 | Cache/pool with no lifecycle | utils.js | 1 | finding: AP-07 |
| AP-07 | Monkey-patched built-in | all source files | 0 | none |
| AP-07 | In-process id counter | all source files | 0 | none |
| AP-08 | Password stored reversibly/encoded | utils.js:17-23; AppManager.js:18 | 2 | finding: AP-08 (password) |
| AP-08 | Fast digest for passwords | all source files | 0 (worse: no digest) | covered by AP-08 (password) |
| AP-08 | Shared/constant/missing salt | utils.js | 1 (no salt) | finding: AP-08 (password) |
| AP-08 | Non-constant-time credential comparison | all source files | 0 (no comparison exists) | none |
| AP-08 | Sensitive values in logs | AppManager.js:45, utils.js:13 | 1: AppManager.js:45 | finding: AP-08 (card log); utils.js:13 discarded: logs a key name only |
| AP-08 | Whole record serialized to client | all responses | 0 (report selects name/amount; checkout returns id) | none |
| AP-08 | Transport without protection / cert check off | all source files | 0 | none |
| AP-08 | No token expiry/rotation | all source files | 0 (no tokens) | none |
| AP-09 | Empty / log-and-continue / success on failure | AppManager.js | 3: 57-60, 133-135, 104/106 | finding: AP-09 |
| AP-09 | Over-broad catch | all source files | 0 | none |
| AP-09 | Same error mapping repeated per handler | AppManager.js | 6: `res.status(500).send("Erro …")` 41, 51, 55, 70, 84 | finding: AP-09 |
| AP-09 | No centralized handler (observed) | app.js; runtime | 1: default handler + process crash observed | finding: AP-09, AP-18 |
| AP-09 | Internal detail in response body | runtime | 1: stack trace observed | finding: AP-18 |
| AP-09 | Inconsistent error convention | AppManager.js | 1: text bodies vs JSON success | discarded: text error bodies are intentional contract; recorded in AP-09 recommendation (preserve) |
| AP-09 | Multi-write without transaction | AppManager.js:50-61 | 1 | finding: AP-09 |
| AP-09 | Exceptions for control flow | all source files | 0 | none |
| AP-10 | Driver call inside loop / loop callback | AppManager.js:89-127 | 3: 92, 104, 106 | finding: AP-10 |
| AP-10 | Per-element FK fetch | AppManager.js | 2: 104, 106 | finding: AP-10 |
| AP-10 | Lazy relation in iteration | all source files | 0 (no ORM) | none |
| AP-10 | Repeated read where a set query works | AppManager.js | 1 | finding: AP-10 |
| AP-10 | Remote call in loop | all source files | 0 | none |
| AP-10 | Whole table read and aggregated in code | AppManager.js:83, 108-110 | 1 | finding: AP-10 |
| AP-10 | Per-element write loop | all source files | 0 | none |
| AP-11 | Input used with no type/range/format check | all routes | 3: card 46, c_id 37, :id 132 | finding: AP-11 |
| AP-11 | Optional input dereferenced without check | AppManager.js | 1: `cc.startsWith` with non-string (observed crash) | finding: AP-11 |
| AP-11 | Unconstrained pagination/limit | all routes | 0 | none |
| AP-11 | Numeric parsing without failure path | all routes | 0 | none |
| AP-11 | Validation on one door not another | all routes | 0 | none |
| AP-11 | Validation after use/side effect | all routes | 0 | none |
| AP-11 | Domain invariants enforced nowhere | AppManager.js | 1: e-mail format/uniqueness | finding: AP-11, AP-20 |
| AP-11 | No upper bound on body/array | app.js:6 | 0 (express.json default limit applies) | none |
| AP-11 | Ad-hoc scattered validation | AppManager.js:35 | 1 | finding: AP-11 |
| AP-12 | ≥10-line structurally identical blocks | all source files | 1: completion blocks 95-99 / 117-122 (4 lines) | discarded: below threshold, removed by the AP-10 rewrite |
| AP-12 | Same rule in several places | all source files | 0 | none |
| AP-12 | Same validation/error mapping repeated | AppManager.js | 1 | covered by AP-09 |
| AP-12 | Hand-written mapping repeated | all source files | 0 | none |
| AP-12 | Copy-and-modify lineage | all source files | 0 | none |
| AP-12 | Same constant literal across files | all source files | 1: 'PAID' (AppManager.js 21, 108) | covered by AP-15 |
| AP-12 | Repeated condition at many call sites | all source files | 0 | none |
| AP-13 | Paired acquire/release | all source files | 0 | none |
| AP-13 | Handle without release on failure | AppManager.js:7 | 1: DB never closed | discarded: single process-lifetime in-memory connection |
| AP-13 | Connection per call | all source files | 0 | none |
| AP-13 | Outbound call without timeout | all source files | 0 | none |
| AP-13 | Retry without bound | all source files | 0 | none |
| AP-13 | Unbounded read | AppManager.js:83, 92 | 1 | covered by AP-10 |
| AP-13 | Unbounded accumulator/cache | utils.js:9 | 1 | covered by AP-07 |
| AP-13 | Background task without shutdown | all source files | 0 | none |
| AP-13 | Unbounded recursion | all source files | 0 | none |
| AP-14 | Runtime deprecation warnings (Layer 1, `--pending-deprecation --trace-deprecation --redirect-warnings`) | exercised: boot; checkout success, denied, missing fields, unknown course, numeric card; financial report; delete user (no seed/migration script exists besides the boot's initDb) | 0 (no warning file written) | none |
| AP-14 | Dependency flagged deprecated in metadata | `npm ci` output; `npm view express@4.22.1 deprecated`, `npm view sqlite3@5.1.7 deprecated` | 9 transitive (sqlite3 install chain); 0 direct | finding: AP-19 sqlite3 (LOW), reported once there |
| AP-14 | Version marked unsupported by manifest | package.json | 0 | none |
| AP-14 | Structurally superseded construct | AppManager.js | 1: callback-only driver API | discarded: no upgrade path established from a Tier A–C source (Tier D only) |
| AP-14 | Live lookups (registry, outdated) | `npm outdated` 2026-11-05 | express 4.22.1 (wanted 4.22.3, latest 5.3.0); sqlite3 5.1.7 (latest 6.0.1) | informs AP-19 findings |
| AP-15 | Unexplained numeric literal | all source files | 3: utils.js 19, 20, 22 | finding: AP-15 |
| AP-15 | Bare duration/size | all source files | 0 | none |
| AP-15 | String literal as enum | AppManager.js | 2: 'PAID', 'DENIED' | finding: AP-15 |
| AP-15 | Literal repeated | AppManager.js | 1 | finding: AP-15 |
| AP-15 | Numeric code compared directly | AppManager.js:46 | 1: `startsWith("4")` | finding: AP-15 |
| AP-15 | Unnamed index | all source files | 0 | none |
| AP-15 | Environment literal inline | utils.js:6 | 1: port 3000 in config object | discarded: already in the config object; moved to env in RP-01 |
| AP-16 | Name contradicting behaviour | all source files | 1: `logAndCache` also mutates global | finding: AP-16 (badCrypto/AppManager), AP-07 |
| AP-16 | Non-descriptive identifiers | AppManager.js:29-33 | 5 | finding: AP-16 |
| AP-16 | Several names for one concept | AppManager.js | 1: usr/name, eml/email, pwd/pass | discarded for request fields (contract); internals in AP-16 |
| AP-16 | Name describes how not what | utils.js:17 | 1 | finding: AP-16 |
| AP-16 | Mixed naming conventions | all source files | 1: snake_case wire fields vs camelCase | discarded: wire fields are contract |
| AP-16 | Mixed human languages | all source files | 1 | finding: AP-16 |
| AP-16 | Inconsistent file naming | src/ | 1: AppManager.js vs app.js/utils.js | finding: AP-16 |
| AP-16 | Comment contradicting code | all source files | 0 (no comments) | none |
| AP-16 | Boolean params at call sites | all source files | 0 | none |
| AP-17 | Commented-out code | all source files | 0 | none |
| AP-17 | Unreachable branch | all source files | 0 | none |
| AP-17 | Defined but never referenced | all source files | 4: totalRevenue, dbUser, dbPass, smtpUser | finding: AP-17 |
| AP-17 | Unused import / undeclared-use dependency | all source files | 1: totalRevenue import AppManager.js:2 | finding: AP-17 |
| AP-17 | Parameter never read / value never used | utils.js | 1: globalCache never read | finding: AP-17/AP-07; audit_logs discarded as AP-17: append-only audit trail by name |
| AP-17 | Constant feature flag | all source files | 0 | none |
| AP-17 | Unregistered endpoint | all source files | 0 | none |
| AP-17 | Backup/old copies | target tree | 0 | none |
| AP-18 | Debug mode by literal | all source files | 0 | none |
| AP-18 | Dev server as production server | app.js | 0 (Express's listen is its production server) | none |
| AP-18 | Any-address bind with debug/diagnostics | app.js:12 | 0 (binds all interfaces, no debug console) | none |
| AP-18 | Error output exposing internals (observed) | runtime: malformed JSON on /api/checkout | 1 | finding: AP-18 |
| AP-18 | Permissive CORS | all source files | 0 (no CORS) | none |
| AP-18 | Unrestricted admin/diagnostic surface | AppManager.js:80 | 1 | covered by AP-04 (report) |
| AP-18 | Protective defaults off | all source files | 0 | none |
| AP-19 | Advisory for direct dependency at resolved version | `npm audit` 2026-11-05 | 0 direct | none |
| AP-19 | Advisory for transitive dependency | `npm audit` 2026-11-05 | 13 packages | findings: AP-19 express (HIGH), AP-19 sqlite3 (LOW) |
| AP-19 | Range would resolve to fixed, lock pins vulnerable | package-lock.json vs `npm audit fix` | express chain | finding: AP-19 express |
| AP-19 | No lockfile with ranges | target tree | 0 (lockfile present) | none |
| AP-19 | No lockfile, exact pins | target tree | 0 | none |
| AP-20 | Identity column without UNIQUE | AppManager.js:12, 40 | 1: users.email | finding: AP-20 |
| AP-20 | Reference column without FK | AppManager.js:14-15 | 3 | finding: AP-20 |
| AP-20 | Parent delete without child rule | AppManager.js:133 | 1 | finding: AP-20 |
| AP-20 | Money in binary float | AppManager.js:13, 15 | 2 | finding: AP-20 |
| AP-20 | Required column nullable / free-text enum | AppManager.js:12-16 | 2: payments.status free text; all NOT NULL missing | finding: AP-20 |

## Classification Decisions
none — the two privileged operations are unambiguous under §6: the financial report is a management aggregate with financial figures and per-student rollups under an `admin` path; `DELETE /api/users/:id` deletes the credential-holding account by request id in an application with no identity model.

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Node runtime APIs used by the app | node:24.12.0 | deprecation | A (none emitted) | `--pending-deprecation --trace-deprecation` run over boot + surface | n/a — local | no issue found |
| express | 4.22.1 | deprecation | B | `npm view express@4.22.1 deprecated` | 2026-11-05 | no issue found |
| sqlite3 | 5.1.7 | deprecation | B | `npm view sqlite3@5.1.7 deprecated` | 2026-11-05 | no issue found |
| sqlite3 install chain (tar, glob, rimraf, inflight, npmlog, prebuild-install, gauge, are-we-there-yet, @npmcli/move-file) | lockfile versions | deprecation | B | npm registry deprecation notices printed by `npm ci` | 2026-11-05 | AP-19 sqlite3 (LOW) |
| express → body-parser 1.20.4, proxy-addr 2.0.7, path-to-regexp 0.1.12, qs 6.14.2 | lockfile versions | advisory | B | `npm audit` (GitHub Advisory Database) | 2026-11-05 | AP-19 express (HIGH) |
| sqlite3 → tar 6.2.1, brace-expansion 1.1.12, ip-address 10.1.0, @tootallnate/once | lockfile versions | advisory | B | `npm audit` | 2026-11-05 | AP-19 sqlite3 (LOW) |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-1 | `run … sleep infinity` on run-1; `exec npm ci`; `exec -d node --pending-deprecation --trace-deprecation --trace-warnings --redirect-warnings=/app/node-warnings.log src/app.js` | first `proc wait` timed out at 30 s (exit 4); second wait ready on 3000. The process later exited on its own after the checkout-card-number-type request (uncaught TypeError) |
| 2 | 2 | stop | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-1 | `docker rm -f` by exact name | removed |
| 3 | 2 | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-2 | `run … sleep infinity` on run-2; `exec npm ci`; `exec -d node src/app.js` (native configuration) | ready on 3000 after 4.8 s |
| 4 | 2 | stop | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-2 | `docker rm -f` by exact name | removed |
| 5 | 3a | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-3 | `run … sleep infinity` on run-3; `exec npm ci`; `exec -d node src/app.js` | ready after 3.8 s; full capture; the process exited on its own at `sec-post-checkout-numeric-card` (crash) |
| 6 | 3a | restart | container | same container (-3) | `exec -d node src/app.js` | ready after 5.5 s; capture of the remaining ids; exited on its own at `rob-post-checkout#card=number` |
| 7 | 3a | restart | container | same (-3) | `exec -d node src/app.js` | ready 5 s; `card=boolean` alone; exited on its own (crash) |
| 8 | 3a | restart | container | same (-3) | `exec -d node src/app.js` | ready 4.8 s; `card=list` alone; exited on its own (crash) |
| 9 | 3a | restart | container | same (-3) | `exec -d node src/app.js` | ready 5 s; `card=empty-object` alone; exited on its own (crash) |
| 10 | 3a | restart | container | same (-3) | `exec -d node src/app.js` | ready 4.8 s; `card=nested-object` alone; exited on its own (crash) |
| 11 | 3a | restart | container | same (-3) | `exec -d node src/app.js` | ready 4.8 s; remaining 14 variants captured; process alive |
| 12 | 3a | stop | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-3 | `docker rm -f` by exact name | removed |
| 13 | 3a | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-4 | run-4; `npm ci`; `exec -d node src/app.js` | ready 4 s; destructive `delete-user-existing` alone |
| 14 | 3a | stop | container | -4 | `docker rm -f` by exact name | removed |
| 15 | 3a | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-5 | run-5; `npm ci`; `exec -d node src/app.js` | ready 4.5 s; destructive `sec-delete-user-anonymous` alone |
| 16 | 3a | stop | container | -5 | `docker rm -f` by exact name | removed |
| 17 | 3b | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-6 | refactored-1; `npm ci`; `npm install sqlite3@^6.0.1`; `npm audit fix`; `npm install express@^4.22.3`; `exec -d -e OPERATOR_TOKEN=… node … src/app.js`; then a foreground `exec node src/app.js` to read the error | `proc wait` timed out (exit 4); the process had exited: `GLIBC_2.38 not found (required by …/node_sqlite3.node)` — the sqlite3 6.0.1 prebuilt binary does not load on the image. sqlite3 reverted to ^5.1.6 (resolved 5.1.7); `npm audit fix` re-run |
| 18 | 3b | stop | container | -6 | `docker rm -f` by exact name | removed |
| 19 | 3c | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-7 | refactored-2; `npm ci`; `exec -d -e OPERATOR_TOKEN=… node --pending-deprecation --trace-deprecation --redirect-warnings=… src/app.js` | ready 5 s; replay 1 (74 entries, 0 errors); no warnings file |
| 20 | 3c | stop | container | -7 | `docker rm -f` by exact name | removed |
| 21 | 3c | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-8 | refactored-3; `npm ci`; `exec -d -e OPERATOR_TOKEN=… node src/app.js` | ready 5.3 s; `delete-user-existing` alone |
| 22 | 3c | stop | container | -8 | `docker rm -f` by exact name | removed |
| 23 | 3c/3d | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-9 | refactored-4; `npm ci`; `exec -d -e OPERATOR_TOKEN=… node src/app.js` | ready 4.8 s; `sec-delete-user-anonymous` alone; compare 1; re-audit runtime checks (malformed JSON, `npm audit`, `npm ls`) |
| 24 | 3c/3d | stop | container | -9 | `docker rm -f` by exact name | removed |
| 25 | 3d | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-10 | refactored-5 (after the re-audit fixes); `npm ci`; `exec -d -e OPERATOR_TOKEN=… node --pending-deprecation … src/app.js` | ready 6 s; replay 2 (74 entries, 0 errors); no warnings file |
| 26 | 3d | stop | container | -10 | `docker rm -f` by exact name | removed |
| 27 | 3d | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-11 | refactored-6; `npm ci`; `exec -d … node src/app.js` | ready 5 s; `delete-user-existing` alone |
| 28 | 3d | stop | container | -11 | `docker rm -f` by exact name | removed |
| 29 | 3d | start | container | refactor-arch-ecommerce-api-legacy-202611050130-5d509d26-12 | refactored-7; `npm ci`; `exec -d … node src/app.js` | ready 4.8 s; `sec-delete-user-anonymous` alone; compare 2 |
| 30 | 3d | stop | container | -12 | `docker rm -f` by exact name | removed |

## Verification Coverage
Full — all planned checks executed. Notes:
  - Layer 2 used `npm audit` / `npm view` / `npm outdated` (the ecosystem's own tools); OSV.dev was not queried separately.
  - The application's stdout was not captured in container mode (`exec -d`); deprecation evidence came from the redirected warnings file, which was never created (no warnings).
  - Scratch root: the environment's scratch directory (§1.1, option 1).

================================
Total: 19 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
ecommerce-api-legacy/
├── .gitignore                       (new)
├── README.md                        (run instructions + variables to export)
├── api.http                         (operator header on the two guarded requests)
├── package.json                     (express ^4.22.3; sqlite3 ^5.1.7)
├── package-lock.json                (regenerated by npm)
├── reports/
│   ├── audit-20261105-0130.md       (Phase 2, as at the gate)
│   ├── audit-latest.md              (this file)
│   ├── surface.json · baseline.json · replay.json · replay-2.json
└── src/
    ├── app.js                       composition root: config, wiring, router, error boundary, listen
    ├── config/
    │   └── index.js                 environment read once, validated, frozen
    ├── models/                      domain + persistence (repositories kept in the model layer)
    │   ├── database.js              promise wrapper, isolated transactions
    │   ├── schema.js                DDL with UNIQUE/NOT NULL/CHECK, integer cents, seed
    │   ├── errors.js                error taxonomy
    │   ├── payment.js               approval rule, statuses, card masking
    │   ├── password.js              scrypt hashing, unusable hash
    │   ├── money.js                 cents conversion
    │   ├── userRepository.js
    │   ├── courseRepository.js
    │   ├── enrollmentRepository.js  enrollment + payment + audit in one transaction
    │   └── financialReport.js       one set-based query + report assembly
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── views/
    │   ├── routes.js                parse → call → render; paths, statuses and bodies unchanged
    │   └── requestParsers.js        boundary type/range validation
    └── middlewares/
        ├── requireOperator.js       operator guard (OPERATOR_TOKEN, fail closed, constant time)
        ├── errorHandler.js          single error boundary
        └── asyncHandler.js
```
Removed: `src/AppManager.js`, `src/utils.js` (content migrated; rewrite in place).
Layout choice: repositories live in `models/` (the guidelines' default for a project this size).

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 11 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 4 FIXED, 0 NOT FIXED
  ✓ Malformed input: 59 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 3 operations
  ✓ Values: 2 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 15/19  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 3 proposed-not-applied, 0 unresolved  (re-audit: 3 findings)
    Re-audit passes: 2; fixed after re-audit: 2 (0 of them missed-in-phase-2)
  ✓ Processes: 12 started, 12 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

### Finding status (Phase 2 → Phase 3)
| # | Finding | Status | Note |
|---|---|---|---|
| 1 | [CRITICAL] God Module (AP-03) | resolved | split into config / models / controllers / views / middlewares (RP-03, RP-05) |
| 2 | [CRITICAL] AP-04 checkout reuses an account by e-mail | proposed | business operation with no identity model (contract-changing) |
| 3 | [CRITICAL] AP-08 card number and key logged | resolved | log line carries `****<last 4>` only, no key (RP-08) |
| 4 | [CRITICAL] AP-09 error handling | resolved | promise-based driver, one transaction for the 3 writes, single error boundary; crashes now answer 400 (security entry `sec-post-checkout-numeric-card` FIXED) |
| 5 | [CRITICAL] AP-04 open financial report | resolved | guarded by `X-Operator-Token` = `OPERATOR_TOKEN`, fail closed (403); `sec-get-admin-financial-report-anonymous` FIXED; operator path PASS + value entry HOLDS |
| 6 | [CRITICAL] AP-04 anonymous account deletion | resolved | same guard; `sec-delete-user-anonymous` FIXED; operator path `delete-user-existing` PASS |
| 7 | [CRITICAL] AP-01 hardcoded secrets | proposed | code part done: literals removed, config from environment, seed account gets an unusable password. Remaining: operator residue — rotate the committed values |
| 8 | [CRITICAL] AP-08 password encoding | resolved | scrypt with a per-password salt; no-password accounts get an unusable hash (RP-08). No legacy hashes persist (in-memory store) |
| 9 | [HIGH] AP-19 express chain | resolved | express 4.22.1 → 4.22.3 (same major); `npm audit` shows no advisory left for body-parser 1.20.9, qs 6.16.2, proxy-addr 2.0.8, path-to-regexp 0.1.13 (2026-11-05); replay PASS |
| 10 | [HIGH] AP-06 hard-wired dependencies | resolved | composition root `src/app.js`; repositories and controllers receive collaborators; no import-time side effects |
| 11 | [HIGH] AP-11 boundary validation | resolved | `views/requestParsers.js`; 59/59 robustness variants ROBUST; `sec-post-checkout-boolean-course` FIXED |
| 12 | [HIGH] AP-18 stack traces in error output | resolved | error boundary answers `400 Bad Request` for malformed JSON (status kept); observed by the re-audit, see Verification Coverage |
| 13 | [HIGH] AP-07 mutable global state | resolved | write-only global cache and exported mutable variable removed |
| 14 | [MEDIUM] AP-10 N+1 in report | resolved | one JOIN query ordered by course and enrollment; value entry HOLDS (same courses, revenues, students, amounts, order) |
| 15 | [LOW] AP-19 sqlite3 install chain | proposed | see Proposed, Not Applied. `npm audit fix` cleared brace-expansion and ip-address; tar/node-gyp/@tootallnate/once and the deprecated build-time packages remain |
| 16 | [LOW] AP-17 dead code | resolved | `totalRevenue`, `dbUser`, `dbPass`, `smtpUser`, `globalCache` removed |
| 17 | [LOW] AP-20 schema constraints | proposed | applied: `users.email` UNIQUE, NOT NULL columns, `payments.status` CHECK, money as integer cents (value entry HOLDS). Remaining (proposed): foreign keys and what a user delete does to its enrollments/payments |
| 18 | [LOW] AP-16 naming | resolved | internal identifiers renamed; request field names (`usr`, `eml`, `pwd`, `c_id`, `card`) kept as contract |
| 19 | [LOW] AP-15 magic values | resolved | `APPROVED_CARD_PREFIX`, `PaymentStatus`, KDF parameters, cents factor named |

### Re-audit
Pass 1 (over the first refactored tree) found 3 items under PROPOSED, NOT APPLIED and 2 unresolved, both with origin `introduced`:
- [HIGH] Swallowed or Uncentralized Error Handling (AP-09), src/models/database.js `transaction`: BEGIN…COMMIT ran on the shared connection while other requests' statements could execute inside it, so a rollback could discard another request's write. Fixed: statements outside a transaction wait for open transactions; transaction work uses its own handle.
- [LOW] Dead Code (AP-17), src/config/index.js `paymentGatewayKey` (no reader after the card log was fixed) and `Database.close()` (never called). Fixed: both removed (README updated).
Then a second full replay (results above, identical counts) and pass 2.
Pass 2: 3 findings, all proposed-not-applied (AP-04 checkout, AP-19 sqlite3 install chain, AP-20 foreign keys/delete rule); 0 unresolved. The AP-01 rotation is an operator step with no trace in the tree.
Discarded in the re-audit: the error text `Erro DB` repeated in three controllers (AP-15/AP-12 signal) — it is each operation's own intentional error body, and one shared constant would tie three error contracts together.

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization — checkout attaches purchases to any existing account   (AP-04)
File: src/controllers/checkoutController.js:54-69 (was src/AppManager.js:40-75)
Reason not applied: the application has no identity model. Checking the password of an existing account would reject clients that check out today with a known e-mail and any or no password. That is a business operation, so the change is contract-changing.
Proposed change: decide who may buy for an existing account. Either verify the stored password (scrypt is now in place, so `pwd` can be checked) or introduce a session or token. Then make the existing-account path require it. Coordinate with every client of `POST /api/checkout`.

### [CRITICAL] Hardcoded Secrets and Credentials — operator residue   (AP-01)
File: (git history) src/utils.js:1-7 at b90300c
Reason not applied: the code no longer contains the values, but they stay in the repository history. Only the owner can invalidate them.
Proposed change: rotate the payment gateway key (`pk_live_…`) and the database password that were committed. Treat both as compromised. Do it now, before this branch is shared. Then supply the new key through the environment if a gateway is ever wired in.

### [LOW] Known-Vulnerable Dependency — sqlite3 install-time chain   (AP-19, with AP-14)
File: package.json:11-11
Reason not applied: the fix npm names is sqlite3 6.0.1, a major upgrade. Applying it was attempted, and the replay boot failed: the 6.0.1 prebuilt binary needs `GLIBC_2.38`, which the `node:24.12.0` (Debian bookworm) image lacks. This is a behaviour change for whoever deploys the app, so it was reverted (RP-18, step 4). `prebuild-install@7.1.3` is also deprecated upstream with no named successor ("No longer maintained… alternatives are available", npm registry, 2026-11-05). It is still a dependency of sqlite3 6.0.1.
Proposed change: upgrade to sqlite3 ^6.0.1 together with a runtime image or host on glibc ≥ 2.38, or build the addon from source on the deployment image. Then replay. Alternatively, evaluate a maintained SQLite driver, which is a new dependency. Until then, the advisories affect only install/build time (node-gyp/tar), not the running server.

### [LOW] Missing Schema-Level Integrity Constraints — foreign keys and delete rule   (AP-20)
File: src/models/schema.js:11-35
Reason not applied: `DELETE /api/users/:id` today keeps the user's enrollments and payments, and its response says so. Enforced foreign keys (with `PRAGMA foreign_keys = ON`) would make that delete either fail (restrict) or remove the children (cascade). Both change what the operation does.
Proposed change: decide the rule (refuse deleting users with enrollments, cascade, or detach). Then declare `enrollments.user_id → users.id`, `enrollments.course_id → courses.id` and `payments.enrollment_id → enrollments.id` with that rule, and switch enforcement on. To count today's violating rows: `SELECT e.id FROM enrollments e LEFT JOIN users u ON u.id = e.user_id WHERE u.id IS NULL;`

## Verification Coverage
DEGRADED — the following checks did not run as specified, and the results above do not cover them:
  - Baseline crash recovery (protocol §3.1): after each crash of the original (6 times, rows 5–10 of the Execution Log), the original was rebooted **inside the same container** (`exec -d`), not from a fresh run copy. The datastore is `:memory:` and the application writes no files, so every reboot started from the seed state. The run copy itself was never changed by the application. The capture was split into 7 `--merge` runs; all 74 non-destructive entries ended up OBSERVED or ERROR (the ERRORs are the 5 card variants and the numeric-card security entry, each confirmed by the process exiting).
  - Card-number masking in the log (AP-08) and the stored password format (AP-08): their effect is in the process log and the in-memory database, which no surface entry can read. They have no value entry → UNVERIFIED by the replay. Read in code: src/controllers/checkoutController.js, src/models/password.js.
  - Removal of the stack-trace page (AP-18): the effect is a text body of the framework's default page. A contract entry for it would report the intended change as a REGRESSION, and value entries only address JSON. It was observed once by the re-audit's runtime check: `POST /api/checkout` with body `{` answered `400`, `Content-Type: text/html`, body `Bad Request`. The replay does not cover it.
  - Operator guard: the replay ran with `OPERATOR_TOKEN` set. The fail-closed path with no token configured was exercised only through the anonymous and empty-header variants, not through a boot without the variable.
  - Layer 2 used `npm audit` / `npm view` / `npm outdated`; OSV.dev was not queried separately.
Scratch root: the environment's scratch directory (§1.1, option 1). Snapshot directory `refactor-arch-ecommerce-api-legacy-202611050130-5d509d26` deleted after the re-audit.
Closing check: `docker ps -a --filter label=refactor-arch.run=202611050130-5d509d26` returned no container.
Fixtures by reference: {{env:OPERATOR_TOKEN}}, {{env:CHECKOUT_PASSWORD}}
================================
