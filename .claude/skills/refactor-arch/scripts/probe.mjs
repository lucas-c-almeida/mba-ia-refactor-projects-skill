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
 *   - It never compares raw values -- only status, media type, a small allow-list of contract
 *     headers, and the recursive SHAPE of the body. Comparing ids, timestamps or ordering would
 *     produce a false regression on every run, and a noisy check is worse than no check.
 *   - It never follows redirects. A redirect is part of the contract.
 *
 * Output is byte-compatible with probe.py: keys sorted by code point, two-space indent, LF.
 * A baseline captured by either implementation can be compared by the other; the shared
 * conformance test (tests/probe-conformance at the repository root) holds them to that.
 *
 * Usage
 * -----
 *   node probe.mjs capture --surface reports/surface.json \
 *                          --base-url http://127.0.0.1:8081 \
 *                          --out reports/baseline.json
 *
 *   # capture only entries added after the baseline, against the ORIGINAL, into the same file
 *   node probe.mjs capture --surface reports/surface.json --base-url http://127.0.0.1:8081 \
 *                          --out reports/baseline.json --only new-entry-a,new-entry-b --merge
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

const PROTOCOL_VERSION = 2;
const DEFAULT_TIMEOUT_SECONDS = 10;
const TEXT_LIMIT_BYTES = 4096;

// Record states (section 3 of the protocol).
const OBSERVED = 'OBSERVED';   // the call completed and a response was read
const ERROR = 'ERROR';         // the call was made and failed at transport level
const SKIPPED = 'SKIPPED';     // the call was never made

// Result states (section 4 of the protocol).
const PASS = 'PASS';
const REGRESSION = 'REGRESSION';
const PRE_EXISTING_FAILURE = 'PRE-EXISTING FAILURE';
const UNVERIFIED = 'UNVERIFIED';
const FIXED = 'FIXED';
const NOT_FIXED = 'NOT FIXED';

// Value masks (protocol section 5.2), applied in this order. ASCII classes only, so that
// every implementation masks exactly the same characters.
const MASKS = [
  [/[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?/g, '<ts>'],
  [/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g, '<uuid>'],
  [/(?<![0-9A-Za-z])[0-9a-fA-F]{16,}(?![0-9A-Za-z])/g, '<hex>'],
  [/[0-9]+/g, '<n>'],
];

// Contract headers (protocol section 5.3). Everything else is transport detail.
const HEADER_EXACT = new Set(['location', 'www-authenticate']);
const HEADER_PREFIX = 'access-control-';
const HEADER_LISTS = new Set([
  'access-control-allow-methods', 'access-control-allow-headers', 'access-control-expose-headers',
]);

const mask = (text) => MASKS.reduce((acc, [pattern, placeholder]) => acc.replace(pattern, placeholder), text);

// ---------------------------------------------------------------------------
// Canonical serialization
//
// Python sorts strings by code point; JS sorts by UTF-16 unit, and JS objects put
// integer-like keys first whatever their insertion order. Both would break byte
// compatibility, so ordering and serialization are done by hand.
// ---------------------------------------------------------------------------

function byCodePoint(a, b) {
  const x = Array.from(a, (c) => c.codePointAt(0));
  const y = Array.from(b, (c) => c.codePointAt(0));
  for (let i = 0; i < Math.min(x.length, y.length); i += 1) {
    if (x[i] !== y[i]) return x[i] - y[i];
  }
  return x.length - y.length;
}

function serialize(value, indent = 0, level = 0) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value ?? null);
  const pad = indent ? `\n${' '.repeat(indent * (level + 1))}` : '';
  const end = indent ? `\n${' '.repeat(indent * level)}` : '';
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    return `[${value.map((v) => pad + serialize(v, indent, level + 1)).join(',')}${end}]`;
  }
  const keys = Object.keys(value).sort(byCodePoint);
  if (keys.length === 0) return '{}';
  const sep = indent ? ': ' : ':';
  return `{${keys.map((k) => pad + JSON.stringify(k) + sep + serialize(value[k], indent, level + 1)).join(',')}${end}}`;
}

const canonical = (descriptor) => serialize(descriptor);
const shapesEqual = (a, b) => canonical(a) === canonical(b);

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
    const distinct = [...seen.keys()].sort(byCodePoint).map((key) => seen.get(key));
    return distinct.length === 1
      ? { type: 'array', items: distinct[0] }
      : { type: 'array', items: { oneOf: distinct } };
  }

  if (kind === 'object') {
    // Null prototype: a body key named "__proto__" must stay an ordinary key.
    const properties = Object.create(null);
    for (const key of Object.keys(value)) properties[key] = shapeOf(value[key]);
    return { type: 'object', properties };
  }
  return 'unknown';
}

/** Skeleton of a short text body: distinct non-empty lines, masked, sorted. */
function textShape(text) {
  const lines = new Set();
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.replace(/[ \t\r\f\v]+$/, '');   // ASCII whitespace only: identical in Python
    if (line) lines.add(mask(line));
  }
  return { type: 'text', lines: [...lines].sort(byCodePoint) };
}

const summary = (descriptor) => {
  if (typeof descriptor === 'string') return descriptor;
  if (descriptor === null || descriptor === undefined) return 'none';
  return descriptor.type ?? ('oneOf' in descriptor ? 'oneOf' : '?');
};

/**
 * Path-addressed differences between two descriptors.
 * Each diff is {kind, path, ...} with kind in {missing, added, typeChanged, textChanged}.
 */
function shapeDiff(baseline, current, path = '$') {
  const diffs = [];

  if (typeof baseline === 'string' || typeof current === 'string'
      || baseline === null || baseline === undefined || current === null || current === undefined) {
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
    const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
    for (const key of Object.keys(before).sort(byCodePoint)) {
      if (!has(after, key)) diffs.push({ kind: 'missing', path: `${path}.${key}` });
    }
    for (const key of Object.keys(after).sort(byCodePoint)) {
      if (!has(before, key)) diffs.push({ kind: 'added', path: `${path}.${key}` });
    }
    for (const key of Object.keys(before).sort(byCodePoint)) {
      if (has(after, key)) diffs.push(...shapeDiff(before[key], after[key], `${path}.${key}`));
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

  if (baselineKind === 'text') {
    const before = new Set(baseline.lines ?? []);
    const after = new Set(current.lines ?? []);
    const removed = [...before].filter((l) => !after.has(l)).sort(byCodePoint);
    const added = [...after].filter((l) => !before.has(l)).sort(byCodePoint);
    if (removed.length || added.length) diffs.push({ kind: 'textChanged', path, removed, added });
    return diffs;
  }

  if (!shapesEqual(baseline, current)) {
    diffs.push({ kind: 'typeChanged', path, from: baselineKind, to: currentKind });
  }
  return diffs;
}

/** Differences in the contract headers. Skipped when either side did not record them. */
function headersDiff(baseline, current) {
  if (!baseline || !current) return [];
  const details = [];
  const names = [...new Set([...Object.keys(baseline), ...Object.keys(current)])].sort(byCodePoint);
  for (const name of names) {
    if (!(name in current)) details.push(`headerMissing ${name}`);
    else if (!(name in baseline)) details.push(`headerAdded ${name}`);
    else if (baseline[name] !== current[name]) {
      details.push(`headerChanged ${name}: ${baseline[name]} -> ${current[name]}`);
    }
  }
  return details;
}

// ---------------------------------------------------------------------------
// Exercising the surface (protocol section 3)
// ---------------------------------------------------------------------------

/** Media type only -- parameters such as charset are not part of the contract here. */
const normalizeContentType = (raw) => (raw ? raw.split(';')[0].trim().toLowerCase() : null);

/** The allow-listed headers of a response, normalized and masked (protocol 5.3). */
function contractHeaders(headers) {
  const collected = new Map();
  for (const [name, value] of headers) {
    if (name === 'set-cookie') continue;
    if (HEADER_EXACT.has(name) || name.startsWith(HEADER_PREFIX)) {
      collected.set(name, [...(collected.get(name) ?? []), value]);
    }
  }
  const result = {};
  for (const [name, values] of collected) {
    let joined = values.join(', ');
    if (HEADER_LISTS.has(name)) {
      const parts = new Set(joined.split(',').map((p) => p.trim().toLowerCase()).filter(Boolean));
      joined = [...parts].sort(byCodePoint).join(', ');
    }
    result[name] = mask(joined.trim());
  }
  const cookies = typeof headers.getSetCookie === 'function'
    ? headers.getSetCookie()
    : (headers.get('set-cookie') ?? '').split(/,(?=\s*[^;,=\s]+=)/).filter(Boolean);
  const names = new Set(cookies.filter((c) => c.includes('=')).map((c) => c.split('=')[0].trim()));
  if (names.size) result['set-cookie'] = [...names].sort(byCodePoint).join(', ');
  return result;
}

function bodyShape(bytes) {
  if (bytes.byteLength === 0) return 'empty';
  let text;
  try {
    // fatal: reject invalid UTF-8 as Python's strict decode does; ignoreBOM: keep it, as Python does.
    text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    return { type: 'opaque', bytes: 'present' };
  }
  try {
    return shapeOf(JSON.parse(text));
  } catch {
    // Not JSON (or declared JSON but unparseable): fall through to the text skeleton.
  }
  if (bytes.byteLength <= TEXT_LIMIT_BYTES) return textShape(text);
  return { type: 'opaque', bytes: 'present' };
}

async function exercise(baseUrl, entry, timeoutSeconds) {
  const id = entry.id ?? `${entry.method} ${entry.path}`;
  const method = (entry.method ?? 'GET').toUpperCase();
  const path = entry.path ?? '/';
  const record = {
    id, method, path, kind: entry.kind ?? 'contract', finding: entry.finding ?? null,
    state: SKIPPED, status: null, contentType: null, headers: null, shape: null, error: null,
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
    const bytes = new Uint8Array(await response.arrayBuffer());
    record.state = OBSERVED;
    record.status = response.status;   // a 3xx/4xx/5xx is a real response, not a transport failure
    record.contentType = normalizeContentType(response.headers.get('content-type'));
    record.headers = contractHeaders(response.headers);
    record.shape = bodyShape(bytes);
  } catch (err) {
    record.state = ERROR;             // refused, reset, timeout, truncated body
    record.error = `${err.name}: ${err.cause?.code ?? err.message}`;
  } finally {
    clearTimeout(timer);
  }
  return record;
}

/** Contract entries first, security entries last: a hostile call may mutate state. */
function orderedEntries(surface, only) {
  const entries = (surface.entries ?? []).filter((e) => !only || only.has(e.id));
  const isSecurity = (e) => (e.kind ?? 'contract') === 'security';
  return [...entries.filter((e) => !isSecurity(e)), ...entries.filter(isSecurity)];
}

async function capture(surface, baseUrl, timeoutSeconds, only) {
  const results = {};
  // Sequential on purpose: concurrency would change the application's observable
  // ordering and load, and the baseline must be reproducible.
  for (const entry of orderedEntries(surface, only)) {
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

/**
 * Protocol v1 used one state, UNVERIFIED, for "skipped" and "transport error" and cannot
 * tell them apart. Treat it as skipped: the v1 reading, and the one that claims nothing.
 */
const stateOf = (record) => (record.state === 'UNVERIFIED' ? SKIPPED : record.state);
const serverError = (record) => stateOf(record) === OBSERVED && (record.status ?? 0) >= 500;
const isFailure = (record) => stateOf(record) === ERROR || serverError(record);
const rejected = (record) => stateOf(record) === OBSERVED
  && (record.status ?? 0) >= 400 && (record.status ?? 0) < 500;
const describe = (record) => (stateOf(record) === ERROR ? 'transport error' : String(record.status));

/** A hostile entry is expected to change: from accepted (or crashing) to rejected. */
function compareSecurity(baseline, current) {
  if (rejected(baseline)) {
    return {
      state: UNVERIFIED,
      details: [`baseline already rejected (${baseline.status}): the entry does not demonstrate the finding`],
    };
  }
  if (rejected(current)) {
    return { state: FIXED, details: [`rejected with ${current.status} (baseline: ${describe(baseline)})`] };
  }
  if (isFailure(current) && !isFailure(baseline)) {
    return {
      state: REGRESSION,
      details: [`hostile input now fails with ${describe(current)} (baseline: ${describe(baseline)})`],
    };
  }
  return {
    state: NOT_FIXED,
    details: [`still not rejected: ${describe(current)} (baseline: ${describe(baseline)})`],
  };
}

function compareOne(baseline, current) {
  if (!baseline) {
    return {
      state: UNVERIFIED,
      details: ['not present in baseline: capture it against the original (protocol 4.3)'],
    };
  }
  if (!current) return { state: UNVERIFIED, details: ['not exercised in replay'] };
  if (stateOf(baseline) === SKIPPED) {
    return { state: UNVERIFIED, details: [`skipped in baseline: ${baseline.error}`] };
  }
  if (stateOf(current) === SKIPPED) {
    return { state: UNVERIFIED, details: [`skipped in replay: ${current.error}`] };
  }

  if ((baseline.kind ?? current.kind) === 'security') return compareSecurity(baseline, current);

  if (stateOf(baseline) === ERROR) {
    return isFailure(current)
      ? { state: PRE_EXISTING_FAILURE, details: [`failed before and after: transport error -> ${describe(current)}`] }
      : { state: PASS, details: ['improved from transport error'] };
  }
  if (stateOf(current) === ERROR) {
    return serverError(baseline)
      ? { state: PRE_EXISTING_FAILURE, details: [`failed before and after: ${baseline.status} -> transport error`] }
      : { state: REGRESSION, details: ['call failed after refactoring: transport error'] };
  }

  const details = [];
  if (baseline.status !== current.status) {
    details.push(`statusChanged ${baseline.status} -> ${current.status}`);
  }
  if (baseline.contentType !== current.contentType) {
    details.push(`contentTypeChanged ${baseline.contentType} -> ${current.contentType}`);
  }
  details.push(...headersDiff(baseline.headers, current.headers));
  if (!shapesEqual(baseline.shape, current.shape)) {
    for (const diff of shapeDiff(baseline.shape, current.shape)) {
      if (diff.kind === 'typeChanged') {
        details.push(`typeChanged ${diff.path}: ${diff.from} -> ${diff.to}`);
      } else if (diff.kind === 'textChanged') {
        details.push(`textChanged ${diff.path}: -${diff.removed.length} +${diff.added.length} lines`);
        details.push(...diff.removed.slice(0, 3).map((l) => `  - ${l}`));
        details.push(...diff.added.slice(0, 3).map((l) => `  + ${l}`));
      } else {
        details.push(`${diff.kind} ${diff.path}`);
      }
    }
  }

  if (details.length === 0) {
    // Identical -- but if it was already broken, that is not a success. You neither
    // fixed it nor broke it, and the report must say exactly that.
    return serverError(baseline)
      ? { state: PRE_EXISTING_FAILURE, details: [`unchanged failure: status ${baseline.status}`] }
      : { state: PASS, details: [] };
  }
  // Already broken before, still broken in the same way -> neither pass nor regression.
  if (serverError(baseline) && baseline.status === current.status) {
    return { state: PRE_EXISTING_FAILURE, details };
  }
  // Improvement is a behaviour change, so it is named rather than hidden -- but it is
  // not a regression.
  if (serverError(baseline) && !isFailure(current)) {
    return { state: PASS, details: [`improved from ${baseline.status}`, ...details] };
  }
  return { state: REGRESSION, details };
}

function compare(baselineDoc, currentDoc) {
  const baselineResults = baselineDoc.results ?? {};
  const currentResults = currentDoc.results ?? {};
  const ids = [...new Set([...Object.keys(baselineResults), ...Object.keys(currentResults)])]
    .sort(byCodePoint);
  return ids.map((id) => ({ id, ...compareOne(baselineResults[id], currentResults[id]) }));
}

// ---------------------------------------------------------------------------
// I/O and CLI
// ---------------------------------------------------------------------------

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

function writeJson(path, document) {
  writeFileSync(path, `${serialize(document, 2)}\n`, 'utf8');
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
  const counts = {
    [PASS]: 0, [REGRESSION]: 0, [PRE_EXISTING_FAILURE]: 0, [UNVERIFIED]: 0, [FIXED]: 0, [NOT_FIXED]: 0,
  };
  for (const row of rows) counts[row.state] += 1;
  console.log('');
  console.log(`  ${counts[PASS]} PASS, ${counts[REGRESSION]} REGRESSION, `
    + `${counts[PRE_EXISTING_FAILURE]} PRE-EXISTING FAILURE, ${counts[UNVERIFIED]} UNVERIFIED`);
  if (counts[FIXED] || counts[NOT_FIXED]) {
    console.log(`  security: ${counts[FIXED]} FIXED, ${counts[NOT_FIXED]} NOT FIXED`);
  }
  return counts;
}

const USAGE = `Baseline-then-replay surface probe (see 06-validation-protocol.md).
This script never boots the application.

  node probe.mjs capture --surface <path> --base-url <url> --out <path>
                         [--only <id,id,...>] [--merge] [--timeout <seconds>]
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
      const only = typeof options.only === 'string' ? new Set(options.only.split(',')) : null;
      let document = await capture(readJson(options.surface), options['base-url'], timeout, only);
      if (options.merge) {
        const previous = readJson(options.out);
        previous.results = { ...(previous.results ?? {}), ...document.results };
        previous.version = PROTOCOL_VERSION;
        document = previous;
      }
      writeJson(options.out, document);
      const states = Object.values(document.results).map((r) => r.state);
      const count = (s) => states.filter((x) => x === s).length;
      console.log(`captured ${states.length} entries (${count(OBSERVED)} observed, `
        + `${count(ERROR)} error, ${count(SKIPPED)} skipped) -> ${options.out}`);
      if (count(ERROR) > 1) {
        console.error('warning: several transport errors -- if one entry crashed the application, '
          + 'the entries after it failed only because it was down (protocol 3.2)');
      }
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
      currentDoc = await capture(readJson(options.surface), options['base-url'], timeout, null);
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
