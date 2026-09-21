# Run log — `/refactor-arch <target> --yes` on ecommerce-api-legacy

- Date: 2026-09-21, 17:23–17:47 local (UTC-3)
- Target (absolute): `C:/Users/lucas/AppData/Local/Temp/claude/D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill/39497ea2-c2b4-400b-8a75-c45be41b239f/scratchpad/round2/ecommerce-api-legacy`
- Target git state at start: branch `main`, clean at `1f550f1 original`. No git command other than `status`/`log`/`diff`/`rev-parse` was run; nothing staged or committed.
- Snapshot directory (skill-mandated scratch): `<scratchpad>/refactor-arch-ecommerce-api-legacy-20260921-1723/` — deleted at the end of Phase 3.
- Outputs in the target: `reports/audit-20260921-1731.md` (Phase 2), `reports/audit-latest.md` (Phase 2 + appended Phase 3 final report), `reports/surface.json`, `reports/baseline.json`, `reports/replay.json`.

---

## 1. Blocks as printed

### Phase 1

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Target:        C:/Users/lucas/AppData/Local/Temp/claude/D--Study-MBA-FullCycle-mba-ia-refactor-projects-skill/39497ea2-c2b4-400b-8a75-c45be41b239f/scratchpad/round2/ecommerce-api-legacy (absolute — the target is on another drive than the CWD, no relative path exists)
Language:      JavaScript (Node.js; runtime present: v24.12.0; no "engines" field)
Framework:     Express 4.22.1 (resolved from package-lock.json; manifest range ^4.18.2)
Dependencies:  runtime: express ^4.18.2 (4.22.1), sqlite3 ^5.1.6 (5.1.7); dev: none
Domain:        LMS course sales — checkout (account + payment + enrollment), admin financial report, user deletion
App type:      HTTP service — 3 routes: POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id
Architecture:  None — one class (AppManager) holds schema/seed, routing, business rules and persistence; utils.js is a grab-bag of config, secrets, cache and hashing
Source files:  3 files analyzed (src/*.js; excluded: .git, .claude/, node_modules (absent), lockfile, docs; no .gitignore present)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite, in-memory, DDL + seed at boot)
================================
```

Recorded for Phase 3 (not part of the block format): boot command `npm start` → `node src/app.js`,
working directory = project root, no required env, port fixed in source (`src/utils.js` `config.port = 3000`,
no override read). Largest file: src/AppManager.js (141 of 180 lines).

### Phase 2 (summary + total)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js v24.12.0) + Express 4.22.1 (resolved from package-lock.json; manifest ^4.18.2) + sqlite3 5.1.7
Files:   3 analyzed | ~140 lines of code (180 physical lines)
Date:    2026-09-21 17:31
Mode:    full
Confirmation: --yes (auto-approved, not human-reviewed)
Tree:    clean at 1f550f1
Runtime: installed the declared dependencies from package-lock.json (`npm ci`) into <snapshot>/deps/node_modules, outside the target; run copies resolve them through NODE_PATH

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 4 | LOW: 3

[CRITICAL] God Module / God Class (AP-03)                         src/AppManager.js:4-141
[CRITICAL] Business Logic in the Delivery Layer (AP-05, escalated) src/AppManager.js:28-78
[CRITICAL] Card number + gateway key logged (AP-08, escalated)     src/AppManager.js:45-45
[CRITICAL] Swallowed/uncentralized errors (AP-09, escalated)       src/AppManager.js:50-63
[CRITICAL] Missing authorization (AP-04)                           src/AppManager.js:131-137
[CRITICAL] Hardcoded secrets (AP-01)                               src/utils.js:1-7
[CRITICAL] Password storage (AP-08, escalated)                     src/utils.js:17-23
[HIGH]     sqlite3 deprecated upstream + install-time advisories (AP-19)  package.json:9-9
[HIGH]     Hard-wired dependencies / no composition root (AP-06)   src/AppManager.js:5-8
[HIGH]     Wrong-typed input crashes the process (AP-11, escalated) src/AppManager.js:29-35
[HIGH]     Default error page leaks stack trace (AP-18)            src/app.js:5-10
[MEDIUM]   express transitive advisories, unreachable (AP-19, de-escalated) package.json:8-8
[MEDIUM]   N+1 in financial report (AP-10)                         src/AppManager.js:83-128
[MEDIUM]   Deletion leaves orphaned records (AP-11)                src/AppManager.js:133-135
[MEDIUM]   Write-only global cache (AP-07, de-escalated)           src/utils.js:9-15
[LOW]      Misleading names (AP-16)                                src/AppManager.js:29-33
[LOW]      Magic values (AP-15)                                    src/AppManager.js:46-48
[LOW]      Dead code (AP-17)                                       src/utils.js:2-5

================================
Total: 18 findings
================================

Phase 2 complete. --yes was passed: the confirmation prompt is skipped and Phase 3 proceeds as `y`
(apply all findings; contract-changing items will be proposed, not applied).
```

(The full report, with Description/Impact/Recommendation/Contract per finding, the Catalog Coverage
table and the Dependency verification table, is in `reports/audit-20260921-1731.md`.)

### Phase 3

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
ecommerce-api-legacy/
├── .env.example
├── .gitignore
├── api.http
├── package.json
├── package-lock.json
├── README.md
├── reports/
│   ├── audit-20260921-1731.md
│   ├── audit-latest.md
│   ├── baseline.json
│   ├── replay.json
│   └── surface.json
└── src/
    ├── app.js                      composition root
    ├── config/
    │   └── index.js
    ├── controllers/
    │   ├── checkoutController.js
    │   ├── reportController.js
    │   └── userController.js
    ├── middlewares/
    │   └── errorBoundary.js
    ├── models/
    │   ├── database.js
    │   ├── errors.js
    │   ├── password.js
    │   ├── payment.js
    │   ├── repositories.js
    │   └── schema.js
    └── routes/
        ├── adminRoutes.js
        └── checkoutRoutes.js

## Validation
  ✓ Application boots without errors
  ✓ Public surface replayed: 13 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED
    Security entries: 3 FIXED, 0 NOT FIXED
  ○ Findings resolved: 14/18  (4 proposed, 0 unresolved)
  ○ Anti-patterns remaining: 4 proposed-not-applied, 1 unresolved  (re-audit: 5 findings)

## Proposed, Not Applied
[CRITICAL] AP-04 Missing authorization — no identity model; any auth rejects every current client.
[CRITICAL] AP-08 Password storage — KDF + hashed seed applied; the "123456" fallback for accounts
           created without pwd held back (would make pwd required).
[HIGH]     AP-19 sqlite3 — upgraded 5.1.7 → 6.0.1 (0 advisories, replay passed); replacing the
           deprecated/archived driver held back (upstream names no successor; node:sqlite is experimental here).
[MEDIUM]   AP-11 Orphaned records on delete — any policy changes the report / DELETE body.
(full entries with File / Reason not applied / Proposed change in reports/audit-latest.md)

## Verification Coverage
Full — every planned check ran (Layer 1 forced-deprecation runs of original and refactored app; Layer 2
OSV/npm registry/npm audit/upstream repo in Phase 2 and in the re-audit; 16/16 inventory entries
captured and replayed, none skipped). Notes: AP-18 fix verified manually with curl (harness cannot send
a malformed body); text bodies compared as masked skeletons (06 §5.1–5.2); values additionally
compared outside the protocol — identical except the report's array order, which the original did
not guarantee; 2 crash entries recaptured per 06 §3.1; 2 late entries captured against the original
per 06 §4.3.
Snapshot directory deleted at the end of Phase 3.
================================
```

Re-audit unresolved item: [MEDIUM] AP-11 `src/models/schema.js:9-9` — `users.email` not unique;
look-up-then-insert at `src/controllers/checkoutController.js:44-47` lets concurrent checkouts create
duplicate accounts. Origin: `missed-in-phase-2` (same pattern in the original, AppManager.js:40-72).

---

## 2. Commands, ports, setup, harness — with outcomes

All boots used port **5211** only (checked free with `netstat -ano | grep ":5211 .*LISTEN"` before
every boot; confirmed free after every shutdown). Ports 5212–5219 were not used.
`<SN>` = `<scratchpad>/refactor-arch-ecommerce-api-legacy-20260921-1723`, `<T>` = target, `<P>` = `<T>/.claude/skills/refactor-arch/scripts/probe.mjs`.

### Snapshot and dependency setup
| Command | Outcome |
|---|---|
| `tar --exclude=./.git -cf - . \| (cd <SN>/pristine && tar -xf -)` (from `<T>`) | pristine snapshot (no `.git`) |
| `cp package.json package-lock.json <SN>/deps/ && cd <SN>/deps && npm ci --no-audit --no-fund` | 191 packages; npm warned deprecated prebuild-install, gauge, tar; sqlite3 prebuilt binary installed fine on Node 24 |
| `cp -r <SN>/pristine <SN>/run-N` for each execution of the original (run-1 … run-6) | fresh run copy per execution |
| `<SN>/launch.js` (out-of-tree launcher, 06 §1.2 option 3): `require(<run>/src/utils.js).config.port = <port>; require(<run>/src/app.js)` | worked; the original's source was not edited |

### Phase 2 — Layer 1 and error-behaviour observation (original, run-1)
`NODE_PATH=<SN>/deps/node_modules node --pending-deprecation --trace-deprecation --trace-warnings launch.js run-1 5211`
- No deprecation warning emitted at boot or on any exercised route.
- `curl -X POST /api/checkout -H 'Content-Type: application/json' -d '{bad'` → 400 text/html with the full stack trace and absolute paths (AP-18 evidence).
- `curl … -d '{"usr":"G","eml":"h@x.com","c_id":1,"card":4111}'` → no response; process exited with `TypeError: cc.startsWith is not a function` (AP-11 evidence). Log also showed `Processando cartão 4111222233334444 na chave pk_live_…` (AP-08 evidence).

### Phase 2 — Layer 2 lookups (2026-09-21)
| Command | Outcome |
|---|---|
| `npm view express@4.22.1 deprecated`, `npm view sqlite3@5.1.7 deprecated` | empty (not flagged) |
| `npm view express dist-tags`, `npm view sqlite3 dist-tags`, `npm outdated` | express latest-4 4.22.3 / latest 5.2.1; sqlite3 latest 6.0.1 |
| `npm audit --json` (in `<SN>/deps`) | 12 vulns (1 critical, 7 high, 1 moderate, 3 low): tar/node-gyp chain under sqlite3; path-to-regexp, qs, body-parser under express |
| `POST https://api.osv.dev/v1/query` for express 4.22.1, sqlite3 5.1.7, path-to-regexp 0.1.12, qs 6.14.2, body-parser 1.20.4 | express/sqlite3: none; path-to-regexp GHSA-37ch-88jc-xwx2; qs GHSA-4mjr-xmp4-gh2g, GHSA-x5fp-wj9c-mxmx, GHSA-q8mj-m7cp-5q26; body-parser GHSA-v422-hmwv-36x6 |
| `GET https://api.osv.dev/v1/vulns/<id>` for the three express-side advisories | details used for the reachability analysis (all unreachable in this app) |
| `grep` in `node_modules/express/lib/utils.js`, `body-parser/lib/types/json.js` | express qs.parse uses only `allowPrototypes`; json limit defaults to 100kb |
| GitHub API releases + raw README of TryGhost/node-sqlite3; repo metadata | README "[DEPRECATED] … unmaintained", `archived: true`; v6.0.0 notes "Mark repository as unmaintained" (Tier C) |
| `node -e "require('node:sqlite')"` | module present; ExperimentalWarning on v24.12.0 |

### Phase 3a — baseline (original)
| Step | Command | Outcome |
|---|---|---|
| boot | `NODE_PATH=<SN>/deps/node_modules node launch.js run-2 5211` (readiness: poll `GET /api/unknown` every 0.25 s, ≤10 s) | ready |
| capture | `node <P> capture --surface <T>/reports/surface.json --base-url http://127.0.0.1:5211 --out <T>/reports/baseline.json` | 14 entries: 12 OBSERVED, 2 ERROR; process exited on `post-api-checkout-card-wrong-type` (crash) |
| §3.1 recapture | fresh run-3; `… capture … --only post-api-checkout-pwd-wrong-type --merge` | ERROR again, process exited with `ERR_INVALID_ARG_TYPE` (Buffer.from(number)) — genuine crash, kept |
| manual AP-18 | on run-3 before the recapture: `curl -X POST … -d '{bad'` | 400 text/html, body contains `node_modules` paths |
| §4.3 late entry 1 | fresh run-4; `… capture … --only post-api-checkout-without-json-body --merge` | OBSERVED 400 "Bad Request" |
| §4.3 late entry 2 | fresh run-6; `… capture … --only post-api-checkout-email-wrong-type --merge` | OBSERVED 200 (original accepted an object as email) |
| shutdown | `taskkill //F //PID <pid on :5211>` | port free |

### Phase 3b — dependency changes
| Command | Outcome |
|---|---|
| `npm install express@4.22.3 sqlite3@6.0.1 --save --package-lock-only --no-audit --no-fund` (in `<T>`) | package.json ^4.22.3 / ^6.0.1; lockfile regenerated; no node_modules created in the target |
| `cp package.json package-lock.json <SN>/deps-new/ && npm ci --no-fund` | 123 packages; `npm audit`: 0 vulnerabilities; bundled SQLite 3.52.0 |

### Phase 3c — replay (refactored, in `<T>`)
Boot: `PORT=5211 NODE_PATH=<SN>/deps-new/node_modules node --pending-deprecation --trace-deprecation [--trace-warnings] src/app.js` (cwd `<T>`).
| Run | Harness command | Outcome |
|---|---|---|
| replay-1 | `node <P> compare --surface … --baseline … --base-url http://127.0.0.1:5211 --out <SN>/replay-1.json` | 13 PASS, 0 REGRESSION; 2 FIXED. Log revealed the error boundary logging the raw request body of a malformed JSON request → fixed (log stack/type only) |
| replay-2 | same, `--out <T>/reports/replay.json` | 13 PASS, 0 REGRESSION; 2 FIXED |
| values check (outside protocol) | `<SN>/values.mjs` replaying contract entries against fresh original run-5 and the refactored app, diffing bodies | identical except report array order |
| (fix) | extended boundary schema to usr/eml types; added `post-api-checkout-email-wrong-type`, captured against original first | — |
| replay-final | same, `--out <T>/reports/replay.json` | **13 PASS, 0 REGRESSION, 0 PRE-EXISTING FAILURE, 0 UNVERIFIED; security 3 FIXED, 0 NOT FIXED; exit 0**; no deprecation warning; manual `{bad` → 400 "Bad Request", log line `POST /api/checkout: 400 entity.parse.failed` |

### Phase 3d — re-audit dependency checks
`npm view express@4.22.3 deprecated` / `sqlite3@6.0.1 deprecated` → empty; OSV for both → `{}`; `npm audit --omit=dev` → 0; lockfile `deprecated` fields → only `prebuild-install@7.1.3`; `npm outdated` → express 5.2.1 available (major, not pursued). Code re-audit by catalog sweep over the 14 new source files.

Snapshot deletion: `rm -rf <SN>` → confirmed gone.

---

## 3. Skill friction

1. **SKILL.md, Phase 1 block, `Target: <path relative to CWD>`.** The target is on a different drive (C:) than the CWD (D:), so no relative path exists. Printed the absolute path with a note.
2. **06-validation-protocol.md §1.2, option 3 ("a launcher … that imports the application's entry object and binds it to a chosen port").** The original's entry exports nothing and calls `listen` as an import side effect; there is no entry object to bind. Options 1 (no override exists) and 2 (native port 3000 was outside the permitted 5211–5219) did not apply. Improvised: the out-of-tree launcher pre-loads the original's own config module and sets `config.port` on the exported (mutable) object before requiring the entry. This only worked because the port lived in a mutable exported object; the protocol has no rule for an entry that binds at import and exposes no seam.
3. **01-project-analysis.md §6 "Runtime environment" + SKILL.md 3c.1 ("Boot the refactored application, in `<target>`").** Dependencies may only be installed in the snapshot's run copy or a `.gitignore`-excluded location; the target had no `.gitignore`, and the refactored app must run inside the target. The skill does not say how the refactored app gets its dependencies. Used `NODE_PATH` pointing at a dependency directory inside the snapshot (`deps`, and `deps-new` after the upgrade) so nothing was installed into the target. Also installed once into a shared `<SN>/deps` instead of per run copy (06 §1.1 allows linking; NODE_PATH is a link in effect).
4. **Dependency upgrades in Phase 3 need a second install; not described.** After RP-18 regenerated the lockfile, the replay needs the new resolved versions. Created `<SN>/deps-new` from the new lockfile. Also 3c.6 deletes the snapshot **before** 3d, but the re-audit's Layer 1 (a forced-deprecation run of the refactored app) needs those installed dependencies — I ran the re-audit checks first and deleted the snapshot afterwards.
5. **02-antipattern-catalog.md AP-14 "Severity follows impact" / overlap rule.** It says a package that is deprecated *and* has an advisory is reported once as AP-19 because "the advisory is the dominant impact". Here the advisories were install-time only (LOW per AP-19) while the deprecation of the only database driver was the dominant impact (HIGH). Reported once under AP-19 as the rule says, with the severity driven by the deprecation, and said so in the finding.
6. **AP-14 "Every finding … must state the modern equivalent … named by the upstream source you cited".** The upstream (sqlite3 README) names no successor, so this was impossible to satisfy literally. Named `node:sqlite` as a candidate, marked as not upstream-named, with the observed ExperimentalWarning. RP-14 step 5 ("deprecated with no successor → propose") covered the Phase 3 action, but the catalog rule and the playbook step disagree on what the finding must contain.
7. **06 §2 / §2.1 and probe.mjs — the harness cannot express the AP-18 fix.** probe.mjs always JSON-encodes `body`, so a malformed-body request cannot be an entry. The fix's effect (no internals in a 400 body) is not a rejection, so it cannot be a security entry either; as a contract entry it would show as `REGRESSION` (textChanged), which §2.1 says is the wrong label. Verified by hand with curl before and after, and declared in Verification Coverage.
8. **04-architecture-guidelines.md §6 vs RP-17.** §6 lists "changing the error response shape" as contract-changing; RP-17 says replacing the framework's default error output with the centralized handler (same status) is safe. I followed RP-17 because it is the more specific rule.
9. **probe.mjs messages.** The crash warning cites "protocol 3.2", but the section is §3.1. With `--merge`, the "several transport errors" warning counts ERRORs already in the merged file, so it fires even when the current run had none, which is misleading.
10. **SKILL.md gate vs 03-report-template.md "With `--yes`, do not print the prompt".** SKILL.md says to print the Total block and the prompt, then describes the `--yes` behaviour. I printed the Total block and replaced the prompt with a one-line `--yes` notice.
11. **Where the Phase 3 report goes.** 03 says it is "appended to `audit-latest.md`". That leaves the timestamped file as Phase-2-only while `audit-latest.md` is no longer a copy of it. I followed the instruction, but whether the timestamped file should also get the Phase 3 section is unspecified.
12. **Phase 1 "Record the exact boot command, its working directory, environment and port in the Phase 1 output"** (01 §6). The Phase 1 block format has no field for these. I recorded them right under the block.
13. **05 playbook method "re-run the validation harness after each meaningful step".** SKILL.md 3c has a single replay step after the refactoring. Since the original was a single file, I rewrote it in one pass and replayed three times at the end rather than after each transformation (see §4).
14. **Partial fixes discovered during validation vs. 3d.** After replay-1 I noticed that my AP-11 fix covered only card/pwd, while the finding's recommendation said "string fields must be strings". Left alone, the finding would have been `unresolved (failed)`. The skill does not say whether to go on fixing after the first replay. I fixed it, added a security entry captured against the original (§4.3), and replayed again. For the re-audit's `missed-in-phase-2` item (email uniqueness), I reported it without fixing, because 3d only says to report.

## 4. Deviations: done without instruction / instructed but skipped

Done without instruction:
- Compared response **values** (not only shapes) between original and refactored with a scratch script (`<SN>/values.mjs`, deleted with the snapshot). The protocol compares only shapes.
- Used `--trace-warnings` in addition to the Layer 1 flags.
- Queried GitHub (releases API, raw README, repo metadata) to establish the sqlite3 Tier C evidence, and fetched OSV advisory details for the reachability argument.
- Added `.gitignore` (node_modules, .env) and `.env.example` under RP-01, and deleted three dead config members plus the only-logged gateway key instead of moving them to env.
- **Operational-constraint slips (outside target/snapshot):** (a) during the run-3 manual check, a curl response body was written to `/tmp/x` and deleted right away; (b) the Phase 3 report section was staged in `<scratchpad>/round2/phase3-append.md`, appended to `audit-latest.md`, and deleted right away. Neither file remains.

Instructed but skipped or reduced:
- Harness re-run after each transformation (05 method): replayed at the end only (three times), not per transformation.
- `sqlite3.verbose()` (the original's verbose-trace mode) was dropped in the new composition root. It is a debugging aid with no client-observable effect; I did not file it as a finding.
- The re-audit's unresolved `missed-in-phase-2` finding (email uniqueness) was reported and not fixed.
