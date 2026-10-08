## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        code-smells-project (D:\Study\MBA FullCycle\mba-ia-refactor-projects-skill\.worktrees\p1\code-smells-project)
Language:      Python (host 3.13.2; container image python:3.13-slim)
Framework:     Flask 3.1.1 (pinned in requirements.txt; no lockfile, so resolved versions come from the run install)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Domain:        E-commerce store API (produtos, usuarios, pedidos, itens_pedido, sales report)
App type:      HTTP service
Architecture:  Nominal: controllers.py and models.py exist, but controllers hold validation/notification logic and also query the DB directly; routes, admin SQL endpoints and config live in app.py; models hold SQL plus business rules
Source files:  4 files analyzed (~780 lines; excluded: .claude/, reports/, requirements.txt, README.md, caches)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Boot:          python app.py (cwd = run copy; app.run(host=0.0.0.0, port=5000, debug=True), reloader on)
Port:          5000, fixed in source; container mode, so native port in its own network namespace
Runtime env:   Python 3.13 image; pip install -r requirements.txt inside the container
Isolation:     container (docker 28.5.2, image python:3.13-slim)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.13 + Flask 3.1.1 (+ flask-cors 5.0.1, SQLite)
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-08 15:00
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    uncommitted changes present — the audit read the working tree as found (only an untracked copy of the skill under .claude/ differs; the 4 source files and requirements.txt are as committed)
Runtime: installed the declared dependencies from requirements.txt into the container (pip, resolved: flask 3.1.1, flask-cors 5.0.1, werkzeug 3.1.9, jinja2 3.1.6, itsdangerous 2.2.0, click 8.5.0, blinker 1.9.0, markupsafe 3.0.4); nothing installed in the target
Isolation: container (docker 28.5.2, image python:3.13-slim)
Scratch: environment scratch directory (C:\Users\lucas\AppData\Local\Temp\claude\D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill\b35825d2-d654-455b-ad56-6dc436b8d6da\scratchpad\refactor-arch-code-smells-project-20261008-1500)  (protocol §1.1)

## Summary
CRITICAL: 10 | HIGH: 8 | MEDIUM: 6 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:7-7
Description: The framework signing key is a string literal assigned to `app.config["SECRET_KEY"]` (`"minha-chave-super-secreta-123"`). The same literal is echoed to every anonymous caller in the `/health` response body (`"secret_key"`, controllers.py:285-289).
Impact: Anyone who can read the repository, a clone or a `/health` response holds the signing key; rotating it needs a code change and a deploy, and history keeps it forever.
Recommendation: Read the key from the environment in a single configuration module with a random per-process fallback when unset, and stop echoing it (keep the `secret_key` field, mask the value). Rotate the committed key. See RP-01.
Contract: safe (masking a leaked secret while keeping the field and its type)

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:8-8
Description: Debug mode is switched on by a literal in the configuration (app.py:8) and again in the entry point that starts the server (`app.run(host="0.0.0.0", port=5000, debug=True)`, app.py:80-88). Observed on the original at its native configuration (no override): the Werkzeug debugger was active and `GET /console` answered `200`, on a listener bound to every interface. Escalated to the CRITICAL ceiling because an interactive console is reachable from outside the host. `CORS(app)` (app.py:9) is a wildcard policy, observed but not filed: it carries no credentials and there are no cookies or sessions in this application.
Impact: Remote code execution by design on any host that runs `python app.py`; debug also turns every unhandled error into a page that discloses source and variables.
Recommendation: Read debug and bind address from configuration with the same bind value as today and debug off by default (opt in through the environment). See RP-17.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization — business operations   (AP-04)
File: app.py:11-30
Description: The route table registers every operation with no authentication or ownership check: `/login` returns a user record but issues no session or token, and nothing else checks a caller. This includes listing all users and all orders (`/usuarios`, `/pedidos`, `/pedidos/usuario/<id>`), creating, updating and deleting products, and changing any order's status. These are business operations: the application has no identity model, so every current client is anonymous (the privileged operations are a separate finding).
Impact: Any caller reads every customer's data and orders, edits the catalog and changes order states by changing one identifier.
Recommendation: Introduce an identity model (verified token or session, principals, ownership and role policy) and enforce it on the operations in the controller layer. See RP-04. The policy is a product decision.
Contract: contract-changing: every current client sends no credentials, so each would receive a new `401`/`403`

### [CRITICAL] Missing or Bypassable Authorization — privileged operations   (AP-04)
File: app.py:47-78
Description: Two administrative routes are open to everyone: `POST /admin/reset-db` deletes every row of `itens_pedido`, `pedidos`, `produtos` and `usuarios` (app.py:47-57), and `POST /admin/query` executes the SQL text sent in the request body, writes included (app.py:59-78). Observed on the original: an anonymous `POST /admin/query` answered `200`. The sales report (`GET /relatorios/vendas`, app.py:28 and controllers.py:257-262, models.py:235-273) aggregates revenue across every customer and is also served to anonymous callers (observed `200`). Privileged by the three signals of `04-architecture-guidelines.md` §6: caller-chosen code, bulk reset, cross-principal report.
Impact: Anyone can wipe the store, read or alter any table, or read financial totals.
Recommendation: Remove `/admin/query` and `/admin/reset-db` from the request surface; guard the report with an operator credential from configuration, closed by default. See RP-04.
Contract: safe (no legitimate client calls these anonymously)

### [CRITICAL] God Module / God Class   (AP-03)
File: controllers.py:1-292
Description: One module mixes delivery (request parsing and JSON responses for every route, 5-262), business rules (category allow-list 52-54, order-status allow-list 242, product validation 28-50), persistence (driver calls inside `health_check`, 264-292), notification side effects (print-based email/SMS/push, 208-210 and 247-250) and diagnostic data (285-289), across five unrelated concepts (products, users and login, orders, report, health). Per the AP-03/AP-05 precedence rule no separate AP-05 is filed for this module.
Impact: Nothing in it can be tested without a Flask request context and a live database; every change touches the whole file.
Recommendation: Split into per-concept controllers that take plain values, with validation at the boundary and persistence in the model layer. See RP-03, RP-05.
Contract: safe

### [CRITICAL] Hardcoded Secrets and Credentials — seeded accounts   (AP-01)
File: database.py:75-79
Description: The first-boot seed writes three accounts with literal passwords (`admin123`, `123456`, `senha123`, including an `admin` account) into the runtime database. The seed reaches the live datastore, so it is in scope. It is a separate finding from the signing key because its fix differs in contract.
Impact: Every environment that boots the application gets an admin account with a published password.
Recommendation: Provision initial accounts from configuration or an operator action, with no default password. See RP-01.
Contract: contract-changing: existing clients log in with these seeded credentials, and removing or changing them changes what `POST /login` answers for them

### [CRITICAL] God Module / God Class   (AP-03)
File: models.py:1-314
Description: 314 lines holding four unrelated domain concepts (products 4-70 and 285-314, users 72-131, orders 133-233 and 275-283, sales report 235-273) with persistence (every function), business rules (order total and stock check 133-169, discount tiers 256-262) and presentation mapping (row-to-dict, repeated). Per the precedence rule no separate AP-05 is filed for this module.
Impact: Any change risks the whole file; business rules cannot run without the database.
Recommendation: One model module per concept with its repository and pure rules separated. See RP-03.
Contract: safe

### [CRITICAL] Injection-Prone Dynamic Query Construction — authentication path   (AP-02)
File: models.py:105-120
Description: `login_usuario` concatenates the request's `email` and `senha` into the statement (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`). Observed on the original: a login with `' OR '1'='1' --` as email answered `200` with a user record. Escalated by being on an authentication path, unauthenticated.
Impact: Authentication bypass: anyone logs in as the first account, the seeded admin.
Recommendation: Bind both values as parameters and compare the password through the credential check of RP-08. See RP-02.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models.py:122-131
Description: `criar_usuario` stores the password exactly as received (also seeded as plain text, database.py:75-84), login compares it with plain equality inside SQL (models.py:109-111), and the user read endpoints serialize the whole record including the `senha` field (models.py:72-103, `GET /usuarios` and `GET /usuarios/<id>`). Escalated to CRITICAL: passwords are stored recoverably.
Impact: One database read, or one call to `GET /usuarios`, discloses every account's password.
Recommendation: Store a salted password-KDF hash with transparent upgrade of legacy plain rows on successful login, and mask the `senha` value in responses (field kept). See RP-08.
Contract: safe (hash with upgrade-on-login; masking a secret value while keeping the field and type)

### [CRITICAL] Injection-Prone Dynamic Query Construction   (AP-02)
File: models.py:285-299
Description: `buscar_produtos` builds the statement by concatenating `termo`, `categoria`, `preco_min` and `preco_max` from the query string. Every other statement in the module is built the same way with request values: 28, 47-50, 57-61, 68, 92, 126-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 279-281 (a systemic habit, not a slip). Observed on the original: a product name containing a single quote answered `500` (the quote ends the literal) and a search with an unbalanced quote answered `500`. No dynamic identifiers.
Impact: Data disclosure, corruption or destruction through any endpoint that takes a name, filter or status; writes are reachable unauthenticated.
Recommendation: Pass the statement with placeholders and the values separately everywhere. See RP-02.
Contract: safe

### [HIGH] Insecure Runtime Configuration — development server as production server   (AP-18)
File: app.py:80-88
Description: The only start path is `python app.py`, which starts the framework's built-in development server (`app.run`), with no production server declared anywhere (requirements.txt lists none, there is no process file or container definition, the README documents `python app.py`). Kept at the default HIGH.
Impact: The built-in server is single-purpose tooling, not hardened for exposed traffic.
Recommendation: Run behind a production WSGI server and document the command. See RP-17.
Contract: contract-changing: a production server is a runtime dependency the application does not have today (whoever deploys must install it)

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: controllers.py:5-22
Description: Every handler wraps its body in `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500` (16 copies, 5-292, and the admin handler at app.py:77-78), so there is no central handler and the raw exception text (SQL fragments, library messages) is returned to the caller. A malformed JSON body, which Flask raises as a `400`, is turned into `500` by the same catch (observed on the original). `criar_pedido` (models.py:133-169) performs several writes on the shared connection with no rollback on failure: a failure mid-way leaves partial writes that the next commit persists.
Impact: Internals leak to callers, client errors read as server errors, and a failed order can leave stock decremented without an order.
Recommendation: One error boundary mapping a small domain taxonomy to the existing status codes and `{"erro": ...}` body, a generic message for unexpected errors, and a rollback on failure. See RP-09.
Contract: safe (status codes and the `erro` body shape are preserved; the message of unexpected errors is a value, not shape)

### [HIGH] Duplicated Logic — diverged validation   (AP-12)
File: controllers.py:24-96
Description: `criar_produto` (28-54) and `atualizar_produto` (72-90) repeat the same field validation, and they have diverged: the update path lacks the name-length checks (47-50) and the category allow-list (52-54), and checks existence before the body while create has no such step. Escalated to HIGH because the copies already behave differently.
Impact: The same product can be rejected on create and accepted on update, so catalog data can reach states create forbids.
Recommendation: Extract one product validation shared by both. See RP-12. Which copy is correct is a product decision.
Contract: contract-changing: update would start rejecting names outside 2-200 characters and unknown categories that it accepts today

### [HIGH] Missing Boundary Validation — types, shapes and domain invariants   (AP-11)
File: controllers.py:188-220
Description: `criar_pedido` passes `itens` through unchecked: items missing `produto_id`/`quantidade` raise `KeyError` (`500`, models.py:140-146) and a negative `quantidade` is accepted (observed `201`), which adds stock back (models.py:163-166) and writes a negative total. Same pattern elsewhere: `preco < 0` on a non-number raises `TypeError` and answers `500` (controllers.py:43-46, 87-90; observed), a malformed or non-object JSON body raises (controllers.py:26, 148, 169, 190, 239; observed `500`), and `float()` on `preco_min`/`preco_max` fails with `500` (controllers.py:118-121; observed). Escalated to HIGH: unvalidated values reach the datastore and permit persistently corrupt state.
Impact: Malformed input is a server error indistinguishable from a bug, and a negative quantity corrupts stock and revenue.
Recommendation: Validate type, presence and range once at the boundary and answer `400`. See RP-11.
Contract: safe (every rejected value is invalid on its face)

### [HIGH] Mutable Global State   (AP-07)
File: database.py:4-12
Description: `db_connection` is a module-level variable reassigned inside `get_db()` (`global db_connection`) and shared by every request with `check_same_thread=False`: one connection and one implicit transaction for all concurrent requests, never closed.
Impact: A handler that fails before `commit()` leaves its writes pending on the connection every other request uses; concurrent requests interleave on one cursor state.
Recommendation: One connection per unit of work, created by a factory and released at the end of the request. See RP-07.
Contract: safe

### [HIGH] Missing Schema-Level Integrity Constraints — sign-in identity   (AP-20)
File: database.py:26-35
Description: `usuarios.email` has no uniqueness constraint although login looks accounts up by email and takes the first row (models.py:105-112) and `criar_usuario` never checks for an existing one (models.py:122-131). Observed on the original: creating a user with the seeded admin's email answered `201`. Escalated to HIGH: two accounts answer to one sign-in name.
Impact: Which account a login reaches depends on row order; a second registration can shadow or hijack an identity.
Recommendation: Add a unique index through the project's idempotent schema step, and map the violation to a client error. See RP-19.
Contract: safe (a duplicate sign-in name breaks an invariant the domain already states)

### [HIGH] Missing Schema-Level Integrity Constraints — money and references   (AP-20)
File: database.py:36-53
Description: Amounts are binary floating point (`preco REAL` 19, `total REAL` 41, `preco_unitario REAL` 51, summed in float at models.py:137-146 and 256-262). `pedidos.usuario_id`, `itens_pedido.pedido_id` and `itens_pedido.produto_id` carry no foreign key, and `deletar_produto` (models.py:65-70) leaves `itens_pedido` rows pointing at nothing (the code even prints a `"Desconhecido"` fallback, models.py:196). Escalated to HIGH: money drifts and charges can attach to deleted products.
Impact: Totals can drift by fractions of a cent; orders can reference users and products that do not exist.
Recommendation: Exact money type or integer minor units with the boundary unchanged, foreign keys, and a stated delete rule, delivered as a migration. See RP-19.
Contract: contract-changing: the delete rule changes what `DELETE /produtos/<id>` does, converting stored amounts needs a data migration and changes serialized values (e.g. sums such as 269.70000000000005)

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: models.py:4-8
Description: Every model function fetches its connection from the module-level `get_db()` (4-8, 24-26, 43-45, 54-56, 65-67 and so on), `controllers.health_check` does the same (controllers.py:264-268), and the first `get_db()` call creates the schema and seeds data as a side effect (database.py:14-84). Nothing assembles the object graph: app construction, configuration, the route table and two admin handlers all sit at module level in app.py.
Impact: No unit can run against a test database or a fake; configuration is read at the point of use (`db_path` literal, database.py:5).
Recommendation: Repositories receive a connection, controllers receive repositories, and one `create_app` composition root wires them. See RP-06.
Contract: safe

### [MEDIUM] Missing Boundary Validation — references and state rules   (AP-11)
File: controllers.py:237-255
Description: `atualizar_status_pedido` answers `200` "Status atualizado" for an order id that does not exist (the `UPDATE` matches no row, models.py:279-283) and accepts any transition; `criar_pedido` accepts a `usuario_id` with no matching user (models.py:148-152); `criar_usuario` accepts any text as email. The cancellation branch only prints "Devolver estoque" (controllers.py:250) and never returns stock.
Impact: Orders for unknown users, silent no-op updates, stock never recovered after cancellation.
Recommendation: Verify referenced records exist and define the allowed status transitions. See RP-11. These rules need a product decision.
Contract: contract-changing: requests that succeed today (status update on an unknown order, order for an unknown user) would start failing

### [MEDIUM] Duplicated Logic   (AP-12)
File: models.py:24-41
Description: The product row-to-dict mapping is written four times (4-22, 24-41, 302-314) and the user mapping twice (79-86, 95-102); `get_pedidos_usuario` (171-201) and `get_todos_pedidos` (203-233) are the same 30-line block differing only in the `WHERE`. The copies agree today (not diverged).
Impact: A new column must be added in each copy; one is eventually forgotten.
Recommendation: One mapper per entity and one order-assembly function. See RP-12.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:171-201
Description: `get_pedidos_usuario` runs one query per order for its items (188) and one per item for the product name (192), i.e. 1 + N + N·M round trips; `get_todos_pedidos` repeats it for the whole table (203-233). `criar_pedido` issues one to three statements per submitted item (139-166), and the item list is caller-controlled. Kept at MEDIUM: the read loops are bounded by stored data, not by the caller.
Impact: Latency grows with the order history; `GET /pedidos` degrades first.
Recommendation: Fetch orders with their items and product names in set-based queries, with explicit ordering that matches today's. See RP-10.
Contract: safe

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models.py:203-233
Description: `GET /pedidos` loads the whole `pedidos` table and its items into memory with no limit; `get_todos_produtos` (4-22) and `get_todos_usuarios` (72-87) do the same for their tables. No cursor or connection is ever closed (database.py:10).
Impact: Response time and memory grow with the data, and one large table read can stall every request.
Recommendation: Paginate or stream list endpoints with a documented default and maximum. See RP-13. This needs a decision for the owner.
Contract: contract-changing: a client that today receives the full collection would receive a page

### [MEDIUM] Magic Values   (AP-15)
File: models.py:256-262
Description: Discount tiers and rates (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`) are bare literals in the report. Order statuses are string literals repeated in two modules that must agree (`'pendente'` models.py:150 and 247, `'aprovado'` 250, `'cancelado'` 253, the allow-list at controllers.py:242, 247 and 249), the category list is a literal (controllers.py:52), and the port, the version string and the environment label are inline (app.py:36, 85, 88; controllers.py:285-287). Escalated to MEDIUM: the same values must agree across modules and the rates are a business rule owned outside engineering.
Impact: A status typo silently creates a new state; nobody knows whether a rate may change.
Recommendation: Name the values in one module per concern. See RP-15.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency — flask-cors   (AP-19)
File: requirements.txt:2-2
Description: OSV.dev (lookup 2026-10-08) returns three advisories for `flask-cors` 5.0.1 (pinned exactly): GHSA-43qf-4rqw-9q2g / CVE-2024-6866 (case-insensitive path matching), GHSA-7rxf-gvfg-47g4 / CVE-2024-6839 (regex ordering by length) and GHSA-8vgw-p6qm-5gr7 / CVE-2024-6844 (`unquote_plus` on the path), each rated moderate by its source; fixed in 6.0.0. De-escalated from HIGH to MEDIUM: the advisories concern multi-pattern or path-based resource matching, and app.py:9 uses `CORS(app)` with the default single pattern, so the vulnerable feature is not in use. The fix is across a major version (5 → 6); the 6.0.0 release notes (GitHub, 2026-10-08) announce a behaviour change in path-specificity ordering, path decoding and path case sensitivity and name no option to turn on. Modern equivalent: `flask-cors` 6.0.0 (lowest fixed version).
Impact: Cross-origin policy can be applied to the wrong path under non-default configuration.
Recommendation: Upgrade to 6.0.0 and replay cross-origin requests (including case-changed and `+` paths) against a baseline captured on 5.0.1. See RP-18.
Contract: safe (major upgrade, applied only because the replay covers the changed behaviour with cross-origin entries; otherwise it would be proposed)

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: models.py:2-2
Description: `import sqlite3` is never referenced in models.py; `import os` in database.py:2 is never referenced either.
Impact: Noise that suggests a dependency that does not exist.
Recommendation: Delete the unused imports. See RP-16.
Contract: safe

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: models.py:187-193
Description: Throwaway names `cursor2` and `cursor3` for nested cursors; parameters and locals called `id` shadow the builtin (models.py:24, 65, 89; controllers.py:14, 56); naming mixes English `get_` prefixes with Portuguese nouns (`get_todos_produtos`, `get_pedidos_usuario` next to `criar_pedido`, `listar_*`); the generic `dados` is used for request payloads throughout.
Impact: Readers cannot tell a new name from an old one or guess the next function's name.
Recommendation: Consistent verb vocabulary and descriptive local names; internal identifiers only. See RP-16.
Contract: safe (no route, field or exported symbol is renamed)

### [LOW] Known-Vulnerable Dependency — flask   (AP-19)
File: requirements.txt:1-1
Description: OSV.dev (lookup 2026-10-08) returns GHSA-68rp-wp8r-4726 / CVE-2026-27205 / PYSEC-2026-2151 for `flask` 3.1.1: the session object's `in` operator does not add `Vary: Cookie`. Rated low by its source; fixed in 3.1.3 (same major and minor line). The project never imports or uses `session`, so the affected feature is unused. Modern equivalent: `flask` 3.1.3.
Impact: Only relevant behind a caching proxy for an application that reads the session by key presence; none of the conditions holds here.
Recommendation: Pin `flask==3.1.3`. See RP-18.
Contract: safe (patch within the same minor line)

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-named identifiers with literals; credential literals in seed data (database.py:75-79); connection URLs with credentials (none); high-entropy literals (none); framework signing key literal (app.py:7); committed credential files (none); default values that are real secrets (none); the literal echoed in a response (controllers.py:289) | 2 findings: app.py:7 secret key; database.py:75-79 seeded accounts |
| AP-02 | input reaching driver calls by concatenation (models.py throughout); interpolation markers; ORM escape hatches (no ORM); dynamic identifiers (none); shell/process execution (none); unsafe deserialization/template (none); path traversal (no filesystem paths from input); caller-supplied SQL (app.py:59-78, filed as AP-04) | 2 findings: models.py:105-120 login; models.py:285-299 systemic |
| AP-03 | module with 3+ responsibility categories (controllers.py, models.py; app.py is 88 lines of one admin concept, AP-05 rule, filed under AP-04); size over 300 with 2+ categories (models.py 314); unit over 50 lines or deep nesting (`criar_pedido`, `criar_produto`); unrelated concepts in one file; low-cohesion class (none); utility bin (none); high afferent coupling | 2 findings: controllers.py:1-292; models.py:1-314 |
| AP-04 | entries on principal data with no auth; direct object reference without principal; check only on one door; role from request (none); unverified token (none); unreachable check (none); disabled guard (none); privileged operations with no guard (app.py:47-78, report) | 2 findings: app.py:11-30 business; app.py:47-78 privileged |
| AP-05 | domain decisions in handlers; persistence in a handler (app.py:47-78); long handlers; request objects deep in the stack; rule in two handlers; pass-through layers. All hits fall in modules already filed as AP-03 (controllers.py) or AP-04 (app.py admin handlers) per the overlap rule | none separately (see AP-03, AP-04) |
| AP-06 | collaborators built internally (models.py:4-8 and each function); import-time side effects (none outside get_db first call); no single wiring place (app.py); no test seam; domain importing driver; config read at point of use (database.py:5) | 1 finding: models.py:4-8 |
| AP-07 | module-level variable mutated (database.py:4-12); request-scoped data stored globally (none); in-memory store of record (none); mutable default/class attribute (none); cache or pool with no lifecycle (the single connection); monkey-patching (none); in-process counters (none) | 1 finding: database.py:4-12 |
| AP-08 | password stored reversibly (models.py:122-131); fast digest (none, plain); constant/missing salt; non-constant-time comparison (models.py:109-111); sensitive values in logs (only emails printed); whole record serialized with `senha` (models.py:72-103); transport/TLS (not applicable); token expiry (no tokens) | 1 finding: models.py:122-131 |
| AP-09 | empty/log-only/swallowing catch; over-broad `except Exception` (every handler); repeated error mapping (controllers.py); no central handler; exception text returned (controllers.py:12 and throughout); sentinel/`erro` dict returns (models.py:143, 145); partial writes without transaction boundary (models.py:133-169); exceptions as control flow (none) | 1 finding: controllers.py:5-22 |
| AP-10 | query inside loop (models.py:171-233, 139-166); per-element foreign-key fetch; lazy relation (no ORM); repeated read with different args; remote call in loop (none); whole table filtered in app code (none); write loop per element (models.py:154-166) | 1 finding: models.py:171-201 |
| AP-11 | input used with no check (controllers.py:188-220 and others); optional input dereferenced; unbounded pagination (see AP-13); numeric parsing without failure path (controllers.py:118-121); validation on one entry point only (controllers.py:24-96); invariants unenforced (negative quantity, orphans); no body-size bound (not observed) | 2 findings: controllers.py:188-220; controllers.py:237-255 |
| AP-12 | structurally identical blocks (models.py:171-233); rule in more than one place (controllers.py:24-96, diverged); repeated mapping/serialization; hand-written mappings; copy-and-modify lineage; repeated constants (see AP-15); repeated guard | 2 findings: controllers.py:24-96; models.py:24-41 |
| AP-13 | acquire/release pairs; handle without release on failure (connection never closed); connection per call vs pool; outbound call with no timeout (none); retry policy (none); unbounded read (models.py:203-233); unbounded accumulator (none); background task (none); unbounded recursion (none) | 1 finding: models.py:203-233 |
| AP-14 | runtime warnings with detectors forced on (`PYTHONWARNINGS=always::DeprecationWarning`, `python -X dev`): boot, first-boot schema and seed, and 42 surface requests exercised (the two destructive entries run in the baseline boots); none emitted. Dependency flagged deprecated: PyPI metadata for flask 3.1.1 and flask-cors 5.0.1 `yanked: false` (2026-10-08). Structurally superseded constructs: none | none |
| AP-15 | numeric literals in decisions (models.py:256-262); unit-less durations (none); repeated status strings across files; repeated literals; numeric codes; tuple offsets (none); environment-specific literals (port, db path) | 1 finding: models.py:256-262 |
| AP-16 | name contradicting behaviour (none); non-descriptive identifiers (`cursor2`, `cursor3`, `dados`, `id`); several names for one concept; mixed casing; mixed languages in identifiers; inconsistent file naming (none); stale comments (none); boolean call-site flags (none) | 1 finding: models.py:187-193 |
| AP-17 | commented-out code (none); unreachable branches (none); unreferenced units (none found; routes registered statically); unused imports (models.py:2, database.py:2); unused parameters; stale feature flags; `_old`/`.bak` copies (none) | 1 finding: models.py:2-2 |
| AP-18 | debug flag literal (app.py:8, 88); development server as production server (app.py:80-88); all-interface bind with debug; error output exposing internals (controllers throughout); wildcard cross-origin (app.py:9, observed, not filed: no credentials, no cookies); diagnostic surfaces (`/console`, `/admin/*`); protective defaults off (none) | 2 findings: app.py:8; app.py:80-88 |
| AP-19 | advisories for direct dependencies at their pinned versions (OSV.dev 2026-10-08: flask, flask-cors); transitive dependencies from installed metadata (werkzeug, jinja2, itsdangerous, click, blinker, markupsafe: none); range-vs-lock mismatch (no lockfile; direct dependencies pinned exactly); no-lockfile case handled as above | 2 findings: requirements.txt:2; requirements.txt:1 |
| AP-20 | looked-up identity column without uniqueness (usuarios.email); foreign-key-like columns without constraints (pedidos.usuario_id, itens_pedido.*); parent delete without child rule (models.py:65-70); money in binary float (database.py:19, 41, 51); nullable must-have columns and free-text enums (status, tipo) | 2 findings: database.py:26-35; database.py:36-53 |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| flask | 3.1.1 | advisory | B | OSV.dev `POST /v1/query` (PyPI) | 2026-10-08 | GHSA-68rp-wp8r-4726 (LOW), fixed in 3.1.3 — finding AP-19 (LOW) |
| flask | 3.1.1 | withdrawn/yanked | B | pypi.org/pypi/flask/3.1.1/json | 2026-10-08 | `yanked: false`, no issue found |
| flask-cors | 5.0.1 | advisory | B | OSV.dev `POST /v1/query` (PyPI) | 2026-10-08 | GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (moderate), fixed in 6.0.0 — finding AP-19 (MEDIUM) |
| flask-cors | 5.0.1 | changelog of the fix version | C | github.com/corydolphin/flask-cors/releases/tag/6.0.0 (API `releases/tags/6.0.0`) | 2026-10-08 | Behaviour change: path-specificity ordering, `unquote` instead of `unquote_plus`, case-sensitive path match; no option to enable |
| flask-cors | 5.0.1 | withdrawn/yanked | B | pypi.org/pypi/flask-cors/5.0.1/json | 2026-10-08 | `yanked: false`, no issue found |
| werkzeug | 3.1.9 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| jinja2 | 3.1.6 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| itsdangerous | 2.2.0 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| click | 8.5.0 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| blinker | 1.9.0 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| markupsafe | 3.0.4 (installed) | advisory | B | OSV.dev | 2026-10-08 | no issue found |
| application code, Python 3.13 / Flask 3.1.1 | n/a | runtime deprecation warnings | A | `PYTHONWARNINGS=always::DeprecationWarning`, `python -X dev`; boot + first-boot seed + 42 surface requests | n/a — local | no warning emitted; no finding |

The transitive versions were read from the installed metadata of the run install (no lockfile exists); the results hold for that installation date.

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-code-smells-project-20261008-1500-1 | `docker run -d ... python:3.13-slim sleep infinity` (run-1), pip install, `docker exec -d ... python -X dev /app/app.py` | ready on port 5000; its stderr is not retrievable from `exec -d`, so the run was discarded |
| 2 | 2 | stop | container | refactor-arch-code-smells-project-20261008-1500-1 | `docker rm -f refactor-arch-code-smells-project-20261008-1500-1` | removed |
| 3 | 2 | start | container | refactor-arch-code-smells-project-20261008-1500-2 | `docker run -d ... sleep infinity` (run-2), pip install | container up |
| 4 | 2 | start (refused) | container | `proc start` inside container 2 (state /reports/proc-orig.json) | `proc.py start ... -- python -X dev /app/app.py` | exit 2: cannot read the process start time in the image; proc stopped the pid it started (21) itself |
| 5 | 2 | start | container | refactor-arch-code-smells-project-20261008-1500-2 | `docker exec ... python -X dev /app/app.py` as a foreground command kept by the harness, output read from its log | ready on port 5000 |
| 6 | 2 | stop | container | refactor-arch-code-smells-project-20261008-1500-2 | `docker rm -f refactor-arch-code-smells-project-20261008-1500-2` | removed; containers carrying label `refactor-arch.run=20261008-1500`: none |
| 7 | 3 | start | container | refactor-arch-code-smells-project-20261008-1500-3 | original, run-3: pip install, `python -X dev /app/app.py`; baseline capture (all non-destructive entries) | ready on port 5000; 46 entries captured |
| 8 | 3 | stop | container | ...-3 | `docker rm -f refactor-arch-code-smells-project-20261008-1500-3` | removed |
| 9 | 3 | start | container | ...-4 | original, run-4 (fresh); baseline of `delete-produtos-10` alone | ready; captured |
| 10 | 3 | stop | container | ...-4 | `docker rm -f ...-4` | removed |
| 11 | 3 | start | container | ...-5 | original, run-5 (fresh); baseline of `sec-post-admin-reset-db` alone | ready; captured (48 entries in baseline.json) |
| 12 | 3 | stop | container | ...-5 | `docker rm -f ...-5` | removed |
| 13 | 3 | start | container | ...-6 | refactored-1 with `OPERATOR_TOKEN` set by `-e`; first full replay + hand verification | ready; 35 PASS, 11 FIXED, 2 UNVERIFIED (destructive, replayed alone below) |
| 14 | 3 | stop | container | ...-6 | `docker rm -f ...-6` | removed |
| 15 | 3 | start | container | ...-7 | refactored-2; replay of `delete-produtos-10` alone | ready; captured |
| 16 | 3 | stop | container | ...-7 | `docker rm -f ...-7` | removed |
| 17 | 3 | start | container | ...-8 | refactored-3; replay of `sec-post-admin-reset-db` alone | ready; captured |
| 18 | 3 | stop | container | ...-8 | `docker rm -f ...-8` | removed |
| 19 | 3 | start | container | ...-9 | refactored-4 (after the fix loop); second full replay + hand verification; installed versions read with `pip list` | ready; 35 PASS, 11 FIXED, 2 UNVERIFIED (replayed alone below) |
| 20 | 3 | stop | container | ...-9 | `docker rm -f ...-9` | removed |
| 21 | 3 | start | container | ...-10 | refactored-5; second replay of `delete-produtos-10` alone | ready; captured |
| 22 | 3 | stop | container | ...-10 | `docker rm -f ...-10` | removed |
| 23 | 3 | start | container | ...-11 | refactored-6; second replay of `sec-post-admin-reset-db` alone | ready; captured |
| 24 | 3 | stop | container | ...-11 | `docker rm -f ...-11` | removed; containers carrying label `refactor-arch.run=20261008-1500`: none; snapshot directory deleted |

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Language-level deprecations by documentation lookup (Layer 2, official docs for Python 3.13 and Flask 3.1.1): not performed; only runtime evidence (Layer 1) and registry/advisory metadata were used → a deprecated API that raises no warning on the exercised paths and appears in no registry record is not covered.
  - Two destructive entries (`DELETE /produtos/10`, `POST /admin/reset-db`) were not exercised in the Phase 2 runtime check: each runs alone on its own fresh boot in Phase 3a, where its output is also read for warnings → their code paths are not covered by the Phase 2 AP-14 evidence.
  - `sec-post-admin-reset-db` baseline and any state-dependent behaviour of the report on a populated database are captured in Phase 3a only.
Scratch root: the environment scratch directory (no approval-requiring paths).
Isolation: container; the first container's stderr could not be read (`exec -d`), so the warnings check ran on a second container (rows 3-5).
Commands (Phase 1-2): 0 directory changes, 0 chained commands.

================================
Total: 27 findings
================================

Confirmation: --yes (auto-approved, not human-reviewed)

---

## Phase 3 — Run record

Scope applied: all severities (gate answer `y` by `--yes`; not a CRITICAL+HIGH-only run).
Confirmation: --yes (auto-approved, not human-reviewed)

### Re-audit passes (SKILL.md 3d)

Pass 1 (after the first full replay, 0 regressions), same catalog and thresholds:

- proposed-not-applied (matches items recorded before the re-audit): 7.
- unresolved, origin `failed`: AP-10 (the order-creation loop still looked up one product per submitted item); AP-16 (route parameters still named `id`, payload variables still called `dados`, view functions still named in Portuguese while controllers use English).
- unresolved, origin `introduced`: AP-15 (a bare `32` for the generated-key size, a bare `500` batch size); AP-12 (the numeric-type predicate written twice).
- unresolved, origin `missed-in-phase-2`: AP-11 (the `itens` array of an order has no upper bound; present in the original, not reported at the gate) and AP-20 (no NOT NULL or CHECK constraints on required columns and closed value sets; the Phase 2 coverage row listed the signal as checked and the audit did not file it). Both fixes are contract-changing or need a product decision, so both are recorded under Proposed, Not Applied with the tag kept.

Fix between the passes (the four `failed`/`introduced` items): batched product lookup (`ProductRepository.find_many`), renamed route parameters, payload variables and view functions, named constants for the two literals, one shared numeric predicate (`models/validation.py`). Full replay again (36 contract entries PASS, 12 security entries FIXED, 0 regressions), then pass 2.

Pass 2: the 7 proposed-not-applied items, plus the 2 `missed-in-phase-2` items above (recorded as proposed with their tag). No `failed`, no `introduced`. There is no third pass.

Counts: Phase 2 total 27 = 20 resolved + 7 proposed + 0 unresolved. Fixed after re-audit: 4 (0 of them missed-in-phase-2). The 2 `missed-in-phase-2` items never join the Phase 2 total.

Reviewed and not filed in the re-audit: the statements in `models/product.py` (`find_many`) and `models/order.py` assemble SQL only from fixed fragments and `?` marks, with every value bound (AP-02: no input text reaches the statement); the broad `except` in `views/health_routes.py` logs the failure and answers `500` in the endpoint's own error shape (AP-09: it surfaces the failure, it does not swallow it); the wildcard cross-origin policy is unchanged and still not a finding (no credentials, no cookies).

Dependency check on the refactored manifest (OSV.dev, 2026-10-08): flask 3.1.3 and flask-cors 6.0.0 return no advisory; the transitive versions read from the installed metadata (`pip list`) are the same as in Phase 2, so those results hold.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
code-smells-project/
├── app.py                        composition root (create_app, run)
├── requirements.txt              flask==3.1.3, flask-cors==6.0.0
├── README.md
├── .env.example
├── .gitignore
├── config/
│   ├── __init__.py
│   └── settings.py               the only reader of the environment
├── models/
│   ├── __init__.py
│   ├── constants.py
│   ├── credentials.py            password hashing, legacy-row upgrade
│   ├── database.py               connection factory, schema, unique index, seed trigger
│   ├── errors.py                 domain error taxonomy
│   ├── order.py                  order persistence and pricing
│   ├── product.py                product persistence
│   ├── product_rules.py          product input rules
│   ├── report.py                 sales report
│   ├── seed.py
│   ├── user.py                   user persistence and authentication
│   └── validation.py
├── controllers/
│   ├── __init__.py
│   ├── health_controller.py
│   ├── notifier.py
│   ├── order_controller.py
│   ├── product_controller.py
│   ├── report_controller.py
│   └── user_controller.py
├── views/
│   ├── __init__.py
│   ├── health_routes.py
│   ├── helpers.py
│   ├── order_routes.py
│   ├── product_routes.py
│   ├── report_routes.py
│   └── user_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── db_connection.py          request-scoped connection
│   ├── error_handler.py          the one error boundary
│   └── operator_guard.py         operator credential, closed by default
└── reports/
    ├── audit-20261008-1500.md
    ├── audit-latest.md
    ├── surface.json
    ├── baseline.json
    └── current.json
```
Layout declared: persistence stays in the model layer (repositories inside `models/`); `views/` holds the route declarations (the View equivalent for an HTTP service); the original `app.py`, `models.py`, `controllers.py` and `database.py` were rewritten in place and the three superseded files removed.

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 36 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 12 FIXED, 0 NOT FIXED
  ○ Findings resolved: 20/27  (7 proposed, 0 unresolved)
  ⚠ Re-audit partial — see Verification Coverage  (9 findings over the checks that ran)
    Re-audit passes: 2; fixed after re-audit: 4 (0 of them missed-in-phase-2)
  ✓ Processes: 11 started, 11 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization — business operations   (AP-04)
File: app.py:11-30 (now the route modules under views/)
Reason not applied: the application has no identity model, so every current client is anonymous; any new `401`/`403` on listing, creating, editing or deleting records would reach every legitimate client.
Proposed change: choose an identity mechanism (token or session), the principals and the ownership/role policy, then enforce it in the controllers (RP-04). Requires a product decision and coordination with every client. Listing users and all orders, product create/update/delete and order status changes are the operations to cover. Judgement recorded: these were classified as business operations (not privileged) because they are the store's own CRUD on its records; `GET /relatorios/vendas` (cross-principal report) and the two `/admin/*` routes were classified as privileged and handled.
### [CRITICAL] Hardcoded Secrets and Credentials — seeded accounts   (AP-01)
File: database.py:75-79 (now models/seed.py)
Reason not applied: existing clients log in with the seeded credentials (`POST /login` answers `200` for them); removing or changing them changes what it answers.
Proposed change: provision the first administrator from configuration or an operator command with no default password, and force a change of the seeded passwords in deployed databases. The passwords are already stored hashed after this refactoring; the literals remain in `models/seed.py`.
### [HIGH] Insecure Runtime Configuration — development server as production server   (AP-18)
File: app.py:80-88 (now the `__main__` block of app.py)
Reason not applied: a production WSGI server is a runtime dependency the application does not have today; whoever deploys must install it.
Proposed change: add a production server and document the command, for example `gunicorn --bind 0.0.0.0:5000 "app:create_app()"` (`create_app` is already a factory). Debug is already off by default.
### [HIGH] Duplicated Logic — diverged validation   (AP-12)
File: controllers.py:24-96 (now models/product_rules.py)
Reason not applied: making the update path as strict as create would reject updates with names outside 2-200 characters or unknown categories, which are accepted today.
Proposed change: apply `validate_new_product` to updates after the owner confirms the update rule. The shared type/sign checks are already extracted; only the divergence remains.
### [HIGH] Missing Schema-Level Integrity Constraints — money and references   (AP-20)
File: database.py:36-53 (now models/database.py)
Reason not applied: the delete rule for children (refuse, cascade, detach) changes what `DELETE /produtos/<id>` does, and moving amounts out of binary floating point needs a data migration and changes serialized values (e.g. `269.70000000000005` becomes `269.7`).
Proposed change: foreign keys with an explicit delete rule, exact money storage with an unchanged boundary format, delivered as a migration; count the violating rows first (orphaned `itens_pedido`, orders for unknown users).
### [MEDIUM] Missing Boundary Validation — references and state rules   (AP-11)
File: controllers.py:237-255 (now controllers/order_controller.py)
Reason not applied: requests that succeed today (status update of an unknown order, an order for an unknown user) would start failing; the allowed status transitions are a product rule.
Proposed change: verify referenced records exist (`404`), define the status transitions, return stock on cancellation.
### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models.py:203-233 (now the list functions in models/order.py, models/product.py and models/user.py)
Reason not applied: pagination changes the collection a client receives today.
Proposed change: a documented default and maximum page size with an opt-out period.
### [MEDIUM] Missing Boundary Validation — unbounded order item list   (AP-11)   origin: missed-in-phase-2
File: controllers.py:188-220 (now controllers/order_controller.py)
Reason not applied: a maximum number of items per order is a product decision; a client may send large orders today.
Proposed change: choose a maximum and reject larger lists with `400`.
### [MEDIUM] Missing Schema-Level Integrity Constraints — required columns and closed value sets   (AP-20)   origin: missed-in-phase-2
File: database.py:14-53 (now models/database.py)
Reason not applied: SQLite adds NOT NULL and CHECK constraints only by rebuilding the table, and existing rows may already violate them (status, type and category are free text).
Proposed change: count the violating rows, then rebuild the tables with NOT NULL and CHECK constraints inside one transaction.

## Verification Coverage
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - Language-level deprecations by documentation lookup (Layer 2, official docs for Python 3.13 and Flask): not performed, in Phase 2 or in the re-audit → a deprecated API that raises no warning on the exercised paths and appears in no registry record is not covered. This is why the re-audit line is `⚠` and not `○`.
Verified by hand rather than by the replay (the shape comparison cannot see values): the masked `senha` and `secret_key` values, the stored hash prefix, the upgrade of a legacy plain-text row on login, and the operator token cases (none, wrong, correct). The operator path with the credential also ran in the replay (`get-relatorios-vendas-operador`: PASS).
Not exercised: the fallback that skips the unique index when the existing data already holds duplicate sign-in names (the databases here were created fresh).
Deprecation evidence for the refactored application: `python -X dev` with warnings forced on; boot output of the second full replay read and clean; the output of the other boots was not inspected.
`sec-get-console` probes the framework debugger path, which is not part of the application's own surface; it is the evidence for the debug-mode finding.
Surface inventory: `reports/surface.json` carries the placeholder `replay-operator-token` for the operator header (a replay fixture, not a credential). The search-injection entry was amended before the baseline was captured, after the first draft turned out to behave like its benign sibling on the original.
Isolation: container (docker 28.5.2, python:3.13-slim); scratch root: the environment scratch directory; the snapshot directory was deleted after the second re-audit; no container of this run is alive.
Commands: 0 directory changes, 0 chained commands. Single-file copies of this run's own report, inventory and scratch script were made with one literal `Copy-Item` each; no command was written with a variable or a `NON-LITERAL` path.
================================
