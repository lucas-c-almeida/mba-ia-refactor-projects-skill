#!/usr/bin/env python3
"""
probe.py -- reference implementation of references/06-validation-protocol.md
            for targets whose runtime is Python.

Python standard library ONLY (urllib, json, re, argparse). Works on Python 3.8+.
No pip install, ever: the harness must never change the target's dependency set.

What it does
------------
  capture   exercise a surface inventory against a RUNNING application and write a baseline
  compare   produce a current capture (live, or from a file) and diff it against a baseline

What it deliberately does NOT do
--------------------------------
  * It never boots the application. Booting is stack-specific; probing is protocol-pure.
    The agent boots and waits for readiness, then calls this script.
  * It never compares raw values -- only status, media type, a small allow-list of contract
    headers, and the recursive SHAPE of the body. Comparing ids, timestamps or ordering would
    produce a false regression on every run, and a noisy check is worse than no check: it costs
    the same and you stop reading it.
  * It never follows redirects. A redirect is part of the contract; following it would record
    the target's response instead of the entry's own.

Usage
-----
  python probe.py capture --surface reports/surface.json \
                          --base-url http://127.0.0.1:8081 \
                          --out reports/baseline.json

  # capture only entries added after the baseline, against the ORIGINAL, into the same file
  python probe.py capture --surface reports/surface.json --base-url http://127.0.0.1:8081 \
                          --out reports/baseline.json --only new-entry-a,new-entry-b --merge

  python probe.py compare --surface reports/surface.json \
                          --baseline reports/baseline.json \
                          --base-url http://127.0.0.1:8081

  python probe.py compare --baseline reports/baseline.json --current reports/after.json

  # a destructive entry runs alone, on its own fresh boot, merged into the capture
  python probe.py capture --surface reports/surface.json --base-url http://127.0.0.1:8081 \
                          --out reports/baseline.json --only purge-archive --merge

Exit codes: 0 = no regressions, 1 = at least one regression, 2 = usage or I/O error.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROTOCOL_VERSION = 3
DEFAULT_TIMEOUT = 10.0
TEXT_LIMIT_BYTES = 4096

# Record states (protocol section 3).
OBSERVED = "OBSERVED"      # the call completed and a response was read
ERROR = "ERROR"            # the call was made and failed at transport level
SKIPPED = "SKIPPED"        # the call was never made

# Result states (protocol section 4).
PASS = "PASS"
REGRESSION = "REGRESSION"
PRE_EXISTING_FAILURE = "PRE-EXISTING FAILURE"
UNVERIFIED = "UNVERIFIED"
FIXED = "FIXED"
NOT_FIXED = "NOT FIXED"

# Value masks (protocol section 5.2), applied in this order. ASCII classes only, so that
# every implementation masks exactly the same characters.
MASKS = [
    (re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}"
                r"(?::[0-9]{2}(?:\.[0-9]+)?)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?"), "<ts>"),
    (re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"),
     "<uuid>"),
    (re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{16,}(?![0-9A-Za-z])"), "<hex>"),
    (re.compile(r"[0-9]+"), "<n>"),
]

# Contract headers (protocol section 5.3). Everything else is transport detail.
HEADER_EXACT = ("location", "www-authenticate")
HEADER_PREFIX = "access-control-"
HEADER_LISTS = ("access-control-allow-methods", "access-control-allow-headers",
                "access-control-expose-headers")


def mask(text):
    for pattern, placeholder in MASKS:
        text = pattern.sub(placeholder, text)
    return text


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
        return {
            "type": "object",
            "properties": {key: shape_of(value[key]) for key in sorted(value)},
        }
    return "unknown"


def text_shape(text):
    """Skeleton of a short text body: distinct non-empty lines, masked, sorted."""
    lines = set()
    for line in re.split(r"\r?\n", text):
        line = line.rstrip(" \t\r\f\v")         # ASCII whitespace only: identical in JS
        if line:
            lines.add(mask(line))
    return {"type": "text", "lines": sorted(lines)}


def _canonical(descriptor):
    """Stable string form of a descriptor, used for dedup and equality.

    ensure_ascii=False on purpose: the JS implementation does not escape either, and the
    sort order of oneOf members must be identical in both.
    """
    return json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def shapes_equal(left, right):
    return _canonical(left) == _canonical(right)


def _summary(descriptor):
    if isinstance(descriptor, str):
        return descriptor
    if descriptor is None:
        return "none"
    return descriptor.get("type", "oneOf" if "oneOf" in descriptor else "?")


def shape_diff(baseline, current, path="$"):
    """
    Path-addressed differences between two descriptors.

    Returns a list of {kind, path, ...} where kind is one of
    'missing' (in baseline, absent now), 'added' (absent in baseline, present now),
    'typeChanged', or 'textChanged' (the masked line set of a text body differs).
    """
    diffs = []

    if isinstance(baseline, str) or isinstance(current, str) \
            or baseline is None or current is None:
        if not shapes_equal(baseline, current):
            diffs.append({"kind": "typeChanged", "path": path,
                          "from": _summary(baseline), "to": _summary(current)})
        return diffs

    baseline_kind = _summary(baseline)
    current_kind = _summary(current)
    if baseline_kind != current_kind:
        diffs.append({"kind": "typeChanged", "path": path,
                      "from": baseline_kind, "to": current_kind})
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

    if baseline_kind == "text":
        before = set(baseline.get("lines", []))
        after = set(current.get("lines", []))
        if before != after:
            diffs.append({"kind": "textChanged", "path": path,
                          "removed": sorted(before - after), "added": sorted(after - before)})
        return diffs

    if not shapes_equal(baseline, current):
        diffs.append({"kind": "typeChanged", "path": path,
                      "from": baseline_kind, "to": current_kind})
    return diffs


def headers_diff(baseline, current):
    """Differences in the contract headers. Skipped when either side did not record them."""
    if baseline is None or current is None:
        return []
    details = []
    for name in sorted(set(baseline) | set(current)):
        if name not in current:
            details.append("headerMissing {0}".format(name))
        elif name not in baseline:
            details.append("headerAdded {0}".format(name))
        elif baseline[name] != current[name]:
            details.append("headerChanged {0}: {1} -> {2}".format(name, baseline[name],
                                                                  current[name]))
    return details


# ---------------------------------------------------------------------------
# Exercising the surface (protocol section 3)
# ---------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Record the redirect itself; never follow it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def normalize_content_type(raw):
    """Media type only -- parameters such as charset are not part of the contract here."""
    if not raw:
        return None
    return raw.split(";")[0].strip().lower()


def contract_headers(message):
    """The allow-listed headers of a response, normalized and masked (protocol 5.3)."""
    collected = {}
    cookies = []
    for name, value in message.items():
        lowered = name.lower()
        if lowered == "set-cookie":
            cookies.append(value)
        elif lowered in HEADER_EXACT or lowered.startswith(HEADER_PREFIX):
            collected.setdefault(lowered, []).append(value)
    result = {}
    for name, values in collected.items():
        joined = ", ".join(values)
        if name in HEADER_LISTS:
            parts = {part.strip().lower() for part in joined.split(",") if part.strip()}
            joined = ", ".join(sorted(parts))
        result[name] = mask(joined.strip())
    names = {cookie.split("=", 1)[0].strip() for cookie in cookies if "=" in cookie}
    if names:
        result["set-cookie"] = ", ".join(sorted(names))
    return result


def _reject_constant(name):
    # JSON has no NaN/Infinity; Python accepts them by default, JS does not. Refuse them so
    # both implementations classify the same body the same way.
    raise ValueError("non-standard JSON constant: " + name)


def _body_shape(payload):
    if not payload:
        return "empty"
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {"type": "opaque", "bytes": "present"}
    try:
        return shape_of(json.loads(text, parse_constant=_reject_constant))
    except ValueError:
        pass
    if len(payload) <= TEXT_LIMIT_BYTES:
        return text_shape(text)
    return {"type": "opaque", "bytes": "present"}


def exercise(base_url, entry, timeout):
    """Issue one call and return its recorded result. Never raises."""
    entry_id = entry.get("id") or "{0} {1}".format(entry.get("method"), entry.get("path"))
    method = (entry.get("method") or "GET").upper()
    path = entry.get("path") or "/"
    record = {"id": entry_id, "method": method, "path": path,
              "kind": entry.get("kind") or "contract", "finding": entry.get("finding"),
              "expect": entry.get("expect"), "like": entry.get("like"),
              "destructive": bool(entry.get("destructive")),
              "state": SKIPPED, "status": None, "contentType": None, "headers": None,
              "shape": None, "error": None}

    if entry.get("skip"):
        record["error"] = entry.get("skipReason") or "skipped by inventory"
        return record

    url = base_url.rstrip("/") + path
    body = entry.get("body")
    raw_body = entry.get("rawBody")
    data = None
    headers = dict(entry.get("headers") or {})
    if raw_body is not None:
        # Sent byte for byte: the point is a body the application's parser has not seen.
        data = raw_body.encode("utf-8")
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
    if data is not None and not any(name.lower() == "content-type" for name in headers):
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        try:
            with _OPENER.open(request, timeout=timeout) as response:
                status = response.getcode()
                message = response.headers
                payload = response.read()
        except urllib.error.HTTPError as err:
            # A 3xx/4xx/5xx is a real, recorded response -- not a transport failure.
            status = err.code
            message = err.headers
            payload = err.read() if err.fp is not None else b""
    except Exception as err:                      # refused, reset, timeout, truncated body
        record["state"] = ERROR
        record["error"] = "{0}: {1}".format(type(err).__name__, err)
        return record

    record["state"] = OBSERVED
    record["status"] = status
    record["contentType"] = normalize_content_type(message.get("Content-Type") if message else None)
    record["headers"] = contract_headers(message) if message else {}
    record["shape"] = _body_shape(payload)
    return record


def ordered_entries(surface, only=None):
    """
    Contract entries first, security entries last: a hostile call may mutate state.

    A destructive entry is exercised only when --only names it and nothing else (protocol
    section 2.2): it runs alone, on its own fresh boot, so that what it destroys cannot reach
    any other entry.
    """
    entries = [e for e in surface.get("entries", []) if only is None or e.get("id") in only]
    destructive = [e for e in entries if e.get("destructive")]
    if destructive:
        if only is None:
            entries = [e for e in entries if not e.get("destructive")]
        elif len(entries) > 1:
            raise ValueError("a destructive entry must be captured alone (--only <its id>), "
                             "on its own fresh boot (protocol section 2.2): "
                             + ",".join(sorted(e.get("id") for e in destructive)))
    regular = [e for e in entries if (e.get("kind") or "contract") != "security"]
    hostile = [e for e in entries if (e.get("kind") or "contract") == "security"]
    return regular + hostile


def destructive_ids(surface):
    return sorted(e.get("id") for e in surface.get("entries", []) if e.get("destructive"))


def capture(surface, base_url, timeout, only=None):
    results = {}
    for entry in ordered_entries(surface, only):
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

def _state(record):
    state = record.get("state")
    if state == "UNVERIFIED":
        # Protocol v1 used one state for "skipped" and "transport error" and cannot tell them
        # apart. Treat it as skipped: the v1 reading, and the one that claims nothing.
        return SKIPPED
    return state


def _server_error(record):
    return _state(record) == OBSERVED and (record.get("status") or 0) >= 500


def _is_failure(record):
    """Already broken: a transport error or a server error."""
    return _state(record) == ERROR or _server_error(record)


def _rejected(record):
    return _state(record) == OBSERVED and 400 <= (record.get("status") or 0) < 500


def _describe(record):
    return "transport error" if _state(record) == ERROR else str(record.get("status"))


def shapes_compatible(left, right):
    """
    Shape equality, except that an empty array matches any array. Used only to compare an
    entry with a DIFFERENT entry (its benign sibling), whose collection may be empty while
    this one's is not -- a data difference, not a behaviour difference.
    """
    if shapes_equal(left, right):
        return True
    if not isinstance(left, dict) or not isinstance(right, dict):
        return False
    if left.get("type") == "array" and right.get("type") == "array":
        if left.get("items") == "empty" or right.get("items") == "empty":
            return True
        return shapes_compatible(left.get("items"), right.get("items"))
    if left.get("type") == "object" and right.get("type") == "object":
        a, b = left.get("properties", {}), right.get("properties", {})
        return set(a) == set(b) and all(shapes_compatible(a[k], b[k]) for k in a)
    return False


def _behaves_like(record, sibling):
    """An ordinary, non-error answer indistinguishable in shape from the benign sibling's."""
    return (_state(record) == OBSERVED and _state(sibling) == OBSERVED
            and (record.get("status") or 0) < 400
            and record.get("status") == sibling.get("status")
            and record.get("contentType") == sibling.get("contentType")
            and shapes_compatible(record.get("shape"), sibling.get("shape")))


def compare_neutralized(baseline, current, like_id, like_baseline, like_current):
    """
    A hostile entry whose fix changes the answer without rejecting it: the input is now
    treated as data. Fixed when it behaves like its benign sibling (protocol section 2.1).
    """
    if not like_id:
        return UNVERIFIED, ["expect 'neutralized' needs 'like': the id of a benign sibling entry"]
    if like_baseline is None or like_current is None \
            or _state(like_baseline) != OBSERVED or _state(like_current) != OBSERVED:
        return UNVERIFIED, ["benign sibling '{0}' was not observed in both runs".format(like_id)]
    if _behaves_like(baseline, like_baseline):
        return UNVERIFIED, ["baseline already behaved like '{0}': the entry does not "
                            "demonstrate the finding".format(like_id)]
    if _behaves_like(current, like_current):
        return FIXED, ["now behaves like '{0}' (baseline: {1})".format(like_id,
                                                                      _describe(baseline))]
    if _is_failure(current) and not _is_failure(baseline):
        return REGRESSION, ["hostile input now fails with {0} (baseline: {1})".format(
            _describe(current), _describe(baseline))]
    return NOT_FIXED, ["still does not behave like '{0}': {1} (baseline: {2})".format(
        like_id, _describe(current), _describe(baseline))]


def compare_security(baseline, current):
    """A hostile entry is expected to change: from accepted (or crashing) to rejected."""
    if _rejected(baseline):
        return UNVERIFIED, ["baseline already rejected ({0}): the entry does not demonstrate "
                            "the finding".format(baseline.get("status"))]
    if _rejected(current):
        return FIXED, ["rejected with {0} (baseline: {1})".format(current.get("status"),
                                                                 _describe(baseline))]
    if _is_failure(current) and not _is_failure(baseline):
        return REGRESSION, ["hostile input now fails with {0} (baseline: {1})".format(
            _describe(current), _describe(baseline))]
    return NOT_FIXED, ["still not rejected: {0} (baseline: {1})".format(
        _describe(current), _describe(baseline))]


def compare_one(baseline, current, baseline_results=None, current_results=None):
    """Return (state, details) for one entry."""
    if baseline is None:
        return UNVERIFIED, ["not present in baseline: capture it against the original "
                            "(protocol section 4.3)"]
    if current is None:
        if baseline.get("destructive"):
            return UNVERIFIED, ["not exercised in replay: destructive, capture it alone "
                                "with --only --merge (protocol section 2.2)"]
        return UNVERIFIED, ["not exercised in replay"]
    if _state(baseline) == SKIPPED:
        return UNVERIFIED, ["skipped in baseline: {0}".format(baseline.get("error"))]
    if _state(current) == SKIPPED:
        return UNVERIFIED, ["skipped in replay: {0}".format(current.get("error"))]

    if (baseline.get("kind") or current.get("kind")) == "security":
        if (baseline.get("expect") or current.get("expect")) == "neutralized":
            like_id = baseline.get("like") or current.get("like")
            return compare_neutralized(baseline, current, like_id,
                                       (baseline_results or {}).get(like_id),
                                       (current_results or {}).get(like_id))
        return compare_security(baseline, current)

    if _state(baseline) == ERROR:
        if _is_failure(current):
            return PRE_EXISTING_FAILURE, ["failed before and after: transport error -> {0}"
                                          .format(_describe(current))]
        return PASS, ["improved from transport error"]
    if _state(current) == ERROR:
        if _server_error(baseline):
            return PRE_EXISTING_FAILURE, ["failed before and after: {0} -> transport error"
                                          .format(baseline.get("status"))]
        return REGRESSION, ["call failed after refactoring: transport error"]

    details = []
    if baseline.get("status") != current.get("status"):
        details.append("statusChanged {0} -> {1}".format(baseline.get("status"),
                                                         current.get("status")))
    if baseline.get("contentType") != current.get("contentType"):
        details.append("contentTypeChanged {0} -> {1}".format(baseline.get("contentType"),
                                                              current.get("contentType")))
    details.extend(headers_diff(baseline.get("headers"), current.get("headers")))
    if not shapes_equal(baseline.get("shape"), current.get("shape")):
        for diff in shape_diff(baseline.get("shape"), current.get("shape")):
            if diff["kind"] == "typeChanged":
                details.append("typeChanged {0}: {1} -> {2}".format(diff["path"], diff["from"],
                                                                    diff["to"]))
            elif diff["kind"] == "textChanged":
                details.append("textChanged {0}: -{1} +{2} lines".format(
                    diff["path"], len(diff["removed"]), len(diff["added"])))
                details.extend("  - {0}".format(line) for line in diff["removed"][:3])
                details.extend("  + {0}".format(line) for line in diff["added"][:3])
            else:
                details.append("{0} {1}".format(diff["kind"], diff["path"]))

    if not details:
        # Identical -- but if it was already broken, that is not a success. You neither
        # fixed it nor broke it, and the report must say exactly that.
        if _server_error(baseline):
            return PRE_EXISTING_FAILURE, ["unchanged failure: status {0}".format(
                baseline.get("status"))]
        return PASS, []

    # Already broken before, still broken in the same way -> neither pass nor regression.
    if _server_error(baseline) and baseline.get("status") == current.get("status"):
        return PRE_EXISTING_FAILURE, details

    # Improvement is a behaviour change, so it is named rather than hidden -- but it is
    # not a regression.
    if _server_error(baseline) and not _is_failure(current):
        return PASS, ["improved from {0}".format(baseline.get("status"))] + details

    return REGRESSION, details


def compare(baseline_doc, current_doc):
    baseline_results = baseline_doc.get("results", {})
    current_results = current_doc.get("results", {})
    rows = []
    for entry_id in sorted(set(baseline_results) | set(current_results)):
        state, details = compare_one(baseline_results.get(entry_id),
                                     current_results.get(entry_id),
                                     baseline_results, current_results)
        rows.append({"id": entry_id, "state": state, "details": details})
    return rows


# ---------------------------------------------------------------------------
# I/O and CLI
# ---------------------------------------------------------------------------

def read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, document):
    # newline="\n" so the file is byte-identical to the Node implementation's on every OS.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def print_table(rows):
    width = max([len(row["id"]) for row in rows] + [4])
    for row in rows:
        print("  {0:<{1}}  {2}".format(row["id"], width, row["state"]))
        for detail in row["details"]:
            print("  {0}    - {1}".format(" " * width, detail))


def summarize(rows):
    counts = {state: 0 for state in (PASS, REGRESSION, PRE_EXISTING_FAILURE, UNVERIFIED,
                                     FIXED, NOT_FIXED)}
    for row in rows:
        counts[row["state"]] += 1
    print("")
    print("  {0} PASS, {1} REGRESSION, {2} PRE-EXISTING FAILURE, {3} UNVERIFIED".format(
        counts[PASS], counts[REGRESSION], counts[PRE_EXISTING_FAILURE], counts[UNVERIFIED]))
    if counts[FIXED] or counts[NOT_FIXED]:
        print("  security: {0} FIXED, {1} NOT FIXED".format(counts[FIXED], counts[NOT_FIXED]))
    return counts


def _note_destructive(surface, only):
    if only is not None:
        return
    pending = destructive_ids(surface)
    if pending:
        print("note: {0} destructive entries not exercised: {1} -- capture each alone, on a "
              "fresh boot, with --only <id> --merge (protocol section 2.2)".format(
                  len(pending), ",".join(pending)), file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Baseline-then-replay surface probe (see 06-validation-protocol.md). "
                    "This script never boots the application.")
    sub = parser.add_subparsers(dest="mode")

    capture_parser = sub.add_parser("capture", help="exercise a running app and write a baseline")
    capture_parser.add_argument("--surface", required=True, help="surface inventory JSON")
    capture_parser.add_argument("--base-url", required=True, help="base URL of the running app")
    capture_parser.add_argument("--out", required=True, help="where to write the capture")
    capture_parser.add_argument("--only", help="comma-separated entry ids to exercise")
    capture_parser.add_argument("--merge", action="store_true",
                                help="merge into an existing --out instead of replacing it")
    capture_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    compare_parser = sub.add_parser("compare", help="diff a current capture against a baseline")
    compare_parser.add_argument("--surface", help="surface inventory JSON (needed with --base-url)")
    compare_parser.add_argument("--baseline", required=True, help="baseline capture JSON")
    compare_parser.add_argument("--base-url", help="capture live from this URL")
    compare_parser.add_argument("--current", help="use this already-captured file instead")
    compare_parser.add_argument("--out", help="optionally write the current capture here")
    compare_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)

    # Text skeletons carry response content; never let a console codepage crash the report.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parser.parse_args(argv)
    if not args.mode:
        parser.print_help()
        return 2

    try:
        if args.mode == "capture":
            only = set(args.only.split(",")) if args.only else None
            surface = read_json(args.surface)
            document = capture(surface, args.base_url, args.timeout, only)
            # Counted before merging: the numbers describe THIS run, not the whole file.
            states = [r["state"] for r in document["results"].values()]
            if args.merge:
                previous = read_json(args.out)
                previous.setdefault("results", {}).update(document["results"])
                previous["version"] = PROTOCOL_VERSION
                document = previous
            write_json(args.out, document)
            print("captured {0} entries now ({1} observed, {2} error, {3} skipped); "
                  "{4} in file -> {5}".format(len(states), states.count(OBSERVED),
                                              states.count(ERROR), states.count(SKIPPED),
                                              len(document["results"]), args.out))
            if states.count(ERROR) > 1:
                print("warning: several transport errors in this run -- if one entry crashed "
                      "the application, the entries after it failed only because it was down "
                      "(protocol section 3.1)", file=sys.stderr)
            _note_destructive(surface, only)
            return 0

        baseline_doc = read_json(args.baseline)
        if args.current:
            current_doc = read_json(args.current)
        elif args.base_url and args.surface:
            surface = read_json(args.surface)
            current_doc = capture(surface, args.base_url, args.timeout)
            if args.out:
                write_json(args.out, current_doc)
            _note_destructive(surface, None)
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
