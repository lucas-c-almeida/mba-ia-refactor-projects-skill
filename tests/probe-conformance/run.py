#!/usr/bin/env python3
"""
Conformance test for the two reference harnesses of the refactor-arch skill:
  .claude/skills/refactor-arch/scripts/probe.py
  .claude/skills/refactor-arch/scripts/probe.mjs

Why it exists: 06-validation-protocol.md is the normative spec and the probes are
translations of it. Translations drift. Round 1 found one probe recording a transport
error differently from what the spec says; this test is what would have caught it.

What it checks
  1. Both probes, run against the same fixture servers, write byte-identical baseline and
     current captures (after blanking the timestamp and the free-text transport error).
  2. Both print byte-identical compare output and exit with the same code.
  3. A capture from one implementation is comparable by the other.
  4. Every fixture ends in the result state the spec prescribes.

It lives outside the skill on purpose: it is maintenance tooling for the skill's authors,
not something the skill ships into a target. Needs Python 3.8+ and Node 18+ on PATH.

  python tests/probe-conformance/run.py
"""

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(ROOT, ".claude", "skills", "refactor-arch", "scripts")
PROBES = {
    "py": [sys.executable, os.path.join(SCRIPTS, "probe.py")],
    "node": ["node", os.path.join(SCRIPTS, "probe.mjs")],
}

# (method, path) -> {"before": response, "after": response}
# A response is (status, headers, body) or the string "crash" (close without answering).
J = {"Content-Type": "application/json"}
T = {"Content-Type": "text/plain; charset=utf-8"}
FIXTURES = {
    ("GET", "/items"): {
        "before": (200, J, [{"id": 1, "label": "a"}, {"id": 2, "label": "b"}]),
        "after": (200, J, [{"id": 7, "label": "z"}]),
    },
    ("GET", "/odd-keys"): {   # integer-like and non-ASCII keys: the byte-compatibility trap
        "before": (200, J, {"10": 1, "9": 2, "é": 3, "a": {"b": [1, "x", None]}}),
        "after": (200, J, {"9": 5, "10": 6, "a": {"b": ["y", None, 2]}, "é": 4}),
    },
    ("GET", "/text-same"): {  # only volatile values differ: masked, so equal
        "before": (200, T, "Order 42 created at 2026-01-01T10:00:00Z\ntoken 0f3c9a2b4d5e6f70aa\n"),
        "after": (200, T, "Order 977 created at 2026-02-03T11:12:13Z\ntoken 99aa88bb77cc66dd00\n"),
    },
    ("GET", "/text-changed"): {  # the wording changed: must be seen (round-1 issue #5)
        "before": (404, T, "Item not found"),
        "after": (404, T, "Resource missing"),
    },
    ("GET", "/crash"): {      # a transport error in the baseline is a failure (issue #4)
        "before": "crash",
        "after": (200, J, {"ok": True}),
    },
    ("GET", "/boom"): {
        "before": (500, J, {"error": "x"}),
        "after": (500, J, {"error": "y"}),
    },
    ("GET", "/redirect"): {   # must be recorded, not followed
        "before": (302, {"Location": "/items/7"}, ""),
        "after": (302, {"Location": "/items/8"}, ""),
    },
    ("GET", "/cors"): {       # contract header changed (issue #10)
        "before": (200, dict(J, **{"Access-Control-Allow-Origin": "*"}), {"a": 1}),
        "after": (200, dict(J, **{"Access-Control-Allow-Origin": "http://example.test"}), {"a": 1}),
    },
    ("GET", "/cookie"): {     # cookie names compared, values ignored
        "before": (200, dict(J, **{"Set-Cookie": ["sid=abc; Path=/", "theme=dark"]}), {}),
        "after": (200, dict(J, **{"Set-Cookie": ["theme=light", "sid=xyz; Path=/; HttpOnly"]}), {}),
    },
    ("GET", "/missing-field"): {
        "before": (200, J, {"a": 1, "b": 2}),
        "after": (200, J, {"a": 1}),
    },
    ("DELETE", "/nothing"): {
        "before": (204, {}, ""),
        "after": (204, {}, ""),
    },
    ("POST", "/hostile"): {   # security entry, fixed (issue #9)
        "before": (201, J, {"id": 1}),
        "after": (422, J, {"error": "invalid"}),
    },
    ("POST", "/hostile-unfixed"): {
        "before": (200, J, {"ok": True}),
        "after": (200, J, {"ok": True}),
    },
    ("GET", "/late"): {       # added to the inventory after the baseline (issue #12)
        "before": (200, J, {"n": 1}),
        "after": (200, J, {"n": 2}),
    },
}

SURFACE = {
    "version": 2,
    "appType": "http",
    "entries": [
        {"id": "get-items", "method": "GET", "path": "/items"},
        {"id": "get-odd-keys", "method": "GET", "path": "/odd-keys"},
        {"id": "get-text-same", "method": "GET", "path": "/text-same"},
        {"id": "get-text-changed", "method": "GET", "path": "/text-changed"},
        {"id": "hostile", "method": "POST", "path": "/hostile", "body": {"from": "2026-05-10", "to": "2026-05-02"},
         "kind": "security", "finding": "AP-11", "expect": "rejected"},
        {"id": "get-crash", "method": "GET", "path": "/crash"},
        {"id": "get-boom", "method": "GET", "path": "/boom"},
        {"id": "get-redirect", "method": "GET", "path": "/redirect"},
        {"id": "get-cors", "method": "GET", "path": "/cors",
         "headers": {"Origin": "http://client.test"}},
        {"id": "get-cookie", "method": "GET", "path": "/cookie"},
        {"id": "get-missing-field", "method": "GET", "path": "/missing-field"},
        {"id": "delete-nothing", "method": "DELETE", "path": "/nothing"},
        {"id": "hostile-unfixed", "method": "POST", "path": "/hostile-unfixed",
         "body": {"q": "' OR 1=1"}, "kind": "security", "finding": "AP-02",
         "expect": "rejected"},
        {"id": "get-skipped", "method": "GET", "path": "/items", "skip": True,
         "skipReason": "fixture: skipped on purpose"},
        {"id": "get-late", "method": "GET", "path": "/late"},
    ],
}

EXPECTED = {
    "get-items": "PASS",
    "get-odd-keys": "PASS",
    "get-text-same": "PASS",
    "get-text-changed": "REGRESSION",
    "get-crash": "PASS",
    "get-boom": "PRE-EXISTING FAILURE",
    "get-redirect": "PASS",
    "get-cors": "REGRESSION",
    "get-cookie": "PASS",
    "get-missing-field": "REGRESSION",
    "delete-nothing": "PASS",
    "hostile": "FIXED",
    "hostile-unfixed": "NOT FIXED",
    "get-skipped": "UNVERIFIED",
    "get-late": "PASS",
}


def make_handler(mode):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def _serve(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            spec = FIXTURES.get((self.command, self.path.split("?")[0]))
            if spec is None:
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            response = spec[mode]
            if response == "crash":
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            status, headers, body = response
            if isinstance(body, (dict, list)):
                payload = json.dumps(body).encode("utf-8")
            else:
                payload = body.encode("utf-8")
            self.send_response(status)
            for name, value in headers.items():
                for item in (value if isinstance(value, list) else [value]):
                    self.send_header(name, item)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = do_DELETE = _serve

    return Handler


def start(mode):
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(mode))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, "http://127.0.0.1:{0}".format(server.server_address[1])


def run(impl, *args):
    proc = subprocess.run(PROBES[impl] + list(args), capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8").replace("\r\n", "\n"), \
        proc.stderr.decode("utf-8", "replace")


VOLATILE = [
    (re.compile(r'"capturedAt": "[^"]*"'), '"capturedAt": "<t>"'),
    (re.compile(r'"baseUrl": "[^"]*"'), '"baseUrl": "<url>"'),
    (re.compile(r'"error": "(?:ERROR|[A-Za-z]*Error)[^"]*"'), '"error": "<transport>"'),
    (re.compile(r'"error": "[^"]*(?:Error|failed|closed|reset|RemoteDisconnected)[^"]*"'),
     '"error": "<transport>"'),
]


def normalized(path):
    with open(path, "rb") as handle:
        text = handle.read().decode("utf-8")
    for pattern, placeholder in VOLATILE:
        text = pattern.sub(placeholder, text)
    return text


def states(stdout):
    found = {}
    for line in stdout.splitlines():
        match = re.match(r"^  (\S+)\s{2,}(\S.*)$", line)
        if match and not line.strip().startswith("-"):
            found[match.group(1)] = match.group(2).strip()
    return found


def main():
    failures = []
    before, before_url = start("before")
    after, after_url = start("after")
    work = tempfile.mkdtemp(prefix="probe-conformance-")
    surface = os.path.join(work, "surface.json")
    with open(surface, "w", encoding="utf-8") as handle:
        json.dump(SURFACE, handle)
    all_but_late = ",".join(e["id"] for e in SURFACE["entries"] if e["id"] != "get-late")

    outputs = {}
    try:
        for impl in PROBES:
            base = os.path.join(work, "base-{0}.json".format(impl))
            cur = os.path.join(work, "cur-{0}.json".format(impl))
            code, _, err = run(impl, "capture", "--surface", surface, "--base-url", before_url,
                               "--out", base, "--only", all_but_late)
            if code != 0:
                failures.append("{0}: capture failed ({1}): {2}".format(impl, code, err))
                continue
            code, _, err = run(impl, "capture", "--surface", surface, "--base-url", before_url,
                               "--out", base, "--only", "get-late", "--merge")
            if code != 0:
                failures.append("{0}: merge capture failed ({1}): {2}".format(impl, code, err))
                continue
            code, out, err = run(impl, "compare", "--surface", surface, "--baseline", base,
                                 "--base-url", after_url, "--out", cur)
            outputs[impl] = {"base": base, "cur": cur, "code": code, "out": out, "err": err}
    finally:
        before.shutdown()
        after.shutdown()

    if set(outputs) == set(PROBES):
        py, node = outputs["py"], outputs["node"]
        for label in ("base", "cur"):
            if normalized(py[label]) != normalized(node[label]):
                failures.append("{0} capture differs between implementations: {1} vs {2}".format(
                    label, py[label], node[label]))
        if py["out"] != node["out"]:
            failures.append("compare output differs:\n--- py\n{0}\n--- node\n{1}".format(
                py["out"], node["out"]))
        if py["code"] != node["code"]:
            failures.append("exit codes differ: py {0}, node {1}".format(py["code"], node["code"]))
        if py["code"] != 1:
            failures.append("expected exit 1 (regressions present), got {0}".format(py["code"]))

        # Cross-implementation: a capture from one must be comparable by the other.
        _, cross_out, _ = run("py", "compare", "--baseline", node["base"], "--current", py["cur"])
        if cross_out != py["out"]:
            failures.append("cross comparison (node baseline, py current) differs")

        got = states(py["out"])
        for entry_id, expected in EXPECTED.items():
            if got.get(entry_id) != expected:
                failures.append("{0}: expected {1}, got {2}".format(
                    entry_id, expected, got.get(entry_id)))

        print(py["out"])

    if failures:
        print("CONFORMANCE FAILED ({0}):".format(len(failures)))
        for failure in failures:
            print("  - " + failure)
        print("work dir kept for inspection: " + work)
        return 1
    print("CONFORMANCE OK -- both probes agree on {0} fixtures".format(len(EXPECTED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
