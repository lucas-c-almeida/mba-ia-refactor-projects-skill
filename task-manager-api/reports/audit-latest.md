## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        .worktrees/p3c/task-manager-api  (relative to D:\Study\MBA FullCycle\mba-ia-refactor-projects-skill)
Language:      Python 3.13 (the project declares no Python version; runs on python:3.13-slim, host Python 3.13.2)
Framework:     Flask 3.0.0 (exact pin in requirements.txt; installed metadata agrees) + Flask-SQLAlchemy 3.1.1
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0 (the last three are never imported)
Domain:        Task manager API: tasks (status, priority, due date, tags) assigned to users and grouped by categories, with login and productivity reports
App type:      hybrid: HTTP service (22 routes) + a setup CLI script (seed.py, run before first boot per README)
Architecture:  Nominal layering: models/, routes/, services/, utils/ exist, but route handlers hold persistence, business rules and serialization; services/ and utils/ are never reached by the live code; category CRUD lives in the reports module
Source files:  15 files analyzed (15 .py, ~1158 lines; excluded: .claude/ (skill copy), reports/ (audit output), README.md, requirements.txt, __pycache__/, instance/)
DB tables:     users, categories, tasks (SQLite file via Flask-SQLAlchemy, created by db.create_all() at import time)
Boot:          python app.py  (app.run(debug=True, host='0.0.0.0', port=5000)); setup first: python seed.py
Port:          5000, fixed in source (app.py:34); the code reads no override; container mode uses the native port inside the container
Runtime env:   Python 3.13 from python:3.13-slim; declared dependencies installed inside the run container with pip from requirements.txt (exact pins, no lockfile; transitive resolved at install: Werkzeug 3.1.9, SQLAlchemy 2.1.4, Jinja2 3.1.6, itsdangerous 2.2.0, click 8.5.0, blinker 1.9.0, MarkupSafe 3.0.4, packaging 26.3, urllib3 2.8.0, idna 3.20, certifi 2026.7.22, charset-normalizer 3.5.2, typing-extensions 4.16.0)
Isolation:     container (docker 28.5.2, image python:3.13-slim)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 (+ Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.4 resolved)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-10 14:31
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    task-manager-api sources clean at the worktree HEAD; the only untracked path under the target is the skill's own copy (.claude/), excluded from the audit
Runtime: installed the declared dependencies from requirements.txt into the run container (pip, outside the target)
Isolation: container (docker 28.5.2, image python:3.13-slim)
Scratch: environment scratch directory (C:\Users\lucas\AppData\Local\Temp\claude\D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill\b35825d2-d654-455b-ad56-6dc436b8d6da\scratchpad\refactor-arch-task-manager-api-p3c-20261010-1420\)  (protocol §1.1)

## Summary
CRITICAL: 9 | HIGH: 7 | MEDIUM: 8 | LOW: 6

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:13-13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` assigns a literal signing key in source. Signal: framework session/signing key set to a literal.
Impact: anyone with read access to the repository (or any clone, image layer or history) can forge values signed with this key; rotating it needs a code change and a deploy.
Recommendation: read the key from the environment in a single settings module and never default to a literal; rotate the committed value (it stays in history). See RP-01.
Contract: safe

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:34-34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` sets debug by literal on the path the application starts with and binds every interface. Observed on the original at its native configuration: startup banner `Debug mode: on`, `Debugger is active!`, a Debugger PIN printed to the log, `GET /console` answered 200, and every unhandled exception answered with the debugger's traceback page. Escalated from the HIGH default to CRITICAL: an interactive console is reachable from outside the host.
Impact: code execution by design behind a PIN that is logged at startup; tracebacks disclose source, paths and library versions to any caller who can trigger an error.
Recommendation: debug and bind address from configuration with debug off by default (opt in via environment), and a centralized error boundary instead of the framework's default page. See RP-17, RP-09.
Contract: safe (debug off; same bind address and port; the default error page is not contract, its status is kept)

### [CRITICAL] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:3-3
Description: `flask-cors==4.0.0`. OSV.dev (querybatch + vulns lookup, 2026-10-10) lists, for this exact version: GHSA-hxwh-jpp2-84pm (CVE-2024-6221, rated HIGH, fixed 4.0.2): `Access-Control-Allow-Private-Network` set to true by default; GHSA-84pr-m4jr-85g5 (MODERATE, fixed 4.0.1): log injection at debug log level; GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (MODERATE, path matching, fixed 6.0.0). Escalated to CRITICAL (high advisory, reachable): evidence tier A, observed on the original, a preflight carrying `Access-Control-Request-Private-Network: true` was answered with `access-control-allow-private-network: true` (surface entry `options-tasks-private-network-preflight`), and `CORS(app)` (app.py:15) applies to every route. The first two are closed within the 4.x line (4.0.2); all five need 6.0.0, across a major. No upstream changelog was consulted, so "does the fix need configuration to take effect" is unverified.
Impact: a page on a public origin can reach this API as a private-network resource; the same dependency carries three further advisories until moved to 6.x.
Recommendation: upgrade to the lowest version that closes the advisories (6.0.0), verified with the cross-origin and preflight entries of the surface. See RP-18.
Contract: contract-changing: the fix removes `Access-Control-Allow-Private-Network` from responses that clients receive today (the replay's contract-header comparison would register it, by design), and the 6.x line is a major upgrade; propose with that header named.

### [CRITICAL] God Module / God Class   (AP-03)
File: routes/report_routes.py:1-223
Description: one module holds two unrelated domain concepts: reporting (lines 12-155: aggregate queries, the overdue rule, per-user roll-ups, response assembly) and category CRUD (lines 157-223, routes `/categories`), and mixes persistence (ORM queries in every handler), business rules, delivery and serialization. The file is named for reports but registers the category routes. 223 lines is below the size threshold; the finding rests on the "several unrelated domain concepts" signal. Catalog default severity kept.
Impact: nothing in it is testable without a server and a database; a change to category handling shares a blast radius with the reports; the name hides where the category routes live.
Recommendation: split by concept: category repository/controller/routes, report controller/routes; keep registered paths unchanged. See RP-03.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/report_routes.py:12-101
Description: `GET /reports/summary` returns `user_productivity` (lines 53-68, 98): for every user, id, name, total and completed tasks and completion rate. By content this is a management aggregate (D27: a per-principal roll-up that names principals; guidelines §6, "returns a management aggregate"), reachable with no credential. The application has no identity model: the only token is `'fake-jwt-token-' + str(user.id)` (user_routes.py:210), and no operation verifies a presented credential.
Impact: any anonymous caller enumerates every user and their workload and performance.
Recommendation: guard the operation with an operator credential read from configuration, compared in constant time, closed by default; the response shape for operators is unchanged. See RP-04.
Contract: safe (privileged operation, guidelines §6: no legitimate anonymous caller)

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/user_routes.py:42-90
Description: business operations with no identity model. No operation verifies a credential. The role of a new account is taken from the request body (`role = data.get('role', 'user')`, line 52, applied at 71-78), so any caller can create an `admin`; `PUT /users/<id>` rewrites name, email, password, role and active for any id (lines 92-132); tasks and categories are created, edited and deleted anonymously (task_routes.py:85-238, report_routes.py:167-223); accounts are listed (`GET /users`, 10-25) and looked up anonymously; `POST /login` issues a token that nothing reads back (207-211). Classified per guidelines §6: ordinary domain-record changes and deletes, plain listings and lookups (account listing included), sign-in and registration are business operations; `GET /tasks/stats` and `GET /categories` are plain counts by state; `GET /reports/user/<id>` and `PUT /users/<id>` are ambiguous (see Verification Coverage) and are treated as business operations.
Impact: horizontal and vertical escalation: any caller reads or changes any record, promotes itself to admin, or deactivates accounts.
Recommendation: introduce an identity model (verified credential, principals, ownership and role policy) and enforce it on the operations. See RP-04.
Contract: contract-changing: every current client sends no credential, so all of them would receive 401/403; the policy needs a product decision.

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/user_routes.py:134-151
Description: `DELETE /users/<id>` deletes an account and, in the same transaction, every task assigned to it (lines 140-145) by the id in the URL. No operation verifies a presented credential (finding above), so there is no "caller's own account": by guidelines §6 this is a privileged operation ("deletes or deactivates an account by an identifier taken from the request, in an application with no identity model").
Impact: any anonymous caller can remove any account and its tasks.
Recommendation: guard with the same operator credential, closed by default. See RP-04.
Contract: safe (privileged operation)

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: seed.py:19-33
Description: the setup script that the README tells every operator to run before first boot creates three accounts with literal passwords (`set_password('1234')` line 19, `'abcd'` line 26, `'pass'` line 33), one of them `role = 'admin'` (line 20). The script writes into the runtime datastore, so these are real accounts with known passwords in every environment that runs it.
Impact: a known admin login in every deployment that follows the README.
Recommendation: read the seed password from the environment (fail loudly when absent) instead of literals; never seed a privileged account with a fixed password. See RP-01.
Contract: safe

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: services/notification_service.py:7-10
Description: `self.email_user = 'taskmanager@gmail.com'` and `self.email_password = 'senha123'` hold an SMTP credential for a third-party mail host (`smtp.gmail.com`, line 7). Signal: literal assigned to an identifier matching `password`, plus a connection to a third-party system. The module is also dead code (AP-17 note: nothing imports it).
Impact: the credential is in the repository and its history regardless of whether the module runs.
Recommendation: delete the dead module (its only effect is the leaked credential) and rotate the mailbox password; if mail is ever needed, read the credential from configuration. See RP-01, RP-16.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: app.py:9-31
Description: the Flask app, its configuration (literals at lines 11-13), CORS, `db.init_app` and blueprint registration are built at module top level, and `db.create_all()` runs inside an app context at import time (lines 30-31): merely importing `app` (as seed.py:2 does) creates and opens the database file. No factory and no single place that assembles the object graph; routes import the global `db` and the models directly. Catalog default HIGH kept: the side effect is a local SQLite file, not live infrastructure.
Impact: nothing can be constructed twice or tested without touching the filesystem; startup order is implicit.
Recommendation: an application factory as the composition root that loads configuration, wires repositories and controllers, registers routes and the error boundary. See RP-06.
Contract: safe

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: app.py:34-34
Description: the entry point starts the framework's development server (`app.run`, with the startup warning "This is a development server" observed in the log) and no production server is declared anywhere (no process file, container command or alternative in the README).
Impact: the development server is single-purpose tooling, not built for production load or hardening.
Recommendation: declare and use a production WSGI server (the command that would run it must be named by the team). See RP-17.
Contract: contract-changing: needs a runtime dependency the application does not have today; propose with the command, apply nothing.

### [HIGH] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models/user.py:16-25
Description: `User.to_dict()` serializes the whole record, including `'password': self.password` (line 21): the stored hash is returned by `GET /users/<id>`, `POST /users`, `PUT /users/<id>` and `POST /login` (user_routes.py:33, 85, 129, 209).
Impact: every anonymous reader of these routes obtains password hashes, which for MD5 (next finding) are cheap to crack.
Recommendation: mask the hash value in responses, keeping the field and its type. See RP-08.
Contract: safe (masking a leaked secret while keeping field and type; guidelines §6)

### [HIGH] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models/user.py:27-32
Description: passwords are stored as an unsalted MD5 digest (`hashlib.md5(pwd.encode()).hexdigest()`, lines 29 and 32) and checked with `==` (not constant-time). Signal: fast general-purpose digest, no salt. Catalog default HIGH kept (a digest, not a recoverable store).
Impact: a single read of the users table lets an attacker recover short passwords (the minimum length is 4) with precomputed tables.
Recommendation: a purpose-built password KDF with per-credential salt and constant-time comparison, with upgrade-on-login for existing digests (no flag day). See RP-08.
Contract: safe

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: routes/task_routes.py:11-299
Description: every handler parses input, applies domain rules (status set and priority range at 110-114 and 177-184, title length, the overdue rule at 30-39, 71-80 and 284-287, completion rate 296), issues ORM queries directly (`Task.query`, `db.session`) and builds response dictionaries by hand (18-28, 59). One domain concept (tasks) and 299 lines, so AP-05 under the AP-03/AP-05 precedence rule, not AP-03 (borderline against the ~300 line threshold; the unrelated-concepts signal is absent).
Impact: the rules cannot be tested without a web server; a second entry point would copy them.
Recommendation: controller per use case, repository for persistence, serializer in the delivery layer; handlers reduce to parse, call, render. See RP-05.
Contract: safe

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: routes/task_routes.py:62-63
Description: no error handler is registered anywhere; each handler repeats its own `try`/`commit`/`rollback`/`return 500` shape with different messages (task_routes.py:146-154, 217-223, 231-238; user_routes.py:80-90, 127-132, 144-151; report_routes.py:182-188, 204-223), bare `except:` blocks absorb everything, including programming errors (task_routes.py:62-63 returns a generic 500 for any failure in the list handler; 137, 204, 236), failures are `print`ed rather than logged, and a request that makes a handler raise is answered by the framework's default page: observed on the original, `POST /tasks` with a non-numeric priority, `PUT /categories/1` with a JSON `null` body and others answered 500 with the interactive traceback page.
Impact: callers cannot tell a bad request from a server fault; internals leak through the default page; the same mapping is maintained in a dozen places.
Recommendation: a domain error taxonomy and one error boundary that keeps the current status codes and body shapes for the errors the application raises on purpose. See RP-09.
Contract: safe (the application's own error statuses and bodies are preserved; only the framework default page is replaced, keeping its status)

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: routes/user_routes.py:10-211
Description: handlers hold rules (email pattern at 61 and 106, role set at 71 and 120, password length at 64 and 115, cascade removal of a user's tasks at 140-142), ORM queries (`User.query`, `Task.query`, `db.session`) and hand-built response dictionaries (15-23, 162-169, 207-211). One domain concept (users and sign-in), 211 lines: AP-05.
Impact: same as the tasks module: rules untestable without a server, duplicated, and coupled to the transport.
Recommendation: user controller + repository; keep the registered routes and bodies identical. See RP-05.
Contract: safe

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: models/task.py:13-14
Description: `tasks.user_id` and `tasks.category_id` declare ORM foreign keys, but SQLite does not enforce foreign keys unless switched on per connection and nothing does, so the declarations count as absent. `DELETE /categories/<id>` (report_routes.py:211-223) removes the parent and leaves its tasks pointing at nothing (orphans); `status` (line 11) and `priority` (line 12) are free values with the closed sets enforced only in handlers. `users.email` is correctly unique (models/user.py:10).
Impact: orphaned tasks show `category_name: null` forever; any second writer can store an invalid status or priority.
Recommendation: decide the delete rule for categories (refuse, detach, cascade), enable foreign-key enforcement and add check constraints through a migration, after counting the rows that would violate them. See RP-19.
Contract: contract-changing: choosing what a category delete does to its tasks changes what that route does today, and the constraints may reject existing rows.

### [MEDIUM] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:4-6
Description: three declared dependencies carry advisories for their pinned versions (OSV.dev, 2026-10-10) and none is imported anywhere in the source: `marshmallow==3.20.1` (GHSA-428g-f7cq-pgp5, MODERATE, DoS in `Schema.load(many=True)`, fixed 3.26.2); `requests==2.31.0` (GHSA-9wx4-h78v-vm56 MODERATE fixed 2.32.0, GHSA-9hjg-9r4m-mvj7 MODERATE fixed 2.32.4, GHSA-gc5v-m9x4-r6x2 MODERATE fixed 2.33.0); `python-dotenv==1.0.0` (GHSA-mf9w-mj56-hr94, MODERATE, symlink following in `set_key`, fixed 1.2.2). De-escalated to MEDIUM: the vulnerable code is demonstrably unused (never imported; also AP-17, declared-but-unused dependencies, reported here once). Reachability: none established, none possible without an import.
Impact: installed in every environment and flagged by every scanner for no benefit.
Recommendation: remove the three unused dependencies from the manifest (closes all five advisories without a version change). See RP-18, RP-16.
Contract: safe

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: routes/report_routes.py:173-180
Description: the rules that need a product decision. `POST /categories` accepts any `description` and any `color` (the column is 7 characters wide, nothing checks a `#rrggbb` shape or any length); `PUT /categories/<id>` and `PUT /users/<id>` accept any `name`; user and task text fields have no maximum length although the columns declare one (user_routes.py:49-65, task_routes.py:166-171); nothing bounds the length of `tags`. Separate from the safe subset of AP-11 (wrong-type values), filed below.
Impact: oversized or malformed values persist; on an engine that enforces column widths they would become server errors.
Recommendation: boundary schema with the maxima and formats the product chooses. See RP-11.
Contract: contract-changing: a maximum or a stricter format would reject requests clients may send today; the values are a product decision.

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: routes/task_routes.py:13-14
Description: `GET /tasks` loads the whole table (`Task.query.all()`) and returns it; `GET /users` (user_routes.py:12), `GET /categories` (report_routes.py:159) and `GET /tasks/search` (task_routes.py:266) do the same, with no limit or pagination. `GET /reports/summary` and `GET /tasks/stats` also read every task into memory (task_routes.py:281, report_routes.py:30). The seed script's own data notes the gap ("Endpoints retornam todos os registros").
Impact: response size and memory grow with the data; one large table makes list endpoints slow for everyone.
Recommendation: paginate lists with a default limit. See RP-13.
Contract: contract-changing: introducing pagination changes what a client that receives the entire collection today would get; propose it, with a default limit and an opt-out left to the team.

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: routes/task_routes.py:16-59
Description: for each task the list handler fetches its user (`User.query.get(t.user_id)`, line 42) and its category (`Category.query.get`, line 51): 1 + 2N queries (observed in the original's log: two `Query.get` calls per task per request). Same pattern: `len(u.tasks)` lazily loads each user's tasks (user_routes.py:22); per-user task queries in the summary report (report_routes.py:55-60); a count query per category (report_routes.py:163). The loop bound is the table size, uncapped. Catalog default MEDIUM kept.
Impact: latency grows linearly with the data and every list request costs hundreds of round trips on a modest dataset.
Recommendation: join/eager-load the related rows, aggregate counts in the datastore with explicit ordering. See RP-10.
Contract: safe (same result, same ordering made explicit)

### [MEDIUM] Duplicated Logic   (AP-12)
File: routes/task_routes.py:30-39
Description: the overdue rule (`due_date < now and status not in done/cancelled`) is written out in six places: task_routes.py:30-39, 71-80, 284-287; user_routes.py:171-180; report_routes.py:34-43 and 132-135; a seventh copy, `Task.is_overdue` (models/task.py:50-60), is never called. The task-to-dictionary mapping is written by hand in task_routes.py:18-28, again in `Task.to_dict` (models/task.py:24-36) and again, with a different field set (no `user_id`, `category_id`, `updated_at`, `tags`), in user_routes.py:162-169. The status set appears at task_routes.py:110 and 177, models/task.py:39 and utils/helpers.py:75 and 110; the email pattern at user_routes.py:61 and 106 and utils/helpers.py:21. The create and update handlers already diverge on the invalid-date message (task_routes.py:138 versus 205). Catalog default MEDIUM kept: the divergence is limited to message text and field subsets.
Impact: every change to the rule must be made seven times.
Recommendation: one overdue rule on the model, one serializer per representation, one definition of the status set, preserving both date-error messages. See RP-12.
Contract: safe

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: routes/task_routes.py:92-114
Description: the safe subset: values that no legitimate client sends because they are the wrong type, which today crash the handler. Observed on the original (answered 500, traceback page): `POST /tasks` with `"priority": "high"` (`priority < 1`, line 113) or `"title": 12345` (`len(title)`, line 96); a JSON array body on `POST /tasks` (`data.get`, line 92); `PUT /tasks/<id>` with `"priority": "x"` (line 182); `GET /tasks/search?priority=abc` (`int(priority)`, line 261; `user_id` at 264 likewise); `POST /users` with a numeric `email` (user_routes.py:61); `PUT /categories/<id>` with a `null` body (report_routes.py:197). By reading (not observed): the same wrong-type crashes exist for `PUT /users/<id>` (`email` at user_routes.py:106, `password` at 115, `active` at 125 reaching the Boolean column) and for list/object values in text fields. Default MEDIUM kept (the crashes do not reach a datastore).
Impact: malformed input becomes a server error, so operators cannot tell attacks from bugs.
Recommendation: reject, with 400 and a clear message, exactly the requests that crash today (wrong type, non-object body, non-numeric query value), leaving every request that is answered today answered the same way. See RP-11.
Contract: safe (guidelines §6, "a value of the wrong type"; covered by security entries)

### [MEDIUM] Dead Code and Commented-Out Code   (AP-17)
File: utils/helpers.py:1-116
Description: the whole module is dead: its only importer is report_routes.py:7 (`format_date`, `calculate_percentage`), which uses neither; every other member (`validate_email`, `process_task_data`, `parse_date`, `log_action`, the constants block at 110-116 and six unused imports) is referenced nowhere. It is also a second, stale implementation of live validation (`process_task_data`, 57-108, duplicates the task validation with different messages), hence escalated from LOW to MEDIUM. `services/notification_service.py` (48 lines, `NotificationService`) is likewise imported nowhere (reported for its credential above); no dynamic dispatch or registration reaches either (checked: no `importlib`, `__import__`, entry points or string-keyed lookup in the tree).
Impact: a reader may edit the wrong copy of the rules; it is searched, reviewed and carried for nothing.
Recommendation: delete both modules and their package directories. See RP-16.
Contract: safe

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: app.py:7-7
Description: unused imports and unreferenced members: `os, sys, json` (app.py:7), `json, os, sys, time` (task_routes.py:7), `hashlib, json` (user_routes.py:6), `json` (report_routes.py:8, models/task.py:3), `format_date, calculate_percentage` (report_routes.py:7); unused methods `Task.validate_status` and `Task.validate_priority` (models/task.py:38-48), `Task.is_overdue` (50-60, see AP-12), `User.is_admin` (models/user.py:34-38).
Impact: noise that hides the real dependencies of each module.
Recommendation: delete them. See RP-16.
Contract: safe

### [LOW] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:1-1
Description: `flask==3.0.0` (OSV.dev, 2026-10-10): GHSA-68rp-wp8r-4726 (CVE-2026-27205, rated LOW): the `Vary: Cookie` header is not set for some forms of session access; fixed in 3.1.3 (same major). Rated LOW by its source and the application never touches `session` (checked: no use of the session object), so the LOW level stands; applicable only behind a caching proxy.
Impact: low; listed by scanners.
Recommendation: move to 3.1.3, the lowest fixed version on the same major line. See RP-18.
Contract: safe (minor upgrade within the major version; the replay covers headers)

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: routes/report_routes.py:24-28
Description: single-letter and positional names in decision code: `p1`..`p5` (priority counts, lines 24-28, mapped to `critical`..`minimal` at 83-89), `t`, `u`, `c`, `d` loop names across modules; the category routes live in a module named for reports (see AP-03).
Impact: readers must decode names to understand the code.
Recommendation: name by meaning (a priority-to-label map), place the routes in a module that says what they serve. See RP-16.
Contract: safe

### [LOW] Deprecated or End-of-Life API Usage   (AP-14)
File: routes/task_routes.py:31-31
Description: `datetime.datetime.utcnow()`. Tier A, observed: the runtime printed `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)` (Python 3.13, `-X dev`, `PYTHONWARNINGS=always::DeprecationWarning`, 2026-10-10) at routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; seed.py:66, 67, 69, 70, 74; and through column defaults `default=datetime.utcnow` (models/task.py:15-16, models/user.py:14, models/category.py:11, reported by SQLAlchemy's schema.py). Successor named by the warning: `datetime.datetime.now(datetime.UTC)`; the columns store naive datetimes, so the equivalent behaviour keeps them naive (`.replace(tzinfo=None)`), to be confirmed by the replay. Soft-deprecated with a drop-in successor: LOW.
Impact: removal on a schedule the project does not control.
Recommendation: one clock function returning naive UTC through the successor API. See RP-14.
Contract: safe when behaviour is equivalent (naive UTC kept)

### [LOW] Deprecated or End-of-Life API Usage   (AP-14)
File: routes/task_routes.py:42-42
Description: `Query.get()`. Tier A, observed: `LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get() (deprecated since: 2.0)` (SQLAlchemy 2.1.4, same run) at routes/task_routes.py:42, 51, 67, 117, 122, 158, 227; routes/user_routes.py:29, 94, 155; routes/report_routes.py:105, 192, 213 (the same call exists, not reached in this run, at user_routes.py:136 and task_routes.py:188 and 195). Successor named by the warning: `Session.get()`. Legacy with a drop-in successor: LOW.
Impact: the legacy query interface is on a path to removal.
Recommendation: `db.session.get(Model, id)` at every call site. See RP-14.
Contract: safe (same lookup semantics)

### [LOW] Magic Values   (AP-15)
File: routes/task_routes.py:96-114
Description: unexplained literals in decisions: title bounds `3` and `200` (96-100), the status list (110) and priority range `1`..`5` (113), password minimum `4` (user_routes.py:64), role list (71), the `7`-day window (report_routes.py:45), `2` as the high-priority cutoff (report_routes.py:129), `'#000000'` default colour (report_routes.py:180), the database URI `'sqlite:///tasks.db'` (app.py:11).
Impact: the same number must be found and changed in several places.
Recommendation: named constants in one module; the environment-specific URI into configuration. See RP-15, RP-01.
Contract: safe

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | name-pattern literals (app.py, notification_service.py, seed data); credential literals in seed/bootstrap data; URL with inline credentials; high-entropy literals; framework signing key; credential files in the tree (.env, keys: none); working-credential defaults | 3 findings (SECRET_KEY, seed passwords, SMTP credential) |
| AP-02 | external value into driver call by concatenation/formatting (only `like(f'%{query}%')`, task_routes.py:252-253: the value is bound, wildcards only); ORM escape hatches (none); dynamic identifiers (none); shell/process execution (none); unsafe deserialization/templates (none); path traversal (none) | none |
| AP-03 | responsibility mix per module; size threshold (largest 299 lines); unit length/nesting (task_routes create/update handlers ~70 lines, noted under AP-05); several concepts in one file (report_routes.py); grab-bag module (utils/helpers.py, dead, filed AP-17); coupling hub | 1 finding (report_routes.py) |
| AP-04 | unauthenticated principal-scoped entries; IDOR by input id; check on one door only; role from request; unverified token; unreachable guard; disabled guard; privileged operations (arbitrary query/code: none; bulk reset: none; account deletion by id: found; maintenance namespace: none; management aggregate: found) | 3 findings (summary aggregate, business operations, account delete) |
| AP-05 | domain decisions in handlers; persistence in handlers; handlers over ~30 lines; request objects deep in the stack (none); same rule in two handlers; pass-through service layer (services/ is dead) | 2 findings (task_routes.py, user_routes.py) |
| AP-06 | collaborators built inside units; import-time side effects (app.py:30-31); no composition root; real database/clock needed to test (utcnow in rules); concrete types in the domain; configuration at point of use | 1 finding |
| AP-07 | reassigned module-level variables (none); request-scoped data in globals (none); in-memory store of record (only `NotificationService.notifications`, dead); mutable defaults (none); unbounded caches (none); monkey-patching (none); process counters (none) | none (dead class noted under AP-17) |
| AP-08 | reversible password storage; fast digest (MD5, models/user.py:29); constant/missing salt; non-constant-time comparison (line 32); sensitive values logged (none); whole-record serialization (`to_dict`); disabled TLS verification (none); token expiry/revocation (no verified token exists, see AP-04) | 2 findings |
| AP-09 | empty/log-only catch (bare `except:` blocks); over-broad catch; repeated error mapping; no centralized handler (default page observed); internals in responses (debug page); sentinel-style errors; partial writes without a transaction (delete_user is one commit); exceptions as flow control (bare `except` around date parse) | 1 finding |
| AP-10 | query in loop (task_routes.py:42/51, report_routes.py:56/163); lazy relation in iteration (user_routes.py:22); repeated reads; remote calls in loops (none); whole table read to count (task_routes.py:281, report_routes.py:30); write loops (delete_user, one commit) | 1 finding |
| AP-11 | direct use of input; null dereference; unconstrained limit parameters; numeric parsing without failure path (search); validation on one entry only; validation after use; domain invariants; body-size bounds; scattered ad-hoc checks | 2 findings (wrong-type subset; product-decision rules) |
| AP-12 | structurally identical blocks; same rule in several places (overdue ×7); repeated validation/serialization; hand-written mappings with different field sets; diverged copies; repeated constants; repeated guard conditions | 1 finding |
| AP-13 | acquire/release pairs; handles without release on failure (session managed by the extension); connection per call (none); calls without timeout (smtplib in dead code); retries; unbounded reads (list endpoints); unbounded accumulators (none); background tasks (none); unbounded recursion (none) | 1 finding |
| AP-14 | forced detectors on (Python `-X dev`, `PYTHONWARNINGS`); exercised: seed.py, boot, 62 non-destructive surface entries; dependency flagged deprecated in manifest/metadata (none observed); superseded constructs; Layer 2 registry lookup (not run per package; see Verification Coverage) | 2 findings (utcnow, Query.get) |
| AP-15 | numeric literals in decisions; unit-less durations; repeated string enums; repeated literals; numeric codes; tuple offsets; environment-specific literals (DB URI) | 1 finding |
| AP-16 | names contradicting behaviour (`validate_*` that only return booleans: ok); non-descriptive identifiers (p1..p5); inconsistent naming; mixed conventions; mixed human languages (Portuguese messages and English identifiers: consistent, left as is); misplaced files (category routes in report module); stale comments (none) | 1 finding |
| AP-17 | commented-out blocks (none); unreachable branches; unreferenced units (helpers.py, notification_service.py, validate_*, is_admin); unused imports; unused parameters; constant flags (none); unreachable endpoints (none); parallel copies `*_old`/`.bak` (none) | 2 findings |
| AP-18 | debug literal on start path (app.py:34); dev server as production; all-interface bind + debug; error output exposing internals (observed); permissive CORS (`CORS(app)` wildcard origin, no credentials, no cookie authentication: does not meet the signal; not filed); admin/diagnostic surfaces (the debugger console, filed within the first); protective defaults off (none) | 2 findings |
| AP-19 | OSV.dev advisories for 19 resolved packages (6 direct + 13 transitive); transitive packages: no advisory returned; no lockfile with ranges (exact pins: manifest is the lock for direct packages) | 3 findings (flask-cors; three unused packages; flask) |
| AP-20 | identity columns without unique (users.email is unique: ok); FK declarations never enforced (SQLite); parent delete with no child rule (categories); floating-point money (none); nullable-but-required and free-text closed sets (status, priority) | 1 finding |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| `datetime.utcnow()` | Python 3.13 | deprecation | A | runtime DeprecationWarning with stack trace (seed.py and surface run) | n/a — local | AP-14 finding |
| `Query.get()` | SQLAlchemy 2.1.4 | deprecation | A | runtime LegacyAPIWarning with stack trace | n/a — local | AP-14 finding |
| flask | 3.0.0 | advisory | B | OSV.dev GHSA-68rp-wp8r-4726 (LOW) | 2026-10-10 | AP-19 finding (LOW) |
| flask-sqlalchemy | 3.1.1 | advisory | B | OSV.dev querybatch | 2026-10-10 | no issue found |
| flask-cors | 4.0.0 | advisory | A + B | OSV.dev GHSA-hxwh-jpp2-84pm, GHSA-84pr-m4jr-85g5, GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7; reachability observed | 2026-10-10 | AP-19 finding (CRITICAL) |
| marshmallow | 3.20.1 | advisory | B | OSV.dev GHSA-428g-f7cq-pgp5 | 2026-10-10 | AP-19 finding (MEDIUM, unused) |
| requests | 2.31.0 | advisory | B | OSV.dev GHSA-9wx4-h78v-vm56, GHSA-9hjg-9r4m-mvj7, GHSA-gc5v-m9x4-r6x2 | 2026-10-10 | AP-19 finding (MEDIUM, unused) |
| python-dotenv | 1.0.0 | advisory | B | OSV.dev GHSA-mf9w-mj56-hr94 | 2026-10-10 | AP-19 finding (MEDIUM, unused) |
| Werkzeug 3.1.9, Jinja2 3.1.6, itsdangerous 2.2.0, click 8.5.0, blinker 1.9.0, SQLAlchemy 2.1.4, MarkupSafe 3.0.4, packaging 26.3, urllib3 2.8.0, idna 3.20, certifi 2026.7.22, charset-normalizer 3.5.2, typing-extensions 4.16.0 | as listed (transitive, installed) | advisory | B | OSV.dev querybatch (empty results) | 2026-10-10 | no issue found |
| package-level deprecation/yank (registry metadata) for the six direct packages | as pinned | deprecation | — | not queried | — | UNVERIFIED (see Verification Coverage) |

The OSV lookup used `POST https://api.osv.dev/v1/querybatch` (one request, 19 queries) and `GET /v1/vulns/<id>` for the GHSA records; the PYSEC-2024/2026 records returned are aliases of the GHSA ids above and were not fetched separately.

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-task-manager-api-p3c-20261010-1420-1 | docker run -d ... python:3.13-slim sleep infinity (run copy run-1) | started; dependencies installed; `proc.py start` inside the container exited 2 (could not read the process start time) and the original was not booted there |
| 2 | 2 | stop | container | refactor-arch-task-manager-api-p3c-20261010-1420-1 | docker rm -f refactor-arch-task-manager-api-p3c-20261010-1420-1 | removed |
| 3 | 2 | start | container | refactor-arch-task-manager-api-p3c-20261010-1420-2 | docker run -d ... python:3.13-slim sleep infinity (run copy run-2; /work = launcher dir) | started; dependencies installed |
| 4 | 2 | start | container (exec -d) | refactor-arch-task-manager-api-p3c-20261010-1420-2 | python -X dev /work/launch.py (runs app.py as __main__ with output to a log file; native config) | ready on port 5000 (proc wait exit 0) |
| 5 | 2 | stop | container | refactor-arch-task-manager-api-p3c-20261010-1420-2 | docker rm -f refactor-arch-task-manager-api-p3c-20261010-1420-2 | removed |
| 6 | 3a | start | container | ...-3 (run-3, original) | docker run -d ... python:3.13-slim sleep infinity; install; seed; launcher boot; `proc wait` ready; probe capture of the 63 non-destructive entries | started |
| 7 | 3a | stop | container | ...-3 | docker rm -f ...-3 | removed |
| 8 | 3a | start | container | ...-4, -5, -6, -7 (run-4..run-7, original, one per destructive entry) | same sequence; `probe capture --only <id> --merge` each: delete-tasks-10 (-4), delete-categories-4 (-5), delete-users-3-operator (-6), delete-users-3-anonymous (-7) | started on 2026-10-10 ~14:3x; the session was interrupted by a usage limit while they were idle (about 4 hours); resumed, the four boots had not been touched (fresh DB, no request received) and were reused |
| 9 | 3a | stop | container | ...-4, -5, -6, -7 | docker rm -f, one call each | removed (4 stops) |
| 10 | 3c | start | container | ...-8 (refactored-1) | docker run -d -e OPERATOR_TOKEN=... -e SEED_USER_PASSWORD=... ; install from the refactored manifest; seed; launcher boot; `probe compare` live (63 non-destructive + 4 destructive pending) | started, ready |
| 11 | 3c | stop | container | ...-8 | docker rm -f ...-8 | removed |
| 12 | 3c | start / stop | container | ...-9 .. -12 (refactored-2..5) | one fresh boot per destructive entry, `probe capture --only <id> --merge` into current.json, then `docker rm -f` each | 4 started, 4 removed |
| 13 | 3d | start / stop | container | ...-13 .. -17 (refactored-6..10) | full replay again after the bounded fix (main + 4 destructive boots), `docker rm -f` each | 5 started, 5 removed |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - AP-14 registry-level deprecation/yank metadata (pypi.org JSON) for the six direct packages: not queried → whether any pinned release is yanked or marked deprecated is unverified (advisories were checked).
  - AP-14 Layer 1 for the destructive entries (delete task, category, user): they are exercised only in Phase 3 on their own boots; `delete_user` (user_routes.py:134-151) and the `Query.get` call at user_routes.py:136 were therefore not observed with detectors on.
  - Tier-A evidence for `utcnow()` at models/task.py:52 (`is_overdue`), services/notification_service.py:35 and utils/helpers.py:38: never executed (dead code), not reported as observed.
  - Changelog of flask-cors 4.0.2/6.0.0 and of flask 3.1.3 not fetched: whether those fixes need configuration to take effect is unverified.
Scratch root: the environment scratch directory (no approvals expected); the snapshot is deleted after the re-audit.
Deviation (declared): the execution container ran the original through a launcher outside the tree (`/work/launch.py` in the snapshot's proc/ directory) that redirects output to a log and runs `app.py` as `__main__` (protocol §1.2 option 3), because `exec -d` discards output and `proc.py start` cannot run inside this image. The application's own code and configuration were not touched.
INCIDENT (classification, not process) — D27 ambiguity: `PUT /users/<id>` can set `active=false` (user_routes.py:124-125), which literally "deactivates an account by an identifier taken from the request", but the route is a general profile edit; by the guideline's own tie-break ("a delete that could be a user's own action"/ambiguous signals) it is classified a business operation and proposed, not guarded. `GET /reports/user/<id>` returns one named user's roll-up; criterion: a management aggregate names or ranks principals "which no single principal could need about the others", yet a user could need their own; classified business and proposed. Both are listed under the AP-04 business finding.
Processes: no process action outside the Execution Log; two containers started and removed by exact name; no INCIDENT.
Commands: 0 directory changes, 0 chained commands.

================================
Total: 30 findings
================================

Confirmation: --yes (auto-approved, not human-reviewed)

## Run continuity — interrupted and resumed
The run was interrupted by a usage limit after the baseline's main capture and the four destructive-entry boots had been prepared. On resume the state was reconciled before anything else: `docker ps -a` filtered by this run's label listed exactly four containers (-4 .. -7, all in the Execution Log, still running, none of them had received a request); the target held no source change (`git status`: only the untracked `.claude/` copy and `reports/`); `reports/` held `surface.json`, the gate-time audit and a `baseline.json` with the 63 non-destructive entries.
- Reused: the pristine snapshot, the surface inventory, the Phase 2 audit and its evidence, the 63-entry baseline capture, and the four prepared original boots (their database was fresh and unmodified, so the four destructive captures are as valid as on a new boot).
- Redone: nothing; the four destructive baseline entries were captured on the reused boots, then the containers were removed by exact name. The baseline has 67 entries (63 + 4), all `OBSERVED`, none `ERROR` or `SKIPPED`.
- Not trusted blindly: the baseline file was checked for the destructive and security entries (statuses 200/200/200/200 for the four deletes, `get-debug-console` 200, `get-reports-summary-anonymous` 200) before being used.
- Note: `baseline.json` contains the throwaway Werkzeug debugger page text (a per-process secret of a container that no longer exists); it protects nothing.

## Execution notes for Phase 3
Scope: all severities (`y`, via `--yes`). Isolation: container. Dependencies of the refactored application were installed in each container from the refactored `requirements.txt`; the refactored application ran from `refactored-<n>/` copies, never from the target.

PHASE 3 and the D27 (guidelines §6) classification of every route is in the final block below.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
task-manager-api/
├── .env.example
├── .gitignore
├── README.md
├── app.py                      composition root (create_app)
├── database.py
├── requirements.txt            flask==3.1.3, flask-sqlalchemy==3.1.1, flask-cors==4.0.0
├── seed.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── controllers/
│   ├── __init__.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── task_controller.py
│   ├── user_controller.py
│   └── validation.py
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py
│   └── guards.py
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── category_repository.py
│   ├── clock.py
│   ├── constants.py
│   ├── errors.py
│   ├── persistence.py
│   ├── task.py
│   ├── task_repository.py
│   ├── user.py
│   └── user_repository.py
├── routes/
│   ├── __init__.py
│   ├── category_routes.py
│   ├── report_routes.py
│   ├── serializers.py
│   ├── task_routes.py
│   └── user_routes.py
└── reports/                    (audit-20261010-1431.md, audit-latest.md, surface.json, baseline.json, current.json)
```
Repositories live in the model layer (one layout, applied uniformly). `services/` and `utils/` were removed (dead, AP-17).

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 57 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 10 FIXED, 0 NOT FIXED
  ○ Findings resolved: 23/30  (6 proposed, 1 unresolved)
  ⚠ Re-audit partial — see Verification Coverage  (7 findings over the checks that ran)
    Re-audit passes: 2; fixed after re-audit: 1 (0 of them missed-in-phase-2)
  ✓ Processes: 17 started, 17 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

Per-finding outcome (Phase 2 order):
- resolved (23): AP-01 SECRET_KEY, AP-18 debug/console, AP-03 report module, AP-04 summary aggregate (guarded), AP-04 account delete (guarded), AP-01 seed passwords, AP-01 SMTP credential (module deleted), AP-06, AP-08 hash exposure (masked), AP-05 tasks, AP-09, AP-05 users, AP-19 unused dependencies (removed), AP-10, AP-12, AP-11 wrong-type subset, AP-17 helpers/services, AP-17 unused imports and methods, AP-19 flask (3.1.3), AP-16, AP-14 `utcnow`, AP-14 `Query.get`, AP-15.
- proposed (6): AP-19 flask-cors, AP-04 business operations, AP-18 development server, AP-20, AP-11 product-decision rules, AP-13 pagination.
- unresolved (1): AP-08 MD5 storage, origin `failed` (see below).

Unresolved after re-audit:
- [HIGH] Unsafe Handling of Credentials and Sensitive Data (AP-08), origin `failed`. File: models/user.py:28-37. Fixed: new passwords, password changes and seed accounts use a salted PBKDF2 hash with constant-time comparison, and a legacy MD5 digest is replaced by a salted hash on the account's next successful login (RP-08). Not fixed: an account that does not log in keeps its MD5 digest in the datastore, and the legacy verification path still calls `hashlib.md5`. Closing it needs an operator decision (a reset window), which this run cannot take.

Fix loop: re-audit pass 1 found the AP-15 residual (status literals repeated across controllers and repositories, column default literals; origin `failed`, fixed after re-audit with named constants) and the AP-08 remainder above; the full replay was repeated and re-audit pass 2 read the changed files and re-ran the live advisory lookup for the new manifest pins (flask 3.1.3 and flask-sqlalchemy 3.1.1: no advisory; flask-cors 4.0.0: the five known). No `missed-in-phase-2` item was found.

## Proposed, Not Applied
### [CRITICAL] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:3-3
Reason not applied: the fix (flask-cors 4.0.2 for GHSA-hxwh-jpp2-84pm and GHSA-84pr-m4jr-85g5; 6.0.0 for the three path-matching advisories) removes `Access-Control-Allow-Private-Network` from the preflight responses clients receive today (the baseline holds `access-control-allow-private-network: true` for `options-tasks-private-network-preflight`), and 6.0.0 is a major upgrade whose changelog was not read. The replay was not run against it; the entry exists, so it would show `headerMissing`.
Proposed change: set `flask-cors==6.0.0`, run the existing replay and accept the removed header as the intended result (or configure the option upstream documents, after reading its changelog).

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/user_routes.py:42-90
Reason not applied: no identity model (nothing verifies a credential; `fake-jwt-token-<id>` is never read back), so every current client would receive 401/403.
Proposed change: an identity model (verified token, principals, ownership and role policy: who may set `role`, edit `/users/<id>`, delete tasks and categories, read `/users` and `/reports/user/<id>`), then enforce it on the operations (RP-04).

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: app.py:34-34
Reason not applied: serving with a production WSGI server needs a runtime dependency the application does not have today.
Proposed change: declare the server the team chooses and its command (for example a WSGI server invoked with `app:create_app()`), and stop using `app.run` outside development.

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: models/task.py:13-14
Reason not applied: choosing what a category delete does to its tasks (refuse, detach, cascade) changes what `DELETE /categories/<id>` does; existing rows may violate new constraints.
Proposed change: a migration that counts violating rows, enables foreign-key enforcement for SQLite, declares the delete rule and check constraints on `status` and `priority`.

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: routes/report_routes.py:173-180 (now controllers/category_controller.py)
Reason not applied: maxima and formats (colour pattern, name and description length, tags length) are product decisions that would reject requests accepted today.
Proposed change: a boundary schema with the limits the team chooses.

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: routes/task_routes.py:13-14 (now models/task_repository.py `list_with_relations`, models/user_repository.py `list_all`, models/category_repository.py `list_all`)
Reason not applied: pagination changes what clients receiving the whole collection get today.
Proposed change: `limit`/`offset` with a default limit and an opt-out.

## Authorization classification (D27, guidelines §6) — every route
No identity model exists before or after (no operation verifies a presented credential). Privileged operations are guarded by `X-Operator-Token` (env `OPERATOR_TOKEN`, unset by default, constant-time comparison, 403 when absent or wrong); the replay covered the anonymous call (`FIXED`, 403) and the operator call (`PASS`, same shape) for both.

| Route | Class | Criterion cited | Action |
|---|---|---|---|
| GET / , GET /health | public by design | health/index, no principal data | unchanged |
| GET /reports/summary | privileged | management aggregate: per-principal roll-up naming every user (`user_productivity`) | guarded |
| DELETE /users/<id> | privileged | deletes an account by request id with no identity model (and cascades its tasks) | guarded |
| POST /users | business | registration; the role in the body is the AP-04 business finding | proposed |
| GET /users, GET /users/<id>, GET /users/<id>/tasks | business | plain listing/lookup, account listing included (hash masked instead, AP-08) | proposed |
| PUT /users/<id> | business (ambiguous) | can set `active=false`, but is a general profile edit; tie-break "ambiguous → business" | proposed |
| POST /login | business | sign-in | unchanged |
| GET/POST /tasks, GET/PUT/DELETE /tasks/<id>, GET /tasks/search | business | ordinary domain records, plain lookups | proposed |
| GET /tasks/stats | business | count of records by state, no financial or per-principal content | proposed |
| GET /reports/user/<id> | business (ambiguous) | one named user's roll-up that a user could need about themselves; tie-break | proposed |
| GET/POST /categories, PUT/DELETE /categories/<id> | business | ordinary domain records; `GET /categories` is a plain count by state | proposed |
| GET /console (debug) | diagnostics | debug console; removed by switching debug off (AP-18) | removed |

AP-11 split: the safe subset (wrong-type values and non-object bodies that used to crash with 500: ten security entries, all `FIXED`) was applied; only the product-decision rules and pagination remain proposed.

## Verification Coverage
DEGRADED — the following checks did not run, and the claims above do not cover them:
  - Re-audit pass 2 was a re-read of the changed files plus the live advisory lookup for the new direct pins and the full replay; the transitive packages installed from the refactored manifest were not re-queried individually (their versions were not re-read), and registry-level deprecation/yank metadata was never queried → the re-audit is partial, so the "zero remaining" form is not available (it would not be anyway: 7 findings remain).
  - The legacy-MD5 upgrade-on-login path (models/user.py `check_password`) is not covered by the surface (all replay accounts are created with the new hash) → unverified by execution.
  - The AP-11 safe subset was verified on the ten listed security entries and by reading; the other wrong-type inputs of the same shape (for example `PUT /users/<id>` with a non-boolean `active`, list/object values in text fields) were not each sent → unverified by execution.
  - The guard's operator path was verified by the replay with `OPERATOR_TOKEN=probe-operator-token` in the environment for both guarded operations.
  - flask-cors 4.0.2/6.0.0 and flask 3.1.3 changelogs were not read (flask 3.1.3 was applied because the replay, including cross-origin entries and contract headers, passed).
Deviations kept from Phase 2: the launcher outside the tree for log capture; containers started with `-e` environment (no shell prefixes).
INCIDENT (classification, not process) — D27 ambiguity: `PUT /users/<id>` and `GET /reports/user/<id>`, as described in the table; proposed, not guarded.
Processes: 17 containers started and 17 removed by exact name; `docker ps -a` filtered by this run's label is empty; the snapshot directory and scratch files were deleted after the re-audit. No process INCIDENT. One interruption (usage limit) is documented above; no command was run against anything this run did not start.
Commands: 0 directory changes, 0 chained commands.
================================
