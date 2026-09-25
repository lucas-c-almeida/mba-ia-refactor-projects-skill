#!/usr/bin/env node
/**
 * proc.mjs -- reference implementation of the process-ownership rules of
 *             references/06-validation-protocol.md section 1.3, for host mode.
 *
 * Zero dependencies. Node 18+ built-ins only. POSIX and Windows.
 *
 * Why it exists
 * -------------
 * The skill starts and stops the application several times per run. Stopping it by hand is
 * where things go wrong: an agent that lost track of its PID reaches for "kill everything
 * called node", and takes down processes that are not its own. This tool makes the safe path
 * the easy one. It stops exactly the process tree it started, and nothing else.
 *
 * What it does
 * ------------
 *   start   run an argv the AGENT derived, in a new process group, record who it started,
 *           wait until the port accepts connections
 *   stop    stop the recorded tree -- after checking that the PID still belongs to the
 *           process that was started (PIDs are reused)
 *   status  is the recorded process alive, and does the port answer?
 *   copy    copy a directory tree to a new directory, leaving out VCS directories -- the
 *           snapshot and every run copy of protocol section 1.1, in one literal command
 *
 * What it deliberately does NOT do
 * --------------------------------
 *   - It knows nothing about stacks. It never decides WHAT to run: the agent derives the boot
 *     command in Phase 1 and passes it after "--".
 *   - It never stops a process it did not start. No lookup by name, image, pattern or port.
 *   - It never frees a busy port. If the port is taken, it refuses to start: pick another port.
 *
 * Behaviour, output and exit codes match proc.py; tests/probe-conformance holds them to it.
 *
 * Usage
 * -----
 *   node proc.mjs start  --state <file> --port 8081 [--cwd <dir>] [--log <file>]
 *                        [--env KEY=VALUE ...] [--timeout 60] -- <argv...>
 *   node proc.mjs stop   --state <file> [--timeout 10]
 *   node proc.mjs status --state <file>
 *   node proc.mjs copy   --from <dir> --to <new dir> [--exclude <name> ...]
 *
 * Every command prints one JSON line (keys sorted) and exits with:
 *   0 ok (status: running)       1 status: not running         2 usage or I/O error
 *   3 port already in use        4 not ready in time (stopped) 5 exited before ready
 *   6 PID identity mismatch: refused to stop a process it did not start
 *   7 port still answering after stop: something else holds it
 */

import { spawn, spawnSync } from 'node:child_process';
import {
  closeSync, cpSync, existsSync, lstatSync, openSync, readFileSync, statSync, writeFileSync,
} from 'node:fs';
import net from 'node:net';
import path from 'node:path';
import process from 'node:process';

const STATE_VERSION = 1;
const IS_WINDOWS = process.platform === 'win32';
const HOST = '127.0.0.1';

const EXIT = {
  OK: 0, NOT_RUNNING: 1, USAGE: 2, PORT_BUSY: 3, NOT_READY: 4, EXITED: 5, IDENTITY: 6, PORT_HELD: 7,
};

// One snapshot of every process, as "pid|parent|creation time". Win32_Process is the only
// built-in source that has the parent PID; Get-Process does not.
const WINDOWS_SNAPSHOT = "Get-CimInstance Win32_Process | ForEach-Object { '{0}|{1}|{2}' -f "
  + '$_.ProcessId, $_.ParentProcessId, '
  + "$_.CreationDate.ToUniversalTime().ToString('o') }";

const sleep = (ms) => new Promise((resolve) => { setTimeout(resolve, ms); });
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

// ---------------------------------------------------------------------------
// Serialization identical to Python's json.dumps(sort_keys=True, ensure_ascii=False)
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
  const comma = indent ? ',' : ', ';
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    return `[${value.map((v) => pad + serialize(v, indent, level + 1)).join(comma)}${end}]`;
  }
  const keys = Object.keys(value).sort(byCodePoint);
  if (keys.length === 0) return '{}';
  return `{${keys.map((k) => `${pad}${JSON.stringify(k)}: ${serialize(value[k], indent, level + 1)}`).join(comma)}${end}}`;
}

function emit(document, code) {
  console.log(serialize(document));
  return code;
}

// ---------------------------------------------------------------------------
// Process identity
//
// A PID alone does not identify a process: once it exits, the number is reused. The
// identity is (PID, start time as the OS reports it). Neither Node nor the Python standard
// library exposes the start time portably, so both implementations ask the same OS tools.
// ---------------------------------------------------------------------------

function run(argv, timeoutMs = 30000) {
  const done = spawnSync(argv[0], argv.slice(1), {
    stdio: ['ignore', 'pipe', 'ignore'], timeout: timeoutMs, windowsHide: true,
  });
  if (done.error || done.status !== 0) return null;
  return done.stdout.toString('utf8');
}

/** Map pid -> [parent, creation] for every process, or null if the snapshot failed. */
function windowsSnapshot() {
  const out = run(['powershell', '-NoProfile', '-NonInteractive', '-Command', WINDOWS_SNAPSHOT]);
  if (out === null) return null;
  const table = new Map();
  for (const line of out.split(/\r?\n/)) {
    const parts = line.trim().split('|');
    if (parts.length === 3 && /^\d+$/.test(parts[0]) && /^\d+$/.test(parts[1])) {
      table.set(Number(parts[0]), [Number(parts[1]), parts[2]]);
    }
  }
  return table;
}

/** The OS start time of a live process, or null if it is not running. */
function startToken(pid) {
  if (IS_WINDOWS) {
    const entry = (windowsSnapshot() ?? new Map()).get(pid);
    return entry ? entry[1] : null;
  }
  const token = (run(['ps', '-o', 'lstart=', '-p', String(pid)]) ?? '').trim();
  return token || null;
}

/**
 * PIDs below root, following parent links. A child must not predate its parent: that is
 * how a reused parent PID is told apart from the real one.
 */
function windowsDescendants(root, table) {
  const found = [];
  const frontier = [root];
  while (frontier.length) {
    const parent = frontier.pop();
    const parentCreated = (table.get(parent) ?? [null, ''])[1];
    for (const [pid, [ppid, created]] of table) {
      if (ppid === parent && pid !== parent && !found.includes(pid) && created >= parentCreated) {
        found.push(pid);
        frontier.push(pid);
      }
    }
  }
  return found.sort((a, b) => a - b);
}

// ---------------------------------------------------------------------------
// Ports
// ---------------------------------------------------------------------------

function portAnswers(port) {
  return new Promise((resolve) => {
    const socket = net.connect({ host: HOST, port });
    const finish = (answer) => { socket.destroy(); resolve(answer); };
    socket.setTimeout(1000, () => finish(false));
    socket.once('connect', () => finish(true));
    socket.once('error', () => finish(false));
  });
}

// ---------------------------------------------------------------------------
// State file
// ---------------------------------------------------------------------------

const readState = (file) => JSON.parse(readFileSync(file, 'utf8'));
const writeState = (file, state) => writeFileSync(file, `${serialize(state, 2)}\n`, 'utf8');

function logTail(file, lines = 20) {
  try {
    return readFileSync(file, 'utf8').split(/\r?\n/).filter((l, i, all) => i < all.length - 1 || l)
      .slice(-lines);
  } catch {
    return [];
  }
}

// ---------------------------------------------------------------------------
// start
// ---------------------------------------------------------------------------

/** shutil.which, for the one question asked of it: is argv[0] a .cmd/.bat launcher? */
function which(command) {
  const exts = IS_WINDOWS ? (process.env.PATHEXT ?? '.EXE;.CMD;.BAT').split(';') : [''];
  const dirs = path.isAbsolute(command) || command.includes(path.sep)
    ? [''] : (process.env.PATH ?? '').split(path.delimiter);
  for (const dir of dirs) {
    for (const ext of [...(path.extname(command) ? [''] : []), ...exts]) {
      const candidate = path.join(dir, command + ext);
      try {
        if (statSync(candidate).isFile()) return candidate;
      } catch { /* keep looking */ }
    }
  }
  return null;
}

/**
 * On Windows a .cmd/.bat launcher cannot be spawned directly; run it through cmd.exe.
 * Prefer the runtime itself (node server.js) -- the tree is then one process shorter.
 */
function resolveArgv(argv) {
  if (!IS_WINDOWS) return argv;
  const found = which(argv[0]);
  return found && /\.(cmd|bat)$/i.test(found) ? ['cmd.exe', '/d', '/c', ...argv] : argv;
}

function killNow(pid) {
  if (IS_WINDOWS) run(['taskkill', '/PID', String(pid), '/T', '/F']);
  else {
    try { process.kill(-pid, 'SIGKILL'); } catch { /* already gone */ }
  }
}

async function cmdStart(opts, argv) {
  if (!argv.length) return emit({ error: 'nothing to run: pass the boot command after --' }, EXIT.USAGE);
  const port = Number(opts.port);
  if (existsSync(opts.state)) {
    const previous = readState(opts.state);
    if (!previous.stoppedAt && startToken(previous.pid) === previous.startToken) {
      return emit({
        error: 'the state file already tracks a live process: stop it first', pid: previous.pid,
      }, EXIT.USAGE);
    }
  }
  if (await portAnswers(port)) {
    return emit({
      error: `port ${port} is already in use by a process this run did not start. `
        + 'Pick another port; never stop the process holding it.',
      port,
    }, EXIT.PORT_BUSY);
  }

  const env = { ...process.env };
  for (const pair of opts.env) {
    const at = pair.indexOf('=');
    if (at <= 0) return emit({ error: `--env expects KEY=VALUE, got '${pair}'` }, EXIT.USAGE);
    env[pair.slice(0, at)] = pair.slice(at + 1);
  }

  const logPath = opts.log ?? `${opts.state}.log`;
  const command = resolveArgv(argv);
  const cwd = path.resolve(opts.cwd ?? process.cwd());
  const logFd = openSync(logPath, 'a');
  // detached: on POSIX a new session (the process leads its own group, so stop can signal
  // the whole tree); on Windows a new process group with no console of its own.
  const child = spawn(command[0], command.slice(1), {
    cwd, env, detached: true, stdio: ['ignore', logFd, logFd], windowsHide: true,
  });
  closeSync(logFd);
  let exitCode = null;
  let spawnError = null;
  child.on('exit', (code, sig) => { exitCode = code ?? sig ?? 'unknown'; });
  child.on('error', (err) => { spawnError = err; });
  await sleep(50);
  if (spawnError) return emit({ error: `could not start: ${spawnError.message}` }, EXIT.USAGE);
  const { pid } = child;

  let token = null;
  for (let i = 0; i < 5; i += 1) {
    token = startToken(pid);
    if (token !== null || exitCode !== null) break;
    await sleep(200);
  }
  if (token === null && exitCode === null) {
    // Without an identity, a later stop could not tell this process from a stranger that
    // reuses its PID. Stop it now, while this process still owns it, and refuse.
    killNow(pid);
    return emit({
      error: 'could not read the start time of the new process, so it could not be stopped '
        + 'safely later; it was stopped. Host mode is unavailable here: declare it (protocol section 1.3)',
      pid,
    }, EXIT.USAGE);
  }

  const state = {
    version: STATE_VERSION, pid, argv: command, cwd, port, log: path.resolve(logPath),
    launchedAt: now(), startToken: token, descendants: [],
    readyAt: null, stoppedAt: null, stopResult: null,
  };
  writeState(opts.state, state);   // recorded before readiness: a failed start is stoppable

  const deadline = Date.now() + Number(opts.timeout ?? 60) * 1000;
  while (Date.now() < deadline) {
    if (exitCode !== null) {
      state.stoppedAt = now();
      state.stopResult = 'exited before ready';
      writeState(opts.state, state);
      return emit({
        error: `the process exited with code ${exitCode} before the port answered`,
        exitCode, logTail: logTail(logPath), pid,
      }, EXIT.EXITED);
    }
    if (await portAnswers(port)) {
      state.readyAt = now();
      if (IS_WINDOWS) {
        const table = windowsSnapshot() ?? new Map();
        state.descendants = windowsDescendants(pid, table).map((p) => [p, table.get(p)[1]]);
      }
      writeState(opts.state, state);
      child.unref();
      return emit({
        state: 'running', pid, port, stateFile: path.resolve(opts.state), log: state.log,
      }, EXIT.OK);
    }
    await sleep(250);
  }

  await stopTree(state, 10);
  state.stoppedAt = now();
  state.stopResult = 'not ready in time';
  writeState(opts.state, state);
  child.unref();
  return emit({
    error: `the port did not answer within ${Number(opts.timeout ?? 60)}s; the process was stopped`,
    logTail: logTail(logPath), pid,
  }, EXIT.NOT_READY);
}

// ---------------------------------------------------------------------------
// stop
// ---------------------------------------------------------------------------

function posixGroupAlive(pgid) {
  try {
    process.kill(-pgid, 0);
    return true;
  } catch (err) {
    return err.code === 'EPERM';
  }
}

/** Stop the recorded tree. Assumes the identity check already passed. */
async function stopTree(state, timeoutSeconds) {
  const { pid } = state;
  if (!IS_WINDOWS) {
    // The group id is the leader's PID. POSIX never reuses a PID while a group of that id
    // still exists, so signalling the group is safe even if the leader has exited.
    if (!posixGroupAlive(pid)) return;
    process.kill(-pid, 'SIGTERM');
    const deadline = Date.now() + timeoutSeconds * 1000;
    while (Date.now() < deadline && posixGroupAlive(pid)) await sleep(200);
    if (posixGroupAlive(pid)) process.kill(-pid, 'SIGKILL');
    return;
  }
  const table = windowsSnapshot() ?? new Map();
  const targets = [];
  if (table.has(pid) && table.get(pid)[1] === state.startToken) {
    targets.push(pid, ...windowsDescendants(pid, table));
  }
  // Descendants recorded at readiness, still alive with the same identity: they may have
  // been orphaned by a parent that exited, which /T can no longer reach.
  for (const [child, token] of state.descendants ?? []) {
    if (table.has(child) && table.get(child)[1] === token && !targets.includes(child)) {
      targets.push(child);
    }
  }
  for (const target of targets) run(['taskkill', '/PID', String(target), '/T', '/F']);
}

async function cmdStop(opts) {
  const state = readState(opts.state);
  if (state.stoppedAt) {
    return emit({
      state: 'stopped', pid: state.pid, note: `already stopped: ${state.stopResult}`,
    }, EXIT.OK);
  }
  const timeout = Number(opts.timeout ?? 10);
  const token = startToken(state.pid);
  if (token !== null && token !== state.startToken) {
    return emit({
      error: `PID ${state.pid} now belongs to a different process (start time ${token}, `
        + `recorded ${state.startToken}). Refusing to stop it. The recorded process is gone.`,
      pid: state.pid,
    }, EXIT.IDENTITY);
  }

  await stopTree(state, timeout);
  state.stoppedAt = now();
  state.stopResult = token !== null ? 'stopped' : 'was not running';

  const deadline = Date.now() + timeout * 1000;
  while (Date.now() < deadline && await portAnswers(state.port)) await sleep(200);
  writeState(opts.state, state);
  if (await portAnswers(state.port)) {
    return emit({
      error: `port ${state.port} still answers after the recorded tree was stopped: `
        + 'another process holds it. Investigate; never stop it by port.',
      pid: state.pid,
    }, EXIT.PORT_HELD);
  }
  return emit({ state: 'stopped', pid: state.pid, note: state.stopResult }, EXIT.OK);
}

// ---------------------------------------------------------------------------
// status
// ---------------------------------------------------------------------------

async function cmdStatus(opts) {
  const state = readState(opts.state);
  const token = startToken(state.pid);
  const alive = token !== null && token === state.startToken && !state.stoppedAt;
  return emit({
    state: alive ? 'running' : 'not running',
    pid: state.pid,
    port: state.port,
    portAnswers: await portAnswers(state.port),
  }, alive ? EXIT.OK : EXIT.NOT_RUNNING);
}

// ---------------------------------------------------------------------------
// copy
//
// Copying a tree without its VCS directory is where an agent improvises shell: a loop, a
// variable holding the destination, a second command to delete .git afterwards. Commands like
// that cannot be analysed by a permission layer, so each one asks the person. One literal
// invocation per copy is analysable, and it behaves the same on every OS.
// ---------------------------------------------------------------------------

const ALWAYS_EXCLUDED = ['.git', '.hg', '.svn'];

function lexists(file) {
  try { lstatSync(file); return true; } catch { return false; }
}

function cmdCopy(opts) {
  const source = path.resolve(opts.from);
  const target = path.resolve(opts.to);
  const excluded = [...new Set([...ALWAYS_EXCLUDED, ...opts.exclude])].sort(byCodePoint);
  const norm = (p) => (IS_WINDOWS ? p.toLowerCase() : p);
  if (!existsSync(source) || !statSync(source).isDirectory()) {
    return emit({ error: `source is not a directory: ${source}` }, EXIT.USAGE);
  }
  if (lexists(target)) {
    return emit({
      error: `destination already exists: ${target}. A copy is always fresh: pick a new `
        + 'directory, never overwrite one.',
    }, EXIT.USAGE);
  }
  if (norm(target).startsWith(norm(source) + path.sep)) {
    return emit({ error: `destination is inside the source: ${target}` }, EXIT.USAGE);
  }
  let copied = 0;
  cpSync(source, target, {
    recursive: true,
    verbatimSymlinks: true,
    preserveTimestamps: true,
    filter: (src) => {
      if (src !== source && excluded.includes(path.basename(src))) return false;
      if (lstatSync(src).isFile()) copied += 1;
      return true;
    },
  });
  return emit({
    copied, excluded, from: source, to: target,
  }, EXIT.OK);
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const USAGE = `Start and stop exactly the process tree this tool started
(06-validation-protocol.md section 1.3). Never stops anything else.

  node proc.mjs start  --state <file> --port <n> [--cwd <dir>] [--log <file>]
                       [--env KEY=VALUE ...] [--timeout <s>] -- <argv...>
  node proc.mjs stop   --state <file> [--timeout <s>]
  node proc.mjs status --state <file>
  node proc.mjs copy   --from <dir> --to <new dir> [--exclude <name> ...]`;

function parseArgs(tokens) {
  const opts = { env: [], exclude: [] };
  for (let i = 0; i < tokens.length; i += 1) {
    const token = tokens[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const value = tokens[i + 1];
    if (value === undefined || value.startsWith('--')) { opts[key] = true; continue; }
    if (key === 'env' || key === 'exclude') opts[key].push(value);
    else opts[key] = value;
    i += 1;
  }
  return opts;
}

async function main() {
  const all = process.argv.slice(2);
  const split = all.indexOf('--');
  const head = split >= 0 ? all.slice(0, split) : all;
  const command = split >= 0 ? all.slice(split + 1) : [];
  const [mode, ...rest] = head;
  const opts = parseArgs(rest);

  const usable = mode === 'copy'
    ? typeof opts.from === 'string' && typeof opts.to === 'string'
    : ['start', 'stop', 'status'].includes(mode) && typeof opts.state === 'string'
      && (mode !== 'start' || /^\d+$/.test(String(opts.port)));
  if (!usable) {
    console.error(USAGE);
    return EXIT.USAGE;
  }
  try {
    if (mode === 'start') return await cmdStart(opts, command);
    if (mode === 'stop') return await cmdStop(opts);
    if (mode === 'copy') return cmdCopy(opts);
    return await cmdStatus(opts);
  } catch (err) {
    return emit({ error: `${err.name}: ${err.message}` }, EXIT.USAGE);
  }
}

process.exitCode = await main();
