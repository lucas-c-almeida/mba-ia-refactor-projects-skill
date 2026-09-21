# Run task-manager-api/iter1 — `/refactor-arch task-manager-api --yes`

- Date: 2026-09-21 (local, UTC-3), branch `round1`, HEAD `38b77d9`
- Executed by a sub-agent in a fresh context; confirmation gate skipped via `--yes`
  (auto-approved, not human-reviewed). Mode: full (live upstream lookups ran).
- Other agents ran the same skill concurrently on sibling directories; this run touched only
  `task-manager-api/` (plus this transcript). Validation port: 5103.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        task-manager-api
Language:      Python (runtime used: CPython 3.13.2; no version declared by the project)
Framework:     Flask 3.0.0 (installed metadata; exact pin in requirements.txt) + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.0.54 resolved)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0 (marshmallow, requests, python-dotenv declared but never imported; no lockfile)
Domain:        Task-management API — users, task categories, tasks with status/priority/due date/tags, plus summary and per-user productivity reports
App type:      HTTP service (21 routes) — plus a one-shot sample-data script (seed.py), not part of the public surface
Architecture:  Nominal layering — models/, routes/, services/, utils/ exist, but route handlers hold validation, business rules, persistence and serialization; services/ and utils/ are never used
Source files:  15 files analyzed (*.py, excluding .venv/, instance/, __pycache__/, reports/; ~1,158 lines)
DB tables:     users, categories, tasks (SQLite via Flask-SQLAlchemy, instance/tasks.db, created by db.create_all at import time)
================================
Boot command (recorded for Phase 3): from task-manager-api/, after `python seed.py`:
  .venv/Scripts/python -m flask --app app run --host 127.0.0.1 --port 5103
  (the declared `python app.py` hardcodes port 5000 and debug=True, so the framework CLI was used to
   assign the port without modifying the code; the project had no Python environment, so a
   git-ignored virtualenv was created at .venv/ from requirements.txt — the README's own install step)
```

## Phase 2 — Audit report (as printed; saved to `task-manager-api/reports/audit-20260921-0009.md`)

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13.2 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1 / SQLAlchemy 2.0.54, SQLite)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-09-21 00:09
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 7 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:11-13
Description: The framework's session/signing key is set to a string literal (`app.config['SECRET_KEY'] = 'super-secret-key-123'`, line 13), and the database URI is an inline literal (line 11), both at module level in the entry point, with no environment read anywhere in the project. Aggravating: it is a signing key, so anything signed with it is forgeable.
Impact: Anyone with read access to the repository (or any clone/fork) can forge session cookies or any other value signed with this key; rotating it requires a code change and a deploy, and the literal stays in git history forever.
Recommendation: Move the key and the database URI into a single configuration module that reads the environment once and fails loudly if the key is missing; add `.env.example` with placeholders; rotate the committed key (see RP-01).
Contract: safe

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: services/notification_service.py:7-10
Description: An SMTP account (host, port, user `taskmanager@gmail.com` and password literal `'senha123'`) is hardcoded in the constructor of `NotificationService`. Aggravating: the credential reaches a third-party system (a public mail provider). The class is also never imported anywhere (see the AP-17 finding), so the credential is committed without even delivering a feature.
Impact: Anyone with repository access can log into the mail account and send mail as the application; the credential must be treated as compromised.
Recommendation: Remove the literal; if the notifier is kept, receive host/user/password from configuration injected by the composition root; rotate the password regardless (see RP-01, RP-06).
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models/user.py:16-25
Description: `User.to_dict()` serializes the whole record including the `password` field (the stored hash), and this method is used to render `GET /users/<id>` (routes/user_routes.py:33), `POST /users` (user_routes.py:85), `PUT /users/<id>` (user_routes.py:129) and `POST /login` (user_routes.py:209). Escalated from the HIGH default because the exposed value is an unsalted fast-digest password hash (see next HIGH AP-08 finding), i.e. effectively recoverable for weak passwords, served to unauthenticated callers.
Impact: Any caller can enumerate `/users/<id>` and collect every account's password hash, then recover weak passwords offline with precomputed tables — and, because passwords are reused, compromise accounts on other systems.
Recommendation: Render users through an explicit allow-list presenter that omits the hash (see RP-08).
Contract: contract-changing: the `password` field would disappear from four response bodies; a client reading it would observe a missing field.

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/user_routes.py:185-211
Description: `POST /login` returns `'fake-jwt-token-' + str(user.id)` (line 210) — a predictable string that no other route ever verifies. No surface entry has any authentication or authorization check: `DELETE /users/<id>` (134-151), `PUT /users/<id>` including `role` (119-122), `POST /users` accepting `role` from the body (52, 71-78), and all task/category/report mutations. The role value is taken from the request and trusted.
Impact: Any anonymous caller can delete any user and their tasks, promote any account (including their own) to `admin`, and read every user's data; the "token" gives a false impression that authentication exists.
Recommendation: Introduce real token issuance/verification and a policy on the operations (RP-04). The legitimate policy (who may change roles, delete users, see other users) cannot be determined from the code without guessing.
Contract: contract-changing: every existing client currently calls without credentials and would start receiving 401/403; role assignment rules require a product decision.

### [HIGH] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models/user.py:27-32
Description: Passwords are hashed with unsalted MD5 (`hashlib.md5(pwd.encode()).hexdigest()`, line 29) and verified with a plain `==` comparison (line 32), instead of a purpose-built password KDF with a constant-time comparison.
Impact: A single read of the `users` table (or of the API responses above) exposes every password to fast offline cracking; identical passwords produce identical hashes across accounts.
Recommendation: Hash with a salted, work-factored KDF already available in the installed stack (Werkzeug's `generate_password_hash`/`check_password_hash`), keep verifying legacy MD5 hashes and re-hash on successful login (see RP-08).
Contract: safe (with upgrade-on-login, legitimate logins keep working; response shape unchanged)

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: routes/task_routes.py:85-223
Description: Route handlers parse the request, validate business rules (title length, status set, priority range, due-date format), check referenced users/categories, mutate the ORM entity, and commit the session directly (e.g. `create_task` 85-154, `update_task` 156-223). The same shape holds in routes/user_routes.py (42-151: email/role rules, duplicate check, password policy, cascade delete of tasks at 140-142) and routes/report_routes.py (12-155: all reporting aggregation computed inside the handlers). The `services/` package exists but holds no use case — nominal layering.
Impact: No rule can be tested or reused without an HTTP request; a second entry point (CLI, job) would have to copy the rules; the create and update paths already validate differently (e.g. update never checks the type of `title`).
Recommendation: Extract one controller method per use case; handlers become parse → call → render; persistence moves to repositories in the model layer (see RP-05, RP-03).
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: app.py:9-34
Description: The application object is created at module level with literal configuration (lines 9-13), `db.create_all()` runs at import time (30-31) so merely importing `app` creates/opens the database file, and the entry point hardcodes `app.run(debug=True, host='0.0.0.0', port=5000)` (34). `seed.py:2` imports this module-level app. `NotificationService.send_email` constructs its own SMTP client inline (services/notification_service.py:15). The interactive debugger bound to all interfaces is a severe exposure when started this way; no catalog escalation condition covers it, so the finding stays at the HIGH default and the exposure is recorded here.
Impact: The app cannot be constructed twice (e.g. with a test database) in one process, importing it has filesystem side effects, and environment-specific values (host, port, debug) require code edits.
Recommendation: Introduce a `create_app()` factory as composition root, a settings object read from the environment (debug off by default), and move `create_all` into the factory (see RP-06, RP-01).
Contract: safe

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: routes/task_routes.py:13-63
Description: `get_tasks` wraps its entire body in a bare `except:` returning a generic 500 (62-63). Bare `except:` also appears at task_routes.py:137, 204, 236; user_routes.py:130, 149; report_routes.py:186, 207, 221; and the same try/commit/rollback/`jsonify({'error': ...})` block is copied into every mutating handler. There is no centralized error handler; errors are "logged" with `print` (task_routes.py:149, 153, 219, 234; user_routes.py:83, 89, 147) and the exception detail in `except Exception as e` blocks is discarded (task_routes.py:221-223).
Impact: Any failure — including programming errors — is absorbed into an indistinguishable 500 with no logged context, so operators cannot diagnose incidents; every handler must re-implement the same mapping.
Recommendation: A small domain error taxonomy raised by controllers and one error boundary registered in the composition root, preserving the existing status codes and `{"error": "<message>"}` bodies; use the logging module (see RP-09).
Contract: safe (when observable statuses and bodies are preserved)

### [HIGH] Deprecated or End-of-Life API Usage   (AP-14)
File: requirements.txt:1-3
Description: The pinned `flask-cors==4.0.0` has published advisories for that exact version (OSV.dev, looked up 2026-09-21): GHSA-hxwh-jpp2-84pm (rated HIGH, fixed in 4.0.2), GHSA-84pr-m4jr-85g5 (fixed 4.0.1), GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (fixed 6.0.0); `CORS(app)` applies it to every route (app.py:15). The pinned `flask==3.0.0` has GHSA-68rp-wp8r-4726 (rated LOW, fixed in 3.1.3). Severity is HIGH, escalated from the MEDIUM default, because a dependency with a HIGH-rated advisory is in the request path of every route. (Neither package is marked deprecated or yanked on PyPI.)
Impact: Known, published weaknesses in the CORS layer apply to every endpoint; they will not be fixed without a version change.
Recommendation: Upgrade `flask-cors` to the maintained line named by the advisories (≥ 6.0.0; latest on PyPI 6.0.5 as of 2026-09-21) and `flask` to ≥ 3.1.3, then re-verify CORS response headers (see RP-14).
Contract: contract-changing: flask-cors 6.x changes origin/path matching semantics (per the advisories' own descriptions), which alters CORS headers browsers observe; the behavioural harness does not capture those headers, so equivalence cannot be verified here.

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: routes/task_routes.py:41-57
Description: For every task, `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` are issued inside the loop (two extra queries per row). Same pattern: routes/user_routes.py:22 (`len(u.tasks)` lazy-loads per user), routes/report_routes.py:53-68 (one task query per user), report_routes.py:159-164 (one count per category); and whole tables are read into memory to count overdue tasks (task_routes.py:281-287, report_routes.py:30-43) next to five separate `count()` queries for statuses (task_routes.py:275-279, report_routes.py:19-28).
Impact: Latency grows linearly with rows; the listing endpoints issue 2N+1 queries.
Recommendation: Eager-load relations / use grouped aggregates and batch lookups (see RP-10).
Contract: safe

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: routes/task_routes.py:102-114
Description: `priority` from the body is compared numerically without a type check (`priority < 1`, line 113); a string value raises `TypeError` and becomes an unhandled 500. Same class: `update_task` calls `len(data['title'])` and compares `data['priority']` without type checks (166-184); `search_tasks` calls `int(priority)` / `int(user_id)` on raw query strings (260-264, `ValueError` → 500); `update_category` dereferences `data` without a None check (report_routes.py:196-197); `create_category`/`update_category` accept any `color` although the column is 7 characters; `update_user` accepts any `name`/`active` value (user_routes.py:102-125).
Impact: Malformed input produces server errors instead of clear client errors, so attacks and bugs are indistinguishable; invalid values can be persisted.
Recommendation: A single boundary validation per use case that rejects unambiguously malformed input with 400 (RP-11); stricter rules that would reject currently accepted input are to be proposed.
Contract: safe for converting crash-500s into 400s; contract-changing for rules that would reject input accepted today (e.g. colour format, non-empty name on update).

### [MEDIUM] Duplicated Logic   (AP-12)
File: routes/task_routes.py:30-39
Description: The "overdue" rule (due date in the past and status not done/cancelled) is written out five more times: task_routes.py:71-80, 283-287; user_routes.py:171-180; report_routes.py:33-43, 132-135 — while `Task.is_overdue()` (models/task.py:50-60) implements it and is never called. Also duplicated: the task serialization hand-built at task_routes.py:17-28 and user_routes.py:162-169 instead of `to_dict`; the status list (task_routes.py:110, 177; models/task.py:39); the email regex (user_routes.py:61, 106); `validate_status`/`validate_priority` in the model are unused while routes re-implement them.
Impact: A change to the rule must be made in six places; the copies agree today, but any missed copy makes the same task overdue on one endpoint and not on another.
Recommendation: One rule in the model, one serializer per representation, one definition of each enumeration (see RP-12).
Contract: safe

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: routes/task_routes.py:14-14
Description: `Task.query.all()` loads the whole table for `GET /tasks` with no limit or pagination; likewise `GET /users` (user_routes.py:12), `GET /categories` (report_routes.py:159), `GET /tasks/search` (task_routes.py:266), and the summary report reads all tasks and all users (report_routes.py:30, 53). `smtplib.SMTP(...)` is opened without a timeout and closed with an explicit `quit()` that is skipped on any exception (services/notification_service.py:15-20).
Impact: Response size and memory grow with the data set; one slow SMTP server would block the worker indefinitely.
Recommendation: Paginate collection endpoints (RP-13); bind the SMTP connection to a `with` scope with a timeout.
Contract: contract-changing for pagination (clients currently receive the full collection); safe for the SMTP scope/timeout.

### [MEDIUM] Deprecated or End-of-Life API Usage   (AP-14)
File: routes/task_routes.py:31-31
Description: Tier A — with `PYTHONWARNINGS=always::DeprecationWarning python -X dev` the runtime emitted `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)` at task_routes.py:31, 72, 285; report_routes.py:35, 42, 45, 71, 133; user_routes.py:172; seed.py:66-74; and via the column defaults `default=datetime.utcnow` (models/task.py:15-16, models/user.py:14, models/category.py:11 — emitted from SQLAlchemy's default executor). Other call sites of the same function exist (task_routes.py:215, models/task.py:52, services/notification_service.py:35, utils/helpers.py:38).
Impact: The call is scheduled for removal; the next Python upgrade that removes it breaks every date computation and every insert.
Recommendation: Replace with the successor named by the runtime warning, `datetime.now(timezone.utc)`, stripped to naive (`.replace(tzinfo=None)`) so stored and serialized values stay identical to today's naive-UTC values (see RP-14).
Contract: safe (naive UTC preserved; values and string format unchanged)

### [MEDIUM] Magic Values   (AP-15)
File: routes/task_routes.py:96-114
Description: Title bounds `3`/`200`, priority bounds `1`/`5`, default priority `3` (104), minimum password length `4` (user_routes.py:64, 115), "high priority" threshold `<= 2` (report_routes.py:129), `7`-day window (report_routes.py:45), default colour `'#000000'` (report_routes.py:180), and the status/role string enumerations repeated across modules (task_routes.py:110, 177; user_routes.py:71, 120; report_routes.py:19-22). Named constants for most of these exist in utils/helpers.py:110-116 and are never used. Escalated from LOW because the same enumerations appear in several modules that must agree.
Impact: Changing a limit requires finding every copy; a typo in a status string silently creates a new state.
Recommendation: One named definition per value, owned by the model layer (see RP-15).
Contract: safe

### [MEDIUM] Dead Code and Commented-Out Code   (AP-17)
File: utils/helpers.py:1-116
Description: No function or constant of `utils/helpers.py` is used; `format_date` and `calculate_percentage` are imported by report_routes.py:7 but never called. `process_task_data` (57-108) is a second, already diverged implementation of task validation (accepts `dd/mm/YYYY` dates and strips the title, unlike the live routes). Also dead: `services/notification_service.py` (never imported), `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`, `User.is_admin`; unused imports at app.py:7, task_routes.py:7, user_routes.py:6, report_routes.py:8, models/task.py:3; declared dependencies never imported: `marshmallow`, `requests` (requirements.txt:4-5), and `python-dotenv` (requirements.txt:6). Escalated from LOW because a stale second implementation of live behaviour is present.
Impact: A maintainer may fix validation in the dead copy and see no effect; unused dependencies carry their own published advisories (OSV lists advisories for marshmallow 3.20.1, requests 2.31.0 and python-dotenv 1.0.0) into every install for no benefit.
Recommendation: Delete the dead units and imports; drop unused dependencies (or put `python-dotenv` to actual use for configuration loading) (see RP-16).
Contract: safe

### [LOW] Deprecated or End-of-Life API Usage   (AP-14)
File: routes/task_routes.py:42-51
Description: Tier A — the runtime emitted `LegacyAPIWarning: The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get() (deprecated since: 2.0)` at task_routes.py:42, 51, 67; user_routes.py:29, 155; report_routes.py:105. Every other `Model.query.get(...)` call site (task_routes.py:117, 122, 158, 188, 195, 227; user_routes.py:94, 136; report_routes.py:192, 213) uses the same API. LOW, de-escalated from MEDIUM: a drop-in successor exists and no advisory is attached.
Impact: A legacy construct slated for removal in a future SQLAlchemy major.
Recommendation: Replace with `db.session.get(Model, id)`, the successor named by the warning (see RP-14).
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: routes/report_routes.py:157-223
Description: The full CRUD for categories lives in the module named for reports; the blueprint is `report_bp`. Non-descriptive names in multi-line scopes (`t`, `p`, `d`, `cat`, `data` in models/task.py:45, models/category.py:14, task_routes.py:16).
Impact: A reader looking for category logic will not find it by name; changes to reports and categories collide in one file.
Recommendation: Move category routes to their own module; rename internals for intent (see RP-16). Route paths stay unchanged.
Contract: safe

## Deprecated API Verification

| Item | Version in use | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|
| `datetime.datetime.utcnow()` | CPython 3.13.2 | A | runtime DeprecationWarning with `-X dev` + `PYTHONWARNINGS=always::DeprecationWarning` | n/a — local | AP-14 [MEDIUM] |
| SQLAlchemy `Query.get()` | SQLAlchemy 2.0.54 | A | runtime LegacyAPIWarning (same run) | n/a — local | AP-14 [LOW] |
| flask-cors | 4.0.0 | B | OSV.dev `/v1/query` (PyPI); PyPI JSON (not yanked) | 2026-09-21 | AP-14 [HIGH] — 5 advisories |
| flask | 3.0.0 | B | OSV.dev; PyPI JSON (not yanked) | 2026-09-21 | AP-14 [HIGH] (same finding) — GHSA-68rp-wp8r-4726, fixed 3.1.3 |
| flask-sqlalchemy | 3.1.1 | B | OSV.dev; PyPI JSON | 2026-09-21 | no issue found |
| sqlalchemy (transitive, resolved) | 2.0.54 | B | OSV.dev; PyPI JSON | 2026-09-21 | no issue found |
| werkzeug (transitive, resolved) | 3.1.8 | B | OSV.dev; PyPI JSON | 2026-09-21 | no issue found |
| marshmallow | 3.20.1 | B | OSV.dev (GHSA-428g-f7cq-pgp5) | 2026-09-21 | unused dependency — AP-17 |
| requests | 2.31.0 | B | OSV.dev (GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2) | 2026-09-21 | unused dependency — AP-17 |
| python-dotenv | 1.0.0 | B | OSV.dev (GHSA-mf9w-mj56-hr94, affects `set_key`) | 2026-09-21 | unused dependency — AP-17 |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Tier-A runtime deprecation scan: only the code paths exercised by the boot, the seed script and read-only GET requests emitted warnings; write-path handlers (POST/PUT/DELETE) were not executed in the audit run → deprecations reachable only from write paths are covered by static site listing, not by observed warnings.
  - Resolved versions: no lockfile exists; versions were read from the installed metadata of a virtual environment created at `.venv/` from `requirements.txt` (exact pins for direct deps; transitive versions are whatever pip resolved on 2026-09-21).

## Proposed, Not Applied
To be determined in Phase 3.

================================
Total: 18 findings
================================

Phase 2 complete. Proceeding with refactoring (Phase 3) — `--yes` was passed (auto-approved, not human-reviewed).
````

## Phase 3 — Final report (appended to `task-manager-api/reports/audit-latest.md`)

````markdown


---

# Phase 3 — Final Report  (2026-09-21 00:25)

Scope applied: all findings (`--yes`, behaves as `y`; auto-approved, not human-reviewed).
Target layout: MVC. Persistence lives inside the model layer (entity + rules + repository per
domain concept, the common MVC reading); `routes/` is the View layer (route declarations plus
explicit response presenters); `controllers/` holds one method per use case; `middlewares/` the
single error boundary; `config/` the environment-backed settings; `app.py` the composition root
(`create_app()` factory). Existing correct names (`models/`, `routes/`, `database.py`, `seed.py`)
were kept.

## Proposed, Not Applied

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/user_routes.py:42-49, controllers/user_controller.py:24-26, 131-152
Reason not applied: every existing client calls every endpoint without credentials; adding
authentication would turn their requests into 401/403. The legitimate policy (who may create users
with a role, change roles, delete users, read other users) cannot be derived from the code without
guessing. The login response keeps its current `token` format (`fake-jwt-token-<id>`) for the same
reason; the code now says explicitly that it is not a verifiable credential.
Proposed change: issue signed, expiring tokens with the (now externalized) `SECRET_KEY`; verify them
in a guard applied on the controller operations (not on single routes); derive the principal and
role from the verified token and stop trusting `role` from request bodies; roll out with a client
migration window.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: routes/presenters.py:60-72
Reason not applied: removing the `password` field changes the response body of `GET /users/<id>`,
`POST /users`, `PUT /users/<id>` and `POST /login`; a client reading the field would observe it
missing. (The hash itself is now a salted scrypt hash, not MD5 — see resolved findings.)
Proposed change: delete the `'password'` line from `presenters.user()`; announce the field removal.

### [HIGH] Deprecated or End-of-Life API Usage   (AP-14)
File: requirements.txt:1-3
Reason not applied: `flask-cors` 6.x (the line that fixes the advisories) changes origin/path
matching semantics, altering CORS headers that browsers observe; the behavioural harness does not
capture response headers, so equivalence could not be verified in this run. The Flask bump is
proposed together so both upgrades are validated in one controlled change.
Proposed change: pin `flask-cors>=6.0.0` (latest 6.0.5 on PyPI, 2026-09-21) and `flask>=3.1.3`;
first add CORS header assertions (preflight + simple request) to the surface inventory, capture,
upgrade, replay.

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models/task.py:99-120, models/user.py:74-75, models/category.py:25-26
Reason not applied: `GET /tasks`, `/users`, `/categories` and `/tasks/search` return the full
collection today; introducing pagination changes what clients receive. (The SMTP part of the
finding was resolved by removing the dead notifier; the seed script now releases its connection.)
Proposed change: `limit`/`offset` (or cursor) parameters with a bounded maximum; decide with the
owners whether the default stays "everything" for a transition period.

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: controllers/category_controller.py:23-51, controllers/user_controller.py:89-122
Reason not applied: the crash paths (malformed values that used to end in HTTP 500) now return 400,
but the remaining rules would reject input that is accepted today: colour format (`#RRGGBB`, the
column holds 7 characters), non-empty `name` on user/category update, strictly boolean `active`
(0/1 are accepted today), and non-object bodies on PUT endpoints (accepted today as a no-op 200).
Proposed change: a declarative boundary schema per endpoint with those rules, released as a
documented validation tightening.

### Related, not a remaining finding — error envelope (AP-09 residual)
File: middlewares/error_handler.py:21-30
Reason not applied: the AP-09 finding is resolved (one boundary, no swallowed errors, logging with
context). Unexpected errors and framework errors (unknown route 404, non-JSON body 415) still render
Flask's standard HTML, exactly as before; switching them to a JSON envelope with a correlation id
would change the error response shape and content type.
Proposed change: `{"error": ..., "correlationId": ...}` for every error response, including 404/415/500.

### Owner actions (not code changes)
- Rotate the signing key and the SMTP password that were committed (`app.py:13` and
  `services/notification_service.py:10` in the original tree). Removing the lines does not remove
  them from git history.
- Users who have not logged in since this change still carry legacy MD5 hashes (verified in
  constant time and replaced by scrypt at their next successful login). Decide a window after which
  remaining legacy hashes are invalidated and a reset is forced.
- `services/notification_service.py` was deleted as dead code (never imported). If notifications are
  wanted, restore it from git history and wire it through the composition root with
  configuration-injected credentials and an SMTP timeout.

## Behaviour changes named (not regressions)
- `search-tasks-bad-priority`, `post-task-bad-priority-type`, `put-task-title-not-string`:
  500 (HTML) → 400 (JSON `{"error": ...}`) — improved from a crash.
- Same class, verified ad hoc after the refactoring only (no baseline entry): non-object JSON body on
  create/login endpoints, container values for `tags`/`description`/`user_id`/`category_id`,
  non-boolean `active`, null `name` on update now return 400 (login: 401) instead of an HTTP 500.
- Startup now requires `SECRET_KEY` in the environment and fails loudly without it; debug mode is off
  unless `FLASK_DEBUG=true`; host/port come from `HOST`/`PORT` (defaults `0.0.0.0`/`5000`, as before).
- Declared-but-unused dependencies `marshmallow`, `requests`, `python-dotenv` were removed; `.env`
  files are no longer auto-loaded (`.env.example` documents the keys to export).

## Re-audit (Phase 3d)

Same catalog, same thresholds, over the refactored tree (28 `.py` files, ~1,508 lines).
Layer 1: all 55 surface entries (every route, including write paths) and `seed.py` executed with
`PYTHONWARNINGS=always::DeprecationWarning python -X dev` — zero warnings of any kind, zero tracebacks.
Layer 2: OSV.dev re-queried 2026-09-21 00:23 for flask 3.0.0, flask-sqlalchemy 3.1.1,
flask-cors 4.0.0, sqlalchemy 2.0.54, werkzeug 3.1.8.

| # | Severity | Id | Remaining finding | Partition |
|---|---|---|---|---|
| 1 | CRITICAL | AP-04 | No authentication/authorization; unverifiable login token; role trusted from body | proposed-not-applied |
| 2 | CRITICAL | AP-08 | Password hash serialized in user responses (routes/presenters.py:60-72) | proposed-not-applied |
| 3 | HIGH | AP-14 | flask-cors 4.0.0 / flask 3.0.0 with published advisories (requirements.txt:1-3) | proposed-not-applied |
| 4 | MEDIUM | AP-13 | Unpaginated collection endpoints | proposed-not-applied |
| 5 | MEDIUM | AP-11 | Format/emptiness rules needing a product decision | proposed-not-applied |

Unresolved: 0. No finding introduced by the refactoring was found. (Considered and not filed: the
`fake-jwt-token-` prefix matches the AP-01 name pattern but is a public, non-secret literal — part of
item 1; legacy-MD5 verification code is a deliberate, time-boxed migration path, not new hashing.)

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── app.py                        composition root: create_app() factory, wiring, error boundary
├── database.py                   Flask-SQLAlchemy extension object
├── seed.py                       sample-data script (uses create_app)
├── requirements.txt
├── .env.example                  every configuration key, placeholders only
├── README.md
├── config/
│   └── settings.py               env read once, validated, frozen Settings
├── models/                       entities, business rules, repositories
│   ├── task.py                   Task, status/priority rules, is_overdue, TaskRepository
│   ├── user.py                   User, password KDF + legacy upgrade, UserRepository
│   ├── category.py               Category, CategoryRepository
│   ├── clock.py                  utc_now() (successor of datetime.utcnow)
│   └── errors.py                 domain error taxonomy
├── controllers/                  one method per use case, no HTTP
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── validation.py             boundary checks for crash-prone input
│   ├── messages.py               shared client-facing messages
│   └── transaction.py            commit/rollback boundary
├── routes/                       View layer: parse -> call -> render
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── category_routes.py        (moved out of report_routes)
│   ├── report_routes.py
│   ├── system_routes.py          / and /health
│   └── presenters.py             explicit response field lists
├── middlewares/
│   └── error_handler.py          single error boundary
└── reports/                      audit, surface inventory, baseline and replay captures
(removed: utils/helpers.py, services/notification_service.py — dead code)

## Validation
  ✓ Application boots without errors  (flask --app app run and python app.py, port 5103 via CLI/env; 0 warnings with detectors forced on)
  ✓ Public surface replayed: 55 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED  (3 PASS are "improved from 500"; identical result on the baseline datastore copy and on a fresh seed)
  ✓ Findings resolved: 13/18  (5 proposed, not applied — see report)
  ○ Anti-patterns remaining: 5 proposed-not-applied, 0 unresolved  (re-audit: 5 findings)

## Proposed, Not Applied
  [CRITICAL] AP-04 Missing authorization / unverifiable login token
  [CRITICAL] AP-08 Password hash field in user responses
  [HIGH]     AP-14 flask-cors / flask upgrades past published advisories
  [MEDIUM]   AP-13 Pagination of collection endpoints
  [MEDIUM]   AP-11 Stricter validation rules needing a product decision
  (related, not a finding: JSON error envelope with correlation id — AP-09 residual)

## Verification Coverage
Full — all planned checks executed (baseline capture, two replays, re-audit with Layer 1 and Layer 2).
What this protocol does not verify, stated so it is not mistaken for coverage:
  - Runtime: the project had no environment; a virtualenv (`.venv/`, git-ignored) was created from
    `requirements.txt` with pip on 2026-09-21. No lockfile exists, so transitive versions are what pip
    resolved that day (SQLAlchemy 2.0.54, Werkzeug 3.1.8). The same environment served baseline and replay.
  - Compared by shape only (per protocol): error message texts, response values, array order/length.
    Messages were preserved by code reading, not by the harness.
  - Response headers are not captured: CORS behaviour was not compared against the baseline (one ad hoc
    post-refactor check only).
  - The crash-path guards listed under "Behaviour changes named" have no baseline entry; their original
    500 behaviour is established by code reading, not observation.
  - Configuration during validation: `SECRET_KEY` set to a placeholder value for the replay runs (the original
    code needed none).
================================
````
