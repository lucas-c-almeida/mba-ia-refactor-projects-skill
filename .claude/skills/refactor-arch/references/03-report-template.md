# 03 — Report Template

The normative output format of Phase 2. Reproduce the structure exactly; the labels are part of the
contract. All labels are in English: `PHASE 1`, `ARCHITECTURE AUDIT REPORT`, `[CRITICAL]`, `File:`,
`Description:`, `Impact:`, `Recommendation:`.

## Where it goes

- Write `<target>/reports/audit-<YYYYMMDD-HHMM>.md`.
- Copy the same content to `<target>/reports/audit-latest.md`.
- Print the report to the terminal as well — the terminal output is what the human reviews at the
  gate.

The timestamped file exists so successive runs can be compared. `audit-latest.md` exists so a
consumer has a stable path.

**This is the only directory Phase 2 may write to.** Creating it and writing these two files is not
a modification of the project, and does not require the confirmation. No file outside
`<target>/reports/` may be created, modified, renamed or deleted before the user answers the gate.

---

## Template

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <target directory name>
Stack:   <Language + Framework + version>
Files:   <N> analyzed | ~<L> lines of code
Date:    <YYYY-MM-DD HH:MM>
Mode:    <full | --offline>
Confirmation: <pending human review | human-confirmed: y | human-confirmed: CRITICAL+HIGH only | --yes (auto-approved, not human-reviewed)>
Tree:    <clean at <commit> | uncommitted changes present — the audit read the working tree as found>
Runtime: <as found | installed the declared dependencies from <file> into <location outside the target>>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Anti-Pattern Name>   (AP-xx)
File: <path relative to target>:<start>-<end>
Description: <what is actually there, in one or two sentences, citing the construct you read. If the severity differs from the catalog default, say so and why, in one clause.>
Impact: <why it matters for this system — consequence, not category restatement>
Recommendation: <the concrete change, naming the playbook transformation: "see RP-xx">
Contract: <safe | contract-changing: what a client would observe differently>

### [CRITICAL] <next finding>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

## Catalog Coverage
<One row per catalog entry, every entry, including those with no hit. This is how a reader tells
"looked and found nothing" from "never looked".>

| Entry | Result |
|---|---|
| AP-01 | <n finding(s): ids of the findings above> |
| AP-02 | <none — what was checked, in a few words> |
| ... | ... |
| AP-19 | <n finding(s), or none, or UNVERIFIED — reason> |

## Dependency and Deprecated API Verification
<One line per checked item, for AP-14 (deprecation) and AP-19 (advisories). Every entry cites
evidence tier and, for tiers B and C, source + date.>

| Item | Version in use | Check | Evidence tier | Source | Looked up | Result |
|---|---|---|---|---|---|---|
| <package or API> | <resolved version> | <deprecation / advisory> | <A/B/C> | <runtime warning / registry / advisory id / docs URL> | <YYYY-MM-DD or "n/a — local"> | <finding id, or "no issue found"> |

<If any check could not be completed, list it here as UNVERIFIED and repeat it in the
Verification Coverage block below.>

## Verification Coverage
<Either:>
Full — all planned checks executed.
<Or, one line per gap:>
DEGRADED — the following checks did not run, and the findings above do not cover them:
  - <check name>: <why it did not run> → <what is therefore unverified>

## Proposed, Not Applied
<Only in the final Phase 3 report; omit in the Phase 2 report, or mark "to be determined in Phase 3".>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
  y = apply all findings (contract-changing items will be proposed, not applied)
  n = stop here; the report is saved and nothing else was touched
  c = apply CRITICAL and HIGH only
>
````

---

## Field rules

**Ordering.** CRITICAL → HIGH → MEDIUM → LOW, always, with no exception. Within a severity, order by
file path then by starting line, so two runs over the same code produce comparable reports.

**`File:`** — a path relative to `<target>`, never absolute and never relative to the CWD. Always a
line range, even for a single line (`config.ext:12-12`). The range must bound the evidence: the
statement and enough context for a reader to see the problem, not the whole file. If one finding has
several sites, list the primary range on `File:` and the rest in `Description:`; do not file one
finding per line for the same defect.

**`Description:`** — what you actually read. Name the construct. "A route handler builds the query
by concatenating the request's filter parameter" is a description; "unsafe database usage" is not.
Never describe something you inferred rather than observed.

**`Impact:`** — the consequence in this system, not a restatement of the category. Say what an
attacker, an operator or the next maintainer experiences.

**`Recommendation:`** — a concrete action, naming the playbook transformation id. For AP-14, name the
specific modern equivalent.

**`Contract:`** — `safe` or `contract-changing`. This is the input to the Phase 3 gate
(`04-architecture-guidelines.md` §6). If contract-changing, state exactly what an existing client
would observe differently.

**Severity deviation.** When the reported severity differs from the catalog default, the deviation
must appear in `Description:` with its reason. A severity that moves without a stated reason looks
like an error even when it is correct.

**Counts.** The `## Summary` counts must equal the number of findings actually listed, and `Total:`
must equal their sum. Inconsistent counts are the fastest way to lose a reader's trust in the whole
report.

**No target-specific expectations.** Never write that a project "should have" a particular number of
findings. The number is whatever the code produces; a small number on a clean project is a correct
result, not a failure of the audit.

---

## The degraded-verification block

Required whenever anything planned did not run. Never omit it to keep the report tidy — the
governing principle of this skill is that it does not degrade silently.

Situations that require it:

| Situation | What to declare |
|---|---|
| `--offline`, or the network is unreachable | Layer 2 deprecation lookups did not run; deprecated or withdrawn packages may exist and were not checked |
| The runtime is unavailable, so deprecation warnings could not be forced on | Tier-A evidence unavailable; only manifest-level signals were used |
| The application would not boot | No behavioural baseline; Phase 3 validation will be `UNVERIFIED` |
| No JSON-capable runtime for the harness | Floor mode; only status/exit-code parity is comparable — response shapes unverified |
| A surface entry could not be exercised safely or deterministically | Name the entry and the reason; it counts as `UNVERIFIED`, not as a pass |
| A part of the tree could not be read | Name it and say it was not audited |
| The declared dependencies could not be installed, or the snapshot could not be created | The original could not run: Tier-A deprecation evidence, the baseline and every behavioural check are unverified |
| The harness was generated for an unshipped ecosystem | Validation ran on code that has not passed the shipped probes' conformance test |
| A baseline from protocol version 1 was compared | Contract headers were not compared; transport errors in that baseline read as skipped |
| A text body exceeded the skeleton limit | Its content was compared as `opaque` — only its presence |

Each line names **the check**, **why it did not run**, and **what is therefore unverified**.
A labelled gap is honest. An unlabelled one is indistinguishable from success.

---

## The confirmation record

The report always records how it was approved:

- `pending human review` — written at the moment the report is produced;
- `human-confirmed: y` / `human-confirmed: CRITICAL+HIGH only` — updated after the answer;
- `--yes (auto-approved, not human-reviewed)` — when the flag was passed.

This exists so an auto-approved run is never mistaken for a reviewed one when the reports are read
later, side by side.

---

## The gate

After printing the report, stop and wait. Do not call a write tool until the answer arrives.

- `y` → Phase 3 over all findings, with the contract gate applied.
- `n` → stop. State the saved report path. Change nothing else.
- `c` → Phase 3 over CRITICAL and HIGH only; list the deferred items in the final report.

With `--yes`, do not print the prompt; proceed as `y` and record the auto-approval.

---

## Phase 3 additions

The final report — printed at the end of Phase 3 and appended to `audit-latest.md` — adds:

```markdown
## Proposed, Not Applied
### [<SEVERITY>] <Anti-Pattern Name>   (AP-xx)
File: <path>:<start>-<end>
Reason not applied: <which contract element would change, and what a client would observe>
Proposed change: <what to do, and what coordination it needs>
```

Plus the Phase 3 block itself:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree, relative to target>

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: <P> PASS, <R> REGRESSION, <F> PRE-EXISTING FAILURE, <U> UNVERIFIED
    Security entries: <X> FIXED, <Y> NOT FIXED
  ✓ Findings resolved: <r>/<total>  (<p> proposed, <u> unresolved)
  <re-audit line>

## Proposed, Not Applied
<list, or "none">

## Verification Coverage
<full, or the degraded block>
================================
```

`✓` only for something you observed to pass. `✗` for a genuine failure. `○` for a true statement
that is not a success. A surface entry that failed before and after the refactoring is
`PRE-EXISTING FAILURE` — neither a pass nor a regression.

**The findings line has exactly three buckets, and they add up.** Every Phase 2 finding is in one:

- `resolved` — all of it is gone, and the re-audit agrees;
- `proposed` — it sits under `PROPOSED, NOT APPLIED`, declined by the contract gate;
- `unresolved` — anything else.

There is no "partially resolved". A finding with any part remaining is not resolved: it is
`unresolved`, or `proposed` when what remains is exactly what the contract gate held back, and its
entry in the final report says which part was fixed and which was not. `<r> + <p> + <u>` equals
`<total>`. The line is `✓` only when `<r>` equals `<total>`; otherwise `○`.

The `Security entries` line appears only when the surface inventory has security entries. A
`NOT FIXED` there on a finding counted as `resolved` is a contradiction: move the finding to
`unresolved`.

---

## The re-audit line

Phase 3d re-runs the audit over the refactored target. It is mandatory, and its result always
occupies one line in `## Validation` — there is no case in which the line is omitted. Choose the
form by what the re-audit returned:

| Condition | Line |
|---|---|
| Complete re-audit, no findings at all | `✓ Zero anti-patterns remaining  (re-audit: 0 findings)` |
| Complete re-audit, findings remain | `○ Anti-patterns remaining: <k> proposed-not-applied, <u> unresolved  (re-audit: <m> findings)` |
| Some check could not run | `⚠ Re-audit partial — see Verification Coverage  (<m> findings over the checks that ran)` |

Rules that make the line mean something:

- **The first form is licensed only by evidence.** It asserts a universal negative — that nothing
  remains — which nothing but a complete re-audit returning zero can support. Having fixed every
  finding on the Phase 2 list does not license it: that list was never a proof of exhaustiveness.
- **One item under `PROPOSED, NOT APPLIED` rules the first form out.** Those findings are, by
  construction, anti-patterns that remain — the contract gate declined them deliberately and the
  report names them a few lines below. Printing "zero remaining" above that list would contradict
  the report within a single screen.
- **`unresolved` and `proposed-not-applied` are different facts and stay separate.** The second is
  a decision that was made on purpose and explained; the first is a transformation that failed or a
  problem the refactoring introduced. Collapsing them into one number hides the only one that
  needs action.
- **Every `unresolved` re-audit finding carries its origin**, listed under the Phase 3 block:
  `failed` (a Phase 2 finding the refactoring did not fully eliminate), `introduced` (created by
  the refactoring) or `missed-in-phase-2` (present in the original, absent from the Phase 2
  report). The last one measures the audit, not the refactoring; keep it visible and separate.
- **A partial re-audit never produces the first form**, whatever it found. Reduced coverage cannot
  support a claim about absence. `--offline` disables the live deprecated-API lookup, so any
  offline run is partial by definition.

This line is the strongest claim in the report and the cheapest to print. That is exactly why it is
the one that must be earned.
