## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        .worktrees/p2/ecommerce-api-legacy
Language:      JavaScript (Node.js v24.12.0 on the host; the run uses the official node:24.12.0 image)
Framework:     Express 4.22.1 (resolved from package-lock.json; manifest range ^4.18.2)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6 (resolved 5.1.7); no dev dependencies
Domain:        LMS API with course checkout: users, courses, enrollments, payments, audit log, financial report
Architecture:  None — a single class (persistence, schema/seed, business rules, routes) plus a "utils" bin; no real layers
Source files:  3 files analyzed (~180 lines). Excluded: node_modules, .claude/ (tool/agent config, includes this skill), reports/ (audit output), package-lock.json, api.http, README.md (not authored source)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite in-memory, DDL + seed inside the class)
Boot:          node src/app.js   (package.json "start": "node src/app.js"; same runtime invocation)
Port:          3000 (literal in src/utils.js config; no override exists in code -> native port, container mode)
Runtime env:   Node 24.12.0 from the official image; declared dependencies installed with npm ci from package-lock.json inside the run copy
Isolation:     container (docker 28.5.2, image node:24.12.0)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express 4.22.1 + sqlite3 5.1.7
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-08 15:01
Mode:    full (live lookups via npm registry and npm audit; OSV.dev not queried — see Verification Coverage)
Confirmation: --yes (auto-approved, no human review)
Scope applied: all severities (default)
Tree:    uncommitted changes present — the audit read the working tree as found (the skill files in the worktree and the target's .claude/ copy were uncommitted; the application source was unmodified)
Runtime: installed the declared dependencies with npm ci from package-lock.json inside a run copy (container /app), outside the target
Isolation: container (docker 28.5.2, image node:24.12.0)
Scratch: environment scratch directory (outside the target)

The Phase 2 findings below are the audit as it stood at the gate (identical to audit-20261008-1501.md). The Phase 3 sections follow at the end.

## Summary
CRITICAL: 5 | HIGH: 9 | MEDIUM: 2 | LOW: 5

## Findings

### [CRITICAL] God Module / God Class   (AP-03)
File: src/AppManager.js:1-141
Description: One class holds persistence (sqlite handle opened in the constructor, lines 5-8; every query), schema and seed data (10-23), business rules (payment approval, user creation, report assembly, 43-76 and 80-129) and delivery (route registration and request parsing, 25-137) for three unrelated domain concepts (checkout, financial reporting, user removal). Under the AP-03/AP-05 precedence rule the mixed handlers are filed here and not as AP-05.
Impact: Nothing can be instantiated or tested without a database and an Express app; every change touches one file that every request passes through.
Recommendation: Split by responsibility into config, models (database, repositories, rules), controllers and routes; see RP-03 and RP-05.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: src/AppManager.js:45-45
Description: The checkout logs the whole card number and the payment gateway key (a live-looking literal) on every purchase: console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`). Escalated to CRITICAL: payment data and a credential written to a log.
Impact: Card numbers and the gateway key leak to every log sink and outlive the request.
Recommendation: Stop logging the card and the key; log only a non-sensitive event; see RP-08.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — privileged report   (AP-04)
File: src/AppManager.js:80-129
Description: GET /api/admin/financial-report returns every course with revenue and every student's name and amount paid, to any anonymous caller. It sits under an admin namespace and aggregates across all principals, so it is a privileged operation (guidelines section 6) even though the application has no identity model.
Impact: Anyone reaching the port reads the whole company's revenue and customer list.
Recommendation: Guard it with an operator credential read from configuration, closed by default (403 when unset); see RP-04.
Contract: safe (privileged operation: only non-operators observe the 403)

### [CRITICAL] Missing or Bypassable Authorization — privileged account deletion   (AP-04)
File: src/AppManager.js:131-137
Description: DELETE /api/users/:id deletes any user by id on an anonymous caller's say-so, with no ownership notion; the answer even admits it leaves enrollments and payments dangling. Privileged operation (deletes accounts with no ownership notion).
Impact: Any caller can delete any account, destroying data and orphaning paid enrollments, with no trace.
Recommendation: Guard it with the same operator credential, closed by default; see RP-04.
Contract: safe (privileged operation)

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: src/utils.js:1-7
Description: The config object holds string literals for a database user and password (dbUser, dbPass), a payment gateway key (paymentGatewayKey, a pk_live_ value) and a mail user (smtpUser), plus the port, all in source.
Impact: Anyone with the repository holds the credentials; rotating them needs a code change and deploy, and history keeps them.
Recommendation: Read every value from the environment in a single config module that fails loudly when required values are missing; add an example file; rotate the exposed values (only the owner can); see RP-01.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: src/AppManager.js:4-8
Description: The constructor opens its own database handle (new sqlite3.Database(':memory:')), configuration is read from the utils module at the point of use (line 45), and src/app.js:8-10 instantiates and wires everything at module load with no factory or composition root.
Impact: No unit can receive a test double; the app cannot be constructed twice in a process.
Recommendation: Inject the database and configuration through a createApp factory used as the composition root; see RP-06.
Contract: safe

### [HIGH] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-15
Description: users.email is the lookup identity (line 40 selects one user by it) but has no uniqueness constraint, so two concurrent first checkouts of one email can insert two users (check-then-insert, lines 40-69); enrollments.user_id and course_id and payments.enrollment_id are joined on but declare no foreign keys, and deleting a user (line 131-137) leaves their enrollments and payments orphaned; money (courses.price, payments.amount) is stored as REAL (binary floating point). Escalated to HIGH: identity can be duplicated and orphans are created today.
Impact: A login-name collision picks the wrong account; orphaned payments point at nobody; sums can drift by fractions of a cent.
Recommendation: Add UNIQUE on users.email and store money as integer minor units, keeping the decimal number at the boundary; the delete behaviour toward children (refuse, cascade, detach) is a product decision and is proposed with the count of orphans; see RP-19.
Contract: contract-changing for the foreign-key / delete rule (deleting a user that has enrollments would be refused, cascaded or detached; today it succeeds and orphans); the unique constraint and the money storage are safe

### [HIGH] Hardcoded Secrets and Credentials — seeded accounts   (AP-01)
File: src/AppManager.js:18-18
Description: The seed script inserts a user with the literal plaintext password '123' into the runtime datastore on every boot; line 68 also gives every user created without a password the default password "123456" (via the weak hash). Severity reported at HIGH instead of the CRITICAL default: no endpoint reads the password column back, so the account cannot currently be used to sign in (the plaintext storage is also AP-08).
Impact: A known credential exists in every environment; once any sign-in is added it is a working back door.
Recommendation: Seed the sample user with a random unusable secret hashed with the real KDF and generate the default password for password-less users the same way; see RP-01 and RP-08.
Contract: safe

### [HIGH] Missing Boundary Validation   (AP-11)
File: src/AppManager.js:29-35
Description: The checkout only tests that usr, eml, c_id and card are truthy; it never checks types. A card that is not a string reaches cc.startsWith (line 46) inside a database callback and throws an uncaught TypeError. Severity raised from the MEDIUM default to HIGH: one anonymous request terminates the whole process (verified by sending it in the baseline run).
Impact: Any caller can take the service down with one request; malformed input is a crash, not a client error.
Recommendation: Validate the types of usr, eml, pwd, c_id and card at the boundary and answer 400 with the existing message; see RP-11.
Contract: safe (a value of the wrong type is invalid on its face; no legitimate client sends it)

### [HIGH] Missing or Bypassable Authorization — checkout ignores the password   (AP-04)
File: src/AppManager.js:40-75
Description: The checkout looks up the user by email and, when it exists, enrolls and charges under that account without ever checking the supplied pwd (it is only used when creating a user). Reported at HIGH rather than CRITICAL: the purchase flow is public by design and the caller pays with their own card; the effect is attributing an enrollment to someone else's account.
Impact: Anyone who knows an email can add enrollments and payments to that account.
Recommendation: Verify the password of an existing account, which needs an identity model and a product decision on existing seed users; see RP-04.
Contract: contract-changing: clients that today send a wrong or empty pwd for an existing email would now be rejected
Note: this is a business operation in an application with no identity model, so it stays under the legitimate-use test's first row.

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: src/AppManager.js:57-62
Description: The audit-log insert callback ignores its error and answers 200 success; the user delete (133-136) ignores its error and always answers that the user was deleted; the report callbacks (92-94, 104-106) dereference results without checking err, so a database error throws inside a callback and crashes the process; the error-to-response mapping (res.status(500).send("Erro ...")) is repeated per call site (41, 51, 55, 69) and no error middleware exists.
Impact: Failures are reported as success or kill the process; diagnosis is impossible.
Recommendation: A domain error taxonomy and one error boundary with preserved status codes and message bodies; see RP-09.
Contract: safe (the intentional error statuses and bodies are kept)

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: src/app.js:5-6
Description: No error handler is registered, so the framework's default one answers. Observed on the original: POST /api/checkout with a truncated JSON body answers 400 text/html containing the stack trace with server file paths (for example /app/node_modules/body-parser/lib/types/json.js:92:19); the X-Powered-By: Express header is also sent.
Impact: Internals are mapped for an attacker on every malformed request.
Recommendation: Register the centralized error boundary (status preserved), disable the X-Powered-By header; see RP-17 and RP-09.
Contract: safe (the framework default page is not part of the error contract)

### [HIGH] Mutable Global State   (AP-07)
File: src/utils.js:9-15
Description: A module-level globalCache object is mutated by logAndCache on every successful checkout (called at AppManager.js:59), grows without bound, is never read anywhere and is lost on restart; it is exported and shared by importers (unbounded accumulator, AP-13, is reported here).
Impact: Memory grows with traffic until the process is restarted; the data is not a store of record and nothing consumes it.
Recommendation: Remove the write-only cache (or bound it and inject it) and the module-level state; see RP-07.
Contract: safe

### [HIGH] Unsafe Handling of Credentials and Sensitive Data — weak password hash   (AP-08)
File: src/utils.js:17-23
Description: badCrypto builds the "hash" from the first two base64 characters of the password repeated and cut to 10 characters, after a 10000-iteration string loop; every password with the same first one or two characters yields the same value, no salt, no work factor, and the loop burns CPU for each new user. Kept at HIGH: the value is a lossy encoding of the prefix, not the full password, and no sign-in reads it.
Impact: Stored passwords are trivially collided or guessed; the hashing cost is wasted CPU, not security.
Recommendation: Use a purpose-built password KDF with a per-credential salt (the runtime's built-in scrypt); see RP-08.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency — express runtime chain   (AP-19)
File: package.json:10-10
Description: npm audit (npm registry advisories, 2026-10-08, Tier B) reports advisories on the resolved runtime chain of express 4.22.1: body-parser < 1.20.6 (GHSA-v422-hmwv-36x6, invalid limit option), path-to-regexp < 0.1.13 (GHSA-37ch-88jc-xwx2, multiple route parameters), proxy-addr (GHSA-jqcg-44mw-7w3h, critical, trust-proxy subnet), qs (GHSA-q8mj-m7cp-5q26, GHSA-x5fp-wj9c-mxmx, GHSA-4mjr-xmp4-gh2g). Reported at MEDIUM: the vulnerable features are not used (no body-parser limit option, routes carry a single parameter, no trust proxy setting); the qs advisories are moderate.
Impact: Published, scannable advisories on the shipped versions.
Recommendation: Update the lockfile within the same major (npm audit fix resolves it per the audit); see RP-18.
Contract: safe (same major, lockfile only)

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: src/AppManager.js:83-127
Description: The financial report reads every course, then per course the enrollments, then per enrollment a user query and a payment query, all inside nested loops (callbacks), and reads whole tables with SELECT * and no bound.
Impact: Round trips grow with data volume (courses + enrollments x 2) and the report latency degrades in production.
Recommendation: Replace with set-based joined queries, preserving the response shape; see RP-10.
Contract: safe

### [LOW] Deprecated or End-of-Life API Usage — install-time dependency chain   (AP-14)
File: package.json:11-11
Description: Installing the resolved tree prints registry deprecation notices (npm registry metadata, 2026-10-08, Tier B) for transitive packages pulled in by sqlite3 5.1.7: npmlog@6.0.2, are-we-there-yet@3.0.1, gauge@4.0.4 ("no longer supported"), rimraf@3.0.2, glob@7.2.3, inflight@1.0.6 (upstream names lru-cache), @npmcli/move-file@1.1.2 (upstream names @npmcli/fs), prebuild-install@7.1.3 ("no longer maintained"). The sqlite3 releases page (https://github.com/TryGhost/node-sqlite3/releases, 2026-10-08, Tier C) lists "Mark repository as unmaintained" and v6.0.0 "Bump all dependencies, SQLite, and modernise CI". No runtime deprecation warning was emitted by Node (--pending-deprecation --trace-deprecation, Tier A: none observed over boot and the exercised surface). For the packages without a named successor: no successor named upstream (npm registry, 2026-10-08).
Impact: Unmaintained packages receive no fixes; they run at install time only.
Recommendation: Move to the sqlite3 release that drops this chain (6.0.1, evaluated with AP-19 below), evaluating maintained alternatives if the repository stays unmaintained; see RP-14.
Contract: safe (same API through the replay; applied only if the full replay passes)

### [LOW] Known-Vulnerable Dependency — install-time chain of sqlite3   (AP-19)
File: package.json:11-11
Description: npm audit (2026-10-08, Tier B) reports advisories on tar <= 7.5.20 (critical, several GHSA ids such as GHSA-34x7-hfp2-rc4v), @tootallnate/once, http-proxy-agent, make-fetch-happen, cacache, node-gyp, brace-expansion, http-cache-semantics and ip-address, all reached through sqlite3 5.1.7's install and build tooling and never loaded at run time. Reported at LOW: install/build-time only. tar@6.2.1 is also deprecated (AP-14, reported there).
Impact: Risk is confined to the machine that installs the package.
Recommendation: The audit's fix is sqlite3 6.0.1, a major upgrade whose release notes (2026-10-08) announce no behaviour change; apply it only if the full replay passes, otherwise propose it; see RP-18.
Contract: safe if the replay passes (major upgrade)

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: src/AppManager.js:2-2
Description: totalRevenue is imported here and never used, and in utils.js:10 it is a let that is never assigned or read; dbUser, dbPass and smtpUser (utils.js:2-5) are never read; globalCache is exported and never read by any importer.
Impact: Noise that suggests features (a revenue total, a mailer, a database login) that do not exist.
Recommendation: Delete the unused names; see RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: src/AppManager.js:29-33
Description: Single-letter or cryptic locals (u, e, p, cid, cc) live across the 50-line checkout handler; badCrypto is neither crypto nor named for what it does; AppManager is a manager bin; logAndCache does two things; identifiers are English while responses are Portuguese. The request field names (usr, eml, pwd, c_id) are the public contract and stay.
Impact: Readers must open the code to learn what each name means.
Recommendation: Rename internals for intent; see RP-16.
Contract: safe for internals only (request field names untouched)

### [LOW] Magic Values   (AP-15)
File: src/AppManager.js:46-48
Description: The payment decision is a bare test of the first card digit "4" with the status strings "PAID" and "DENIED" repeated as literals (46-48, 21), plus the hash length 10000/10/2 (utils.js:19-22), the default password "123456" (line 68), the cache key prefix and the port 3000.
Impact: The meaning of the numbers and whether the strings agree across files is held in memory only.
Recommendation: Named constants (a payment status enumeration, the card-approval prefix, hash parameters); see RP-15.
Contract: safe

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-named identifiers with literals; seed/bootstrap credential data in INSERTs; URL with inline credentials; high-entropy / prefixed literals; session-signing key literal; committed credential files; default fallbacks that are working credentials | 2 findings: utils config (CRITICAL), seed and default passwords (HIGH) |
| AP-02 | external input into driver calls by concatenation/interpolation (all queries use ? placeholders; the template string at AppManager.js:57 is passed as a bound parameter); ORM raw escapes (none); dynamic identifiers (none); shell/process execution (none); unsafe deserialization/templating (none); path traversal (none) | none |
| AP-03 | >=3 responsibility categories in one module; size >300 with 2 categories; unit >50 lines or deep nesting; several unrelated domain concepts in one file; low-cohesion class; utils/manager bin; high afferent coupling | 1 finding: AppManager.js (utils.js is covered under AP-07/08 and AP-17) |
| AP-04 | entries without auth/ownership checks; lookups filtered only by input id; check only on one door; role from the request; unverified tokens; unreachable guards; commented-out guards; privileged operations unguarded | 3 findings: report, delete (privileged), checkout password |
| AP-05 | domain decisions in handlers; driver calls in handlers; handlers >30 lines; request objects deep in the stack; duplicated rule across handlers; pass-through service | none separately (module filed as AP-03 by the precedence rule) |
| AP-06 | collaborators built inside units; import-time side effects; no single wiring place; no seam for doubles; domain importing concrete drivers; config read at point of use | 1 finding |
| AP-07 | reassigned module state; request-scoped data stored globally; in-memory store of record; mutable defaults/shared attributes; cache without lifecycle; monkey-patching; process-memory counters | 1 finding |
| AP-08 | reversible password storage; fast digest; shared/constant salt; non-constant-time comparison; sensitive values logged; whole record serialized; TLS verification off; token expiry | 2 findings: card/key logged, weak hash |
| AP-09 | empty/log-and-continue catches; over-broad catches; repeated error mapping; no central handler (default handler observed); stack traces in bodies; inconsistent return conventions; partial multi-write without transaction; exceptions as control flow | 1 finding (stack-trace leak is AP-18) |
| AP-10 | driver call in loop or in a function called from a loop; per-element related fetch; lazy relation in iteration; repeated reads set-based query would replace; remote call in loop; whole table read in memory; write loop | 1 finding |
| AP-11 | input used without type/range check; optional input dereferenced; unconstrained pagination; numeric parse without failure path; validation on one door only; validation after side effect; unenforced invariants; no body size bound (default body limit applies); ad-hoc scattered validation | 1 finding |
| AP-12 | structurally identical blocks >=10 lines; same rule in two places; repeated validation/serialization; hand-written mappings; copy-modify lineage; repeated constants; repeated guard | none (the two completion blocks of the report are under 10 lines) |
| AP-13 | paired acquire/release; handles without release on failure; connection per call; calls without timeout (no outbound calls exist); retries; unbounded reads; unbounded accumulators (reported under AP-07); background tasks without shutdown; recursion | none separately |
| AP-14 | forced detectors (--pending-deprecation --trace-deprecation) over boot, seed (run at boot) and every non-destructive surface entry: no warning emitted; deprecated dependencies in installed metadata; superseded constructs | 1 finding (install-time chain, LOW) |
| AP-15 | unexplained numerics; unitless durations; repeated enumerated strings; repeated literals; numeric codes; positional indexes; inline environment-specific literals | 1 finding |
| AP-16 | names contradicting behaviour; non-descriptive identifiers; several names for one concept; how-names; mixed casing; mixed human languages; stale comments; boolean parameters | 1 finding |
| AP-17 | commented-out code; unreachable branches; unreferenced units; unused imports and declared dependencies; unused parameters/values; constant flags; unregistered endpoints; *_old/backup copies | 1 finding |
| AP-18 | debug/reload literals (none); dev server as production (plain Node server, nothing declared); all-interface bind with debug (none); error output exposing internals (observed); permissive CORS (none configured); unrestricted diagnostic surfaces (admin report under AP-04); disabled protective defaults | 1 finding |
| AP-19 | npm audit over the resolved tree, direct and transitive; lockfile pins vs ranges (lockfile present); lockless ranges (n/a) | 2 findings |
| AP-20 | identity columns without unique constraint; reference columns without foreign key; parent delete with no child rule; money as binary floating point; nullable required columns / free-text closed sets | 1 finding |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Node runtime APIs | node 24.12.0 | deprecation (forced detectors) | A | runtime warnings over boot, seed and 9 surface entries | n/a — local | no issue found |
| express | 4.22.1 | deprecation | B | npm view express@4.22.1 deprecated (empty) | 2026-10-08 | no issue found |
| sqlite3 | 5.1.7 | deprecation | B | npm view sqlite3@5.1.7 deprecated (empty) | 2026-10-08 | no issue found |
| sqlite3 | 5.1.7 | maintenance status | C | https://github.com/TryGhost/node-sqlite3/releases | 2026-10-08 | AP-14 finding |
| npmlog, are-we-there-yet, gauge, rimraf, glob, inflight, @npmcli/move-file, prebuild-install, tar | as resolved | deprecation | B | npm registry notices at install | 2026-10-08 | AP-14 finding |
| express chain (body-parser, path-to-regexp, proxy-addr, qs) | as resolved | advisory | B | npm audit (GitHub advisory database) | 2026-10-08 | AP-19 finding (MEDIUM) |
| sqlite3 install chain (tar, node-gyp, cacache, ...) | as resolved | advisory | B | npm audit | 2026-10-08 | AP-19 finding (LOW) |
| express (after refactor) | 4.22.3 (lockfile) | advisory | B | npm audit on the refactored lockfile | 2026-10-08 | express chain clean; 7 advisories remain, all in the sqlite3 5.x install chain |
| sqlite3 6.0.1 (attempted) | 6.0.1 | replay | n/a | refactored copy booted in node:24.12.0 | 2026-10-08 | does not boot: native binding needs GLIBC_2.38, the image has 2.36 — reverted, proposed |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | ...-20261008-1501-1 | docker run -d ... sleep infinity (run-1); npm ci; exec -d node --pending-deprecation --trace-deprecation src/app.js | ready on port 3000 |
| 2 | 2 | stop | container | ...-1 | docker rm -f ...-1 | removed |
| 3 | 3a | start/stop | container | ...-2 | original baseline, non-destructive entries (run-2) | captured 9; removed by name |
| 4 | 3a | start/stop | container | ...-3 | original baseline, delete-api-users-1 alone (run-3) | captured; removed by name |
| 5 | 3a | start/stop | container | ...-4 | original baseline, sec-delete-api-users-1-anonymous alone (run-4) | captured; removed by name |
| 6 | 3a | start/stop | container | ...-5 | original baseline, sec-post-api-checkout-card-wrong-type alone (run-5): the original crashed (transport error, recorded as baseline) | captured; removed by name |
| 7 | 3b | start/stop | container | ...-6 | manifest tool only: npm install/update --package-lock-only against the target manifest, no application run, no node_modules created | lockfile regenerated; removed by name |
| 8 | 3c | start/stop | container | ...-7, -8, -9, -10 | first replay with sqlite3 6.0.1 | application did not boot (GLIBC_2.38); removed by name |
| 9 | 3b | start/stop | container | ...-11 | manifest tool only: lockfile regenerated after the sqlite3 revert | removed by name |
| 10 | 3c | start/stop | container | ...-12 to -15 | replay 1 of the refactored application (refactored-5..8), 4 boots | compared; removed by name |
| 11 | 3d | start/stop | container | ...-16 to -19 | replay 2 after the post-re-audit fixes (refactored-9..12), 4 boots | compared; removed by name |

19 containers started (including the two manifest-tool ones and four that failed to boot), 19 removed by their exact name; `docker ps -a --filter label=refactor-arch.run=20261008-1501` returned nothing at the end. The snapshot directory was deleted after the second re-audit.

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - OSV.dev query: not used; the ecosystem's own audit tool (npm audit) was used instead (catalog AP-19 allows it) → advisories only as listed by that tool.
  - Layer 1 over the destructive and crash entries (DELETE /api/users/1, anonymous DELETE, non-string card): not exercised with the detectors on → deprecation warnings on those paths unverified.
  - Layer 2 language-level documentation lookups (Node 24 / Express 4 changelogs): not fetched → language-level deprecations without a runtime warning are unverified.
  - Re-audit is full as to the catalog and the local checks, but the Layer 1 deprecation detectors were not re-run on the refactored application → the re-audit is PARTIAL for AP-14 runtime warnings.
Manifest operations (npm install/update --package-lock-only) ran in a container with the target mounted, not in a run copy, because the output is the target's own lockfile. They create no application artifacts.
The test operator token used by the replay (operator-secret-for-validation, in reports/surface.json) is a harness fixture that reaches only the validation run; it is not a deployment credential.
Scratch root: the environment's scratch directory. Excluded from every copy: node_modules, .claude (tool config), VCS directories.
No INCIDENT. No NON-LITERAL command. One non-conforming detail declared: audit-latest.md was written at the end of the run, not at the gate; the gate-time audit is audit-20261008-1501.md.

================================
Total: 21 findings
================================

Confirmation: --yes (auto-approved, no human review)

---

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
├── reports/                      (audit-*.md, audit-latest.md, surface.json, baseline.json, replay.json)
└── src/
    ├── app.js                    composition root (createApp factory + start)
    ├── errors.js                 domain error taxonomy
    ├── config/
    │   └── index.js              environment read once, frozen
    ├── models/
    │   ├── database.js           promise wrapper over the driver
    │   ├── schema.js             DDL, constraints and seed
    │   ├── passwordHasher.js     scrypt KDF
    │   ├── paymentPolicy.js      pure payment rules
    │   ├── userRepository.js
    │   ├── courseRepository.js
    │   ├── enrollmentRepository.js
    │   └── reportRepository.js   one set-based query
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── middlewares/
    │   ├── asyncHandler.js
    │   ├── requireOperator.js    operator guard, closed by default
    │   └── errorBoundary.js      single error boundary
    └── views/
        ├── checkoutRoutes.js
        └── adminRoutes.js        report and user deletion, behind the guard

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 9 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 3 FIXED, 0 NOT FIXED
  ○ Findings resolved: 17/21  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 6 proposed-not-applied, 0 unresolved  (re-audit: 6 findings)
    Re-audit passes: 2; fixed after re-audit: 4 (1 of them missed-in-phase-2)
  ✓ Processes: 19 started, 19 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

## Proposed, Not Applied
### [HIGH] Missing or Bypassable Authorization — checkout ignores the password   (AP-04)
File: src/AppManager.js:40-75 (original; now src/controllers/checkoutController.js)
Reason not applied: verifying the password of an existing account rejects clients that today send a wrong or empty pwd for an existing email; there is no identity model, and the seeded user has no known password.
Proposed change: decide the identity model (who signs in, where passwords are verified), then verify with the scrypt hashes already stored for new accounts.

### [HIGH] Missing Schema-Level Integrity Constraints   (AP-20)
File: src/AppManager.js:12-15 (original; now src/models/schema.js)
Reason not applied: what a user delete does to enrollments and payments (refuse, cascade, detach) changes what the delete route does today (it succeeds and orphans). Applied from this finding: UNIQUE on users.email, money as integer cents with decimals at the boundary (replay PASS). Held back: foreign keys and the delete rule.
Proposed change: pick the rule, add foreign keys and enable PRAGMA foreign_keys; first count the violating rows (enrollments or payments whose user no longer exists).

### [LOW] Deprecated or End-of-Life API Usage — install-time dependency chain   (AP-14)
File: package.json:11-11
Reason not applied: the fix is sqlite3 6.0.1, which was applied and replayed: the application did not boot in the node:24.12.0 image (native binding needs GLIBC_2.38; the image has 2.36). Whoever deploys it would need a newer base image (or the musl build fixed in 6.0.1 on Alpine). Reverted per RP-18 step 4.
Proposed change: upgrade to sqlite3 6.0.1 together with a base image with glibc >= 2.38 and re-run the replay; prebuild-install and the other deprecated build tools are removed with it (to be confirmed after the upgrade).

### [LOW] Known-Vulnerable Dependency — install-time chain of sqlite3   (AP-19)
File: package.json:11-11
Reason not applied: same upgrade as above; the 7 remaining advisories (tar, node-gyp chain and others) are install/build time only.
Proposed change: same as above.

### [MEDIUM] Missing Boundary Validation — format and length of fields   (AP-11, missed-in-phase-2)
File: src/controllers/checkoutController.js:15-22
Reason not applied: email format and field length limits need a product decision and would reject requests clients may send today.
Proposed change: define the allowed formats and maximum lengths and enforce them at the boundary.

### [MEDIUM] Swallowed or Uncentralized Error Handling — failed course lookup reads as "not found"   (AP-09, missed-in-phase-2)
File: src/controllers/checkoutController.js:25-30
Reason not applied: the original answered 404 "Curso não encontrado" when the course query itself failed; answering 500 would change an intentional status. The failure is now logged.
Proposed change: answer 500 "Erro DB" for a failed lookup, separately from "not found".

## Findings detail after the re-audit

First re-audit (10 findings): 6 proposed-not-applied (the four above that were already recorded, plus the two missed-in-phase-2 items) and 4 to fix:
  - introduced: AP-09, the new dependency errors lost their cause (fixed: cause carried and logged at the boundary);
  - introduced: AP-17, unused verifyPassword and close() I had written (removed);
  - introduced: AP-06, the controller and the seed imported the hashing helper directly (injected from the composition root);
  - missed-in-phase-2: AP-20, payments.status was a free-text closed set (CHECK constraint added; safe).
Second re-audit (after the second full replay: 9 PASS, 0 REGRESSION, 3 FIXED): 6 findings, all proposed-not-applied; 0 unresolved. The Phase 2 total stays 21; the missed-in-phase-2 items are counted apart (2 found, 1 fixed after re-audit, 1 plus the AP-11 residual proposed).

## Verification Coverage
Partial for AP-14 runtime warnings in the re-audit (the deprecation detectors were not re-run on the refactored application); everything else as in the Verification Coverage above. Operator path: the replay ran with OPERATOR_TOKEN set and the report and delete entries carrying the header matched the baseline (PASS); wrong token and anonymous answer 403 (verified by hand and by the security entries). Value-level equivalence of the report (cents conversion) was checked by hand: revenue 1994 and 994 for the replayed state; the shape comparison alone would not catch value drift.
================================
