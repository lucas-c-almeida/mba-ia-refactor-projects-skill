================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.22.1
Files:   3 analyzed | ~183 lines of code
Date:    2026-09-25 18:29
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    clean at c19c6961d0d0ac7527b804d17fb73068a893a7eb — the audit read the working tree as found
Runtime: installed the declared dependencies from package-lock.json into the run copy's own node_modules, inside the container (the target's own node_modules is a Windows-host native build of sqlite3 and was excluded from every copy)
Isolation: container (Docker 28.5.2, image node:24 — glibc-based; node:24-alpine was rejected because sqlite3's prebuilt native addon does not ship a musl build)
Scratch: environment scratch directory (protocol §1.1)

## Summary
CRITICAL: 7 | HIGH: 6 | MEDIUM: 1 | LOW: 3

## Findings

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:1-142
Description: The `AppManager` class concentrates persistence (raw `this.db.run`/`get`/`all` calls throughout, e.g. lines 12-21, 37, 50, 54, 57), business rules (the payment-approval heuristic at line 46, revenue aggregation at lines 89-121, the password fallback at line 68) and delivery (all three routes registered and handled inline in `setupRoutes`, lines 25-138) in one file. It also holds three unrelated domain concepts — checkout/enrollment, financial reporting, and user deletion — which alone is the catalog's "several unrelated domain concepts" signal, independent of the ~300-400 line size threshold (this file is 142 lines).
Impact: Nothing in this file can be tested without an in-memory database and a live Express app object. A change to payment logic, to the report, or to user deletion each risks the other two, because they share one file, one constructor and one implicit call chain.
Recommendation: RP-03 — split by responsibility: a repository per entity for persistence, a policy/use-case module for the checkout and reporting rules, and thin route handlers that parse, call and render. Per the catalog's AP-03/AP-05 precedence rule, the handlers' business logic (which would otherwise be AP-05) is folded into this finding rather than filed separately.
Recommendation: RP-03
Contract: safe — the registered routes, methods and response shapes are unchanged by moving code between files.

### [CRITICAL] Hardcoded Secrets and Credentials — default password used as a real credential   (AP-01)
File: src/AppManager.js:66-71
Description: When `/api/checkout` is called for an email with no existing user, line 68 computes `badCrypto(p || "123456")`: if the client omits `pwd`, the literal `"123456"` becomes the account's actual, working password — not a placeholder. This matches the catalog's "default value that is a real secret" signal directly.
Impact: Any caller can create a real, usable account for an arbitrary email simply by omitting `pwd`; that account's password is then a fixed, publicly-known string. There is no login endpoint in this API today, so the immediate blast radius is limited to this codebase, but the credential is real and would authenticate wherever this "hash" is later trusted — the obvious next step for an LMS API that already has signup-via-checkout.
Recommendation: RP-01 — when `pwd` is absent, generate a random per-account credential server-side instead of defaulting to a fixed literal.
Contract: safe — checkout still succeeds without a `pwd` field either way; only the value actually stored changes from a fixed, known string to a random one. (Making `pwd` itself required would be a separate, contract-changing decision — see the AP-11 finding below.)

### [CRITICAL] Missing or Bypassable Authorization — financial report   (AP-04)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` has no authentication check and no authorization check anywhere on its path — despite its name and its content (per-course revenue, every enrolled student's name, and what each student paid), any unauthenticated caller can read it. Directly observed: calling it with no credentials returned `200` with the full report, including student names and amounts paid.
Impact: Complete disclosure of business revenue and per-student payment data to anyone who can reach the API.
Recommendation: RP-04 — introduce an identity model and enforce it on this operation.
Contract: contract-changing — the application has no identity model at all (no login, session or token anywhere in the code); every current caller of this endpoint is anonymous, so any new authentication requirement rejects all of them. Per the legitimate-use test (`04-architecture-guidelines.md` §6), this is proposed, not applied.

### [CRITICAL] Missing or Bypassable Authorization — delete user   (AP-04)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` has no authentication or ownership check; the handler deletes whatever row matches the supplied `id`, with no verification of who is asking. Directly observed: an unauthenticated call to `DELETE /api/users/999` was accepted and executed.
Impact: Anyone can delete any user by guessing or enumerating small integer ids — a destructive, unauthenticated operation reachable from the public internet.
Recommendation: RP-04.
Contract: contract-changing — same reasoning as above (no identity model exists anywhere in the application); proposed, not applied.

### [CRITICAL] Swallowed or Uncentralized Error Handling — delete always reports success   (AP-09)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` ignores the callback's `err` parameter entirely and always sends the same "deleted" response, regardless of whether the delete matched a row or the driver failed. Directly observed: `DELETE /api/users/999` (a non-existent id — nothing to delete) still returned `200` with "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." Escalated from the catalog's default HIGH to CRITICAL: this matches "a swallowed failure silently discards a persisted write" — any real failure of this delete (a lock, a driver error) would be reported to the caller identically to the no-op case just observed. Related, and worth noting in the same place: `/api/checkout`'s multi-step write (user → enrollment → payment → audit_log, lines 50-61) also has no transaction boundary, so a failure partway through leaves partial state with no compensation — the same absence of error-handling discipline, on a different path.
Impact: A caller cannot tell a successful deletion from a failed one; anything that depends on "the delete succeeded" is silently wrong exactly when it matters most.
Recommendation: RP-09 — introduce a domain error taxonomy and a centralized boundary; this handler should propagate the driver error and report whether a row was actually affected (the driver's own `this.changes`).
Contract: contract-changing — today this endpoint has exactly one observable outcome (200 + fixed text) no matter what happens in the database; making it report failure accurately introduces a status/body the client has never observed on this path. Propose it alongside the AP-04 fix for the same endpoint — both are gated on the same product decision about what this operation should actually do.

### [CRITICAL] Hardcoded Secrets and Credentials — configuration literals   (AP-01)
File: src/utils.js:1-7
Description: `dbPass` ("senha_super_secreta_prod_123") and `paymentGatewayKey` ("pk_live_1234567890abcdef") are literal secrets assigned to identifiers matching the credential-name pattern, committed in source. `paymentGatewayKey` is live-looking (`pk_live_...`) and is actually read and logged at AppManager.js:45 (see the separate AP-08 finding on that line).
Impact: Anyone with read access to the repository, a clone, or a stack trace holds these values. `paymentGatewayKey` reaching what is presented as a real payment gateway is the catalog's own escalating condition ("the credential reaches a third-party or production system"); rotation requires a code change and a redeploy, and the value stays in git history even after removal.
Recommendation: RP-01 — externalize into environment-read configuration with a fail-loud check for missing required values; rotate `paymentGatewayKey` (and whatever real credential `dbPass` stands in for), since both are now permanently in history.
Contract: safe — where a value is read from is not observable to a client.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — reversible password storage   (AP-08)
File: src/utils.js:17-23
Description: `badCrypto` (called at AppManager.js:68) is the only "hashing" applied to user passwords. It repeats `Buffer.from(pwd).toString('base64').substring(0,2)` 10,000 times and truncates the result to 10 characters. Base64 is a reversible encoding, not a one-way function — the transformation is decodable, not merely weak, and truncation to 10 characters collapses the space further. This matches the catalog's own escalating example almost verbatim: "encoded (base64/hex) and described as if that were protection."
Impact: Every password in `users.pass` can be recovered by anyone with read access to the database, trivially — there is no cryptographic protection at all, despite the function's name suggesting there is (compounds with AP-16, below).
Recommendation: RP-08 — replace with a purpose-built password KDF (bcrypt/scrypt/argon2), with a per-credential salt and a tunable work factor.
Contract: safe — there is no login/authenticate endpoint in this API today that reads these hashes back, so changing the storage format changes nothing a client observes.

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:4-9
Description: The constructor opens its own database connection (`this.db = new sqlite3.Database(':memory:')`, lines 6-8) instead of receiving one; `src/app.js:8-10` instantiates `AppManager` directly and calls `initDb()`/`setupRoutes()` in sequence, with no factory and no composition root separating wiring from logic.
Impact: `AppManager` cannot be constructed in a test without a real (even if in-memory) sqlite3 database. There is exactly one way to wire this application, and it is split across two files rather than assembled in one place.
Recommendation: RP-06 — inject the database connection (or a repository built from it); introduce a composition root that reads configuration, builds the connection, builds repositories/controllers, and wires routes.
Contract: safe — wiring is not observable.

### [HIGH] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-16
Description: `users.email` is used as the sign-in identity (`SELECT id FROM users WHERE email = ?`, line 40, taking the single/first result) with no `UNIQUE` constraint. `enrollments.user_id`/`enrollments.course_id` and `payments.enrollment_id` are foreign-key-shaped columns (joined and filtered on throughout) with no `FOREIGN KEY` declared. The application's own code documents the consequence: `DELETE /api/users/:id` (line 135) literally responds "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco" ("...but enrollments and payments stayed dirty in the database").
Impact: Escalated to HIGH because both aggravating conditions the catalog names are met at once: identity can be corrupted (nothing in the schema prevents two `users` rows for the same email — the existence check at line 40 and the insert at line 69 are not even atomic with each other), and reference integrity can be corrupted (deleting a user leaves `enrollments`/`payments` pointing at nothing — confirmed by the application's own response text).
Recommendation: RP-19 — add a `UNIQUE` index on `users.email` (zero existing rows violate it) and declare the foreign keys on `enrollments`/`payments`.
Contract: mixed — the `UNIQUE` index on `email` is safe (no existing duplicates, and it does not intersect any exercised write path). Actually *enforcing* the foreign keys is contract-changing: SQLite requires `PRAGMA foreign_keys = ON` per connection (an undeclared-or-unenabled foreign key counts as absent per the catalog), and turning it on would change what `DELETE /api/users/:id` does for any user with enrollments — from today's silent "success with orphans" to a database error. What happens on delete (refuse, cascade, or detach) is a product decision: propose it.

### [HIGH] Unsafe Handling of Credentials and Sensitive Data — card number and secret key logged   (AP-08)
File: src/AppManager.js:45-46
Description: `` console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`) `` writes the full, unmasked card number supplied by the client and the payment gateway secret key to the process log on every checkout. Directly observed: a checkout with card `4111222233334444` produced the log line `Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef`.
Impact: Whoever can read this process's logs — a log aggregator, a support engineer, a misconfigured log shipper — reads full card numbers and the live payment gateway credential together, in plaintext, on every transaction.
Recommendation: RP-08 — never log a full PAN (mask to last 4 digits) or a secret; redact both at the log boundary.
Contract: safe — logging is not part of the observed HTTP contract.

### [HIGH] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` reads all courses, then for each course runs a query for its enrollments (line 92, inside `courses.forEach`), then for each enrollment runs one query for the user (line 104) and a second for the payment (line 106) — a query nested two loops deep, so the round-trip count is proportional to courses × enrollments-per-course × 2, not to a handful of set-based queries.
Impact: Escalated to HIGH — this is a doubly-nested N+1, not a single one, on an admin reporting endpoint of exactly the kind that gets called repeatedly, and whose cost grows fastest as the business it reports on grows. Against a real (non-in-memory, remote) database this pattern also exhausts the connection pool under concurrent report requests.
Recommendation: RP-10 — collapse into a small number of set-based queries (join enrollments to users and payments, or batch by id list) and assemble the report from the result sets.
Contract: safe — same result content per course/student, same response shape; only the query strategy changes. Ordering of `students` within a course is not documented or guaranteed today.

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: src/app.js:1-14
Description: The application never sets or checks `NODE_ENV`, and registers no error-handling middleware. Directly observed: sending a malformed JSON body to `POST /api/checkout` produced Express's default development-mode error page — a full HTML stack trace, including internal file paths (`/app/node_modules/body-parser/lib/types/json.js:92:19`, and further frames down to `raw-body`). This is Express's built-in behaviour whenever `app.get('env')` is not `'production'`, which is the case here because `NODE_ENV` is never set anywhere in the codebase, its deployment files, or its documentation. Binding via `app.listen(config.port, ...)` with no host argument defaults to all interfaces — normal on its own, but combined here with the leaking default error page, it is exactly the aggravating combination the catalog names.
Impact: Every unhandled error — not just malformed JSON — leaks internal file paths and stack frames to any caller, for free. This also compounds with AP-09: because there is no centralized handler anywhere, this default page is the *only* error response the application has for anything it does not explicitly catch itself.
Recommendation: RP-17 — set safe runtime defaults regardless of environment, and replace Express's default error output with the centralized handler from the AP-09 fix (RP-09), keeping the status codes Express itself already chooses for these failures (e.g. 400 for a JSON parse error).
Contract: safe — per `04-architecture-guidelines.md` §6 ("the error contract"), the framework's default error page (what answers when nothing handled the error) is not part of the application's intentional contract; replacing its body while keeping the status code is safe.

### [HIGH] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: `globalCache` (line 9) is a module-level object mutated by `logAndCache` (lines 12-15), called once per successful checkout (`AppManager.js:59`) with a per-user key. It accumulates for the lifetime of the process, is shared across all concurrent requests, and is never read back, bounded or evicted anywhere in the codebase.
Impact: Unbounded, purposeless memory growth shared across concurrent requests; a second process instance (for scaling) would each keep a different, inconsistent cache, since nothing here is backed by the datastore.
Recommendation: RP-07 — if this data has a purpose, give it a bound and an eviction policy, or move it to the datastore; since this codebase never reads it back, the simplest fix is to delete it.
Contract: safe — nothing reads `globalCache` back through any observable route.

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: src/AppManager.js:29-35
Description: `POST /api/checkout` checks only the *presence* of `usr`, `eml`, `c_id`, `card` (`if (!u || !e || !cid || !cc) return 400`, line 35). There is no type check (`c_id` can be any non-empty string, not necessarily a numeric id), no format check on `eml`, no length or format check on `card`, and `pwd` is not validated at all — it is optional and silently falls back to a fixed default (see the AP-01 finding on that fallback).
Impact: Malformed input (a non-numeric `c_id`, an absurdly long `card` value) is not rejected at the boundary; it reaches the persistence layer and produces whatever the driver happens to do, rather than a clear `400`. Operators cannot distinguish a client bug from an attack from the response alone.
Recommendation: RP-11 — introduce a boundary schema: `c_id` must parse as a positive integer, `eml` must match a basic email shape, `card` must be a plausible card-number string.
Contract: safe for values unambiguously invalid on their face (a non-numeric `c_id`, a non-string `card`) — these already fail downstream today (404/500), so rejecting them earlier with `400` changes nothing a legitimate client observes. Making `pwd` required, or tightening `card` to a real format/Luhn check, could reject a request some current client sends today — that part is a product decision and is proposed, not applied.

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: The checkout handler destructures its entire input into single/double-letter names — `u`, `e`, `p`, `cid`, `cc` for `usr`, `eml`, `pwd`, `c_id`, `card` respectively — and keeps those names for the rest of the ~49-line handler (through line 77).
Impact: Every line that touches these variables requires re-deriving what they mean; the cost is paid by every future reader.
Recommendation: RP-16 — rename to the value's meaning (`userName`, `email`, `password`, `courseId`, `cardNumber`); this scope naturally disappears once the handler is split per the AP-03 fix.
Contract: safe — local variable names are not part of the public surface.

### [LOW] Magic Values — card-network heuristic standing in for payment processing   (AP-15)
File: src/AppManager.js:46-46
Description: `let status = cc.startsWith("4") ? "PAID" : "DENIED";` decides payment approval by checking whether the card number starts with the literal `"4"` (the Visa BIN prefix), with no named constant — and with no actual gateway call, despite the surrounding code logging that it is "processing" the card against `config.paymentGatewayKey` (line 45).
Impact: The literal `"4"` is unexplained in place; more importantly, the "payment processing" it stands in for is entirely fake, which is easy to miss because the log line and the gateway key suggest a real integration.
Recommendation: RP-15 — name the literal at minimum (`const VISA_PREFIX = '4'`); the underlying stub is a design decision for the project owner (no real gateway is available to integrate against in this exercise), so only the naming is applied here.
Contract: safe — naming a constant is not observable.

### [LOW] Dead Code — unused `totalRevenue`   (AP-17)
File: src/utils.js:10-10
Description: `totalRevenue` is declared (line 10) and exported (line 25), and imported by `AppManager.js:2`, but never read or written anywhere after its initial declaration.
Impact: A reader who sees `totalRevenue` imported into `AppManager.js` reasonably assumes it does something; it does not, and it sits as noise next to the real (if inefficient — see AP-10) revenue computation in the financial report.
Recommendation: RP-16 — delete the unused declaration, export and import.
Contract: safe — nothing outside this process reads it.

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-named identifier literal; seed/fixture writing to runtime datastore; connection URL with inline credentials; high-entropy/credential-prefix literal; framework signing/session key literal; credential-bearing file committed; default value that is a real secret | 2 findings (config literals; default-password fallback) |
| AP-02 | input reaching driver via concatenation/interpolation; interpolation markers inside statement string; ORM raw/escape-hatch with input; dynamic identifiers from input; shell/process exec with concatenated command; deserialization/template injection/path traversal | none — all driver calls use bound `?` placeholders with a separate parameter array |
| AP-03 | 3+ responsibility categories mixed; size threshold + 2+ categories; single unit >50 lines/deep nesting/many params; several unrelated domain concepts in one file; low-cohesion class; "manager/utils" grab-bag; high afferent coupling | 1 finding |
| AP-04 | surface entry with no auth/ownership check; IDOR via input id with no principal scoping; auth enforced only in delivery layer while reachable elsewhere; role/tenant value trusted from request; token accepted without verification; auth check written but unreachable; commented-out/flag-disabled guard | 2 findings (financial report; delete user) |
| AP-05 | route handler with domain decisions; persistence calls inside handler; handler >30 lines not parse/call/render; req/res objects reaching deep into call stack; duplicated rule across handlers; nominal service/controller pass-through | 0 separate findings — folded into AP-03 per the catalog's precedence rule (one module, several unrelated domain concepts) |
| AP-06 | unit constructs own collaborators; import-time side effects; no single composition root; test would require real DB/clock/filesystem; concrete types where abstraction needed; config read scattered at point of use | 1 finding |
| AP-07 | module-level var reassigned from multiple places; request-scoped data stored globally; in-memory collection as store of record; mutable default param/shared attribute/exported mutable object; cache/pool with no lifecycle; monkey-patched builtin; process-memory counter/sequence | 1 finding |
| AP-08 | password in reversible form/weak digest; shared/constant/missing salt; plain-equality credential comparison; sensitive values reaching a log; response serializing whole record; transport without protection/cert verification disabled; no expiry/revocation/rotation for tokens | 2 findings (reversible password storage; card+secret logged) |
| AP-09 | empty/log-and-continue catch; catch returning success on failure; over-broad catch; same error mapping repeated across handlers; no centralized handler at all; stack trace/SQL/path in response; errors signalled inconsistently; failure leaving partially-applied state; exceptions for expected control flow | 1 finding (delete-handler swallow; checkout's missing transaction boundary noted in the same finding) |
| AP-10 | driver/ORM call inside loop; iterating and fetching per element by FK; lazy relation inside iteration; repeated read collapsible to one query; remote call inside loop; whole table read into memory; write loop with one round trip per element | 1 finding |
| AP-11 | input used directly with no validation; optional input dereferenced without check; unconstrained pagination/limit; numeric parsing with no failure path; validation on one entry point but not a second; validation after side effect; domain invariants unenforced; no upper bound on body/array; validation scattered as ad hoc conditionals | 1 finding |
| AP-12 | ≥10-line structurally identical blocks; same rule in multiple places; same validation/error-mapping/serialization repeated; hand-written mapping duplicated with different fields; copy-and-modify lineage; same constant repeated across files; condition repeated across call sites | none at block scale — the repeated single-line error-mapping pattern is noted under AP-09 rather than filed separately |
| AP-13 | resource acquired/released without scope-bound construct; connection/file/cursor with no release on failure path; connection opened per call where pool exists; outbound call with no timeout; no retry policy; unbounded read into memory; unbounded in-memory cache; background task with no shutdown; unbounded recursion | none filed separately — the unbounded report read is the dominant AP-10 finding, the unbounded cache is the dominant AP-07 finding |
| AP-14 | Layer 1: `node --pending-deprecation --trace-deprecation` while exercising all 3 routes; Layer 2: npm registry `deprecated` field for both direct dependencies at their resolved versions | no issue found — see Dependency and Deprecated API Verification |
| AP-15 | unexplained numeric literal in a decision; bare duration/size with no unit; string literal as enumerated value repeated across files; numeric code compared directly; index/offset into fixed record; environment-specific literal inline | 1 finding (card-network heuristic); badCrypto's loop/substring literals and the repeated "PAID"/"DENIED" status strings are noted as further instances of the same pattern, not filed separately |
| AP-16 | name contradicting behaviour; non-descriptive identifiers outside tiny scope; several names for one concept; name describing how not what; mixed casing/pluralization; mixed human languages; inconsistent file/directory naming; stale comment contradicting code; unreadable boolean parameters | 1 finding (checkout parameter names); the codebase's consistent Portuguese response/log strings alongside English identifiers were checked and excluded — a deliberate, consistent choice, per the catalog's own de-escalation rule |
| AP-17 | commented-out code block; unreachable branch; unused/undeclared import; unused parameter; stuck feature flag; endpoint not reachable from any registration; duplicated older file version | 1 finding (`totalRevenue`) |
| AP-18 | debug/dev mode switched on by literal; dev server used as production server; bind-to-all-interfaces + debug/diagnostic combo; error output exposing internals; permissive CORS with credentials; diagnostic/admin routes reachable without restriction; protective defaults switched off | 1 finding (default error page leaks internals); the "admin route with no restriction" signal is the same evidence already filed as AP-04 and is not re-filed here |
| AP-19 | OSV.dev advisory query for both direct dependencies at their resolved, lockfile-pinned versions | no issue found — see Dependency and Deprecated API Verification |
| AP-20 | column treated as identity with no uniqueness constraint; column referencing another table's key with no foreign key; parent delete with no rule for children; money stored in binary floating point; column that must always have a value left nullable | 1 finding |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| express | 4.22.1 | deprecation | A | runtime warning (`node --pending-deprecation --trace-deprecation`, routes exercised: checkout, financial-report, delete-user, malformed-body) | 2026-09-25 | no issue found — no DeprecationWarning emitted |
| express | 4.22.1 | deprecation | B | npm registry (`npm view express@4.22.1 deprecated`) | 2026-09-25 | no issue found — empty (not deprecated) |
| express | 4.22.1 | advisory | B | OSV.dev (`POST api.osv.dev/v1/query`, ecosystem npm) | 2026-09-25 | no issue found — no advisories returned |
| sqlite3 | 5.1.7 | deprecation | A | runtime warning (same exercise as above) | 2026-09-25 | no issue found — no DeprecationWarning emitted |
| sqlite3 | 5.1.7 | deprecation | B | npm registry (`npm view sqlite3@5.1.7 deprecated`) | 2026-09-25 | no issue found — empty (not deprecated) |
| sqlite3 | 5.1.7 | advisory | B | OSV.dev | 2026-09-25 | no issue found — no advisories returned |

Context, not a finding (no deprecation or advisory evidence attached, so not reportable per AP-14/AP-19's evidence grading): as of 2026-09-25, the npm registry's `latest` tag for `express` is `5.2.1` and for `sqlite3` is `6.0.1` — both one major line ahead of the versions this project pins. Neither package's registry metadata marks the in-use version deprecated or yanked.

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | `refactor-arch-ecommerce-api-legacy-20260925-1829-1` | `docker run -d --name refactor-arch-ecommerce-api-legacy-20260925-1829-1 -v <run-1>:/app -w /app --label refactor-arch.run=20260925-1829 node:24 sh -c "npm install --no-audit --no-fund && node --pending-deprecation --trace-deprecation src/app.js"` (run-1, a fresh copy of pristine/) | ready on port 3000 (confirmed via `docker logs`, then exercised with 4 requests: checkout success, malformed-JSON checkout, financial-report, delete-nonexistent-user) |
| 2 | 2 | stop | container | `refactor-arch-ecommerce-api-legacy-20260925-1829-1` | `docker stop refactor-arch-ecommerce-api-legacy-20260925-1829-1` then `docker rm refactor-arch-ecommerce-api-legacy-20260925-1829-1` | stopped and removed by exact name |
| 3 | 3a | start | container | `...-1829-2` | boot original from `run-2/` (fresh copy of `pristine/`) | ready on port 3000 |
| 4 | 3a | stop | container | `...-1829-2` | `docker stop` then `docker rm` | stopped/removed; 8 contract entries captured to `baseline.json` |
| 5 | 3a | start | container | `...-1829-3` | boot original from `run-3/` (destructive entry, own fresh boot per protocol §2.2) | ready on port 3000 |
| 6 | 3a | stop | container | `...-1829-3` | `docker stop` then `docker rm` | stopped/removed; `delete-seed-user` captured, merged into `baseline.json` (9/9 total) |
| 7 | 3c | start | container | `...-1829-r1` | boot refactored app from `refactored-1/` (first refactor attempt) | **crashed on boot**: `SQLITE_ERROR: incomplete input` — a malformed inline SQL `--` comment in `models/db.js` swallowed the closing paren of the `enrollments` table statement |
| 8 | 3c | stop | container | `...-1829-r1` | `docker stop` then `docker rm` | stopped/removed; root-caused and fixed (real `FOREIGN KEY` clauses replace the comment trick) |
| 9 | 3c | start | container | `...-1829-r2` | boot fixed refactored app from `refactored-2/` (contract entries, replay pass 1) | ready on port 3000 |
| 10 | 3c | stop | container | `...-1829-r2` | `docker stop` then `docker rm` | stopped/removed; 7 PASS, 1 sanctioned REGRESSION (see Validation), 1 UNVERIFIED (destructive pending) |
| 11 | 3c | start | container | `...-1829-r3` | boot refactored app from `refactored-3/` (destructive entry, replay pass 1, own fresh boot) | ready on port 3000 |
| 12 | 3c | stop | container | `...-1829-r3` | `docker stop` then `docker rm` | stopped/removed; full pass-1 compare: 8 PASS, 1 sanctioned REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED |
| 13 | 3d | start | container | `...-1829-r4` | boot refactored app from `refactored-4/`, mandatory re-replay after the bounded-fix-loop changes (hashed seed password, `toCents` now used) | `npm install` fell back from a prebuilt sqlite3 binary to compiling it from source via `node-gyp` (network-dependent non-determinism, not a code defect); became ready, but the session was interrupted before any probe ran against it |
| 14 | 3d | stop | container | `...-1829-r4` | `docker stop` then `docker rm` | stopped/removed with no data collected; re-run cleanly as rows 15-18 below |
| 15 | 3d | start | container | `...-1829-r5` | boot refactored app from `refactored-5/` (destructive entry, replay pass 2, own fresh boot) | ready on port 3000 |
| 16 | 3d | stop | container | `...-1829-r5` | `docker stop` then `docker rm` | stopped/removed; `delete-seed-user` captured |
| 17 | 3d | start | container | `...-1829-r6` | boot refactored app from `refactored-6/` (contract entries, replay pass 2) | ready on port 3000 |
| 18 | 3d | stop | container | `...-1829-r6` | `docker stop` then `docker rm` | stopped/removed; final pass-2 compare (merged with row 16's capture): 8 PASS, 1 sanctioned REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED — identical to pass 1 |
| 19 | 3d | start | container | `...-1829-r7` | boot refactored app from `refactored-7/` with `--pending-deprecation --trace-deprecation`, re-audit's AP-14 Layer-1 check; exercised checkout, financial-report, malformed-JSON, delete-nonexistent-user | ready on port 3000; 0 `DeprecationWarning` lines across all 4 requests; malformed-JSON confirmed 400 + safe "Bad Request" body (AP-18 fix holds on a live boot, not just the probe) |
| 20 | 3d | stop | container | `...-1829-r7` | `docker stop` then `docker rm` | stopped and removed by exact name |

## Verification Coverage
Full — all planned Phase 2 **and** Phase 3 checks executed. The only deviation from a clean single pass: replay pass 1 (rows 9-12) ran against a refactored copy with a schema bug (row 7-8, `refactored-1`) that was caught by the boot itself (the application crashed rather than serving wrong data) and fixed before any probe ran against it — the bug never reached a captured result. Row 13's interrupted boot ("`refactored-4`") produced no data and was safely re-run in full as rows 15-18; nothing from that interruption is reflected in any count below.

================================
Total: 17 findings
================================

Confirmation: --yes (auto-approved, not human-reviewed)

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
ecommerce-api-legacy/
├── src/
│   ├── app.js                       composition root — the only file that names concrete implementations
│   ├── config/
│   │   └── settings.js              reads process.env once; PORT only (see settings.js for why the
│   │                                 original's dbUser/dbPass/smtpUser/paymentGatewayKey were dropped,
│   │                                 not carried forward as unused "required" config)
│   ├── errors.js                    domain error taxonomy (ValidationError, NotFoundError,
│   │                                 PaymentDeniedError, DatabaseError)
│   ├── models/
│   │   ├── db.js                    schema + seed data
│   │   ├── repositories.js          UserRepository, CourseRepository, EnrollmentRepository,
│   │   │                             PaymentRepository, AuditLogRepository — one connection, injected
│   │   ├── checkoutPolicy.js        payment-approval rule (named constant, no business logic in routes)
│   │   ├── password.js              one-way credential hashing (Node's built-in crypto.scrypt)
│   │   └── money.js                 exact-arithmetic cents <-> decimal helpers
│   ├── controllers/
│   │   ├── checkoutController.js    the checkout use case
│   │   ├── financialReportController.js   set-based report assembly (no N+1)
│   │   └── userController.js
│   ├── routes/
│   │   ├── checkoutRoutes.js        parse -> call -> render
│   │   ├── financialReportRoutes.js
│   │   └── userRoutes.js
│   └── middlewares/
│       └── errorBoundary.js         the one centralized error-handling boundary
├── package.json / package-lock.json
├── api.http / README.md
└── reports/
    ├── audit-20260925-1829.md       Phase 2 report, frozen at the gate
    ├── audit-latest.md              this file
    ├── surface.json                 public-surface inventory (9 entries: 8 contract + 1 destructive)
    ├── baseline.json                original application's captured behaviour
    └── replay.json                  refactored application's captured behaviour (pass 2, final)
```
Target architecture: literal MVC (`04-architecture-guidelines.md` §1) — this is an HTTP service with a
request surface, so no adaptation was needed or declared. Persistence lives inside the model layer as
repositories (the guidelines' "common MVC reading" option, applied uniformly across all five entities).

## Validation
  ✓ Application boots without errors
  ○ Public surface replayed: 8 PASS, 1 REGRESSION (sanctioned, see note), 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Note on the 1 REGRESSION (`checkout-malformed-json`): status stayed 400 in both baseline and
    replay; only the body changed, from Express's default HTML stack-trace page to a safe "Bad
    Request" text. That is the AP-18 fix working as intended — `04-architecture-guidelines.md` §6's
    "error contract" carve-out states the framework's default error page (what answers when nothing
    handled the error) is not part of the application's contract, so replacing it while keeping the
    status code is `safe`. The harness has no way to encode that carve-out, so it mechanically diffs
    the two bodies and reports REGRESSION; this note is what makes the distinction visible. Both
    replay passes (pass 1: rows 9-12 of the Execution Log; pass 2: rows 15-18) produced the identical
    8/1/0/0 result, confirming this is a stable, intended difference, not flakiness.
    This run's inventory carries no `kind: "security"` entries (none of the applied fixes changed how
    a hostile request is handled without also changing a status code already covered above), so no
    separate Security entries line appears.
  ○ Findings resolved: 12/17 (5 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 5 proposed-not-applied, 0 unresolved  (re-audit: 5 findings)
    Re-audit passes: 2; fixed after re-audit: 2 (1 of them missed-in-phase-2)
  ✓ Processes: 10 started, 10 stopped through their handles, 0 left running, 0 incidents
    Isolation: container

## Proposed, Not Applied

### [CRITICAL] Missing or Bypassable Authorization — financial report   (AP-04)
File: src/routes/financialReportRoutes.js:1-19
Reason not applied: the application has no identity model anywhere (no login, session or token); every
current caller of this route is anonymous, so any new authentication requirement rejects all of them —
contract-changing per the legitimate-use test (`04-architecture-guidelines.md` §6).
Proposed change: introduce an identity model (at minimum an API key or session scheme), decide who may
call this route, and enforce it in `controllers/financialReportController.js`. Needs a product decision
on the authentication mechanism and who holds admin access — not something this refactor can decide.

### [CRITICAL] Missing or Bypassable Authorization — delete user   (AP-04)
File: src/routes/userRoutes.js:1-27
Reason not applied: same reasoning as above — no identity model exists, every current caller is
anonymous.
Proposed change: same identity-model decision as above, plus an ownership/role check in
`controllers/userController.js` (only the account's own owner or an admin may delete it).

### [CRITICAL] Swallowed or Uncentralized Error Handling — delete always reports success   (AP-09)
File: src/models/repositories.js:42-55 (`UserRepository.deleteById`)
Reason not applied: today `DELETE /api/users/:id` has exactly one observable outcome (200, fixed text)
regardless of what the database reports; making it accurate introduces a status/body a client has never
observed on this path. It is also gated behind the same product decision as the AP-04 finding on the
same route — what this operation should even do, and for whom, has to be decided together.
Proposed change: propagate the driver error through `deleteById`, report the number of rows actually
affected (the driver's own `this.changes`), and have the route return 404 when nothing was deleted and
500 on a genuine driver error — once the AP-04 decision for this route is made.

### [MEDIUM] Missing Boundary Validation — checkout `pwd`/`card`   (AP-11)
File: src/routes/checkoutRoutes.js:20-44
Reason not applied: `pwd` is optional today and a legitimate client may already omit it; making it
required, or tightening `card` to a real format/Luhn check, could reject a request some current client
sends today.
Proposed change: decide whether `pwd` should become required (and how already-created passwordless
accounts are handled) and what card-format validation the product wants; add both to the boundary
schema in this file once decided.

### [HIGH] Missing Schema-Level Integrity Constraints — FK enforcement / delete behaviour   (AP-20)
File: src/models/db.js:29-51
Reason not applied: the foreign keys are declared but SQLite never enforces them without `PRAGMA
foreign_keys = ON`. Turning that on changes what `DELETE /api/users/:id` does for a user with existing
enrollments — from today's silent "success with orphans" to a database error — and choosing
refuse/cascade/detach is a product decision (`05-refactoring-playbook.md` RP-19). (The UNIQUE index on
`users.email`, the other half of this finding, was safe and is applied — see `models/db.js`.)
Proposed change: once the product decides the delete behaviour, issue `PRAGMA foreign_keys = ON` at
connection start and, if cascading is chosen, add the corresponding `ON DELETE` clause to the
`enrollments`/`payments` foreign keys; verify with a dedicated security-entry replay before applying.

## Verification Coverage
Full. Both replay passes ran to completion (contract entries + the destructive entry on its own fresh
boot, each pass). The re-audit ran two passes as the bounded fix loop allows (D23): pass 1 found two
items beyond the frozen Phase 2 list — one `missed-in-phase-2` (AP-01: the seed user's password was
inserted as the plain literal `"123"`, src/AppManager.js:18 original — Phase 2 caught the config
secrets but missed this literal) and one `introduced` (AP-17-shaped: `models/money.js` exported
`toCents` but nothing called it, dead code left behind by the refactor itself). Both were fixed
(seed password now hashed via `models/password.js`; the seed now calls `toCents` instead of hardcoded
cent literals), the mandatory full replay was re-run, and pass 2 confirmed both fixes and found
nothing new. AP-14's Layer 1 (forced `--pending-deprecation --trace-deprecation`) was re-run against
the refactored code (Execution Log row 19) — 0 warnings, same as Phase 2. AP-14 Layer 2 and AP-19 were
not re-queried against OSV.dev/the npm registry a second time: the dependency set and resolved versions
are unchanged from Phase 2 (no upgrade was applied — see `04-architecture-guidelines.md` §6, dependency
upgrades — none were proposed either, since none of the 17 findings concerned a vulnerable or
deprecated dependency), so Phase 2's same-day evidence still holds; this reuse is noted here rather
than left silent.
================================
