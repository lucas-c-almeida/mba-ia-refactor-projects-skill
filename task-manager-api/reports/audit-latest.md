## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        .worktrees/r7-p3/task-manager-api
Language:      Python (runtime version not declared by the target; host has 3.13.2)
Framework:     Flask ==3.0.0 (manifest pin; no lockfile, not installed on host)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0 (marshmallow, requests, python-dotenv declared but never imported)
Domain:        Task management API: users, task categories, and tasks with status/priority/due date, plus summary and per-user productivity reports
App type:      HTTP service (JSON REST API), with a seed script (`seed.py`) as an operator CLI
Architecture:  Nominal layering: models/ routes/ services/ utils/ exist, but route handlers hold queries, business rules and serialization; services/ and most of utils/ are never imported
Source files:  15 files analyzed (*.py authored in the target; excluded .claude/, reports/, __pycache__/, venv dirs, .gitignore matches (none present))
DB tables:     users, categories, tasks (SQLite, via Flask-SQLAlchemy models; created by db.create_all() at import)
Boot:          python app.py  (README: `pip install -r requirements.txt`, `python seed.py`, `python app.py`)
Port:          5000, fixed in app.py:34 (app.run(debug=True, host='0.0.0.0', port=5000)); no override read
Runtime env:   Python 3.13 (official image), dependencies installed from requirements.txt inside the container
Isolation:     container (docker 28.5.2, image python:3.13-slim); container commands carried by PowerShell (the Bash tool is MINGW64 and rewrites POSIX paths)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.8 resolved at install, SQLite)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-11-04 22:35
Mode:    full
Confirmation: human-confirmed: y; D1=business, D2=privileged (condition from the human: the operator credential is required only when the request changes `role` or `active` — a value different from the stored one; resending the stored values needs no credential)
Tree:    clean at e6d2704
Runtime: installed the declared dependencies from requirements.txt into the run container (site-packages of python:3.13-slim), outside the target
Isolation: container (docker 28.5.2, image python:3.13-slim)
Scratch: environment scratch directory  (protocol §1.1)

## Summary
CRITICAL: 12 | HIGH: 8 | MEDIUM: 8 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:13-13
Description: The framework's session/signing key is set to a string literal: `app.config['SECRET_KEY'] = 'super-secret-key-123'`. The database URI (app.py:11) is a literal too, though it carries no credential.
Impact: Anyone with read access to the repository or any clone holds the signing key; any session or signed value the framework issues can be forged, and rotating it needs a code change and a deploy.
Recommendation: Read the key from configuration (environment), fail closed when it is empty or a placeholder; see RP-01.
Contract: safe

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:33-34
Description: The entry point starts the framework's development server with `debug=True` bound to `0.0.0.0`; no production server is declared anywhere. Observed in the snapshot run: the log prints `Debug mode: on`, `Debugger is active!` and a debugger PIN, and a request that raises (POST /tasks with `"priority": "x"`, GET /tasks/search?priority=abc) answers 500 with the Werkzeug Debugger HTML page carrying the exception text. Escalated to CRITICAL: an interactive debugger on a listener reachable from outside the host.
Impact: The debugger console offers code evaluation to anyone who can reach the port (guarded only by a PIN derivable from host facts), and every unhandled error maps the internals for the next attack.
Recommendation: Take debug, host and port from configuration with debug off by default; replace the framework's default error page with the centralized handler (RP-09). A production WSGI server is a new runtime dependency and is proposed, not applied. See RP-17.
Contract: safe for debug-off and the error boundary (the default error page is not contract; status 500 kept); contract-changing for adding a production server (new runtime dependency).

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password hash in responses   (AP-08)
File: models/user.py:16-25
Description: `User.to_dict()` serializes the whole row, including `'password': self.password` (line 21). It is returned by GET /users/<id> (routes/user_routes.py:33), POST /users (:85), PUT /users/<id> (:129) and POST /login (:209) — observed: the responses carry a 32-hex-char value. Escalated to CRITICAL: the value is an unsalted MD5 digest (models/user.py:29), so exposing it makes the passwords practically recoverable.
Impact: Any anonymous caller harvests every account's password hash with one request per id and cracks the short seeded and user-chosen passwords offline; credentials reused elsewhere fall with them.
Recommendation: Mask the field's value in every serialization while keeping the key and its string type; see RP-08.
Contract: safe (masking keeps the field and its type; no legitimate client reads a hash back)

### [CRITICAL] Known-Vulnerable Dependency — flask-cors 4.0.0   (AP-19)
File: requirements.txt:3-3
Description: OSV.dev (looked up 2026-11-04) returns for flask-cors 4.0.0: GHSA-hxwh-jpp2-84pm / CVE-2024-6221 (HIGH; `Access-Control-Allow-Private-Network: true` sent by default; fixed in 4.0.2), GHSA-84pr-m4jr-85g5 / CVE-2024-1681 (MODERATE, log injection at debug log level; fixed 4.0.1), and GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (MODERATE, path/case matching; fixed 6.0.0). Escalated to CRITICAL: reachability observed — `CORS(app)` (app.py:15) covers every route, and a preflight to /tasks with `Access-Control-Request-Private-Network: true` from an arbitrary origin answered `Access-Control-Allow-Private-Network: true`.
Impact: Any web page a user on the deployment's network visits can drive this unauthenticated API from the browser, across the private-network boundary that browsers otherwise enforce.
Recommendation: Upgrade to flask-cors 4.0.2 (same major: fixes the HIGH and the log injection). The 6.0.0 fixes cross a major line: apply only if the replay, with Origin and preflight entries comparing the Access-Control-* headers, stays PASS; otherwise propose. See RP-18.
Contract: safe within 4.x; 6.x conditional on replay coverage of the CORS headers.

### [CRITICAL] God Module / God Class   (AP-03)
File: routes/report_routes.py:1-223
Description: One module holds two unrelated domain concepts — reporting (12-155) and the full category CRUD (157-223, under the report blueprint) — and mixes persistence (queries at 15-30, 46-56, 105-109, 159-163, 183-184, 205, 218-219), business rules (overdue rule 33-43 and 132-135, completion rate 67 and 151, high-priority threshold 129) and serialization (70-99, 137-153). `summary_report` alone is 89 lines (13-101).
Impact: Any change to categories or reports touches the same file and the same blueprint; nothing in it can be tested without a database and a request context.
Recommendation: Split into a category controller/model repository and a report controller, with routes reduced to parse → call → render; see RP-03, RP-05.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — management report open   (AP-04)
File: routes/report_routes.py:12-101
Description: GET /reports/summary returns a per-principal rollup (`user_productivity`, 53-68: every user's name, task totals and completion rate) with no guard of any kind. Privileged operation (management aggregate with per-principal rollups); the application has no identity model.
Impact: Any anonymous caller reads a productivity ranking of every user.
Recommendation: Guard the operation with an operator credential read from configuration, compared in constant time, closed by default; see RP-04.
Contract: safe (privileged operation: only non-operators are rejected)

### [CRITICAL] Missing or Bypassable Authorization — per-user activity report   (AP-04)
File: routes/report_routes.py:103-155
Description: GET /reports/user/<id> returns one user's name, email and task statistics for any id taken from the path, with no guard. Its classification (privileged management rollup vs. a user's own dashboard) is ambiguous: see Classification Decisions, D1.
Impact: Any caller enumerates every user's email address and activity by iterating ids.
Recommendation: Per D1: guard with the operator credential (privileged), or propose the identity model (business); see RP-04.
Contract: decided at the gate (D1): safe if privileged, contract-changing if business.

### [CRITICAL] Missing or Bypassable Authorization — account deactivation and role change   (AP-04)
File: routes/user_routes.py:92-132
Description: PUT /users/<id> lets any anonymous caller set `active` (124-125, deactivating the account, which then cannot log in at 204-205), `role` (119-122, including `admin`) and `password` (114-117) of any account by path id. The same operation also edits the name and email — ordinary profile data. Classification is ambiguous: see D2.
Impact: Anyone can lock any user out, reset their password (account takeover) or promote any account to admin.
Recommendation: Per D2: require the operator credential for the privileged fields (`active`, `role`), or propose the identity model; see RP-04. The password and profile edits stay with the identity-model proposal in all cases.
Contract: decided at the gate (D2) for `active`/`role`; the rest is contract-changing (proposed).

### [CRITICAL] Missing or Bypassable Authorization — account deletion open   (AP-04)
File: routes/user_routes.py:134-151
Description: DELETE /users/<id> deletes any account, and every task assigned to it (140-142), by path id, with no guard, in an application with no identity model (no operation verifies a presented credential). Privileged operation by definition.
Impact: Any anonymous caller can wipe every account and its tasks by iterating ids; nothing distinguishes the attack from legitimate use.
Recommendation: Guard with an operator credential from configuration, constant-time compare, closed by default; see RP-04.
Contract: safe (privileged operation)

### [CRITICAL] Missing or Bypassable Authorization — no identity model   (AP-04)
File: routes/user_routes.py:185-211
Description: POST /login issues `'fake-jwt-token-' + str(user.id)` (210), a predictable token that no operation ever verifies; every task, user and category operation is anonymous, and the role is taken from the request body at registration (52, 71-72) and trusted. Business operations (CRUD, listings, sign-in, registration) on principal data with no identity model.
Impact: Every client acts as any principal; user listings expose every email (GET /users), and the issued token is guessable and meaningless.
Recommendation: Introduce a real identity model (verified tokens or sessions, ownership and role policy) as a product decision; see RP-04.
Contract: contract-changing: every current client would receive a new 401/403 on operations it calls anonymously today.

### [CRITICAL] Hardcoded Secrets and Credentials — seeded accounts with known passwords   (AP-01)
File: seed.py:16-35
Description: The documented setup script (README: "run it before the first boot") creates three accounts in the runtime database with literal passwords `set_password('1234')`, `('abcd')`, `('pass')` (19, 26, 33); the first is `role = 'admin'` (20).
Impact: Every environment that follows the README has an admin account with a password published in the repository.
Recommendation: Take seed passwords from the environment (or generate random ones) instead of literals; see RP-01.
Contract: safe (the HTTP surface is unchanged; no legitimate client depends on a published password)

### [CRITICAL] Hardcoded Secrets and Credentials — SMTP credential   (AP-01)
File: services/notification_service.py:7-10
Description: `self.email_user = 'taskmanager@gmail.com'` and `self.email_password = 'senha123'` are literals for a third-party SMTP account (smtp.gmail.com). The module is never imported (see the AP-17 finding).
Impact: The credential to an external mail account follows every clone and the history; whoever reads it can send mail as the service.
Recommendation: Remove the literal (here, by removing the dead module); a committed credential must also be rotated by its owner; see RP-01.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: app.py:9-31
Description: The module builds the app at import with literal configuration (11-13), and runs `db.create_all()` inside `app.app_context()` at top level (30-31): importing it touches the database. `seed.py:2` imports the entry point (`from app import app, db`), so seeding runs the import-time side effects. There is no factory and no single place where configuration is resolved; route modules reach the global `db` and model classes directly.
Impact: Nothing can be imported for a test without creating a SQLite file in the working directory; configuration cannot vary per environment without editing code.
Recommendation: Introduce an application factory as composition root with a config module, moving schema creation into the factory; see RP-06.
Contract: safe

### [HIGH] Insecure Runtime Configuration — cross-origin policy reflects any origin   (AP-18)
File: app.py:15-15
Description: `CORS(app)` applies the default policy to every route; observed: a preflight from `https://example.org` received `Access-Control-Allow-Origin: https://example.org` and all methods including DELETE. No credentials are involved (no cookies), so not CRITICAL; the data is not public read-only, so not LOW.
Impact: Any web page can read and mutate users, tasks and categories through a visitor's browser, including on internal deployments.
Recommendation: Restrict allowed origins through configuration; see RP-17.
Contract: contract-changing: cross-origin browser clients from origins not listed would stop receiving CORS headers.

### [HIGH] Unsafe Handling of Credentials and Sensitive Data — fast unsalted password hash   (AP-08)
File: models/user.py:27-32
Description: `set_password` stores `hashlib.md5(pwd.encode()).hexdigest()` — a fast general-purpose digest with no salt — and `check_password` compares with `==`, not in constant time.
Impact: A leaked table (or the API itself, see the CRITICAL AP-08 finding) yields every password through precomputed tables in seconds; identical passwords share a hash.
Recommendation: Use a purpose-built KDF from the standard library (salted, iterated) with a constant-time compare, verifying legacy MD5 hashes once and rehashing on successful login; the reset of legacy hashes is an operator residue; see RP-08.
Contract: safe (the same credentials keep logging in)

### [HIGH] Business Logic in the Delivery Layer — task routes   (AP-05)
File: routes/task_routes.py:11-63
Description: `get_tasks` (53 lines) queries, hand-serializes, computes the overdue rule four levels deep (30-39) and resolves user/category names per row. The same mix is in `create_task` (85-154, validation, existence checks, persistence and logging), `update_task` (156-223), `search_tasks` (240-271, query building) and `task_stats` (273-299, counting and the completion-rate formula). One domain concept, below the AP-03 size threshold: AP-05.
Impact: The task rules cannot be tested or reused without a web request; every entry point re-implements them (see AP-12).
Recommendation: Move queries into the model/repository, rules into the model, orchestration into a task controller; routes become parse → call → render; see RP-05.
Contract: safe

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: routes/task_routes.py:62-63
Description: `get_tasks` wraps its whole body in a bare `except:` returning `{'error': 'Erro interno'}` with nothing logged. Bare or over-broad excepts repeat at task_routes.py:137, 151, 221, 236; user_routes.py:87, 130, 149; report_routes.py:186, 207, 221 — the same try/rollback/500 shape copied per handler. No error handler is registered: unhandled errors fall to the framework's default, observed as the Werkzeug debugger page (see AP-18).
Impact: Failures are invisible in logs, internal errors leak through the default page, and each handler maps errors its own way.
Recommendation: One error boundary registered in the factory, a small error taxonomy, handlers that let errors propagate; keep the application's own error statuses and bodies; see RP-09.
Contract: safe (intentional error statuses and bodies preserved; only the framework default page is replaced, keeping its status)

### [HIGH] Missing Boundary Validation   (AP-11)
File: routes/task_routes.py:102-114
Description: Request values are used with no type check: `priority < 1` (113) raises on a string — observed 500 for `"priority": "x"`; `len(title)` (96) on a non-string; `','.join(tags)` (142) on non-string items; `int(priority)`/`int(user_id)` in search (261, 264) — observed 500 for `priority=abc`. The same pattern is in update_task (166-213), user_routes.py create/update (49-72, 102-125: `re.match`/`len` on non-strings, `active` stored as given) and report_routes.py categories (173-180, 196-202: no body check, `color` unchecked). Escalated to HIGH: unvalidated values reach the datastore (category fields, `description`, `active`, `tags`).
Impact: Malformed requests answer 500 with the debugger page instead of a 400, and wrong-typed values are written to the database.
Recommendation: Type and range checks at the boundary for every input of every operation; see RP-11.
Contract: safe (only wrong-typed or out-of-range values get a new 400)

### [HIGH] Duplicated Logic — validation copies that diverged   (AP-12)
File: routes/task_routes.py:166-184
Description: The title/status/priority validation is copied from create_task (92-114) into update_task (166-184) without the presence guard: `len(data['title'])` with `"title": null` raises (500) where create answers 400. The same divergence exists between create_category (169-175, checks the body) and update_category (196-197, `'name' in data` on a null body raises), and a third copy of the task validation lives unused in utils/helpers.py:57-108 with different rules (strips the title, coerces priority with `int()`, accepts `dd/mm/YYYY`). Escalated to HIGH: the copies have diverged in behaviour.
Impact: The answer depends on which door the request takes; a fix applied to one copy leaves the others broken.
Recommendation: One validator per entity at the boundary, shared by create and update; see RP-12.
Contract: safe

### [HIGH] Business Logic in the Delivery Layer — user routes   (AP-05)
File: routes/user_routes.py:42-90
Description: `create_user` validates, checks uniqueness with a query, hashes, persists and prints; `update_user` (92-132), `delete_user` (134-151, cascade by hand), `get_user_tasks` (153-183, overdue rule and hand-written mapping) and `login` (185-211, credential check and token issuing) mix persistence, rules and serialization in the handler.
Impact: Account rules (uniqueness, password policy, activation) cannot be tested or reused without HTTP.
Recommendation: User controller + model repository; routes parse → call → render; see RP-05.
Contract: safe

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: models/task.py:13-14
Description: `user_id` and `category_id` declare foreign keys, but the engine is SQLite and nothing enables `PRAGMA foreign_keys`, so they are not enforced. DELETE /categories/<id> (routes/report_routes.py:211-223) deletes a category with no rule for its tasks — observed: deleting category 4 succeeded while task 4 still referenced it, leaving an orphan. `status` (11) is free text with no check.
**Correction (Phase 3, re-audit pass 1):** the orphan statement above was not observed — Phase 2 saw only the delete's 200. Re-checked against a fresh copy of the original: after DELETE /categories/4, GET /tasks/4 reports `category_id: null`, because the ORM's unit of work loads the `Category.tasks` backref and nulls the children before deleting. The "parent delete with no child rule" signal was a false positive. The finding stands on its other two parts: foreign keys not enforced, and `status`/`role` stored as free text.
Impact: Tasks point at categories that no longer exist, and any write path that skips the handler's checks stores invalid references or statuses.
Recommendation: Enable foreign-key enforcement per connection and re-parent (null) a category's tasks before deleting it; see RP-19.
Contract: safe (a task whose category was deleted reports `category_id: null` instead of a dangling id; no legitimate client relies on a reference to nothing)

### [MEDIUM] Known-Vulnerable Dependency — unused and unreached packages   (AP-19)
File: requirements.txt:4-6
Description: OSV.dev (2026-11-04): marshmallow 3.20.1 — GHSA-428g-f7cq-pgp5 (MODERATE, fixed 3.26.2); requests 2.31.0 — GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2 (MODERATE, fixed 2.33.0); python-dotenv 1.0.0 — GHSA-mf9w-mj56-hr94 (MODERATE, `set_key` symlink following, fixed 1.2.2). marshmallow and requests are never imported (also AP-17); python-dotenv is used by the runtime (`Flask.run` calls `cli.load_dotenv()`, verified in the installed flask/app.py:573-574), but not its `set_key`. MEDIUM: moderate advisories, vulnerable features unused.
Impact: Every install pulls code with published advisories that the application does not need.
Recommendation: Remove marshmallow and requests (no import, no configuration or runtime use); upgrade python-dotenv to 1.2.2 (same major); see RP-18, RP-16.
Contract: safe

### [MEDIUM] Unbounded Resources — unpaginated listings   (AP-13)
File: routes/task_routes.py:11-14
Description: GET /tasks reads `Task.query.all()` with no limit; so do GET /users (user_routes.py:12), GET /categories (report_routes.py:159), GET /tasks/search (task_routes.py:266) and GET /users/<id>/tasks (user_routes.py:159).
Impact: Response size and memory grow with the table; one request returns the whole dataset.
Recommendation: Add pagination with a bounded page size; see RP-13.
Contract: contract-changing: a default page size would change what clients receive today.

### [MEDIUM] Duplicated Logic — overdue rule and task mappings   (AP-12)
File: routes/task_routes.py:30-39
Description: The overdue rule (due date past and status not done/cancelled) is written out at task_routes.py:30-39, 71-80, 283-287; user_routes.py:171-180; report_routes.py:33-43, 132-135, while `Task.is_overdue` (models/task.py:50-60) is never called. The task-to-dict mapping is hand-written again in get_tasks (17-28) and get_user_tasks (user_routes.py:162-169, a different field set) beside `Task.to_dict`.
Impact: Changing what "overdue" means needs six edits; the mappings drift independently.
Recommendation: One model method for the rule, one serializer per representation; see RP-12.
Contract: safe

### [MEDIUM] Deprecated or End-of-Life API Usage — datetime.utcnow()   (AP-14)
File: routes/task_routes.py:31-31
Description: Tier A: running the original with `PYTHONWARNINGS=always::DeprecationWarning -X dev` emitted "datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)" at task_routes.py:31, 72, 215, 285; user_routes.py:172; report_routes.py:35, 42, 45, 71, 133; seed.py:66, 67, 69, 70, 74; and through the column defaults `default=datetime.utcnow` (models/task.py:15-16, models/user.py:14, models/category.py:11). Not exercised but same call: utils/helpers.py:38, services/notification_service.py:35.
Impact: The call is scheduled for removal; a routine Python upgrade breaks every timestamp and the overdue rule at once.
Recommendation: Modern equivalent named by the runtime: `datetime.now(datetime.UTC)`; keep stored values naive UTC (`.replace(tzinfo=None)`) behind one clock helper so serialization and comparisons do not change; see RP-14.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: routes/task_routes.py:41-57
Description: get_tasks issues `User.query.get` and `Category.query.get` per task (42, 51). Also: `len(u.tasks)` lazy-loads per user (user_routes.py:22); one task query per user in the summary (report_routes.py:55-56); one count per category (report_routes.py:163); whole-table reads to count overdue tasks in Python (task_routes.py:281-287, report_routes.py:30-43); nine separate count queries for status/priority (report_routes.py:19-28).
Impact: Latency grows linearly with users, tasks and categories; the summary scales with users × tasks.
Recommendation: Set-based queries: joins/eager loading for names, grouped counts, overdue counted in SQL; see RP-10.
Contract: safe

### [MEDIUM] Magic Values   (AP-15)
File: routes/task_routes.py:110-110
Description: Status strings `'pending'`, `'in_progress'`, `'done'`, `'cancelled'` are repeated as literals across modules (task_routes.py:32, 110, 177, 276-279, 286; user_routes.py:173; report_routes.py:19-22, 36, 49, 60, 120-127, 134; models/task.py:11, 39, 53); also the role list (user_routes.py:71, 120), title bounds 3/200 (task_routes.py:96-100, 167-170), password minimum 4 (user_routes.py:64, 115), priority bounds and the "high priority" threshold `<= 2` (report_routes.py:129), the 7-day window (report_routes.py:45). The unused constants in utils/helpers.py:110-116 show the intent. Escalated to MEDIUM: the status values appear in several modules that must agree.
Impact: A typo silently creates a new status; changing a bound means hunting every copy.
Recommendation: Named constants owned by the model layer; see RP-15.
Contract: safe

### [MEDIUM] Dead Code — stale second implementations   (AP-17)
File: utils/helpers.py:57-116
Description: `process_task_data` and the constants block are a second, different implementation of the live task validation, never called. Unreferenced as well: every other helper in the module (`format_date` and `calculate_percentage` are imported at report_routes.py:7 but unused), `Task.validate_status`, `validate_priority`, `is_overdue` (models/task.py:38-60), `User.is_admin` (models/user.py:34-38), and the whole `services/notification_service.py` module (never imported; it also holds the SMTP credential of the AP-01 finding). Escalated to MEDIUM: stale copies of live rules that a reader may modify instead of the real one.
Impact: The services/ and utils/ layers look real but are decorative; maintainers edit code that never runs.
Recommendation: Delete the dead units, keeping the rules in the one place that runs; see RP-16.
Contract: safe

### [LOW] Dead Code — unused imports   (AP-17)
File: app.py:7-7
Description: `import os, sys, json, datetime` — os, sys and json unused. Likewise task_routes.py:7 (json, os, sys, time), user_routes.py:6 (hashlib, json), report_routes.py:8 (json), models/task.py:3 (json), utils/helpers.py:3-7 (os, json, sys, math, hashlib).
Impact: Noise that misstates each module's real dependencies.
Recommendation: Remove; see RP-16.
Contract: safe

### [LOW] Known-Vulnerable Dependency — flask 3.0.0   (AP-19)
File: requirements.txt:1-1
Description: OSV.dev (2026-11-04): GHSA-68rp-wp8r-4726 / CVE-2026-27205, rated LOW by its source — the session does not add `Vary: Cookie` when accessed in some ways; fixed in 3.1.3. The application never uses the session.
Impact: Low; a caching proxy could serve a session-dependent response to another user if sessions are ever used.
Recommendation: Upgrade to flask 3.1.3 (same major); see RP-18.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: routes/report_routes.py:24-28
Description: Priority counts are held in `p1`..`p5` and emitted under `critical`..`minimal` (84-88), so the mapping lives only in their order; the category CRUD (157-223) is registered on `report_bp` in a file named for reports.
Impact: A reader cannot see that priority 1 means "critical" without reading two places; categories are not where their name says.
Recommendation: Named priority labels in the model; category routes in their own module; see RP-16.
Contract: safe

### [LOW] Deprecated or End-of-Life API Usage — Query.get()   (AP-14)
File: routes/task_routes.py:42-42
Description: Tier A: the run emitted SQLAlchemy `LegacyAPIWarning`: "The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get()" at task_routes.py:42, 51, 67, 117, 122, 158, 227; user_routes.py:29, 94, 136, 155; report_routes.py:105, 192, 213 (same call, not reached in the run: task_routes.py:188, 195).
Impact: Legacy construct with a drop-in successor; it will follow the 1.x API out.
Recommendation: Modern equivalent named by the warning: `Session.get(Model, id)` (`db.session.get`); see RP-14.
Contract: safe

## Signal Ledger

| Entry | Signal | Examined | Occurrences | Outcome |
|---|---|---|---|---|
| AP-01 | Literal assigned to secret-named identifier | all source files | 2: app.py:13; services/notification_service.py:10 | finding: AP-01 app.py:13; AP-01 notification_service.py:7-10 |
| AP-01 | Credential literals in seed/fixture data reaching runtime | seed.py, models | 3: seed.py:19, 26, 33 | finding: AP-01 seed.py:16-35 |
| AP-01 | Connection URL with inline credentials | all source files | 0 (app.py:11 `sqlite:///tasks.db` has none) | none |
| AP-01 | High-entropy literal / credential prefix | all source files | 0 | none |
| AP-01 | Framework signing key set to literal | app.py | 1: app.py:13 | finding: AP-01 app.py:13 |
| AP-01 | Credential-bearing file committed | target tree (ls -la) | 0 (no .env, *.pem, *.key) | none |
| AP-01 | Config read with real secret as default | all source files | 0 (no environment reads at all) | none |
| AP-02 | Input reaching driver via concatenation | routes/*.py | 0 (ORM only; `like(f'%{query}%')` at task_routes.py:252-253 builds a bound value) | discarded: the f-string forms the bound parameter, not SQL text |
| AP-02 | Interpolation markers inside statement strings | all source files | 0 raw statements | none |
| AP-02 | ORM escape hatch with built string | all source files | 0 | none |
| AP-02 | Dynamic identifiers from input | routes/*.py | 0 | none |
| AP-02 | Shell/process execution with input | all source files | 0 | none |
| AP-02 | Unsafe deserialization / template from input | all source files | 1: services/notification_service.py:18 (mail headers from task title) | discarded: module never imported (AP-17), unreachable |
| AP-02 | Path traversal | all source files | 0 | none |
| AP-03 | ≥3 responsibility categories in one module | all modules | 3: routes/report_routes.py, routes/task_routes.py, routes/user_routes.py | finding: AP-03 report_routes.py (two concepts); task/user routes → AP-05 by precedence |
| AP-03 | >300–400 lines with ≥2 categories | all modules | 0 (largest: task_routes.py 299) | none |
| AP-03 | Unit >50 lines / nesting >3 / many params | routes/*.py | 5: get_tasks 11-63, create_task 85-154, update_task 156-223, summary_report 12-101, nesting 30-39 | folded into AP-05 task_routes, AP-03 report_routes |
| AP-03 | Several unrelated domain concepts in one file | all modules | 1: report_routes.py (reports + categories) | finding: AP-03 report_routes.py |
| AP-03 | Low-cohesion class | models, services | 0 | none |
| AP-03 | Grab-bag utils/helpers module | utils/helpers.py | 1 | discarded as AP-03: module is unused; filed as AP-17 utils/helpers.py |
| AP-03 | Very high afferent coupling | import graph | 1: database.py (imported by all models/routes) | discarded: holds only the db handle, one responsibility |
| AP-04 | Principal resource with no auth/ownership check | routes/*.py | all 18 routes | findings: AP-04 user_routes.py:185-211 (business), report_routes 12-101, 103-155, user_routes 92-132, 134-151 |
| AP-04 | Lookup filtered only by input id (IDOR) | routes/*.py | 14 `Query.get(<path id>)` | folded into AP-04 business finding |
| AP-04 | Check only on one door | all | 0 (no checks exist) | none |
| AP-04 | Role/permission taken from request | user_routes.py | 2: 52, 119-122 | folded into AP-04 user_routes.py:185-211 and :92-132 |
| AP-04 | Token accepted without verification | all | 1: user_routes.py:210 issues a token nothing verifies | folded into AP-04 user_routes.py:185-211 |
| AP-04 | Check written but never reached | all | 0 (User.is_admin defined, never called — AP-17) | none |
| AP-04 | Commented/flag-disabled guard | all | 0 | none |
| AP-04 | Privileged operation with no guard | routes/*.py | 3 (+1 ambiguous): DELETE /users/<id>, GET /reports/summary, PUT /users/<id> active/role (D2), GET /reports/user/<id> (D1) | findings: AP-04 user_routes 134-151, report_routes 12-101, user_routes 92-132 (D2), report_routes 103-155 (D1); GET /tasks/stats discarded: plain count by state |
| AP-05 | Domain decisions in handlers | routes/*.py | 3 modules | findings: AP-05 task_routes, AP-05 user_routes; report_routes under AP-03 |
| AP-05 | Persistence calls in handlers | routes/*.py | all handlers | same findings |
| AP-05 | Handler >30 lines not mapping | routes/*.py | 8 handlers | same findings |
| AP-05 | Request objects deep in stack | all | 0 (request read only in handlers) | none |
| AP-05 | Same rule in two handlers | routes/*.py | overdue ×6, validation ×2 | filed as AP-12 findings |
| AP-05 | Pass-through service layer | services/ | services/ never imported | filed as AP-17 (dead, not pass-through) |
| AP-06 | Unit constructs collaborators | all | 1: notification_service.py:15 (SMTP in method) | discarded: dead module (AP-17) |
| AP-06 | Import-time side effects | all | 1: app.py:30-31 create_all | finding: AP-06 app.py:9-31 |
| AP-06 | No composition root | app.py, seed.py | 1 | finding: AP-06 app.py:9-31 |
| AP-06 | Clock/random/fs inside rules, no seam | routes, models | overdue rule calls datetime.utcnow() inline (6 sites) | folded into AP-06 and AP-12 (one clock helper) |
| AP-06 | Domain importing concrete driver | models | models import Flask-SQLAlchemy `db` | discarded: Active Record via the ORM is the chosen model-layer persistence (guidelines §2) |
| AP-06 | Config read at point of use | all | 0 env reads; literals in app.py:11-13 | folded into AP-06 / AP-01 |
| AP-07 | Module-level variable mutated | all | 0 | none |
| AP-07 | Request-scoped data stored globally | all | 0 | none |
| AP-07 | In-memory collection as store | services/notification_service.py:6 | 1 (instance list `notifications`) | discarded: instance attribute of a never-instantiated class |
| AP-07 | Mutable default / shared class attribute | all | 0 | none |
| AP-07 | Cache/pool with no lifecycle | all | 0 (pool owned by Flask-SQLAlchemy) | none |
| AP-07 | Monkey-patched built-in | all | 0 | none |
| AP-07 | In-process id counter | all | 0 | none |
| AP-08 | Password stored reversibly | models/user.py | 0 | none |
| AP-08 | Fast digest for passwords | models/user.py | 1: user.py:29, 32 | finding: AP-08 user.py:27-32 |
| AP-08 | Shared/missing salt | models/user.py | 1: no salt | finding: AP-08 user.py:27-32 |
| AP-08 | Non-constant-time compare | models/user.py | 1: user.py:32 | finding: AP-08 user.py:27-32 |
| AP-08 | Sensitive values in logs | all `print` sites | 6 prints (ids, titles, names, exception text) | discarded: no credential or token printed; names are a minor personal-data trace on stdout |
| AP-08 | Whole record serialized with secret field | models/*.py | 1: user.py:16-25 | finding: AP-08 user.py:16-25 |
| AP-08 | Transport without protection / verify off | all | 0 | none |
| AP-08 | Token with no expiry/rotation | user_routes.py:210 | 1 | folded into AP-04 user_routes.py:185-211 (token never verified at all) |
| AP-09 | Empty/log-and-continue catch | routes/*.py | 10 bare/broad excepts | finding: AP-09 task_routes.py:62-63 |
| AP-09 | Over-broad catch over large block | task_routes.py:13-63 | 1 | same finding |
| AP-09 | Same error mapping per handler | routes/*.py | 10 | same finding |
| AP-09 | No centralized handler (observed default) | app.py; run | 1: observed Werkzeug debugger page on 500 | same finding + AP-18 app.py:33-34 |
| AP-09 | Internals in response body | run | 1: debugger page with exception text | filed under AP-18 app.py:33-34 |
| AP-09 | Inconsistent error-by-return convention | all | 0 | none |
| AP-09 | Partial writes without transaction | user_routes.py:140-146 | 0 (single commit) | none |
| AP-09 | Exceptions for control flow | task_routes.py:135-138 | 1 (strptime in try) | discarded: narrow intent, the bare except is covered by the AP-09 finding |
| AP-10 | Driver/ORM call in loop body | routes/*.py | 4: task_routes 42, 51; report_routes 56, 163 | finding: AP-10 task_routes.py:41-57 |
| AP-10 | Per-element FK fetch | routes/*.py | same | same finding |
| AP-10 | Lazy relation in iteration | user_routes.py:22 | 1 | same finding |
| AP-10 | Same read repeated with different args | report_routes.py:19-28; task_routes.py:275-279 | 2 | same finding |
| AP-10 | Remote call in loop | all | 0 | none |
| AP-10 | Whole table read to count in app code | task_routes.py:281; report_routes.py:30 | 2 | same finding |
| AP-10 | Write loop one round trip each | user_routes.py:141-142; seed.py:78-90 | 2 | discarded: deletes flushed in one commit; seed is a one-shot of 10 rows |
| AP-11 | Input used without type/range check | routes/*.py | all write handlers + search | finding: AP-11 task_routes.py:102-114 |
| AP-11 | Optional input dereferenced without null check | task_routes.py:167; report_routes.py:197 | 2 | finding: AP-12 task_routes.py:166-184 (divergence) |
| AP-11 | Unconstrained pagination param | all | 0 (no pagination at all) | see AP-13 |
| AP-11 | Numeric parse with no failure path | task_routes.py:261, 264 | 2 (observed 500) | finding: AP-11 |
| AP-11 | Validation on one entry, not the other | create vs update | 2 pairs | finding: AP-12 task_routes.py:166-184 |
| AP-11 | Validation after use | all | 0 | none |
| AP-11 | Domain invariant enforced nowhere | models | color length/format (report_routes 180, 202), `active` type | folded into AP-11 |
| AP-11 | No upper bound on body/array length | all | tags arrays, description unbounded | folded into AP-11 |
| AP-11 | Validation scattered as ad-hoc conditionals | routes/*.py | yes | folded into AP-11/AP-12 |
| AP-12 | Structurally identical blocks ≥10 lines | routes/*.py | overdue block ×6, mapping ×3 | finding: AP-12 task_routes.py:30-39 |
| AP-12 | Same rule in several places | routes, models, utils | overdue ×7, validation ×3 | findings: AP-12 30-39, AP-12 166-184 |
| AP-12 | Same validation/mapping per handler | routes/*.py | yes | same findings |
| AP-12 | Hand-written mapping with different field sets | task_routes 17-28; user_routes 162-169 | 2 | finding: AP-12 task_routes.py:30-39 |
| AP-12 | Copy-and-modify with divergence | create/update pairs; helpers | 3 | finding: AP-12 task_routes.py:166-184 (HIGH) |
| AP-12 | Same constant literal across files | all | status strings | filed as AP-15 |
| AP-12 | Condition repeated at call sites | all | `if not data` per handler | folded into AP-11 |
| AP-13 | Paired acquire/release with gap | notification_service.py:15-20 | 1 | discarded: dead module (AP-17) |
| AP-13 | Handle without release on failure | all; seed run | 1 ResourceWarning "unclosed database" at seed exit | discarded: pooled connection owned by Flask-SQLAlchemy in a one-shot script, released at interpreter exit; no handle opened by project code |
| AP-13 | Connection per call / unbounded pool | all | 0 | none |
| AP-13 | Outbound call without timeout | notification_service.py:15 | 1 | discarded: dead module |
| AP-13 | Unbounded retry | all | 0 | none |
| AP-13 | Unbounded read | routes/*.py | 5 listings | finding: AP-13 task_routes.py:11-14 |
| AP-13 | Unbounded accumulator | notification_service.py:6 | 1 | discarded: dead module |
| AP-13 | Background task with no shutdown | all | 0 | none |
| AP-13 | Unbounded recursion | all | 0 | none |
| AP-14 | Layer 1: forced warnings — boot | `python -X dev app.py`, PYTHONWARNINGS=always::DeprecationWarning | 0 at boot | none |
| AP-14 | Layer 1: forced warnings — seed script | `python -X dev seed.py` | utcnow at seed.py:66-74 and column defaults | finding: AP-14 task_routes.py:31-31 |
| AP-14 | Layer 1: forced warnings — surface | 24 requests, one per route incl. error paths (all 18 routes) | utcnow ×10 sites; Query.get ×14 sites | findings: AP-14 utcnow (MEDIUM), AP-14 Query.get (LOW) |
| AP-14 | Deprecated flag in manifest/installed metadata | requirements.txt, pip list | 0 | none |
| AP-14 | Structurally superseded constructs | all | 0 beyond the above | none |
| AP-14 | Layer 2: registry yanked/deprecated | not queried per package | — | UNVERIFIED — PyPI per-release `yanked` not queried; see Verification Coverage |
| AP-15 | Unexplained numeric literal in decisions | routes/*.py | 3/200, 4, 1/5, <=2, 7 | finding: AP-15 |
| AP-15 | Bare duration/size without unit | report_routes.py:45 | 1 (`days=7` names the unit) | folded into AP-15 |
| AP-15 | String enum literals repeated across files | all | status ×20+, roles ×3 | finding: AP-15 task_routes.py:110 |
| AP-15 | Literal repeated in several places | all | same | same finding |
| AP-15 | Numeric code compared directly | all | 0 | none |
| AP-15 | Unnamed index/offset | all | 0 | none |
| AP-15 | Environment literal inline | app.py:11, 34; notification_service.py:7-8 | 3 | folded into AP-06 / AP-18 / AP-01 |
| AP-16 | Name contradicts behaviour | all | 0 | none |
| AP-16 | Non-descriptive identifiers | routes/*.py | p1..p5, d, data, t, c | finding: AP-16 report_routes.py:24-28 |
| AP-16 | Several names for one concept | all | 0 | none |
| AP-16 | How-not-what names | all | 0 | none |
| AP-16 | Mixed naming conventions | all | 0 | none |
| AP-16 | Mixed human languages | all | Portuguese messages/docstring, English identifiers | discarded: consistent split (messages pt, identifiers en), deliberate |
| AP-16 | Files where their name says they don't belong | routes/report_routes.py | 1 (categories) | finding: AP-16 (and AP-03) |
| AP-16 | Comment contradicting code | all | 0 | none |
| AP-16 | Boolean params at call sites | all | 0 | none |
| AP-17 | Commented-out code | all | 0 | none |
| AP-17 | Unreachable branch | all | 0 | none |
| AP-17 | Defined, never referenced unit | all | helpers (9 units), Task ×3 methods, User.is_admin, NotificationService | finding: AP-17 utils/helpers.py:57-116 |
| AP-17 | Unused import / declared dep never imported | all; requirements.txt | 6 modules; marshmallow, requests | finding: AP-17 app.py:7-7; deps filed under AP-19 requirements.txt:4-6; python-dotenv kept (runtime use verified) |
| AP-17 | Parameter never read | utils/helpers.py:57 (`existing_task`) | 1 | folded into AP-17 helpers (dead unit) |
| AP-17 | Constant feature flag | all | 0 | none |
| AP-17 | Unregistered endpoint | all | 0 | none |
| AP-17 | Old/backup copies | tree | 0 | none |
| AP-18 | Debug on by literal on start path | app.py:34 | 1 (observed) | finding: AP-18 app.py:33-34 |
| AP-18 | Dev server as production server | app.py:34; no Procfile/Dockerfile | 1 | same finding |
| AP-18 | Bind all interfaces + debug | app.py:34 | 1 (observed 0.0.0.0) | same finding |
| AP-18 | Internals in error output | run | 1 (debugger page) | same finding |
| AP-18 | CORS trusts every origin / reflects Origin | app.py:15; run | 1 (observed reflection) | finding: AP-18 app.py:15-15 |
| AP-18 | Unrestricted diagnostic surfaces | run | Werkzeug debugger console | same as AP-18 app.py:33-34 |
| AP-18 | Protective defaults off | all | 0 | none |
| AP-19 | OSV advisory for direct dependency | 6 direct deps, versions pinned | 5 packages with advisories | findings: AP-19 flask-cors (CRITICAL), AP-19 marshmallow/requests/python-dotenv (MEDIUM), AP-19 flask (LOW) |
| AP-19 | Advisory for transitive dependency | 11 installed transitive packages | 0 | none |
| AP-19 | Range resolves to fixed but lock pins vulnerable | no lockfile | 0 | none |
| AP-19 | No lockfile with ranges | requirements.txt | 0 (all direct pins exact); transitive versions are install-date dependent | none (transitives queried at installed versions, 2026-11-04) |
| AP-19 | No lockfile, exact pins | requirements.txt | 6 | queried (see table) |
| AP-20 | Identity column without uniqueness | models | 0 (users.email unique) | none |
| AP-20 | FK column without enforced FK | models/task.py:13-14 | 2 (SQLite, pragma never enabled) | finding: AP-20 models/task.py:13-14 |
| AP-20 | Parent delete with no child rule | report_routes.py:218 | 1 (observed orphan) | same finding |
| AP-20 | Money in binary float | models | 0 | none |
| AP-20 | Closed set stored as free text | models/task.py:11; user.py:12 | 2 (status, role) | folded into AP-20 |

## Classification Decisions
D1. GET /reports/user/<id> — returns one user's name, email and task statistics for any id.
  Privileged because: it is activity per user, computed for any principal named in the path; with no identity model nobody can be asking about themselves, so only an operator has a legitimate reason to read another user's rollup.
  Business because:   it is a single-principal view (a personal dashboard / profile statistics), contains no financial figure and no ranking across principals.
  If privileged: guard with the operator credential (`OPERATOR_TOKEN`, closed by default) — finding becomes resolved.
  If business:   proposed under PROPOSED, NOT APPLIED with the identity model.
D2. PUT /users/<id> — updates name, email, password, role and `active` of any account.
  Privileged because: setting `active=false` deactivates an account and `role` changes privileges, by request id, with no identity model.
  Business because:   the same operation is the ordinary profile edit (name, email), which clients use today anonymously.
  If privileged: requests that change `active` or `role` require the operator credential (`OPERATOR_TOKEN`); name/email/password edits stay open — the `active`/`role` part becomes resolved, password/profile access stays with the identity-model proposal.
  If business:   proposed under PROPOSED, NOT APPLIED.

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| datetime.utcnow() | Python 3.13 (image python:3.13-slim) | deprecation | A | DeprecationWarning, forced (-X dev, PYTHONWARNINGS) | n/a — local | AP-14 MEDIUM |
| SQLAlchemy Query.get() | SQLAlchemy 2.1.8 | deprecation (legacy) | A | LegacyAPIWarning, forced | n/a — local | AP-14 LOW |
| flask | 3.0.0 | advisory | B | OSV.dev GHSA-68rp-wp8r-4726 | 2026-11-04 | AP-19 LOW |
| flask-sqlalchemy | 3.1.1 | advisory | B | OSV.dev (no vulns) | 2026-11-04 | no issue found |
| flask-cors | 4.0.0 | advisory | B | OSV.dev GHSA-hxwh-jpp2-84pm, GHSA-84pr-m4jr-85g5, GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 | 2026-11-04 | AP-19 CRITICAL |
| marshmallow | 3.20.1 | advisory | B | OSV.dev GHSA-428g-f7cq-pgp5 | 2026-11-04 | AP-19 MEDIUM |
| requests | 2.31.0 | advisory | B | OSV.dev GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2 | 2026-11-04 | AP-19 MEDIUM |
| python-dotenv | 1.0.0 | advisory | B | OSV.dev GHSA-mf9w-mj56-hr94 | 2026-11-04 | AP-19 MEDIUM |
| werkzeug, sqlalchemy, jinja2, urllib3, certifi, idna, click, itsdangerous, markupsafe, blinker, charset-normalizer | installed versions (pip list in run container) | advisory | B | OSV.dev querybatch (no vulns) | 2026-11-04 | no issue found |
| all direct packages | pinned | registry deprecation/yank | — | not queried | — | UNVERIFIED |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-task-manager-api-202611050130-8146e33a-1 | `docker run -d ... python:3.13-slim sleep infinity`, run-1 mounted at /app | running |
| 2 | 2 | exec (one-shot) | container | same | `pip install -r requirements.txt` | installed |
| 3 | 2 | exec (one-shot) | container | same | `python -X dev seed.py` (detectors on) | exit 0; warnings recorded |
| 4 | 2 | start (foreground exec, bounded) | container | same | `timeout 90 python -X dev app.py` | ready on 5000; ended by its own timeout (exit 124) before use |
| 5 | 2 | start (foreground exec, bounded) | container | same | `timeout 240 python -X dev app.py` | ready on 5000; exercised 24 requests + 1 CORS preflight |
| 6 | 2 | stop | container | same | `docker rm -f` by exact name | removed; exec of #5 ended (exit 137) |
| 7 | 3a | start | container | refactor-arch-task-manager-api-202611050130-8146e33a-2 | run-2 (original): install, `python seed.py`, `exec -d python app.py`, `proc wait --port 5000` | ready on 5000; full baseline capture (483 entries) |
| 8 | 3a | stop | container | -2 | `docker rm -f` by exact name | removed |
| 9 | 3a | start | container | -3, -4, -5, -6 | run-3..run-6 (original), each: install, seed, `exec -d python app.py`, `proc wait` | ready on 5000; one destructive entry each (delete-task, delete-category, delete-user-operator, delete-user-anonymous) |
| 10 | 3a | stop | container | -3, -4, -5, -6 | one `docker rm -f` naming the four containers exactly | removed |
| 11 | 3c | start | container | -7 | refactored-1: install refactored manifest, seed (detectors on), `exec -d python app.py`, `proc wait` | ready on 5000; full replay (483 entries) |
| 12 | 3c | stop | container | -7 | `docker rm -f` by exact name | removed |
| 13 | 3c | start | container | -8, -9, -10, -11 | refactored-2..refactored-5, each: install, seed, `exec -d`, `proc wait` | ready; one destructive entry each; PNA preflight check on -11 |
| 14 | 3c | stop | container | -8, -9, -10, -11 | one `docker rm -f` naming the four exactly | removed |
| 15 | 3d | start (foreground exec, bounded) | container | -12 | refactored-6: install, seed (detectors on), `timeout 300 python -X dev app.py` | ready; surface + 3 destructive paths exercised with detectors on |
| 16 | 3d | stop | container | -12 | `docker rm -f` by exact name | removed; bounded exec ended (exit 137) |
| 17 | 3d | start | container | -13 | run-7 (original): install, seed, `exec -d python app.py`, `proc wait` | ready; category-delete orphan re-check |
| 18 | 3d | stop | container | -13 | `docker rm -f` by exact name | removed |
| 19 | 3d | start | container | -14 | run-8 (original): install, seed, `exec -d python app.py`, `proc wait` | ready; late capture of create-task-dangling-user (§4.3) |
| 20 | 3d | stop | container | -14 | `docker rm -f` by exact name | removed |
| 21 | 3d | start | container | -15, -16, -17, -18, -19 | refactored-7..refactored-11 (after fix loop): install, seed, `exec -d`, `proc wait` | ready; second full replay (484 entries) + four destructive entries; FK check on -15 |
| 22 | 3d | stop | container | -15..-19 | one `docker rm -f` naming the five exactly | removed |
| 23 | 3d | start (foreground exec, bounded) | container | -20 | refactored-12: install, seed (detectors on), `timeout 300 python -X dev app.py` | ready; second re-audit runtime checks |
| 24 | 3d | stop | container | -20 | `docker rm -f` by exact name | removed; bounded exec ended (exit 137) |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - AP-14 Layer 2 registry check (PyPI per-release `yanked`/`yanked_reason`): not queried → whether any pinned version is yanked is unverified.
  - AP-14 Layer 1 for utils/helpers.py:38 and services/notification_service.py:35: never reached by any run (dead code) → their utcnow use is reported by reading, at the same tier as the observed identical call.
  - Boot runs were foreground `exec` calls bounded by `timeout` (instead of `exec -d`) so that the forced warnings reached the log; the process lived inside this run's container, whose removal by exact name was the stop (row 6).
Scratch root: C:\Users\lucas\AppData\Local\Temp\claude\b247d7bb4f414394\805dbf78-3ef5-40ce-9aab-ca850a1feaef\scratchpad\refactor-arch-task-manager-api-202611050130-8146e33a (environment scratch directory). Excluded from every copy: .git, .hg, .svn, .venv, venv, __pycache__.

================================
Total: 32 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
  For each classification decision, answer privileged or business (e.g. "y D1=privileged D2=business").
  An unanswered decision is treated as business (proposed).
> y D1=business D2=privileged
  (condition from the human on D2: the operator credential is required only when the request changes `role` or `active` to a value different from the stored one; resending the stored values keeps working without it)

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
task-manager-api/
├── .env.example            every variable, secrets empty (loaded by python-dotenv, or exported)
├── .gitignore              .env, instance/, *.db, __pycache__/, venvs
├── README.md               layout and run instructions
├── app.py                  composition root: create_app() — config, CORS, db, controllers, routes, error boundary
├── database.py             db handle, get_by_id (Session.get), commit(), SQLite foreign-key enforcement
├── requirements.txt        flask 3.1.3, flask-sqlalchemy 3.1.1, flask-cors 6.0.0, python-dotenv 1.2.2
├── seed.py                 operator script; account passwords from SEED_*_PASSWORD
├── config/
│   ├── __init__.py
│   └── settings.py         reads the environment once; immutable Settings
├── models/                 Models: entities, rules, queries
│   ├── __init__.py
│   ├── category.py
│   ├── clock.py            utc_now() — successor of datetime.utcnow(), naive UTC
│   ├── errors.py           domain error taxonomy
│   ├── task.py             statuses, priorities, overdue rule, completion rate, set-based queries
│   └── user.py             roles, scrypt KDF with legacy-MD5 upgrade, masked serialization
├── controllers/            Controllers: one use case per method, no HTTP
│   ├── __init__.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── task_controller.py
│   └── user_controller.py
├── routes/                 Views: parse → controller → render
│   ├── __init__.py         register_routes()
│   ├── category_routes.py
│   ├── presenters.py       response shapes
│   ├── report_routes.py
│   ├── system_routes.py    / and /health
│   ├── task_routes.py
│   ├── user_routes.py
│   └── validation.py       boundary type checks
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py    error boundary, correlation id
│   └── operator_guard.py   X-Operator-Token vs OPERATOR_TOKEN, closed by default
└── reports/                audit, surface.json, baseline.json, replay.json, compare.json
```
Removed: `services/` (never imported; held the SMTP credential), `utils/` (unused helpers, a stale second validation). Layout: MVC with the routes as Views and persistence kept in the model layer (Active Record through Flask-SQLAlchemy), applied uniformly.

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 69 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 5 FIXED, 0 NOT FIXED
  ✓ Malformed input: 401 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 16 operations
  ✓ Values: 13 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 20/32  (12 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 12 proposed-not-applied, 0 unresolved  (re-audit: 12 findings)
    Re-audit passes: 2; fixed after re-audit: 1 (0 of them missed-in-phase-2)
  ✓ Processes: 20 started, 20 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

### Replay notes
- Baseline: 488 entries against the original (483 full capture, 4 destructive each on its own fresh boot, 1 late security entry captured against a fresh original per §4.3). It held 105 answers with status 500. The final replay holds none.
- The final replay ran after the fix loop: one full capture plus the four destructive entries, each on its own fresh boot. The first full replay, before the fix loop, also had 0 REGRESSION.
- Security FIXED: report-summary-anonymous (AP-04, 403), update-user-role-anonymous and update-user-deactivate-anonymous (AP-04/D2, 403), delete-user-anonymous (AP-04, 403), create-task-dangling-user (AP-20, 404).
- D2 condition: update-user-same-role-active resends the stored `role`/`active` without a credential. It is PASS (200), and its value entry HOLDS. update-user-role-operator changes the role with the credential and is PASS. Changing either field without the credential is rejected (FIXED above).
- Status changes in the robustness matrix: wrong-typed or out-of-range input that answered 500 (or, for wrong types, 201) now answers the application's own 400/404. The protocol compares only the status class for these, so none is a regression.

### Findings — final state
| # | Finding | Bucket | Note |
|---|---|---|---|
| 1 | [CRITICAL] AP-01 app.py:13 signing key | proposed | Literal removed; the key now comes from SECRET_KEY. Operator residue: rotate the committed value |
| 2 | [CRITICAL] AP-18 app.py:33-34 debug/dev server | proposed | Applied: debug off by default (APP_DEBUG), default debugger page replaced by the error boundary (observed "Debug mode: off"). Remaining: a production WSGI server, which is a new runtime dependency |
| 3 | [CRITICAL] AP-08 models/user.py:16-25 hash in responses | resolved | Field kept, value masked; value entries HOLD (get-user, login, create-user, update-user) |
| 4 | [CRITICAL] AP-19 flask-cors 4.0.0 | resolved | flask-cors 6.0.0 (major upgrade applied: cors-simple and cors-preflight PASS on the Access-Control-* headers). OSV clean for 6.0.0 (2026-11-04) |
| 5 | [CRITICAL] AP-03 routes/report_routes.py | resolved | Split into report and category routes, controllers and presenters |
| 6 | [CRITICAL] AP-04 /reports/summary | resolved | Guarded with the operator credential; anonymous → 403 (FIXED), operator → PASS |
| 7 | [CRITICAL] AP-04 /reports/user/<id> | proposed | Decided at the gate: D1 = business |
| 8 | [CRITICAL] AP-04 PUT /users/<id> active/role | proposed | Decided at the gate: D2 = privileged, with the human's condition. Applied: changing `role`/`active` requires the operator credential (FIXED ×2); resending the stored values does not (PASS). Remaining, held back by the gate: anonymous password and profile edits of any account, which belong to the identity-model proposal |
| 9 | [CRITICAL] AP-04 DELETE /users/<id> | resolved | Guarded; anonymous → 403 (FIXED), operator → PASS |
| 10 | [CRITICAL] AP-04 no identity model | proposed | Contract-changing (every current client would receive a 401/403) |
| 11 | [CRITICAL] AP-01 seed.py passwords | proposed | Literals removed; passwords come from SEED_*_PASSWORD, random when unset. Operator residue: environments already seeded keep the published passwords |
| 12 | [CRITICAL] AP-01 SMTP credential | proposed | Dead module deleted. Operator residue: rotate the committed SMTP password |
| 13 | [HIGH] AP-06 app.py:9-31 | resolved | create_app() factory; no import-time side effects; clock injected into controllers; seed builds its own app |
| 14 | [HIGH] AP-18 app.py:15 CORS | proposed | Policy now set from CORS_ORIGINS (default `*`, same behaviour). Narrowing it is contract-changing |
| 15 | [HIGH] AP-08 models/user.py:27-32 MD5 | proposed | scrypt (stdlib) with hmac.compare_digest. Legacy MD5 hashes are verified once and rehashed at sign-in. Operator residue: accounts that never sign in keep MD5 hashes |
| 16 | [HIGH] AP-05 task routes | resolved | Routes are parse → controller → render |
| 17 | [HIGH] AP-09 error handling | resolved | One error boundary; intentional error statuses and bodies unchanged (all PASS); 0 answers with status 500 in the replay |
| 18 | [HIGH] AP-11 boundary validation | proposed | Applied: type and range checks for every input of every operation (401/401 ROBUST). Remaining: stricter rules that need a product decision (color format, length limits for description, tags and name) |
| 19 | [HIGH] AP-12 diverged validation | resolved | One field spec and one rule set shared by create and update. The behaviour now follows the create copy (400 instead of 500) |
| 20 | [HIGH] AP-05 user routes | resolved | — |
| 21 | [MEDIUM] AP-20 schema integrity | proposed | Applied after re-audit pass 1: `PRAGMA foreign_keys=ON` per connection (checked: pragma = 1, a dangling insert is refused), and any reference that is sent is checked (FIXED). Remaining: CHECK constraints on `status`/`role`, which need a table rebuild. The Phase 2 orphan claim was corrected (see the finding) |
| 22 | [MEDIUM] AP-19 marshmallow/requests/python-dotenv | resolved | marshmallow and requests removed (no import, no configuration or runtime use); python-dotenv → 1.2.2 and now loads `.env` explicitly |
| 23 | [MEDIUM] AP-13 unpaginated listings | proposed | Contract-changing |
| 24 | [MEDIUM] AP-12 overdue rule and mappings | resolved | Task.is_overdue / overdue_condition; presenters |
| 25 | [MEDIUM] AP-14 datetime.utcnow() | resolved | models/clock.utc_now(); re-audit runs with detectors on show no DeprecationWarning; created_at/due_date format value entries HOLD |
| 26 | [MEDIUM] AP-10 N+1 | resolved | Name lookups use IN queries; grouped counts; overdue counted in SQL; summary figures and user_productivity HOLD sameAsBaseline |
| 27 | [MEDIUM] AP-15 magic values | resolved | Named constants in models |
| 28 | [MEDIUM] AP-17 stale implementations | resolved | utils/, services/ and the unused model methods deleted |
| 29 | [LOW] AP-17 unused imports | resolved | — |
| 30 | [LOW] AP-19 flask 3.0.0 | resolved | flask 3.1.3 (same major) |
| 31 | [LOW] AP-16 naming | resolved | PRIORITY_LABELS; category routes in their own module |
| 32 | [LOW] AP-14 Query.get() | resolved | Session.get via database.get_by_id; no LegacyAPIWarning in either re-audit run |

### Re-audit
- Pass 1 (runtime: boot, seed and the whole surface with detectors on; OSV for the new pins; static sweep of every catalog signal over the refactored tree). It found the 12 items below plus AP-20 (`failed`: foreign keys still not enforced) and the Phase 2 AP-20 false-positive signal.
- Fix loop: AP-20 foreign-key enforcement applied, a late security entry added and captured against the original, then a second full replay (clean).
- Pass 2 (same checks on the final tree, plus the PyPI yanked check for every direct pin: none yanked, 2026-11-04). It found 12 findings, all matching items recorded under Proposed, Not Applied. No `introduced`, no `failed`, no `missed-in-phase-2`.
- Not filed: controllers/user_controller.py `_upgrade_hash` catches broadly, but deliberately. It is narrow in effect, documented and logged (AP-09 de-escalation). The seed's ResourceWarning at exit is the same Flask-SQLAlchemy pooled connection at interpreter exit discarded in Phase 2.

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization — no identity model   (AP-04)
File: routes/user_routes.py:59-67 (login), every route
Reason not applied: Every current client calls every operation anonymously. Requiring credentials would answer 401/403 to all of them, and the sign-in token `fake-jwt-token-<id>` is part of today's response.
Proposed change: Choose the identity model: verified tokens or sessions issued by /login, an ownership policy for tasks, and a role policy for user management. Then require it on business operations. Clients must be updated in step with the change.

### [CRITICAL] Missing or Bypassable Authorization — per-user activity report   (AP-04)
File: routes/report_routes.py:16-18
Reason not applied: Decided at the gate: D1 = business. Closing it would reject clients that read it today.
Proposed change: Scope it to the authenticated principal (or to operators) once the identity model exists.

### [CRITICAL] Missing or Bypassable Authorization — anonymous password/profile edits   (AP-04)
File: routes/user_routes.py:41-46, controllers/user_controller.py:55-85
Reason not applied: D2 = privileged covers only `role`/`active`, and those changes are now operator-only. Password, name and email edits are ordinary profile operations that clients send anonymously today.
Proposed change: Require the account's own verified identity (or an operator) for profile and password changes, as part of the identity model.

### [CRITICAL] Insecure Runtime Configuration — development server   (AP-18)
File: app.py:51-53
Reason not applied: A production WSGI server is a runtime dependency the application does not have today.
Proposed change: Add a WSGI server (for example, one declared in requirements.txt) and start `app:create_app()` with it. The debug flag stays off by configuration.

### [CRITICAL] Hardcoded Secrets — committed signing key   (AP-01)
File: app.py (history: `SECRET_KEY = 'super-secret-key-123'`)
Reason not applied: Operator residue. The value stays in git history.
Proposed change: Generate a new key, set SECRET_KEY in each environment, and treat anything signed with the old key as compromised. When: before the next deploy.

### [CRITICAL] Hardcoded Secrets — seeded accounts with published passwords   (AP-01)
File: seed.py
Reason not applied: Operator residue. Databases seeded by the old script still hold accounts with the passwords published in the repository.
Proposed change: In each existing environment, either reseed with SEED_ADMIN_PASSWORD/SEED_USER_PASSWORD/SEED_MANAGER_PASSWORD set (`python seed.py`, which resets every table) or change those three passwords through PUT /users/<id>. When: immediately, for every environment that ran the old seed.

### [CRITICAL] Hardcoded Secrets — SMTP credential   (AP-01)
File: services/notification_service.py (deleted; still in history)
Reason not applied: Operator residue.
Proposed change: The owner of taskmanager@gmail.com changes its password and revokes any app passwords. When: now.

### [HIGH] Insecure Runtime Configuration — cross-origin policy   (AP-18)
File: config/settings.py:53-57, app.py:33-33
Reason not applied: Narrowing the origins would stop cross-origin browser clients from origins that are not listed.
Proposed change: Set CORS_ORIGINS to the team's list of front-end origins (comma-separated). The code already supports it.

### [HIGH] Unsafe Handling of Credentials — legacy MD5 hashes   (AP-08)
File: models/user.py:69-85
Reason not applied: Operator residue. Hashes upgrade to scrypt only when their owner signs in.
Proposed change: After a reset window (for example, 30 days), force a password reset for every account whose `password` does not start with `scrypt$`. The SQL `SELECT id FROM users WHERE password NOT LIKE 'scrypt$%'` lists them.

### [HIGH] Missing Boundary Validation — stricter rules   (AP-11)
File: routes/category_routes.py:7-17, routes/task_routes.py:9-18
Reason not applied: Rejecting values clients send today (any color string, unbounded description or tag lengths) needs a product decision.
Proposed change: Decide on and apply `#RRGGBB` for color, and maximum lengths matching the columns (name 100, description 300, tags 500).

### [MEDIUM] Missing Schema-Level Integrity Constraints — closed sets as free text   (AP-20)
File: models/task.py (status), models/user.py (role)
Reason not applied: SQLite cannot add a CHECK constraint to an existing table, so it needs a table rebuild migration over existing data.
Proposed change: First count violations (`SELECT COUNT(*) FROM tasks WHERE status NOT IN ('pending','in_progress','done','cancelled')`, and the same for users.role). Then rebuild each table with the CHECK constraint inside one transaction. Until then, every write goes through Task.check_status / User.check_role.

### [MEDIUM] Unbounded Resources — unpaginated listings   (AP-13)
File: routes/task_routes.py:24-26, routes/user_routes.py:26-28, routes/category_routes.py:23-26
Reason not applied: A default page size would change what clients receive today.
Proposed change: Add `limit`/`offset` (or a cursor) with a bounded maximum. Agree on the default with the clients (for example, no limit unless requested, as an opt-in first step).

## Verification Coverage
Re-audit: complete. Every catalog check ran on the final tree: forced-deprecation runs of boot, seed and the whole surface; OSV.dev for every installed package (2026-11-04); the PyPI yanked check for every direct pin (2026-11-04).
Replay: the baseline plus two full replays, with destructive entries each on a fresh boot.
DEGRADED — three transformation effects have no harness entry, so the replay lines do not cover them. What was observed directly is stated with each; none is counted as passed:
  - AP-19 private-network header: a header-only effect, and the baseline preflight did not send the private-network request header. A direct preflight against a refactored run answered `Access-Control-Allow-Private-Network: false` (the original answered `true`). → UNVERIFIED by the harness.
  - AP-20 per-connection enforcement: a script in a refactored run copy read `PRAGMA foreign_keys` = 1, and a direct dangling insert was refused. → UNVERIFIED by the harness. The API-level rejection is covered (create-task-dangling-user FIXED).
  - AP-08 legacy-MD5 verification and rehash-on-login: every replay seeds a fresh database with scrypt hashes, so this path never ran. → UNVERIFIED.
Still open from Phase 2 (it no longer affects the final tree): the AP-14 Layer 2 PyPI yank check was never run for the original's pins. All of them were replaced or removed, and the final pins were checked.
Phase 2 audit defect, recorded: the AP-20 description asserted an observed orphan that was never observed (correction under that finding). It is not counted as missed-in-phase-2, because it is a precision error, not a recall one.
Scratch root (environment scratch directory) deleted at the end of the run, after confirming that no container labelled `refactor-arch.run=202611050130-8146e33a` was left.
Fixtures by reference: OPERATOR_TOKEN, SEED_ADMIN_PASSWORD, NEW_USER_PASSWORD, SHORT_PASSWORD, WRONG_PASSWORD
================================
