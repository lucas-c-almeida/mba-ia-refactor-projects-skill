#!/usr/bin/env python3
"""
proc.py -- reference implementation of the process-ownership rules of
           references/06-validation-protocol.md section 1.3, for host mode.

Python standard library ONLY. Works on Python 3.8+, on POSIX and Windows.

Why it exists
-------------
The skill starts and stops the application several times per run. Stopping it by hand is
where things go wrong: an agent that lost track of its PID reaches for "kill everything
called python", and takes down processes that are not its own. This tool makes the safe
path the easy one. It stops exactly the process tree it started, and nothing else.

What it does
------------
  start   run an argv the AGENT derived, in a new process group, record who it started,
          wait until the port accepts connections
  stop    stop the recorded tree -- after checking that the PID still belongs to the
          process that was started (PIDs are reused)
  status  is the recorded process alive, and does the port answer?

What it deliberately does NOT do
--------------------------------
  * It knows nothing about stacks. It never decides WHAT to run: the agent derives the boot
    command in Phase 1 and passes it after "--".
  * It never stops a process it did not start. No lookup by name, image, pattern or port.
  * It never frees a busy port. If the port is taken, it refuses to start: pick another port.

Usage
-----
  python proc.py start  --state <file> --port 8081 [--cwd <dir>] [--log <file>]
                        [--env KEY=VALUE ...] [--timeout 60] -- <argv...>
  python proc.py stop   --state <file> [--timeout 10]
  python proc.py status --state <file>

Every command prints one JSON line (keys sorted) and exits with:
  0 ok (status: running)       1 status: not running         2 usage or I/O error
  3 port already in use        4 not ready in time (stopped) 5 exited before ready
  6 PID identity mismatch: refused to stop a process it did not start
  7 port still answering after stop: something else holds it
"""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

STATE_VERSION = 1
IS_WINDOWS = os.name == "nt"
HOST = "127.0.0.1"

EXIT_OK, EXIT_NOT_RUNNING, EXIT_USAGE = 0, 1, 2
EXIT_PORT_BUSY, EXIT_NOT_READY, EXIT_EXITED = 3, 4, 5
EXIT_IDENTITY, EXIT_PORT_HELD = 6, 7

# One snapshot of every process, as "pid|parent|creation time". Win32_Process is the only
# built-in source that has the parent PID; Get-Process does not.
WINDOWS_SNAPSHOT = ("Get-CimInstance Win32_Process | ForEach-Object { '{0}|{1}|{2}' -f "
                    "$_.ProcessId, $_.ParentProcessId, "
                    "$_.CreationDate.ToUniversalTime().ToString('o') }")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def emit(document, code):
    print(json.dumps(document, sort_keys=True, ensure_ascii=False))
    return code


# ---------------------------------------------------------------------------
# Process identity
#
# A PID alone does not identify a process: once it exits, the number is reused. The
# identity is (PID, start time as the OS reports it). Neither the standard library nor
# Node exposes the start time portably, so both implementations ask the same OS tools.
# ---------------------------------------------------------------------------

def _run(argv, timeout=30):
    try:
        done = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              stdin=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.decode("utf-8", "replace")


def windows_snapshot():
    """{pid: (parent, creation)} for every process, or None if the snapshot failed."""
    out = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_SNAPSHOT])
    if out is None:
        return None
    table = {}
    for line in out.splitlines():
        parts = line.strip().split("|")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            table[int(parts[0])] = (int(parts[1]), parts[2])
    return table


def start_token(pid, snapshot=None):
    """The OS start time of a live process, or None if it is not running."""
    if IS_WINDOWS:
        table = snapshot if snapshot is not None else windows_snapshot()
        entry = (table or {}).get(pid)
        return entry[1] if entry else None
    out = _run(["ps", "-o", "lstart=", "-p", str(pid)])
    token = (out or "").strip()
    return token or None


def windows_descendants(root, table):
    """PIDs below root, following parent links. A child must not predate its parent:
    that is how a reused parent PID is told apart from the real one."""
    found, frontier = [], [root]
    while frontier:
        parent = frontier.pop()
        parent_created = table.get(parent, (None, ""))[1]
        for pid, (ppid, created) in table.items():
            if ppid == parent and pid != parent and pid not in found and created >= parent_created:
                found.append(pid)
                frontier.append(pid)
    return sorted(found)


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------

def port_answers(port):
    try:
        with socket.create_connection((HOST, port), timeout=1):
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# State file
# ---------------------------------------------------------------------------

def read_state(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_state(path, state):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(state, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def log_tail(path, lines=20):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().splitlines()[-lines:]
    except OSError:
        return []


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------

def resolve_argv(argv):
    """On Windows a .cmd/.bat launcher cannot be spawned directly; run it through cmd.exe.
    Prefer the runtime itself (node server.js) -- the tree is then one process shorter."""
    if not IS_WINDOWS:
        return argv
    found = shutil.which(argv[0])
    if found and found.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/d", "/c"] + argv
    return argv


def spawn(argv, cwd, env, log_handle):
    common = dict(cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=log_handle,
                  stderr=subprocess.STDOUT)
    if not IS_WINDOWS:
        # A new session: the process leads its own group, so stop can signal the whole tree.
        return subprocess.Popen(argv, start_new_session=True, **common)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    breakaway = 0x01000000   # CREATE_BREAKAWAY_FROM_JOB: survive the calling shell's job
    try:
        return subprocess.Popen(argv, creationflags=flags | breakaway, **common)
    except OSError:
        return subprocess.Popen(argv, creationflags=flags, **common)


def cmd_start(args):
    if not args.argv:
        return emit({"error": "nothing to run: pass the boot command after --"}, EXIT_USAGE)
    if os.path.exists(args.state):
        previous = read_state(args.state)
        if not previous.get("stoppedAt") and start_token(previous["pid"]) == previous.get("startToken"):
            return emit({"error": "the state file already tracks a live process: stop it first",
                         "pid": previous["pid"]}, EXIT_USAGE)
    if port_answers(args.port):
        return emit({"error": "port {0} is already in use by a process this run did not start. "
                              "Pick another port; never stop the process holding it."
                              .format(args.port), "port": args.port}, EXIT_PORT_BUSY)

    env = dict(os.environ)
    for pair in args.env or []:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            return emit({"error": "--env expects KEY=VALUE, got {0!r}".format(pair)}, EXIT_USAGE)
        env[key] = value

    log_path = args.log or args.state + ".log"
    argv = resolve_argv(args.argv)
    cwd = os.path.abspath(args.cwd or os.getcwd())
    with open(log_path, "ab") as log_handle:
        child = spawn(argv, cwd, env, log_handle)

    token = None
    for _ in range(5):
        token = start_token(child.pid)
        if token is not None or child.poll() is not None:
            break
        time.sleep(0.2)
    if token is None and child.poll() is None:
        # Without an identity, a later stop could not tell this process from a stranger
        # that reuses its PID. Stop it now, while we still hold its handle (an open handle
        # keeps the PID from being reused), and refuse.
        if IS_WINDOWS:
            _run(["taskkill", "/PID", str(child.pid), "/T", "/F"])
        else:
            os.killpg(child.pid, signal.SIGKILL)
        child.wait()
        return emit({"error": "could not read the start time of the new process, so it could "
                              "not be stopped safely later; it was stopped. Host mode is "
                              "unavailable here: declare it (protocol section 1.3)",
                     "pid": child.pid}, EXIT_USAGE)
    state = {
        "version": STATE_VERSION, "pid": child.pid, "argv": argv, "cwd": cwd,
        "port": args.port, "log": os.path.abspath(log_path), "launchedAt": now(),
        "startToken": token, "descendants": [],
        "readyAt": None, "stoppedAt": None, "stopResult": None,
    }
    write_state(args.state, state)     # recorded before readiness: a failed start is stoppable

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        code = child.poll()
        if code is not None:
            state["stoppedAt"], state["stopResult"] = now(), "exited before ready"
            write_state(args.state, state)
            return emit({"error": "the process exited with code {0} before the port answered"
                                  .format(code), "exitCode": code, "logTail": log_tail(log_path),
                         "pid": child.pid}, EXIT_EXITED)
        if port_answers(args.port):
            state["readyAt"] = now()
            if IS_WINDOWS:
                table = windows_snapshot() or {}
                state["descendants"] = [[pid, table[pid][1]]
                                        for pid in windows_descendants(child.pid, table)]
            write_state(args.state, state)
            return emit({"state": "running", "pid": child.pid, "port": args.port,
                         "stateFile": os.path.abspath(args.state), "log": state["log"]}, EXIT_OK)
        time.sleep(0.25)

    stop_tree(state, 10)
    state["stoppedAt"], state["stopResult"] = now(), "not ready in time"
    write_state(args.state, state)
    return emit({"error": "the port did not answer within {0}s; the process was stopped"
                          .format(args.timeout), "logTail": log_tail(log_path),
                 "pid": child.pid}, EXIT_NOT_READY)


# ---------------------------------------------------------------------------
# stop
# ---------------------------------------------------------------------------

def _posix_group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def stop_tree(state, timeout):
    """Stop the recorded tree. Assumes the identity check already passed."""
    pid = state["pid"]
    if not IS_WINDOWS:
        # The group id is the leader's PID. POSIX never reuses a PID while a group of that
        # id still exists, so signalling the group is safe even if the leader has exited.
        if not _posix_group_alive(pid):
            return
        os.killpg(pid, signal.SIGTERM)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and _posix_group_alive(pid):
            time.sleep(0.2)
        if _posix_group_alive(pid):
            os.killpg(pid, signal.SIGKILL)
        return

    table = windows_snapshot() or {}
    targets = []
    if pid in table and table[pid][1] == state.get("startToken"):
        targets.append(pid)
        targets.extend(windows_descendants(pid, table))
    # Descendants recorded at readiness, still alive with the same identity: they may have
    # been orphaned by a parent that exited, which /T can no longer reach.
    for child, token in state.get("descendants") or []:
        if child in table and table[child][1] == token and child not in targets:
            targets.append(child)
    for target in targets:
        _run(["taskkill", "/PID", str(target), "/T", "/F"])


def cmd_stop(args):
    state = read_state(args.state)
    if state.get("stoppedAt"):
        return emit({"state": "stopped", "pid": state["pid"], "note": "already stopped: "
                     + str(state.get("stopResult"))}, EXIT_OK)

    token = start_token(state["pid"])
    if token is not None and token != state.get("startToken"):
        return emit({"error": "PID {0} now belongs to a different process (start time {1}, "
                              "recorded {2}). Refusing to stop it. The recorded process is gone."
                              .format(state["pid"], token, state.get("startToken")),
                     "pid": state["pid"]}, EXIT_IDENTITY)

    stop_tree(state, args.timeout)
    state["stoppedAt"] = now()
    state["stopResult"] = "stopped" if token is not None else "was not running"

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline and port_answers(state["port"]):
        time.sleep(0.2)
    write_state(args.state, state)
    if port_answers(state["port"]):
        return emit({"error": "port {0} still answers after the recorded tree was stopped: "
                              "another process holds it. Investigate; never stop it by port."
                              .format(state["port"]), "pid": state["pid"]}, EXIT_PORT_HELD)
    return emit({"state": "stopped", "pid": state["pid"], "note": state["stopResult"]}, EXIT_OK)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def cmd_status(args):
    state = read_state(args.state)
    token = start_token(state["pid"])
    alive = token is not None and token == state.get("startToken") and not state.get("stoppedAt")
    document = {"state": "running" if alive else "not running", "pid": state["pid"],
                "port": state["port"], "portAnswers": port_answers(state["port"])}
    return emit(document, EXIT_OK if alive else EXIT_NOT_RUNNING)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = []
    if "--" in argv:
        split = argv.index("--")
        argv, command = argv[:split], argv[split + 1:]

    parser = argparse.ArgumentParser(
        description="Start and stop exactly the process tree this tool started "
                    "(06-validation-protocol.md section 1.3). Never stops anything else.")
    sub = parser.add_subparsers(dest="mode")
    start_parser = sub.add_parser("start", help="run the argv given after --")
    start_parser.add_argument("--state", required=True)
    start_parser.add_argument("--port", required=True, type=int)
    start_parser.add_argument("--cwd")
    start_parser.add_argument("--log")
    start_parser.add_argument("--env", action="append")
    start_parser.add_argument("--timeout", type=float, default=60.0)
    stop_parser = sub.add_parser("stop", help="stop the recorded tree")
    stop_parser.add_argument("--state", required=True)
    stop_parser.add_argument("--timeout", type=float, default=10.0)
    status_parser = sub.add_parser("status", help="report on the recorded process")
    status_parser.add_argument("--state", required=True)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser.parse_args(argv)
    if not args.mode:
        parser.print_help()
        return EXIT_USAGE
    try:
        if args.mode == "start":
            args.argv = command
            return cmd_start(args)
        if args.mode == "stop":
            return cmd_stop(args)
        return cmd_status(args)
    except (OSError, ValueError, KeyError) as err:
        return emit({"error": "{0}: {1}".format(type(err).__name__, err)}, EXIT_USAGE)


if __name__ == "__main__":
    sys.exit(main())
