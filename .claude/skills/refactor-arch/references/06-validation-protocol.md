# 06 — Validation Protocol

**This document is normative.** `scripts/probe.py` and `scripts/probe.mjs` are reference
implementations of it, not the definition. For any ecosystem without a shipped implementation,
generate one from this document — the protocol does not change with the language.

## 0. Why baseline-then-replay

"The application still works" is not verifiable after the fact. An entry point that returned a
server error before the refactoring returns the same error after it, and a naive check records that
as success. The only way to know whether *you* broke something is to record what the system did
**before** you touched it, and compare.

This is a characterization test in the sense of Feathers' *Working Effectively with Legacy Code*: it
does not assert that the behaviour is correct, only that it is **unchanged**. That is exactly the
claim Phase 3 needs to make, and it is what allows the refactoring to be aggressive rather than
timid: with the surface pinned, a large internal restructuring is verifiable in a way that a careful
small one, unverified, is not.

```
enumerate surface  →  capture baseline  →  REFACTOR  →  replay  →  compare
    (Phase 1)          (Phase 3a)                       (Phase 3c)
```

## 1. Division of labour — non-negotiable

| Responsibility | Owner | Why |
|---|---|---|
| Derive the boot command | **Agent** | Stack-specific; it is what Phase 1 deduced |
| Start the process and wait for readiness | **Agent** | Stack-specific |
| Provision configuration, ports, datastore | **Agent** | Project-specific |
| Exercise the surface, record the shape, compare | **Harness** (`probe`) | Protocol-pure; identical in every language |
| Own the process's lifetime: start the derived command, record it, stop exactly it | **Container runtime** or **`proc`** (§1.3) | Process ownership is OS-specific and error-prone by hand; it is not stack-specific |

**The harness never boots the application.** A harness that knew how to start a Flask app, a Node
server, a Go binary and a Rails app would be a collection of stack-specific special cases —
precisely the coupling this skill exists to avoid. Booting is stack-specific; probing is not.

**Deciding what to run is not the same as owning its lifetime.** The agent derives the boot
command (Phase 1) — that knowledge is stack-specific and stays with the agent. Starting that
command, remembering exactly which process it became, and stopping exactly that process is the
same job for every stack, and it is the job an agent gets wrong under pressure. It belongs to a
container runtime or to `proc` (§1.3), never to a hand-typed kill command.

**The harness runs on the target's own runtime.** If you could boot the application, you have a
runtime in which you can run a script. A Python target gets the Python harness (standard library
only); a Node target gets the Node harness (built-ins only). The additional dependency is zero **by
construction**, not by luck. Never install a package in order to validate — doing so modifies the
target's dependency set, which is itself a change you would then have to validate.

That rule is about **adding** a dependency. Installing the dependencies the target **already
declares**, so that it can boot at all, is a different act: see `01-project-analysis.md` §6
("Runtime environment").

### 1.1 Where the original runs — the pristine snapshot

The original application is never run inside `<target>`. Running it writes runtime artifacts — a
file database, caches, logs, compiled bytecode — and before the Phase 2 gate no file outside
`<target>/reports/` may be created. After the gate, those artifacts would contaminate the tree being
refactored.

At the start of Phase 2, before anything executes, copy the target to a **pristine snapshot**
outside it — never inside `<target>` and never inside `reports/` — in a **scratch root** chosen in
this order:

1. **The scratch directory the agent's environment designates**, if it designates one (a
   session scratch or work directory the agent may read and write without asking). It is outside
   every project by construction, and commands that touch it need no approval.
2. Otherwise, a directory **inside the working directories the agent is allowed to use, but
   outside `<target>`** — `<parent of target>/.refactor-arch-work/` when the target is a
   subdirectory of an allowed directory. Say in the report that it must be deleted (it is, at the
   end of the run) and never committed.
3. Otherwise, the system temporary directory — **declared** in the report: in an environment that
   restricts reads outside the working directories, every command that touches it will ask the
   user for approval.

Resolve the scratch root **once**, print its absolute path, and from then on write it literally
in every command (§1.4). Record which of the three it was under `## Verification Coverage`.

```
<scratch root>/refactor-arch-<target-name>-<YYYYMMDD-HHMM>/
├── pristine/         exact copy of <target> as found — never executed, never modified
├── run-<n>/          a fresh copy of pristine/, made for each execution of the original
├── refactored-<n>/   a fresh copy of <target> after refactoring, for each execution of it
└── proc/             proc state files and logs (host mode, §1.3)
```

- Copy the working tree as it is, uncommitted changes included: the snapshot is what the audit read.
  Leave out the VCS directory. Make **every** copy — `pristine/`, each `run-<n>/`, each
  `refactored-<n>/` — with `proc copy` (§1.4), one literal command each:
  `<runtime> proc copy --from <dir> --to <new dir>`. It leaves VCS directories out, refuses an
  existing destination, and behaves the same on every OS.
- **Dependency directories are never copied.** Phase 1 identifies the directories where the
  ecosystem installs dependencies inside the tree (a virtual environment, a vendored package
  directory, build output); pass each one to every `proc copy` as `--exclude <name>`, and install
  the declared dependencies inside the copy that runs (below, and §1 above). A copied dependency
  directory carries whatever happened to be installed on this machine, not what the manifest
  declares, and it can be thousands of files. Name the excluded directories in the report.
- Every execution of the **original** — the Phase 2 deprecation run, the Phase 3a baseline, a late
  capture (§4.3) — happens in a new `run-<n>/` copy. Each starts from the same state, which makes
  the runs comparable with each other.
- The **refactored** application also runs from a copy: `refactored-<n>/`, made from `<target>`
  just before each execution of it (the replay, the re-audit's runtime checks). **Nothing ever
  executes inside `<target>`**, so a file database, bytecode caches or build output never land in
  the tree being delivered. Leave out the VCS directory, as for the snapshot.
- Dependencies are installed **inside the copy that runs** (or inside its container, §1.3): the
  original's from its manifest, the refactored application's from the **refactored** manifest,
  which may pin different versions. The report names where each environment lived.
- Warnings and stack traces from a run copy name paths inside the copy. Translate them to paths
  relative to `<target>` before they reach the report.
- Delete the snapshot directory **after the re-audit (Phase 3d)** — the re-audit still needs a
  runtime — and say so. If Phase 3 does not run, delete it at the end of Phase 2. Before deleting,
  confirm that no process or container of this run is still alive (§1.3).

This rule keeps the Phase 2 write restriction absolute rather than full of exceptions, and it gives
every execution of the original the same starting state.

### 1.2 Ports

**In container mode (§1.3) there is nothing to choose:** each container has its own network
namespace, so the application listens on its native port with its native configuration, and the
probe runs inside the same container. Two containers never collide.

In host mode, choose the port in this order, and never edit the original's source to change it:

1. The framework's or the application's own override — a CLI flag, an environment variable, a
   settings key the code already reads. The port the baseline used is the port the replay uses.
2. The application's native port, with baseline and replay run **one after the other**, never at
   the same time. `proc start` refuses a port that already answers; it never frees one.
3. A launcher **outside the tree** (inside the run copy's parent, never in `<target>`) that imports
   the application's entry object and binds it to a chosen port. It is tooling, not a change to the
   target, and it is deleted with the snapshot. **It exists only when the entry point exposes an
   application object to import.** An entry point that builds and starts its server as a side
   effect of being loaded has none; skip this option rather than editing the entry point.

**An override is only neutral if it changes nothing but the port.** A framework's run command
often carries its own defaults — debug mode, reloader, bind address — that differ from the
entry point's. Before relying on one, compare what it changes. If it changes anything besides the
port, record the difference in the report, and gather any evidence that depends on that setting
(a debug console, a verbose error page — catalog AP-18) from an execution at the **native**
configuration, not from the overridden one. Otherwise the audit observes the override, not the
application.

If none of the three works, the baseline is `UNVERIFIED` — declare it. Do not patch the original.

### 1.3 Execution modes and process ownership

Every execution of the original or of the refactored application is a process this skill starts
on someone's machine. **The skill owns exactly the processes it starts, and nothing else.** An
action that reaches a process the skill did not start — stopping it, signalling it, freeing its
port — is an incident, whatever the intent.

Detect the mode in Phase 1 (a read-only question: does a container runtime answer, and can the
image be obtained?), print it as `Isolation:`, and keep it for the whole run. Record it in the
report.

**Container mode — preferred.** Use it whenever a container runtime answers (`docker version`,
`podman version`).

- Image: the runtime's **official** image at the version Phase 1 detected. An ecosystem with no
  official image, or an image that cannot be obtained (no network, `--offline` with no local
  copy), means host mode.
- Mount the run copy (or `refactored-<n>/`) read-write as the working directory, the skill's
  `scripts/` read-only, and `<target>/reports/` read-write as the probe's input and output
  directory (the inventory and the captures live there; §2, §3). Every mount is written with
  literal absolute host paths (§1.4) — never `$(pwd)` or `${PWD}`. On a POSIX host, run as the
  invoking user's uid and gid, so the files the application creates can be deleted with the
  snapshot: read them once (`id -u`, `id -g`) and pass the numbers literally (`--user 1000:1000`),
  never `$(id -u)`.
- Name every container `refactor-arch-<target-name>-<run-id>-<n>` and label it
  `refactor-arch.run=<run-id>`. Start it detached; install the declared dependencies and boot
  the derived command inside it.
- **Run the probe inside the same container** (`exec`), against the native port on the loopback
  address. Nothing is published to the host, and the bind address never has to change.
- Stop it by removing **that exact name**. Never remove containers by filter, label or pattern,
  and never touch a container this run did not create.
- At the end: list the containers carrying this run's label. The list must be empty.

**Host mode — declared as reduced isolation.** Record `Isolation: reduced (host)` and why. Every
start and stop goes through `proc` (`scripts/proc.py`, `scripts/proc.mjs`, or one generated from
§7), with its state files under the snapshot's `proc/` directory:

```
<runtime> proc start  --state <snapshot>/proc/<name>.json --port <n> --cwd <run copy>
                      [--env KEY=VALUE ...] [--timeout <s>] -- <boot argv>
<runtime> proc stop   --state <snapshot>/proc/<name>.json
<runtime> proc status --state <snapshot>/proc/<name>.json
<runtime> proc copy   --from <dir> --to <new dir> [--exclude <name> ...]
```

Every `<...>` above is written as a literal absolute path in the actual command (§1.4).

`proc` starts the argv in a new process group, records the PID and the OS start time, waits for
the port, and stops **only the recorded tree** — after checking that the PID still belongs to the
process it started. It refuses a busy port instead of freeing it. Its exit codes are part of the
evidence: `3` (port busy — choose another), `5` (exited before ready — the log tail is the
finding), `6` (the PID now belongs to someone else — it refused, and so must you), `7` (the port
still answers after stop — something else holds it; investigate, do not kill).

**Forbidden in both modes:**

- stopping anything by name, image or pattern — `pkill`, `killall`, `taskkill /IM`,
  `Stop-Process -Name`, `docker rm $(docker ps -q)`, and their equivalents;
- stopping a process or container this run did not start, including the one holding a port you
  wanted;
- starting the application any other way than through the container runtime or `proc`.

If `proc` cannot stop something, report it and leave it running. A process left running is a
nuisance the user can resolve; a stranger's process killed is damage nobody can undo.

**The execution log.** Every start and stop — its phase, mode, handle (container name, or PID
and state file), command and result — is a row of the report's `## Execution Log`
(`03-report-template.md`). A process action that is not in the log is an incident and goes into
`## Verification Coverage`, stated plainly.

### 1.4 Commands a reviewer can read — literal, one at a time

Every command this skill runs is shown to a person, or to a permission layer acting for them,
before it runs. That check reads the command **as text**: it can tell which paths a literal
command touches, but not what `$SNAP/run-2`, `$env:TEMP`, `%TEMP%` or `$(mktemp -d)` will become
at run time. A command it cannot read is a command it has to ask about. A run that starts and
stops the application a dozen times, each through a variable, turns into a dozen interruptions —
and a person who approves a dozen opaque commands in a row has stopped reading them.

So, in every command — copies, `proc`, the container runtime, the probe, deletions:

- **Resolve each path once, then write it literally.** Find the scratch root (§1.1), print its
  absolute path, and paste that path into every later command. Never write `$VAR`, `${VAR}`,
  `$env:VAR`, `%VAR%`, `$(...)`, backticks, or `~`; never assign a shell variable to reuse later.
  Shell state does not survive between commands anyway.
- **Pass the application's environment as arguments**, never through the shell:
  `proc start --env KEY=VALUE`, or `-e KEY=VALUE` on the container runtime. No `export`, no
  `$env:KEY = ...`, no `KEY=VALUE cmd` prefix.
- **One command per invocation.** No `cd <dir> && ...` chains, no loops, no pipelines that build
  paths. Give the working directory as an argument instead: `proc start --cwd`, the container
  runtime's `-w`, an absolute path to the script.
- **Copy with `proc copy`**, never with a hand-written copy-then-delete sequence.
- **Read and search files with the agent's own file tools**, not with shell commands. They
  need no shell, so there is nothing to analyse.
- **Inside a container, pass an argv**, not a shell string: `exec <name> python /skill/probe.py
  capture --surface ... --out ...`, never `exec <name> sh -c "... $X ..."`.

When a step truly cannot be written this way, run it anyway, say in the report which command
needed approval and why, and write it as simply as the step allows.

## 2. Surface inventory

Enumerated statically from the **original** code, before any modification
(`01-project-analysis.md` §5). Phase 1 is read-only and only holds the enumeration; the file is
written in Phase 3a, step 1, to `<target>/reports/surface.json`.

```json
{
  "version": 3,
  "appType": "http",
  "baseUrl": "http://127.0.0.1:8081",
  "entries": [
    {
      "id": "list-stock-items",
      "method": "GET",
      "path": "/stock-items?limit=10",
      "headers": { "Accept": "application/json" },
      "body": null,
      "skip": false,
      "skipReason": null
    },
    {
      "id": "purge-archive",
      "method": "DELETE",
      "path": "/archive",
      "destructive": true
    },
    {
      "id": "notify-third-party",
      "method": "POST",
      "path": "/webhooks/test",
      "skip": true,
      "skipReason": "calls a third party"
    },
    {
      "id": "reserve-inverted-period",
      "method": "POST",
      "path": "/reservations",
      "body": { "roomId": 3, "from": "2026-05-10", "to": "2026-05-02" },
      "kind": "security",
      "finding": "AP-11",
      "expect": "rejected"
    },
    {
      "id": "reserve-malformed-body",
      "method": "POST",
      "path": "/reservations",
      "rawBody": "{\"roomId\": ",
      "kind": "security",
      "finding": "AP-11",
      "expect": "rejected"
    },
    {
      "id": "search-stock-quote",
      "method": "GET",
      "path": "/stock-items?name=%27",
      "kind": "security",
      "finding": "AP-02",
      "expect": "neutralized",
      "like": "list-stock-items"
    }
  ]
}
```

Field rules:

- `id` — stable and unique. It is the join key between baseline and replay; if an id changes, the
  comparison silently loses the entry. Derive it from method + path, not from a counter.
- `path` — fully resolved, including any path parameter substituted with a value that exists, and
  any query string needed to make the call meaningful.
- `body` — a minimal valid payload for methods that take one, `null` otherwise. It is serialized
  as JSON.
- `rawBody` — a string sent **byte for byte** instead of `body`, for input no serializer would
  produce: a truncated document, a wrong type at the top level. Its content type is the entry's
  `Content-Type` header, `application/json` by default.
- `headers` — anything needed to exercise the entry, including authentication.
- `destructive: true` — the entry is exercised, but alone, on its own fresh boot (§2.2).
- `skip: true` — the entry is recorded but never called. Every skipped entry is `UNVERIFIED` and
  **must** appear in the report's degraded-verification block. Skipping silently is the failure mode
  this whole document exists to prevent.

Reasons to skip: it calls a third party; it requires credentials you do not have; it is
non-deterministic in a way the shape comparison cannot absorb. **Destructive is not a reason to
skip** — it is a reason to isolate (§2.2). Deleting, purging and resetting are behaviour clients
depend on, and a refactoring breaks them as easily as anything else.

**Coverage rule.** Prefer exercising every entry, including the error paths that are part of the
surface — a `404` for a missing identifier and a `400` for malformed input are behaviour a client
depends on, and they are cheap to capture. An entry that is never exercised is never protected.

**Contract headers need a request that elicits them.** Cross-origin headers appear only when the
request carries an `Origin` header; include one entry with it (and a preflight `OPTIONS` entry)
whenever the application configures cross-origin access, or a change to that policy — typically
from a dependency upgrade — goes unobserved (§5.3).

### 2.1 Security entries — hostile input whose behaviour is expected to change

Some findings are only fixed when a request that used to be **accepted** is now **rejected**: an
injection payload, an out-of-range domain value, a call without the identity the operation requires.
Put such a request in the ordinary inventory and the fix shows up as a `REGRESSION`. That is the
wrong label, and it teaches the reader to ignore the result state.

Mark those entries separately:

| Field | Value |
|---|---|
| `kind` | `"security"` (the default, when absent, is `"contract"`) |
| `finding` | The catalog id of the finding the entry demonstrates, e.g. `"AP-02"`. **Required**: a security entry that does not name a finding is an unexplained exemption from the regression rule |
| `expect` | `"rejected"`: the fixed application answers with a client error (`4xx`). `"neutralized"`: the fixed application treats the input as ordinary data — it answers like a benign request would |
| `like` | Required with `"neutralized"`: the id of a **benign sibling** — an entry on the same operation with legitimate input, captured in the same runs |

**Rejected or neutralized.** Some fixes do not reject hostile input: they defuse it. A
parameterized query does not refuse a quote character; it searches for one. Filing that as
`"rejected"` turns a correct fix into `NOT FIXED`, or worse, into a regression. Filing it as a
contract entry turns it into a `REGRESSION` for sure — the answer changed, which is the point of
the fix. `"neutralized"` has an objective criterion instead: after the fix, the hostile request
must be **indistinguishable in shape from its benign sibling** — same non-error status, same
media type, same body shape (an empty collection matches a populated one: that is data, not
behaviour). Choose `rejected` when the fix is a validation, and `neutralized` when the fix is
escaping, parameterization or encoding.

If the anomaly the finding describes is only visible in **values** — the injected request
returned rows of the right shape that it should not have — the shape comparison cannot tell the
two runs apart, and the entry comes back `UNVERIFIED`. Verify that finding another way and say
how.

Rules:

- A security entry is **only** for input no legitimate client sends. A request a legitimate client
  sends stays a contract entry, whatever the finding says. Hostility has to be evident from the
  payload itself: an injection string, a period ending before it starts, another principal's identifier.
- Security entries run **after** every contract entry (the harness orders them). A hostile call may
  mutate state, and the contract entries must see the same datastore in baseline and replay.
- A fix whose effect is visible neither as a rejection nor as a neutralization (for example, a
  hash no longer returned, or output that is now escaped) cannot be a security entry. Verify it
  another way and say how.
- A security entry whose finding ends up `PROPOSED, NOT APPLIED` is expected to come back
  `NOT FIXED`. Say so next to the result, so that nobody mistakes it for a failed fix.

### 2.2 Destructive entries — exercised alone

An entry that deletes, purges or resets state would change what every later entry observes, so
running it in the middle of a capture makes the rest of the capture meaningless. Skipping it
leaves the operation unprotected. Mark it `destructive: true` instead:

- A full capture or live compare **leaves it out**, and says so.
- It is captured **alone**, on its **own fresh boot** (a new run copy, or a new
  `refactored-<n>/`), with `capture --only <its id> --merge` into the same file. The harness
  refuses `--only` lists that mix a destructive entry with anything else.
- Replay it the same way: fresh boot, `--only <its id> --merge` into the current capture, then
  `compare --current`.

Each destructive entry costs one extra boot in the baseline and one in the replay. That cost is
the price of protecting it; declare the entries you chose to skip anyway, with their reasons.

## 3. Capture

Run against the original booted from a fresh run copy of the pristine snapshot (§1.1), before the
first file of `<target>` is modified.

For each entry, record

| Field | Note |
|---|---|
| `state` | `OBSERVED` — the call completed and a response was read. `ERROR` — the call was made and failed at transport level (refused, reset, timed out, truncated). `SKIPPED` — the call was never made |
| `status` | HTTP status, or process exit code, depending on the adapter |
| `contentType` | Media type only — parameters such as charset are stripped before comparison |
| `headers` | The contract headers of §5.3, normalized |
| `shape` | The shape descriptor (§5) of the body |
| `kind`, `finding`, `expect`, `like`, `destructive` | Copied from the inventory entry, so a comparison from files alone knows which rule applies |
| `error` | Transport error text for `ERROR`, the skip reason for `SKIPPED` |

**`ERROR` and `SKIPPED` are different facts and must never share a state.** A transport error is
observed behaviour — the application failed to answer. A skipped entry is an absence of
observation. Protocol version 1 recorded both as `UNVERIFIED`, so a request that crashed the
original was reported as "not verified" instead of "failed before", and its fix could never show up
as an improvement. An implementation reading a version-1 file treats `UNVERIFIED` as `SKIPPED`,
because that reading claims nothing. A version-2 file has no `expect`, `like` or `destructive`
fields: its security entries are read as `"rejected"`, and none of its entries as destructive.

Output goes to `<target>/reports/baseline.json`:

```json
{
  "version": 3,
  "capturedAt": "2026-09-20T18:04:11Z",
  "baseUrl": "http://127.0.0.1:8081",
  "results": {
    "list-stock-items": {
      "id": "list-stock-items", "method": "GET", "path": "/stock-items?limit=10",
      "kind": "contract", "finding": null, "expect": null, "like": null, "destructive": false,
      "state": "OBSERVED", "status": 200, "contentType": "application/json",
      "headers": {},
      "shape": { "type": "array", "items": { "type": "object",
                 "properties": { "id": "number", "label": "string", "quantity": "number" } } },
      "error": null
    }
  }
}
```

### 3.1 An entry that crashes the original

If one call brings the original down, every call after it fails with a transport error only
because nothing is listening. Those later errors describe the crash, not the entries. The harness
warns when a capture has more than one `ERROR`. When that happens:

1. Identify the entry that crashed the process (the first `ERROR`, confirmed by the process having
   exited — `proc status`, or the container's state).
2. Stop what is left of that execution through its handle (`proc stop`, or remove the container by
   name), then boot the original again from a **fresh** run copy.
3. Capture the entries after it with `--only <ids> --merge`, so they are recorded against a live
   application. Keep the crashing entry's own `ERROR` — that is the real baseline behaviour.

The same applies to the replay.

If capture is impossible at all — the application will not boot, the datastore cannot be provisioned,
no runtime is available — record that, continue the refactoring, and mark the whole Phase 3
validation `UNVERIFIED` with the reason. Do not repair the original application in order to capture
a baseline: that is already a modification, and it destroys the comparison you were trying to make.

## 4. Replay and compare

After the refactoring, boot the new application from a fresh `refactored-<n>/` copy (§1.1),
**on the same base URL**, and repeat exactly the same calls, in the same order, from the same
inventory file. Compare against the baseline.

### Result states — contract entries

A **failure** is a transport error (`ERROR`) or a server error (status ≥ 500).

| State | Condition |
|---|---|
| `PASS` | Status, content type, contract headers and shape all equal |
| `PASS (improved from <status or transport error>)` | The baseline was a failure and the replay is not |
| `REGRESSION` | Anything differs and the baseline was not a failure; or the baseline answered and the replay has a transport error |
| `PRE-EXISTING FAILURE` | The baseline was a failure and the replay is a failure too |
| `UNVERIFIED` | The entry was `SKIPPED` in either run, or is missing from either run |

`PRE-EXISTING FAILURE` is the honesty rule. An entry that failed before and fails now is neither a
pass nor a regression: you neither fixed it nor broke it, and the report must say exactly that.
Never report it as `✗`, and never report it as `✓`.

An entry that **improves** is not a regression, but it is still a behaviour change, so it is named
rather than hidden. **A transport error in the baseline is a failure like a server error** — a
request that used to crash the application and now gets an answer is an improvement, and the
report says so.

### 4.1 Result states — security entries (§2.1)

| State | Condition |
|---|---|
| `FIXED` | The baseline did not reject the input (it accepted it, or failed on it) and the replay rejects it with a `4xx` |
| `NOT FIXED` | The replay still does not reject it |
| `REGRESSION` | The baseline answered, and the replay now fails (≥ 500 or transport error): the fix made hostile input crash the application |
| `UNVERIFIED` | Skipped or missing in either run; or the baseline **already** rejected the input, so the entry never demonstrated the finding — rewrite it |

For `expect: "neutralized"`, "rejects" is replaced by "behaves like the benign sibling" (§2.1):

| State | Condition |
|---|---|
| `FIXED` | The baseline did not behave like the sibling, and the replay does |
| `NOT FIXED` | The replay still does not behave like the sibling |
| `REGRESSION` | The baseline answered, and the replay now fails (≥ 500 or transport error) |
| `UNVERIFIED` | Skipped or missing; `like` absent, or the sibling not observed in both runs; or the baseline **already** behaved like the sibling — the entry never demonstrated the finding |

A `NOT FIXED` on a finding that Phase 3 reports as resolved is a contradiction, and the finding
moves to `unresolved`. A `NOT FIXED` on a finding under `PROPOSED, NOT APPLIED` is expected.

### 4.2 Exit code

`0` when there are no regressions; `1` when there is at least one; `2` on a usage or I/O error. The
agent must not treat a non-zero exit as a harness problem: it is the finding. `NOT FIXED` does not
change the exit code, because it is expected for proposed items; the agent reconciles it with the
report as §4.1 says.

### 4.3 Entries added after the baseline

Refactoring often reveals an entry the inventory missed: an edge case, an error path, a hostile
input. Adding it to the replay alone gives it nothing to be compared with, and it comes back
`UNVERIFIED` — or worse, it is described as passing because the new code handles it.

An entry added after the baseline is captured **against the original**:

1. Add it to `surface.json` (never change an existing id — that is the join key).
2. Boot the original from a **fresh** run copy of the pristine snapshot (§1.1).
3. `capture --only <new ids> --merge` into the existing `baseline.json`. The command reports what
   **this** run captured, not the whole file; read its counts as such.
4. Then replay as usual.

If the snapshot is gone and cannot be rebuilt, the entry is `UNVERIFIED` in the final report, with
that reason.

## 5. Shape, not values

**Compared:** status / exit code, media type, the contract headers (§5.3), and the **shape** of the
body — for JSON, the recursive set of keys and the type of each leaf; for short text, its masked
line skeleton (§5.1).

**Not compared:** any volatile value. Generated identifiers, timestamps, durations, hashes,
correlation ids, cursor tokens, random values, and ordering that the application does not guarantee.

Why: comparing values produces a false regression on every run, and within two days everyone learns
to ignore the validation result. **A noisy check is worse than no check — it costs the same and you
stop reading it.**

### Shape descriptor

Deterministic, so two captures of the same shape serialize identically.

| Value | Descriptor |
|---|---|
| null | `"null"` |
| boolean | `"boolean"` |
| number | `"number"` |
| string | `"string"` |
| empty array | `{"type":"array","items":"empty"}` |
| array, uniform elements | `{"type":"array","items": <element descriptor>}` |
| array, mixed elements | `{"type":"array","items":{"oneOf":[<distinct descriptors, sorted>]}}` |
| object | `{"type":"object","properties":{<key>: <descriptor>, ...}}`, keys sorted |
| empty body | `"empty"` |
| non-JSON body, valid UTF-8, ≤ 4096 bytes | `{"type":"text","lines":[<masked lines, sorted>]}` (§5.1) |
| anything else (binary, invalid UTF-8, longer text) | `{"type":"opaque","bytes":"present"}` |

A body is classified by its bytes, not by its declared content type: it is JSON if it parses as
standard JSON (no `NaN`/`Infinity`); otherwise text or opaque as above. "Sorted" means by Unicode
code point, and serialization is key-sorted, two-space indented, UTF-8, unescaped, LF line endings —
so every implementation writes the same bytes.

Notes:

- Array **length and order are deliberately not compared** — only the element shape. A collection
  whose row count depends on the datastore's contents would otherwise fail on every run.
- Object keys **are** compared, recursively and exactly. A removed field, an added field or a changed
  leaf type is a shape difference and therefore a regression. An added field is backwards compatible
  for many clients, but a refactoring should not be adding fields; the diff labels it `added` so the
  report can explain it.
- The descriptor deliberately ignores every value. If a *value* genuinely is the contract — a status
  enumeration, a fixed code — assert it in a dedicated entry rather than weakening the general rule.

### 5.1 Text bodies — the masked skeleton

Version 1 recorded every non-JSON body as `opaque`. That hid exactly the changes a client sees in a
plain-text or HTML response: an error message reworded, a line dropped. The skeleton keeps the
wording and drops the volatile values:

1. split the body into lines on `\n` (with an optional preceding `\r`);
2. strip trailing ASCII whitespace from each line and drop empty lines;
3. apply the masks of §5.2 to each line;
4. keep the **set** of distinct lines, sorted.

Line order and repetition are ignored for the same reason array order and length are: they vary
with data. A reworded message, an added or removed line, or a changed template **is** detected, and
reported as `textChanged` with the lines removed and added.

The 4096-byte limit keeps a large rendered page out of the comparison, where every dynamic fragment
would become noise. A larger text body is `opaque`, and an entry whose content matters that much
needs a dedicated assertion.

### 5.2 Masks

Applied in this order, to text lines and to header values. ASCII character classes only, so every
implementation masks the same characters:

| Order | Pattern | Placeholder |
|---|---|---|
| 1 | ISO-8601 date-time: `[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z\|[+-][0-9]{2}:?[0-9]{2})?` | `<ts>` |
| 2 | UUID: 8-4-4-4-12 hex groups | `<uuid>` |
| 3 | A run of 16 or more hex characters not adjacent to another letter or digit | `<hex>` |
| 4 | Any remaining run of decimal digits `[0-9]+` | `<n>` |

State this rule in the report whenever a text comparison contributed to a result: it defines what
was and was not verified.

### 5.3 Contract headers

Most response headers are transport detail and change for reasons nobody cares about. A few are
contract: clients act on them, and a dependency upgrade can change them without touching a line of
the application. These are recorded and compared:

| Header | Normalization |
|---|---|
| `Location` | masked (§5.2) |
| `WWW-Authenticate` | masked |
| every `Access-Control-*` | masked; for `-Allow-Methods`, `-Allow-Headers`, `-Expose-Headers`: split on commas, trimmed, lower-cased, de-duplicated, sorted |
| `Set-Cookie` | the cookie **names** only, de-duplicated and sorted; values and attributes ignored |

Names are lower-cased; repeated headers are joined with `", "`. A difference is reported as
`headerMissing`, `headerAdded` or `headerChanged`, and counts like a shape difference. A version-1
file has no `headers` field; headers are then not compared, and the report must say so.

Redirects are **never followed**: a `3xx` and its `Location` are the entry's own behaviour.

### Diff output

Report, per differing entry: `statusChanged`, `contentTypeChanged`, the header differences, and for
shapes a path-addressed list — `missing` (in baseline, absent now), `added` (absent in baseline,
present now), `typeChanged` (path, from, to), `textChanged` (lines removed and added). Paths use
dotted notation with `[]` for array elements: `data.items[].label`.

## 6. Adapters per application type

The algorithm is identical — *enumerate → exercise → record shape → compare*. Only the adapter
changes.

| App type | Exercise | `status` is | `shape` is from |
|---|---|---|---|
| **HTTP service** | Issue the request | The HTTP status | The parsed response body |
| **CLI** | Run the command with its flags, capture stdout/stderr | The exit code | Parsed stdout if it is JSON; otherwise a line-count-free structural summary (§6.1) |
| **Library** | Call each exported symbol with recorded arguments, inside the target's own test runner or a small driver script | `0` on return, `1` on raise | The returned value's shape, plus the exception type on failure |
| **Queue worker** | Publish a recorded message, wait bounded, collect what is produced | Delivered / not delivered | The shape of produced messages and of the resulting persisted records |

**6.1 — Non-JSON stdout.** Do not compare text verbatim: it carries timestamps, paths and durations.
Use the text skeleton of §5.1, with one more mask applied first: absolute filesystem paths become
`<path>`. State the masking rule in the report, because it defines what you are and are not
verifying.

**6.2 — Effects as surface.** For a worker, the observable result is partly in the datastore. Capture
the shape of the affected records (the key set, not values, and a row count only if the operation's
count is deterministic).

**6.3 — Hybrid applications.** Enumerate every surface the application has and run every relevant
adapter. Report the states per surface.

## 7. Implementing the harness for an unshipped ecosystem

When the target's runtime is neither Python nor Node, generate an implementation **from this
document**, in the target's own language, using only its standard library.

It must:

1. Expose two modes, `capture` and `compare`, with the CLI of §8.
2. Read the surface inventory of §2 and write the baseline of §3 — same JSON, byte-compatible, so a
   capture from one implementation can be compared by another.
3. Implement the shape descriptor of §5 exactly — sorted keys, sorted `oneOf`, the text skeleton,
   the masks, the contract headers — so descriptors serialize identically across implementations.
4. Keep the three record states of §3 distinct, and implement the result states of §4 and §4.1
   (both `rejected` and `neutralized`) and the exit codes.
5. Run security entries after contract entries; leave destructive entries out of full runs and
   refuse to mix them with other ids (§2.2); send `rawBody` verbatim; support `--only` and
   `--merge` (§4.3), counting only the current run in what it prints.
6. Never follow redirects.
7. **Never boot the application**, never install a dependency, never write outside the paths it is
   given.
8. Apply a per-request timeout and never hang: a hung harness is indistinguishable from a broken
   application, and it is the agent that will be blamed.

Read `scripts/probe.py` and `scripts/probe.mjs` before writing it — they are short, and they are
teaching artifacts as much as tools. A generated implementation has not been through the
conformance test the shipped ones pass; say in the report that validation ran on a generated
harness.

**Host mode on an unshipped runtime** needs `proc` too. Prefer running the shipped `proc.py` or
`proc.mjs` if either runtime exists on the host: `proc` never loads the target's code, so it does
not have to share its runtime. Generate one only when neither exists, from §1.3 and the shipped
implementations, and keep all of their guarantees: a new process group; the PID **and** the OS
start time recorded before readiness; identity checked before every stop; only the recorded tree
stopped; a busy port refused, never freed; the same exit codes. Say in the report that process
ownership ran on a generated tool.

## 8. Harness CLI (shared by every implementation)

```
<runtime> probe capture  --surface <path> --base-url <url> --out <path>
                         [--only <id,id,...>] [--merge] [--timeout <seconds>]
<runtime> probe compare  --surface <path> --baseline <path>
                         [--base-url <url>] [--current <path>] [--out <path>] [--timeout <seconds>]
```

- `capture` exercises the surface against a **running** application and writes a baseline file.
  `--only` restricts it to the listed ids; `--merge` adds the results to an existing `--out` file
  instead of replacing it (§3.1, §4.3).
- `compare` produces a current capture — from `--base-url` (live) or `--current` (a file captured
  earlier) — and diffs it against `--baseline`. It prints a per-entry table and a summary, and exits
  `1` if any entry is a `REGRESSION`.
- `--timeout` defaults to 10 seconds per request. There is no unbounded mode.
- `capture` prints what **this** run captured and, separately, how many entries the file now holds.
  Its transport-error warning counts this run only (§3.1).
- A full `capture` or live `compare` leaves destructive entries out and notes them on stderr
  (§2.2).

`proc` (host mode, §1.3, and the copies of §1.1 in both modes) has its own CLI, shared by
`proc.py` and `proc.mjs`; it is documented in §1.3 and at the top of each script.

## 9. Floor mode — declared, never silent

If no runtime capable of parsing JSON is available, the protocol degrades to **status-code parity
only**:

One literal command per surface entry (§1.4), recording each status code in
`reports/baseline-floor.txt` as `<id> <code>`, one line per entry:

```
curl -s -o /dev/null -w "%{http_code}" -X GET http://127.0.0.1:8081/widgets --max-time 10
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8081/widgets --max-time 10
```

After refactoring, repeat the same commands into `reports/replay-floor.txt` and compare the two
files line by line.

Floor mode verifies that each entry still answers with the same status. It verifies **nothing** about
the response body: a handler that returns `200` with an empty object where it previously returned a
populated one passes.

**Therefore the report must carry, verbatim, the degraded-verification block:**

```
DEGRADED — validation ran in floor mode (status-code parity only).
  Reason: no JSON-capable runtime available in the target environment.
  Unverified: response content types, response body shapes, added/removed/renamed fields.
```

Labelled degraded validation is honest. Silent degraded validation is worse than no validation,
because in the output it is indistinguishable from the real thing.

## 10. Failure modes of this protocol

- **Capturing after the first edit.** The baseline is then a baseline of the new code, and the
  comparison is tautological. Capture first, always.
- **Changing the inventory between capture and replay.** The join key is `id`; editing paths or ids
  between the two runs loses entries silently. Read the same file both times.
- **Different data between the runs.** Shape comparison absorbs most of this, but a collection that
  is empty in one run and populated in the other changes the array descriptor. Use the same datastore
  state for both, or accept and declare it.
- **Treating a skipped entry as a pass.** It is `UNVERIFIED`, and it belongs in the degraded block.
- **Forgetting to shut the first process down.** The replay then hits the old application on the same
  port and everything "passes". Stop every execution through its handle; `proc start` refuses a
  port that still answers.
- **Stopping by name, image or pattern.** It reaches processes the run did not start — on a
  developer's machine, their editor's language server, a notebook kernel, another project's
  server. It is never necessary: the handle (container name, or `proc` state file) always exists,
  and when it does not, the right move is to report the orphan, not to sweep (§1.3).
- **Freeing a busy port.** The process holding it is not yours. Choose another port.
- **Running the refactored application inside the target.** Its runtime artifacts land in the
  delivered tree. Run it from `refactored-<n>/` (§1.1).
- **Paths carried in shell variables.** `SNAP=...` once and `$SNAP/run-2` afterwards reads
  naturally, but no reviewer or permission layer can check what it expands to, so every such
  command interrupts the user. Write the literal path (§1.4).
- **Deleting the snapshot before the re-audit.** The re-audit still needs to run the application.
- **Relying on a port override that also turns debug off.** The audit then never observes the
  debug surface it is supposed to judge (§1.2).
- **Calling a non-zero exit a harness bug.** It is the result. Fix the regression or report it.
- **Running the original inside the target.** Its runtime artifacts land in the tree — before the
  gate, that breaks the write restriction; after it, they mix with the refactored code. Run it from
  the snapshot (§1.1).
- **Reading a crash cascade as many failures.** One entry killed the process; the rest were never
  answered. Restart and re-capture them (§3.1).
- **Filing hostile input as a contract entry.** Its fix then reads as a regression. Mark it
  `security` with its finding id (§2.1) — `rejected` for a validation fix, `neutralized` with a
  benign sibling for an escaping or parameterization fix.
- **Skipping a destructive entry.** It is then never protected. Isolate it (§2.2).
- **Checking a late entry only against the new code.** It has no baseline, so nothing was compared.
  Capture it against the original (§4.3).
- **Editing the original to change its port.** Use the order in §1.2.
