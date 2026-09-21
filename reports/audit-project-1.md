================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13.2 + Flask 3.1.1 (flask-cors 5.0.1, Werkzeug 3.1.8 resolved)
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-21 00:07
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)

## Summary
CRITICAL: 8 | HIGH: 10 | MEDIUM: 7 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:7-7
Description: The Flask signing key is assigned a string literal (`app.config["SECRET_KEY"] = "minha-chave-..."`); the same literal is repeated in controllers.py:289. It is a session/signing key, which the catalog lists as aggravating.
Impact: Anyone with read access to the repository can forge anything Flask signs with this key; rotating it requires a code change and a deploy, and the value stays in git history.
Recommendation: Read the key from the environment in a single configuration module and fail closed (generate an ephemeral random key with a warning) when absent — see RP-01.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: app.py:47-78
Description: `POST /admin/reset-db` deletes every row of every table and `POST /admin/query` executes an arbitrary SQL string from the request body (also AP-02 by construction); neither has any authentication or authorization check. No authentication mechanism exists anywhere in the application: `/login` returns the user record but no token, and all resource endpoints (`/usuarios`, `/pedidos`, `/relatorios/vendas`, product writes, `PUT /pedidos/<id>/status`) are open. Maximum urgency: the unprotected operations are destructive and expose personal data.
Impact: Any network caller can wipe the database or run any statement, and read every user's and order's data.
Recommendation: Introduce authentication and an authorization check on the operation (see RP-04); remove or disable the SQL console.
Contract: contract-changing: previously anonymous calls would receive 401/403 (or 404 if the admin routes are removed).

### [CRITICAL] Unsafe Handling of Sensitive Data — signing key and internals in /health   (AP-08)
File: controllers.py:264-292
Description: The unauthenticated health endpoint returns `"secret_key": "minha-chave-super-secreta-123"`, the database path, `"debug": True` and a hardcoded `"ambiente": "producao"`. Escalated to CRITICAL: a signing key is served to any caller.
Impact: The secret is disclosed at runtime even if it were removed from source; the endpoint also advertises that the interactive debugger is on.
Recommendation: Redact the value immediately (keep the field so the body shape is unchanged) and derive the other values from configuration; remove the field in a coordinated change — see RP-08.
Contract: safe for the redaction; removing the `secret_key` field is contract-changing (field removal).

### [CRITICAL] God Module / God Class   (AP-03)
File: models.py:1-314
Description: A 314-line module that holds persistence (every SQL statement), business rules (stock sufficiency and order total at 139-146, discount tiers at 256-262) and presentation/serialization (hand-written row-to-dict mappings at 12-21, 31-40, 79-86, 95-102, 178-199, 211-231, 304-313) for three unrelated domain concepts (products, users, orders) plus reporting. Escalation condition met: the module also contains the AP-02 injections.
Impact: No rule can be tested without a live SQLite file; every change to one domain concept touches the module every other concept lives in.
Recommendation: Split into per-entity repositories (persistence), services (rules) and serializers — see RP-03.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials — password field serialized in responses   (AP-08)
File: models.py:72-103
Description: `get_todos_usuarios` and `get_usuario_por_id` serialize the `senha` column into the response of the unauthenticated `GET /usuarios` and `GET /usuarios/<id>`. Escalated to CRITICAL: combined with plaintext storage, every password is publicly readable.
Impact: Anonymous full credential disclosure for every account.
Recommendation: Explicit field selection in the serializer excluding `senha` — see RP-08. Hashing (plaintext-storage finding) reduces exposure to password hashes in the meantime.
Contract: contract-changing: removing `senha` removes a field from the `/usuarios` and `/usuarios/<id>` response bodies.

### [CRITICAL] Injection-Prone Dynamic Query Construction in the Authentication Path   (AP-02)
File: models.py:105-120
Description: `login_usuario` builds `SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'` by concatenating the request's email and password and passes it to `cursor.execute`. Escalation condition met: the injection point is in an authentication path on an unauthenticated endpoint.
Impact: A caller can log in as any user without a password (e.g. an email value that closes the quote and comments out the password clause), including the seeded admin account.
Recommendation: Parameterized statement with `?` placeholders and a separate parameter tuple; verify the password in code against a hash (see RP-02, RP-08).
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials — plaintext password storage   (AP-08)
File: models.py:122-131
Description: `criar_usuario` stores the password exactly as given; the schema column `senha TEXT` (database.py:26-35) and the seed users (database.py:75-83) are plaintext, and login compares plaintext in SQL (models.py:109-111). Escalated from HIGH to CRITICAL: passwords are stored recoverably.
Impact: A single database read (trivial here, via AP-02 or `/admin/query`) discloses every user's password, reusable on other systems.
Recommendation: Hash with a purpose-built password KDF and verify with a constant-time check; upgrade legacy plaintext rows on successful login — see RP-08.
Contract: safe (the login request/response contract is unchanged)

### [CRITICAL] Injection-Prone Dynamic Query Construction (systemic)   (AP-02)
File: models.py:285-299
Description: `buscar_produtos` concatenates the free-text query parameters `q` and `categoria` into `LIKE '%...%'` and `categoria = '...'` clauses. The same construction habit appears at every statement in the module: models.py:47-50 and 57-61 (product name/description/category from the JSON body), 126-129 (user name/email/password from the body), 140, 148-151, 155-166 (order `produto_id`, `quantidade`, `usuario_id` taken from the JSON body, not type-checked), 174, 188, 192, 220, 224, 279-281, and 28, 68, 92 (these last three receive values already constrained by an `<int:>` route converter, so they are not attacker-influenced on their own but follow the same unsafe pattern). Escalation: systemic pattern, includes write statements.
Impact: Read, modification or destruction of any table through ordinary public endpoints (search, product create/update, user create, order create).
Recommendation: Replace every concatenated statement with bound parameters — see RP-02.
Contract: safe

### [HIGH] Magic Values — environment configuration hardcoded (debug on all interfaces)   (AP-15)
File: app.py:80-88
Description: `app.run(host="0.0.0.0", port=5000, debug=True)` plus `app.config["DEBUG"] = True` (app.py:8): host, port and debug mode are literals in code. Escalated from LOW to HIGH beyond the catalog's MEDIUM ceiling: the literal enables Werkzeug's interactive debugger bound to every interface, which allows code execution for anyone who can trigger an error.
Impact: Remote code execution risk on any machine running `python app.py`; configuration cannot differ per environment.
Recommendation: Read host/port/debug from the environment with safe defaults (debug off, loopback) — see RP-15, RP-01.
Contract: safe

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: controllers.py:5-12
Description: Every handler (16 occurrences in controllers.py, plus app.py:77-78) wraps its whole body in `except Exception as e` and returns `{"erro": str(e)}` with 500; there is no central error handler.
Impact: Internal exception text (including SQL fragments, given AP-02) is returned to callers; the same mapping is duplicated in every handler.
Recommendation: One registered error handler that logs the exception and returns the same body shape with a generic message — see RP-09.
Contract: safe (status and body shape preserved; only the message text changes)

### [HIGH] Duplicated Logic (diverged copies)   (AP-12)
File: controllers.py:64-96
Description: The product validation of `atualizar_produto` is a copy of `criar_produto`'s (28-50) that has diverged: the update path lacks the name-length checks (47-50) and the category allow-list (52-54), and silently resets the category to "geral" when omitted. Escalated to HIGH: the copies already behave differently.
Impact: A product can be updated into a state that creation forbids (one-letter name, unknown category).
Recommendation: One validator shared by both paths — see RP-12.
Contract: contract-changing if the update path is made as strict as creation (previously accepted PUT bodies would get 400); sharing the code while keeping each path's current rule set is safe.

### [HIGH] Missing Boundary Validation   (AP-11)
File: controllers.py:188-203
Description: Order items are never validated: `produto_id`/`quantidade` presence and type are unchecked (a missing key raises `KeyError` → 500) and a negative or zero `quantidade` is accepted. Also: `login` and `atualizar_status_pedido` dereference `request.get_json()` without a None check (170, 240); `buscar_produtos` calls `float()` on `preco_min`/`preco_max` with no failure path (118-121); `criar_produto` compares `preco`/`estoque` numerically without a type check (43-46). Escalated to HIGH: a negative quantity increases stock and produces a negative total — persistently corrupt domain state.
Impact: Malformed input becomes a 500; valid-looking malicious input corrupts inventory.
Recommendation: Validate once at the boundary with explicit 400 responses — see RP-11.
Contract: safe for inputs that previously produced 500; rejecting `quantidade <= 0` changes a previously accepted (illegitimate) request from 201 to 400.

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: controllers.py:237-255
Description: `atualizar_status_pedido` holds the order-status allow-list (242) and the per-status side effects (247-250, "Devolver estoque" is announced but never performed). Other handlers do the same: `criar_pedido` performs the notification workflow (208-210, prints claiming to send e-mail/SMS/push), `criar_produto` owns the category allow-list (52-54), `health_check` issues SQL directly from the handler (264-274), and app.py:47-78 runs raw SQL inside route functions. Also noted: the service layer does not exist; controllers call the data module directly.
Impact: The rules cannot be tested without Flask and cannot be reused by a second entry point.
Recommendation: Move rules and workflows into a service layer; handlers only map request → service call → response — see RP-05.
Contract: safe

### [HIGH] Mutable Global State   (AP-07)
File: database.py:4-11
Description: A module-level `db_connection` is lazily reassigned and shared by every request, opened with `check_same_thread=False`, while Flask's development server handles requests in threads.
Impact: Concurrent requests share one connection and its transaction: one request's uncommitted writes can be committed or seen by another; behaviour depends on interleaving.
Recommendation: Request-scoped connection stored on the application context and closed on teardown — see RP-07.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: database.py:7-86
Description: A single accessor `get_db()` opens the connection, runs the DDL and seeds data; every data function (models.py, 17 call sites) and the health handler call it directly, with a hardcoded relative path `db_path = "loja.db"` (database.py:5). There is no application factory; `app.py` builds and configures the app at import time.
Impact: No unit can be tested against a different database; schema creation and seeding run as a side effect of the first query.
Recommendation: Application factory as composition root; configuration injected; schema/seed as an explicit init step; repositories receive the connection — see RP-06.
Contract: safe

### [HIGH] Non-Atomic Multi-Write Operation with Sentinel Error Returns   (AP-09)
File: models.py:133-169
Description: `criar_pedido` inserts the order, its items and stock decrements as separate statements with a single `commit()` at the end and no rollback on failure; failures are signalled by returning `{"erro": ...}` dicts (143, 145) that the caller must remember to check (controllers.py:205).
Impact: An exception mid-loop leaves pending writes on the shared connection (AP-07), which the next request's `commit()` persists — a half-created order with partial stock decrements.
Recommendation: Wrap in a transaction with rollback; raise domain exceptions instead of sentinel dicts — see RP-09.
Contract: safe

### [HIGH] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:139-166
Description: `criar_pedido` issues one SELECT per item to validate (140), then another SELECT, an INSERT and an UPDATE per item (155-166). Escalated from MEDIUM to HIGH: the loop bound is the caller-supplied `itens` array, with no maximum.
Impact: One request can trigger an arbitrary number of round trips while holding the shared connection.
Recommendation: Fetch all referenced products in one `IN (...)` query, batch the writes in one transaction, and bound the item count — see RP-10.
Contract: safe

### [HIGH] Deprecated or End-of-Life API Usage — dependency with security advisories   (AP-14)
File: requirements.txt:2-2
Description: `flask-cors==5.0.1` (resolved 5.0.1). OSV.dev reports GHSA-43qf-4rqw-9q2g (CVE-2024-6866), GHSA-7rxf-gvfg-47g4 (CVE-2024-6839) and GHSA-8vgw-p6qm-5gr7 (CVE-2024-6844) for this version, all fixed in 6.0.0 (Tier B, looked up 2026-09-21). Escalated from MEDIUM to HIGH per the AP-14 rule (security advisory).
Impact: CORS path matching may apply the wrong policy; no fix will reach 5.0.x.
Recommendation: Upgrade to flask-cors 6.0.5 (current release per PyPI, OSV returns no advisories for it, looked up 2026-09-21) — see RP-14.
Contract: safe (the app uses the default policy for all paths)

### [MEDIUM] Unsafe Handling of Sensitive Data — PII in logs   (AP-08)
File: controllers.py:161-182
Description: User e-mails are printed on user creation and on every successful and failed login (161, 179, 182); all logging uses `print`. De-escalated from HIGH to MEDIUM: the output is local stdout, not shipped off-host in this codebase.
Impact: Personal data and login-attempt history end up in whatever captures stdout.
Recommendation: Use the logging module and omit or mask identifiers — see RP-08.
Contract: safe

### [MEDIUM] Magic Values — enumerations as repeated string literals   (AP-15)
File: controllers.py:242-250
Description: Order statuses (`"pendente"`, `"aprovado"`, `"cancelado"`, ...) are literals repeated across controllers.py:242-250, models.py:150 and 247-253 and database.py:40; the category list (controllers.py:52), version `"1.0.0"` (app.py:36, controllers.py:285) and `"loja.db"` (database.py:5, controllers.py:287) are also repeated. Escalated to MEDIUM: several modules must agree.
Impact: A typo silently creates a new status that no report counts.
Recommendation: Single definitions (constants) imported where needed — see RP-15.
Contract: safe

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models.py:4-8
Description: `SELECT * FROM produtos` with no limit (also `usuarios` at 75, `pedidos` at 206); the global connection (database.py:10) is never closed.
Impact: Response size and memory grow with the table; no connection lifecycle.
Recommendation: Request-scoped connection closed on teardown (safe); optional pagination — see RP-13.
Contract: safe for the connection lifecycle; a default page size would be contract-changing (clients would receive fewer rows).

### [MEDIUM] Duplicated Logic   (AP-12)
File: models.py:171-233
Description: `get_pedidos_usuario` and `get_todos_pedidos` are identical except for the WHERE clause; the product row-to-dict mapping is written four times (12-21, 31-40, 304-313 and implied by 7) and the user mapping twice (79-86, 95-102).
Impact: A field added to one copy will be missing from the others.
Recommendation: One serializer per entity and one parameterized order query — see RP-12.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:203-233
Description: `get_todos_pedidos` runs one query per order for its items and one query per item for the product name; `get_pedidos_usuario` (171-201) does the same.
Impact: `GET /pedidos` issues 1 + orders + items queries; latency grows linearly with data.
Recommendation: One join over orders, items and products, grouped in code — see RP-10.
Contract: safe

### [MEDIUM] Magic Values — business rule thresholds   (AP-15)
File: models.py:256-262
Description: Discount tiers `10000/5000/1000` with rates `0.1/0.05/0.02` inline in the sales report. Escalated to MEDIUM: a pricing rule owned by the business.
Impact: Nobody can tell whether changing a number is safe or where else it is assumed.
Recommendation: Named constants in the domain/service layer — see RP-15.
Contract: safe

### [MEDIUM] Deprecated or End-of-Life API Usage — framework with advisory   (AP-14)
File: requirements.txt:1-1
Description: `flask==3.1.1` (resolved 3.1.1). OSV.dev reports GHSA-68rp-wp8r-4726 (CVE-2026-27205, "session does not add `Vary: Cookie` header"), fixed in 3.1.3 (Tier B, looked up 2026-09-21). Kept at MEDIUM rather than escalated: the application never reads or writes the Flask session, so the vulnerable path is not exercised.
Impact: Becomes exploitable as soon as session use is added.
Recommendation: Upgrade to Flask 3.1.3 (latest per PyPI, OSV returns no advisories for it, looked up 2026-09-21) — see RP-14.
Contract: safe

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: models.py:2-2
Description: `import sqlite3` is unused in models.py; `import os` is unused in database.py:2; the result of `cursor.execute("SELECT 1")` in controllers.py:268 is never read.
Impact: Noise that suggests dependencies that do not exist.
Recommendation: Delete — see RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: models.py:24-24
Description: `models.py` holds no models but data-access functions; route handlers live in `controllers.py`; `id` shadows the builtin (models.py:24, 54, 65, 89 and handlers); `cursor2`/`cursor3` (models.py:187-191); mixed English/Portuguese in identifiers (`get_todos_produtos`, `get_produto_por_id`); prints claim "ENVIANDO EMAIL/SMS/PUSH" (controllers.py:208-210) while nothing is sent.
Impact: Readers are misled about where things live and what happens.
Recommendation: Rename by responsibility in the new layers — see RP-16.
Contract: safe

## Deprecated API Verification

| Item | Version in use | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|
| Runtime deprecation warnings (Python `-X dev`, `PYTHONWARNINGS=always::DeprecationWarning`, 11 GET/POST calls) | Python 3.13.2 | A | runtime | n/a — local | no warning emitted |
| flask | 3.1.1 | B | OSV.dev query; pypi.org/pypi/flask/json (not yanked; latest 3.1.3) | 2026-09-21 | AP-14 MEDIUM (GHSA-68rp-wp8r-4726) |
| flask-cors | 5.0.1 | B | OSV.dev query; pypi.org/pypi/flask-cors/json (not yanked; latest 6.0.5) | 2026-09-21 | AP-14 HIGH (3 advisories) |
| werkzeug (transitive) | 3.1.8 | B | OSV.dev query; PyPI (latest 3.1.8) | 2026-09-21 | no issue found |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Language/framework-level deprecation from official docs (Layer 2, row 4): not fetched → deprecations of Python/Flask APIs that emit no runtime warning on the exercised paths are unverified.
  - Runtime deprecation detection covered only the 11 GET/POST calls exercised; write paths (PUT/DELETE, admin) were not run in Phase 2 → warnings on those paths unverified at this point (re-checked in Phase 3 replay).
Note: Flask and flask-cors are not installed in the host interpreter; the declared, pinned dependencies were installed into a throwaway virtual environment outside the target to run the checks. No target file was modified.

## Proposed, Not Applied
To be determined in Phase 3.

================================
Total: 27 findings
================================

Phase 2 complete. Confirmation skipped: --yes (auto-approved, not human-reviewed). Proceeding as `y`.


================================================================
PHASE 3 ADDENDUM (appended 2026-09-21 00:25)
================================================================
Confirmation: --yes (auto-approved, not human-reviewed). Scope applied: all findings (as `y`).
Layout chosen: flat Flask project, MVC packages at the target root (config/, models/, controllers/,
views/, middlewares/, app.py composition root). Persistence lives inside the model layer
(repositories in models/), applied uniformly.

## Transformations applied (finding -> playbook)
- AP-01 app.py:7 -> RP-01: SECRET_KEY read from env in config/settings.py; ephemeral random key + warning when absent.
- AP-04 app.py:47-78 -> PROPOSED, NOT APPLIED (see below). Handlers moved to views/sistema_routes.py + controllers/sistema_controller.py + models/sistema.py.
- AP-08 controllers.py:264-292 -> RP-08 partial: secret value redacted ("***"), db_path/debug/ambiente now from config; field removal proposed.
- AP-03 models.py -> RP-03: split into models/{produto,usuario,pedido,sistema}.py repositories, controllers/*, views/serializers.py.
- AP-08 models.py:72-103 -> PROPOSED, NOT APPLIED (field removal); explicit allow-list serializer added; the field now carries a hash.
- AP-02 models.py:105-120 and 285-299 (+ all sites) -> RP-02: every statement bound; only fixed fragments concatenated.
- AP-08 models.py:122-131 -> RP-08: werkzeug scrypt hashes, constant-time legacy comparison, transparent re-hash on login; seed users hashed.
- AP-15 app.py:80-88 -> RP-15/RP-01: host/port/debug from env, defaults 127.0.0.1 / 5000 / debug off.
- AP-09 controllers.py:5-12 -> RP-09: single error boundary (middlewares/error_handler.py), same status codes and body shapes, generic 500 message, details logged; X-Request-ID correlation header.
- AP-12 controllers.py:64-96 -> RP-12: shared schema + models/regras_produto.py; each path keeps its current rule set (unification proposed).
- AP-11 controllers.py:188-203 -> RP-11: views/schemas.py; malformed input -> 400; quantidade <= 0 and non-integer ids rejected (unambiguously invalid, guidelines section 6 caveat).
- AP-05 controllers.py:237-255 -> RP-05: rules/workflows in controllers/*, notifications behind an injected NotificadorLog (honest log text).
- AP-07 database.py:4-11 -> RP-07: request-scoped connection on flask.g, closed on teardown.
- AP-06 database.py:7-86 -> RP-06: create_app() composition root, explicit database.initialize(), repositories receive a connection provider.
- AP-09 models.py:133-169 -> RP-09: order creation in one transaction (commit/rollback); domain exceptions replace sentinel dicts.
- AP-10 models.py:139-166 -> RP-10: one IN(...) query + executemany writes.
- AP-14 requirements.txt:1-2 -> RP-14: flask 3.1.3, flask-cors 6.0.5 (Werkzeug 3.1.8 now declared, since it is imported directly).
- AP-08 controllers.py:161-182 -> RP-08: logging module, no e-mails logged.
- AP-15 controllers.py:242-250, models.py:256-262 -> RP-15: models/constants.py (statuses, categories, discount tiers, version); DDL defaults formatted from constants.
- AP-13 models.py:4-8 -> RP-13 partial: connection lifecycle fixed; pagination proposed.
- AP-10 models.py:203-233 -> RP-10: single LEFT JOIN query.
- AP-12 models.py:171-233 -> RP-12: one listing method, one serializer per entity.
- AP-17 models.py:2 / AP-16 models.py:24 -> RP-16: unused imports deleted; files named by responsibility; no builtin shadowing; no cursor2/cursor3.
Superseded files removed: controllers.py, models.py, database.py.

## Intended behaviour changes on illegitimate input (outside the contract surface)
Probed separately (reports/surface-security.json, baseline-security.json, replay-security.json). The
harness classifies the first three as REGRESSION because status and shape changed; they are the
intended effect of the AP-02 / AP-11 fixes and are listed here rather than hidden:
- SEC login-sql-injection: 200 (logged in as admin without the password) -> 401.
- SEC order-negative-quantity: 201 (stock increased, negative total) -> 400.
- SEC order-produto-id-string ("2 OR 1=1"): 201 -> 400.
- SEC search-sql-injection: 500 (SQL syntax error leaked) -> 200 with empty result (improved).

## Re-audit (Phase 3d) - same catalog, same thresholds, over the refactored target
Deprecated-API checks re-run: Layer 1 (`-X dev`, PYTHONWARNINGS=always::DeprecationWarning, all 43
surface entries): no warning. Layer 2 OSV.dev flask 3.1.3 / flask-cors 6.0.5 / werkzeug 3.1.8: no
advisories (2026-09-21). Tier C: Flask 3.1.3 CHANGES.rst (only `__version__` deprecated, unused),
Werkzeug 3.1.8 CHANGES.rst (OrderedMultiDict deprecated, unused), flask-cors GitHub release 6.0.0
(breaking: path-specificity ordering; the app uses one default pattern). Looked up 2026-09-21.

proposed-not-applied (4):
- [CRITICAL] AP-04 views/sistema_routes.py:35-46 - /admin/reset-db and /admin/query (arbitrary SQL, models/sistema.py:28-40) unauthenticated; no auth mechanism anywhere.
- [CRITICAL] AP-08 views/serializers.py:5-7 - `senha` (now a hash) still returned by /usuarios and /usuarios/<id>.
- [HIGH] AP-12 models/regras_produto.py:31-35 - the update path still lacks the creation invariants (name length, category).
- [MEDIUM] AP-13 models/produto.py:8-10 (also models/usuario.py:10-12, models/pedido.py:36-72) - list endpoints unbounded, no pagination.

unresolved (4):
- [CRITICAL] AP-01 models/database.py:65-70 - seed accounts with working literal passwords, including an admin account, inserted into every empty database. Pre-existing (original database.py:75-83) and MISSED by the Phase 2 audit (only mentioned inside the AP-08 storage finding). The fix (seed only under an explicit dev flag / env-provided password) changes the documented seed data and the `POST /login valid` surface entry, so it is contract-changing and needs a decision.
- [MEDIUM] AP-11 controllers/pedido_controller.py:12-31 - domain invariants not enforced: an order may reference a non-existent usuario_id; PUT /pedidos/<id>/status returns 200 for a non-existent order (controllers/pedido_controller.py:39-46); duplicate e-mails accepted (models/usuario.py:22-29). Pre-existing, missed by Phase 2; fixing rejects currently accepted requests (contract-changing).
- [MEDIUM] AP-13 app.py:28-54 - no MAX_CONTENT_LENGTH and no bound on the order item count. Named in the Phase 2 AP-10 recommendation but neither applied nor recorded as proposed; bounding rejects currently accepted bodies (contract-changing).
- [MEDIUM] AP-08 controllers/sistema_controller.py:23-35 - /health still discloses db_path, debug and environment (the secret value is redacted). De-escalated to MEDIUM: internal, non-secret values. Only the secret_key field removal had been recorded as proposed, so this remainder counts as unresolved.

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: views/sistema_routes.py:35-46
Reason not applied: adding authentication changes what every current anonymous caller observes (401/403, or 404 if the admin routes are removed); there is no existing principal/token mechanism, so a policy would have to be invented (guidelines section 6 caveat).
Proposed change: token-based authentication issued by /login; an admin role required for /admin/*; delete /admin/query outright; scope /pedidos/usuario/<id> and /usuarios/<id> to the authenticated principal. Needs client coordination.

### [CRITICAL] Unsafe Handling of Credentials - password field in responses   (AP-08)
File: views/serializers.py:5-7
Reason not applied: removing `senha` removes a field from GET /usuarios and GET /usuarios/<id>.
Proposed change: drop `senha` from _CAMPOS_USUARIO after announcing the change. Until then the field carries a scrypt hash, never the password.

### [CRITICAL] Unsafe Handling of Sensitive Data - secret_key field in /health   (AP-08)
File: controllers/sistema_controller.py:23-35
Reason not applied: removing `secret_key` (and `db_path`, `debug`) changes the /health body shape.
Proposed change: reduce /health to status/database/counts/versao. The secret value is already redacted.

### [HIGH] Duplicated Logic - diverged product validation   (AP-12)
File: models/regras_produto.py:31-35
Reason not applied: applying the name-length and category rules to PUT /produtos/<id> would reject bodies accepted today (and "categoria defaults to geral on update" needs a decision).
Proposed change: validar_para_atualizacao = validar_para_criacao; make categoria optional-unchanged on update.

### [MEDIUM] Unbounded Resources - list endpoints without pagination   (AP-13)
File: models/produto.py:8-10
Reason not applied: a default page size changes how many rows clients receive.
Proposed change: optional `limit`/`offset` with no default first, then a documented default.

Password migration plan (RP-08): legacy plaintext rows are verified in constant time and re-hashed on
the next successful login; after an agreed window, force a reset for accounts still in plaintext.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
code-smells-project/
├── app.py                  composition root (create_app)
├── requirements.txt
├── .env.example
├── README.md
├── config/
│   └── settings.py
├── models/
│   ├── constants.py
│   ├── database.py
│   ├── errors.py
│   ├── notificacoes.py
│   ├── passwords.py
│   ├── pedido.py
│   ├── produto.py
│   ├── regras_produto.py
│   ├── sistema.py
│   └── usuario.py
├── controllers/
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py
│   └── usuario_controller.py
├── views/
│   ├── pedido_routes.py
│   ├── produto_routes.py
│   ├── schemas.py
│   ├── serializers.py
│   ├── sistema_routes.py
│   └── usuario_routes.py
├── middlewares/
│   ├── error_handler.py
│   └── request_context.py
└── reports/
(package __init__.py files omitted)

## Validation
  ✓ Application boots without errors  (flask --app app.py run --port 5101; also `python app.py` with APP_PORT=5101)
  ✓ Public surface replayed: 43 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED  (2 of the PASS improved from 500 to 400)
  ✓ Findings resolved: 22/27  (5 proposed, not applied — see report)
  ○ Anti-patterns remaining: 4 proposed-not-applied, 4 unresolved  (re-audit: 8 findings)

## Proposed, Not Applied
- [CRITICAL] AP-04 no authentication on admin/resource endpoints (views/sistema_routes.py:35-46)
- [CRITICAL] AP-08 `senha` field in user responses (views/serializers.py:5-7)
- [CRITICAL] AP-08 `secret_key` field in /health, value redacted (controllers/sistema_controller.py:23-35)
- [HIGH] AP-12 update path lacks the creation invariants (models/regras_produto.py:31-35)
- [MEDIUM] AP-13 list endpoints without pagination (models/produto.py:8-10)

## Verification Coverage
Full: all planned checks executed, under these declared conditions:
  - Runtime: the host interpreter lacks Flask, so the pinned dependencies were installed into a throwaway
    venv outside the target (flask 3.1.1 / flask-cors 5.0.1 for the baseline, upgraded to the new pins
    for the replay as part of the AP-14 fix). No validation-only dependency was installed.
  - Boot: the project's own `python app.py` hardcodes port 5000, so the baseline used the Flask CLI
    convention `flask --app app.py run --port 5101`, from a scratch working directory with a fresh
    loja.db for every run (same datastore state for baseline and replay).
  - POST /admin/reset-db was exercised (as the last entry, against the throwaway DB) instead of skipped.
  - Phase 2's two DEGRADED items were closed later: all write paths ran with deprecation warnings
    forced on (3a/3c), and Tier C docs were consulted during 3d.
  - The "intended behaviour changes" probes are reported above, outside the surface counts.
================================
