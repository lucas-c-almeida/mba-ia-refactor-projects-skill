================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.13 + Flask 3.0.0
Files:   15 analyzed | ~1,160 lines of code
Date:    2026-09-25 19:21
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    clean at 6d1ce62 (git status showed no diff against HEAD for this project) — leftover, untracked, gitignored/orphaned runtime artifacts from a prior session's Phase 3 run were found alongside the tracked tree (empty controllers/, middlewares/, config/ directories with only __pycache__ contents, and instance/tasks.db) and were excluded from the snapshot; see Verification Coverage.
Runtime: as found for analysis; declared dependencies (requirements.txt) installed inside the container image below, into the run copy only — never into the target
Isolation: container (Docker 28.5.2 / Docker Desktop, image python:3.13-slim)
Scratch: environment scratch directory — C:\Users\lucas\AppData\Local\Temp\claude\D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill\f71d6f47-05b8-4a52-b5b3-8dd608bf42c0\scratchpad\refactor-arch-task-manager-api-20260925-1921\ (protocol §1.1)

## Summary
CRITICAL: 6 | HIGH: 7 | MEDIUM: 14 | LOW: 4
(MEDIUM was 13 at the gate; one additional finding — AP-14, below — surfaced during Phase 3a
baseline provisioning, before any file was edited, and is added here. It is absent from the frozen
`audit-20260925-1921.md`, which reflects only what Layer-1 evidence had been gathered by the gate.
See the note after the AP-14 finding and `## Verification Coverage`.)

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials — Flask signing key   (AP-01)
File: app.py:13-13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` assigns a literal string to Flask's session/CSRF signing key at module scope.
Impact: Anyone with read access to the repository (or a clone, a log, a container layer) can forge session cookies and CSRF tokens. Escalated per catalog: this is a signing key, not just an access credential — forgeable tokens, not just leaked access.
Recommendation: Externalize via RP-01 — read from `SECRET_KEY` environment variable at startup, fail loudly if absent.
Contract: safe

### [CRITICAL] Hardcoded Secrets and Credentials — SMTP credential to a third party   (AP-01)
File: services/notification_service.py:7-10
Description: `self.email_password = 'senha123'` (with host/user also literal) are hardcoded Gmail SMTP credentials, reaching a third-party system.
Impact: Escalated per catalog ("the credential reaches a third-party or production system"): rotation requires a code change and redeploy, and the credential is exposed to anyone who reads the repository.
Recommendation: Externalize via RP-01. Note: this whole class is unreferenced dead code (see AP-17 below) — the cleanest fix is deletion, which also removes the secret.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — no authentication enforced anywhere   (AP-04)
File: routes/task_routes.py:1-299
Description: `POST /login` exists and returns a token (`'fake-jwt-token-' + str(user.id)`), but no route anywhere — not in routes/task_routes.py, routes/user_routes.py, or routes/report_routes.py — checks any `Authorization` header, verifies that token, or scopes a lookup to a caller. Every create/read/update/delete on tasks, users and categories is reachable by anyone with network access to the process, including the destructive ones (DELETE /tasks/<id>, DELETE /users/<id>, DELETE /categories/<id>).
Impact: Escalated per catalog ("flag as maximum urgency when the unprotected operation is destructive... or exposes personal data"): any caller can read, modify or delete any user's data, and the login token is decorative — it authenticates nothing downstream.
Recommendation: RP-04 — introduce a real identity model (verified session or token), a policy function, and enforce it on the operation (controller), not just a route. This is the same finding in routes/user_routes.py and routes/report_routes.py; filed once here as the systemic issue.
Contract: contract-changing — the application has no identity model today (the login token is never verified by any endpoint), so every current client is anonymous. Per the legitimate-use test (`04-architecture-guidelines.md` §6), adding real enforcement would reject every current client, legitimate ones included. Proposed, not applied: introduce token verification middleware plus per-resource ownership/role checks; the identity model, principals and policy need a product decision.

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data — password hashes exposed to unauthenticated callers   (AP-08)
File: models/user.py:16-25
Description: `User.to_dict()` includes `'password': self.password` (the stored hash), and this method backs the response of `GET /users`, `GET /users/<id>`, `POST /users`, `PUT /users/<id>` and `POST /login`. Combined with AP-04 (no authentication anywhere), `GET /users` lets any unauthenticated caller download every user's password hash in one request.
Impact: Escalated from the catalog's HIGH default to CRITICAL because of the AP-04 compounding: this is not an internal leak confined to an authenticated admin view — it is a fully public, unauthenticated bulk credential dump, directly enabling offline cracking of every account (worsened by the weak MD5 hashing in the next finding).
Recommendation: RP-08 — replace the whole-record serialization with an explicit field allow-list (`id`, `name`, `email`, `role`, `active`, `created_at`); never include `password`.
Contract: safe — the shape stays a string-typed field so the response shape is unchanged; mask the value (e.g. a fixed placeholder) rather than dropping the key, since dropping it would itself be a contract change (04-architecture-guidelines.md §6: "removing a field that leaks a secret" is gated, masking is not).

### [CRITICAL] Insecure Runtime Configuration — debug mode + bind-all on the production entry point   (AP-18)
File: app.py:34-34 (context: app.py:9-34)
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` is the same entry point `README.md` documents as the way to run the application, with no environment gate on `debug`. `debug=True` enables the Werkzeug interactive debugger (arbitrary code execution via the debugger console on any unhandled exception), and `host='0.0.0.0'` binds every interface, not just loopback.
Impact: Escalated per catalog ("the debug mode offers an interactive console... and the listener is reachable from outside the host: remote code execution by design"). Any unhandled exception (e.g. the AP-11 finding below) serves the interactive debugger to the network, not just a stack trace.
Recommendation: RP-17 — read `debug` from an environment variable defaulting to `false`; keep `host='0.0.0.0'` (normal for a containerized service) but never derive it from a literal `True`.
Contract: safe — turning debug off on the path the application already runs in production does not change status codes or body shapes for the application's own responses (only the framework's own debugger page disappears, which is not part of the error contract per `04-architecture-guidelines.md` §6).

### [CRITICAL] Known-Vulnerable Dependency — flask-cors 4.0.0, reachable default-enabled advisory   (AP-19)
File: requirements.txt:3-3 (app.py:15 — `CORS(app)` with no configuration)
Description: OSV.dev (queried 2026-09-25) reports flask-cors 4.0.0 affected by GHSA-hxwh-jpp2-84pm / CVE-2024-6221 (github-rated HIGH): the `Access-Control-Allow-Private-Network` header defaults to `true` with no configuration needed to trigger it, fixed in 4.0.2. The app calls bare `CORS(app)` with every default left in place, so the vulnerable default is active and reachable. The same query also returned GHSA-84pr-m4jr-85g5 (log injection at debug log level, MODERATE, fixed 4.0.1) and three MODERATE per-resource regex-matching advisories (GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7, all fixed only in 6.0.0) that concern per-resource CORS pattern matching — a feature this app does not use (no resource patterns are configured, only the global default), so those three are not reachable here.
Impact: Escalated to CRITICAL per catalog ("the advisory is rated critical or high by its source AND the vulnerable code path is reachable... the vulnerable feature is enabled"). Exposes private-network resources to unauthorized external origins by default.
Recommendation: RP-18 — upgrade to flask-cors>=4.0.2 (same major line as installed, closes the HIGH and the log-injection MODERATE advisory). The three regex-matching MODERATE advisories require 6.0.0 (a major bump) and are not reachable given this app's configuration; noted for completeness, not acted on.
Contract: safe — 4.0.0 → 4.0.2 is a patch-level upgrade within the same major version; no behaviour this app exercises changes.

### [HIGH] Business Logic in the Delivery Layer — routes/task_routes.py   (AP-05)
File: routes/task_routes.py:1-299
Description: Every handler in this blueprint issues ORM calls directly (`Task.query...`, `db.session...`), and re-implements domain rules inline: status/priority validation (lines 110-114, 181-184), overdue determination (lines 30-39, 71-80, 282-287), and tag serialization — with no controller or service in between. Below the ~300-400 line God-Module threshold and holding a single domain concept (tasks), so filed as AP-05 rather than AP-03 per the catalog's precedence rule.
Impact: None of this logic can be tested without a running Flask app and a database; a second entry point (a CLI import job, a scheduled job) would have to duplicate all of it.
Recommendation: RP-05 — extract a `TaskController` per use case; handlers become parse → call → render.
Contract: safe — extraction preserves routes, status codes and body shapes.

### [HIGH] Business Logic in the Delivery Layer — routes/user_routes.py   (AP-05)
File: routes/user_routes.py:1-211
Description: Persistence (`User.query...`, `db.session...`) and business rules (email format, password length, role whitelist, login credential check) are all inline in the route handlers, with no controller layer.
Impact: Same as above — untestable without the framework and the database; the login rule cannot be reused by a second entry point.
Recommendation: RP-05 — extract a `UserController` (including `authenticate`); handlers reduce to parse → call → render.
Contract: safe.

### [HIGH] Business Logic in the Delivery Layer — category CRUD in routes/report_routes.py   (AP-05)
File: routes/report_routes.py:167-223
Description: `create_category`, `update_category` and `delete_category` issue persistence calls and validation directly in the handler, with no controller.
Impact: Same class of issue as above, confined to the category use cases.
Recommendation: RP-05 — extract a `CategoryController`.
Contract: safe.

### [HIGH] Hard-Wired Dependencies / No Composition Root — app.py builds and mutates state at import time   (AP-06)
File: app.py:1-34
Description: `app = Flask(__name__)`, `db.init_app(app)`, blueprint registration and `with app.app_context(): db.create_all()` (lines 9-31) all execute at module import time, with no factory function. `seed.py` already depends on this by doing `from app import app, db` (seed.py:2), which re-triggers the same import-time side effects merely to obtain a reference.
Impact: The module cannot be imported for a test, or imported twice in one process, without re-running schema creation against a live database connection. There is no single place that assembles the object graph.
Recommendation: RP-06 — introduce a `create_app()` factory as the composition root; keep the module-level `app` only as `create_app()`'s result under the `__main__` guard.
Contract: safe — wiring is not observable; the boot command and behaviour are unchanged.

### [HIGH] Unsafe Handling of Credentials and Sensitive Data — MD5, unsalted password hashing   (AP-08)
File: models/user.py:27-32
Description: `set_password`/`check_password` hash with `hashlib.md5(pwd.encode()).hexdigest()` — a fast, general-purpose digest with no salt and no work factor.
Impact: MD5 is crackable at billions of attempts per second on commodity hardware; combined with the AP-08 finding above (hashes are publicly readable), every password is realistically recoverable.
Recommendation: RP-08 — move to a purpose-built password KDF (e.g. `werkzeug.security.generate_password_hash`/`check_password_hash`, already a transitive dependency of Flask) with a transparent upgrade-on-login path for existing MD5 hashes.
Contract: safe — done as a transparent upgrade-on-login, a legitimate client's login behaviour (right password succeeds, wrong password fails) is unchanged.

### [HIGH] Swallowed or Uncentralized Error Handling — bare/over-broad excepts, no centralized handler   (AP-09)
File: routes/task_routes.py:146-154
Description: The same `try: ... db.session.commit() ... except Exception as e: db.session.rollback(); return jsonify({'error': '...'}), 500` (or a bare `except:`) shape is copied into nearly every write handler: task_routes.py:62-63, 146-154, 217-223, 236-238; user_routes.py:87-90, 127-132, 144-151; report_routes.py:182-188, 204-209, 217-223. No `@app.errorhandler` is registered anywhere, so any exception these don't catch reaches Flask's own debug-mode handler (compounds with AP-18).
Impact: Failures are handled inconsistently (some routes 500 with a generic message, others let the interactive debugger take over), and every handler repeats the same boilerplate, which will drift as more are added.
Recommendation: RP-09 — a small domain error taxonomy plus one `@app.errorhandler` registered in the composition root, preserving the existing status codes and body shapes.
Contract: safe — centralizing while preserving the existing status codes and `{'error': ...}` shape is explicitly safe per `04-architecture-guidelines.md` §6.

### [HIGH] Missing Schema-Level Integrity Constraints — category deletion orphans tasks   (AP-20)
File: routes/report_routes.py:211-223 (also database.py:1-3, models/task.py:13-14)
Description: `tasks.category_id` is declared as `db.ForeignKey('categories.id')`, but SQLite only enforces foreign keys when `PRAGMA foreign_keys=ON` is set per connection, and nothing in database.py or app.py sets it. `delete_category` (report_routes.py:211-223) deletes a category with no check for, and no handling of, tasks that reference it — unlike `delete_user` (user_routes.py:134-151), which does explicitly delete dependent tasks first.
Impact: Escalated from the catalog's MEDIUM default to HIGH ("lets... the children stay pointing at nothing"): this is not a hypothetical gap, it is a concretely demonstrable orphaning path with no compensating application code, unlike the equivalent user-deletion path which was handled.
Recommendation: RP-19 — decide and implement a delete policy for the category→task relationship (restrict, cascade, or set null), then enable FK enforcement to make the schema hold it.
Contract: contract-changing — today, deleting a referenced category silently succeeds and leaves the orphaned reference; any of restrict/cascade/set-null changes what that same call observes (success vs. rejection, or a different task state). Proposed, not applied — needs a product decision on which policy to apply; see `## Proposed, Not Applied`.

### [MEDIUM] N+1 Query — routes/task_routes.py get_tasks   (AP-10)
File: routes/task_routes.py:11-63
Description: One query loads all tasks, then for each task `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` run inside the loop (lines 41-57) — up to 2N extra round trips for N tasks.
Impact: Latency grows linearly with the number of tasks; this endpoint has no pagination (see AP-13), so N is also unbounded.
Recommendation: RP-10 — one join or two batched `IN` queries instead of per-row lookups.
Contract: safe.

### [MEDIUM] N+1 Query — routes/user_routes.py get_users   (AP-10)
File: routes/user_routes.py:10-25
Description: `'task_count': len(u.tasks)` inside `for u in users:` (lines 14-24) accesses a lazy-loaded relationship per user, issuing one query per user.
Impact: Same latency-growth pattern as above, on the users list endpoint.
Recommendation: RP-10 — replace with a single grouped count query (`SELECT user_id, COUNT(*) ... GROUP BY user_id`) joined into the result.
Contract: safe.

### [MEDIUM] N+1 Query — routes/report_routes.py summary_report per-user loop   (AP-10)
File: routes/report_routes.py:53-68
Description: `for u in users: user_tasks = Task.query.filter_by(user_id=u.id).all()` — one query per user to build `user_productivity`.
Impact: Same pattern; this endpoint additionally does a full-table `Task.query.all()` earlier in the same function (line 30) for the overdue list.
Recommendation: RP-10 — one grouped aggregate query for per-user totals/completions.
Contract: safe.

### [MEDIUM] N+1 Query — routes/report_routes.py get_categories   (AP-10)
File: routes/report_routes.py:157-165
Description: `cat_data['task_count'] = Task.query.filter_by(category_id=c.id).count()` inside `for c in categories:`.
Impact: Same pattern, on the categories list endpoint.
Recommendation: RP-10 — one grouped count query joined into the category list.
Contract: safe.

### [MEDIUM] Missing Boundary Validation — update_category dereferences an absent body   (AP-11)
File: routes/report_routes.py:190-202
Description: Unlike every other write handler in this codebase, `update_category` does `data = request.get_json()` and immediately does `if 'name' in data:` with no `if not data: return 400` guard. A request with no JSON body, or a non-object JSON body, raises `TypeError` inside the handler.
Impact: A malformed request becomes an unhandled 500 (and, given AP-18, serves the interactive debugger) instead of a clear 400 — the same class of request every sibling handler already rejects cleanly.
Recommendation: RP-11 — add the same `if not data: return jsonify({'error': ...}), 400` guard used elsewhere in this file.
Contract: safe — rejecting a request with no legitimate use (an empty/absent body on an update) is a value no legitimate client sends.

### [MEDIUM] Missing Boundary Validation — unhandled int() parsing in search_tasks   (AP-11)
File: routes/task_routes.py:240-265
Description: `priority = request.args.get('priority', '')` then `Task.priority == int(priority)` (line 261), and similarly `int(user_id)` (line 264) — a non-numeric query value raises `ValueError` with no surrounding `try`/`except`.
Impact: Same class as above: a malformed query string becomes a 500 instead of a 400.
Recommendation: RP-11 — validate/parse with a failure path that returns 400 on a non-numeric value.
Contract: safe.

### [MEDIUM] Duplicated Logic — overdue determination repeated across six live call sites   (AP-12)
File: routes/task_routes.py:30-39
Description: The rule "`due_date` is set, is in the past, and `status` is not `done`/`cancelled`" is independently re-implemented in: routes/task_routes.py:30-39 (get_tasks), :71-80 (get_task), :282-287 (task_stats); routes/user_routes.py:171-180 (get_user_tasks); routes/report_routes.py:34-43 (summary_report), :132-135 (user_report). A seventh copy exists as `Task.is_overdue()` (models/task.py:50-60) but is never called by any of the six — see AP-17.
Impact: All six copies currently agree, but a future rule change (e.g. a grace period) has six places to update and one of them will be missed; this is the exact "forgotten copy becomes a latent defect" impact the catalog describes.
Recommendation: RP-12 — extract to a single `Task.is_overdue()`-style method or module function and call it from all six sites (the model already has the right shape; it's just unused).
Contract: safe — the copies agree today, so unifying them changes nothing observable.

### [MEDIUM] Duplicated Logic — status/priority valid-value sets and bounds repeated   (AP-12)
File: routes/task_routes.py:110-114
Description: The literal list `['pending', 'in_progress', 'done', 'cancelled']` and the bounds check `1 <= priority <= 5` are repeated at task_routes.py:110-114 and :177-184, again as `Task.validate_status`/`validate_priority` (models/task.py:38-48, unused — see AP-17), and again as `VALID_STATUSES`/constants in utils/helpers.py:75,84,110-115 (also unused).
Impact: Four independent copies of the same two invariants; a fifth valid status added in one place would silently not be enforced in the others.
Recommendation: RP-12 + RP-15 — one named constant/set per invariant, referenced everywhere.
Contract: safe.

### [MEDIUM] Duplicated Logic — email format validation repeated   (AP-12)
File: routes/user_routes.py:61-61
Description: The regex `r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'` is repeated verbatim at user_routes.py:61 and :106, and a third time as the unused `utils/helpers.py:validate_email` (line 19-23).
Impact: Same class as above — three copies of one rule.
Recommendation: RP-12 — one `is_valid_email` used by both call sites; delete the unused third copy (AP-17).
Contract: safe.

### [MEDIUM] Unbounded Resources — no pagination on any list endpoint   (AP-13)
File: routes/task_routes.py:11-63 (also routes/user_routes.py:10-25, routes/report_routes.py:157-165)
Description: `GET /tasks`, `GET /users` and `GET /categories` all load the full table and return every row, with no limit/offset/page parameter anywhere in the codebase.
Impact: Response size and processing cost grow without bound as data grows; this compounds the N+1 findings above rather than duplicating them — fixing the N+1s alone would still leave an unbounded response.
Recommendation: RP-13 — add a bounded default page size with an explicit opt-out.
Contract: contract-changing — clients today receive the full collection in one response; introducing pagination changes that shape/semantics for existing callers per `05-refactoring-playbook.md` RP-13. Proposed, not applied.

### [MEDIUM] Magic Values — validation bounds and defaults duplicated as literals   (AP-15)
File: models/task.py:45-48
Description: Priority bounds (`1`/`5`), title length bounds (`3`/`200`), minimum password length (`4`) and the default category color (`'#000000'`) appear as bare literals in models/task.py:45-48, routes/task_routes.py:96-100,113-114,182-183, routes/user_routes.py:64-65, and routes/report_routes.py:180 — even though utils/helpers.py already defines named constants for most of them (lines 110-116) that nothing uses.
Impact: Escalated from the catalog's LOW default to MEDIUM per catalog rule ("the same magic value appears in several modules that must agree"): five-plus independent modules must stay in sync on the same two or three numbers.
Recommendation: RP-15 — one constants module, imported everywhere these are checked (or wire up the already-written-but-unused constants in utils/helpers.py).
Contract: safe.

### [MEDIUM] Known-Vulnerable Dependency — three unused runtime dependencies each carry an advisory   (AP-19)
File: requirements.txt:4-6
Description: OSV.dev (queried 2026-09-25) reports: marshmallow 3.20.1 — GHSA-428g-f7cq-pgp5/CVE-2025-68480, MODERATE, DoS in `Schema.load(many=True)`, fixed 3.26.2; requests 2.31.0 — three advisories (GHSA-9hjg-9r4m-mvj7, GHSA-9wx4-h78v-vm56, GHSA-gc5v-m9x4-r6x2), all MODERATE, fixed by 2.33.0; python-dotenv 1.0.0 — GHSA-mf9w-mj56-hr94/CVE-2026-28684, MODERATE, symlink-following file overwrite in `set_key`/`unset_key`, fixed 1.2.2. None of the three packages is imported anywhere in this codebase (confirmed — see AP-17).
Impact: De-escalated per catalog ("the vulnerable feature is demonstrably unused — the affected module is never imported"): zero runtime exposure today, but each is a live advisory against the exact pinned version, and an unmaintained, unused dependency is also install-time attack surface (supply chain) for no benefit.
Recommendation: RP-18/RP-16 — since none of the three is used, delete them from requirements.txt rather than upgrading dead weight; flask-sqlalchemy 3.1.1 returned no advisories (queried 2026-09-25) and is the only ORM dependency actually needed.
Contract: safe — removing an unused, undeclared-in-code dependency has no observable effect.

### [LOW] Dead Code — services/notification_service.py is entirely unreferenced   (AP-17)
File: services/notification_service.py:1-48
Description: `NotificationService` is never imported or instantiated anywhere else in the codebase (confirmed by search) — no route creates or assigns tasks and notifies anyone.
Impact: Read, and now audited, at full cost while doing nothing; also the container for the AP-01 SMTP-credential finding above.
Recommendation: RP-16 — delete the file (its secret finding is resolved as a side effect); if notifications are wanted, reintroduce as an adapter behind a port the domain declares (04-architecture-guidelines.md §3), wired from the composition root.
Contract: safe.

### [LOW] Dead Code — utils/helpers.py is a largely unreferenced grab-bag   (AP-17)
File: utils/helpers.py:1-117
Description: Of nine functions and five constants, only `parse_date` has a caller — from `process_task_data`, which itself has no caller anywhere in the codebase. `format_date`, `calculate_percentage`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color` and the five constants are all unreferenced. The module also mixes unrelated concerns (formatting, validation, ID generation, logging, a whole request-parsing helper) with no shared theme — the "utilities" grab-bag signal the catalog associates with AP-03; filed here as AP-17 rather than as a God Module because none of it executes, so the God-Module impact (blast radius, untestability) does not actually apply to code nothing calls.
Impact: A reader has to check each function's callers to learn it does nothing; the named constants that would have fixed the AP-15 finding above are sitting unused right next to the problem they'd solve.
Recommendation: RP-16 — delete the whole file; where the refactor needs equivalent behaviour (date formatting, email validation), write it once in the layer that owns it and wire the existing constants in rather than reintroducing new literals.
Contract: safe.

### [LOW] Dead Code — Task model's own validation/overdue methods are never called   (AP-17)
File: models/task.py:38-60
Description: `validate_status`, `validate_priority` and `is_overdue` are defined on `Task` but no route or script calls any of them — every call site re-implements the same checks inline instead (cross-reference AP-12 above).
Impact: The one place these rules *should* live already exists and is correct; the duplication elsewhere is doubly avoidable.
Recommendation: RP-16/RP-12 — wire these into the six duplicated call sites instead of deleting them; this is the fix for the AP-12 finding above, not a separate action.
Contract: safe.

### [LOW] Dead Code — unused imports and declared-but-unimported packages   (AP-17)
File: routes/task_routes.py:7-7
Description: `import json, os, sys, time` (task_routes.py:7) — none of the four names is used anywhere in the file. Same pattern: `hashlib, json` unused in routes/user_routes.py:6; `json` unused in routes/report_routes.py:8; `json` unused in models/task.py:3.
Impact: Minor noise; a reader assumes an unused import signals intended-but-abandoned behaviour and spends time confirming otherwise.
Recommendation: RP-16 — remove the unused imports.
Contract: safe.

### [MEDIUM] Insecure Runtime Configuration — permissive cross-origin policy   (AP-18)
File: app.py:15-15
Description: `CORS(app)` is called with no configuration, which applies flask-cors' wildcard-origin default to every route, including every write endpoint (there is no read-only/public-data carve-out).
Impact: Any website can script a cross-origin request against this API. De-escalated from the catalog's HIGH bar because the app sets no cookies and `supports_credentials` is not enabled, so the classic cookie-riding CSRF amplification does not apply directly — but combined with AP-04 (no auth at all), the API is already fully open, so this specifically is not what makes it exploitable.
Recommendation: RP-17 — restrict to an explicit allow-list of origins, configurable per environment.
Contract: contract-changing — narrowing the origin policy changes which origins can call the API today; proposed, not applied, pending the list of origins that should be allowed.

### [MEDIUM] Deprecated API Usage — `datetime.datetime.utcnow()` throughout   (AP-14)
File: seed.py:66-74
Description: **Discovered after the gate, before any file was edited** — during Phase 3a's baseline
provisioning (running `seed.py` against the original in a run copy, per this phase's own step 2/3),
not during the Phase 2 Layer-1 check itself, which had only run `import app` and did not exercise
this code path. Tier A evidence: `PYTHONWARNINGS=always::DeprecationWarning python -X dev` on
`seed.py` (container `refactor-arch-task-manager-api-20260925-1921-1`, 2026-09-25) emitted
`DeprecationWarning: datetime.datetime.utcnow() is deprecated ... Use ... datetime.now(datetime.UTC)`
at seed.py:66,67,69,70,74. The identical construct (confirmed by search, not by memory) also occurs
at: models/task.py:15,16,52; models/user.py:14; models/category.py:11;
routes/task_routes.py:31,72,215,285; routes/user_routes.py:172; routes/report_routes.py:35,42,45,71,133;
services/notification_service.py:35; utils/helpers.py:38.
Impact: `datetime.utcnow()` is deprecated as of this Python version; a future interpreter will remove
it. Its documented successor, `datetime.now(datetime.UTC)`, is **not** a drop-in replacement here —
it returns a timezone-*aware* value, while every column and comparison in this codebase is naive;
comparing the two raises `TypeError`. A careless RP-14 application would have broken every
overdue/timestamp comparison in the app.
Recommendation: RP-14 — a single naive-preserving helper (`datetime.now(timezone.utc).replace(tzinfo=None)`)
used everywhere the deprecated call was, so the migration is behaviourally identical rather than
merely syntactically modern.
Contract: safe.

**Why this entry exists here and not in the frozen `audit-20260925-1921.md`:** that file is the audit
"as it stood at the gate" (SKILL.md, D5) and must not be edited afterward. This finding was not yet
observed at that moment — Phase 2's Layer-1 check only ran `import app`, which never executes this
line. Running the fuller provisioning step in Phase 3a (which the protocol also requires: booting the
original before capturing a baseline) surfaced it before any target file was touched. Treating it as a
normal Phase 2 finding here — rather than silently fixing it off the books, or silently omitting it —
is the same "never degrade silently" principle applied to a gap in *this run's own* Layer-1 coverage.
It is fixed below like any other MEDIUM finding, and is not tagged `missed-in-phase-2` because the
formal Phase 3d re-audit never had a chance to miss it — it was already fixed by the time that ran.
See `## Verification Coverage` for the same note, and the final report for the calibration
implication: a Layer-1 deprecation check that only imports the entry point has a real recall gap
against constructs that only run when the code executes, not merely imports.

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-like identifier names; connection URLs with inline creds; high-entropy literals; signing/session config; committed credential files; unsafe defaults | 2 findings (CRITICAL x2, above) |
| AP-02 | string-built driver calls; interpolation before the driver call; ORM raw escape hatches; dynamic identifiers; shell/process exec; deserialization/template injection; path traversal | none — `.like()`/`.filter()` calls are parameter-bound by SQLAlchemy throughout; no raw SQL, `os.system`, `eval`, or unvalidated path joins found |
| AP-03 | 3+ mixed responsibility categories; size threshold + 2+ categories; single unit complexity; several unrelated domain concepts; low-cohesion class; "utils/manager" grab-bag; high afferent coupling | none filed as AP-03 — task_routes.py mixes categories but stays under the size threshold with one domain concept (→ AP-05 per precedence rule); utils/helpers.py is a grab-bag but entirely dead (→ AP-17) |
| AP-04 | unauthenticated resource access; IDOR (filter by input id only); delivery-only enforcement; trusted role/tenant from request; unverified token; unreachable guard | 1 finding (CRITICAL, systemic across all three route files) |
| AP-05 | domain decisions in handlers; persistence in handlers; handler >30 lines; framework objects deep in the stack; duplicated rule across handlers; pass-through service/controller | 3 findings (HIGH) |
| AP-06 | self-constructed collaborators; import-time side effects; no composition root; untestable without live infra; concrete types where abstraction is needed; env read at point of use | 1 finding (HIGH) |
| AP-07 | reassigned module/static globals; request-scoped data in a global; in-memory store of record; mutable default parameter; unbounded cache/pool; monkey-patching; in-process counters | none — `db = SQLAlchemy()` and `app = Flask(__name__)` are the framework's own immutable-after-init singletons, not mutated application state; no other module-level mutable state found |
| AP-08 | reversible credential storage; fast general-purpose digest; missing/shared salt; non-constant-time comparison; sensitive values logged; whole-record serialization; unprotected transport; no token expiry | 2 findings (CRITICAL, HIGH) |
| AP-09 | empty/log-and-continue catch; over-broad catch; repeated error-mapping per handler; no centralized handler (observe framework default); leaked internals in response; inconsistent error signalling; unbounded partial-write state; exceptions for control flow | 1 finding (HIGH) |
| AP-10 | driver/ORM call inside a loop; per-element FK lookup; lazy relation accessed in iteration; repeated single-arg reads instead of one set query; remote call in a loop; whole table read for in-app aggregation; per-element write loop | 4 findings (MEDIUM) |
| AP-11 | input used directly with no presence/type/range/format check; optional input dereferenced unchecked; unconstrained pagination param; numeric parse with no failure path; validation on one entry point but not a sibling; validation after side effect; unenforced domain invariants; no upper bound on body/array size; ad-hoc scattered validation | 2 findings (MEDIUM) |
| AP-12 | structurally identical blocks; same rule in >1 place; same validation/error-mapping/serialization repeated; hand-written mapping duplicated; copy-and-modify lineage with divergence; repeated constant; repeated guard condition | 3 findings (MEDIUM) |
| AP-13 | scope-unbound acquire/release; unreleased handle on failure path; per-call connection where a pool exists; outbound call with no timeout; unbounded/no-backoff retry; unbounded read into memory; unbounded accumulator/cache; task/thread with no shutdown path; unbounded recursion | 1 finding (MEDIUM) |
| AP-14 | forced runtime deprecation warnings (Layer 1); manifest/lockfile deprecation markers; structurally superseded constructs (callback-vs-async, sync-vs-async, hand-rolled-vs-native) | 1 finding (MEDIUM) — surfaced during Phase 3a provisioning (running seed.py), not during the Phase 2 `import app`-only check; see the finding above and Verification Coverage |
| AP-15 | unexplained numeric literal in decision/computation; unitless duration/size; repeated string-enum literal; numeric code without a named constant; unnamed index/offset; inline environment-specific literal | 1 finding (MEDIUM, escalated) |
| AP-16 | name contradicts behaviour; non-descriptive identifiers outside tiny scope; several names for one concept; name describing how not what; mixed casing/pluralization conventions; mixed human languages inconsistently; inconsistent file/dir naming; stale comment contradicting code; unreadable boolean parameters | none — checked for mixed-language inconsistency specifically (Portuguese user-facing strings alongside English code) and found it consistent and deliberate throughout, not a violation; no other signal met the bar for a reportable finding |
| AP-17 | commented-out code; unreachable branch; defined-but-never-referenced unit; unused import; declared-but-unimported dependency; unread parameter/unused computed value; stale feature flag; unreachable endpoint; parallel old-copy file | 4 findings (LOW) |
| AP-18 | debug/dev/reload mode on the started path; framework dev server as the production server; bind-all combined with debug or a diagnostic endpoint; internals exposed in error output (own handler or framework default); permissive cross-origin with credentials or reflected origin; unrestricted diagnostic/admin surfaces; disabled protective defaults | 2 findings (1 CRITICAL, 1 MEDIUM) |
| AP-19 | OSV.dev query per direct dependency at its resolved/pinned version; reachability of the vulnerable feature; lockfile-vs-manifest fixed-version mismatch | 2 findings (1 CRITICAL — flask-cors; 1 MEDIUM — marshmallow/requests/python-dotenv, unused); flask 3.0.0 has one LOW advisory (folded into the Dependency and Deprecated API Verification table below, not filed as a separate catalog finding since it is below the reporting-worthy bar on its own merits — see that table); flask-sqlalchemy 3.1.1: no advisories found |
| AP-20 | identity-treated column with no uniqueness constraint; FK-shaped column with no FK declaration, or declared-but-never-enabled FK; parent delete with no rule for children; money stored in binary float; always-required column left nullable / closed set stored as free text | 1 finding (HIGH); users.email already has a real uniqueness constraint — checked, no finding needed there |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Python / Flask / Flask-SQLAlchemy / Flask-Cors import-time behaviour | 3.13 / 3.0.0 / 3.1.1 / 4.0.0 | deprecation (Layer 1, forced on: `PYTHONWARNINGS=always::DeprecationWarning python -X dev -c "import app"`) | A | runtime warning capture (container run-1) | n/a — local, 2026-09-25 | no DeprecationWarning emitted (one unrelated ResourceWarning about an unclosed sqlite connection at script exit — not a deprecation, not filed) |
| flask | 3.0.0 | advisory | B | OSV.dev (GHSA-68rp-wp8r-4726 / CVE-2026-27205) | 2026-09-25 | LOW-rated advisory (missing `Vary: Cookie` on some session access); this app never uses Flask's `session` object at all, so the affected code path is unreachable; not filed as a catalog finding on its own (below the reporting bar), but folded into the flask-cors RP-18 recommendation: upgrade flask to >=3.1.3 alongside it (same major, safe) |
| flask-sqlalchemy | 3.1.1 | advisory | B | OSV.dev | 2026-09-25 | no advisories found |
| flask-cors | 4.0.0 | advisory | B | OSV.dev (6 advisories, see AP-19 CRITICAL finding) | 2026-09-25 | reported above |
| marshmallow | 3.20.1 | advisory | B | OSV.dev (GHSA-428g-f7cq-pgp5 / CVE-2025-68480) | 2026-09-25 | reported above (unused) |
| requests | 2.31.0 | advisory | B | OSV.dev (3 advisories) | 2026-09-25 | reported above (unused) |
| python-dotenv | 1.0.0 | advisory | B | OSV.dev (GHSA-mf9w-mj56-hr94 / CVE-2026-28684) | 2026-09-25 | reported above (unused) |

No manifest/lockfile deprecation markers found (no lockfile exists — requirements.txt exact-pins every direct dependency, so it is treated as the resolved set per `01-project-analysis.md` §2). No structurally-superseded constructs (callback-vs-async, sync-vs-async) apply to this codebase.

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-task-manager-api-20260925-1921-1 | docker run -d --name refactor-arch-task-manager-api-20260925-1921-1 --label refactor-arch.run=task-manager-api-20260925-1921 -v <run-1>:/app -v <scripts>:/skill:ro -v <target>/reports:/reports python:3.13-slim sleep infinity | started, container id 0375943f9f7c |
| 2 | 2 | exec | container | refactor-arch-task-manager-api-20260925-1921-1 | pip install --quiet --no-input -r /app/requirements.txt | dependencies installed (root-user pip warning only) |
| 3 | 2 | exec | container | refactor-arch-task-manager-api-20260925-1921-1 | env PYTHONWARNINGS=always::DeprecationWarning, cwd /app: python -X dev -c "import app" | exit 0; one ResourceWarning, no DeprecationWarning |

(Container #1 was reused for the Phase 3a baseline capture against the same original code — rows
continue below. This note stays in the frozen file as written at the gate.)

**Phase 3 rows** (appended here; the timestamped file above stops at row 3):

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 4 | 3a | exec | container | ...-1 | seed.py in /app | seeded; 5 DeprecationWarning (AP-14, see finding) |
| 5 | 3a | start (app) | container | ...-1 | exec -d python app.py | ready on :5000 |
| 6 | 3a | capture | container | ...-1 | probe.py capture (24 non-destructive entries) | 24 observed, 0 error -> baseline.json |
| 7 | 3a | stop | container | ...-1 | docker rm -f (exact name) | removed |
| 8 | 3a | start | container | ...-2 | run-2 copy, sleep infinity | started |
| 9 | 3a | capture (destructive) | container | ...-2 | probe.py capture --only delete-task --merge | 1 observed -> baseline.json (25 total) |
| 10 | 3a | stop | container | ...-2 | docker rm -f | removed |
| 11 | 3a | start | container | ...-3 | run-3 copy, sleep infinity | started |
| 12 | 3a | capture (destructive) | container | ...-3 | probe.py capture --only delete-user --merge | 1 observed -> baseline.json (26 total) |
| 13 | 3a | stop | container | ...-3 | docker rm -f | removed |
| 14 | 3a | start | container | ...-4 | run-4 copy, sleep infinity | started |
| 15 | 3a | capture (destructive) | container | ...-4 | probe.py capture --only delete-category-with-tasks --merge | 1 observed -> baseline.json (27 total) |
| 16 | 3a | stop | container | ...-4 | docker rm -f | removed |
| 17 | 3c | start | container | ...-r1 | refactored-1 copy, sleep infinity | started (first replay pass, before the AP-10 category fix) |
| 18 | 3c | compare | container | ...-r1 | probe.py compare (24 non-destructive entries) | 22 PASS, 0 REGRESSION, 2 FIXED |
| 19 | 3c | stop | container | ...-r1 | docker rm -f | removed |
| 20 | 3c | start | container | ...-r2 | refactored-2 copy, sleep infinity | started |
| 21 | 3c | capture+compare (destructive) | container | ...-r2 | probe.py capture --only delete-task; compare --current | delete-task PASS |
| 22 | 3c | stop | container | ...-r2 | docker rm -f | removed |
| 23 | 3c | start | container | ...-r3 | refactored-3 copy, sleep infinity | started |
| 24 | 3c | capture+compare (destructive) | container | ...-r3 | probe.py capture --only delete-user; compare --current | delete-user PASS |
| 25 | 3c | stop | container | ...-r3 | docker rm -f | removed |
| 26 | 3c | start | container | ...-r4 | refactored-4 copy, sleep infinity | started |
| 27 | 3c | capture+compare (destructive) | container | ...-r4 | probe.py capture --only delete-category-with-tasks; compare --current | NOT FIXED (proposed, expected) |
| 28 | 3c | stop | container | ...-r4 | docker rm -f | removed |
| 29 | 3d (fix) | (code edit, no process) | — | — | fixed the missed category N+1 (controllers/category_controller.py) | — |
| 30 | 3c (re-verify) | start | container | ...-r5 | refactored-5 copy (post-fix), sleep infinity | started — this is the FINAL, authoritative full pass |
| 31 | 3c (re-verify) | compare | container | ...-r5 | probe.py compare (24 non-destructive entries) | 22 PASS, 0 REGRESSION, 2 FIXED (list-categories still PASS) |
| 32 | — | capture (non-isolated, see INCIDENT) | container | ...-r5 | probe.py capture --only delete-task | PASS, but DISCARDED — not isolated, see Verification Coverage |
| 33 | 3c | stop | container | ...-r5 | docker rm -f | removed |

Every handle above is the exact container name `refactor-arch-task-manager-api-20260925-1921-<n>`
(`...-1` through `...-4`, `...-r1` through `...-r5`), each removed by that exact name. A final
`docker ps -a --filter label=refactor-arch.run=task-manager-api-20260925-1921` (twice: once before
deleting the snapshot, once confirmed empty) returned no containers. 9 containers started, 9
stopped through their exact handles, 0 left running, 0 out-of-log process actions.

## Verification Coverage
DEGRADED — the following did not run at full strength, and the findings above do not extend past what is stated:
  - Source-tree exclusions: empty leftover `controllers/`, `middlewares/`, `config/` directories (containing only stale `__pycache__` bytecode from a prior, unrelated session) and `instance/tasks.db` were found alongside the tracked tree and excluded from analysis and from the snapshot copy (`proc copy --exclude`). They contain no `.py` source and were not audited; they are not part of this run's evidence and are not claimed to be clean.
  - AP-16 (mixed-language naming) was checked and explicitly not filed (see Catalog Coverage) rather than skipped — noted here only because a reader scanning for "what wasn't looked at" should see it was in fact looked at.

No process or container action outside the Execution Log occurred. No command in this phase required a non-literal path or shell substitution (protocol §1.4) except that container-internal paths (`/app`, `/skill`) had to be issued through PowerShell rather than the Bash/git-bash tool, because git-bash's POSIX-path emulation rewrites `/app` to a Windows path before Docker sees it (protocol §1.4, "keep container paths out of a shell that rewrites them") — this is declared here as the literal-command rule required, not a NON-LITERAL exception; every command actually sent to Docker was fully literal.

================================
Total: 31 findings
================================

Confirmation: --yes (auto-approved, not human-reviewed)

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
task-manager-api/
├── .env.example                    (new — documents every setting AP-01/AP-18 externalized)
├── app.py                          (composition root: create_app() factory — AP-06)
├── config/
│   ├── __init__.py
│   └── settings.py                 (the only module that reads os.environ)
├── controllers/                    (new layer — use-case orchestration, AP-05)
│   ├── __init__.py
│   ├── category_controller.py
│   ├── report_controller.py
│   ├── task_controller.py
│   └── user_controller.py
├── database.py                     (db = SQLAlchemy(); + utcnow() helper, AP-14)
├── middlewares/                    (new — centralized error boundary, AP-09)
│   ├── __init__.py
│   ├── error_handler.py
│   └── errors.py                   (small domain error taxonomy)
├── models/                         (unchanged location; rules wired in instead of duplicated)
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── README.md
├── reports/                        (audit output — not part of the application)
├── requirements.txt                (flask 3.1.3, flask-sqlalchemy 3.1.1, flask-cors 4.0.2 —
│                                     marshmallow/requests/python-dotenv removed, AP-17/AP-19)
├── routes/                         (unchanged location; now parse -> call -> render only)
│   ├── __init__.py
│   ├── report_routes.py
│   ├── task_routes.py
│   └── user_routes.py
└── seed.py                         (now calls create_app(), not a module-level import)

Removed entirely (AP-17 — confirmed unreferenced before deletion):
  services/   (notification_service.py: never instantiated anywhere; also resolved AP-01's
               hardcoded SMTP credential as a side effect of deletion)
  utils/      (helpers.py: 8 of 9 functions and all 5 constants unreferenced; the one function
               with a caller was itself only called by another unreferenced function)

Layering choice, stated per 04-architecture-guidelines.md §2: persistence stays inside the model
layer (Task.query / User.query / Category.query, ActiveRecord-style) rather than a separate
repositories/ package — the project's size does not warrant the extra indirection, and controllers
never issue a driver/session call directly, so the controller/model boundary is still real.

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 24 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 2 FIXED, 1 NOT FIXED (the NOT FIXED entry's finding, AP-20, is
    PROPOSED, NOT APPLIED below — this result is expected and declared, not a failure)
  ○ Findings resolved: 27/31  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 4 proposed-not-applied, 0 unresolved  (re-audit: 4 findings)
    Re-audit passes: 1; fixed after re-audit: 0 (0 of them missed-in-phase-2)
  ✓ Processes: 9 started, 9 stopped through their handles, 0 left running, 0 incidents
    Isolation: container

## Proposed, Not Applied

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: routes/task_routes.py:1-299 (and routes/user_routes.py, routes/report_routes.py)
Reason not applied: the application has no identity model — the login token is never verified by
any route, so every current client is anonymous. Per the legitimate-use test
(04-architecture-guidelines.md §6), enforcing authentication would reject every current client,
legitimate ones included.
Proposed change: introduce a verified session or token-verification middleware, decide the
principals and roles, and enforce ownership/role checks in each controller (RP-04) — a product
decision this run cannot make unilaterally.

### [HIGH] Missing Schema-Level Integrity Constraints — category deletion orphans tasks   (AP-20)
File: routes/report_routes.py:211-223 (controllers/category_controller.py:delete(); database.py;
models/task.py:13-14)
Reason not applied: today, deleting a referenced category silently succeeds and leaves the
orphaned reference (verified unchanged by replay: delete-category-with-tasks is `NOT FIXED`,
still 200/200). Any of restrict/cascade/set-null changes what that same call observes.
Proposed change: pick a delete policy for category -> task (restrict is the safest default absent
other guidance), implement it, then enable SQLite foreign-key enforcement
(`PRAGMA foreign_keys=ON` per connection) so the schema — not just the application — holds it
(RP-19).

### [MEDIUM] Unbounded Resources — no pagination on any list endpoint   (AP-13)
File: routes/task_routes.py (GET /tasks), routes/user_routes.py (GET /users),
routes/report_routes.py (GET /categories)
Reason not applied: clients today receive the full collection in one response; adding pagination
changes that shape for existing callers (05-refactoring-playbook.md RP-13).
Proposed change: add a bounded default page size with an explicit opt-out parameter, documented
as a version-bumped or explicitly-opted-in behaviour change.

### [MEDIUM] Insecure Runtime Configuration — permissive cross-origin policy   (AP-18)
File: app.py:22 (`CORS(app, origins=settings.cors_origins)`, defaulting to `"*"`)
Reason not applied: narrowing the origin policy changes which origins can call the API today; the
policy is now configuration (config/settings.py, CORS_ORIGINS) with the SAME default as before, so
this is safely deployable without a code change once a decision is made.
Proposed change: set `CORS_ORIGINS` to an explicit comma-separated allow-list per environment.

## Verification Coverage
Full — all planned checks executed (Layer 1 deprecation re-check via seed.py across five separate
container boots, zero DeprecationWarnings; Layer 2 OSV.dev re-check for flask 3.1.3 — no advisories
— and flask-cors 4.0.2 — the reachable HIGH advisory is resolved; three MODERATE per-resource-regex
advisories, fixed only in 6.0.0, remain in the dependency and are unreachable given this app's
global-CORS-with-no-resource-patterns configuration, exactly as declared and scoped at the Phase 2
gate — not a new or silently-dropped finding).

INCIDENT — a chained shell command: three `Remove-Item` calls joined with `;` in one PowerShell
invocation, used to delete stale `__pycache__` leftovers from a prior, unrelated session inside
controllers/, middlewares/, config/ before writing this run's own files there. This violates this
run's own literal-one-command-per-invocation discipline (06-validation-protocol.md §1.4's spirit,
and this run's explicit instructions); the effect was a benign, idempotent cleanup of files this
run did not create and that were about to be superseded regardless, and no process or version
control state was affected. Declared here rather than omitted.

INCIDENT — a destructive surface entry (`delete-task`) was captured against container
`refactor-arch-task-manager-api-20260925-1921-r5` on a boot that had already served the full
non-destructive replay in the same process lifetime, instead of its own fresh boot
(06-validation-protocol.md §2.2 requires a destructive entry to run alone). No data corruption
resulted (the entry targets task id 10, untouched by the preceding calls), but the isolation
guarantee the protocol exists to provide was not honoured for that one capture. Its result (PASS)
was discarded and is not counted as evidence; the authoritative `delete-task` PASS result used in
this report is from its own isolated boot (`...-r2`, captured before the later category_controller
fix — a fix that did not touch `TaskController.delete()`, so that earlier result remains valid for
the final code).

NOTE — container-internal paths (`/app`, `/skill`, `/reports`) had to be issued through PowerShell
rather than through the Bash/git-bash tool for every `docker exec`/`docker run` call: git-bash's
POSIX-path emulation rewrites `/app` to a Windows host path before Docker sees it, which the
protocol identifies as a known Windows failure mode (06-validation-protocol.md §1.4, "keep
container paths out of a shell that rewrites them"). Every command actually sent to Docker was
still fully literal — no `$VAR`, no substitution — this is a shell-selection note, not a
NON-LITERAL exception.

NOTE — one anti-pattern instance (the category-listing N+1, AP-10) was missed on the first pass of
this refactor's own implementation and caught by self-review before the formal Phase 3d re-audit
ran; it was fixed and re-verified (list-categories still PASS) before that re-audit, so it appears
above as an ordinary `resolved` finding rather than a `missed-in-phase-2` or `failed` re-audit
result. Recorded here for the same transparency reason as the AP-14 addition earlier in this
report.
================================
