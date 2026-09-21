# 04 — Architecture Guidelines

The target architecture for Phase 3, and the rules for getting there without breaking anything.

## 1. The target, stated once

> **Layered separation, with MVC as its concrete instance.**

The invariant is not a folder layout. It is this: **each unit has one reason to change, and
dependencies point in one direction — from the outside in.**

When the application has a request surface — an HTTP service, a CLI, a message consumer — that
invariant is realized as literal MVC: Models, Views/Routes, Controllers. When it does not — a pure
library — there is no View, and forcing one produces an empty directory that satisfies a checklist
and helps nobody. In that case use the nearest mapping (domain / ports / adapters), and **declare
the adaptation and its reason in the report**. Declaring it is not an excuse; it is the deliverable.

| Application type | Concrete shape |
|---|---|
| HTTP service | `models/` · `views/` or `routes/` · `controllers/` · `config/` · `middlewares/` |
| CLI | `models/` (domain) · `commands/` (the View equivalent: argument parsing and output rendering) · `controllers/` (use cases) |
| Queue worker | `models/` · `handlers/` (the View equivalent: subscription and message decoding) · `controllers/` |
| Library | `domain/` · `ports/` (interfaces the domain needs) · `adapters/` (implementations) — declare the adaptation |

## 2. The layers

### Models — the domain

**Owns:** domain entities and value objects; business rules and invariants; persistence for those
entities (repository or data-mapper), including the queries.

**Must never contain:** a framework request or response object; a status code; a route path; a
header; a serialization format chosen for a client; argument parsing; direct reads of process
environment; presentation strings intended for an end user.

**Test:** the model layer must be exercisable with no server running and no argument parser
instantiated.

Where the persistence code lives is a judgement call with two defensible answers. Either keep the
repository inside the model layer (the common MVC reading, and the right default for a project of
modest size), or split it into a separate `repositories/` package that the model layer depends on
through an interface. Pick one, apply it uniformly, and say which in the report. What is **not**
defensible is persistence code inside a controller or a route.

### Views / Routes — the delivery boundary

**Owns:** the mapping between the outside world's protocol and the application's use cases. Route
declaration and registration; HTTP method and path, or command and flag, or topic and routing key;
deserializing input into plain values; serializing a result into the response format; selecting the
status code or exit code; content negotiation; the response envelope.

**Must never contain:** a business rule; a database call; a conditional on a domain value that
decides *what the system does* rather than *how it is presented*.

**Rule of thumb:** a route handler should read as *parse → call one controller method → render*.
If you cannot summarize it in that sentence, logic has leaked in.

This is also the layer whose details are the **public contract** (§6). It is the layer you are least
free to change.

### Controllers — use-case orchestration

**Owns:** one use case per method. Coordinating models, repositories and external adapters;
transaction boundaries; authorization decisions for the use case; translating domain errors into
the application's error taxonomy.

**Must never contain:** SQL or driver calls (delegate to a repository); framework request/response
objects (accept plain values, return plain values or domain objects); rendering or formatting.

**The test that catches a fake controller:** could this controller be called from a second entry
point — a CLI command, a scheduled job, a test — with no web request in sight? If not, it is a route
handler that has been renamed, and the layering is nominal.

### Configuration

One module that reads the environment once, validates that required values are present, applies
defaults for optional ones, and exposes a typed, immutable object. Everything else receives
configuration; nothing else reads the environment.

Rules: no secret literal in the codebase (AP-01); missing required configuration fails loudly at
startup, not lazily at first use; provide a committed example file listing every key with
placeholder values; distinguish per-environment values from constants — a constant does not belong
in configuration at all.

### Error handling

One centralized boundary at the outermost layer: framework error middleware, a top-level handler, or
the equivalent for the application type.

- A small domain error taxonomy owned by the domain layer: not found, invalid input, conflict, not
  authorized, dependency failure.
- One mapping from that taxonomy to protocol responses, in one place.
- Log the full context internally; return a safe message externally. Never a stack trace, a driver
  error or an internal path in a response body.
- Every response carries a correlation identifier so a report can be tied to a log line.
- Handlers do not `try`/`catch` for the purpose of shaping responses; they let errors reach the
  boundary.

### Composition root / entry point

One file, at the outermost layer, that does the wiring and nothing else: load configuration, create
the infrastructure clients, construct repositories, construct controllers with their dependencies,
register routes or commands, register the error boundary, start.

**Nothing else in the codebase constructs its own infrastructure.** No module has side effects at
import time. The composition root is the only place where concrete implementations are named.

## 3. Dependency direction

```
        Views / Routes  ──depends on──▶  Controllers  ──depends on──▶  Models
              │                               │                          │
              └────────── depends on ─────────┴─── Config, Errors ───────┘

    Composition root  ──constructs──▶  all of the above
```

The rule, in one line: **dependencies point inward, toward the domain. The domain depends on
nothing.**

Concrete violations to look for, in any language:

- A model importing the routing module, the request object or the framework's application object.
- A controller importing the router.
- A cycle between layers — usually appearing first as an import placed inside a function to "fix" an
  import error. That local fix is a signal that the direction is wrong, not that the import system
  is.
- A shared `utils` module that everything imports and that imports from several layers. It is not a
  layer; it is a coupling hub. Split it by destination layer.

When the domain needs something the outside provides — sending mail, calling a third party, reading
the clock — invert it: the domain declares the interface (the port), the outer layer implements it
(the adapter), and the composition root connects them.

## 4. Directory structure

A reasonable default for a request-surface application:

```
<target>/
├── src/                      (or the ecosystem's conventional root)
│   ├── config/               configuration loading and validation
│   ├── models/               entities, rules, and their persistence
│   ├── controllers/          one module per use-case group
│   ├── views/  or routes/    route/command/handler declarations
│   ├── middlewares/          cross-cutting: error boundary, auth, logging
│   └── <entry point>         composition root
└── <manifest, existing project files>
```

**Follow the ecosystem's own conventions where they conflict with this sketch.** A Go project does
not use a `src/` directory; a Ruby project has established package layout expectations; some
frameworks dictate where entry points live. The layering is the requirement; the exact folder names
are not. State the layout you chose in the report.

Sizing: one module per domain concept, not one module for all of them (AP-03) and not one module per
function. If a layer directory would hold a single small file, keep the file and skip the ceremony.

## 5. Judging existing layers: real or nominal

A project may arrive already partly layered. Do not assume that means it is layered. Open the files
and test each claimed layer:

| Claimed layer | It is **nominal** if… |
|---|---|
| `models/` | it imports the framework's request object, formats output for a client, or contains route declarations |
| `routes/` or `views/` | it contains driver calls, or branches on domain values to decide behaviour rather than presentation |
| `controllers/` or `services/` | it is a pass-through with no logic while the logic stayed in the handler; or it accepts and returns framework request/response objects; or it issues driver calls directly |
| `utils/` or `helpers/` | its members share no theme — it holds business rules, formatting and I/O side by side |
| `repositories/` | it returns framework-shaped objects, or contains business rules rather than data access |

Two further checks that decide the matter:

1. **The second-caller test.** Could this unit be invoked from a different entry point without
   modification? If not, it belongs to the delivery layer whatever the directory says.
2. **The import-direction test.** Draw the actual import graph between the claimed layers. If any
   inner layer imports an outer one, the layering is decorative.

## 6. The public-contract gate

Phase 3 fixes findings of **all** severities — but any change that alters what a legitimate client
observes is **not applied**. It is recorded under `PROPOSED, NOT APPLIED` with its rationale.

**Counts as a contract change (gated, proposed only):**

- renaming or moving a route, command or exported symbol;
- changing the HTTP method, the command name or the message topic;
- changing the success status code or the CLI exit code;
- changing the response body shape: renaming, removing or restructuring a field;
- changing a field's type, or its serialization format;
- making a previously optional parameter required, or removing an accepted parameter;
- changing pagination, ordering or default filtering semantics that a client may depend on;
- tightening validation so that previously accepted requests are now rejected;
- changing the error response shape.

**Does not count (applied):**

- parameterizing an injectable query;
- moving a secret to configuration;
- eliminating an N+1;
- extracting logic into a layer;
- renaming an internal identifier, file or module not part of the public surface;
- replacing a magic value with a named constant;
- centralizing error handling **while preserving the observable status codes and body shapes**;
- adding a missing authorization check — with one caveat, below;
- deleting dead code;
- replacing a deprecated API with its documented equivalent, when the observable behaviour is the
  same.

**The security caveat.** Adding a missing authorization check (AP-04) changes what an *illegitimate*
client observes, which is the point. It is applied. But if you cannot determine who the legitimate
principals are without guessing, do not invent a policy: apply what you can prove (for example,
scoping a lookup to the authenticated principal, which is unambiguous) and propose the rest. Apply
the same reasoning to tightened validation: reject what is unambiguously invalid; propose rules that
require a product decision.

**Why the gate exists.** "Nothing broke" is only a verifiable claim if the contract was preserved
(see `06-validation-protocol.md`). Deciding on the team's behalf what may break is not an automated
tool's role. Everything safe is fixed; everything risky is proposed with an argument.

## 7. Improving an already-layered target without churn

For a project with real or partly real layers, the goal is improvement, not a rewrite.

**Do:**

- move misplaced code into the layer that owns it, keeping the code itself intact;
- add the layer that is genuinely missing, not the layer the diagram has;
- fix the import direction where it is inverted;
- split a coupling hub (`utils`) by destination layer;
- introduce the composition root and remove import-time side effects;
- centralize error handling and configuration if they are scattered;
- keep existing names that are correct.

**Do not:**

- rename files, modules or symbols that are already accurate, to match a preferred convention;
- move an entire tree to a different root directory for aesthetics;
- introduce an abstraction with exactly one implementation and no second caller in sight;
- add layers the application does not need — a mapper per entity, a service per model, an interface
  per class — in a codebase that does not have the size to pay for them;
- reformat files you did not otherwise change. A diff full of whitespace hides the real change and
  makes review, and any later bisect, much harder.

**The test for every proposed move:** name the anti-pattern finding it resolves. A change that
resolves no finding is churn, and churn costs review time and risk for nothing. Every edit in Phase 3
should be traceable to a finding id.
