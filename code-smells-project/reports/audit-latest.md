## Phase 1 — Project Analysis
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        code-smells-project
Language:      Python (runtime version not declared by the project; image python:3.13-slim used for execution)
Framework:     Flask 3.1.1 (exact pin in requirements.txt; no lockfile)
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Domain:        E-commerce store API — products (produtos), users (usuarios), orders (pedidos/itens_pedido), sales report
App type:      HTTP service
Architecture:  Nominal MVC-by-filename: app.py (routes + admin handlers with raw SQL), controllers.py (HTTP + validation + business rules), models.py (raw SQL + business rules), database.py (global connection + DDL + seed); no config/service layer
Source files:  4 files analyzed (*.py; excluded: README.md, requirements.txt, .claude/, reports/, __pycache__, .gitignore matches)
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, embedded file loja.db, DDL in database.py)
Boot:          python app.py (cwd = target root; from project README)
Port:          5000, fixed in source (app.run(host="0.0.0.0", port=5000, debug=True)); no override read
Runtime env:   Python 3.13 (official image), deps installed in container from requirements.txt
Isolation:     container (docker 28.5.2, image python:3.13-slim); container commands via PowerShell (Git Bash rewrites POSIX paths)
================================
```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-30 14:49
Mode:    full
Confirmation: human-confirmed: y
Tree:    clean at 7ef5932 (no uncommitted changes under the target)
Runtime: installed the declared dependencies from requirements.txt into run-1/.deps (pip --target, inside the container, in the run copy outside the target)
Isolation: container (docker 28.5.2, image python:3.13-slim)
Scratch: environment scratch directory (C:\Users\lucas\AppData\Local\Temp\claude\D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill\d2004b79-894d-46db-979b-1fbb52811091\scratchpad\refactor-arch-code-smells-project-20260930-1449)  (protocol §1.1)

## Summary
CRITICAL: 12 | HIGH: 7 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: app.py:7-7
Description: The framework's session/signing key is set to a string literal (`app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`). The same literal is repeated in controllers.py:289, where it is also returned to clients (see the AP-18 finding on controllers.py:264-292).
Impact: Anyone with read access to the repository holds the signing key; any signed cookie or token the application ever issues can be forged. Rotation requires a code change and a deploy, and the value stays in git history.
Recommendation: Read the key from the environment through a single configuration module; when absent, fail loudly or generate a per-process random key (the application does not use sessions today). See RP-01.
Contract: safe

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: app.py:11-30
Description: None of the 17 registered business routes has an authentication or ownership check: `/usuarios` and `/usuarios/<id>` list every account, `/pedidos/usuario/<usuario_id>` returns any user's orders by changing the path id (IDOR), and `PUT/DELETE /produtos/<id>` and `PUT /pedidos/<id>/status` mutate state anonymously. A `tipo` role column (`admin`/`cliente`) exists in the schema but is never checked; `/login` returns the user record but issues no session or token, so there is no identity model at all.
Impact: Any network client reads every user's personal data and orders, edits the catalogue and changes order status, indistinguishably from legitimate use.
Recommendation: Introduce an identity model (session or signed token issued by `/login`), then enforce ownership on principal-scoped reads and a role check on catalogue/status mutations. See RP-04.
Contract: contract-changing — there is no identity model, so every current client (all anonymous) would receive the new 401/403.

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: app.py:47-57
Description: `POST /admin/reset-db` deletes every row of the four tables with no authentication, confirmation or environment guard; the handler also issues the driver calls itself (AP-05). The sibling route `POST /admin/query` (app.py:59-78) is equally unauthenticated (see the AP-02 finding on those lines). Escalated to maximum urgency: the operation is destructive.
Impact: One anonymous request erases all products, users and orders.
Recommendation: Remove the administrative surface from the public application, or gate it behind an identity model with an admin role and an explicit environment flag. See RP-04.
Contract: contract-changing — removing or protecting the route changes what every current (anonymous) client observes.

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: app.py:59-78
Description: `POST /admin/query` passes the request body's `sql` field straight to `cursor.execute(query)` and commits non-SELECT statements. Observed: `{"sql": "SELECT COUNT(*) AS n FROM produtos"}` returns 200 with rows. It is unauthenticated (AP-04), and a body that is not a JSON object (`[]`) crashes it into the framework debugger page (observed 500 text/html).
Impact: Arbitrary SQL — read, modify or drop anything in the database — by any network client.
Recommendation: Remove the endpoint; if an operational query tool is needed, move it out of the public surface. See RP-02 / RP-04.
Contract: contract-changing — the route would disappear or start rejecting its current callers.

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:80-88
Description: The entry point starts the framework's development server with `debug=True` bound to `0.0.0.0` (line 88), and `app.config["DEBUG"] = True` is set by literal at line 8. Observed at boot: "Debug mode: on", "Running on all addresses (0.0.0.0)", "Debugger is active!", and an unhandled exception (POST /admin/query with body `[]`) answered with the 500 HTML debugger page. No production server is declared anywhere. Escalated to CRITICAL: an interactive debugger console reachable from outside the host.
Impact: The interactive Werkzeug debugger is exposed on every interface — remote code execution by design once its PIN is obtained — and tracebacks with source excerpts are served to any client that triggers an error.
Recommendation: Read debug mode from configuration, default off; keep the development server for development only and declare a production WSGI server. See RP-17.
Contract: safe for the debug flag (only the framework's default error page changes, status kept); declaring a production WSGI server is contract-changing (new runtime dependency) and will be proposed.

### [CRITICAL] God Module / God Class   (AP-03)
File: controllers.py:1-292
Description: One module holds the handlers for four unrelated domain concepts — products (5-126), users and login (128-186), orders (188-255), reports and health (257-292) — and mixes delivery (request parsing and status selection throughout), business rules (the category allow-list at 52-54, the order-status enumeration and its notification side effects at 242-250, order notifications at 208-210) and persistence (raw driver calls in `health_check`, 264-274). Handlers are not "parse → call → render"; `models` functions are called directly with no use-case layer between (AP-05 in every handler, reported here per the precedence rule).
Impact: No rule can be tested without a Flask request context; every change touches a file shared by every feature; a second entry point (CLI, job) cannot reuse any of the logic.
Recommendation: Split into per-concept route modules (views), controllers holding use cases with plain values, and models/repositories holding the rules and SQL. See RP-03 / RP-05.
Contract: safe

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: controllers.py:264-292
Description: `GET /health` returns, to any anonymous caller, the signing key literal (`"secret_key": "minha-chave-super-secreta-123"`), `"debug": True`, the database file path and a hard-coded `"ambiente": "producao"` — a diagnostic endpoint exposing configuration. Observed in the Phase 2 run (200, JSON). Escalated to CRITICAL: the output exposes a credential.
Impact: The session-signing key is served over HTTP, so anyone who can reach the health check can forge signed data; the response also maps internals for further attacks.
Recommendation: Keep the fields (clients may parse them) but mask the secret's value and derive the others from configuration; never serialize a secret. See RP-17 / RP-08.
Contract: safe — masking the value while keeping the field and its type (string).

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: database.py:75-83
Description: The bootstrap routine that runs on first connection seeds the runtime database with three accounts whose passwords are literals, including an `admin` account (`"admin@loja.com", "admin123", "admin"`). This data reaches the runtime datastore in every environment that boots the application, so it is in scope (not a test fixture).
Impact: Every deployment starts with an administrator account whose password is public in the repository.
Recommendation: Seed demonstration accounts only behind an explicit development flag, or read the initial admin credential from the environment. See RP-01.
Contract: contract-changing — the README documents the example users; the seeded accounts and their known passwords would stop logging in.

### [CRITICAL] God Module / God Class   (AP-03)
File: models.py:1-314
Description: One module holds persistence for four unrelated concepts — products (4-70, 285-314), users and authentication (72-131), orders (133-233, 275-283) and the sales report (235-273) — and mixes persistence (raw SQL in every function), business rules (order total and stock checks at 139-146, stock decrement at 163-166, the discount tiers at 256-262) and presentation (hand-written row-to-dict serialization repeated in nearly every function). Escalated context: it also contains the systemic injection (AP-02) below.
Impact: Every domain concept shares one untestable file whose every function opens the global connection; a change to any rule risks all of them.
Recommendation: One model/repository module per concept, with rules in the model layer and SQL in parameterized repository methods. See RP-03.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models.py:72-103
Description: `get_todos_usuarios` and `get_usuario_por_id` serialize the whole row including `"senha"` — which is the plaintext password (see the next AP-08 finding). Observed: `GET /usuarios` returns every account's password to an anonymous caller. Escalated from HIGH to CRITICAL: plaintext credentials of every account are disclosed over the network with no authentication (AP-04).
Impact: One unauthenticated request yields every user's password, reusable on other systems.
Recommendation: Select fields explicitly and never return the password; to keep the response shape, mask the value while keeping the field. See RP-08.
Contract: safe — masking the value while keeping the field and its type; removing the field would be contract-changing.

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: models.py:105-120
Description: `login_usuario` builds `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` from the request body. Observed: `{"email": "' OR '1'='1' --", "senha": "x"}` returns 200 "Login OK" with the first account (authentication bypass). The same construction habit is systemic: every statement in the module is concatenated — 28, 47-50, 57-61, 68, 92, 126-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 279-281 and the search builder 289-299 (observed: `GET /produtos/busca?categoria='` → 500 with the driver's syntax error; `POST /produtos` with an apostrophe in `nome` → 500 `near "Reilly": syntax error`). Maximum urgency: unauthenticated, in the authentication path, includes writes.
Impact: Authentication bypass, data disclosure and data modification through any string parameter; legitimate input containing an apostrophe fails.
Recommendation: Parameterize every statement (placeholders with a separate parameter tuple); build the search's WHERE clause from fixed fragments plus bound values. See RP-02.
Contract: safe

### [CRITICAL] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: models.py:122-131
Description: `criar_usuario` stores the password exactly as received in a `senha TEXT` column (database.py:31), and `login_usuario` compares it in SQL by plain equality (109-111); seeded passwords are plaintext too (database.py:75-79). Escalated to CRITICAL: passwords are stored recoverably.
Impact: Any read of the database file — or of `GET /usuarios` — compromises every account, and via password reuse accounts on other systems.
Recommendation: Store a salted hash from a purpose-built KDF available in the standard library (e.g. PBKDF2/scrypt), verify with a constant-time comparison, and migrate existing plaintext rows on startup. See RP-08.
Contract: safe — valid credentials keep logging in; only the stored representation changes.

### [HIGH] Swallowed or Uncentralized Error Handling   (AP-09)
File: controllers.py:5-12
Description: Every handler wraps its body in `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500` (controllers.py 5-12, 14-22, 24-62, 64-96, 98-109, 111-126, 128-134, 136-144, 146-165, 167-186, 188-220, 222-227, 229-235, 237-255, 257-262), so internal exception text reaches clients (observed: `near "Reilly": syntax error`, SQLite errors). There is no central error handler; errors outside those blocks (app.py admin handlers) reach the debugger page (observed). A missing JSON body turns into a 500 via `None.get` (169-170, 239-240). The order creation writes several rows with one commit at the end and no rollback (models.py:148-168): an exception between them leaves the open transaction on the shared connection to be committed by the next request.
Impact: Clients see driver internals; malformed input and server faults are indistinguishable; a failed order can be half-persisted later by an unrelated request.
Recommendation: One error boundary registered on the application that maps a small error taxonomy to the existing statuses and `{"erro": ...}` body, logs the detail internally and returns a safe message; explicit transaction with rollback around multi-write use cases. See RP-09.
Contract: safe — statuses and the `{"erro": string}` shape are preserved; only the internal message value is replaced.

### [HIGH] Duplicated Logic   (AP-12)
File: controllers.py:64-96
Description: `atualizar_produto` re-implements the validation of `criar_produto` (24-62) and the copies have diverged: the update omits the name-length checks (47-50) and the category allow-list (52-54). Escalated to HIGH: the copies already behave differently — a category rejected by POST is accepted by PUT.
Impact: Invalid domain values (unknown category, one-letter or 10 000-character names) enter through the update door that the create door refuses.
Recommendation: One product validation in the model layer, used by both use cases. See RP-12 / RP-11.
Contract: safe — the rejected values break an invariant the domain already states (the category enumeration and name bounds enforced on create); only requests no legitimate client sends are rejected.

### [HIGH] Missing Boundary Validation   (AP-11)
File: controllers.py:188-220
Description: Order creation checks only presence of `usuario_id` and a non-empty `itens`; each item's `quantidade` is never checked for type or sign (models.py:139-146), `usuario_id` is never verified to exist, and `produto_id` absence raises KeyError → 500. Observed: an item with `"quantidade": -5` is accepted (201), producing a negative total and *increasing* stock via `estoque - (-5)`. Escalated to HIGH: the unvalidated value reaches the datastore and corrupts domain state (stock, revenue). Related: `preco`/`estoque` types are not checked on product create/update (43-46, 87-90: a string raises TypeError → 500).
Impact: Any client can inflate stock and create negative-value orders that flow into the sales report.
Recommendation: Validate at the boundary: positive integer quantities, existing user and products, numeric price/stock; reject with 400 in the handler's existing error shape. See RP-11.
Contract: safe — negative/zero/non-numeric quantities and unknown user ids are invalid on their face; no legitimate client sends them.

### [HIGH] Mutable Global State   (AP-07)
File: database.py:4-11
Description: A module-level `db_connection` is lazily assigned by `get_db()` and shared by every request and thread (`check_same_thread=False`), with one open transaction across all of them; it is never closed.
Impact: Concurrent requests share one connection and transaction, so one request's uncommitted writes are committed or seen by another; the application cannot safely run with more than one thread or be tested in isolation.
Recommendation: Connection per request (opened in the request context, closed at teardown), created by a factory the composition root owns. See RP-07.
Contract: safe

### [HIGH] Missing Schema-Level Integrity Constraints   (AP-20)
File: database.py:14-53
Description: `usuarios.email` is used as the sign-in identity (`login_usuario` takes `fetchone()`) but has no UNIQUE constraint; `pedidos.usuario_id`, `itens_pedido.pedido_id` and `itens_pedido.produto_id` reference other tables with no FOREIGN KEY (and SQLite foreign keys are never enabled), so `DELETE /produtos/<id>` leaves order items pointing at nothing (the code already falls back to "Desconhecido", models.py:196); money (`preco`, `total`, `preco_unitario`) is stored as `REAL`. Escalated to HIGH: identity and money can be corrupted — two accounts may share one email, and totals are binary-float sums.
Impact: Login can resolve to the wrong account; order history silently loses product references; revenue figures drift by fractions of a cent.
Recommendation: UNIQUE on email, foreign keys enabled per connection with a declared delete rule, money in integer cents or DECIMAL, with a migration for existing data. See RP-19.
Contract: contract-changing — duplicate-email sign-ups and deletion of a product referenced by orders would start failing; existing databases need a migration.

### [HIGH] Hard-Wired Dependencies / No Composition Root   (AP-06)
File: models.py:1-1
Description: Models import the concrete `database.get_db` singleton and every one of the 15 model functions opens it itself (models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286); controllers.py:3/266 and app.py:4/49/66/82 do the same. There is no place where the object graph is assembled; app.py mixes wiring with handlers.
Impact: No model or controller can be exercised without the real SQLite file; swapping the datastore or injecting a test double means editing every function.
Recommendation: A composition root (application factory) that builds configuration, the connection provider and the repositories, and passes them to controllers. See RP-06.
Contract: safe

### [HIGH] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:133-169
Description: `criar_pedido` runs one SELECT per item to validate (139-146), then per item another SELECT for the price, an INSERT and an UPDATE (154-166). Escalated to HIGH: the loop bound is the request's `itens` array, caller-controlled and unbounded.
Impact: One request can issue an arbitrary number of round trips while holding the single shared connection, stalling every other request.
Recommendation: Fetch all referenced products in one `IN` query, reuse the fetched price, and batch the inserts/updates inside one transaction; bound the number of items. See RP-10.
Contract: safe

### [MEDIUM] Unsafe Handling of Credentials and Sensitive Data   (AP-08)
File: controllers.py:161-182
Description: User email addresses are written to stdout on every sign-up (161) and every successful or failed login (179, 182), including attacker-supplied strings. De-escalated from HIGH to MEDIUM: the values are personal data (email), not credentials or tokens.
Impact: Personal data spreads to wherever process output is collected, with weaker access control than the database.
Recommendation: Use the logging module with non-identifying context (user id, outcome); never log the raw email or request body. See RP-08.
Contract: safe

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models.py:4-8
Description: `GET /produtos`, `GET /usuarios` (models.py:72-76) and `GET /pedidos` (203-207) read whole tables with `SELECT *` and no limit or pagination; the search (289-299) is equally unbounded. Cursors are never closed and the shared connection has no lifecycle (see AP-07).
Impact: Response size and latency grow with data volume; a large catalogue or order table makes each listing call a memory spike.
Recommendation: Add pagination with a bounded page size. See RP-13.
Contract: contract-changing — imposing a default page size changes what an existing client receives from a listing.

### [MEDIUM] Duplicated Logic   (AP-12)
File: models.py:9-21
Description: The product row-to-dict mapping is written three times (9-21, 31-40, 302-313), the user mapping twice (78-86, 94-102), and the whole order assembly with items is duplicated line for line between `get_pedidos_usuario` (171-201) and `get_todos_pedidos` (203-233).
Impact: A field added to one copy is forgotten in the others; responses for the same entity drift apart.
Recommendation: One serializer per entity and one order-assembly function parameterized by filter. See RP-12.
Contract: safe

### [MEDIUM] N+1 and Query-Inside-Loop Access   (AP-10)
File: models.py:171-233
Description: `get_pedidos_usuario` and `get_todos_pedidos` run one query per order for its items and one query per item for the product name (1 + N + N·M round trips). `relatorio_vendas` issues five separate queries where one aggregate would do (239-254), and `health_check` four (controllers.py:268-274).
Impact: `GET /pedidos` latency grows with orders × items; passes on seed data, degrades in production.
Recommendation: One query joining orders, items and products, grouped in memory; one aggregate query for the report. See RP-10.
Contract: safe

### [MEDIUM] Magic Values   (AP-15)
File: models.py:256-262
Description: The discount tiers are bare literals — thresholds 10000/5000/1000 and rates 0.1/0.05/0.02 — inline in the report query function. Escalated to MEDIUM: a commercial rule whose owner is not the engineer.
Impact: Nobody can tell whether changing a threshold is safe, or where else it is assumed.
Recommendation: Named constants (or configuration) in the model layer next to the rule. See RP-15.
Contract: safe

### [MEDIUM] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:2-2
Description: flask-cors 5.0.1 (exact pin) has three advisories from OSV.dev (looked up 2026-09-30): GHSA-43qf-4rqw-9q2g (CVE-2024-6866, case-insensitive path matching), GHSA-7rxf-gvfg-47g4 (CVE-2024-6839, regex priority), GHSA-8vgw-p6qm-5gr7 (CVE-2024-6844, `+` path normalization), all MODERATE; fixed in 6.0.0. MEDIUM per the moderate rating; the application uses one global `CORS(app)` policy, so the per-path matching defects do not currently change which policy applies.
Impact: Any future per-path CORS configuration would be matched incorrectly; the pinned version receives no fix.
Recommendation: Upgrade to flask-cors 6.0.0 or later (major upgrade; no extra configuration named by the advisories). See RP-18.
Contract: safe only if the replay covers the changed behaviour — the inventory includes a cross-origin GET and a preflight entry so the CORS contract headers are compared; otherwise proposed.

### [LOW] Misleading Names and Inconsistent Structure   (AP-16)
File: controllers.py:14-14
Description: `buscar_produto` (fetch by id, line 14) and `buscar_produtos` (free-text search, line 111) differ by one letter but do different things; models mix an English verb with Portuguese nouns (`get_todos_produtos`, `get_usuario_por_id`) beside `criar_`/`deletar_`; handlers take a parameter named `id` that shadows the builtin; the module named `controllers` actually holds the request handlers (the view layer).
Impact: Readers pick the wrong function and misjudge which layer a file belongs to.
Recommendation: Rename internal identifiers to one convention and name modules by the layer they hold. See RP-16.
Contract: safe — internal identifiers only; routes unchanged.

### [LOW] Magic Values   (AP-15)
File: controllers.py:242-250
Description: Order-status values are string literals repeated across files with no single definition — the allow-list here, `'pendente'` in models.py:150 and database.py:40, `'pendente'/'aprovado'/'cancelado'` in models.py:247-253; the category allow-list is a local literal (controllers.py:52); the version `"1.0.0"` is duplicated (app.py:36, controllers.py:285).
Impact: A typo silently creates a new status that no report counts.
Recommendation: One enumeration of statuses and categories in the model layer. See RP-15.
Contract: safe

### [LOW] Dead Code and Commented-Out Code   (AP-17)
File: database.py:2-2
Description: `import os` is never used; `import sqlite3` in models.py:2 is never used either.
Impact: Noise that suggests dependencies the module does not have.
Recommendation: Delete the unused imports. See RP-16.
Contract: safe

### [LOW] Known-Vulnerable Dependency   (AP-19)
File: requirements.txt:1-1
Description: flask 3.1.1 has GHSA-68rp-wp8r-4726 / PYSEC-2026-2151 (CVE-2026-27205, missing `Vary: Cookie` on some session access), rated LOW by GitHub, OSV.dev looked up 2026-09-30; fixed in 3.1.3. The application never accesses `session`, so the affected path is unused.
Impact: Latent only; becomes relevant if sessions are introduced (e.g. for the identity model AP-04 needs).
Recommendation: Upgrade to flask 3.1.3 (same major). See RP-18.
Contract: safe — upgrade within the same major version.

## Catalog Coverage

| Entry | Signals checked | Result |
|---|---|---|
| AP-01 | secret-named identifiers with literals; credential literals in seed/bootstrap data by column position; connection URLs with inline credentials; high-entropy/prefixed literals; framework signing key set by literal; committed credential files (.env, *.pem, *.key); env reads with a real-secret fallback | 2 findings: app.py:7-7, database.py:75-83 |
| AP-02 | input reaching driver calls by concatenation/interpolation; interpolation markers inside statement strings (which side of the call); ORM escape hatches; dynamic identifiers; shell/process execution; unsafe deserialization / template injection; path traversal | 2 findings: app.py:59-78, models.py:105-120 (systemic, all sites listed) |
| AP-03 | ≥3 responsibility categories per module; >300–400 lines with ≥2 categories; units >50 lines / deep nesting / >5 params / varying return shapes; several unrelated domain concepts per file; low-cohesion classes; grab-bag utility modules; very high afferent coupling | 2 findings: controllers.py:1-292, models.py:1-314 (app.py: composition + admin handlers, reported under AP-04/AP-02; database.py: one concept) |
| AP-04 | principal-scoped entries without authn/ownership; lookups filtered only by input id (IDOR); checks only on one door; role/tenant trusted from request; tokens decoded not verified; unreachable/late checks; disabled guards | 2 findings: app.py:11-30, app.py:47-57 |
| AP-05 | domain decisions in handlers; persistence calls in handlers; handlers >30 lines not mapping-only; request objects deep in the stack; same rule in two handlers; pass-through service layer | 0 separate findings — every hit is inside modules filed as AP-03 (controllers.py) or on lines filed as AP-04/AP-02 (app.py admin handlers), per the precedence rule |
| AP-06 | collaborators constructed inside logic; import-time side effects; no composition root; no test seam (clock/random/fs/db); domain importing concrete driver; configuration read at point of use | 1 finding: models.py:1-1 |
| AP-07 | module-level mutable reassigned from several places; request-scoped data stored globally; in-memory store of record; mutable defaults / shared class attributes; cache/pool without lifecycle; monkey-patching; in-process id counters | 1 finding: database.py:4-11 |
| AP-08 | reversible password storage; fast digests; shared/missing salt; non-constant-time comparison; sensitive values in logs/errors; whole-record serialization leaking fields; transport/cert verification disabled; no token expiry/rotation | 3 findings: models.py:72-103, models.py:122-131, controllers.py:161-182 |
| AP-09 | empty/log-and-continue/success-on-failure catches; over-broad catches; repeated error-to-response mapping; no central handler (observed the framework default: debugger HTML page); internals in response bodies; inconsistent error signalling; multi-write without transaction; exceptions for control flow | 1 finding: controllers.py:5-12 |
| AP-10 | driver calls inside loops (one level of indirection); per-element FK fetch; lazy loads in iteration; repeated reads answerable by one set query; remote calls in loops; whole table filtered in app code; write loops without batching | 2 findings: models.py:133-169, models.py:171-233 |
| AP-11 | input used with no presence/type/range/format check; optional input dereferenced; unconstrained pagination; numeric parsing without failure path; validation on one door only; validation after side effect; unenforced domain invariants; no body/array bounds; scattered ad-hoc validation | 1 finding: controllers.py:188-220 (divergent-door case filed as AP-12 controllers.py:64-96) |
| AP-12 | ≥10-line structural clones; same rule in several places; repeated validation/error/serialization shape; hand-written mappings in several places; diverged copy-and-modify lineage; repeated constant literals; repeated guard conditions | 2 findings: controllers.py:64-96, models.py:9-21 |
| AP-13 | paired acquire/release without scope construct; handles without release on failure; per-call connections / unbounded pools; outbound calls without timeout; unbounded retries; unbounded reads; unbounded accumulators; background tasks without shutdown; unbounded recursion | 1 finding: models.py:4-8 (no outbound network calls, no background tasks, no recursion) |
| AP-14 | Layer 1: runtime warnings forced on (`python -X dev`, `PYTHONWARNINGS=always::DeprecationWarning`) while exercising: boot via the derived command (`python app.py`, which also runs the schema+seed bootstrap `get_db()`), the Werkzeug reloader child, and 46 surface requests covering every registered route (all four modules' entries); deprecated flags in manifest (none; no lockfile); structurally superseded constructs. Layer 2: PyPI JSON yanked metadata for flask 3.1.1 and flask-cors 5.0.1 (2026-09-30) | none — no DeprecationWarning emitted; neither pinned release is yanked |
| AP-15 | unexplained numeric literals in rules; unit-less durations/sizes; string enumerations repeated across files; repeated literals; bare numeric codes; unnamed tuple/array indexes; environment-specific literals inline (port 5000, `loja.db`) | 2 findings: models.py:256-262, controllers.py:242-250 |
| AP-16 | names contradicting behaviour; non-descriptive identifiers; several names for one concept; how-not-what names; mixed conventions; mixed human languages; misplaced files; stale comments; boolean parameters | 1 finding: controllers.py:14-14 |
| AP-17 | commented-out blocks; unreachable branches; unreferenced units; unused imports / undeclared-or-unused dependencies; unused parameters/values; constant feature flags; unregistered endpoints; *_old/*.bak copies | 1 finding: database.py:2-2 |
| AP-18 | debug mode on by literal on the start path (observed "Debugger is active!"); dev server as production; any-address bind combined with debug; internals in error output (observed debugger page and driver errors); CORS wildcard with credentials/reflection (flask-cors default: `*`, no credentials — not a hit); unrestricted diagnostic/admin surfaces; protective defaults disabled | 2 findings: app.py:80-88, controllers.py:264-292 (admin routes filed under AP-04/AP-02) |
| AP-19 | OSV.dev querybatch (2026-09-30) for direct deps at exact pins and for transitive versions installed in the run (werkzeug 3.1.9, jinja2 3.1.6, itsdangerous 2.2.0, click 8.5.0, blinker 1.9.0, markupsafe 3.0.3); lockfile vs manifest; ranges without lockfile (none: all exact pins) | 2 findings: requirements.txt:2-2, requirements.txt:1-1; transitives: no advisories (installation of 2026-09-30) |
| AP-20 | identity columns without UNIQUE; FK-like columns without FOREIGN KEY (and SQLite FK enforcement never enabled); parent deletes without child rule; money in binary floating point; required columns nullable / closed sets as free text | 1 finding: database.py:14-53 |

## Dependency and Deprecated API Verification

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Application code (boot + bootstrap + 46 requests) | Python 3.13 / Flask 3.1.1 | deprecation (runtime warnings forced on) | A (none emitted) | `python -X dev`, `PYTHONWARNINGS=always::DeprecationWarning` | n/a — local | no issue found |
| flask | 3.1.1 | deprecation / yanked | B | https://pypi.org/pypi/flask/3.1.1/json (`yanked: false`) | 2026-09-30 | no issue found |
| flask-cors | 5.0.1 | deprecation / yanked | B | https://pypi.org/pypi/flask-cors/5.0.1/json (`yanked: false`) | 2026-09-30 | no issue found |
| flask | 3.1.1 | advisory | B | OSV.dev: GHSA-68rp-wp8r-4726 / PYSEC-2026-2151 (LOW) | 2026-09-30 | AP-19 requirements.txt:1-1 |
| flask-cors | 5.0.1 | advisory | B | OSV.dev: GHSA-43qf-4rqw-9q2g, GHSA-7rxf-gvfg-47g4, GHSA-8vgw-p6qm-5gr7 (+ PYSEC-2026-1383/1384/1385 aliases), MODERATE | 2026-09-30 | AP-19 requirements.txt:2-2 |
| werkzeug, jinja2, itsdangerous, click, blinker, markupsafe | 3.1.9, 3.1.6, 2.2.0, 8.5.0, 1.9.0, 3.0.3 (installed 2026-09-30) | advisory | B | OSV.dev querybatch | 2026-09-30 | no issue found (holds for this installation date only) |

## Execution Log

| # | Phase | Action | Mode | Handle | Command | Result |
|---|---|---|---|---|---|---|
| 1 | 2 | start | container | refactor-arch-code-smells-project-20260930-1449-1 | `docker run -d ... -v run-1:/app -w /app python:3.13-slim sleep infinity` (run-1) | running; used for `pip install -r requirements.txt` |
| 2 | 2 | start (attempt) | container | proc state /tmp/app-1.json inside container -1 | `proc.py start ... -- python -X dev app.py` | refused, exit 2: the image has no `ps`, so proc could not record the start time; proc stopped its own child (pid 22) and declared it — nothing left running |
| 3 | 2 | stop | container | refactor-arch-code-smells-project-20260930-1449-1 | `docker rm -f` by exact name | removed |
| 4 | 2 | start | container | refactor-arch-code-smells-project-20260930-1449-2 | `docker run -d ... -e PYTHONPATH=/app/.deps -e PYTHONWARNINGS=always::DeprecationWarning python -X dev app.py` (run-1) | ready on port 5000 (`proc.py wait`) |
| 5 | 2 | stop | container | refactor-arch-code-smells-project-20260930-1449-2 | `docker rm -f` by exact name | removed |
| 6 | 3a | start | container | refactor-arch-code-smells-project-20260930-1449-3 | `python app.py` (run-2, original deps from run-1/.deps read-only) | ready on port 5000; baseline captured (51 entries) |
| 7 | 3a | stop | container | refactor-arch-code-smells-project-20260930-1449-3 | `docker rm -f` by exact name | removed |
| 8 | 3a | start | container | refactor-arch-code-smells-project-20260930-1449-4 | `python app.py` (run-3) | ready; destructive `delete-produto` captured alone |
| 9 | 3a | stop | container | refactor-arch-code-smells-project-20260930-1449-4 | `docker rm -f` by exact name | removed |
| 10 | 3a | start | container | refactor-arch-code-smells-project-20260930-1449-5 | `python app.py` (run-4) | ready; destructive `admin-reset-db` captured alone |
| 11 | 3a | stop | container | refactor-arch-code-smells-project-20260930-1449-5 | `docker rm -f` by exact name | removed |
| 12 | 3c | start | container | refactor-arch-code-smells-project-20260930-1449-6 | `sleep infinity` (refactored-1) + `pip install --target /app/.deps -r requirements.txt` (refactored manifest) | installed flask 3.1.3, flask-cors 6.0.0 |
| 13 | 3c | stop | container | refactor-arch-code-smells-project-20260930-1449-6 | `docker rm -f` by exact name | removed |
| 14 | 3c | start | container | refactor-arch-code-smells-project-20260930-1449-7 | `python -X dev app.py`, DeprecationWarning forced on (refactored-1) | ready on port 5000; replay 1 (51 entries) |
| 15 | 3c | stop | container | refactor-arch-code-smells-project-20260930-1449-7 | `docker rm -f` by exact name | removed |
| 16 | 3c | start | container | refactor-arch-code-smells-project-20260930-1449-8 | `python app.py` (refactored-2) | ready; `delete-produto` replayed alone |
| 17 | 3c | stop | container | refactor-arch-code-smells-project-20260930-1449-8 | `docker rm -f` by exact name | removed |
| 18 | 3c | start | container | refactor-arch-code-smells-project-20260930-1449-9 | `python app.py` (refactored-3) | ready; `admin-reset-db` replayed alone |
| 19 | 3c | stop | container | refactor-arch-code-smells-project-20260930-1449-9 | `docker rm -f` by exact name | removed |
| 20 | 3d | start | container | refactor-arch-code-smells-project-20260930-1449-10 | `python app.py` (run-5, original) | ready; late entry `create-pedido-oversell-duplicate-lines` captured against the original (§4.3) |
| 21 | 3d | stop | container | refactor-arch-code-smells-project-20260930-1449-10 | `docker rm -f` by exact name | removed |
| 22 | 3d | start | container | refactor-arch-code-smells-project-20260930-1449-11 | `python -X dev app.py`, DeprecationWarning forced on (refactored-4) | ready; replay 2 (52 entries) |
| 23 | 3d | stop | container | refactor-arch-code-smells-project-20260930-1449-11 | `docker rm -f` by exact name | removed |
| 24 | 3d | start | container | refactor-arch-code-smells-project-20260930-1449-12 | `python app.py` (refactored-5) | ready; `delete-produto` replayed alone |
| 25 | 3d | stop | container | refactor-arch-code-smells-project-20260930-1449-12 | `docker rm -f` by exact name | removed |
| 26 | 3d | start | container | refactor-arch-code-smells-project-20260930-1449-13 | `python app.py` (refactored-6) | ready; `admin-reset-db` replayed alone |
| 27 | 3d | stop | container | refactor-arch-code-smells-project-20260930-1449-13 | `docker rm -f` by exact name | removed |

## Verification Coverage
Full — all planned checks executed, with these declared deviations:
  - Boot mechanism: the application ran as the container's main process (`docker run -d ... python -X dev app.py`) instead of `docker exec -d`, so its stdout/stderr (deprecation warnings, tracebacks) is readable through `docker logs`; dependencies were installed with `pip --target /app/.deps` inside the run copy, from requirements.txt. Nothing ran inside the target.
  - Destructive entries (`DELETE /produtos/10`, `POST /admin/reset-db`) were not exercised in Phase 2; they will be captured alone in Phase 3a.
  - Execution Log row 2: `proc start` inside the container failed by design (no `ps` in the image) and stopped its own child; the start/stop pair is within this run's container, which was then removed by name.

================================
Total: 29 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
>

Answer: y (human, relayed by the orchestrator) — Phase 3 over all findings.

---

# Phase 3 — Refactoring

## Layout decisions
- Target: literal MVC for an HTTP service. `models/` holds entities, rules **and** their SQL repositories (persistence kept inside the model layer, uniformly); `controllers/` hold one use case per method with plain values; `views/` hold Flask blueprints (parse → call → render); `config/` reads the environment once; `middlewares/` hold the error boundary and the per-request connection; `adapters/` holds the notification side effect (stdout, as before). `app.py` is the composition root (`create_app()` factory) and remains the entry point (`python app.py`).
- Rewritten in place: `controllers.py`, `models.py` and `database.py` were removed; their content lives in the new layers. Every route, method, success status and response body shape is unchanged (replay below).
- Naming convention: domain vocabulary in Portuguese; framework/infrastructure entry points keep the framework's names (`create_app`, `Settings`, `load_settings`).

## Transformations applied (finding → playbook)
| Phase 2 finding | Transformation | What was done |
|---|---|---|
| AP-01 app.py:7-7 | RP-01 | `SECRET_KEY` read from the environment (config/settings.py); random per-process key when absent; `.env.example` and `.gitignore` added. **Rotate the committed key — it stays in git history.** |
| AP-02 models.py:105-120 | RP-02 | Every statement parameterized; search built from fixed fragments + bound values |
| AP-03 controllers.py, models.py | RP-03/RP-05 | Split into views / controllers / models per concept |
| AP-06 models.py:1-1 | RP-06 | Repositories receive a connection provider; composition root wires everything |
| AP-07 database.py:4-11 | RP-07 | Global connection removed; one connection per request, closed at teardown |
| AP-08 models.py:72-103 | RP-08 | `senha` value masked (`********`), field and type kept |
| AP-08 models.py:122-131 | RP-08 | PBKDF2-SHA256 (stdlib) salted hashes, constant-time verify; plaintext rows migrated at startup; seeded passwords hashed |
| AP-08 controllers.py:161-182 | RP-08 | Logging module; emails no longer logged (user id / outcome only) |
| AP-09 controllers.py:5-12 | RP-09 | One error boundary; domain error taxonomy keeps every status and `{"erro": ...}` shape; unexpected errors → generic message; order writes in one transaction |
| AP-10 models.py:171-233 | RP-10 | One JOIN per listing; one aggregate query for the report; one query for health counts |
| AP-10 models.py:133-169 | RP-10 | One `IN` query for the products, batched inserts/updates in one transaction (item-count bound proposed) |
| AP-11 controllers.py:188-220 | RP-11 | Positive integer quantities, existing user, valid product ids, numeric price/stock |
| AP-12 controllers.py:64-96 | RP-12 | One product validation for create and update |
| AP-12 models.py:9-21 | RP-12 | One serializer per entity; one order-assembly function |
| AP-15 models.py:256-262, controllers.py:242-250 | RP-15 | `FAIXAS_DESCONTO`, `StatusPedido`, `CATEGORIAS_VALIDAS`, `APP_VERSION`, name bounds |
| AP-16 controllers.py:14-14 | RP-16 | `obter` vs `buscar`, `produto_id`/`usuario_id` parameters, modules named by layer |
| AP-17 database.py:2-2 | RP-16 | Unused imports gone with the rewrite |
| AP-18 app.py:80-88 | RP-17 | Debug from `APP_DEBUG`, default off (bind address kept at its previous value via `APP_HOST`) |
| AP-18 controllers.py:264-292 | RP-17/RP-08 | Secret value masked; debug/db_path/environment derived from configuration |
| AP-19 requirements.txt:1-1 | RP-18 | flask 3.1.1 → 3.1.3 (same major) |
| AP-19 requirements.txt:2-2 | RP-18 | flask-cors 5.0.1 → 6.0.0 (major). Changelog (Tier C, https://github.com/corydolphin/flask-cors/releases/tag/6.0.0, 2026-10-01): only breaking change is path-specificity ordering; the app uses one global `/*` policy, and the replay's cross-origin GET and preflight entries compare the CORS headers: PASS |
| AP-20 database.py:14-53 | RP-19 | Unique index on `usuarios.email` (created only when existing data has no duplicates); duplicate sign-up → 400. FKs/delete rule/money type proposed |

## Dependency and Deprecated API Verification (refactored manifest)
| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| Refactored application (boot + 54 requests, twice) | Python 3.13 / Flask 3.1.3 | deprecation (warnings forced on) | A (none emitted) | `python -X dev`, `PYTHONWARNINGS=always::DeprecationWarning` | n/a — local | no issue found |
| flask | 3.1.3 | advisory / yanked | B | OSV.dev querybatch; https://pypi.org/pypi/flask/3.1.3/json | 2026-10-01 | no advisories; not yanked |
| flask-cors | 6.0.0 | advisory / yanked | B | OSV.dev querybatch; https://pypi.org/pypi/flask-cors/6.0.0/json | 2026-10-01 | no advisories; not yanked |
| werkzeug, jinja2, itsdangerous, click, blinker, markupsafe | 3.1.9, 3.1.6, 2.2.0, 8.5.0, 1.9.0, 3.0.3 | advisory | B | OSV.dev querybatch | 2026-10-01 | no advisories (installation of 2026-10-01) |

## Re-audit

### Pass 1 — 14 findings (9 proposed-not-applied, 5 unresolved)
Proposed-not-applied (match items recorded under Proposed, Not Applied before the re-audit): the 9 items listed in the Phase 3 block below.

Unresolved:

### [HIGH] Missing Boundary Validation   (AP-11) — origin: missed-in-phase-2 — fixed after re-audit
File: models/pedido.py:60-83 (original: models.py:139-146)
Description: Each order line was checked against the product's stock independently, so repeating a product across lines oversold it (observed against the original: two lines of 5 on a product with stock 8 → 201, stock −2). Fixed: the requested quantity is accumulated per product before the stock check. Security entry `create-pedido-oversell-duplicate-lines` captured against the original (201) and replayed: FIXED (400).

### [LOW] Magic Values   (AP-15) — origin: failed — fixed after re-audit
File: models/database.py:31-47
Description: The DDL still carried `'pendente'` and `'cliente'` as literal defaults, duplicating `StatusPedido.PENDENTE` and `TIPO_PADRAO`. Fixed: the defaults are built from those constants.

### [LOW] Misleading Names and Inconsistent Structure   (AP-16) — origin: failed — fixed after re-audit
File: models/database.py:61-64
Description: `connect` was the only English verb among the module's Portuguese functions. Renamed `conectar`.

### [MEDIUM] Missing Boundary Validation   (AP-11) — origin: missed-in-phase-2 — proposed
File: controllers/pedido_controller.py:34-43 (original: controllers.py:237-255, models.py:275-283)
Description: `PUT /pedidos/<id>/status` answers 200 "Status atualizado" for an order that does not exist; nothing is updated. Answering 404 changes the status a client observes for that request: recorded under Proposed, Not Applied.

### [MEDIUM] Missing Boundary Validation   (AP-11) — origin: missed-in-phase-2 — proposed
File: views/usuario_routes.py:18-27 (original: controllers.py:146-165)
Description: Sign-up accepts any non-empty strings: no email format, no length bounds on name, email or password. The rules are a product decision: recorded under Proposed, Not Applied.

### Pass 2 (after the bounded fix loop and a second full replay) — 11 findings
9 proposed-not-applied + 2 unresolved (both `missed-in-phase-2`, both recorded under Proposed, Not Applied: the status update of a missing order, and the sign-up field rules). No `failed` or `introduced` items remain.

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
code-smells-project/
├── app.py                      composition root (create_app) + entry point
├── requirements.txt            flask==3.1.3, flask-cors==6.0.0
├── .env.example
├── .gitignore
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py
├── models/
│   ├── __init__.py
│   ├── errors.py               domain error taxonomy
│   ├── database.py             connection factory, schema, migrations, seed
│   ├── seed.py
│   ├── senhas.py               PBKDF2 password hashing
│   ├── produto.py
│   ├── usuario.py
│   ├── pedido.py
│   ├── relatorio.py
│   └── sistema.py
├── controllers/
│   ├── __init__.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   └── sistema_controller.py
├── views/
│   ├── __init__.py             registrar_rotas
│   ├── requisicao.py
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   ├── relatorio_routes.py
│   └── sistema_routes.py
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py
│   └── db_session.py
├── adapters/
│   ├── __init__.py
│   └── notificador.py
└── reports/                    audit output (surface.json, baseline.json, replay.json, replay-2.json, audit-*.md)
```

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 45 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    (2 of the PASS improved from 500: create-produto-apostrophe → 201, admin-query-array-body → 400)
    Security entries: 9 FIXED, 0 NOT FIXED
  ○ Findings resolved: 20/29  (9 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 9 proposed-not-applied, 2 unresolved  (re-audit: 11 findings)
    Re-audit passes: 2; fixed after re-audit: 3 (1 of them missed-in-phase-2)
  ✓ Processes: 14 started, 14 stopped through their handles, 0 left running, 0 incidents
    Isolation: container
  ✓ Commands: 0 directory changes, 0 chained commands

## Proposed, Not Applied
### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: views/__init__.py:11-16 (original app.py:11-30)
Reason not applied: the application has no identity model; every current client is anonymous, so any authentication or ownership check would reject all of them (401/403 on every route).
Proposed change: have `/login` issue a session or signed token; enforce ownership on `/usuarios/<id>` and `/pedidos/usuario/<id>`, and an admin role (the existing `tipo` column) on product and order-status mutations. Needs a product decision on principals and policy, and coordinated client changes.

### [CRITICAL] Missing or Bypassable Authorization   (AP-04)
File: views/sistema_routes.py:32-35 (original app.py:47-57)
Reason not applied: protecting or removing `POST /admin/reset-db` changes what every current (anonymous) caller observes.
Proposed change: remove the route from the public application, or gate it behind the admin role plus an explicit environment flag (e.g. `ADMIN_ROUTES_ENABLED=false` by default).

### [CRITICAL] Injection-Prone Dynamic Query or Command Construction   (AP-02)
File: views/sistema_routes.py:37-45, models/sistema.py:29-36 (original app.py:59-78)
Reason not applied: `POST /admin/query` executes arbitrary SQL by design; removing or restricting it removes a route clients can call. (Its crash on a non-object body and its leak of driver errors were fixed: 400 / generic 500.)
Proposed change: delete the endpoint; if an operational query tool is needed, provide it outside the public HTTP surface.

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: app.py:62-72 (original app.py:80-88)
Reason not applied: the debug half is fixed (off by default, opt-in via `APP_DEBUG`); running under a production WSGI server needs a runtime dependency the application does not have today.
Proposed change: add a production server (e.g. a WSGI server package) to requirements and start with it against `app:create_app()`; keep `python app.py` for development only.

### [CRITICAL] Insecure Runtime Configuration   (AP-18)
File: controllers/sistema_controller.py:17-32 (original controllers.py:264-292)
Reason not applied: the secret value is masked (field kept), but `/health` still exposes `db_path`, `debug` and `ambiente` to anonymous callers; removing those fields or restricting the endpoint changes the response shape / who can reach it.
Proposed change: reduce `/health` to `status`/`database`/`counts`, and move configuration details behind an authenticated diagnostics route.

### [CRITICAL] Hardcoded Secrets and Credentials   (AP-01)
File: models/seed.py:21-25 (original database.py:75-83)
Reason not applied: the README documents the example users; making the seed opt-in or changing the admin password would stop the documented accounts from logging in. (Seeded passwords are now stored hashed.)
Proposed change: seed demo users only when `SEED_DEMO_DATA=true`, and read the initial admin credential from the environment.

### [HIGH] Missing Schema-Level Integrity Constraints   (AP-20)
File: models/database.py:41-58 (original database.py:14-53)
Reason not applied: the unique email index was applied; the rest changes observable behaviour or needs a migration decision — a foreign key with a delete rule changes what `DELETE /produtos/<id>` does to orders that reference the product (refuse, cascade or detach); SQLite cannot add foreign keys to existing tables without a rebuild; moving money from REAL to integer cents needs a data migration.
Proposed change: decide the delete rule for products referenced by orders; migrate `pedidos`/`itens_pedido` by table rebuild with `FOREIGN KEY` clauses and `PRAGMA foreign_keys=ON`; store `preco`/`total`/`preco_unitario` as integer cents while serializing the same decimal numbers. Count first: `SELECT i.id FROM itens_pedido i LEFT JOIN produtos p ON p.id = i.produto_id WHERE p.id IS NULL`.

### [HIGH] N+1 and Query-Inside-Loop Access   (AP-10)
File: models/pedido.py:42-56 (original models.py:133-169)
Reason not applied: the round trips are fixed (one `IN` query, batched writes in one transaction); what remains is the unbounded `itens` array, and a maximum number of lines is a product decision that would reject orders clients may send today.
Proposed change: choose a maximum number of lines per order and enforce it in `validar_itens`.

### [MEDIUM] Unbounded Resources and Leaked Handles   (AP-13)
File: models/produto.py:69-71, models/usuario.py:30-32, models/pedido.py:146-150 (original models.py:4-8)
Reason not applied: connections and cursors are now scope-bound (fixed), but adding pagination changes what a client receives from `GET /produtos`, `/usuarios`, `/pedidos` and `/produtos/busca`.
Proposed change: optional `limit`/`offset` query parameters with a bounded default, announced to clients before the default is enforced.

### [MEDIUM] Missing Boundary Validation   (AP-11) — missed-in-phase-2
File: controllers/pedido_controller.py:34-43 (original controllers.py:237-255)
Reason not applied: `PUT /pedidos/<id>/status` for a missing order answers 200 today; answering 404 changes the observed status.
Proposed change: check existence and raise `NotFoundError("Pedido não encontrado")` → 404.

### [MEDIUM] Missing Boundary Validation   (AP-11) — missed-in-phase-2
File: views/usuario_routes.py:18-27 (original controllers.py:146-165)
Reason not applied: email format and length limits are product rules that could reject sign-ups clients send today.
Proposed change: define the email format and the maximum lengths of name, email and password, then validate them at the boundary.

## Verification Coverage
Full — every planned check ran (baseline, full replay twice, destructive entries alone on fresh boots, a late entry captured against the original, two re-audit passes with runtime deprecation detection and live OSV/PyPI lookups). Declared deviations:
  - Boot mechanism: each execution ran as the container's main process (`docker run -d ... python app.py`) rather than `docker exec -d`, so application output was available through `docker logs`; readiness was checked with `proc.py wait` inside the container. Dependencies: original's from requirements.txt into run-1/.deps (mounted read-only into later original runs); refactored's from the refactored requirements.txt into refactored-1/.deps (mounted read-only into later refactored runs; the manifest did not change between them).
  - The baseline ran the original with debug on (its native configuration); the replay ran the refactored application with its new default (debug off). The only observable differences are the error pages, covered by `admin-query-array-body` (PASS, improved from 500).
  - The two `compare --current` runs read only files and ran on the host's Python 3.13.2; they started nothing.
  - Execution Log row 2: `proc start` inside a container refused (no `ps` in the image) and stopped its own child; counted as one start and one stop through its handle.
  - Scratch root: the environment's scratch directory. The snapshot directory was deleted after the re-audit, once `docker ps -a --filter label=refactor-arch.run=20260930-1449` listed no container.
  - Text comparison masks (protocol §5.2) applied to the text bodies compared (`not-found-route`, `preflight-produtos`: empty body).
================================
