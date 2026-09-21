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
| Exercise the surface, record the shape, compare | **Harness** | Protocol-pure; identical in every language |
| Shut the process down | **Agent** | Stack-specific |

**The harness never boots the application.** A harness that knew how to start a Flask app, a Node
server, a Go binary and a Rails app would be a collection of stack-specific special cases —
precisely the coupling this skill exists to avoid. Booting is stack-specific; probing is not.

**The harness runs on the target's own runtime.** If you could boot the application, you have a
runtime in which you can run a script. A Python target gets the Python harness (standard library
only); a Node target gets the Node harness (built-ins only). The additional dependency is zero **by
construction**, not by luck. Never install a package in order to validate — doing so modifies the
target's dependency set, which is itself a change you would then have to validate.

## 2. Surface inventory

Enumerated statically from the **original** code, before any modification
(`01-project-analysis.md` §5). Written to `<target>/reports/surface.json`.

```json
{
  "version": 1,
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
      "skip": true,
      "skipReason": "destructive; not safe to exercise"
    }
  ]
}
```

Field rules:

- `id` — stable and unique. It is the join key between baseline and replay; if an id changes, the
  comparison silently loses the entry. Derive it from method + path, not from a counter.
- `path` — fully resolved, including any path parameter substituted with a value that exists, and
  any query string needed to make the call meaningful.
- `body` — a minimal valid payload for methods that take one, `null` otherwise.
- `headers` — anything needed to exercise the entry, including authentication.
- `skip: true` — the entry is recorded but never called. Every skipped entry is `UNVERIFIED` and
  **must** appear in the report's degraded-verification block. Skipping silently is the failure mode
  this whole document exists to prevent.

Reasons to skip: the operation is destructive; it calls a third party; it requires credentials you
do not have; it is non-deterministic in a way the shape comparison cannot absorb.

**Coverage rule.** Prefer exercising every entry, including the error paths that are part of the
surface — a `404` for a missing identifier and a `400` for malformed input are behaviour a client
depends on, and they are cheap to capture. An entry that is never exercised is never protected.

## 3. Capture

Run **after** the application is up and ready, and **before** the first file is modified.

For each non-skipped entry: issue the call, then record

| Field | Note |
|---|---|
| `status` | HTTP status, or process exit code, depending on the adapter |
| `contentType` | Media type only — parameters such as charset are stripped before comparison |
| `shape` | The recursive shape descriptor (§5) of the parsed body |
| `state` | `OBSERVED` when the call completed; `UNVERIFIED` when it could not be made |
| `error` | Transport-level error text when the call could not be made |

Output goes to `<target>/reports/baseline.json`:

```json
{
  "version": 1,
  "capturedAt": "2026-09-20T18:04:11Z",
  "baseUrl": "http://127.0.0.1:8081",
  "results": {
    "list-stock-items": {
      "id": "list-stock-items", "method": "GET", "path": "/stock-items?limit=10",
      "state": "OBSERVED", "status": 200, "contentType": "application/json",
      "shape": { "type": "array", "items": { "type": "object",
                 "properties": { "id": "number", "label": "string", "quantity": "number" } } },
      "error": null
    }
  }
}
```

If capture is impossible at all — the application will not boot, the datastore cannot be provisioned,
no runtime is available — record that, continue the refactoring, and mark the whole Phase 3
validation `UNVERIFIED` with the reason. Do not repair the original application in order to capture
a baseline: that is already a modification, and it destroys the comparison you were trying to make.

## 4. Replay and compare

After the refactoring, boot the new application **on the same base URL** and repeat exactly the same
calls, in the same order, from the same inventory file. Compare against the baseline.

### Result states

| State | Condition |
|---|---|
| `PASS` | Status equal, content type equal, shape equal |
| `REGRESSION` | Any of the three differs, and the baseline was not itself a failure |
| `PRE-EXISTING FAILURE` | The baseline was a failure (status ≥ 500 or a transport error) and the replay fails in the same way |
| `UNVERIFIED` | The entry was skipped, or was `UNVERIFIED` in the baseline, or could not be exercised now |

`PRE-EXISTING FAILURE` is the honesty rule. An entry that returned a server error before and returns
the same server error now is neither a pass nor a regression: you neither fixed it nor broke it, and
the report must say exactly that. Never report it as `✗`, and never report it as `✓`.

An entry that **improves** — a baseline server error that now succeeds — is not a regression. Report
it as `PASS (improved from <baseline status>)`. It is usually the intended effect of a fix, but it is
still a behaviour change, so it is named rather than hidden.

### Exit code

`0` when there are no regressions; `1` when there is at least one; `2` on a usage or I/O error. The
agent must not treat a non-zero exit as a harness problem: it is the finding.

## 5. Shape, not values

**Compared:** status / exit code, media type, and the **shape** of the body — the recursive set of
keys and the type of each leaf.

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
| non-JSON body | `{"type":"opaque","bytes":"present"}` or `"empty"` |

Notes:

- Array **length and order are deliberately not compared** — only the element shape. A collection
  whose row count depends on the datastore's contents would otherwise fail on every run.
- Object keys **are** compared, recursively and exactly. A removed field, an added field or a changed
  leaf type is a shape difference and therefore a regression. An added field is backwards compatible
  for many clients, but a refactoring should not be adding fields; the diff labels it `added` so the
  report can explain it.
- The descriptor deliberately ignores every value. If a *value* genuinely is the contract — a status
  enumeration, a fixed code — assert it in a dedicated entry rather than weakening the general rule.

### Diff output

Report, per differing entry: `statusChanged`, `contentTypeChanged`, and for shapes a path-addressed
list — `missing` (in baseline, absent now), `added` (absent in baseline, present now),
`typeChanged` (path, from, to). Paths use dotted notation with `[]` for array elements:
`data.items[].label`.

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
Reduce it to a structure — the set of distinct line *forms* after masking digits, hex runs, ISO
timestamps and absolute paths with placeholders — and compare that. State the masking rule in the
report, because it defines what you are and are not verifying.

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
3. Implement the shape descriptor of §5 exactly, including the sorted keys and the sorted `oneOf`,
   so descriptors serialize identically across implementations.
4. Implement the four result states of §4 and the exit codes.
5. **Never boot the application**, never install a dependency, never write outside the paths it is
   given.
6. Apply a per-request timeout and never hang: a hung harness is indistinguishable from a broken
   application, and it is the agent that will be blamed.

Read `scripts/probe.py` and `scripts/probe.mjs` before writing it — they are short, and they are
teaching artifacts as much as tools.

## 8. Harness CLI (shared by every implementation)

```
<runtime> probe capture  --surface <path> --base-url <url> --out <path> [--timeout <seconds>]
<runtime> probe compare  --surface <path> --baseline <path>
                         [--base-url <url>] [--current <path>] [--out <path>] [--timeout <seconds>]
```

- `capture` exercises the surface against a **running** application and writes a baseline file.
- `compare` produces a current capture — from `--base-url` (live) or `--current` (a file captured
  earlier) — and diffs it against `--baseline`. It prints a per-entry table and a summary, and exits
  `1` if any entry is a `REGRESSION`.
- `--timeout` defaults to 10 seconds per request. There is no unbounded mode.

## 9. Floor mode — declared, never silent

If no runtime capable of parsing JSON is available, the protocol degrades to **status-code parity
only**:

```bash
# Capture, before refactoring
while IFS=' ' read -r id method path; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -X "$method" "$BASE_URL$path" --max-time 10)
  printf '%s %s\n' "$id" "$code"
done < surface.txt > reports/baseline-floor.txt

# Replay, after refactoring
... > reports/replay-floor.txt
diff reports/baseline-floor.txt reports/replay-floor.txt
```

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
  port and everything "passes". Confirm the port is free before the second boot.
- **Calling a non-zero exit a harness bug.** It is the result. Fix the regression or report it.
