# 02 — Anti-Pattern Catalog

Nineteen entries, drawn from Fowler's *Refactoring*, Feathers' *Working Effectively with Legacy
Code*, the SOLID principles and the OWASP Top 10. Nothing here is specific to a project, a framework
or an ecosystem.

**Sweep by entry.** Phase 2 walks this catalog one entry at a time, looking for that entry's signals
across the whole target — source, and the data and scripts that reach the runtime — and records
each entry's outcome in the report's coverage table, hits or none. A file-by-file reading only
catches what stands out in each file.

## How to use this catalog

Each entry gives: a canonical name, a **default severity**, **observable detection signals**,
**escalation / de-escalation** conditions, **impact**, and the matching transformation in
`05-refactoring-playbook.md`.

**Severity follows impact in context, not the category label.** The default is where you start; the
escalation and de-escalation conditions are how you arrive at the severity you actually report. When
you move off the default, say so in the finding's `Description`, in one clause.

| Severity | Definition |
|---|---|
| **CRITICAL** | Architecture or security failures that prevent correct operation, expose sensitive data, or completely destroy separation of concerns. |
| **HIGH** | Strong violations of layering or SOLID that severely impede maintenance and testing. |
| **MEDIUM** | Standardization problems, duplication, moderate performance bottlenecks, missing validation. |
| **LOW** | Readability, naming, magic numbers. |

**Signals are language-agnostic by construction.** Where a signal needs a concrete token, it is given
as a pattern spanning several ecosystems. When you meet an ecosystem not listed, match the *concept*
— "the call that sends a statement to the database driver", "the construct that registers a route" —
rather than looking for the literal token.

**Evidence rule.** A finding exists only if you read the code that produces it and can cite
`file:start-end`. A category that plausibly applies but that you did not observe is not a finding.
Inventing findings is worse than missing them: it destroys the report's credibility wholesale.

**Overlap.** One piece of code can match several entries. Report the one whose *impact* dominates,
and mention the others in `Description` rather than filing near-duplicates on the same lines. A file
that is a God Module (AP-03) containing a hardcoded secret (AP-01) and an injection (AP-02) is three
findings only if the lines differ; they usually do.

### Index

| Id | Name | Default |
|---|---|---|
| AP-01 | Hardcoded Secrets and Credentials | CRITICAL |
| AP-02 | Injection-Prone Dynamic Query or Command Construction | CRITICAL |
| AP-03 | God Module / God Class | CRITICAL |
| AP-04 | Missing or Bypassable Authorization | CRITICAL |
| AP-05 | Business Logic in the Delivery Layer | HIGH |
| AP-06 | Hard-Wired Dependencies / No Composition Root | HIGH |
| AP-07 | Mutable Global State | HIGH |
| AP-08 | Unsafe Handling of Credentials and Sensitive Data | HIGH |
| AP-09 | Swallowed or Uncentralized Error Handling | HIGH |
| AP-10 | N+1 and Query-Inside-Loop Access | MEDIUM |
| AP-11 | Missing Boundary Validation | MEDIUM |
| AP-12 | Duplicated Logic | MEDIUM |
| AP-13 | Unbounded Resources and Leaked Handles | MEDIUM |
| AP-14 | Deprecated or End-of-Life API Usage | MEDIUM (impact-driven) |
| AP-15 | Magic Values | LOW |
| AP-16 | Misleading Names and Inconsistent Structure | LOW |
| AP-17 | Dead Code and Commented-Out Code | LOW |
| AP-18 | Insecure Runtime Configuration | HIGH |
| AP-19 | Known-Vulnerable Dependency | HIGH (impact-driven) |

AP-18 and AP-19 come last because they were added after the first calibration round, not because
they matter less. Their ids are stable; the index is not ordered by severity.

---

## AP-01 — Hardcoded Secrets and Credentials

**Default severity:** CRITICAL · **Transformation:** RP-01

**Detection signals**

- A string literal assigned to, or passed as, an identifier whose name matches
  `(secret|key|token|password|passwd|pwd|credential|api[_-]?key|access[_-]?key|private[_-]?key|dsn|conn(ection)?[_-]?str|auth|bearer|salt|signing)`
  — case-insensitive, in any language — outside an example, fixture or test file.
- **What counts as "example, fixture or test" is decided by where the data ends up, not by the file
  name.** A seed script, a migration, a bootstrap routine or a fixture loaded at startup or by a
  documented setup command writes into the **runtime** datastore: a credential literal there
  creates a real account with a known password in every environment that runs it. It is in scope.
  Only data that reaches nothing but a test run is excluded. Credential literals inside data —
  a row of initial users, an insert statement, a JSON document of default accounts — are found by
  the value's position (a password or token column or field), not by an identifier name.
- A connection URL literal carrying inline credentials: a `scheme://user:password@host` shape for
  any scheme.
- A high-entropy literal (≥20 characters, mixed case and digits, no whitespace) with no obvious
  non-secret purpose; or a literal with a recognizable credential prefix or armored-key header.
- A framework's session/signing/crypto configuration key set to a literal rather than read from the
  environment or a secret store.
- A credential-bearing file committed to version control: `.env`, `*.pem`, `*.key`, a service-account
  JSON, a cloud credentials file — present and *not* ignored.
- A default value that is a real secret: a configuration read whose fallback argument is a working
  credential rather than a placeholder or a hard failure.

**Escalate** — already report at CRITICAL; note as aggravating: the credential reaches a
third-party or production system; the file is committed and the repository is public or widely
shared; the secret is a signing or session key (forgeable tokens, not just leaked access).

**De-escalate to LOW/informational** — the literal is unambiguously a placeholder
(`changeme`, `xxx`, `<your-key>`, all-zeros) and is in an example or template file; or it is a
non-secret identifier that merely matches the name pattern (a public client id, a public endpoint
key). Verify before de-escalating; "it looks fake" is not verification.

**Impact.** Anyone with read access to the repository — or to a stack trace, a log, a container
image layer, a forked clone — holds the credential. Rotation requires a code change and a deploy.
The secret follows every copy of the repository forever, including after it is "removed", because
history retains it.

---

## AP-02 — Injection-Prone Dynamic Query or Command Construction

**Default severity:** CRITICAL · **Transformation:** RP-02

**Detection signals**

- A value that originates from outside the process — request body, query string, path parameter,
  header, cookie, CLI argument, environment, message payload, file content — reaching a driver call
  through string concatenation, interpolation or formatting, rather than through a parameter binding.
  The driver call is whatever sends a statement: `execute` / `query` / `exec` / `raw` / `find` /
  `aggregate` / `Query` / `prepare` with an already-built string.
- The interpolation markers of any language appearing inside a statement string:
  `"..." + var`, `f"...{var}..."`, `` `...${var}...` ``, `%s`-style formatting applied *before* the
  driver call, `#{var}`, `.format(...)`, `sprintf`, string builders.
  **The distinction that matters:** a `?`/`$1`/`:name`/`%s` placeholder passed to the driver
  *together with a separate parameter sequence* is safe; the same-looking marker resolved by the
  language before the call is not. Read which side of the call the substitution happens on.
- An ORM escape hatch (`raw`, `literal`, `text`, `whereRaw`, `find_by_sql`, `exec_query`) that
  receives a string built from input.
- Dynamic identifiers — table, column, sort field, direction — taken from input and concatenated.
  Placeholders cannot bind identifiers, so this requires an allow-list, and its absence is the
  finding.
- Shell or process execution with a concatenated command string, or an API that spawns through a
  shell interpreter, with any input-derived segment.
- Deserialization of untrusted input by a mechanism that can instantiate arbitrary types, or template
  rendering of a template string built from input (server-side template injection).
- Input-derived path segments concatenated into a filesystem path with no normalization and no
  containment check (path traversal).

**Escalate (already CRITICAL; flag as maximum urgency)** — the endpoint is unauthenticated; the
statement is a write or delete; the injection point is in an authentication or authorization path;
the same pattern occurs in many places, indicating a systemic construction habit rather than a slip.

**De-escalate to HIGH/MEDIUM** — the interpolated value is provably not attacker-influenced: a
compile-time constant, or a value fully validated against a closed allow-list immediately before use,
with the validation visible in the same unit. Type-casting alone is not containment for identifiers,
and "it's an internal service" is not containment at all.

**Impact.** Data disclosure, corruption or destruction; authentication bypass; in the process and
shell variants, arbitrary code execution. This is the single highest-leverage class in the catalog:
one occurrence can be terminal for the whole system.

---

## AP-03 — God Module / God Class

**Default severity:** CRITICAL · **Transformation:** RP-03

**Detection signals**

- One module concentrates **three or more** distinct responsibility categories:
  (a) persistence / external I/O, (b) business rules, (c) delivery — routing, request parsing,
  CLI argument handling, message dispatch, (d) presentation / serialization / formatting,
  (e) configuration and wiring.
- A module exceeds roughly 300–400 lines **and** carries two or more of those categories. Line count
  alone is never the finding — a long module doing one thing well is fine.
- A single unit (function, method, class) exceeds roughly 50 lines, or nests conditionals more than
  three deep, or takes more than about five parameters, or returns different shapes down different
  branches.
- One file holds the logic for several unrelated domain concepts.
- A class with many fields whose methods each touch a disjoint subset of them — low cohesion, a
  class that is really several classes sharing a namespace.
- A "utilities", "helpers", "common", "misc" or "manager" module whose members share no theme: the
  shape of a leftover bin, not of an abstraction.
- Very high afferent coupling: nearly every other module imports this one.

**Escalate** — the module also contains credentials (AP-01) or injection (AP-02); it is the single
place every request passes through, making every change a global risk; it has no tests because it
cannot be instantiated without a database and a server.

**De-escalate to HIGH** — the responsibilities are mixed but the module is small and the concepts
are genuinely one (a compact script whose whole purpose is one job). **De-escalate to MEDIUM** — the
module is long but single-responsibility, and the real complaint is size.

**Impact.** Nothing can be tested in isolation, because instantiating any part drags in all of it.
Every change has a blast radius covering the whole file. Concurrent work collides constantly. This is
the pattern that makes every other pattern in this catalog harder to fix.

---

## AP-04 — Missing or Bypassable Authorization

**Default severity:** CRITICAL · **Transformation:** RP-04

**Detection signals**

- A surface entry that reads, mutates or deletes a resource belonging to a principal, with no
  authentication check and no ownership check anywhere on its path.
- A handler that takes an identifier from input and fetches or mutates by it directly, without
  constraining the query by the authenticated principal (insecure direct object reference). The
  observable signal: the lookup's filter uses only the input id.
- Authorization enforced **only** in the delivery layer while the same operation is also reachable
  by another route, a CLI command, a message handler or an exported function — the check is
  bypassable because it is not on the operation, only on one of its doors.
- A role, permission, tenant or "is admin" value taken from the request (body, query, header, cookie)
  and trusted, rather than derived from a verified session or token.
- A token accepted without verifying its signature, issuer, audience or expiry; a token *decoded*
  rather than *verified* — the observable signal is a decode call with verification disabled or with
  no key supplied.
- An authorization check written but never reached: declared after the side effect, inside a branch
  that cannot run, or on a middleware that is registered after the route it should protect.
- A commented-out or feature-flag-disabled guard.

**Escalate** — already CRITICAL; flag as maximum urgency when the unprotected operation is
destructive, escalates privilege, or exposes personal or financial data.

**De-escalate to HIGH** — the surface is genuinely public by design (a read-only public catalog, a
health endpoint) and exposes no principal-scoped data; or the check exists correctly at a single
enforced choke point that every path demonstrably traverses.

**Impact.** Horizontal escalation — any principal reads or modifies another's data by changing one
identifier. Vertical escalation — any caller performs privileged operations. Neither leaves a trace
distinguishable from legitimate use.

---

## AP-05 — Business Logic in the Delivery Layer

**Default severity:** HIGH · **Transformation:** RP-05

**Detection signals**

- A route handler, CLI command function or message handler that contains domain decisions:
  eligibility rules, pricing or fee computation, state-transition rules, quota or limit arithmetic,
  multi-step workflows with branching.
- Persistence calls issued directly inside a handler: the driver, ORM session or repository invoked
  from the same function that parses the request.
- A handler longer than roughly 30 lines that is not simply mapping input to a call and a call to a
  response.
- Framework request/response objects reaching deep into the call stack — a function three levels
  below the handler that still takes a request object, or reads a header, or sets a status code.
  The domain should not know that HTTP exists.
- The same business rule implemented in two handlers, because there was no shared place to put it
  (compounds with AP-12).
- A "service" or "controller" layer that exists but is a pass-through, while the logic stayed in the
  handler — nominal layering (see `01-project-analysis.md` §4).

**Escalate to CRITICAL** — the handler also performs persistence and formatting, making the file a
God Module (AP-03); or the duplicated rule has already diverged between its copies, so the system
behaves differently depending on which door you enter.

**De-escalate to MEDIUM** — the logic in the handler is genuinely delivery-level: input coercion,
content negotiation, pagination parameter parsing, status-code selection. That belongs there.

**Impact.** The rule cannot be tested without a web server or a process runner. It cannot be reused
by a second entry point without copying it. Changing the transport forces rewriting the business
rules. This is the defining violation of layered architecture.

---

## AP-06 — Hard-Wired Dependencies / No Composition Root

**Default severity:** HIGH · **Transformation:** RP-06

**Detection signals**

- A unit constructs its own collaborators internally: opening a connection, instantiating a client,
  reading a configuration value, or calling a module-level singleton, inside the function that also
  holds the logic.
- Import-time side effects: a module that, merely by being imported, connects to a database, reads
  the environment, binds a port, starts a timer or spawns a thread. Observable signal — executable
  statements with external effects at module top level rather than inside a function.
- No single place where the object graph is assembled. Wiring is scattered across whichever module
  happened to need it first.
- A test would require the real database, network or clock to run at all; there is no seam to
  substitute a double. Direct calls to the system clock, the random source or the filesystem inside
  business rules are the common forms.
- Concrete types referenced where an abstraction is needed: the domain layer importing a specific
  driver, HTTP client or ORM.
- Configuration read at the point of use — environment access scattered through handlers and rules
  instead of resolved once and injected.

**Escalate to CRITICAL** — the import-time side effect makes the application unrunnable or
unimportable without live infrastructure, so nothing at all can be tested or even loaded in
isolation.

**De-escalate to MEDIUM** — the hard-wired collaborator is a pure, deterministic, dependency-free
helper. Injecting a pure function is ceremony, not decoupling.

**Impact.** No unit is testable in isolation; the test suite becomes an integration suite or does not
exist. Swapping an implementation means editing every call site. Startup order becomes implicit and
fragile, and failures appear at import time with no useful context.

---

## AP-07 — Mutable Global State

**Default severity:** HIGH · **Transformation:** RP-07

**Detection signals**

- A module-level or static variable that is reassigned or mutated after initialization, from more
  than one place.
- Request- or invocation-scoped data stored globally: the current principal, tenant, locale,
  correlation id or transaction held in a module-level slot and read elsewhere. In a concurrent
  runtime this is a correctness bug, not a style issue.
- An in-memory collection used as the store of record — a module-level dictionary, list, map or
  counter that accumulates across requests.
- A mutable default parameter value, a shared mutable class attribute, or a mutable object exported
  and mutated by importers.
- A cache or connection pool with no lifecycle: never invalidated, never bounded, never closed.
- A monkey-patched or reassigned built-in, library function or prototype, changing behaviour for the
  entire process.
- An identifier counter or sequence maintained in process memory — correct only while exactly one
  process exists.

**Escalate to CRITICAL** — the global state carries security-relevant data (the current principal,
an authorization decision) across concurrent invocations, so one caller can be served under
another's identity.

**De-escalate to MEDIUM/LOW** — the global is genuinely immutable after initialization and is
process-wide by nature: a logger, a frozen configuration object, a constant table. Say so explicitly
rather than passing over it.

**Impact.** Behaviour depends on execution history, so bugs are order-dependent and unreproducible.
Tests contaminate each other and must run serially. The application cannot be scaled to more than one
process without silent data loss.

---

## AP-08 — Unsafe Handling of Credentials and Sensitive Data

**Default severity:** HIGH · **Transformation:** RP-08

Distinct from AP-01: that one is about secrets *the project owns*; this one is about credentials and
personal data *the project is entrusted with*.

**Detection signals**

- A password, token or secret persisted in a reversible form: stored as given, encrypted with a key
  stored alongside, or encoded (base64/hex) and described as if that were protection.
- A password hashed with a fast, general-purpose digest (the MD-family, the SHA-family used
  directly), with or without a salt, instead of a purpose-built password KDF.
- A shared, constant or missing salt; a salt derived from the account identifier.
- Credential comparison with a plain equality operator instead of a constant-time comparison.
- Sensitive values reaching a log, an error message, a stack trace, a metric label or an analytics
  event: the observable signal is a whole request body, header map, configuration object or record
  being logged wholesale.
- A response serializing an entire persistence record, carrying fields the caller should not see —
  password hashes, internal flags, other principals' identifiers. The signal is "serialize the whole
  row" with no explicit field selection.
- Transport without protection where the data warrants it; certificate verification explicitly
  disabled.
- No expiry, revocation or rotation path for issued tokens; session identifiers that never change
  across a privilege transition.

**Escalate to CRITICAL** — passwords or payment-adjacent data are stored recoverably; sensitive
values are written to a log that is shipped off-host; certificate verification is disabled on a path
carrying credentials.

**De-escalate to MEDIUM** — the exposed field is internal but not sensitive (a surrogate key, a
timestamp) and the leak is confined to a local development log.

**Impact.** A single database read compromises every account, and — because credentials are reused —
accounts on other systems too. Logged secrets outlive the incident and spread to wherever logs are
aggregated, usually with much weaker access control than the database.

---

## AP-09 — Swallowed or Uncentralized Error Handling

**Default severity:** HIGH · **Transformation:** RP-09

**Detection signals**

- A catch/rescue block that is empty, that only logs and continues, or that returns a success value
  on the failure path.
- A catch that is over-broad — catching the base exception type or every error — wrapping a large
  block, so unrelated failures are absorbed together.
- The same error-to-response mapping repeated in every handler: the same `try`/`catch` shape,
  status-code selection and message formatting copied across the delivery layer.
- No centralized handler at all: no error middleware, no framework error hook, no top-level boundary.
  Any unhandled failure reaches the caller as a raw stack trace. **Absent code is still behaviour:**
  when the application registers no handler, the framework's default one runs. Observe what it
  returns — run the original from the snapshot and send a request that makes it fail — rather than
  recalling it. If it exposes internals, that is also AP-18.
- A stack trace, SQL fragment, file path or internal exception message returned in a response body —
  this is also an information leak, and compounds with AP-08.
- Errors signalled by return convention — a sentinel value, a null, an `{error: "..."}` object —
  inconsistently with the rest of the codebase, so callers forget to check.
- A failure of a critical operation that leaves the system in a partially applied state: several
  writes with no transaction boundary and no compensation.
- Control flow driven by exceptions for ordinary, expected conditions.

**Escalate to CRITICAL** — a swallowed failure silently discards a persisted write, or an
authentication/authorization failure is caught and treated as success.

**De-escalate to MEDIUM** — the swallow is deliberate, narrow, commented and correct (a best-effort
cleanup on a known-benign exception type). Deliberateness must be visible in the code, not inferred.

**Impact.** Failures become invisible: the system reports success while doing nothing. Diagnosis is
impossible because the original error and its context are gone. Callers cannot distinguish "not
found" from "the database is down", so they retry the wrong things.

---

## AP-10 — N+1 and Query-Inside-Loop Access

**Default severity:** MEDIUM · **Transformation:** RP-10

**Detection signals**

- A driver or ORM call inside a loop body — or inside a function that is itself called from a loop.
  Follow one level of indirection; the pattern is usually hidden behind a helper.
- Iterating a collection of records and, per element, fetching a related record by its foreign key.
- A lazy-loaded relation accessed inside an iteration, including inside a template or serializer
  iterating a collection.
- The same read repeated with different arguments where one set-based query (an `IN` list, a join,
  an aggregate) would answer all of them.
- A remote call — HTTP, RPC, cache, message publish — inside a loop with no batching and no
  concurrency.
- A whole table read into memory to be filtered, counted, summed or sorted in application code, where
  the datastore could do it.
- A write loop with one round trip per element instead of a batch or a transaction.

**Escalate to HIGH** — the loop bound is caller-controlled and unbounded, so a single request can
issue arbitrarily many round trips: that is a denial-of-service surface, not just slowness.
**Escalate to HIGH** also when the loop is on a hot path and the cost is already visibly harmful.

**De-escalate to LOW** — the collection is provably tiny and fixed (a handful of configuration rows
read once at startup), and the call is local and cheap.

**Impact.** Latency grows linearly with data volume, so the system passes every test on a small
dataset and degrades in production. Connection pools exhaust under concurrency, converting a
performance problem into an availability one.

---

## AP-11 — Missing Boundary Validation

**Default severity:** MEDIUM · **Transformation:** RP-11

**Detection signals**

- A surface entry reading an input field and using it directly — as a number, a date, an identifier,
  a filter — with no presence, type, range, format or length check.
- Optional input dereferenced without a null/absence check; the failure mode is a crash on a
  malformed request rather than a clear rejection.
- An unconstrained pagination or limit parameter passed to the datastore.
- Numeric parsing with no failure path, or silent coercion of an unparseable value to a default.
- Validation present on one entry point but not on a second that reaches the same operation.
- Validation implemented *after* the value has already been used, or after a side effect.
- Domain invariants enforced nowhere: a quantity that may be negative, a date range whose end
  precedes its start, a state transition that skips a required intermediate state, a required
  relationship never verified to exist.
- No upper bound on request body, upload or array length.
- Validation logic scattered through the handler as ad-hoc conditionals instead of expressed once at
  the boundary.

**Escalate to HIGH** — the unvalidated value reaches a datastore, a filesystem path or a process
invocation (then also examine AP-02); or the missing invariant permits persistently corrupt domain
state, such as a negative balance or an overlapping reservation.

**De-escalate to LOW** — the input is internal and already constrained upstream by a type system or
a schema that you verified.

**Impact.** Malformed input becomes a server error rather than a clear client error, so operators
cannot distinguish attacks from bugs. Invalid domain state persists and spreads: the corruption is
discovered far from where it entered, sometimes only in reports months later.

---

## AP-12 — Duplicated Logic

**Default severity:** MEDIUM · **Transformation:** RP-12

**Detection signals**

- Two or more blocks, of roughly ten lines or more, that are structurally identical and differ only
  in literals or identifier names.
- The same business rule — a threshold, a formula, an eligibility test, a state machine — expressed
  in more than one place.
- The same validation, the same error-to-response mapping or the same serialization shape repeated
  per handler.
- A mapping between two representations (record to response, input to domain object) written by hand
  in several places with slightly different field sets.
- Copy-and-modify lineage: near-identical units whose names differ by a suffix or a domain word,
  where one copy has a fix the other lacks. **Divergence is the aggravating signal** — identical
  copies are a maintenance cost, diverged copies are already a defect.
- The same constant literal repeated across files (compounds with AP-15).
- A condition repeated in many call sites that should be one guard at a choke point.

**Escalate to HIGH** — the copies have already diverged in behaviour, so the system's answer depends
on which path the caller took; or the duplicated rule is security-relevant, so a fix applied to one
copy leaves the other exploitable.

**De-escalate to LOW** — the similarity is incidental: two blocks that look alike but answer to
different reasons for change. Unifying them would couple things that should move independently.
Prefer duplication to the wrong abstraction, and say so in the finding.

**Impact.** Every change must be made *n* times, and the *n*-th is eventually forgotten. The
forgotten one becomes a latent defect that surfaces only through the path nobody tests.

---

## AP-13 — Unbounded Resources and Leaked Handles

**Default severity:** MEDIUM · **Transformation:** RP-13

**Detection signals**

- A resource acquired and released by explicit paired calls, with a return, a branch or an exception
  able to run between them — instead of a scope-bound construct (`with`, `using`, `defer`,
  try-with-resources, block form, `finally`).
- A connection, file, socket, cursor, temporary file or lock with no visible release on the failure
  path.
- A connection opened per call where a pool exists, or a pool with no size bound.
- An outbound network call with no timeout configured — the default in most clients is no timeout at
  all, so absence is the signal.
- No retry policy, or a retry with no bound and no backoff.
- An unbounded read: a whole table, file or stream loaded into memory with no pagination, no limit
  and no streaming, where size grows with usage.
- An unbounded in-memory accumulator, cache or queue — no eviction, no maximum.
- A background task, thread, timer or subscription started with no shutdown path.
- Recursion with no depth bound over caller-influenced data.

**Escalate to HIGH** — the unbounded quantity is controlled by the caller, making it a
denial-of-service vector; or handle exhaustion is already observable, turning the defect into an
availability problem.

**De-escalate to LOW** — the resource is short-lived within a one-shot process that exits
immediately, where the runtime's own teardown is a sufficient guarantee.

**Impact.** The system runs correctly under test and degrades under sustained load, which is the
hardest failure class to attribute. A missing timeout turns one slow dependency into a full outage:
every worker blocks on it and the service stops answering unrelated traffic.

---

## AP-14 — Deprecated or End-of-Life API Usage

**Default severity:** MEDIUM, **impact-driven** (see the severity rule below) · **Transformation:** RP-14

> **Founding rule of this entry.**
>
> The skill may know **where to ask**. It may never know **the answer**.
>
> Your own prior knowledge is a *hypothesis generator, never evidence*. You may decide to **check**
> whether something is deprecated; you may not **report** that it is. Every finding in this category
> cites a **source and the date of the lookup**, or it is not reported at all.

A registry endpoint is stable infrastructure and can be written down. "Package X is deprecated" is a
perishable fact and can only come from a live lookup. This section therefore versions the **adapter
table** — where to ask — and never the answers.

### Layer 1 — local evidence, offline, with detectors forced on

Runtimes **hide** deprecation warnings by default. Python suppresses `DeprecationWarning` outside
`__main__`; Node keeps pending deprecations off. A clean run with the detectors off is not
information. Turn them on before concluding anything:

```bash
# Python target
PYTHONWARNINGS=always::DeprecationWarning python -X dev <boot command>

# Node target
node --pending-deprecation --trace-deprecation <boot entry>
```

For other ecosystems, use the equivalent: the compiler's deprecation diagnostics raised to warnings
or errors, the build tool's deprecation report, the linter rule set that flags deprecated members.
Name the mechanism you used in the finding.

Side benefit that matters for the deliverable: a forced warning arrives with a **stack trace naming
file and line** — exactly the `File: <path>:<line>` the report requires. The evidence arrives
pre-formatted.

Other local, ecosystem-agnostic signals:

- a dependency flagged as deprecated in the manifest, lockfile or installed metadata;
- a package resolved to a version the manifest itself marks as unsupported;
- structurally superseded constructs: a callback-based API where the ecosystem has moved to its
  async primitive; a blocking synchronous call where a non-blocking one exists; a hand-rolled
  implementation of something the runtime now provides natively.

Local evidence works with `--offline`. Layer 1 always runs.

### Layer 2 — live lookup, at run time, never a stored list

Run these at execution time and stamp every result with the date. Skip them under `--offline` and
declare the skip.

| Source | Query | Covers |
|---|---|---|
| **OSV.dev** | `POST https://api.osv.dev/v1/query` with `{"package": {"name": "<pkg>", "ecosystem": "<npm\|PyPI\|Go\|crates.io\|Maven\|RubyGems\|Packagist\|NuGet>"}, "version": "<resolved version>"}` | Security advisories for the exact resolved version — reported under **AP-19**, which shares this entry's adapters and evidence rules. **One API across ecosystems — agnostic by design.** |
| Ecosystem registry | `npm view <pkg>@<ver> deprecated`; `https://pypi.org/pypi/<pkg>/json` → per-release `yanked` and `yanked_reason`, plus `info.yanked`; the equivalent metadata endpoint for other registries | Whether the exact pinned version is deprecated or withdrawn |
| Native tooling | `npm outdated`, `pip list --outdated`, or the ecosystem's equivalent | Distance from the current release; end-of-life major lines |
| Official documentation or changelog **for the version in use** | Fetch, last resort | *Language-level* and *framework-level* deprecations, which no registry reports |

Rules for Layer 2:

- Query the **resolved** version from the lockfile or installed metadata, never the manifest range.
- Use the ecosystem identifier the API expects; a wrong identifier returns an empty result that looks
  like "no advisories". An empty result from a malformed query is `UNVERIFIED`, not a clean bill.
- If the network is unavailable, the lookup fails or the endpoint answers unexpectedly, record
  `UNVERIFIED` for that package and carry it into the report's degraded-verification block. Never
  fall back to memory.

### Evidence grading — decides whether a finding may be reported

| Tier | Evidence | Reportable? |
|---|---|---|
| **A — observed** | A warning emitted by the runtime or compiler during an actual run, with a stack trace | Yes — with file and line |
| **B — declared** | Registry or advisory metadata for the exact pinned version | Yes — citing source + date of lookup |
| **C — documented** | Official documentation or changelog for the version in use | Yes — citing URL + date of lookup |
| **D — suspected** | The model's own prior knowledge | **No. Never reportable.** Promote to A, B or C by verification, or discard. |

A Tier-D suspicion is a legitimate reason to *run a check*. It is never a legitimate line in a
report. If verification is impossible — no network and no local signal — the correct output is the
degraded-verification note, not a finding.

**Severity follows impact.** An unsupported major line with no upgrade path is HIGH. A
soft-deprecated call with a drop-in successor and no risk is LOW. Default MEDIUM only when the
impact is genuinely unremarkable. A package that is deprecated **and** has a security advisory for
the resolved version is reported once, as AP-19, with the deprecation named in its description —
the advisory is the dominant impact (see "Overlap" above).

**Every finding in this category must state the modern equivalent** — the specific successor API,
the maintained replacement package, or the migration path named by the upstream source you cited.
"Stop using it" without a named replacement is not a recommendation.

**Impact.** A deprecated API is removed on a schedule the project does not control: the failure
arrives at the next routine upgrade, and by then the migration is urgent instead of planned. An
unmaintained dependency receives no security fix, so today's advisory is permanent.

---

## AP-15 — Magic Values

**Default severity:** LOW · **Transformation:** RP-15

**Detection signals**

- An unexplained numeric literal in a decision or a computation: a threshold, a limit, a multiplier,
  a rate, a timeout, a retry count, a size. `0`, `1` and `-1` in trivially obvious roles are not
  findings.
- A bare duration or size with no unit in the surrounding name, so the reader cannot tell seconds
  from milliseconds, or bytes from kilobytes.
- A string literal used as an enumerated value — a status, a role, a type, a state — repeated across
  files with no single definition, and no protection against a typo silently creating a new value.
- A literal repeated in several places, so a change requires finding all of them (compounds with
  AP-12).
- A numeric code compared directly instead of through a named constant.
- An index or offset into a tuple, array or fixed-width record with no name explaining the position.
- An environment-specific literal — a URL, a hostname, a path, a port — inline in logic rather than
  in configuration (if it is a credential, that is AP-01 at CRITICAL instead).

**Escalate to MEDIUM** — the same magic value appears in several modules that must agree; or it
encodes a business rule whose owner is not the engineer (a tax rate, a legal retention period, a
regulatory limit) and which will certainly change without a code-driven reason.

**De-escalate to informational** — the literal is local, used once, and its meaning is unmistakable
from the surrounding line.

**Impact.** The reader cannot tell what the number means or whether changing it is safe, so nobody
changes it. Agreement between copies is maintained by memory, and memory fails silently.

---

## AP-16 — Misleading Names and Inconsistent Structure

**Default severity:** LOW · **Transformation:** RP-16

**Detection signals**

- A name that contradicts behaviour: a `get`/`find`/`is` that mutates or performs I/O, a `validate`
  that also persists, a boolean whose name is negated relative to its meaning.
- Non-descriptive identifiers outside a two-or-three-line scope: single letters, `data`, `info`,
  `temp`, `obj`, `res`, `val`, `x1`, `arr`, `stuff`, `thing`.
- Several names for one concept within the same codebase, or one name meaning two things in
  different modules.
- A unit whose name describes *how* rather than *what*, tying the name to an implementation that will
  change.
- Mixed naming conventions within one codebase or one file — several casing styles for the same kind
  of entity, several pluralization rules for the same kind of collection.
- Mixed human languages in identifiers, or identifiers in one language and comments in another, when
  it is not a deliberate, consistent choice.
- Inconsistent file and directory naming, or files placed where their name says they do not belong.
- A comment that contradicts the code beneath it — one of the two is wrong, and the comment is not
  executed, so it is usually the stale one.
- Boolean parameters at call sites that make the call unreadable without opening the definition.

**Escalate to MEDIUM** — the misleading name has demonstrably caused a defect, or it concerns a
security-relevant unit where a wrong assumption is dangerous (a name suggesting a value is sanitized,
validated or authorized when it is not).

**De-escalate to informational** — short names in a genuinely tiny scope where the convention is
idiomatic for the language, such as a loop index or a receiver.

**Impact.** Names are the primary documentation of a codebase, and a wrong name is worse than no
name: it is confidently misleading. Readers act on it, and the cost is paid by everyone who arrives
later.

---

## AP-17 — Dead Code and Commented-Out Code

**Default severity:** LOW · **Transformation:** RP-16

**Detection signals**

- A block of code that is commented out rather than deleted, especially with a date or an initial.
- An unreachable branch: a condition that cannot be true, code after an unconditional return or
  raise, a duplicated condition in a chain where the second can never be reached.
- A defined but never referenced unit — function, class, constant, module — with no export and no
  dynamic-dispatch path to it. Rule out reflection, dynamic import, plugin registration and
  string-keyed dispatch before concluding; if you cannot rule them out, say so and lower confidence.
- An import that is never used; a declared dependency never imported anywhere.
- A parameter that is accepted and never read; a computed value that is never used.
- A feature flag that has been constant for a long time, with the dead side still present.
- An endpoint, command or export not reachable from any registration.
- A duplicated older version of a file kept alongside the new one — `*_old`, `*_backup`, `*.bak`,
  `*_v2`, `*.orig`, or a parallel directory holding a previous implementation. **Version control is
  the backup; a second copy in the tree is dead code, and the fact that it is "kept just in case" is
  the finding, not a defence.**

**Escalate to MEDIUM** — the dead code is a second, stale implementation of live behaviour, so a
reader may modify the wrong one; or the commented-out block contains a credential or a hint about
one (then also AP-01).

**De-escalate to informational** — the code is genuinely reachable through a dynamic mechanism you
identified, or it is a documented, intentionally staged extension point.

**Impact.** Dead code is read, searched, reviewed, migrated and maintained at full cost while
delivering nothing. It misleads readers about what the system does, and it hides real code in the
noise.

---

## AP-18 — Insecure Runtime Configuration

**Default severity:** HIGH · **Transformation:** RP-17 · **Source:** OWASP Top 10, *Security
Misconfiguration*

Distinct from AP-01: that one is a secret in the code; this one is a **setting** that makes the
running application less safe than its code — usually a development convenience that reaches the
path production runs.

**Detection signals**

- A framework's debug, development or reload mode switched on by a literal, on the code path the
  application is started with — not gated by configuration or an environment check. The
  observable signal is a debug flag set to a true value in the entry point, the application
  factory or a settings module that production loads.
- The development server of a framework used as the production server: the entry point starts the
  framework's built-in server with no production server declared anywhere (no process file, no
  container command, no documented alternative).
- A listener bound to every interface (the "any" address of the platform) **in combination with**
  debug mode or with a diagnostic endpoint. Binding to every interface is normal in containers; the
  combination is what exposes the debugger to the network.
- Error output that exposes internals in the mode the application runs in: stack traces, exception
  messages, driver errors, file paths or configuration in response bodies — whether from the
  application's own handler or from the framework's default one when none is registered (observe
  it; see AP-09).
- A cross-origin policy that trusts every origin **and** allows credentials, or that reflects the
  request's `Origin` back unconditionally; a wildcard policy applied to the whole application where
  state-changing routes rely on cookies.
- Diagnostic, administrative or introspection surfaces reachable without restriction: a debug
  console, a profiler, an admin route, a metrics endpoint exposing configuration, directory listing.
- Protective defaults switched off: forgery protection disabled for cookie-authenticated forms,
  verbose query or request logging enabled unconditionally, secure-cookie flags turned off.

**Escalate to CRITICAL** — the debug mode offers an interactive console or code evaluation and the
listener is reachable from outside the host: that is remote code execution by design; or the error
output exposes credentials or configuration.

**De-escalate to MEDIUM** — the setting is confined to an entry point that is demonstrably
development-only (a separate script the production start path never runs), and the report shows how
you established that. **De-escalate to LOW** — the permissive cross-origin policy carries no
credentials and fronts only public, read-only data.

**Impact.** The application is less safe than its code: a correct program is shipped with the door
its developers used for convenience left open. Debug consoles give an attacker code execution;
verbose errors map the internals for the next attack; a permissive cross-origin policy lets any
site act with the user's session.

---

## AP-19 — Known-Vulnerable Dependency

**Default severity:** HIGH, **impact-driven** · **Transformation:** RP-18 · **Source:** OWASP Top
10, *Vulnerable and Outdated Components*

Distinct from AP-14: a deprecated API is one that will be removed; a vulnerable dependency is one
with a **published security advisory for the exact version in use**. The two often co-occur and
are then reported once, here (see AP-14, "Severity follows impact").

**This entry inherits AP-14's founding rule and evidence grading in full.** The model's prior
knowledge that a version "has a CVE" is Tier D and never reportable. Every finding cites the
advisory identifier, the source queried and the date of the lookup.

**Detection signals**

- An advisory returned by OSV.dev (or the ecosystem's own audit tool — `npm audit`, `pip-audit`
  when present in the environment, `bundle audit`, `govulncheck`, the equivalent) for a **direct**
  dependency at its **resolved** version, from the lockfile or installed metadata.
- The same, for a **transitive** dependency: report it against the direct dependency that pulls it
  in, because that is what the project can change.
- A manifest range that would resolve to a fixed version, while the lockfile pins a vulnerable
  one: the fix is a lockfile update, and the finding says so.
- No lockfile at all, so the version installed is whatever resolved that day: the audit cannot be
  exact. Report it (AP-19 at MEDIUM) and mark the advisory check `UNVERIFIED` for those packages.

**Severity follows the advisory and the reachability.**

- **Escalate to CRITICAL** — the advisory is rated critical or high by its source **and** the
  vulnerable code path is reachable from the application's surface: the vulnerable function is
  called, the vulnerable feature is enabled, the input reaches it. Say how you established
  reachability.
- **HIGH** (default) — a high or critical advisory whose reachability you could not establish
  either way.
- **De-escalate to MEDIUM** — the advisory is moderate; or the vulnerable feature is demonstrably
  unused (the affected module is never imported, the affected option is never enabled). **LOW** —
  the package only runs at install or build time, never at run time, and the advisory does not
  concern that phase.

**Every finding names the fixed version** from the advisory, and the upgrade path: within the same
major version, or across a major — which decides whether Phase 3 may apply it
(`04-architecture-guidelines.md` §6, dependency upgrades).

If the lookup cannot run (`--offline`, no network, an unexpected response), this entry is
`UNVERIFIED` for every package and goes to the degraded-verification block. Never fall back to
memory.

**Impact.** The vulnerability is public, documented and often already weaponized: attackers read
the same advisories, and scan for the versions they name. Unlike a flaw in the project's own code,
this one is found without reading the project at all.
