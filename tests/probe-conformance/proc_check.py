"""
Safety and conformance checks for the two lifecycle tools of the refactor-arch skill:
  .claude/skills/refactor-arch/scripts/proc.py
  .claude/skills/refactor-arch/scripts/proc.mjs

Why it exists: round 2 of the skill ended with an agent stopping "every python.exe" on the
host. proc is the fix, and a fix that is not tested is a claim. The central check is the
decoy: a process this test starts on its own, which proc must never touch -- not when it
stops its own tree, and not when a state file points at the decoy's PID.

It also holds `proc copy` (the fresh copies of protocol section 1.1) to one behaviour in
both implementations: VCS directories left out, the destination never overwritten.

Run through tests/probe-conformance/run.py.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, ".claude", "skills", "refactor-arch", "scripts")
TOOLS = {
    "py": [sys.executable, os.path.join(SCRIPTS, "proc.py")],
    "node": ["node", os.path.join(SCRIPTS, "proc.mjs")],
}

# A server one level down the tree, as a reloader or a launcher shim would leave it: the
# process proc starts is not the one listening.
TREE = ("import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-m', 'http.server', sys.argv[1], "
        "'--bind', '127.0.0.1'])\n"
        "time.sleep(600)\n")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def answers(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def call(impl, *args):
    done = subprocess.run(TOOLS[impl] + list(args), capture_output=True, timeout=120)
    out = done.stdout.decode("utf-8", "replace").strip()
    try:
        document = json.loads(out.splitlines()[-1]) if out else {}
    except ValueError:
        document = {"unparsed": out}
    return done.returncode, document


def check_one(impl, work, decoy, failures):
    shapes = []

    def expect(label, got, want):
        if got != want:
            failures.append("proc {0}: {1}: expected exit {2}, got {3}".format(impl, label,
                                                                             want, got))

    state = os.path.join(work, "{0}-server.json".format(impl))
    port = free_port()
    code, doc = call(impl, "start", "--state", state, "--port", str(port), "--timeout", "30",
                     "--", sys.executable, "-c", TREE, str(port))
    expect("start", code, 0)
    shapes.append(("start", sorted(doc)))

    other = os.path.join(work, "{0}-busy.json".format(impl))
    code, doc = call(impl, "start", "--state", other, "--port", str(port),
                     "--", sys.executable, "-m", "http.server", str(port))
    expect("start on a busy port", code, 3)
    shapes.append(("busy", sorted(doc)))

    code, doc = call(impl, "status", "--state", state)
    expect("status while running", code, 0)
    shapes.append(("status", sorted(doc)))

    code, doc = call(impl, "stop", "--state", state)
    expect("stop", code, 0)
    shapes.append(("stop", sorted(doc)))
    if answers(port):
        failures.append("proc {0}: the server one level down still answers after stop".format(
            impl))
    if decoy.poll() is not None:
        failures.append("proc {0}: THE DECOY DIED -- stop reached a process it did not start"
                        .format(impl))

    code, doc = call(impl, "stop", "--state", state)
    expect("second stop", code, 0)

    # A state file that points at the decoy's PID, with a different identity: the situation
    # after a PID has been reused. proc must refuse, and the decoy must live.
    forged = os.path.join(work, "{0}-forged.json".format(impl))
    with open(forged, "w", encoding="utf-8") as handle:
        json.dump({"version": 1, "pid": decoy.pid, "startToken": "not-the-decoy",
                   "port": free_port(), "descendants": [], "stoppedAt": None}, handle)
    code, doc = call(impl, "stop", "--state", forged)
    expect("stop with a reused PID", code, 6)
    shapes.append(("identity", sorted(doc)))
    if decoy.poll() is not None:
        failures.append("proc {0}: THE DECOY DIED -- a forged state file made proc stop it"
                        .format(impl))

    exits = os.path.join(work, "{0}-exits.json".format(impl))
    code, doc = call(impl, "start", "--state", exits, "--port", str(free_port()),
                     "--", sys.executable, "-c", "import sys; sys.exit(3)")
    expect("process that exits before ready", code, 5)
    shapes.append(("exits", sorted(doc)))

    shapes.extend(check_copy(impl, work, expect, failures))
    return shapes


def make_tree(root):
    for rel, text in (("app.txt", "a"), ("pkg/mod.txt", "b"), (".git/HEAD", "ref"),
                      ("pkg/.git", "gitdir: elsewhere"), ("cache/tmp.txt", "c")):
        full = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)


def check_copy(impl, work, expect, failures):
    shapes = []
    source = os.path.join(work, "{0}-tree".format(impl))
    make_tree(source)
    dest = os.path.join(work, "{0}-copies".format(impl), "run-1")
    code, doc = call(impl, "copy", "--from", source, "--to", dest, "--exclude", "cache")
    expect("copy", code, 0)
    shapes.append(("copy", sorted(doc), doc.get("copied"), doc.get("excluded")))
    found = sorted(os.path.relpath(os.path.join(d, f), dest).replace(os.sep, "/")
                   for d, _, files in os.walk(dest) for f in files)
    if found != ["app.txt", "pkg/mod.txt"]:
        failures.append("proc {0}: copy produced {1}, expected app.txt and pkg/mod.txt only"
                        .format(impl, found))

    code, doc = call(impl, "copy", "--from", source, "--to", dest)
    expect("copy onto an existing destination", code, 2)
    shapes.append(("copy exists", sorted(doc)))

    code, doc = call(impl, "copy", "--from", source, "--to", os.path.join(source, "inner"))
    expect("copy into the source", code, 2)
    shapes.append(("copy inside", sorted(doc)))
    if os.path.exists(os.path.join(source, "inner")):
        failures.append("proc {0}: copy into the source wrote something".format(impl))
    return shapes


def check_proc():
    failures = []
    work = tempfile.mkdtemp(prefix="proc-conformance-")
    decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        time.sleep(0.5)
        shapes = {impl: check_one(impl, work, decoy, failures) for impl in TOOLS}
        if shapes["py"] != shapes["node"]:
            failures.append("proc output keys differ between implementations:\n  py   {0}\n"
                            "  node {1}".format(shapes["py"], shapes["node"]))
    finally:
        decoy.kill()
        decoy.wait()
    if failures:
        failures.append("proc work dir kept for inspection: " + work)
    return failures
