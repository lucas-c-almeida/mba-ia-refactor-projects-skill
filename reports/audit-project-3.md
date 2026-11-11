## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        D:/Study/MBA FullCycle/mba-ia-refactor-projects-skill/.worktrees/r8-p3/task-manager-api
Language:      Python (runtime version not declared by the project; 15 .py files)
Framework:     Flask 3.0.0 (pinned in requirements.txt; no lockfile)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0
Domain:        Task management API — users, task categories, tasks with status/priority/due date, and reports
App type:      HTTP service (JSON API, 21 routes) + seed script
Architecture:  Nominal MVC — models/, routes/, services/, utils/ exist, but routes hold persistence, business rules and serialization; services/ and most of utils/ are unused
Source files:  15 files analyzed (*.py; excluded: .claude/, reports/, __pycache__, VCS dir, non-code files)
DB tables:     users, categories, tasks (SQLite via Flask-SQLAlchemy, created by db.create_all())
Boot:          python seed.py, then python app.py (cwd = run copy)
Port:          5000, fixed in app.py:34 (app.run(debug=True, host='0.0.0.0', port=5000))
Runtime env:   Python 3.13 (official image, matches host 3.13.2; no version declared), deps from requirements.txt installed in the container
Isolation:     container (docker 28.5.2, image python:3.13-slim)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.1.8 resolved at install)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-11-10 23:12
Mode:    full
Confirmation: human-confirmed: y; D1=business
Tree:    clean at e97e998
Runtime: installed the declared dependencies from requirements.txt into the container refactor-arch-task-manager-api-202611110155-8bb272fa-1 (site-packages of python:3.13-slim), outside the target
Isolation: container (docker 28.5.2, image python:3.13-slim)
Scratch: environment scratch directory — C:\Users\lucas\AppData\Local\Temp\claude\b247d7bb4f414394\ba923cae-119c-41c1-b0ad-d78f9f1be3ab\scratchpad\refactor-arch-task-manager-api-202611110155-8bb272fa  (protocol §1.1)

## Summary
CRITICAL: 10 | HIGH: 6 | MEDIUM: 10 | LOW: 5

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:13-13
Description: The framework's signing key is set to a literal: `app.config['SECRET_KEY'] = 'super-secret-key-123'`, on the module every boot and the seed script import. Aggravating per the catalog: it is a signing/session key, so anything Flask signs with it (sessions, any future signed token) is forgeable by whoever reads the repository.
Impact: The key is public to everyone with repository access and cannot be rotated without a code change and deploy; it stays in history forever.
Recommendation: Read it from the environment (empty or placeholder treated as unset; generate a random per-process key when unset so nothing signs with a known value). See RP-01.
Contract: safe

### [CRITICAL] Insecure Runtime Configuration — debugger exposed on all interfaces   (AP-18)
File: app.py:33-34
Description: The documented start path (`python app.py`, README.md:10) runs `app.run(debug=True, host='0.0.0.0', port=5000)`: debug mode switched on by a literal, bound to every interface, on the framework's development server with no production server declared anywhere. Observed in the run copy: `POST /tasks` with `"priority": "high"` and `GET /tasks/search?priority=abc` both answered `500 text/html` with the Werkzeug Debugger page carrying the full traceback (`TypeError: '<' not supported between instances of 'str' and 'int'`, `ValueError: invalid literal for int()`). Escalated to CRITICAL: the debugger offers interactive code evaluation and the listener is reachable from outside the host; its error output exposes source paths and code.
Impact: Any network client that can trigger an unhandled error reaches an in-browser debugger (PIN-protected code execution) and reads source fragments and internal paths; the development server is not built for production traffic.
Recommendation: Take debug and the bind address from configuration with safe defaults (debug off), and register the centralized error handler so no default error page answers (RP-17, RP-09). Running a production WSGI server is a new runtime dependency and is proposed.
Contract: safe for the debug flag, bind address and default error page (status 500 kept); contract-changing for adopting a production server (new runtime dependency — proposed).

### [CRITICAL] Unsafe Handling of Credentials — unsalted MD5 password hashing   (AP-08)
File: models/user.py:27-32
Description: `set_password` stores `hashlib.md5(pwd.encode()).hexdigest()` and `check_password` compares with `==`: a fast general-purpose digest, no salt, non-constant-time comparison. Escalated to CRITICAL: unsalted MD5 of short passwords (the API accepts 4 characters, routes/user_routes.py:64) is recoverable by lookup table, so stored passwords are effectively recoverable — and the hash is also returned by the API (see the AP-08 HIGH finding).
Impact: One database read, or one `GET /users/<id>` response, yields every user's password within seconds of offline cracking; credentials reused elsewhere are compromised too.
Recommendation: Hash with a purpose-built KDF already available through the installed framework stack (werkzeug.security), verify legacy MD5 hashes once at sign-in and rehash on success, compare in constant time. Accounts that never sign in keep MD5 until an operator reset (operator residue, proposed). See RP-08.
Contract: safe (the stored value changes format; the field and its type stay).

### [CRITICAL] God Module — reports and category CRUD in one route module   (AP-03)
File: routes/report_routes.py:1-223
Description: One module holds two unrelated domain concepts with every responsibility mixed: report endpoints (lines 12-155: delivery + persistence queries + business rules — overdue, completion rate, "high priority" threshold — + presentation) and category CRUD (lines 157-223: delivery + persistence + serialization), all registered on a blueprint named `reports` (a file placed where its name says it does not belong — AP-16, reported here). `summary_report` (lines 13-101) is an 89-line unit with conditionals nested four deep (lines 33-37). Precedence rule 1 (several unrelated concepts) makes this AP-03, not AP-05; default severity kept.
Impact: Changing category handling risks the reports and vice versa; nothing in the module can be tested without the Flask app and the database.
Recommendation: Split into a categories controller/route module and a reports controller backed by a report service and repository queries. See RP-03.
Contract: safe (routes, methods and bodies unchanged).

### [CRITICAL] Missing Authorization — management rollup per user open to anyone   (AP-04)
File: routes/report_routes.py:12-101
Description: `GET /reports/summary` returns, with no credential, a `user_productivity` rollup naming every user with their task totals and completion rate (lines 53-68), plus global overdue lists. A per-principal management aggregate is a privileged operation (04-architecture-guidelines.md §6); the application has no identity model (the login token is never verified anywhere).
Impact: Any anonymous caller ranks every user by productivity — personal performance data no single principal needs about the others.
Recommendation: Guard the operation with an operator credential read from configuration (constant-time comparison, closed by default: `403` when unset, empty or placeholder). See RP-04.
Contract: safe (privileged operation — only non-operators are rejected).

### [CRITICAL] Missing Authorization — per-user report open to anyone   (AP-04)
File: routes/report_routes.py:103-155
Description: `GET /reports/user/<id>` returns any user's name, email and task statistics (done/pending/overdue/high-priority counts, completion rate) for an id taken from the path, with no credential. Whether this is a management rollup or a profile read is ambiguous under §6 — listed as D1 under `## Classification Decisions`.
Impact: Any caller enumerates ids and reads every user's email and work statistics.
Recommendation: If privileged (D1=privileged): guard with the operator credential (RP-04). If business: propose the identity model with an ownership check.
Contract: decided at the gate (D1) — privileged: safe (guarded); business: contract-changing (every current anonymous client would be rejected).

### [CRITICAL] Missing Authorization — account takeover and deletion by id   (AP-04)
File: routes/user_routes.py:92-151
Description: With no identity model, `PUT /users/<id>` changes the account's password (lines 114-117), sign-in email (105-112), role (119-122, `admin` accepted) and enabled flag (124-125) for any id in the path, and `DELETE /users/<id>` (134-151) deletes the account and all its tasks — no credential on any path. These are privileged fields/operations (§6: take over, lock or delete an account by request id). The ordinary `name` field (102-103) stays with the business finding below. Flagged maximum urgency: destructive and privilege-escalating.
Impact: Any anonymous caller takes over an account (sets its password, then signs in as it), grants itself `admin`, locks users out, or deletes them with their data.
Recommendation: Split by field: a request that would change `password`, `email`, `role` or `active` (a value different from the stored one; the password verified against the stored hash) needs the operator credential from configuration, checked before any write; `DELETE` needs it always; name edits and resends of stored values stay open. See RP-04.
Contract: safe (privileged — only non-operators are rejected; ordinary edits unaffected).

### [CRITICAL] Missing Authorization — no identity model on business operations   (AP-04)
File: routes/user_routes.py:185-211
Description: `POST /login` issues `'fake-jwt-token-' + str(user.id)` (line 210) — a predictable value with no signature or expiry — and no operation ever reads or verifies it. Every task, category and user listing/CRUD route (routes/task_routes.py:11-299, routes/report_routes.py:157-223, routes/user_routes.py:10-90, 153-183) is therefore anonymous, and `POST /users` trusts a `role` taken from the body (lines 52, 71-72), so anyone registers as `admin`.
Impact: Any caller reads, edits and deletes every task and category and lists every account; roles mean nothing.
Recommendation: Introduce an identity model (verified, expiring tokens; principals owning tasks; registration not choosing its role) — a product decision. See RP-04.
Contract: contract-changing: every current client is anonymous and would receive `401`; registration would stop honouring `role`.

### [CRITICAL] Hardcoded Secrets and Credentials — seeded accounts with known passwords   (AP-01)
File: seed.py:16-35
Description: The seed script — the documented setup command (README.md:9, "rode-o antes do primeiro boot") that writes the runtime database — creates three accounts with literal passwords `'1234'` (an `admin`), `'abcd'` and `'pass'` (lines 19, 26, 33).
Impact: Every environment provisioned the documented way has an admin account whose password is in the repository.
Recommendation: Take seed passwords from the environment, or generate random ones and print them once; never a literal. Databases already seeded keep the known passwords until an operator resets them (operator residue, proposed). See RP-01.
Contract: safe (seed script is not part of the request surface; its output changes only in values).

### [CRITICAL] Hardcoded Secrets and Credentials — SMTP account in source   (AP-01)
File: services/notification_service.py:7-10
Description: `NotificationService.__init__` holds the SMTP host, user `'taskmanager@gmail.com'` and password `'senha123'` as literals. The class is never imported (dead code, see AP-17), but the credential is committed. Aggravating: it is a credential to a third-party system.
Impact: Anyone with repository access can use the mail account; it must be considered compromised.
Recommendation: Delete the dead class (RP-16); any future mail configuration comes from the environment (RP-01). Rotating the committed password is an operator action (proposed residue).
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: app.py:9-31
Description: The application object, its configuration literals (database URI, secret key), CORS, blueprint registration and `db.create_all()` (lines 30-31) all run at import time of `app.py`; there is no application factory, so `seed.py:2` importing `app` creates the database file as a side effect. Business rules call the system clock directly (`datetime.utcnow()` in routes/task_routes.py:31, 72, 285; routes/report_routes.py:35, 42, 45, 133; routes/user_routes.py:172).
Impact: No test can load the app with another database or configuration; importing the module touches the filesystem; time-dependent rules (overdue) cannot be tested deterministically.
Recommendation: Application factory that takes configuration, a single composition root for extensions and blueprints, and an injectable clock for the overdue rule. See RP-06.
Contract: safe

### [HIGH] Sensitive Data in Responses and Logs — password hash returned   (AP-08)
File: models/user.py:16-25
Description: `User.to_dict()` serializes the whole row including `'password': self.password` (line 21). It feeds `GET /users/<id>`, `POST /users`, `PUT /users/<id>` and `POST /login`; observed in the run copy: `GET /users/1` returned `"password": "81dc9bdb52..."`. Second site: `print(f"ERRO: {str(e)}")` (routes/user_routes.py:89) writes the raw driver error, which for a failed INSERT carries the bound parameters, hash included, to stdout.
Impact: Every API client receives every requested user's password hash, which with unsalted MD5 is the password (see the CRITICAL AP-08).
Recommendation: Mask the field's value while keeping the field and its type; log errors without bound parameters. See RP-08.
Contract: safe (masking keeps field and type; removing the field would be contract-changing and is not proposed).

### [HIGH] Known-Vulnerable Dependency — flask-cors 4.0.0   (AP-19)
File: requirements.txt:3-3
Description: OSV.dev (queried 2026-11-10) returns for flask-cors 4.0.0: GHSA-hxwh-jpp2-84pm / CVE-2024-6221 (HIGH — `Access-Control-Allow-Private-Network` set to true by default; fixed 4.0.2), GHSA-84pr-m4jr-85g5 / CVE-2024-1681 (MODERATE, log injection at debug log level; fixed 4.0.1), and GHSA-43qf-4rqw-9q2g / CVE-2024-6866, GHSA-7rxf-gvfg-47g4 / CVE-2024-6839, GHSA-8vgw-p6qm-5gr7 / CVE-2024-6844 (MODERATE, path-matching flaws; fixed 6.0.0). `CORS(app)` (app.py:15) applies the extension to every route; reachability of the private-network header was not established, so the HIGH default is kept.
Impact: A published, documented weakness in the cross-origin layer of every response.
Recommendation: Upgrade within the major line to 4.0.2 (fixes the HIGH and the log-injection advisory). The three path-matching advisories need 6.0.0, a major upgrade: apply only if the replay covers the CORS contract headers (Origin and preflight entries), otherwise propose. See RP-18.
Contract: safe for 4.0.2 (same major); 6.0.0 safe only with CORS headers covered by the replay, else contract-changing.

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: routes/task_routes.py:13-63
Description: `get_tasks` wraps its whole body in a bare `except:` returning `500 {'error': 'Erro interno'}`, absorbing every failure with no logging. The same shape — bare `except:` with a per-handler error body — repeats at routes/task_routes.py:137, 151, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221, while other failures are not caught at all. No error handler is registered anywhere; observed in the run copy, an unhandled error answers with the framework's default (debugger) page (see AP-18).
Impact: Real failures disappear without a trace; malformed input crashes some handlers and is silently absorbed in others, so callers cannot tell "bad request" from "database down".
Recommendation: A centralized error handler that logs and maps exceptions; narrow except clauses only where a specific failure is expected; keep every intentional status and body. See RP-09.
Contract: safe (intentional error statuses and bodies preserved; the default page replaced, its status kept).

### [HIGH] Business Logic in the Delivery Layer — task routes   (AP-05)
File: routes/task_routes.py:85-223
Description: `create_task` (85-154, 70 lines) and `update_task` (156-223, 68 lines) parse the request, validate domain rules (title length, status set, priority range, referenced user/category existence), convert dates and tags, write through `db.session` and serialize — all in the handler. The overdue rule is computed in handlers (30-39, 71-80, 283-287) with four-deep nesting, `get_tasks` hand-serializes rows (17-28), and `task_stats` aggregates in the handler (273-299). There is no task service: `services/` holds only an unused notification class (nominal layering). One domain concept below the AP-03 threshold (299 lines) → AP-05.
Impact: Task rules cannot be tested or reused without an HTTP request and a database; every rule change edits handlers.
Recommendation: Controller → service → repository split for tasks, with the overdue rule on the model/service. See RP-05.
Contract: safe

### [HIGH] Business Logic in the Delivery Layer — user routes   (AP-05)
File: routes/user_routes.py:42-151
Description: `create_user` (42-90) and `update_user` (92-132) hold validation rules (email regex, password length, role set, email uniqueness) and persistence; `delete_user` (134-151) runs a multi-step cascade workflow (delete every task, then the account) in the handler; `get_user_tasks` (153-183) re-implements task serialization and the overdue rule.
Impact: Account rules live in HTTP handlers and are duplicated, so a second entry point (CLI, admin job) would have to copy them.
Recommendation: User service and repository; handlers only map request → service → response. See RP-05.
Contract: safe

### [MEDIUM] Missing Schema-Level Integrity Constraints   (AP-20)
File: models/task.py:11-14
Description: `status` is free text (`String(50)`) and `priority` an unconstrained integer, though the application treats them as a closed set and a 1-5 range; `users.role` (models/user.py:12) is free text too. `user_id`/`category_id` declare foreign keys, but SQLite enforces them only with `PRAGMA foreign_keys=ON`, which the application never enables, so the declarations are inert. (Orphans were checked and not observed: deleting a category in the run copy made the ORM null its tasks' `category_id`; deleting a user deletes its tasks.)
Impact: Any path that skips the route checks (the seed script, a future job, a direct SQL fix) can store an unknown status, priority 0 or a dangling reference, and every reader then misbehaves.
Recommendation: CHECK constraints for status, priority and role, and enable foreign-key enforcement on each connection. Existing databases need a migration (operator residue). See RP-19.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency — unused or unreachable packages   (AP-19)
File: requirements.txt:4-6
Description: OSV.dev (queried 2026-11-10): marshmallow 3.20.1 — GHSA-428g-f7cq-pgp5 / CVE-2025-68480 (MODERATE, DoS in `Schema.load(many=True)`; fixed 3.26.2); requests 2.31.0 — GHSA-9hjg-9r4m-mvj7 / CVE-2024-47081, GHSA-9wx4-h78v-vm56 / CVE-2024-35195, GHSA-gc5v-m9x4-r6x2 / CVE-2026-25645 (all MODERATE; fixed 2.32.4 / 2.32.0 / 2.33.0); python-dotenv 1.0.0 — GHSA-mf9w-mj56-hr94 / CVE-2026-28684 (MODERATE, symlink following in `set_key`/`unset_key`; fixed 1.2.2). marshmallow and requests are never imported (AP-17); python-dotenv is loaded implicitly by `app.run()` to read `.env`, but `set_key`/`unset_key` are never called. MEDIUM: moderate advisories, vulnerable features unused.
Impact: Installed code with public advisories that the application does not need; any future use inherits them.
Recommendation: Remove marshmallow and requests from the manifest (unused); upgrade python-dotenv to 1.2.2 (same major). See RP-18, RP-16.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop — reports and categories   (AP-10)
File: routes/report_routes.py:53-68
Description: `summary_report` runs `Task.query.filter_by(user_id=u.id).all()` once per user inside the loop over `User.query.all()`; `get_categories` issues one `COUNT` per category inside its loop (157-165); `summary_report` also issues nine separate count queries (15-28) and loads the whole tasks table into memory to count overdue tasks (30-43).
Impact: Report latency grows with users × tasks; the endpoint degrades with data volume and holds connections longer under load.
Recommendation: Grouped aggregate queries (`GROUP BY user_id, status`, `GROUP BY category_id`) and an overdue filter in SQL. See RP-10.
Contract: safe

### [MEDIUM] Unbounded Resources — whole-table listings   (AP-13)
File: routes/task_routes.py:11-14
Description: `GET /tasks` returns `Task.query.all()` with no limit or pagination; so do `GET /users` (routes/user_routes.py:12), `GET /categories` (routes/report_routes.py:159) and `GET /tasks/search` (routes/task_routes.py:266). The seed data itself records the gap ("Endpoints retornam todos os registros", seed.py:70).
Impact: Response size and memory grow with the table; one request can serialize the whole database.
Recommendation: Add pagination with a bounded page size. Changing the default result set is a contract change, so it is proposed. See RP-13.
Contract: contract-changing: clients reading the full list in one call would receive a page.

### [MEDIUM] Duplicated Logic — serialization and validation rules   (AP-12)
File: routes/task_routes.py:17-28
Description: Task serialization is written by hand in `get_tasks` (17-28), again with a different field set in `get_user_tasks` (routes/user_routes.py:162-169, no `user_id`, `updated_at`, `tags`), alongside `Task.to_dict()` (models/task.py:23-36). The status set is spelled out in routes/task_routes.py:110 and 177, models/task.py:39 and utils/helpers.py:75 and 110; the priority range in routes/task_routes.py:113, 182 and models/task.py:46; title length in routes/task_routes.py:96-100, 167-170 and utils/helpers.py:64; the email regex in routes/user_routes.py:61, 106 and utils/helpers.py:21; status counts in routes/task_routes.py:275-279 and routes/report_routes.py:19-22.
Impact: Every rule change has to be repeated in up to four places; the two hand-written task shapes already differ.
Recommendation: One serializer per resource (keeping each endpoint's current field set) and one validation module for task/user rules. See RP-12.
Contract: safe

### [MEDIUM] Duplicated Logic — the overdue rule   (AP-12)
File: routes/task_routes.py:30-39
Description: The rule "due date in the past and status not done/cancelled" is re-implemented at routes/task_routes.py:30-39, 71-80, 284-287; routes/user_routes.py:171-180; routes/report_routes.py:34-37 and 132-135 — while `Task.is_overdue()` (models/task.py:50-60) implements it and is never called.
Impact: A change to what "overdue" means (time zones, a new terminal status) must be made in seven places; missing one makes the reports disagree with the task list.
Recommendation: One rule on the model/service, used everywhere (and computed in SQL for counts). See RP-12.
Contract: safe

### [MEDIUM] Deprecated API — datetime.utcnow()   (AP-14)
File: routes/task_routes.py:31-31
Description: Tier A — observed 2026-11-10 with `-X dev` and `PYTHONWARNINGS=always::DeprecationWarning` on Python 3.13: "DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)." Raised at routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; seed.py:66, 67, 69, 70, 74; and through the column defaults `default=datetime.utcnow` (models/task.py:15-16, models/user.py:14, models/category.py:11) on every insert/update.
Impact: Removal is scheduled upstream; the next Python upgrade that drops it breaks every handler that checks overdue and every insert.
Recommendation: Modern equivalent named by the warning: `datetime.now(datetime.UTC)`. Stored values are naive, so use one clock helper returning `datetime.now(UTC).replace(tzinfo=None)` to keep comparisons and the serialized format identical. See RP-14.
Contract: safe (values and their string format unchanged).

### [MEDIUM] N+1 and Query-Inside-Loop — task listing   (AP-10)
File: routes/task_routes.py:41-57
Description: For every task, `get_tasks` issues `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` inside the loop (observed: one `Query.get` warning pair per task in the run). `GET /users` touches the lazy `u.tasks` relation per user (routes/user_routes.py:22), and `task_stats` loads every task to count overdue ones in Python (routes/task_routes.py:281-287).
Impact: `GET /tasks` costs 1 + 2N queries; it slows linearly with the task count.
Recommendation: Eager-load or join the user and category names; count overdue in SQL. See RP-10.
Contract: safe

### [MEDIUM] Missing Boundary Validation — task inputs   (AP-11)
File: routes/task_routes.py:85-114
Description: `create_task` uses `priority` (line 113), `title` (96-100) and `tags` (140-144) with no type check: observed in the run copy, `"priority": "high"` answered `500` (TypeError). `update_task` repeats the pattern (166-184: `len(data['title'])` on a non-string, `data['priority'] < 1` on a non-number), and `search_tasks` calls `int(priority)`/`int(user_id)` on query strings (260-264): observed `GET /tasks/search?priority=abc` → `500` (ValueError). A non-object JSON body makes `data.get` fail (`AttributeError`).
Impact: Malformed input is a server error instead of a client error; with debug on it also opens the debugger (AP-18).
Recommendation: Type and range checks at the boundary for every field each task operation reads, answering the application's own `400`. See RP-11.
Contract: safe (only requests no legitimate client sends change from `500` to `400`).

### [MEDIUM] Missing Boundary Validation — user and category inputs   (AP-11)
File: routes/user_routes.py:92-125
Description: `update_user` assigns `name` and `active` unchecked (103, 125) and runs `re.match`/`len` on `email`/`password` without type checks (106, 115): observed `PUT /users/1` with `"active": "no"` → `500 {"error": "Erro ao atualizar"}`. `create_user` does the same for `name`, `email`, `password` (49-65). `update_category` dereferences `request.get_json()` without the presence check the other handlers have (routes/report_routes.py:196-202), and `color`/`name` lengths are never checked against the 7/100-character columns (routes/report_routes.py:178-180) — `is_valid_color` exists in utils/helpers.py:52 and is never used.
Impact: Wrong-typed input crashes the handler or is silently absorbed as a 500.
Recommendation: Boundary validation of type, length and format for every user and category field. See RP-11.
Contract: safe

### [LOW] Known-Vulnerable Dependency — flask 3.0.0   (AP-19)
File: requirements.txt:1-1
Description: OSV.dev (queried 2026-11-10): GHSA-68rp-wp8r-4726 / CVE-2026-27205, severity LOW — `Vary: Cookie` not set for some forms of session access; fixed 3.1.3. The application never touches `session`, so the vulnerable path is not reached.
Impact: Low today; any future session use behind a caching proxy would inherit it.
Recommendation: Upgrade to flask 3.1.3 (same major). See RP-18.
Contract: safe

### [LOW] Magic Values   (AP-15)
File: routes/report_routes.py:24-28
Description: Priority numbers 1-5 are mapped to labels by position (`'critical': p1 … 'minimal': p5`, lines 84-88), "high priority" is `t.priority <= 2` (line 129) and the recent-activity window is a bare `timedelta(days=7)` (line 45); the password minimum `4` (routes/user_routes.py:64, 115) and title bounds `3`/`200` are inline literals while `utils/helpers.py:110-116` defines named constants nobody imports.
Impact: The meaning of each number lives only in the reader's head; changing a threshold means hunting literals.
Recommendation: Named constants in one domain module. See RP-15.
Contract: safe

### [LOW] Deprecated API — Query.get()   (AP-14)
File: routes/task_routes.py:42-42
Description: Tier A — observed 2026-11-10 (SQLAlchemy 2.1.8 via Flask-SQLAlchemy 3.1.1): "LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get() (deprecated since: 2.0)". Raised at routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213. LOW: drop-in successor, no behaviour risk.
Impact: Legacy construct on an unpinned transitive dependency; a future SQLAlchemy release can drop it.
Recommendation: Modern equivalent named by the warning: `Session.get()` — `db.session.get(Model, id)`. See RP-14.
Contract: safe

### [LOW] Dead Code — unused notification service   (AP-17)
File: services/notification_service.py:1-48
Description: `NotificationService` (send_email, notify_task_assigned, notify_task_overdue, get_notifications and an in-memory `notifications` list) is never imported anywhere; it also carries the committed SMTP credential (AP-01) and opens SMTP connections with no timeout and no `finally`.
Impact: Readers assume notifications exist; the dead class keeps a credential and unsafe I/O in the tree.
Recommendation: Delete it (git keeps it). See RP-16.
Contract: safe

### [LOW] Dead Code — unused helpers, imports, methods and dependencies   (AP-17)
File: utils/helpers.py:1-116
Description: Nothing in `utils/helpers.py` is used: `format_date` and `calculate_percentage` are imported by routes/report_routes.py:7 and never called; the rest (validate_email, sanitize_string, generate_id, log_action, parse_date, is_valid_color, process_task_data, the constants at 110-116) is never imported. Also dead: unused imports (app.py:7 `os, sys, json`; routes/task_routes.py:7 `json, os, sys, time`; routes/user_routes.py:6 `hashlib, json`; routes/report_routes.py:8 `json`; models/task.py:3 `json`), never-called methods (`Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin`), and the declared dependencies `marshmallow` and `requests`, never imported. (`python-dotenv` is not dead: `app.run()` loads `.env` through it.)
Impact: A second, divergent copy of the task validation (it strips titles and accepts `dd/mm/YYYY` dates, the routes do not) invites edits to the wrong one.
Recommendation: Delete the dead code and unused manifest entries, keeping only what the refactoring reuses. See RP-16.
Contract: safe

## Signal Ledger

| Entry | Signal | Examined | Occurrences | Outcome |
|---|---|---|---|---|
| AP-01 | Literal assigned to secret-like identifier | all source files | 3: app.py:13; services/notification_service.py:10; (email_user :9) | finding: [CRITICAL] AP-01 app.py:13-13; [CRITICAL] AP-01 services/notification_service.py:7-10 |
| AP-01 | Credential literals in seed/fixture/bootstrap data | seed.py, README.md | 3: seed.py:19, 26, 33 | finding: [CRITICAL] AP-01 seed.py:16-35 |
| AP-01 | Connection URL with inline credentials | all source files | 0 (app.py:11 `sqlite:///tasks.db` has none) | none |
| AP-01 | High-entropy / prefixed credential literal | all source files | 0 | none |
| AP-01 | Framework signing key set to a literal | app.py | 1: app.py:13 | finding: [CRITICAL] AP-01 app.py:13-13 |
| AP-01 | Credential-bearing file committed | target tree (ls -la) | 0 (no .env, *.pem, *.key) | none |
| AP-01 | Config read with a real secret as fallback | all source files | 0 (no environment reads at all) | none |
| AP-02 | External value reaching a driver call by concatenation | routes/*.py | 0 — all access through ORM query builder with bound parameters | none |
| AP-02 | Interpolation markers inside a statement string | all source files | 1: routes/task_routes.py:252-253 `f'%{query}%'` | discarded: builds the LIKE pattern value, which SQLAlchemy binds as a parameter; no statement text is built |
| AP-02 | ORM escape hatch with input-built string | all source files | 0 | none |
| AP-02 | Dynamic identifiers from input | all source files | 0 | none |
| AP-02 | Shell/process execution with input | all source files | 0 | none |
| AP-02 | Unsafe deserialization / template from input | all source files | 0 | none |
| AP-02 | Path traversal | all source files | 0 | none |
| AP-03 | Module with ≥3 responsibility categories | all modules | 3: routes/report_routes.py, routes/task_routes.py, routes/user_routes.py | finding: [CRITICAL] AP-03 routes/report_routes.py:1-223; task/user routes are single-concept below threshold → [HIGH] AP-05 (precedence rule 2) |
| AP-03 | >300-400 lines with ≥2 categories | all modules | 0 (largest: routes/task_routes.py, 299 lines) | none |
| AP-03 | Unit >50 lines / nesting >3 / >5 params | routes/*.py | 4: report_routes.py:13-101 (89 lines); task_routes.py:12-63, 86-154, 157-223 | finding: [CRITICAL] AP-03 (report_routes); [HIGH] AP-05 routes/task_routes.py:85-223 |
| AP-03 | Several unrelated domain concepts in one file | all modules | 1: routes/report_routes.py (reports + categories) | finding: [CRITICAL] AP-03 routes/report_routes.py:1-223 |
| AP-03 | Low-cohesion class | models/*.py, services/*.py | 0 | none |
| AP-03 | Leftover-bin helpers module | utils/helpers.py | 1 | discarded as AP-03: the module is entirely unused → [LOW] AP-17 utils/helpers.py:1-116 |
| AP-03 | Very high afferent coupling | import graph | 0 (database.py imported widely but holds only the db handle) | none |
| AP-04 | Principal-scoped entry with no auth/ownership check | all routes | 21 routes | finding: [CRITICAL] AP-04 routes/user_routes.py:185-211 (business) and the privileged findings below |
| AP-04 | Lookup filtered only by input id (IDOR) | all routes | 14 `Query.get(<path id>)` sites | finding: [CRITICAL] AP-04 routes/user_routes.py:185-211 (no principal exists to scope by) |
| AP-04 | Authorization only in the delivery layer, bypassable | all routes | 0 (no authorization anywhere) | none |
| AP-04 | Role/permission taken from request and trusted | routes/user_routes.py | 2: :52/71-72 (POST role), :119-122 (PUT role) | finding: [CRITICAL] AP-04 routes/user_routes.py:185-211 (POST); [CRITICAL] AP-04 routes/user_routes.py:92-151 (PUT) |
| AP-04 | Token accepted without verification | all source files | 1: routes/user_routes.py:210 token issued, never verified anywhere | finding: [CRITICAL] AP-04 routes/user_routes.py:185-211 |
| AP-04 | Check written but never reached | all source files | 1: `User.is_admin` (models/user.py:34) never called | discarded as AP-04: it is not a guard on any path → [LOW] AP-17 utils/helpers.py:1-116 |
| AP-04 | Commented-out / flag-disabled guard | all source files | 0 | none |
| AP-04 | Privileged operation with no guard | all routes | 4: DELETE /users/<id>, PUT /users/<id> privileged fields, GET /reports/summary, GET /reports/user/<id> (ambiguous) | finding: [CRITICAL] AP-04 routes/user_routes.py:92-151; [CRITICAL] AP-04 routes/report_routes.py:12-101; [CRITICAL] AP-04 routes/report_routes.py:103-155 (D1). GET /tasks/stats discarded: count of records by state is a plain read (§6) |
| AP-05 | Domain decisions in handlers | routes/*.py | 3 modules | finding: [HIGH] AP-05 routes/task_routes.py:85-223; [HIGH] AP-05 routes/user_routes.py:42-151; report_routes covered by AP-03 |
| AP-05 | Persistence calls inside handlers | routes/*.py | every handler | same findings |
| AP-05 | Handler >30 lines not simply mapping | routes/*.py | 8 (e.g. task_routes.py:86-154, user_routes.py:43-90, report_routes.py:13-101) | same findings / AP-03 |
| AP-05 | Request objects deep in the stack | all source files | 0 (request used only in handlers) | none |
| AP-05 | Same rule in two handlers | routes/*.py | overdue ×7, validation ×2-4 | finding: [MEDIUM] AP-12 (both) |
| AP-05 | Pass-through / nominal service layer | services/, utils/ | 1: no task/user service; services/ holds only an unused class | finding: [HIGH] AP-05 routes/task_routes.py:85-223 (described) |
| AP-06 | Unit constructs its own collaborators | all source files | 1: services/notification_service.py:15 opens SMTP itself | discarded: dead class → [LOW] AP-17 services/notification_service.py:1-48 |
| AP-06 | Import-time side effects | all modules | 1: app.py:9-31 (`db.create_all()` at import; seed.py:2 imports it) | finding: [HIGH] AP-06 app.py:9-31 |
| AP-06 | No composition root | app.py | 1 | finding: [HIGH] AP-06 app.py:9-31 |
| AP-06 | Direct clock calls in business rules | routes/*.py | 10 sites (task_routes.py:31…; report_routes.py:35…) | finding: [HIGH] AP-06 app.py:9-31 (described) |
| AP-06 | Concrete driver/ORM in domain layer | models/*.py | models are ORM classes (expected in this MVC target) | discarded: the model layer is the persistence layer here, not a separate domain layer |
| AP-06 | Configuration read at point of use | all source files | 0 environment reads | none (configuration is literal — AP-01/AP-18) |
| AP-07 | Module-level variable mutated from several places | all modules | 0 (`app`, `db`, blueprints are framework singletons, set once) | none |
| AP-07 | Request-scoped data stored globally | all modules | 0 | none |
| AP-07 | In-memory collection as store of record | all modules | 1: services/notification_service.py:6 `self.notifications` | discarded: class never instantiated → [LOW] AP-17 services/notification_service.py:1-48 |
| AP-07 | Mutable default / shared class attribute | all modules | 0 | none |
| AP-07 | Cache/pool with no lifecycle | all modules | 0 | none |
| AP-07 | Monkey-patched built-in | all modules | 0 | none |
| AP-07 | In-process id counter | all modules | 0 | none |
| AP-08 | Reversible password storage | models/user.py | 0 | none |
| AP-08 | Fast digest for passwords | models/user.py | 1: models/user.py:29, 32 (MD5) | finding: [CRITICAL] AP-08 models/user.py:27-32 |
| AP-08 | Missing/constant salt | models/user.py | 1: no salt | finding: [CRITICAL] AP-08 models/user.py:27-32 |
| AP-08 | Non-constant-time credential comparison | models/user.py | 1: models/user.py:32 `==` | finding: [CRITICAL] AP-08 models/user.py:27-32 |
| AP-08 | Sensitive values in logs | all source files | 1: routes/user_routes.py:89 `print(str(e))` (driver error carries bound params); others print ids/titles only | finding: [HIGH] AP-08 models/user.py:16-25 (second site) |
| AP-08 | Whole-row serialization with sensitive fields | models/*.py | 1: models/user.py:21 `password` (observed in GET /users/1) | finding: [HIGH] AP-08 models/user.py:16-25 |
| AP-08 | Transport without protection / verification off | all source files | 0 | none |
| AP-08 | Tokens with no expiry/revocation | routes/user_routes.py | 1: :210 predictable token, no expiry | finding: [CRITICAL] AP-04 routes/user_routes.py:185-211 (the token is never verified, so the dominant impact is the missing identity model) |
| AP-09 | Empty / log-and-continue / success-on-failure catch | routes/*.py | 0 returning success | none |
| AP-09 | Over-broad catch | routes/*.py | 10 bare `except:` (task_routes.py:62, 137, 236; user_routes.py:130, 149; report_routes.py:186, 207, 221; plus `except Exception` 151, 221) | finding: [HIGH] AP-09 routes/task_routes.py:13-63 |
| AP-09 | Same error mapping repeated per handler | routes/*.py | every handler | finding: [HIGH] AP-09 routes/task_routes.py:13-63 |
| AP-09 | No centralized handler | app.py | 1 (none registered; observed default debugger page on 500) | finding: [HIGH] AP-09 routes/task_routes.py:13-63; [CRITICAL] AP-18 app.py:33-34 |
| AP-09 | Internals returned in responses | run copy (observed) | 2 observed debugger/traceback pages | finding: [CRITICAL] AP-18 app.py:33-34 |
| AP-09 | Inconsistent error-return convention | all source files | 0 (all `{'error': ...}` with a status) | none |
| AP-09 | Partial writes with no transaction | routes/user_routes.py:140-148 | 1 candidate | discarded: task deletes and the user delete share one session commit (one transaction) |
| AP-09 | Exceptions for ordinary control flow | routes/task_routes.py:134-138 | 1: strptime in try for date format | discarded: narrow use for parsing, answers 400 — conventional in Python |
| AP-10 | Driver/ORM call inside a loop | routes/*.py | 4: task_routes.py:42, 51; report_routes.py:56, 163 | finding: [MEDIUM] AP-10 routes/task_routes.py:41-57; [MEDIUM] AP-10 routes/report_routes.py:53-68 |
| AP-10 | Per-element FK fetch | routes/task_routes.py | 1: :41-57 | finding: [MEDIUM] AP-10 routes/task_routes.py:41-57 |
| AP-10 | Lazy relation in iteration | routes/user_routes.py | 1: :22 `len(u.tasks)` | finding: [MEDIUM] AP-10 routes/task_routes.py:41-57 (described) |
| AP-10 | Same read repeated with different args | routes/*.py | 2: report_routes.py:15-28 (9 counts); task_routes.py:275-279 | finding: [MEDIUM] AP-10 routes/report_routes.py:53-68 |
| AP-10 | Remote call in a loop | all source files | 0 | none |
| AP-10 | Whole table read to filter/count in code | routes/*.py | 3: task_routes.py:281; report_routes.py:30, 53 | findings: both AP-10 |
| AP-10 | Write loop without batch | routes/user_routes.py:140-142, seed.py:78-90 | 2 | discarded: both add/delete to one session committed once (one transaction, one flush) |
| AP-11 | Input used with no type/range/format check | routes/*.py | many (task_routes.py:96, 113, 141, 167, 182, 261, 264; user_routes.py:61, 64, 103, 106, 115, 125; report_routes.py:178-180, 198-202) | finding: [MEDIUM] AP-11 routes/task_routes.py:85-114; [MEDIUM] AP-11 routes/user_routes.py:92-125 |
| AP-11 | Optional input dereferenced without check | routes/report_routes.py:196-197 | 1 | finding: [MEDIUM] AP-11 routes/user_routes.py:92-125 |
| AP-11 | Unconstrained pagination/limit | routes/*.py | 0 (no pagination at all) | see AP-13 |
| AP-11 | Numeric parse with no failure path | routes/task_routes.py:261, 264 | 2 (observed 500) | finding: [MEDIUM] AP-11 routes/task_routes.py:85-114 |
| AP-11 | Validation on one entry point but not another | routes/report_routes.py:169-171 vs 196 | 1 (create checks body, update does not) | finding: [MEDIUM] AP-11 routes/user_routes.py:92-125 |
| AP-11 | Validation after use / side effect | routes/*.py | 0 | none |
| AP-11 | Domain invariants enforced nowhere | routes/*.py | priority type (fraction accepted by range check), color format | findings: both AP-11; schema side in [MEDIUM] AP-20 |
| AP-11 | No bound on body/array length | routes/*.py | tags list, description, name unbounded | finding: [MEDIUM] AP-11 routes/task_routes.py:85-114 (described with title/tags) |
| AP-11 | Ad-hoc validation scattered | routes/*.py | all handlers | findings: AP-11 and [MEDIUM] AP-12 routes/task_routes.py:17-28 |
| AP-12 | ≥10-line structurally identical blocks | routes/*.py | overdue block ×4 (10 lines each) | finding: [MEDIUM] AP-12 routes/task_routes.py:30-39 |
| AP-12 | Same business rule in several places | all modules | overdue ×7; completion rate ×3 (task_routes.py:296, report_routes.py:67, 151) | finding: [MEDIUM] AP-12 routes/task_routes.py:30-39 |
| AP-12 | Same validation/serialization per handler | all modules | status set ×5, priority ×3, title ×3, email ×3, task serialization ×3 | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28 |
| AP-12 | Hand-written mappings with different field sets | routes/*.py | 2: task_routes.py:17-28, user_routes.py:162-169 | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28 |
| AP-12 | Diverged copy-and-modify | utils/helpers.py:57-108 vs routes | 1 (dead copy diverges) | finding: [LOW] AP-17 utils/helpers.py:1-116 (dead, so no live divergence) |
| AP-12 | Same constant literal across files | all modules | status strings, '#000000' (report_routes.py:180, models/category.py:10, helpers.py:116) | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28; [LOW] AP-15 |
| AP-12 | Condition repeated instead of a choke point | routes/*.py | `if not data` ×7 | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28 (validation module) |
| AP-13 | Paired acquire/release without scope | services/notification_service.py:15-20 | 1 | discarded: dead class → [LOW] AP-17 services/notification_service.py:1-48 |
| AP-13 | Handle with no release on failure | all source files; seed run | 1: ResourceWarning "unclosed database" at seed.py exit | discarded: one-shot process, runtime teardown closes it (catalog de-escalation to informational) |
| AP-13 | Connection per call / unbounded pool | all source files | 0 (Flask-SQLAlchemy pool) | none |
| AP-13 | Outbound call with no timeout | services/notification_service.py:15 | 1 | discarded: dead class → AP-17 |
| AP-13 | Retry without bound | all source files | 0 | none |
| AP-13 | Unbounded read | routes/*.py | 4: task_routes.py:14, 266; user_routes.py:12; report_routes.py:159 | finding: [MEDIUM] AP-13 routes/task_routes.py:11-14 |
| AP-13 | Unbounded in-memory accumulator | services/notification_service.py:31 | 1 | discarded: dead class → AP-17 |
| AP-13 | Background task with no shutdown | all source files | 0 | none |
| AP-13 | Unbounded recursion | all source files | 0 | none |
| AP-14 | Layer 1: boot with detectors on | `python -X dev app.py` in container, PYTHONWARNINGS=always::DeprecationWarning | boot reached readiness on 5000; boot-time stderr not captured (see Verification Coverage) | covered by the in-process pass below |
| AP-14 | Layer 1: documented seed script | `python -X dev seed.py` | utcnow warnings at seed.py:66, 67, 69, 70, 74 and via column defaults | finding: [MEDIUM] AP-14 routes/task_routes.py:31-31 |
| AP-14 | Layer 1: every surface entry | 21 routes over HTTP (27 calls) and in-process test client with warnings forced (22 calls) | utcnow ×10 sites; Query.get ×16 sites | finding: [MEDIUM] AP-14 routes/task_routes.py:31-31; [LOW] AP-14 routes/task_routes.py:42-42 |
| AP-14 | Dependency flagged deprecated in manifest/metadata | requirements.txt, installed metadata | 0 | none |
| AP-14 | Version marked unsupported by manifest | requirements.txt | 0 | none |
| AP-14 | Structurally superseded constructs | all source files | Query.get (observed, above) | finding: [LOW] AP-14 routes/task_routes.py:42-42 |
| AP-14 | Layer 2: registry yanked check | PyPI JSON for the 6 direct pins, 2026-11-10 | 0 yanked | none |
| AP-14 | Layer 2: native outdated tooling | Phase 2: not run. Re-audit (2026-11-11): `pip list --outdated` in container -13 over the refactored manifest | 3: flask-cors 6.0.0 (latest 6.0.5), python-dotenv 1.2.2 (latest 1.2.4), pip 26.2.1 (latest 26.3) | discarded: patch releases within the pinned major and minor, no advisory (OSV clean 2026-11-11) and no deprecation or end-of-life signal; pip is the image's installer, not an application dependency. The original's distance was never measured (Phase 2 gap, closed only for the refactored set) |
| AP-14 | Layer 2: official docs/changelog | — | not needed | none — both language/framework deprecations were observed at Tier A |
| AP-15 | Unexplained numeric literal in a decision | routes/*.py | report_routes.py:45, 129; user_routes.py:64, 115; task_routes.py:96-100, 113 | finding: [LOW] AP-15 routes/report_routes.py:24-28 |
| AP-15 | Duration/size with no unit | routes/report_routes.py:45 | 1 (`days=7` names its unit) | finding: [LOW] AP-15 (as a magic threshold, unit is explicit) |
| AP-15 | Enumerated string literal repeated across files | all modules | status ×5 files, roles ×2 | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28 (dominant impact: duplication) |
| AP-15 | Literal repeated in several places | all modules | '#000000' ×3 | finding: [MEDIUM] AP-12 routes/task_routes.py:17-28 |
| AP-15 | Numeric code compared directly | routes/report_routes.py:24-28 | priority 1-5 mapped by position | finding: [LOW] AP-15 routes/report_routes.py:24-28 |
| AP-15 | Unnamed index/offset | all modules | 0 | none |
| AP-15 | Environment-specific literal inline | app.py:11, 34 | 2: DB URI, port/host | finding: [CRITICAL] AP-18 app.py:33-34 (host/port/debug); DB URI → [HIGH] AP-06 app.py:9-31 (configuration in the composition root) |
| AP-16 | Name contradicts behaviour | all modules | 0 | none |
| AP-16 | Non-descriptive identifiers in wide scope | all modules | `data`, `t`, `u`, `c` only in short loop/handler scope | discarded: idiomatic short scope |
| AP-16 | Several names for one concept | all modules | 0 | none |
| AP-16 | How-not-what names | all modules | 0 | none |
| AP-16 | Mixed naming conventions | all modules | 0 (snake_case throughout) | none |
| AP-16 | Mixed human languages | all modules | identifiers English, user-facing messages and comments Portuguese | discarded: consistent split (code English, user text Portuguese), deliberate |
| AP-16 | File placed where its name says it does not belong | routes/report_routes.py | 1: category CRUD under `reports` blueprint | finding: [CRITICAL] AP-03 routes/report_routes.py:1-223 (same lines) |
| AP-16 | Comment contradicting code | all modules | 0 | none |
| AP-16 | Unreadable boolean call-site params | all modules | 0 | none |
| AP-17 | Commented-out code | all modules | 0 | none |
| AP-17 | Unreachable branch | all modules | 0 | none |
| AP-17 | Defined but never referenced unit | all modules | utils/helpers.py (all), NotificationService, Task.validate_status/validate_priority/is_overdue, User.is_admin | finding: [LOW] AP-17 utils/helpers.py:1-116; [LOW] AP-17 services/notification_service.py:1-48 |
| AP-17 | Unused import / declared dependency never imported | all modules, requirements.txt | 13 unused imports; marshmallow, requests | finding: [LOW] AP-17 utils/helpers.py:1-116; python-dotenv discarded (loaded by `app.run()`) |
| AP-17 | Parameter never read / value never used | all modules | utils/helpers.py:57 `existing_task` (dead function) | finding: [LOW] AP-17 utils/helpers.py:1-116 |
| AP-17 | Constant feature flag | all modules | 0 | none |
| AP-17 | Unregistered endpoint | routes/*.py | 0 (all three blueprints registered) | none |
| AP-17 | Old/backup copy kept | target tree | 0 | none |
| AP-18 | Debug mode on by literal on start path | app.py | 1: app.py:34 | finding: [CRITICAL] AP-18 app.py:33-34 |
| AP-18 | Development server as production server | app.py, README.md | 1 (no production server declared anywhere) | finding: [CRITICAL] AP-18 app.py:33-34 |
| AP-18 | Bound to all interfaces with debug | app.py:34 | 1 | finding: [CRITICAL] AP-18 app.py:33-34 |
| AP-18 | Error output exposing internals | run copy (observed) | 2 (debugger pages with traceback) | finding: [CRITICAL] AP-18 app.py:33-34 |
| AP-18 | Permissive cross-origin policy with credentials | app.py:15 | 1: `CORS(app)` wildcard | discarded: no credentials allowed (extension default) and no cookie-based state; advisories on the extension → [HIGH] AP-19 requirements.txt:3-3 |
| AP-18 | Unrestricted diagnostic/admin surface | all routes | 1: `/health` returns status + timestamp | discarded: no configuration or internals exposed |
| AP-18 | Protective defaults switched off | app.py | 0 | none |
| AP-19 | OSV advisory for a direct dependency | OSV querybatch, 6 direct pins, 2026-11-10 | flask 1, flask-cors 5, marshmallow 1, requests 3, python-dotenv 1, flask-sqlalchemy 0 | findings: [HIGH] AP-19 requirements.txt:3-3; [MEDIUM] AP-19 requirements.txt:4-6; [LOW] AP-19 requirements.txt:1-1 |
| AP-19 | OSV advisory for a transitive dependency | OSV querybatch, 13 installed transitive versions, 2026-11-10 | 0 | none |
| AP-19 | Lockfile pins vulnerable version where range allows fix | — | no lockfile | none |
| AP-19 | No lockfile with ranges | requirements.txt | 0 (every direct dependency pinned exactly) | none — transitive versions resolved at install (SQLAlchemy 2.1.8, Werkzeug 3.1.9 …); results hold for the 2026-11-10 installation |
| AP-19 | No lockfile, exact pins | requirements.txt | 6 pins queried | covered above |
| AP-20 | Identity column without uniqueness | models/*.py | 0 (`users.email` is unique) | none |
| AP-20 | FK column without enforced FK | models/task.py:13-14; app.py | 2 declared, never enforced (no `PRAGMA foreign_keys=ON`) | finding: [MEDIUM] AP-20 models/task.py:11-14 |
| AP-20 | Parent delete with no child rule (orphans) | routes/report_routes.py:211-223; routes/user_routes.py:134-151 | 2 candidates | discarded: observed — the ORM nulls `tasks.category_id` on category delete (2 task updates seen); user delete removes tasks explicitly |
| AP-20 | Money in binary float | models/*.py | 0 | none |
| AP-20 | Closed set as free text / required column nullable | models/*.py | status, priority, role | finding: [MEDIUM] AP-20 models/task.py:11-14 |

## Classification Decisions
D1. GET /reports/user/<id> — returns one user's name, email and task statistics (totals by status, overdue, high-priority, completion rate) for any id in the path.
  Privileged because: it is per-principal activity readable about any principal by anyone; enumerating ids yields a per-user productivity rollup, the same data the summary report (classified privileged) exposes for everyone at once.
  Business because:   it concerns a single user and reads like that user's own dashboard/profile statistics, the kind of view an ordinary client shows to the user it is about.
  If privileged: guard it with the operator credential from configuration, closed by default (RP-04) — the finding becomes resolved.
  If business:   proposed under PROPOSED, NOT APPLIED with the identity model and an ownership check.

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| datetime.utcnow() (Python stdlib) | Python 3.13 | deprecation | A | runtime DeprecationWarning (-X dev, PYTHONWARNINGS) | n/a — local, 2026-11-10 run | [MEDIUM] AP-14 routes/task_routes.py:31-31 |
| Query.get() (SQLAlchemy) | SQLAlchemy 2.1.8 | deprecation | A | runtime LegacyAPIWarning | n/a — local, 2026-11-10 run | [LOW] AP-14 routes/task_routes.py:42-42 |
| flask | 3.0.0 | advisory | B | OSV GHSA-68rp-wp8r-4726 (CVE-2026-27205, LOW) | 2026-11-10 | [LOW] AP-19 requirements.txt:1-1 |
| flask | 3.0.0 | yanked | B | pypi.org/pypi/flask/3.0.0/json | 2026-11-10 | no issue found |
| flask-sqlalchemy | 3.1.1 | advisory / yanked | B | OSV; pypi.org JSON | 2026-11-10 | no issue found |
| flask-cors | 4.0.0 | advisory | B | OSV GHSA-hxwh-jpp2-84pm (HIGH), GHSA-84pr-m4jr-85g5, GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (MODERATE) | 2026-11-10 | [HIGH] AP-19 requirements.txt:3-3 |
| flask-cors | 4.0.0 | yanked | B | pypi.org JSON | 2026-11-10 | no issue found |
| marshmallow | 3.20.1 | advisory | B | OSV GHSA-428g-f7cq-pgp5 (MODERATE) | 2026-11-10 | [MEDIUM] AP-19 requirements.txt:4-6 |
| requests | 2.31.0 | advisory | B | OSV GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2 (MODERATE) | 2026-11-10 | [MEDIUM] AP-19 requirements.txt:4-6 |
| python-dotenv | 1.0.0 | advisory | B | OSV GHSA-mf9w-mj56-hr94 (MODERATE) | 2026-11-10 | [MEDIUM] AP-19 requirements.txt:4-6 |
| marshmallow, requests, python-dotenv | as pinned | yanked | B | pypi.org JSON | 2026-11-10 | no issue found |
| werkzeug, jinja2, itsdangerous, click, blinker, sqlalchemy, markupsafe, packaging, charset-normalizer, idna, urllib3, certifi, typing-extensions | 3.1.9, 3.1.6, 2.2.0, 8.5.1, 1.9.0, 2.1.8, 3.0.4, 26.3, 3.5.2, 3.20, 2.8.0, 2026.10.23, 4.16.0 (installed 2026-11-10) | advisory | B | OSV querybatch | 2026-11-10 | no issue found |
| outdated distance (pip list --outdated) | — | deprecation | — | not run | — | UNVERIFIED |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-1 | `docker run -d ... -v <run-1>:/app -v <skill scripts>:/skill:ro -w /app -e PYTHONWARNINGS=always::DeprecationWarning python:3.13-slim sleep infinity` (run copy run-1) | running |
| 2 | 2 | exec | container | same | `pip install -r /app/requirements.txt` | 19 packages installed |
| 3 | 2 | exec | container | same | `python -X dev seed.py` | exit 0; Tier-A warnings recorded |
| 4 | 2 | start | container | same (exec -d) | `python -X dev app.py` | ready on port 5000 (`proc wait`, 0.0 s) |
| 5 | 2 | exec | container | same | `python /app/_exercise.py` (27 HTTP calls, scratch tool in run-1) | 2 debugger pages observed |
| 6 | 2 | exec | container | same | `python seed.py` (reseed run-1) | exit 0 |
| 7 | 2 | exec | container | same | `python -X dev -W default /app/_exercise_inproc.py` (22 calls, test client) | Tier-A warnings recorded per handler line |
| 8 | 2 | stop | container | refactor-arch-task-manager-api-202611110155-8bb272fa-1 | `docker rm -f` by exact name | removed |
| 9 | 3a | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-2 | run copy run-2: `run ... sleep infinity`; `pip install -r requirements.txt`; `python seed.py`; `exec -d python app.py`; `proc wait --port 5000` | ready on port 5000 |
| 10 | 3a | exec | container | same | `probe.py capture` (full, destructive entries left out) | 471 entries observed, 0 error |
| 11 | 3a | stop | container | refactor-arch-task-manager-api-202611110155-8bb272fa-2 | `docker rm -f` by exact name | removed |
| 12 | 3a | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-3, -4, -5, -6 | run copies run-3..run-6, same sequence as row 9, one per destructive entry | each ready on port 5000 |
| 13 | 3a | exec | container | -3 / -4 / -5 / -6 | `probe.py capture --only <id> --merge` for delete-task / delete-category / delete-user-operator / sec-delete-user-anonymous | 1 observed each; 475 entries in baseline.json |
| 14 | 3a | stop | container | -3, -4, -5, -6 | `docker rm -f` by exact names | removed (4) |
| 15 | 3c | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-7 | copy refactored-1, refactored manifest installed, `python seed.py`, `exec -d python app.py`, OPERATOR_TOKEN by `-e` | ready on port 5000 |
| 16 | 3c | exec | container | same | `probe.py compare --base-url ... --out /reports/replay-1.json` | 51 PASS, 0 REGRESSION, 4 destructive left for isolated replay |
| 17 | 3c | stop | container | refactor-arch-task-manager-api-202611110155-8bb272fa-7 | `docker rm -f` by exact name | removed |
| 18 | 3c | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-8, -9, -10, -11 | copies refactored-2..refactored-5, same sequence as row 15 | each ready on port 5000 |
| 19 | 3c | exec | container | -8 / -9 / -10 / -11 | `probe.py capture --only <id> --merge --out /reports/replay-1.json` per destructive entry | 1 observed each |
| 20 | 3c | stop | container | -8, -9, -10, -11 | `docker rm -f` by exact names | removed (4) |
| 21 | 3d | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-12 | copy refactored-6, refactored manifest, `python -X dev seed.py`, `python -X dev -W default _reaudit_inproc.py` (PYTHONWARNINGS=always::DeprecationWarning) | 0 deprecation warnings; every route answered |
| 22 | 3d | stop | container | refactor-arch-task-manager-api-202611110155-8bb272fa-12 | `docker rm -f` by exact name | removed |
| 23 | 3d | start | container | refactor-arch-task-manager-api-202611110155-8bb272fa-13 | copy refactored-7 of the target: `run ... sleep infinity`, `pip install -r requirements.txt`, then `pip list --outdated` (approved by the person to close the re-audit gap) | 3 outdated, all patch-level (see Signal Ledger, AP-14) |
| 24 | 3d | stop | container | refactor-arch-task-manager-api-202611110155-8bb272fa-13 | `docker rm -f` by exact name | removed; label listing afterwards empty |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Boot-time stderr of the HTTP-served app: `exec -d` output does not reach `docker logs`, so warnings emitted while serving over HTTP were not read → covered instead by the in-process pass (same handlers, same detectors); boot-only warnings of the debug server itself are unverified.
  - `pip list --outdated`: not run → distance from current releases is not measured.
  - PyPI yanked check ran for the 6 direct pins only → transitive packages were checked for advisories (OSV) but not for yanked status.
  - Reachability of the flask-cors HIGH advisory (private-network header) was not exercised → severity kept at the HIGH default, not escalated.
  - No lockfile: transitive versions are whatever resolved on 2026-11-10; the advisory results hold for that installation only.
Scratch root: the environment's scratch directory (C:\Users\lucas\AppData\Local\Temp\claude\b247d7bb4f414394\ba923cae-119c-41c1-b0ad-d78f9f1be3ab\scratchpad\refactor-arch-task-manager-api-202611110155-8bb272fa); snapshot `pristine/` and run copy `run-1/` live there. Excluded from every copy: .git, .venv, __pycache__, reports.
Command rule: 0 directory changes, 0 chained commands so far.

================================
Total: 31 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
  For each classification decision, answer privileged or business (e.g. "y D1=privileged D2=business").
  An unanswered decision is treated as business (proposed).
>

Answer received: `y, D1=Business` (human). D1 recorded as business: GET /reports/user/<id> stays open and its access control is proposed.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
task-manager-api/
├── app.py                    composition root: create_app() wires config, repositories, controllers, routes
├── database.py               SQLAlchemy handle + per-connection foreign-key enforcement
├── seed.py                   sample data; passwords generated per run, printed once
├── requirements.txt          flask 3.1.3, flask-sqlalchemy 3.1.1, flask-cors 6.0.0, python-dotenv 1.2.2
├── README.md                 layout, run instructions, variables to export
├── .gitignore                instance/, *.db, __pycache__/, .venv/, .env
├── config/
│   ├── __init__.py
│   └── settings.py           the only module that reads the environment
├── models/                   domain + persistence
│   ├── __init__.py
│   ├── category.py
│   ├── clock.py              utcnow() / SystemClock (successor of datetime.utcnow)
│   ├── errors.py             domain error taxonomy
│   ├── repositories.py       every query of the application
│   ├── task.py               Task, status/priority constants, overdue rule, CHECK constraints
│   └── user.py               User, password KDF + legacy-digest verification, roles
├── controllers/              use cases, plain values in and out
│   ├── __init__.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── task_controller.py
│   └── user_controller.py
├── routes/                   views: routes, boundary validation, response shapes
│   ├── __init__.py
│   ├── category_routes.py
│   ├── converters.py         path ids bounded to the driver's integer range
│   ├── report_routes.py
│   ├── serializers.py
│   ├── system_routes.py      / and /health
│   ├── task_routes.py
│   ├── user_routes.py
│   └── validation.py
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py      single error boundary (JSON, status kept)
│   └── operator_guard.py     X-Operator-Token, closed when OPERATOR_TOKEN is unset
└── reports/                  audit-20261110-2312.md, audit-latest.md, surface.json, baseline.json, replay-1.json
Removed: services/ (dead notification class with committed SMTP credential), utils/ (dead helpers).
Repositories stay inside the model layer (04-architecture-guidelines.md §2). The layout is MVC: routes/ is the view layer.
```

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 54 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 6 FIXED, 0 NOT FIXED
  ✓ Malformed input: 405 ROBUST, 0 NOT ROBUST, 0 REGRESSION over 16 operations
  ✓ Values: 10 HOLDS, 0 VIOLATED, 0 UNVERIFIED
  ○ Findings resolved: 22/31  (9 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 6 proposed-not-applied, 0 unresolved  (re-audit: 6 findings)
    Re-audit passes: 1; fixed after re-audit: 0 (0 of them missed-in-phase-2)
  ✓ Processes: 13 started, 13 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

## Findings by bucket
Resolved (22):
  [CRITICAL] AP-01 app.py:13 signing key literal — read from SECRET_KEY, random per process when unset (the key never signed anything, so nothing to rotate).
  [CRITICAL] AP-03 routes/report_routes.py — split into routes/report_routes.py + routes/category_routes.py, controllers and repository queries.
  [CRITICAL] AP-04 routes/report_routes.py:12-101 summary rollup — guarded by the operator credential (sec-summary-report-anonymous FIXED; summary-report-operator PASS; val-summary-report HOLDS).
  [CRITICAL] AP-04 routes/user_routes.py:92-151 account takeover/deletion — guarded field by field (email, password, role, active) and on DELETE, refused before any write (5 security entries FIXED; update-user-name, update-user-resend-stored, update-user-role-operator, delete-user-operator PASS).
  [HIGH] AP-06 app.py:9-31 — application factory, single composition root, injected clock, no import-time side effects.
  [HIGH] AP-08 models/user.py:16-25 — password field masked, type kept (val-get-user-password-masked, val-login-password-masked HOLD); driver errors logged without bound parameters (hide_parameters).
  [HIGH] AP-19 flask-cors 4.0.0 — upgraded to 6.0.0 (major); replay covered the CORS contract headers (cors-simple-get, cors-preflight-post, cors-preflight-put-user PASS); OSV clean 2026-11-11.
  [HIGH] AP-09 — one error boundary; bare excepts removed; intentional error bodies and statuses kept.
  [HIGH] AP-05 task routes — TaskController + TaskRepository; handlers parse → call → render.
  [HIGH] AP-05 user routes — UserController + UserRepository.
  [MEDIUM] AP-19 marshmallow, requests (removed: never imported), python-dotenv → 1.2.2; OSV clean 2026-11-11.
  [MEDIUM] AP-10 reports/categories — grouped aggregate queries (val-summary-report, val-list-categories HOLD).
  [MEDIUM] AP-12 serialization/validation — one serializer per representation, one validation module, constants in the models.
  [MEDIUM] AP-12 overdue rule — Task.is_overdue / Task.overdue_clause, used everywhere.
  [MEDIUM] AP-14 datetime.utcnow() — models/clock.utcnow() = datetime.now(UTC) naive; 0 warnings in the re-audit run; format kept (val-task-timestamp-format HOLDS).
  [MEDIUM] AP-10 task listing — one outer-join query (val-list-tasks, val-list-users HOLD).
  [MEDIUM] AP-11 task inputs — type/range checks at the boundary, bounded path-id converter (all task variants ROBUST).
  [LOW] AP-19 flask 3.0.0 → 3.1.3 (same major); OSV clean 2026-11-11.
  [LOW] AP-15 — named constants (PRIORITY_LABELS, HIGH_PRIORITY_MAX, RECENT_ACTIVITY_DAYS, PASSWORD_MIN_LENGTH, title bounds).
  [LOW] AP-14 Query.get() — db.session.get(); 0 warnings in the re-audit run.
  [LOW] AP-17 services/notification_service.py — deleted.
  [LOW] AP-17 utils/helpers.py, unused imports, unused model methods, unused dependencies — deleted.
Proposed (9): listed under Proposed, Not Applied below.
Unresolved (0).

## Re-audit (pass 1, over the refactored target, same catalog)
Findings: 6, all matching items recorded under Proposed, Not Applied before the re-audit ran:
  - AP-18 app.py:59-63 — the framework's development server still serves the app (production server proposed).
  - AP-08 models/user.py:44-51 — legacy MD5 verification path kept for the digest migration (reset window proposed).
  - AP-04 routes/report_routes.py:15-18 — per-user report open (D1 = business, proposed).
  - AP-04 controllers/user_controller.py:114-123 — no identity model: unverified token, anonymous CRUD, role chosen at registration (proposed).
  - AP-13 models/repositories.py:30-36, 106-107, 121-122 — listings unbounded (pagination proposed).
  - AP-11 routes/validation.py:188-214 — category/user string lengths not bounded to their columns (proposed).
Unresolved: 0 (failed 0, introduced 0, missed-in-phase-2 0).
Signals that matched and were discarded in the re-audit:
  - AP-08 seed.py prints the generated sample passwords once: a deliberate delivery channel for credentials the operator needs, not a request or error log.
  - AP-13 ResourceWarning "unclosed database" at seed.py exit: one-shot process, runtime teardown closes it.
  - AP-09 controllers catch Exception around a single commit: they log it and re-raise a domain error. Nothing is swallowed.
  - AP-06 routes/system_routes.py reads datetime.now() for the health timestamp: presentation only, value kept from the original (local time).

## Proposed, Not Applied
### [CRITICAL] Insecure Runtime Configuration — development server   (AP-18)
File: app.py:59-63
Reason not applied: serving through a production WSGI server needs a runtime dependency the application does not have (e.g. a WSGI server package) — whoever deploys must install something new. Debug is now off by default (APP_DEBUG), and the default error page is replaced. Those parts were applied.
Proposed change: add a production WSGI server to requirements.txt and start it with the factory (`<server> "app:create_app()"`); keep `python app.py` for development.

### [CRITICAL] Unsafe Handling of Credentials — legacy MD5 digests   (AP-08)
File: models/user.py:44-51
Reason not applied: operator residue. New and changed passwords use the KDF, and legacy digests are replaced at the user's next successful sign-in. Accounts that never sign in keep an unsalted MD5 digest until an operator acts.
Proposed change: after a reset window (e.g. 30 days from deploy), list the remaining legacy accounts with `SELECT id, email FROM users WHERE length(password) = 32;`, then reset each through `PUT /users/<id>` with `X-Operator-Token` and a new password. After that, delete the legacy branch in models/user.py.

### [CRITICAL] Missing Authorization — per-user report   (AP-04)
File: routes/report_routes.py:15-18
Reason not applied: decided at the gate: D1 = business. Every current client is anonymous and would receive the new rejection.
Proposed change: introduce the identity model (below) and allow the report only to its own user or an operator.

### [CRITICAL] Missing Authorization — no identity model   (AP-04)
File: controllers/user_controller.py:114-123
Reason not applied: contract-changing. Requiring a verified token would answer 401 to every current client. Registration would also stop honouring `role`.
Proposed change: issue signed, expiring tokens at /login and verify them on every business route. Scope tasks to their owner. Fix the role at registration to `user`, with role changes only through the operator path.

### [CRITICAL] Hardcoded Secrets — seeded accounts with known passwords   (AP-01)
File: seed.py:56-67
Reason not applied: operator residue. The new seed generates random passwords, but databases already seeded by the previous script still hold accounts with the published passwords (one of them `admin`).
Proposed change: in every environment seeded before this change, rerun `python seed.py` (development data) or reset the three accounts through `PUT /users/<id>` with `X-Operator-Token`.

### [CRITICAL] Hardcoded Secrets — SMTP account   (AP-01)
File: services/notification_service.py:7-10 (deleted)
Reason not applied: operator residue. The file is gone, but the password stays in git history.
Proposed change: rotate the mail account's password at the provider now. Any future mail configuration comes from the environment.

### [MEDIUM] Missing Schema-Level Integrity Constraints — existing databases   (AP-20)
File: models/task.py:31-35
Reason not applied: operator residue. The CHECK constraints (status, priority, role) apply to databases created from now on, because `db.create_all()` does not alter existing tables. Foreign-key enforcement applies to all databases.
Proposed change: on each existing database, first count the violating rows (`SELECT COUNT(*) FROM tasks WHERE status NOT IN ('pending','in_progress','done','cancelled') OR priority NOT BETWEEN 1 AND 5;`, `SELECT COUNT(*) FROM users WHERE role NOT IN ('user','admin','manager');`, `PRAGMA foreign_key_check;`). If all are zero, rebuild `tasks` and `users` by copy inside one transaction (create the constrained table, copy rows, swap names).

### [MEDIUM] Unbounded Resources — whole-table listings   (AP-13)
File: models/repositories.py:30-36
Reason not applied: contract-changing. A client that reads the full list in one call would start receiving a page.
Proposed change: optional `page`/`per_page` query parameters with a bounded maximum, and a decision on the default page size.

### [MEDIUM] Missing Boundary Validation — string lengths   (AP-11)
File: routes/validation.py:188-214
Reason not applied: contract-changing. Bounding `name` (100), `email` (150), `color` (7, `#rrggbb`) and category `description` (300) to their columns would reject values that clients can store today (SQLite does not enforce declared lengths). The type checks were applied (every user and category variant ROBUST).
Proposed change: apply the column lengths and the color format once the team confirms them.

## Verification Coverage
DEGRADED — the following checks did not run:
  - `pip list --outdated` did not run in Phase 2, so the original's distance from current releases was never measured. Closed for the re-audit on 2026-11-11 with the person's approval: run in container -13 over the refactored manifest, it found 3 patch-level updates and no finding (Signal Ledger, AP-14). With it, every planned re-audit check ran, so the re-audit line is ○, no longer ⚠.
  - Server stderr in the HTTP runs: `exec -d` output does not reach `docker logs`. Runtime warnings were read from in-process passes over every route instead (Phase 2: original; 3d: refactored, 0 warnings).
  - The registry yanked check covered only the direct pins (Phase 2: 6 packages; re-audit: flask 3.1.3, flask-cors 6.0.0, python-dotenv 1.2.2 — none yanked, 2026-11-11). Transitive packages were checked for advisories only (OSV, clean 2026-11-11).
  - Final container listing: the Docker engine became unreachable after container -12 was removed (the engine was stopped outside this run), so the closing `docker ps --filter label=refactor-arch.run=202611110155-8bb272fa` could not run at that point. It ran when the engine was back: empty before container -13 started, and empty again after -13 was removed. All 12 containers of the run were removed by exact name, with each removal confirmed in its output (Execution Log rows 8, 11, 14, 17, 20, 22). The listing taken at the session resume, before -7..-12 existed, was empty.
  - The value of the flask-cors private-network header (Phase 2 HIGH advisory) is not observable to the shape harness. Its reachability was not exercised. The upgrade past the fixed version is verified by OSV, not by the replay.
Isolation: container (docker 28.5.2, python:3.13-slim). Scratch root: the environment's scratch directory. The snapshot and all run copies were deleted after the re-audit.
Process ownership: the scratch tools `_exercise.py`, `_exercise_inproc.py` and `_reaudit_inproc.py` lived only in run copies and were deleted with the snapshot.
Text-comparison masks (protocol §5.2) applied to text bodies and contract headers.
Fixtures by reference: OPERATOR_TOKEN, TEST_USER_PASSWORD, WRONG_PASSWORD, SHORT_PASSWORD, NEW_PASSWORD
Operator guard: variable OPERATOR_TOKEN (header X-Operator-Token), unset by default. Unset or empty means the guarded operations answer 403.
================================
