# 01 — Project Analysis

Heuristics for Phase 1. Everything here is read-only: Phase 1 writes nothing.

The output of this phase is not decoration. Four of its fields are consumed later:
the **application type** and **public surface** drive validation (§5), the **boot command** drives
the baseline capture (§6), and the **current architecture map** drives the Phase 3 plan (§4).

**Ordering principle — evidence beats declaration.** When two sources disagree, prefer the one closer
to what actually runs: installed metadata > lockfile > manifest range > documentation > file naming.
State which source you used when the answer is non-obvious, and never print a version you did not
read from a file.

---

## 1. Language detection

Do not rely on a single signal. Rank by weight:

| Weight | Signal |
|---|---|
| Strong | A manifest file naming an ecosystem (`package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Gemfile`, `composer.json`, `pom.xml`, `build.gradle*`, `Cargo.toml`, `*.csproj`, `mix.exs`, `pubspec.yaml`) |
| Strong | A lockfile (`*.lock`, `*-lock.json`, `*.lockb`, `*.sum`) — also proves the manifest is actually used |
| Medium | Source-file extension census, weighted by total bytes rather than file count |
| Medium | A shebang or explicit interpreter in entry scripts, `Dockerfile` or `Procfile` |
| Weak | Directory naming conventions |

**Exclude from the census** anything not authored here: dependency directories
(`node_modules`, `vendor`, `.venv`, `venv`, `site-packages`, `target`, `Pods`), build output
(`dist`, `build`, `out`, `.next`, `__pycache__`, `*.min.*`), and anything matched by `.gitignore`.
State the exclusion rule you used in the report — a file count is meaningless without it.

A repository may be **polyglot**. Report the dominant language by authored bytes and name the others.
If a second language carries real logic (not just tooling), analyze it too.

## 2. Framework and version

Find the framework by what the entry point imports and instantiates, not by what the manifest lists.
A dependency that is declared but never imported is itself a finding (AP-17).

Resolve the **exact** version in this order:

1. Installed metadata — the resolved-version field in the lockfile; the installed distribution
   metadata directory; the module path in the dependency graph.
2. A command against the target's own runtime that prints the version. Run it only if the runtime is
   present; never install anything to answer this.
3. The manifest's declared range. If this is all you have, print the range **as a range**
   (`^4.18.0`, `>=3,<4`), not as a resolved version.

If the framework is absent, say `none (plain <language>)` — a framework-free project is a normal
finding, not a detection failure. Micro-frameworks, routers used standalone, and in-house
"frameworks" all count; name what you actually find.

## 3. Dependencies

List **direct** dependencies only — transitive ones belong to the lockfile, not the report.
Separate runtime from development dependencies where the manifest distinguishes them.

Note, without editorializing:

- dependencies declared but never imported anywhere in the source;
- modules imported but not declared in any manifest (an undeclared dependency — it will break a
  clean install, and is worth a MEDIUM finding);
- a manifest with no lockfile, or a lockfile out of sync with the manifest.

## 4. Mapping the current architecture

Describe what **is**, before judging it. Produce, internally, a small table:

| Question | How to answer |
|---|---|
| Where does execution start? | The entry point named by the manifest, `Procfile`, container `CMD`, or the file that starts a server / parses arguments |
| What are the top-level source groupings? | Directory names, plus the actual import graph — they often disagree |
| Which direction do imports flow? | Does the persistence code import the delivery code, or only the reverse? |
| Where does persistence happen? | Files containing driver calls, ORM sessions, connection setup |
| Where do business rules live? | Conditionals on domain values: price, eligibility, state transitions, quantity, permissions |
| Where is configuration read? | Environment reads, config-file loads, module-level constants |
| How are errors handled? | Centralized handler/middleware, or per-call-site `try`/`catch`/`rescue` |

Then classify the layering in one line:

- **None** — one or few files holding delivery, rules and persistence together.
- **Nominal** — the directories exist (`models/`, `services/`, `controllers/`, `routes/`, `utils/`)
  but the contents do not respect them: persistence inside a route handler, HTTP objects inside a
  model, business rules in a `utils` grab-bag, a "service" that is a thin pass-through while the
  logic stayed in the handler.
- **Real** — each layer contains only what belongs to it and the dependency direction holds.

The **nominal** case is the most common and the most misleading. Never infer layering from directory
names; open the files. A `services/` directory whose files import the web request object is not a
service layer. See `04-architecture-guidelines.md` §7 for how to improve a nominal layout without
gratuitous churn.

Also record the **size shape**: largest files by line count, and any file that is a significant
fraction of the whole codebase. A single file holding a large share of the source is a strong
God Module signal (AP-03).

## 5. Application type and public surface

> **Public surface** = the set of observable entry points that the outside world uses.

This is the unifying concept for validation. The algorithm is identical for all application types —
*enumerate the surface → exercise it → record the shape → compare*. Only the adapter changes.

| Type | Surface | Detection signals | What Phase 3 compares |
|---|---|---|---|
| **HTTP service** | Routes: method + path (+ required params) | Route decorators/registrations, a router table, a server bind call, an OpenAPI or `.http`/`.rest` file | Status, content-type, body shape |
| **CLI** | Commands, subcommands and flags | An argument-parser setup, a `bin`/console-script entry, a `main` dispatching on `argv` | Exit code, stdout shape, stderr presence |
| **Library** | The exported public API | Package export map, `__all__`, exported symbols, the public section of the docs | Signatures, return shape |
| **Queue worker / consumer** | Message types consumed | Subscription/consumer registration, a handler map keyed by topic or routing key | Produced messages and observable effects |

Rules for enumerating:

- Enumerate **statically, from the original code**, before any modification.
- Include everything reachable from outside, including routes registered dynamically in a loop or by
  a helper — follow the registration, not just the literal decorators.
- Record, per entry, everything needed to exercise it: method, path template, a sample value for each
  path/query parameter, a minimal valid body, and whether authentication is required.
- Mark entries you cannot exercise safely or deterministically (destructive operations, calls to a
  third-party service, endpoints needing credentials you do not have). They become `UNVERIFIED`, not
  silent omissions.
- A project may be **hybrid** — a service with a CLI for migrations, a library with a demo server.
  Enumerate every surface it has and say so.

Write the inventory to `<target>/reports/` in the format specified by `06-validation-protocol.md` §2.

## 6. Deriving the boot command

The agent boots; the harness never does. Derive the command from the target's own declarations —
never from assumption.

Look, in order:

1. A script entry in the manifest (`start`, `dev`, `serve`, `run`) — the project's own answer.
2. A task runner: `Makefile`, `Taskfile`, `justfile`, `invoke`/`rake`/`mix` tasks.
3. Container or platform declarations: `Dockerfile` `CMD`/`ENTRYPOINT`, `compose` service command,
   `Procfile`.
4. Framework convention for the detected framework, applied to the detected entry point.
5. Direct interpreter invocation of the entry point.
6. The project's own README or run documentation, as a last resort — verify it still matches the code.

Then handle what boot needs:

- **Configuration.** If required environment variables are missing, look for a `.env.example`,
  `.env.sample`, a settings template or the defaults in code. Use placeholder values for the
  capture run and record that you did. Never invent a credential for a real external service.
- **Port.** Record how the port is set: an override the code already reads (flag, environment
  variable, settings key), or a value fixed in source. A fixed port is not a reason to edit the
  original — `06-validation-protocol.md` §1.2 gives the order to follow. Prefer a free, non-default
  port where an override exists, so a developer's already-running instance is not mistaken for
  yours.
- **Runtime environment.** If the target's runtime is present but the dependencies the target
  **declares** are not installed, install exactly those — from the lockfile when there is one, at
  the resolved versions — into an isolated location that is not part of the target: a virtual
  environment or dependency directory inside the snapshot's run copy, or one that `.gitignore`
  already excludes. Record in the report what was installed, where and from which file. This is not
  "adding a dependency": the dependency set is the one the project already declares. **Adding** a
  package the project does not declare — for the harness, for convenience, to make boot work —
  stays forbidden. If the declared dependencies cannot be installed (no network, a resolution
  failure), the baseline is `UNVERIFIED`; declare it.
- **Readiness.** Do not assume the process is ready when it is launched. Poll a cheap surface entry —
  or the process's own readiness/health entry if one exists — until it answers, with a bounded
  timeout. For a CLI or library, readiness is trivially true after the runtime starts.
- **Database.** If the app needs a datastore, find how it is provisioned (a migration command, a seed
  script, an embedded file database, a container). Use the project's own mechanism. If the datastore
  cannot be provisioned, the baseline is `UNVERIFIED` — declare it; do not fabricate a schema.
- **Failure to boot.** If the original application does not boot, that is itself a finding, and the
  baseline is `UNVERIFIED`. Record the error verbatim. Do not repair the original in order to
  capture a baseline — that is already a modification, and it destroys the comparison.

Record the exact boot command, its working directory, environment and port in the Phase 1 output —
Phase 3 replays it twice. Also record whether the working tree has uncommitted changes: the
snapshot copies the tree as found, and the report should say what the audit read.

## 7. Database and schema detection

Identify the engine, then the tables:

| Source | What it gives |
|---|---|
| Migration directory | The authoritative, ordered schema history — best source |
| Schema/DDL file, or an embedded database's introspection | Current shape |
| ORM model classes | Tables plus relationships; watch for an explicit table-name attribute overriding the class name |
| Raw statements in source | Table and column names as actually used — compare against the above; drift is a finding |
| Connection string / driver import / config key | The engine and whether it is embedded, local or remote |

Report table names as they exist, in the project's own language. If the schema is implicit
(document store, no migrations), report the collections or the top-level document shapes and say the
schema is implicit. If there is no datastore at all, say `none detected` — that is an answer, not a
gap.

## 8. Domain inference

Infer the domain from the intersection of three sources: table and column names, route paths or
command names, and the vocabulary of the business rules. One line, concrete, in the project's own
terms. If the sources conflict — routes speak of one thing, the schema of another — report the
conflict rather than averaging it; divergent vocabulary is itself an architectural signal.

## 9. Failure modes of this phase

- **Guessing a version.** Print the range or `undetermined`. A wrong version poisons every downstream
  deprecation check.
- **Counting dependency files.** Always state the exclusion rule alongside the count.
- **Trusting directory names.** Open the files; nominal layering is the default in legacy code.
- **Skipping surface enumeration** because the project "obviously" has routes. The inventory is the
  input to validation; without it Phase 3 has nothing to compare against.
- **Repairing the target during analysis.** Phase 1 writes nothing. Not even a formatting fix.
