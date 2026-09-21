================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13.2 + Flask 3.1.1 (flask-cors 5.0.1)
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-21 17:23
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    clean at d129f9b
Runtime: installed the declared dependencies from requirements.txt into <tmp>/refactor-arch-code-smells-project-20260921-1723/venv (outside the target)

## Summary
CRITICAL: 11 | HIGH: 8 | MEDIUM: 11 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:7-7
Description: The Flask signing key is set to the literal `"minha-chave-super-secreta-123"`; the same literal is repeated at controllers.py:289-289. It is a session/signing key (aggravating).
Impact: Anyone with the repository can forge any value Flask signs with this key; rotation requires a code change and a deploy, and the value lives in history forever.
Recommendation: Read it from the environment through a single config module, fail loudly if absent in non-debug mode; see RP-01.
Contract: safe

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:8-8
Description: `app.config["DEBUG"] = True` and `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88-88) enable debug mode by literal on the only start path, bound to every interface. Observed in a run copy: an unhandled error (`POST /admin/query` with body `null`) returned the Werkzeug debugger page with `EVALEX = true` (interactive console, PIN-protected) and the full traceback. Escalated from HIGH: an interactive code-evaluation console on a listener reachable from outside the host.
Impact: The debugger console is one PIN away from remote code execution, and every unhandled error hands an attacker the source paths and stack.
Recommendation: Read debug mode from configuration, default off; see RP-17.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: app.py:18-26
Description: The user and order routes (`GET /usuarios`, `GET /usuarios/<id>`, `GET /pedidos`, `GET /pedidos/usuario/<usuario_id>`, `PUT /pedidos/<pedido_id>/status`) — and the product write routes at app.py:14-16 — are registered with no authentication and no ownership check anywhere on their path; lookups filter only by the input id. `POST /login` (controllers.py:167-186) returns user data but issues no session or token, so no identity model exists.
Impact: Any caller lists every account, reads any user's orders by changing one number, and changes any order's status — horizontal and vertical escalation indistinguishable from legitimate use.
Recommendation: Introduce an identity model (token issued at login), then scope reads and writes to the verified principal and role. See RP-04.
Contract: contract-changing: every current client is anonymous; adding authentication rejects all of them (legitimate-use test, no identity model).

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: app.py:47-57
Description: `POST /admin/reset-db` deletes every row of `itens_pedido`, `pedidos`, `produtos` and `usuarios` with no authentication or confirmation. Escalation noted: the unprotected operation is destructive.
Impact: One anonymous request wipes the whole store.
Recommendation: Remove from the public surface or restrict to an operator identity; see RP-04.
Contract: contract-changing: removing or gating the route changes what every current (anonymous) client observes.

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: app.py:59-78
Description: `POST /admin/query` reads `sql` from the JSON body and passes it verbatim to `cursor.execute(query)`, committing anything that is not a SELECT. There is no authentication on the route (overlaps AP-04). Escalation noted: unauthenticated, and writes/deletes are accepted.
Impact: Any network caller can read every table (including plaintext passwords) and alter or drop data with one request — the whole database is a public endpoint.
Recommendation: Remove the endpoint or put it behind an operator-only identity; never execute caller-supplied SQL. See RP-02 / RP-04.
Contract: contract-changing: the route exists and answers 200 to any caller; removing or gating it changes what every current client observes (the application has no identity model).

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: controllers.py:276-290
Description: `GET /health` returns the signing secret (`"secret_key": "minha-chave-super-secreta-123"`), the database path, `"debug": True` and an environment label — all hardcoded literals — to any caller (observed in a run copy). Escalated from HIGH: the diagnostic output exposes a credential and configuration.
Impact: The signing key is published over HTTP to anyone who asks; configuration details map the deployment for the next attack.
Recommendation: Stop returning the secret and configuration; derive the remaining values from configuration; see RP-17 / RP-01.
Contract: contract-changing (in part): redacting the secret value and deriving the other values from configuration keeps the body shape and is safe; removing the `secret_key`, `db_path`, `debug` and `ambiente` fields changes the response shape.

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: database.py:75-83
Description: The boot routine seeds the runtime database with accounts whose passwords are literals, including an `admin` account (`"admin123"`), in every environment that starts the application. The seed runs from `get_db()` at startup — runtime data, not a test fixture.
Impact: Every deployment ships with a known admin credential.
Recommendation: Remove credential literals from the seed; create initial accounts from environment-provided secrets or an explicit setup command; see RP-01.
Contract: contract-changing: the README documents the sample accounts; removing their known passwords changes which logins succeed for current clients.

### [CRITICAL] God Module / God Class   (AP-03)
File: models.py:1-314
Description: One 314-line module holds persistence (every SQL statement), business rules (stock check and order total at 139-146, stock decrement at 163-166, discount tiers at 256-262) and presentation/serialization (hand-built response dicts throughout), for three unrelated domain concepts (products, users, orders). Escalation noted: it also contains the injection sites of the next finding.
Impact: Nothing can be tested without a live database; every change has the whole file as blast radius.
Recommendation: Split into per-concept repositories and domain rules, with serialization in the view layer; see RP-03.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models.py:79-86
Description: `get_todos_usuarios` and `get_usuario_por_id` (models.py:95-102) serialize the `senha` column into the response; observed `GET /usuarios/2` returning `"senha": "123456"`. Escalated from HIGH: every account's password is returned to anonymous callers.
Impact: One request discloses every user's password — and, because passwords are reused, their accounts elsewhere.
Recommendation: Never serialize the credential column; see RP-08.
Contract: safe for the value (redacting it keeps the field and its type); removing the field would be contract-changing.

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: models.py:109-111
Description: `login_usuario` concatenates `email` and `senha` from the request body into the WHERE clause. The same construction is used in every statement of the module: 28, 47-50, 57-61, 68, 92, 126-129, 140, 148-151, 155, 157-166, 174, 188, 192, 220, 224, 279-281, and the search builder at 289-297 (`termo`, `categoria` concatenated from the query string). Escalation noted: authentication path, unauthenticated endpoints, write statements, systemic habit.
Impact: `email = "admin@loja.com' --"` logs in as admin with any password; the search and write paths allow data disclosure and corruption; a legitimate apostrophe in a product name breaks the insert.
Recommendation: Parameter binding for every statement; see RP-02.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models.py:122-131
Description: `criar_usuario` stores the password exactly as received; `login_usuario` (models.py:109-111) compares it in SQL by plain equality; the seed (database.py:75-79) stores plaintext too. Escalated from HIGH: passwords stored recoverably.
Impact: Any database read — or the `/admin/query` endpoint — yields every password in clear.
Recommendation: Store a salted, slow KDF hash; verify with constant-time comparison; migrate existing rows; see RP-08.
Contract: safe: legitimate logins keep succeeding with the same credentials.

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: app.py:80-88
Description: The only start path is `app.run(...)`, the framework's development server; no production server is declared anywhere (no process file, no container command, no alternative in the README).
Impact: The development server is not built for concurrent production traffic or hardening; it is also what exposes the debugger of the CRITICAL finding above.
Recommendation: Declare a production WSGI server as the documented start path; see RP-17.
Contract: contract-changing: requires adding a dependency the project does not declare and changing the documented boot command.

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: controllers.py:5-12
Description: Every handler (all of controllers.py, app.py:77-78) wraps its body in `except Exception as e: return jsonify({"erro": str(e)}), 500` — the same broad catch copied ~18 times, returning the raw exception text (observed: `POST /login` with no body returns the Werkzeug 415 message with status 500). No centralized handler exists; unhandled errors reach the Werkzeug debugger. `criar_pedido` (models.py:148-168) performs several writes with no rollback on failure, on a connection shared by all requests, so a partial write is committed by the next request's `commit()`.
Impact: Internal details leak to callers; a half-written order can persist; every handler must be edited to change error policy.
Recommendation: One error boundary mapping a small error taxonomy to the existing status codes and body shapes; transaction with rollback per use case; see RP-09.
Contract: safe, provided status codes and body shapes are preserved (only the message value of 500 responses changes).

### [HIGH] Duplicated Logic   (AP-12)
File: controllers.py:24-96
Description: `criar_produto` and `atualizar_produto` duplicate the presence and range validation, and the copies have diverged: update omits the name-length checks (47-50) and the category allow-list (52-54). Escalated from MEDIUM: the copies behave differently.
Impact: A product can be updated into a state that creation forbids (unknown category, one-letter name).
Recommendation: One validation function used by both; see RP-12 / RP-11.
Contract: safe: an unknown enumerated category and a name outside the domain's own stated length bounds are values no legitimate client sends (legitimate-use test, invariant already stated by the domain).

### [HIGH] Business Logic in the Delivery Layer   (AP-05)
File: controllers.py:188-255
Description: The order handlers carry domain behaviour: `criar_pedido` performs the post-order notifications (email/SMS/push, 208-210) and `atualizar_status_pedido` owns the status set (242) and the per-transition side effects (247-250). `health_check` (264-274) issues SQL directly; the admin handlers in app.py:47-78 do the same. Handlers take the framework `request` implicitly throughout.
Impact: The rules cannot be exercised without an HTTP request, and a second entry point would have to copy them.
Recommendation: Move use cases to controllers that accept plain values and repositories that own SQL; routes only parse → call → render. See RP-05.
Contract: safe

### [HIGH] Missing Boundary Validation   (AP-11)
File: controllers.py:195-201
Description: `criar_pedido` checks only that `itens` is non-empty; each item's `produto_id` and `quantidade` go unchecked into models.py:139-166. A negative `quantidade` passes the stock check, produces a negative total and *increases* stock; a missing key raises and returns 500. Escalated from MEDIUM: permits persistently corrupt domain state.
Impact: Stock and revenue figures can be corrupted by one request; malformed input is indistinguishable from a server fault.
Recommendation: Validate each item (integer id, positive integer quantity) at the boundary; see RP-11.
Contract: safe: non-positive or non-integer quantities are invalid on their face.

### [HIGH] Mutable Global State   (AP-07)
File: database.py:4-11
Description: A module-level `db_connection` is lazily assigned on first use and shared by every request, opened with `check_same_thread=False` under Flask's threaded server; cursors and `commit()` interleave across concurrent requests.
Impact: One request's commit can commit another's partial writes; concurrent writes race on a single connection.
Recommendation: A connection per request (or unit of work), created by an injected factory and closed at teardown; see RP-07.
Contract: safe

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: models.py:1-7
Description: Every model function calls the module-level `get_db()` singleton itself (models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286); controllers import `models` and `get_db` directly; configuration (secret, debug, DB path, port) is spread as literals across app.py:7-8, database.py:5 and app.py:88. There is no place where the object graph is assembled.
Impact: No unit can be tested without the real SQLite file; swapping the store means editing every function.
Recommendation: A composition root that loads config, builds the connection factory, repositories and controllers, and registers routes; see RP-06.
Contract: safe

### [HIGH] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:139-166
Description: `criar_pedido` issues one SELECT per item to validate, then per item another SELECT, an INSERT and an UPDATE. The loop bound is the caller-supplied `itens` array with no maximum. Escalated from MEDIUM: caller-controlled, unbounded round trips.
Impact: A single request can issue arbitrarily many statements.
Recommendation: Fetch all referenced products in one `IN` query, write items and stock updates in batch within one transaction; see RP-10.
Contract: safe

### [MEDIUM] Insecure Runtime Configuration   (AP-18)
File: app.py:9-9
Description: `CORS(app)` applies the library's default policy to every route; observed `GET /produtos` with `Origin: http://evil.example` answered `Access-Control-Allow-Origin: http://evil.example` (origin reflected). Credentials are not allowed. De-escalated from HIGH: no credentials are sent, but the policy covers sensitive and state-changing routes, so not LOW.
Impact: Any web origin can script the whole API from a visitor's browser, including the destructive admin routes.
Recommendation: Restrict origins to a configured allow-list; see RP-17.
Contract: contract-changing: a browser client on a currently-accepted origin would lose `Access-Control-Allow-Origin`.

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: controllers.py:43-50
Description: `preco` and `estoque` are compared with `< 0` without a type check (a string raises TypeError → 500); `buscar_produtos` (118-121) calls `float()` on `preco_min`/`preco_max` with no failure path (→ 500); `login` (169-171) and `atualizar_status_pedido` (239-240) dereference `request.get_json()` without handling a missing body (→ 500).
Impact: Malformed requests become server errors carrying internal messages, instead of clear client errors.
Recommendation: Type and presence checks at the boundary returning 400; see RP-11.
Contract: safe: wrong-typed values and missing bodies are invalid on their face.

### [MEDIUM] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: controllers.py:161-182
Description: User emails (personal data) are written to stdout on user creation and on every login attempt, success and failure (161, 179, 182). De-escalated from HIGH: stdout of a development server, no evidence of off-host shipping.
Impact: Personal data and a record of failed login attempts per address accumulate wherever logs go.
Recommendation: Structured logging without personal data; see RP-08.
Contract: safe

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: controllers.py:195-203
Description: `criar_pedido` never verifies that `usuario_id` refers to an existing user, and `atualizar_status_pedido` (237-245) returns 200 "Status atualizado" for a `pedido_id` that does not exist; the `itens` array has no upper bound.
Impact: Orders are created for non-existent users; clients are told an update succeeded when nothing changed.
Recommendation: Verify referenced entities exist (404/400) and bound the item count; see RP-11.
Contract: contract-changing: requires product decisions (new 404 on status update of an unknown id; a maximum item count; rejecting orders for unknown users).

### [MEDIUM] Magic Values   (AP-15)
File: controllers.py:242-250
Description: Order statuses are string literals repeated across modules that must agree: controllers.py:242, 247, 249 and models.py:150, 247, 250, 253. Escalated from LOW: several modules must agree on the values.
Impact: A typo silently creates a new status that no report counts.
Recommendation: One status enumeration in the domain; see RP-15.
Contract: safe

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models.py:4-8
Description: `GET /produtos`, `GET /usuarios` (72-76) and `GET /pedidos` (203-207) read whole tables with no limit or pagination.
Impact: Response size and latency grow with the data without bound.
Recommendation: Pagination with a bounded page size; see RP-13.
Contract: contract-changing: a default page size changes how many records current clients receive.

### [MEDIUM] Duplicated Logic   (AP-12)
File: models.py:12-21
Description: The product row→dict mapping is written three times (12-21, 31-40, 304-313), the user mapping twice (79-86, 95-102), and the order-with-items assembly twice, identically (178-199 and 210-231).
Impact: A field change must be made in every copy; the order copies are one forgotten edit away from diverging.
Recommendation: One serializer per entity; one order-assembly function; see RP-12.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:171-233
Description: `get_pedidos_usuario` and `get_todos_pedidos` query `itens_pedido` once per order and `produtos` once per item (188, 192, 220, 224).
Impact: Listing N orders with M items costs 1 + N + N·M queries.
Recommendation: One join (orders ⟕ items ⟕ products) grouped in memory; see RP-10.
Contract: safe

### [MEDIUM] Magic Values   (AP-15)
File: models.py:256-262
Description: Discount tiers are bare literals (thresholds 10000 / 5000 / 1000, rates 0.1 / 0.05 / 0.02) inside the query function. Escalated from LOW: a business rule owned by the business.
Impact: The commercial policy is invisible and will change without a code-driven reason.
Recommendation: Named constants in the domain module; see RP-15.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:1-1
Description: `flask==3.1.1` has advisory GHSA-68rp-wp8r-4726 / CVE-2026-27205 (missing `Vary: Cookie` on some session accesses), rated LOW by its source, fixed in 3.1.3 (OSV.dev, 2026-09-21). The application never uses `session`, so the feature is demonstrably unused. De-escalated from HIGH. Also: there is no lockfile, so transitive versions (Werkzeug, Jinja2, …) float; the audit checked the versions resolved on 2026-09-21.
Impact: Low today; the floating transitive set makes future audits non-reproducible.
Recommendation: Upgrade to 3.1.3 (same major); pin the transitive set; see RP-18.
Contract: safe (patch upgrade within the same major).

### [MEDIUM] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:2-2
Description: `flask-cors==5.0.1` has three advisories, all MODERATE, fixed in 6.0.0 (OSV.dev, 2026-09-21): GHSA-43qf-4rqw-9q2g / CVE-2024-6866 (case-insensitive path matching), GHSA-7rxf-gvfg-47g4 / CVE-2024-6839 (regex priority), GHSA-8vgw-p6qm-5gr7 / CVE-2024-6844 (`+` in paths). De-escalated from HIGH: moderate advisories, and the app uses a single app-wide resource where path matching has little to decide.
Impact: Mis-applied CORS policy on crafted paths.
Recommendation: Upgrade to 6.0.5 (latest). This crosses a major; the 6.0.0 changelog announces one breaking change (path-specificity ordering, relevant only with several resources). See RP-18.
Contract: safe only if the replay covers the CORS headers — the Phase 3 inventory includes an `Origin` request and a preflight for that reason; otherwise contract-changing.

### [LOW] Magic Values   (AP-15)
File: controllers.py:47-54
Description: Name-length bounds (2, 200) and the category allow-list are inline literals inside the handler.
Impact: The domain's rules are buried in delivery code and were not reused by the update path (see AP-12 finding).
Recommendation: Named constants in the domain; see RP-15.
Contract: safe

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: database.py:2-2
Description: `import os` is never used; `import sqlite3` at models.py:2-2 is never used either.
Impact: Noise that misleads readers about dependencies.
Recommendation: Delete; see RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: models.py:4-4
Description: Identifiers mix human languages within one naming scheme (`get_todos_produtos`, `get_usuario_por_id`, `login_usuario` beside `criar_produto`); parameters named `id` shadow the builtin (models.py:24, 54, 65, 89; controllers.py:14, 64, 98, 136); `cursor2` / `cursor3` (models.py:187, 191, 219, 223); `models.py` is a data-access module, not a model layer.
Impact: Readers cannot predict names; the file names misstate the architecture.
Recommendation: One consistent naming scheme per layer; see RP-16.
Contract: safe (internal identifiers only).

## Catalog Coverage

| Entry | Result |
|---|---|
| AP-01 | 2 findings: app.py:7-7, database.py:75-83 |
| AP-02 | 2 findings: app.py:59-78, models.py:109-111 (systemic) |
| AP-03 | 1 finding: models.py:1-314 (app.py and controllers.py considered; their mixing is reported as AP-05/AP-18) |
| AP-04 | 2 findings: app.py:18-26, app.py:47-57 |
| AP-05 | 1 finding: controllers.py:188-255 |
| AP-06 | 1 finding: models.py:1-7 |
| AP-07 | 1 finding: database.py:4-11 |
| AP-08 | 3 findings: models.py:79-86, models.py:122-131, controllers.py:161-182 |
| AP-09 | 1 finding: controllers.py:5-12 |
| AP-10 | 2 findings: models.py:139-166, models.py:171-233 |
| AP-11 | 3 findings: controllers.py:195-201, controllers.py:43-50, controllers.py:195-203 |
| AP-12 | 2 findings: controllers.py:24-96, models.py:12-21 |
| AP-13 | 1 finding: models.py:4-8 |
| AP-14 | none — forced DeprecationWarning run (Tier A) emitted none; PyPI metadata shows neither pinned release yanked; no deprecated classifier |
| AP-15 | 3 findings: models.py:256-262, controllers.py:242-250, controllers.py:47-54 |
| AP-16 | 1 finding: models.py:4-4 |
| AP-17 | 1 finding: database.py:2-2 |
| AP-18 | 4 findings: app.py:8-8, controllers.py:276-290, app.py:80-88, app.py:9-9 |
| AP-19 | 2 findings: requirements.txt:1-1, requirements.txt:2-2 |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Python runtime + app code | 3.13.2 | deprecation (forced `PYTHONWARNINGS=always::DeprecationWarning python -X dev`, all GET routes exercised) | A | runtime warnings | n/a — local | no issue found |
| flask | 3.1.1 | advisory | B | OSV.dev (GHSA-68rp-wp8r-4726) | 2026-09-21 | AP-19 requirements.txt:1-1 |
| flask | 3.1.1 | deprecation / yanked | B | pypi.org/pypi/flask/json | 2026-09-21 | no issue found |
| flask-cors | 5.0.1 | advisory | B | OSV.dev (GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7) | 2026-09-21 | AP-19 requirements.txt:2-2 |
| flask-cors | 5.0.1 | deprecation / yanked | B | pypi.org/pypi/flask-cors/json | 2026-09-21 | no issue found |
| werkzeug (transitive) | 3.1.8 | advisory | B | OSV.dev | 2026-09-21 | no issue found |
| jinja2 (transitive) | 3.1.6 | advisory | B | OSV.dev | 2026-09-21 | no issue found |
| itsdangerous, click, blinker, markupsafe (transitive) | 2.2.0, 8.5.0, 1.9.0, 3.0.3 | advisory | B | OSV.dev | 2026-09-21 | no issue found |
| flask-cors 6.0 upgrade | 6.0.0–6.0.5 | changelog | C | github.com/corydolphin/flask-cors/releases | 2026-09-21 | breaking change limited to multi-resource path ordering |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Exact transitive advisory check: no lockfile exists → transitive versions were checked as resolved on 2026-09-21, not as any pinned set a deployment would install.

## Proposed, Not Applied
To be determined in Phase 3.

================================
Total: 33 findings
================================

---

# Phase 3 — Final Report (appended 2026-09-21)

Confirmation: --yes (auto-approved, not human-reviewed). Phase 3 ran over all findings (`y` scope).
Target architecture: MVC (HTTP service). Layout: `config/`, `models/` (entities, rules and their repositories; persistence stays inside the model layer, one module per domain concept), `controllers/`, `views/` (routes and serializers), `middlewares/` (error boundary, per-request connection), and `app.py` (composition root, `criar_app()`). The layout stays flat (no `src/`), so `python app.py` keeps working. Naming convention: Portuguese for domain and infrastructure identifiers. The MVC layer term `Controller` is kept as the class suffix, matching `controllers/`.
Runtime (replay): installed requirements.txt (flask==3.1.3, flask-cors==6.0.1) into <tmp>/refactor-arch-code-smells-project-20260921-1723/venv-refactored, outside the target and deleted with the snapshot.
Owner action: rotate the committed secret. The old signing key `minha-chave-super-secreta-123` stays in git history and must be treated as compromised.
Password migration: plaintext passwords are hashed at boot (`UsuarioRepositorio.migrar_senhas_em_claro`). This was verified against a database created by the original app: 4 rows migrated and the legacy logins still succeed.

## Proposed, Not Applied
### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: models/dados_iniciais.py:21-25   (was database.py:75-83)
Reason not applied: the README documents the sample accounts; removing their known passwords changes which logins succeed for current clients. (Applied part: passwords are now stored only as PBKDF2 hashes.)
Proposed change: seed accounts only from environment-provided secrets or an explicit setup command; decide whether production should seed at all.

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: views/usuarios.py:32-35   (also views/pedidos.py:30-36, views/produtos.py:58-60; was app.py:18-26)
Reason not applied: the application has no identity model, so any authentication rejects every current (anonymous) client.
Proposed change: issue a token at `/login` and define principals and roles (`tipo` admin/cliente already exists). Then scope user and order reads and writes to the verified principal (RP-04).

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: views/sistema.py:55-55   (was app.py:47-57)
Reason not applied: removing or gating `POST /admin/reset-db` changes what current clients observe.
Proposed change: remove it from the HTTP surface (make it a maintenance command) or restrict it to an operator identity.

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: models/administracao.py:19-24   (route at views/sistema.py:56-56; was app.py:59-78)
Reason not applied: `POST /admin/query` executes caller SQL by design; removing or gating it changes the contract.
Proposed change: delete the endpoint; if an operator console is needed, move it off the public surface.

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: views/sistema.py:37-39   (was controllers.py:276-290)
Reason not applied: removing the `secret_key`, `db_path`, `debug` and `ambiente` fields changes the `/health` body shape. (Applied part: the secret value is redacted to `********`, and the other values now come from configuration.)
Proposed change: reduce `/health` to status plus counts.

### [HIGH] Insecure Runtime Configuration   (AP-18)
File: app.py:88-88   (was app.py:80-88)
Reason not applied: a production WSGI server is a dependency the project does not declare, and it changes the documented boot command.
Proposed change: declare a WSGI server and document a factory-based start. `criar_app` is already a factory.

### [MEDIUM] Insecure Runtime Configuration   (AP-18)
File: app.py:53-55   (was app.py:9-9)
Reason not applied: narrowing CORS removes `Access-Control-Allow-Origin` for browser clients on currently accepted origins.
Proposed change: set `CORS_ORIGINS` to the team's allow-list. The setting already exists; the default `*` preserves today's policy.

### [MEDIUM] Missing Boundary Validation   (AP-11)
File: models/pedido.py:60-72   (also models/pedido.py:168-171; was controllers.py:195-203)
Reason not applied: rejecting orders for unknown users, returning 404 for a status update of an unknown order, and capping the item count are product decisions.
Proposed change: verify `usuario_id` exists, return 404 on an unknown `pedido_id`, and cap `itens`.

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models/produto.py:90-92   (also models/usuario.py:65-67, models/pedido.py:133-166; was models.py:4-8)
Reason not applied: a default page size changes how many records current clients receive.
Proposed change: `limit`/`offset` query parameters with a bounded default, agreed with clients.

## Re-audit (Phase 3d): 12 findings
Same catalog and thresholds, over the refactored target. Layer 1 (forced DeprecationWarning plus `-X dev`, all route families exercised) emitted no warnings. Layer 2 (OSV.dev and PyPI, 2026-09-21) covered flask 3.1.3, flask-cors 6.0.1 and every transitive package pinned in constraints.txt: no advisories, nothing yanked.

proposed-not-applied (9): the nine items above, each re-found at the cited lines.

unresolved (3):

### [MEDIUM] Missing Boundary Validation   (AP-11), origin: missed-in-phase-2
File: models/pedido.py:98-112
Description: `fechar_pedido` checks each order line against the stock read before the order, so two lines for the same product can together exceed stock and drive `estoque` negative. The original had the same logic (models.py:139-146), and the refactoring preserved it verbatim.
Recommendation: aggregate quantities per product before the stock check (RP-11). Rejecting such an order enforces an invariant the domain already states (estoque >= 0).

### [MEDIUM] Missing Boundary Validation   (AP-11), origin: missed-in-phase-2
File: models/pedido.py:90-95
Description: any status may follow any other (for example `cancelado` → `entregue`). Cancelling does not restore stock, although the notification says "Devolver estoque". The original had the same behaviour (controllers.py:237-255).
Recommendation: a transition table in the domain. The transitions are a product decision (contract-changing).

### [MEDIUM] Missing Boundary Validation   (AP-11), origin: missed-in-phase-2
File: models/usuario.py:82-88
Description: user creation does not enforce email uniqueness, so several accounts can share one login email. The original had the same behaviour (models.py:122-131).
Recommendation: a unique constraint and a 409 on duplicates (contract-changing: duplicates are accepted today).

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
./
├── config/
│   ├── __init__.py
│   └── configuracao.py
├── controllers/
│   ├── __init__.py
│   ├── pedido_controller.py
│   ├── produto_controller.py
│   ├── sistema_controller.py
│   └── usuario_controller.py
├── middlewares/
│   ├── __init__.py
│   ├── sessao_banco.py
│   └── tratamento_erros.py
├── models/
│   ├── __init__.py
│   ├── administracao.py
│   ├── banco_de_dados.py
│   ├── dados_iniciais.py
│   ├── erros.py
│   ├── notificacao.py
│   ├── pedido.py
│   ├── produto.py
│   ├── relatorio.py
│   ├── saude.py
│   ├── senha.py
│   └── usuario.py
├── reports/
│   ├── audit-20260921-1723.md
│   ├── audit-latest.md
│   ├── baseline.json
│   ├── replay-compare.txt
│   ├── replay.json
│   └── surface.json
├── views/
│   ├── __init__.py
│   ├── pedidos.py
│   ├── produtos.py
│   ├── serializadores.py
│   ├── sistema.py
│   └── usuarios.py
├── .env.example
├── .gitignore
├── app.py
├── constraints.txt
├── README.md
└── requirements.txt

## Validation
  ✓ Application boots without errors
  ✗ Public surface replayed: 45 PASS, 1 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 5 FIXED, 0 NOT FIXED
  ○ Findings resolved: 24/33  (9 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 9 proposed-not-applied, 3 unresolved  (re-audit: 12 findings)

Replay notes:
  - REGRESSION get-produtos-busca-aspas (GET /produtos/busca?q=%27): the `dados[]` shape changed from empty to object. It was not fixed, because it is the AP-02 fix itself. In the original, the quote became part of the SQL (`LIKE '%'%'`) and matched nothing. With parameter binding it is a literal, and it matches the product whose name contains `''`. Restoring the old result would mean restoring the injection. The inventory filed this hostile input as a contract entry, which was an inventory error (protocol §2.1 and §10). Re-filing it after capture would have changed the inventory between capture and replay.
  - 4 entries PASS (improved): post-produto-apostrofo 500→201 (AP-02); post-produto-preco-texto, get-produtos-busca-preco-invalido and post-login-sem-corpo 500→400 (AP-11/AP-09).
  - The contract headers (Access-Control-*) matched on every entry, including the Origin request and the preflight, so the replay covers the flask-cors 5.0.1→6.0.1 major upgrade.
  - The destructive entry post-admin-reset-db was captured and replayed alone against a fresh database, in a separate boot, in both runs.
  - Verified outside the harness:
    - legacy plaintext passwords migrate at boot and still log in;
    - an SQL error on /admin/query now returns `{"erro": "Erro interno do servidor"}` with an X-Correlation-ID header, and no longer leaks the driver message or the Werkzeug debugger;
    - debug is off by default.
  - The snapshot directory <tmp>/refactor-arch-code-smells-project-20260921-1723 was deleted after validation.

## Proposed, Not Applied
9 items, listed in full under "## Proposed, Not Applied" above: AP-01 seed accounts, AP-04 ×2, AP-02 /admin/query, AP-18 /health fields, AP-18 dev server, AP-18 CORS, AP-11 referenced-entity checks, AP-13 pagination.

## Verification Coverage
Full. All planned checks ran:
  - Layer 1 forced-warning runs, on the original and on the refactored app;
  - Layer 2 OSV and PyPI lookups (2026-09-21);
  - baseline and replay of all 51 inventory entries, none skipped;
  - a complete re-audit.
The text-body comparison (the HTML 404 entry) applied the §5.2 masks: timestamps, UUIDs, runs of 16+ hex characters and digit runs are masked, and the wording is compared.
================================
