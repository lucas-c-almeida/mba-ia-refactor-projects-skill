---
name: refactor-arch
description: Analyze, audit and refactor any codebase toward layered architecture (MVC as its concrete instance), in three sequential phases — stack analysis, severity-ranked anti-pattern audit with a mandatory human confirmation gate, and validated refactoring with baseline-then-replay behavioural verification. Technology-agnostic; works on any language, framework or application type (HTTP service, CLI, library, queue worker). Use when asked to audit architecture, find code smells or anti-patterns, assess technical debt, restructure a project into MVC or layers, or modernize a legacy codebase.
argument-hint: "[target-directory] [--yes] [--offline]"
---

# refactor-arch

Three sequential phases. Never skip one, never reorder them.

```
PHASE 1  Analysis      →  understand the target. Read only. Always runs.
PHASE 2  Audit         →  findings report. Writes only to <target>/reports/. Ends at a blocking gate.
PHASE 3  Refactoring   →  restructure + validate. Runs only after the gate is passed.
```

## Invocation contract

```
/refactor-arch                    # target = current working directory
/refactor-arch some/subdir        # target = that directory
/refactor-arch some/subdir --yes  # skip the Phase 2 confirmation (records the fact in the report)
/refactor-arch --offline          # skip live upstream lookups (records the fact in the report)
```

**Target resolution.** The first non-flag argument is `<target>`. If absent, `<target>` is the current
working directory. Resolve it once, at the start, and state it in the Phase 1 block. **Every path you
print, write or validate is relative to `<target>`, never to the CWD.** The target may be a
subdirectory of a larger repository; never analyze, report on, or modify anything outside it.

**Flags.**

| Flag | Effect | Obligation |
|---|---|---|
| `--yes` | Skips the Phase 2 confirmation prompt and proceeds directly to Phase 3. | The report must record `Confirmation: --yes (auto-approved, not human-reviewed)`. |
| `--offline` | Skips all live upstream lookups (Layer 2 of the deprecated-API check). | The report must carry the degraded-verification block naming what went unverified. |

Absent flags mean the opposite: the gate blocks, and upstream lookups are attempted.

## Governing principle — never degrade silently

Whenever you verify less than the full protocol — no network, no JSON-capable runtime, no request
surface, baseline capture impossible, a tool missing, a boot command that never becomes ready — you
**say so in the report and name exactly what went unverified**. A labelled degraded verification is
honest. A silent one is worse than no verification at all, because it is indistinguishable from
success in the output.

Corollaries you must hold to:

- Never report a finding you did not observe in the code you read. Cite file and line, always.
- Never claim a check passed that you did not run. `UNVERIFIED` is a legitimate, expected result.
- Never assert that an API is deprecated from memory. Prior knowledge is a hypothesis to verify,
  never evidence to report. See `references/02-antipattern-catalog.md`, AP-14.

---

## PHASE 1 — Analysis

**Read `references/01-project-analysis.md` before starting.** It carries the detection heuristics.

Read-only. Do not write anything in this phase.

1. Detect language(s) and the dominant one.
2. Detect framework and its resolved version (prefer lockfile/installed metadata over manifest range).
3. Enumerate direct dependencies.
4. Infer the application domain from names, schema and routes — describe it in one line.
5. Determine the **application type** and enumerate its **public surface** (HTTP service / CLI /
   library / queue worker). This drives Phase 3 validation. See `01-project-analysis.md` §5.
6. Map the current architecture: what layers exist, whether they are real or nominal.
7. Count source files (exclude vendored, generated and dependency directories — state the rule used).
8. Identify the database and its tables, from migrations, schema files, ORM models or raw DDL.
9. Derive the boot command for the stack, and record it — Phase 3 needs it.

Print exactly:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        <path relative to CWD>
Language:      <language + runtime version if detectable>
Framework:     <framework + resolved version, or "none (plain <language>)">
Dependencies:  <direct dependencies, comma-separated>
Domain:        <one line>
App type:      <HTTP service | CLI | library | queue worker | hybrid: ...>
Architecture:  <one line: current layering, and whether it is real or nominal>
Source files:  <N> files analyzed
DB tables:     <table names, or "none detected">
================================
```

If a field cannot be determined, print `undetermined — <reason>`. Never guess a version.

---

## PHASE 2 — Audit

**Read `references/02-antipattern-catalog.md` and `references/03-report-template.md` before starting.**

1. Walk the source files identified in Phase 1. Cross every one against the catalog.
2. For each match, record: catalog id, name, severity, file, exact line range, what you actually saw,
   why it matters, what to do.
3. Apply the severity rules in the catalog. **Severity follows impact in this context, not the
   category label.** Each entry lists explicit escalation and de-escalation conditions; apply them and
   say in the finding when you did.
4. For AP-14 (deprecated APIs), follow its evidence protocol strictly. Tier D — your own prior
   knowledge — is never reportable. Skip Layer 2 if `--offline`, and declare it.
5. Sort findings CRITICAL → HIGH → MEDIUM → LOW.
6. Mark each finding `contract-safe` or `contract-changing` per the gate in
   `references/04-architecture-guidelines.md` §6. Phase 3 needs this classification.
7. Write the report to `<target>/reports/audit-<YYYYMMDD-HHMM>.md` and copy it to
   `<target>/reports/audit-latest.md`. Print it to the terminal as well.

**Write restriction (hard rule).** In Phase 2 you may create or modify files **only** inside
`<target>/reports/`. No file outside that directory may be created, modified, renamed or deleted
before the user confirms. `reports/` is audit output, not project source — writing there is not a
violation, and you must not paralyse yourself over it.

**The gate.** After printing the report, stop and ask literally:

```
================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
>
```

Then **wait for the answer**. Do not call any write tool until it arrives.

- `y` → Phase 3 over all findings.
- `n` → stop. Confirm the report path. Make no further change.
- `c` → Phase 3 over CRITICAL and HIGH only; list the deferred items in the final report.
- `--yes` was passed → skip the prompt, behave as `y`, and record the auto-approval in the report.

---

## PHASE 3 — Refactoring

**Read `references/06-validation-protocol.md` first, then
`references/04-architecture-guidelines.md` and `references/05-refactoring-playbook.md`.**

### 3a. Capture the baseline — before touching any file

This step happens **first**, before the first edit. Once you have modified a file, the original
behaviour is no longer observable and the entire validation becomes `UNVERIFIED`.

1. Enumerate the public surface (from Phase 1 §5) into a surface inventory file under
   `<target>/reports/`.
2. Boot the application with the Phase 1 boot command and wait for readiness. **You** do this — the
   harness never boots anything.
3. Run the harness in `capture` mode against the running application:
   `scripts/probe.py` for a Python target, `scripts/probe.mjs` for a Node target, or an
   implementation you generate from `06-validation-protocol.md` for any other ecosystem, on the
   target's own runtime. Never install a dependency to validate.
4. Shut the application down.

If the baseline cannot be captured, say so explicitly, continue, and mark the final validation
`UNVERIFIED` with the reason. Do not pretend.

### 3b. Refactor

- Target architecture per `04-architecture-guidelines.md`: layered separation, with MVC as its
  concrete instance when the application has a request surface, and the nearest mapping
  (domain / ports / adapters) when it does not — declaring the adaptation in the report.
- One transformation per finding, from `05-refactoring-playbook.md`. Cross-reference the ids.
- Fix findings of **all** severities that the gate answer authorized.
- **Public-contract gate.** Any fix that would change what a legitimate client observes — route path
  or method, success status code, response body shape, a removed or renamed field, a previously
  optional parameter made required — is **not applied**. Record it under `PROPOSED, NOT APPLIED`
  with its rationale. Everything else is applied.
- **Rewrite in place.** Content migrates into the new layers and the superseded files are removed.
  Do not leave a parallel copy in `legacy/`, `old/` or a second source tree — that is dead code, and
  the next audit would rightly flag it. Git history is the backup.
- Never invent behaviour. If a line's intent is unclear, preserve it verbatim in the new layer and
  note it.

### 3c. Replay and validate

1. Boot the refactored application. If it does not boot, that is the finding — report it, do not
   hide it.
2. Run the harness in `compare` mode against the baseline.
3. Classify every surface entry: `PASS` / `REGRESSION` / `PRE-EXISTING FAILURE` / `UNVERIFIED`.
   An entry that already failed in the baseline and fails identically now is
   `PRE-EXISTING FAILURE`, never `✗` — do not take credit for it and do not take blame for it.
4. If a regression is found, fix it and replay. If it cannot be fixed, report it plainly.

### 3d. Re-audit — mandatory

Run Phase 2's audit again over the refactored target, with the same catalog and the same
thresholds. This step is **not optional**: it is the only thing that licenses any claim about what
remains, and without it the final block would be asserting an absence nobody looked for.

Partition the re-audit's findings into two sets:

- **proposed-not-applied** — findings that match an item already recorded under
  `PROPOSED, NOT APPLIED`. These are expected: the contract gate declined them on purpose.
- **unresolved** — everything else. A finding here is either one the refactoring failed to
  eliminate, or one the refactoring introduced. Both are worth knowing; say which.

Report the counts. Do not silently drop a re-audit finding because it is inconvenient, and do not
reclassify one into `proposed-not-applied` unless it genuinely matches an item you already
recorded before the re-audit ran.

If any part of the audit could not run this time — `--offline` disables the live deprecated-API
lookup, for instance — the re-audit is **partial**, and `## Verification Coverage` must say so.
A partial re-audit can never produce the `Zero anti-patterns remaining` line.

Print exactly:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<directory tree, relative to target>

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: <P> PASS, <R> REGRESSION, <F> PRE-EXISTING FAILURE, <U> UNVERIFIED
  ✓ Findings resolved: <n>/<total>  (<k> proposed, not applied — see report)
  <re-audit line — see below>

## Proposed, Not Applied
<contract-changing items, or "none">

## Verification Coverage
<full, or the degraded-verification block naming what went unverified and why>
================================
```

The re-audit line always appears, in one of exactly three forms, chosen by what 3d actually
returned:

```
  ✓ Zero anti-patterns remaining  (re-audit: 0 findings)
  ○ Anti-patterns remaining: <k> proposed-not-applied, <u> unresolved  (re-audit: <m> findings)
  ⚠ Re-audit partial — see Verification Coverage  (<m> findings over the checks that ran)
```

The first form requires a complete re-audit returning nothing at all — not "nothing unexpected".
If a single item sits under `PROPOSED, NOT APPLIED`, the second form is the correct one; the report
would otherwise contradict itself three lines apart.

Use `✗` for a genuine failure, `✓` only for something you actually observed to pass, `○` for a
true statement that is not a success, and `⚠` where coverage itself was reduced.

---

## Reference map — read on demand, not upfront

| File | Read it when |
|---|---|
| `references/01-project-analysis.md` | Start of Phase 1 |
| `references/02-antipattern-catalog.md` | Start of Phase 2 |
| `references/03-report-template.md` | Writing the Phase 2 report |
| `references/04-architecture-guidelines.md` | Planning the Phase 3 structure |
| `references/05-refactoring-playbook.md` | Executing each Phase 3 transformation |
| `references/06-validation-protocol.md` | Phase 3a, and whenever validation degrades |
| `scripts/probe.py`, `scripts/probe.mjs` | Reference harness implementations; read to adapt |
