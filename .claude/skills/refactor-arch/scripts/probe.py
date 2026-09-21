#!/usr/bin/env python3
"""
probe.py -- reference implementation of references/06-validation-protocol.md
            for targets whose runtime is Python.

Python standard library ONLY (urllib, json, argparse). Works on Python 3.8+.
No pip install, ever: the harness must never change the target's dependency set.

What it does
------------
  capture   exercise a surface inventory against a RUNNING application and write a baseline
  compare   produce a current capture (live, or from a file) and diff it against a baseline

What it deliberately does NOT do
--------------------------------
  * It never boots the application. Booting is stack-specific; probing is protocol-pure.
    The agent boots and waits for readiness, then calls this script.
  * It never compares values -- only status, media type and the recursive SHAPE of the body.
    Comparing ids, timestamps or ordering would produce a false regression on every run,
    and a noisy check is worse than no check: it costs the same and you stop reading it.

Usage
-----
  python probe.py capture --surface reports/surface.json \
                          --base-url http://127.0.0.1:8081 \
                          --out reports/baseline.json

  python probe.py compare --surface reports/surface.json \
                          --baseline reports/baseline.json \
                          --base-url http://127.0.0.1:8081

  python probe.py compare --surface reports/surface.json \
                          --baseline reports/baseline.json \
                          --current reports/after.json

Exit codes: 0 = no regressions, 1 = at least one regression, 2 = usage or I/O error.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROTOCOL_VERSION = 1
DEFAULT_TIMEOUT = 10.0

# Result states (section 4 of the protocol).
PASS = "PASS"
REGRESSION = "REGRESSION"
PRE_EXISTING_FAILURE = "PRE-EXISTING FAILURE"
UNVERIFIED = "UNVERIFIED"


# ---------------------------------------------------------------------------
# Shape descriptor (protocol section 5)
#
# The descriptor captures the recursive set of keys and the type of each leaf,
# and nothing else. Array length and order are deliberately ignored: a collection
# whose row count depends on the datastore would otherwise fail on every run.
# ---------------------------------------------------------------------------

def shape_of(value):
    """Return the deterministic shape descriptor of a parsed JSON value."""
    if value is None:
        return "null"
    if isinstance(value, bool):          # checked before int: bool is a subclass of int
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return {"type": "array", "items": "empty"}
        # Deduplicate element descriptors by canonical serialization, then sort,
        # so two captures of the same shape serialize identically.
        seen = {}
        for element in value:
            descriptor = shape_of(element)
            seen[_canonical(descriptor)] = descriptor
        distinct = [seen[key] for key in sorted(seen)]
        if len(distinct) == 1:
            return {"type": "array", "items": distinct[0]}
        return {"type": "array", "items": {"oneOf": distinct}}
    if isinstance(value, dict):
        # sort_keys on dump makes the ordering canonical; building sorted here
        # keeps the in-memory structure readable too.
        return {
            "type": "object",
            "properties": {key: shape_of(value[key]) for key in sorted(value)},
        }
    return "unknown"


def _canonical(descriptor):
    """Stable string form of a descriptor, used for dedup and equality."""
    return json.dumps(descriptor, sort_keys=True, separators=(",", ":"))


def shapes_equal(left, right):
    return _canonical(left) == _canonical(right)


def shape_diff(baseline, current, path="$"):
    """
    Path-addressed differences between two descriptors.

    Returns a list of {kind, path, ...} where kind is one of
    'missing' (in baseline, absent now), 'added' (absent in baseline, present now)
    or 'typeChanged'.
    """
    diffs = []

    # Leaf vs leaf, or a structural kind change.
    if isinstance(baseline, str) or isinstance(current, str):
        if not shapes_equal(baseline, current):
            diffs.append({"kind": "typeChanged", "path": path,
                          "from": _summary(baseline), "to": _summary(current)})
        return diffs

    baseline_kind = baseline.get("type", "oneOf" if "oneOf" in baseline else "?")
    current_kind = current.get("type", "oneOf" if "oneOf" in current else "?")
    if baseline_kind != current_kind:
        diffs.append({"kind": "typeChanged", "path": path,
                      "from": _summary(baseline), "to": _summary(current)})
        return diffs

    if baseline_kind == "object":
        baseline_props = baseline.get("properties", {})
        current_props = current.get("properties", {})
        for key in sorted(set(baseline_props) - set(current_props)):
            diffs.append({"kind": "missing", "path": "{0}.{1}".format(path, key)})
        for key in sorted(set(current_props) - set(baseline_props)):
            diffs.append({"kind": "added", "path": "{0}.{1}".format(path, key)})
        for key in sorted(set(baseline_props) & set(current_props)):
            diffs.extend(shape_diff(baseline_props[key], current_props[key],
                                    "{0}.{1}".format(path, key)))
        return diffs

    if baseline_kind == "array":
        baseline_items = baseline.get("items")
        current_items = current.get("items")
        if baseline_items == "empty" or current_items == "empty":
            # An empty collection in one run and a populated one in the other is a
            # data difference, not a code difference. Report it, but as its own kind.
            if baseline_items != current_items:
                diffs.append({"kind": "typeChanged", "path": path + "[]",
                              "from": _summary(baseline_items),
                              "to": _summary(current_items)})
            return diffs
        return shape_diff(baseline_items, current_items, path + "[]")

    if not shapes_equal(baseline, current):
        diffs.append({"kind": "typeChanged", "path": path,
                      "from": _summary(baseline), "to": _summary(current)})
    return diffs


def _summary(descriptor):
    if isinstance(descriptor, str):
        return descriptor
    return descriptor.get("type", "oneOf" if "oneOf" in descriptor else "?")


# ---------------------------------------------------------------------------
# Exercising the surface (protocol section 3)
# ---------------------------------------------------------------------------

def normalize_content_type(raw):
    """Media type only -- parameters such as charset are not part of the contract here."""
    if not raw:
        return None
    return raw.split(";")[0].strip().lower()


def exercise(base_url, entry, timeout):
    """Issue one call and return its recorded result. Never raises."""
    entry_id = entry.get("id") or "{0} {1}".format(entry.get("method"), entry.get("path"))
    method = (entry.get("method") or "GET").upper()
    path = entry.get("path") or "/"
    record = {"id": entry_id, "method": method, "path": path,
              "state": UNVERIFIED, "status": None, "contentType": None,
              "shape": None, "error": None}

    if entry.get("skip"):
        record["error"] = entry.get("skipReason") or "skipped by inventory"
        return record

    url = base_url.rstrip("/") + path
    body = entry.get("body")
    data = None
    headers = dict(entry.get("headers") or {})
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.getcode()
            content_type = response.headers.get("Content-Type")
            payload = response.read()
    except urllib.error.HTTPError as err:
        # A 4xx/5xx is a real, recorded response -- not a transport failure.
        status = err.code
        content_type = err.headers.get("Content-Type") if err.headers else None
        try:
            payload = err.read()
        except Exception:
            payload = b""
    except Exception as err:                      # URLError, timeout, DNS, refused connection
        record["error"] = "{0}: {1}".format(type(err).__name__, err)
        return record

    record["state"] = "OBSERVED"
    record["status"] = status
    record["contentType"] = normalize_content_type(content_type)
    record["shape"] = _body_shape(payload, record["contentType"])
    return record


def _body_shape(payload, content_type):
    if not payload:
        return "empty"
    if content_type and "json" not in content_type:
        return {"type": "opaque", "bytes": "present"}
    try:
        return shape_of(json.loads(payload.decode("utf-8")))
    except Exception:
        # Declared as JSON but unparseable, or an unknown content type that is not JSON.
        return {"type": "opaque", "bytes": "present"}


def capture(surface, base_url, timeout):
    results = {}
    for entry in surface.get("entries", []):
        record = exercise(base_url, entry, timeout)
        results[record["id"]] = record
    return {
        "version": PROTOCOL_VERSION,
        # Timezone-aware on purpose: the naive utcnow() is deprecated on newer runtimes,
        # and a harness that emits its own deprecation warning is not a good teaching artifact.
        "capturedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseUrl": base_url,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Comparison (protocol section 4)
# ---------------------------------------------------------------------------

def _is_failure(record):
    """A baseline entry that was already broken: transport error or a server error."""
    if record.get("state") != "OBSERVED":
        return True
    status = record.get("status")
    return status is not None and status >= 500


def compare_one(baseline, current):
    """Return (state, details) for one entry."""
    details = []

    if baseline is None:
        return UNVERIFIED, ["not present in baseline"]
    if current is None:
        return UNVERIFIED, ["not exercised in replay"]
    if baseline.get("state") != "OBSERVED":
        return UNVERIFIED, ["baseline unverified: {0}".format(baseline.get("error"))]
    if current.get("state") != "OBSERVED":
        if _is_failure(baseline):
            return PRE_EXISTING_FAILURE, ["failed before and after: {0}".format(current.get("error"))]
        return REGRESSION, ["call failed after refactoring: {0}".format(current.get("error"))]

    same_status = baseline.get("status") == current.get("status")
    same_type = baseline.get("contentType") == current.get("contentType")
    diffs = [] if shapes_equal(baseline.get("shape"), current.get("shape")) else \
        shape_diff(baseline.get("shape"), current.get("shape"))

    if same_status and same_type and not diffs:
        # Identical -- but if it was already broken, that is not a success. You neither
        # fixed it nor broke it, and the report must say exactly that.
        if _is_failure(baseline):
            return PRE_EXISTING_FAILURE, [
                "unchanged failure: status {0}".format(baseline.get("status"))]
        return PASS, []

    if not same_status:
        details.append("statusChanged {0} -> {1}".format(baseline.get("status"),
                                                         current.get("status")))
    if not same_type:
        details.append("contentTypeChanged {0} -> {1}".format(baseline.get("contentType"),
                                                              current.get("contentType")))
    for diff in diffs:
        if diff["kind"] == "typeChanged":
            details.append("typeChanged {0}: {1} -> {2}".format(diff["path"], diff["from"],
                                                                diff["to"]))
        else:
            details.append("{0} {1}".format(diff["kind"], diff["path"]))

    # Already broken before, still broken in the same way -> neither pass nor regression.
    if _is_failure(baseline) and baseline.get("status") == current.get("status"):
        return PRE_EXISTING_FAILURE, details

    # Improvement is a behaviour change, so it is named rather than hidden -- but it is
    # not a regression.
    if _is_failure(baseline) and not _is_failure(current):
        return PASS, ["improved from {0}".format(baseline.get("status"))] + details

    return REGRESSION, details


def compare(baseline_doc, current_doc):
    baseline_results = baseline_doc.get("results", {})
    current_results = current_doc.get("results", {})
    rows = []
    for entry_id in sorted(set(baseline_results) | set(current_results)):
        state, details = compare_one(baseline_results.get(entry_id),
                                     current_results.get(entry_id))
        rows.append({"id": entry_id, "state": state, "details": details})
    return rows


# ---------------------------------------------------------------------------
# I/O and CLI
# ---------------------------------------------------------------------------

def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, document):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")


def print_table(rows):
    width = max([len(row["id"]) for row in rows] + [4])
    for row in rows:
        line = "  {0:<{1}}  {2}".format(row["id"], width, row["state"])
        print(line)
        for detail in row["details"]:
            print("  {0}    - {1}".format(" " * width, detail))


def summarize(rows):
    counts = {PASS: 0, REGRESSION: 0, PRE_EXISTING_FAILURE: 0, UNVERIFIED: 0}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    print("")
    print("  {0} PASS, {1} REGRESSION, {2} PRE-EXISTING FAILURE, {3} UNVERIFIED".format(
        counts[PASS], counts[REGRESSION], counts[PRE_EXISTING_FAILURE], counts[UNVERIFIED]))
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Baseline-then-replay surface probe (see 06-validation-protocol.md). "
                    "This script never boots the application.")
    sub = parser.add_subparsers(dest="mode")

    capture_parser = sub.add_parser("capture", help="exercise a running app and write a baseline")
    capture_parser.add_argument("--surface", required=True, help="surface inventory JSON")
    capture_parser.add_argument("--base-url", required=True, help="base URL of the running app")
    capture_parser.add_argument("--out", required=True, help="where to write the capture")
    capture_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    compare_parser = sub.add_parser("compare", help="diff a current capture against a baseline")
    compare_parser.add_argument("--surface", help="surface inventory JSON (needed with --base-url)")
    compare_parser.add_argument("--baseline", required=True, help="baseline capture JSON")
    compare_parser.add_argument("--base-url", help="capture live from this URL")
    compare_parser.add_argument("--current", help="use this already-captured file instead")
    compare_parser.add_argument("--out", help="optionally write the current capture here")
    compare_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    args = parser.parse_args(argv)
    if not args.mode:
        parser.print_help()
        return 2

    try:
        if args.mode == "capture":
            surface = read_json(args.surface)
            document = capture(surface, args.base_url, args.timeout)
            write_json(args.out, document)
            observed = sum(1 for r in document["results"].values() if r["state"] == "OBSERVED")
            skipped = len(document["results"]) - observed
            print("captured {0} entries ({1} observed, {2} unverified) -> {3}".format(
                len(document["results"]), observed, skipped, args.out))
            return 0

        baseline_doc = read_json(args.baseline)
        if args.current:
            current_doc = read_json(args.current)
        elif args.base_url and args.surface:
            current_doc = capture(read_json(args.surface), args.base_url, args.timeout)
            if args.out:
                write_json(args.out, current_doc)
        else:
            print("compare needs either --current, or both --base-url and --surface",
                  file=sys.stderr)
            return 2

        rows = compare(baseline_doc, current_doc)
        if not rows:
            print("nothing to compare: the inventory produced no entries", file=sys.stderr)
            return 2
        print_table(rows)
        counts = summarize(rows)
        return 1 if counts[REGRESSION] else 0

    except (OSError, ValueError) as err:
        print("probe: {0}".format(err), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
