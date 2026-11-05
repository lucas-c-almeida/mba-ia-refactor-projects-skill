"""
The lifecycle tools inside slim container images (round 7, R11).

Why it exists: in round 6, `proc start` failed in every slim image with "could not read the
start time of the new process" -- the tools read the start time through `ps`, and slim images
do not ship it. The agents then improvised around the tool. proc now reads /proc/<pid>/stat
on Linux; this check runs each implementation in a slim image of its own runtime, confirms
`ps` really is absent there (otherwise the check proves nothing), and drives start, status,
stop and a second stop.

Opt-in, because it needs a container runtime and the images locally:
  python tests/probe-conformance/run.py --container

Every container is named refactor-arch-conformance-<impl>-<random hex> and removed by that
exact name, never by image or pattern (decision D19).
"""

import binascii
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, ".claude", "skills", "refactor-arch", "scripts")
PORT = "8099"
CASES = {
    "py": {
        "image": "python:3.13-slim",
        "tool": ["python", "/s/proc.py"],
        "server": ["python", "-m", "http.server", PORT, "--bind", "127.0.0.1"],
    },
    "node": {
        "image": "node:24-bookworm-slim",
        "tool": ["node", "/s/proc.mjs"],
        "server": ["node", "-e", "require('http').createServer((q, s) => s.end('ok'))"
                   ".listen(" + PORT + ", '127.0.0.1')"],
    },
}


def docker(*args, timeout=120):
    done = subprocess.run(["docker"] + list(args), capture_output=True, timeout=timeout)
    return done.returncode, done.stdout.decode("utf-8", "replace").strip()


def last_json(text):
    try:
        return json.loads(text.splitlines()[-1]) if text else {}
    except ValueError:
        return {"unparsed": text}


def check_one(impl, case, failures):
    name = "refactor-arch-conformance-{0}-{1}".format(
        impl, binascii.hexlify(os.urandom(4)).decode("ascii"))
    code, out = docker("run", "-d", "--name", name, "-v", SCRIPTS + ":/s:ro", case["image"],
                       "sleep", "infinity")
    if code != 0:
        failures.append("container {0}: could not start {1}: {2}".format(impl, case["image"],
                                                                       out))
        return
    try:
        code, _ = docker("exec", name, "which", "ps")
        if code == 0:
            failures.append("container {0}: {1} ships `ps`, so this check does not exercise "
                            "the slim path".format(impl, case["image"]))
        steps = [
            ("start", ["start", "--state", "/tmp/app.json", "--port", PORT, "--timeout", "30",
                       "--"] + case["server"], 0),
            ("status", ["status", "--state", "/tmp/app.json"], 0),
            ("stop", ["stop", "--state", "/tmp/app.json"], 0),
            ("status after stop", ["status", "--state", "/tmp/app.json"], 1),
            ("second stop", ["stop", "--state", "/tmp/app.json"], 0),
        ]
        for label, args, want in steps:
            code, out = docker("exec", name, *(case["tool"] + args))
            if code != want:
                failures.append("container {0}: {1}: expected exit {2}, got {3}: {4}".format(
                    impl, label, want, code, last_json(out)))
                break
        else:
            code, out = docker("exec", name, *(case["tool"] + ["wait", "--port", PORT,
                                                                "--timeout", "1"]))
            if code != 4:
                failures.append("container {0}: the port still answers after stop".format(impl))
    finally:
        docker("rm", "-f", name)


def check_containers():
    failures = []
    code, _ = docker("version", "--format", "{{.Server.Version}}", timeout=30)
    if code != 0:
        return ["container check requested, but no container runtime answers"]
    for impl, case in CASES.items():
        check_one(impl, case, failures)
    return failures
