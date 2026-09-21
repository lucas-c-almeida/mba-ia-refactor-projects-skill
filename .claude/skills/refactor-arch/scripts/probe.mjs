#!/usr/bin/env node
/**
 * probe.mjs -- reference implementation of references/06-validation-protocol.md
 *              for targets whose runtime is Node.
 *
 * Zero dependencies. Node 18+ built-ins only (global fetch, node:fs, node:process).
 * Never `npm install` anything to validate: the harness must not change the target's
 * dependency set.
 *
 * What it does
 * ------------
 *   capture   exercise a surface inventory against a RUNNING application, write a baseline
 *   compare   produce a current capture (live, or from a file) and diff it against a baseline
 *
 * What it deliberately does NOT do
 * --------------------------------
 *   - It never boots the application. Booting is stack-specific; probing is protocol-pure.
 *     The agent boots and waits for readiness, then calls this script.
 *   - It never compares values -- only status, media type and the recursive SHAPE of the body.
 *     Comparing ids, timestamps or ordering would produce a false regression on every run,
 *     and a noisy check is worse than no check: it costs the same and you stop reading it.
 *
 * Output is byte-compatible with probe.py: keys sorted, two-space indent. A baseline
 * captured by either implementation can be compared by the other.
 *
 * Usage
 * -----
 *   node probe.mjs capture --surface reports/surface.json \
 *                          --base-url http://127.0.0.1:8081 \
 *                          --out reports/baseline.json
 *
 *   node probe.mjs compare --surface reports/surface.json \
 *                          --baseline reports/baseline.json \
 *                          --base-url http://127.0.0.1:8081
 *
 *   node probe.mjs compare --baseline reports/baseline.json --current reports/after.json
 *
 * Exit codes: 0 = no regressions, 1 = at least one regression, 2 = usage or I/O error.
 */

import { readFileSync, writeFileSync } from 'node:fs';
import process from 'node:process';

const PROTOCOL_VERSION = 1;
const DEFAULT_TIMEOUT_SECONDS = 10;

// Result states (section 4 of the protocol).
const PASS = 'PASS';
const REGRESSION = 'REGRESSION';
const PRE_EXISTING_FAILURE = 'PRE-EXISTING FAILURE';
const UNVERIFIED = 'UNVERIFIED';

// ---------------------------------------------------------------------------
// Shape descriptor (protocol section 5)
//
// The descriptor captures the recursive set of keys and the type of each leaf,
// and nothing else. Array length and order are deliberately ignored: a collection
// whose row count depends on the datastore would otherwise fail on every run.
// ---------------------------------------------------------------------------

function shapeOf(value) {
  if (value === null || value === undefined) return 'null';
  const kind = typeof value;
  if (kind === 'boolean') return 'boolean';
  if (kind === 'number') return 'number';
  if (kind === 'string') return 'string';

  if (Array.isArray(value)) {
    if (value.length === 0) return { type: 'array', items: 'empty' };
    // Deduplicate element descriptors by canonical serialization, then sort, so two
    // captures of the same shape serialize identically.
    const seen = new Map();
    for (const element of value) {
      const descriptor = shapeOf(element);
      seen.set(canonical(descriptor), descriptor);
    }
    const distinct = [...seen.keys()].sort().map((key) => seen.get(key));
    return distinct.length === 1
      ? { type: 'array', items: distinct[0] }
      : { type: 'array', items: { oneOf: distinct } };
  }

  if (kind === 'object') {
    const properties = {};
    for (const key of Object.keys(value).sort()) properties[key] = shapeOf(value[key]);
    return { type: 'object', properties };
  }
  return 'unknown';
}

/** Deep key-sorted clone: makes JSON.stringify deterministic and matches probe.py. */
function sortKeysDeep(value) {
  if (Array.isArray(value)) return value.map(sortKeysDeep);
  if (value && typeof value === 'object') {
    const out = {};
    for (const key of Object.keys(value).sort()) out[key] = sortKeysDeep(value[key]);
    return out;
  }
  return value;
}

const canonical = (descriptor) => JSON.stringify(sortKeysDeep(descriptor));
const shapesEqual = (a, b) => canonical(a) === canonical(b);

const summary = (descriptor) =>
  typeof descriptor === 'string'
    ? descriptor
    : (descriptor?.type ?? (descriptor && 'oneOf' in descriptor ? 'oneOf' : '?'));

/**
 * Path-addressed differences between two descriptors.
 * Each diff is {kind, path, ...} with kind in {missing, added, typeChanged}.
 */
function shapeDiff(baseline, current, path = '$') {
  const diffs = [];

  if (typeof baseline === 'string' || typeof current === 'string') {
    if (!shapesEqual(baseline, current)) {
      diffs.push({ kind: 'typeChanged', path, from: summary(baseline), to: summary(current) });
    }
    return diffs;
  }

  const baselineKind = summary(baseline);
  const currentKind = summary(current);
  if (baselineKind !== currentKind) {
    diffs.push({ kind: 'typeChanged', path, from: baselineKind, to: currentKind });
    return diffs;
  }

  if (baselineKind === 'object') {
    const before = baseline.properties ?? {};
    const after = current.properties ?? {};
    for (const key of Object.keys(before).sort()) {
      if (!(key in after)) diffs.push({ kind: 'missing', path: `${path}.${key}` });
    }
    for (const key of Object.keys(after).sort()) {
      if (!(key in before)) diffs.push({ kind: 'added', path: `${path}.${key}` });
    }
    for (const key of Object.keys(before).sort()) {
      if (key in after) diffs.push(...shapeDiff(before[key], after[key], `${path}.${key}`));
    }
    return diffs;
  }

  if (baselineKind === 'array') {
    const before = baseline.items;
    const after = current.items;
    if (before === 'empty' || after === 'empty') {
      // An empty collection in one run and a populated one in the other is a data
      // difference, not a code difference. Report it, but as its own kind.
      if (before !== after) {
        diffs.push({
          kind: 'typeChanged', path: `${path}[]`, from: summary(before), to: summary(after),
        });
      }
      return diffs;
    }
    return shapeDiff(before, after, `${path}[]`);
  }

  if (!shapesEqual(baseline, current)) {
    diffs.push({ kind: 'typeChanged', path, from: baselineKind, to: currentKind });
  }
  return diffs;
}

// ---------------------------------------------------------------------------
// Exercising the surface (protocol section 3)
// ---------------------------------------------------------------------------

/** Media type only -- parameters such as charset are not part of the contract here. */
const normalizeContentType = (raw) => (raw ? raw.split(';')[0].trim().toLowerCase() : null);

async function exercise(baseUrl, entry, timeoutSeconds) {
  const id = entry.id ?? `${entry.method} ${entry.path}`;
  const method = (entry.method ?? 'GET').toUpperCase();
  const path = entry.path ?? '/';
  const record = {
    id, method, path,
    state: UNVERIFIED, status: null, contentType: null, shape: null, error: null,
  };

  if (entry.skip) {
    record.error = entry.skipReason ?? 'skipped by inventory';
    return record;
  }

  const headers = { ...(entry.headers ?? {}) };
  let body;
  if (entry.body !== undefined && entry.body !== null) {
    body = JSON.stringify(entry.body);
    if (!Object.keys(headers).some((h) => h.toLowerCase() === 'content-type')) {
      headers['Content-Type'] = 'application/json';
    }
  }

  // A harness must never hang: a hung probe is indistinguishable from a broken app.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutSeconds * 1000);
  try {
    const response = await fetch(baseUrl.replace(/\/+$/, '') + path, {
      method, headers, body, signal: controller.signal, redirect: 'manual',
    });
    const contentType = normalizeContentType(response.headers.get('content-type'));
    const text = await response.text();
    record.state = 'OBSERVED';
    record.status = response.status;   // a 4xx/5xx is a real response, not a transport failure
    record.contentType = contentType;
    record.shape = bodyShape(text, contentType);
  } catch (err) {
    record.error = `${err.name}: ${err.message}`;
  } finally {
    clearTimeout(timer);
  }
  return record;
}

function bodyShape(text, contentType) {
  if (!text) return 'empty';
  if (contentType && !contentType.includes('json')) return { type: 'opaque', bytes: 'present' };
  try {
    return shapeOf(JSON.parse(text));
  } catch {
    // Declared as JSON but unparseable, or an unknown content type that is not JSON.
    return { type: 'opaque', bytes: 'present' };
  }
}

async function capture(surface, baseUrl, timeoutSeconds) {
  const results = {};
  // Sequential on purpose: concurrency would change the application's observable
  // ordering and load, and the baseline must be reproducible.
  for (const entry of surface.entries ?? []) {
    const record = await exercise(baseUrl, entry, timeoutSeconds);
    results[record.id] = record;
  }
  return {
    version: PROTOCOL_VERSION,
    capturedAt: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
    baseUrl,
    results,
  };
}

// ---------------------------------------------------------------------------
// Comparison (protocol section 4)
// ---------------------------------------------------------------------------

/** A baseline entry that was already broken: transport error or a server error. */
const isFailure = (record) =>
  record.state !== 'OBSERVED' || (record.status !== null && record.status >= 500);

function compareOne(baseline, current) {
  if (!baseline) return { state: UNVERIFIED, details: ['not present in baseline'] };
  if (!current) return { state: UNVERIFIED, details: ['not exercised in replay'] };
  if (baseline.state !== 'OBSERVED') {
    return { state: UNVERIFIED, details: [`baseline unverified: ${baseline.error}`] };
  }
  if (current.state !== 'OBSERVED') {
    return isFailure(baseline)
      ? { state: PRE_EXISTING_FAILURE, details: [`failed before and after: ${current.error}`] }
      : { state: REGRESSION, details: [`call failed after refactoring: ${current.error}`] };
  }

  const sameStatus = baseline.status === current.status;
  const sameType = baseline.contentType === current.contentType;
  const diffs = shapesEqual(baseline.shape, current.shape)
    ? [] : shapeDiff(baseline.shape, current.shape);

  if (sameStatus && sameType && diffs.length === 0) {
    // Identical -- but if it was already broken, that is not a success. You neither
    // fixed it nor broke it, and the report must say exactly that.
    return isFailure(baseline)
      ? { state: PRE_EXISTING_FAILURE, details: [`unchanged failure: status ${baseline.status}`] }
      : { state: PASS, details: [] };
  }

  const details = [];
  if (!sameStatus) details.push(`statusChanged ${baseline.status} -> ${current.status}`);
  if (!sameType) details.push(`contentTypeChanged ${baseline.contentType} -> ${current.contentType}`);
  for (const diff of diffs) {
    details.push(diff.kind === 'typeChanged'
      ? `typeChanged ${diff.path}: ${diff.from} -> ${diff.to}`
      : `${diff.kind} ${diff.path}`);
  }

  // Already broken before, still broken in the same way -> neither pass nor regression.
  if (isFailure(baseline) && baseline.status === current.status) {
    return { state: PRE_EXISTING_FAILURE, details };
  }
  // Improvement is a behaviour change, so it is named rather than hidden -- but it is
  // not a regression.
  if (isFailure(baseline) && !isFailure(current)) {
    return { state: PASS, details: [`improved from ${baseline.status}`, ...details] };
  }
  return { state: REGRESSION, details };
}

function compare(baselineDoc, currentDoc) {
  const baselineResults = baselineDoc.results ?? {};
  const currentResults = currentDoc.results ?? {};
  const ids = [...new Set([...Object.keys(baselineResults), ...Object.keys(currentResults)])].sort();
  return ids.map((id) => ({
    id, ...compareOne(baselineResults[id], currentResults[id]),
  }));
}

// ---------------------------------------------------------------------------
// I/O and CLI
// ---------------------------------------------------------------------------

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

function writeJson(path, document) {
  writeFileSync(path, `${JSON.stringify(sortKeysDeep(document), null, 2)}\n`, 'utf8');
}

/** Minimal --flag value parser: no dependency, no surprises. */
function parseArgs(argv) {
  const options = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) options[key] = true;
    else { options[key] = next; i += 1; }
  }
  return options;
}

function printTable(rows) {
  const width = Math.max(4, ...rows.map((row) => row.id.length));
  for (const row of rows) {
    console.log(`  ${row.id.padEnd(width)}  ${row.state}`);
    for (const detail of row.details) console.log(`  ${' '.repeat(width)}    - ${detail}`);
  }
}

function summarize(rows) {
  const counts = { [PASS]: 0, [REGRESSION]: 0, [PRE_EXISTING_FAILURE]: 0, [UNVERIFIED]: 0 };
  for (const row of rows) counts[row.state] = (counts[row.state] ?? 0) + 1;
  console.log('');
  console.log(`  ${counts[PASS]} PASS, ${counts[REGRESSION]} REGRESSION, `
    + `${counts[PRE_EXISTING_FAILURE]} PRE-EXISTING FAILURE, ${counts[UNVERIFIED]} UNVERIFIED`);
  return counts;
}

const USAGE = `Baseline-then-replay surface probe (see 06-validation-protocol.md).
This script never boots the application.

  node probe.mjs capture --surface <path> --base-url <url> --out <path> [--timeout <seconds>]
  node probe.mjs compare --baseline <path> [--surface <path> --base-url <url>]
                         [--current <path>] [--out <path>] [--timeout <seconds>]`;

async function main() {
  const [mode, ...rest] = process.argv.slice(2);
  const options = parseArgs(rest);
  const timeout = Number(options.timeout ?? DEFAULT_TIMEOUT_SECONDS);

  if (mode !== 'capture' && mode !== 'compare') {
    console.error(USAGE);
    return 2;
  }

  try {
    if (mode === 'capture') {
      if (!options.surface || !options['base-url'] || !options.out) {
        console.error('capture needs --surface, --base-url and --out');
        return 2;
      }
      const document = await capture(readJson(options.surface), options['base-url'], timeout);
      writeJson(options.out, document);
      const records = Object.values(document.results);
      const observed = records.filter((r) => r.state === 'OBSERVED').length;
      console.log(`captured ${records.length} entries (${observed} observed, `
        + `${records.length - observed} unverified) -> ${options.out}`);
      return 0;
    }

    if (!options.baseline) {
      console.error('compare needs --baseline');
      return 2;
    }
    const baselineDoc = readJson(options.baseline);

    let currentDoc;
    if (options.current) {
      currentDoc = readJson(options.current);
    } else if (options['base-url'] && options.surface) {
      currentDoc = await capture(readJson(options.surface), options['base-url'], timeout);
      if (options.out) writeJson(options.out, currentDoc);
    } else {
      console.error('compare needs either --current, or both --base-url and --surface');
      return 2;
    }

    const rows = compare(baselineDoc, currentDoc);
    if (rows.length === 0) {
      console.error('nothing to compare: the inventory produced no entries');
      return 2;
    }
    printTable(rows);
    return summarize(rows)[REGRESSION] > 0 ? 1 : 0;
  } catch (err) {
    console.error(`probe: ${err.message}`);
    return 2;
  }
}

// Set the exit code and let the event loop drain, rather than calling process.exit():
// a hard exit while fetch's sockets are still closing aborts the runtime on some platforms.
process.exitCode = await main();
