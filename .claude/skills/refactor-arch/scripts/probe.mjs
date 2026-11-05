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
 *   # a destructive entry runs alone, on its own fresh boot, merged into the capture
 *   node probe.mjs capture --surface reports/surface.json --base-url http://127.0.0.1:8081 \
 *                          --out reports/baseline.json --only purge-archive --merge
 *
 *   # a secret written as {{env:NAME}} in the inventory is supplied at call time, never stored
 *   node probe.mjs capture ... --env OPERATOR_TOKEN=<value>
 *
 * Exit codes: 0 = no regressions, 1 = at least one regression (or NOT ROBUST / VIOLATED),
 * 2 = usage or I/O error.
 */

import { readFileSync, writeFileSync } from 'node:fs';
import process from 'node:process';

const PROTOCOL_VERSION = 3;
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
const ROBUST = 'ROBUST';           // robustness variant: no server error, no crash (section 4.4)
const NOT_ROBUST = 'NOT ROBUST';   // robustness variant: failed before and still fails
const HOLDS = 'HOLDS';             // value entry: every assertion holds (section 4.5)
const VIOLATED = 'VIOLATED';       // value entry: at least one assertion does not hold

// Robustness matrix (protocol section 2.3). Every implementation emits the same variants,
// in the same order, with the same ids.
const INT64_MAX = '9223372036854775807';
const INT64_OVERFLOW = '9223372036854775808';
const NON_FINITE = '1e999';
const NESTING_DEPTH = 64;
const FIELD_LOCATIONS = ['body', 'query', 'header', 'path'];
const FIELD_TYPES = ['string', 'number', 'integer', 'boolean', 'array', 'object'];
const RAW_MARK = '__probe_raw_literal__';
const OMIT = Symbol('omit');
const REPEAT = Symbol('repeat');

// Secrets are written as {{env:NAME}} in the inventory and resolved at call time (section 2.5).
const ENV_PATTERN = /\{\{env:([A-Za-z_][A-Za-z0-9_]*)\}\}/g;
const SECRET_NAME = /secret|key|token|passw|pwd|credential|dsn|conn_str/i;
const VALUE_OPS = ['equals', 'matches', 'absent', 'sameAsBaseline'];
const PATH_TOKEN = /\.([^.[\]]+)|\[([0-9]+)\]|\[\*\]/y;

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

// ---------------------------------------------------------------------------
// Secrets by reference (protocol section 2.5)
// ---------------------------------------------------------------------------

/** Every NAME referenced as {{env:NAME}} anywhere inside a JSON-like value. */
function envNames(value, names = new Set()) {
  if (typeof value === 'string') {
    for (const match of value.matchAll(ENV_PATTERN)) names.add(match[1]);
  } else if (Array.isArray(value)) {
    for (const item of value) envNames(item, names);
  } else if (value !== null && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) { envNames(key, names); envNames(item, names); }
  }
  return names;
}

function resolveEnv(value, env) {
  if (typeof value === 'string') return value.replace(ENV_PATTERN, (_, name) => env[name]);
  if (Array.isArray(value)) return value.map((item) => resolveEnv(item, env));
  if (value !== null && typeof value === 'object') {
    const out = {};
    for (const [key, item] of Object.entries(value)) out[resolveEnv(key, env)] = resolveEnv(item, env);
    return out;
  }
  return value;
}

// ---------------------------------------------------------------------------
// Robustness matrix (protocol section 2.3)
// ---------------------------------------------------------------------------

/** A JSON number no serializer emits faithfully in every runtime: sent as literal text. */
class Raw {
  constructor(text) { this.text = text; }
}

const numeric = (type) => type === 'number' || type === 'integer';

function nested() {
  let value = {};
  for (let i = 0; i < NESTING_DEPTH; i += 1) value = { a: value };
  return value;
}

function bodyVariants(type) {
  const variants = [['omitted', OMIT], ['null', null]];
  variants.push(type === 'string' ? ['empty-string', ''] : ['string', 'x']);
  if (!numeric(type)) variants.push(['number', 1]);
  if (type !== 'boolean') variants.push(['boolean', true]);
  if (type !== 'array') variants.push(['list', ['x']]);
  if (type !== 'object') variants.push(['empty-object', {}]);
  variants.push(['nested-object', nested()]);
  if (numeric(type)) {
    variants.push(['zero', 0], ['negative', -1], ['int64-max', new Raw(INT64_MAX)],
      ['int64-overflow', new Raw(INT64_OVERFLOW)], ['non-finite', new Raw(NON_FINITE)]);
  }
  if (type === 'integer') variants.push(['fraction', 1.5]);
  return variants;
}

function textVariants(type, location) {
  const variants = [];
  if (location !== 'path') variants.push(['omitted', OMIT], ['empty', '']);
  if (type !== 'string') variants.push(['string', 'x']);
  if (numeric(type)) {
    variants.push(['zero', '0'], ['negative', '-1'], ['int64-max', INT64_MAX],
      ['int64-overflow', INT64_OVERFLOW], ['non-finite', NON_FINITE], ['nan', 'NaN']);
  }
  if (type === 'integer') variants.push(['fraction', '1.5']);
  if (location === 'query') variants.push(['repeated', REPEAT]);
  return variants;
}

function setDotted(body, name, value) {
  const keys = name.split('.');
  let node = body;
  for (const key of keys.slice(0, -1)) {
    const next = node[key];
    if (next === null || typeof next !== 'object' || Array.isArray(next)) node[key] = {};
    node = node[key];
  }
  const last = keys[keys.length - 1];
  if (value === OMIT) delete node[last];
  else node[last] = value;
}

function withQuery(path, name, value) {
  const cut = path.indexOf('?');
  const base = cut < 0 ? path : path.slice(0, cut);
  const query = cut < 0 ? '' : path.slice(cut + 1);
  const params = query.split('&').filter((p) => p && p.split('=')[0] !== name);
  if (value === REPEAT) params.push(`${name}=x`, `${name}=y`);
  else if (value !== OMIT) params.push(`${name}=${value}`);
  return base + (params.length ? `?${params.join('&')}` : '');
}

function checkFields(entry) {
  const { fields } = entry;
  if (!Array.isArray(fields) || fields.length === 0) {
    throw new Error(`robustness entry '${entry.id}' needs a non-empty 'fields' list (protocol section 2.3)`);
  }
  if (entry.destructive) {
    throw new Error(`robustness entry '${entry.id}' cannot be destructive: its variants would share one boot (protocol section 2.3)`);
  }
  for (const field of fields) {
    if (!FIELD_LOCATIONS.includes(field.in) || !field.name || !FIELD_TYPES.includes(field.type)) {
      throw new Error(`robustness entry '${entry.id}': each field needs 'in' (${FIELD_LOCATIONS.join('/')}), 'name' and 'type' (${FIELD_TYPES.join('/')})`);
    }
    if (field.in === 'path' && (!('value' in field) || !(entry.path ?? '').includes(`{${field.name}}`))) {
      throw new Error(`robustness entry '${entry.id}': path field '${field.name}' needs a benign 'value' and a '{${field.name}}' placeholder in 'path'`);
    }
    const { body } = entry;
    if (field.in === 'body' && body !== undefined && body !== null
        && (typeof body !== 'object' || Array.isArray(body))) {
      throw new Error(`robustness entry '${entry.id}': a body field needs an object 'body'`);
    }
  }
}

const asText = (value) => String(value);   // booleans as true/false, like probe.py

/** The derived entries of one robustness entry, in a fixed order. */
function expand(entry) {
  if (entry.skip) return [entry];
  checkFields(entry);
  const { fields } = entry;
  const derived = [];
  for (const field of fields) {
    const location = field.in;
    const { name } = field;
    const variants = location === 'body' ? bodyVariants(field.type) : textVariants(field.type, location);
    for (const [label, original] of variants) {
      let value = original;
      let path = entry.path ?? '/';
      for (const other of fields) {
        if (other.in === 'path' && other !== field) path = path.split(`{${other.name}}`).join(asText(other.value));
      }
      let headers = { ...(entry.headers ?? {}) };
      let body = entry.body !== undefined && entry.body !== null ? JSON.parse(JSON.stringify(entry.body)) : null;
      let rawLiteral = null;
      if (location === 'body') {
        body = body ?? {};
        if (value instanceof Raw) { rawLiteral = value.text; value = RAW_MARK; }
        setDotted(body, name, value === OMIT || value === null || typeof value !== 'object'
          ? value : JSON.parse(JSON.stringify(value)));
      } else if (location === 'query') {
        path = withQuery(path, name, value);
      } else if (location === 'header') {
        headers = Object.fromEntries(Object.entries(headers).filter(([k]) => k.toLowerCase() !== name.toLowerCase()));
        if (value !== OMIT) headers[name] = value;
      } else {
        path = path.split(`{${name}}`).join(value);
      }
      derived.push({
        id: `${entry.id}#${name}=${label}`, method: entry.method, path, headers, body,
        kind: 'robustness', finding: entry.finding ?? null, _rawLiteral: rawLiteral, _base: entry.id,
      });
    }
  }
  return derived;
}

// ---------------------------------------------------------------------------
// Value assertions (protocol section 2.4)
// ---------------------------------------------------------------------------

function parseJsonPath(path) {
  if (typeof path !== 'string' || !path.startsWith('$')) {
    throw new Error(`value assertion path must start with '$': ${JSON.stringify(path)}`);
  }
  const tokens = [];
  let position = 1;
  while (position < path.length) {
    PATH_TOKEN.lastIndex = position;
    const match = PATH_TOKEN.exec(path);
    if (!match) throw new Error(`unsupported value assertion path: ${JSON.stringify(path)}`);
    if (match[1] !== undefined) tokens.push(['key', match[1]]);
    else if (match[2] !== undefined) tokens.push(['index', Number(match[2])]);
    else tokens.push(['star', null]);
    position = PATH_TOKEN.lastIndex;
  }
  return tokens;
}

/** [found, value]. A path with [*] yields the list of every match. */
function extract(document, path) {
  let nodes = [document];
  let star = false;
  for (const [kind, token] of parseJsonPath(path)) {
    const following = [];
    for (const node of nodes) {
      if (kind === 'star') {
        if (Array.isArray(node)) following.push(...node);
      } else if (kind === 'index') {
        if (Array.isArray(node) && token < node.length) following.push(node[token]);
      } else if (node !== null && typeof node === 'object' && !Array.isArray(node)
          && Object.prototype.hasOwnProperty.call(node, token)) {
        following.push(node[token]);
      }
    }
    star = star || kind === 'star';
    nodes = following;
  }
  if (star) return [nodes.length > 0, nodes];
  return nodes.length ? [true, nodes[0]] : [false, null];
}

function assertionOp(assertion) {
  const ops = VALUE_OPS.filter((op) => op in assertion);
  if (ops.length !== 1) {
    throw new Error(`a value assertion needs exactly one of ${VALUE_OPS.join('/')}: ${serialize(assertion)}`);
  }
  return ops[0];
}

function checkAssertions(entry) {
  const assertions = entry.assert;
  if (!Array.isArray(assertions) || assertions.length === 0) {
    throw new Error(`value entry '${entry.id}' needs a non-empty 'assert' list (protocol section 2.4)`);
  }
  for (const assertion of assertions) {
    const op = assertionOp(assertion);
    const keys = parseJsonPath(assertion.path).filter(([kind]) => kind === 'key').map(([, k]) => k);
    if (op === 'sameAsBaseline' && keys.length && SECRET_NAME.test(keys[keys.length - 1])) {
      throw new Error(`value entry '${entry.id}': sameAsBaseline would store the value of '${assertion.path}' `
        + "in the capture; assert it with 'absent' or 'matches' instead (protocol section 2.5)");
    }
  }
}

function evaluate(assertions, document, foundDocument) {
  return assertions.map((assertion) => {
    const op = assertionOp(assertion);
    const [found, value] = foundDocument ? extract(document, assertion.path) : [false, null];
    if (op === 'sameAsBaseline') {
      return { op, path: assertion.path, found, value: found ? value : null };
    }
    let holds;
    if (op === 'absent') holds = !found;
    else if (!found) holds = false;
    else if (op === 'equals') holds = canonical(value) === canonical(assertion.equals);
    else {
      const pattern = new RegExp(assertion.matches);
      const items = Array.isArray(value) && assertion.path.includes('[*]') ? value : [value];
      holds = items.length > 0 && items.every((item) => typeof item === 'string' && pattern.test(item));
    }
    return { op, path: assertion.path, holds };
  });
}

function parseJsonBody(bytes) {
  try {
    return [true, JSON.parse(new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes))];
  } catch {
    return [false, null];
  }
}

async function exercise(baseUrl, entry, timeoutSeconds, env = {}) {
  const id = entry.id ?? `${entry.method} ${entry.path}`;
  const method = (entry.method ?? 'GET').toUpperCase();
  const path = entry.path ?? '/';
  const kind = entry.kind ?? 'contract';
  const record = {
    id, method, path, kind, finding: entry.finding ?? null,
    expect: entry.expect ?? null, like: entry.like ?? null, destructive: Boolean(entry.destructive),
    state: SKIPPED, status: null, contentType: null, headers: null, shape: null, error: null,
  };
  if (kind === 'value') record.assertions = null;

  if (entry.skip) {
    record.error = entry.skipReason ?? 'skipped by inventory';
    return record;
  }

  const headers = resolveEnv({ ...(entry.headers ?? {}) }, env);
  let body;
  if (entry.rawBody !== undefined && entry.rawBody !== null) {
    // Sent byte for byte: the point is a body the application's parser has not seen.
    body = resolveEnv(entry.rawBody, env);
  } else if (entry.body !== undefined && entry.body !== null) {
    body = JSON.stringify(resolveEnv(entry.body, env));
    if (entry._rawLiteral !== undefined && entry._rawLiteral !== null) {
      body = body.split(`"${RAW_MARK}"`).join(entry._rawLiteral);
    }
  }
  if (body !== undefined && !Object.keys(headers).some((h) => h.toLowerCase() === 'content-type')) {
    headers['Content-Type'] = 'application/json';
  }

  // A harness must never hang: a hung probe is indistinguishable from a broken app.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutSeconds * 1000);
  try {
    const response = await fetch(baseUrl.replace(/\/+$/, '') + resolveEnv(path, env), {
      method, headers, body, signal: controller.signal, redirect: 'manual',
    });
    const bytes = new Uint8Array(await response.arrayBuffer());
    record.state = OBSERVED;
    record.status = response.status;   // a 3xx/4xx/5xx is a real response, not a transport failure
    record.contentType = normalizeContentType(response.headers.get('content-type'));
    record.headers = contractHeaders(response.headers);
    record.shape = bodyShape(bytes);
    if (kind === 'value') {
      const [parsed, document] = parseJsonBody(bytes);
      record.assertions = evaluate(entry.assert ?? [], document, parsed);
    }
  } catch (err) {
    record.state = ERROR;             // refused, reset, timeout, truncated body
    record.error = `${err.name}: ${err.cause?.code ?? err.message}`;
  } finally {
    clearTimeout(timer);
  }
  return record;
}

/**
 * Contract and value entries first, then security, then robustness: hostile and malformed
 * calls may mutate state, and the contract entries must see the same datastore in both runs.
 *
 * A destructive entry is exercised only when --only names it and nothing else (protocol
 * section 2.2): it runs alone, on its own fresh boot, so that what it destroys cannot reach
 * any other entry. --only accepts a robustness entry's id (all its variants) or a variant id.
 */
function orderedEntries(surface, only) {
  const expanded = [];
  for (const entry of surface.entries ?? []) {
    const kind = entry.kind ?? 'contract';
    if (kind === 'robustness') {
      expanded.push(...expand(entry));
    } else {
      if (kind === 'value' && !entry.skip) checkAssertions(entry);
      expanded.push(entry);
    }
  }
  let entries = expanded.filter((e) => !only || only.has(e.id) || (e._base !== undefined && only.has(e._base)));
  const destructive = entries.filter((e) => e.destructive);
  if (destructive.length) {
    if (!only) {
      entries = entries.filter((e) => !e.destructive);
    } else if (entries.length > 1) {
      throw new Error('a destructive entry must be captured alone (--only <its id>), '
        + 'on its own fresh boot (protocol section 2.2): '
        + destructive.map((e) => e.id).sort(byCodePoint).join(','));
    }
  }
  const kindOf = (e) => e.kind ?? 'contract';
  return [
    ...entries.filter((e) => kindOf(e) !== 'security' && kindOf(e) !== 'robustness'),
    ...entries.filter((e) => kindOf(e) === 'security'),
    ...entries.filter((e) => kindOf(e) === 'robustness'),
  ];
}

const destructiveIds = (surface) => (surface.entries ?? [])
  .filter((e) => e.destructive).map((e) => e.id).sort(byCodePoint);

async function capture(surface, baseUrl, timeoutSeconds, only, env = {}) {
  const entries = orderedEntries(surface, only);
  // Every secret the selected entries reference must be supplied before the first call:
  // failing halfway would leave a partial capture that looks complete.
  const missing = new Set();
  for (const entry of entries) {
    if (entry.skip) continue;
    for (const key of ['path', 'headers', 'body', 'rawBody']) {
      for (const name of envNames(entry[key])) if (!(name in env)) missing.add(name);
    }
  }
  if (missing.size) {
    throw new Error(`missing ${[...missing].sort(byCodePoint).join(', ')} for {{env:NAME}} placeholders: `
      + 'pass --env NAME=VALUE or set it in the environment (protocol section 2.5)');
  }
  const results = {};
  // Sequential on purpose: concurrency would change the application's observable
  // ordering and load, and the baseline must be reproducible.
  for (const entry of entries) {
    const record = await exercise(baseUrl, entry, timeoutSeconds, env);
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

/**
 * Shape equality, except that an empty array matches any array. Used only to compare an
 * entry with a DIFFERENT entry (its benign sibling), whose collection may be empty while
 * this one's is not -- a data difference, not a behaviour difference.
 */
function shapesCompatible(left, right) {
  if (shapesEqual(left, right)) return true;
  const isObj = (d) => d !== null && typeof d === 'object';
  if (!isObj(left) || !isObj(right)) return false;
  if (left.type === 'array' && right.type === 'array') {
    if (left.items === 'empty' || right.items === 'empty') return true;
    return shapesCompatible(left.items, right.items);
  }
  if (left.type === 'object' && right.type === 'object') {
    const a = left.properties ?? {};
    const b = right.properties ?? {};
    const keysA = Object.keys(a).sort(byCodePoint);
    const keysB = Object.keys(b).sort(byCodePoint);
    return keysA.length === keysB.length && keysA.every((k, i) => k === keysB[i])
      && keysA.every((k) => shapesCompatible(a[k], b[k]));
  }
  return false;
}

/** An ordinary, non-error answer indistinguishable in shape from the benign sibling's. */
const behavesLike = (record, sibling) => stateOf(record) === OBSERVED && stateOf(sibling) === OBSERVED
  && (record.status ?? 0) < 400
  && record.status === sibling.status
  && record.contentType === sibling.contentType
  && shapesCompatible(record.shape, sibling.shape);

/**
 * A hostile entry whose fix changes the answer without rejecting it: the input is now
 * treated as data. Fixed when it behaves like its benign sibling (protocol section 2.1).
 */
function compareNeutralized(baseline, current, likeId, likeBaseline, likeCurrent) {
  if (!likeId) {
    return { state: UNVERIFIED, details: ["expect 'neutralized' needs 'like': the id of a benign sibling entry"] };
  }
  if (!likeBaseline || !likeCurrent
      || stateOf(likeBaseline) !== OBSERVED || stateOf(likeCurrent) !== OBSERVED) {
    return { state: UNVERIFIED, details: [`benign sibling '${likeId}' was not observed in both runs`] };
  }
  if (behavesLike(baseline, likeBaseline)) {
    return {
      state: UNVERIFIED,
      details: [`baseline already behaved like '${likeId}': the entry does not demonstrate the finding`],
    };
  }
  if (behavesLike(current, likeCurrent)) {
    return { state: FIXED, details: [`now behaves like '${likeId}' (baseline: ${describe(baseline)})`] };
  }
  if (isFailure(current) && !isFailure(baseline)) {
    return {
      state: REGRESSION,
      details: [`hostile input now fails with ${describe(current)} (baseline: ${describe(baseline)})`],
    };
  }
  return {
    state: NOT_FIXED,
    details: [`still does not behave like '${likeId}': ${describe(current)} (baseline: ${describe(baseline)})`],
  };
}

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

/**
 * A malformed-input variant. Only the status class matters: hardening a wrong-typed input
 * from 2xx to 4xx is the point of the fix (protocol section 4.4).
 */
function compareRobustness(baseline, current) {
  if (isFailure(current)) {
    return isFailure(baseline)
      ? { state: NOT_ROBUST, details: [`fails before and after: ${describe(baseline)} -> ${describe(current)}`] }
      : {
        state: REGRESSION,
        details: [`malformed input now fails with ${describe(current)} (baseline: ${describe(baseline)})`],
      };
  }
  return { state: ROBUST, details: [`${describe(current)} (baseline: ${describe(baseline)})`] };
}

/** Assertions on values the transformation changes (protocol section 4.5). */
function compareValue(baseline, current) {
  if (stateOf(current) !== OBSERVED || serverError(current)) {
    return {
      state: VIOLATED,
      details: [`no answer to assert on: ${describe(current)} (baseline: ${describe(baseline)})`],
    };
  }
  const currentAssertions = current.assertions ?? [];
  const baselineAssertions = baseline.assertions ?? [];
  if (currentAssertions.length === 0) return { state: UNVERIFIED, details: ['no assertions recorded'] };
  const violated = [];
  const unverified = [];
  currentAssertions.forEach((assertion, index) => {
    if (assertion.op === 'sameAsBaseline') {
      const before = baselineAssertions[index];
      if (!before || !before.found) unverified.push(`sameAsBaseline ${assertion.path}: no baseline value`);
      else if (!assertion.found) violated.push(`sameAsBaseline ${assertion.path}: absent now`);
      else if (canonical(before.value) !== canonical(assertion.value)) {
        violated.push(`sameAsBaseline ${assertion.path}: value differs from baseline`);
      }
    } else if (!assertion.holds) {
      violated.push(`${assertion.op} ${assertion.path}: does not hold`);
    }
  });
  if (violated.length) return { state: VIOLATED, details: violated };
  if (unverified.length) return { state: UNVERIFIED, details: unverified };
  return { state: HOLDS, details: [] };
}

function compareOne(baseline, current, baselineResults = {}, currentResults = {}) {
  if (!baseline) {
    return {
      state: UNVERIFIED,
      details: ['not present in baseline: capture it against the original (protocol section 4.3)'],
    };
  }
  if (!current) {
    return baseline.destructive
      ? {
        state: UNVERIFIED,
        details: ['not exercised in replay: destructive, capture it alone with --only --merge (protocol section 2.2)'],
      }
      : { state: UNVERIFIED, details: ['not exercised in replay'] };
  }
  if (stateOf(baseline) === SKIPPED) {
    return { state: UNVERIFIED, details: [`skipped in baseline: ${baseline.error}`] };
  }
  if (stateOf(current) === SKIPPED) {
    return { state: UNVERIFIED, details: [`skipped in replay: ${current.error}`] };
  }

  const kind = baseline.kind ?? current.kind;
  if (kind === 'robustness') return compareRobustness(baseline, current);
  if (kind === 'value') return compareValue(baseline, current);
  if (kind === 'security') {
    if ((baseline.expect ?? current.expect) === 'neutralized') {
      const likeId = baseline.like ?? current.like;
      return compareNeutralized(baseline, current, likeId,
        likeId ? baselineResults[likeId] : undefined, likeId ? currentResults[likeId] : undefined);
    }
    return compareSecurity(baseline, current);
  }

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
  return ids.map((id) => ({
    id, ...compareOne(baselineResults[id], currentResults[id], baselineResults, currentResults),
  }));
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
    if (key === 'env') {
      // Repeatable, like probe.py's --env.
      if (next === undefined || next.startsWith('--')) throw new Error('--env expects NAME=VALUE');
      options.env = [...(options.env ?? []), next];
      i += 1;
    } else if (next === undefined || next.startsWith('--')) options[key] = true;
    else { options[key] = next; i += 1; }
  }
  return options;
}

/** The process environment, overridden by --env NAME=VALUE pairs. */
function buildEnv(pairs) {
  const env = { ...process.env };
  for (const pair of pairs ?? []) {
    const cut = pair.indexOf('=');
    if (cut <= 0) throw new Error(`--env expects NAME=VALUE, got ${JSON.stringify(pair)}`);
    env[pair.slice(0, cut)] = pair.slice(cut + 1);
  }
  return env;
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
    [ROBUST]: 0, [NOT_ROBUST]: 0, [HOLDS]: 0, [VIOLATED]: 0,
  };
  for (const row of rows) counts[row.state] += 1;
  console.log('');
  console.log(`  ${counts[PASS]} PASS, ${counts[REGRESSION]} REGRESSION, `
    + `${counts[PRE_EXISTING_FAILURE]} PRE-EXISTING FAILURE, ${counts[UNVERIFIED]} UNVERIFIED`);
  if (counts[FIXED] || counts[NOT_FIXED]) {
    console.log(`  security: ${counts[FIXED]} FIXED, ${counts[NOT_FIXED]} NOT FIXED`);
  }
  if (counts[ROBUST] || counts[NOT_ROBUST]) {
    console.log(`  robustness: ${counts[ROBUST]} ROBUST, ${counts[NOT_ROBUST]} NOT ROBUST`);
  }
  if (counts[HOLDS] || counts[VIOLATED]) {
    console.log(`  values: ${counts[HOLDS]} HOLDS, ${counts[VIOLATED]} VIOLATED`);
  }
  return counts;
}

function noteDestructive(surface, only) {
  if (only) return;
  const pending = destructiveIds(surface);
  if (pending.length) {
    console.error(`note: ${pending.length} destructive entries not exercised: ${pending.join(',')} `
      + '-- capture each alone, on a fresh boot, with --only <id> --merge (protocol section 2.2)');
  }
}

const USAGE = `Baseline-then-replay surface probe (see 06-validation-protocol.md).
This script never boots the application.

  node probe.mjs capture --surface <path> --base-url <url> --out <path>
                         [--only <id,id,...>] [--merge] [--timeout <seconds>]
                         [--env NAME=VALUE ...]
  node probe.mjs compare --baseline <path> [--surface <path> --base-url <url>]
                         [--current <path>] [--out <path>] [--timeout <seconds>]
                         [--env NAME=VALUE ...]`;

async function main() {
  const [mode, ...rest] = process.argv.slice(2);

  if (mode !== 'capture' && mode !== 'compare') {
    console.error(USAGE);
    return 2;
  }

  try {
    const options = parseArgs(rest);
    const timeout = Number(options.timeout ?? DEFAULT_TIMEOUT_SECONDS);
    const env = buildEnv(options.env);
    if (mode === 'capture') {
      if (!options.surface || !options['base-url'] || !options.out) {
        console.error('capture needs --surface, --base-url and --out');
        return 2;
      }
      const only = typeof options.only === 'string' ? new Set(options.only.split(',')) : null;
      const surface = readJson(options.surface);
      let document = await capture(surface, options['base-url'], timeout, only, env);
      // Counted before merging: the numbers describe THIS run, not the whole file.
      const states = Object.values(document.results).map((r) => r.state);
      const count = (s) => states.filter((x) => x === s).length;
      if (options.merge) {
        const previous = readJson(options.out);
        previous.results = { ...(previous.results ?? {}), ...document.results };
        previous.version = PROTOCOL_VERSION;
        document = previous;
      }
      writeJson(options.out, document);
      console.log(`captured ${states.length} entries now (${count(OBSERVED)} observed, `
        + `${count(ERROR)} error, ${count(SKIPPED)} skipped); `
        + `${Object.keys(document.results).length} in file -> ${options.out}`);
      if (count(ERROR) > 1) {
        console.error('warning: several transport errors in this run -- if one entry crashed '
          + 'the application, the entries after it failed only because it was down '
          + '(protocol section 3.1)');
      }
      noteDestructive(surface, only);
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
      const surface = readJson(options.surface);
      currentDoc = await capture(surface, options['base-url'], timeout, null, env);
      if (options.out) writeJson(options.out, currentDoc);
      noteDestructive(surface, null);
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
    const counts = summarize(rows);
    return counts[REGRESSION] || counts[NOT_ROBUST] || counts[VIOLATED] ? 1 : 0;
  } catch (err) {
    console.error(`probe: ${err.message}`);
    return 2;
  }
}

// Set the exit code and let the event loop drain, rather than calling process.exit():
// a hard exit while fetch's sockets are still closing aborts the runtime on some platforms.
process.exitCode = await main();
