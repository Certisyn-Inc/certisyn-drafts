#!/usr/bin/env python3
"""Checks the deterministic encoder against bytes it did not compute.

    python3 runners/run_deterministic_encoding_vectors.py    # no arguments

Every other class in this tree computes its expected bytes with the encoder
imported from the implementation under test, so an encoder defect is shared by
the subject and the checker and nothing fires -- including an RFC 8949 Section
4.2.1 map-ordering violation, which is the defect most likely to ship by
accident because both orderings are well-formed CBOR and neither raises.

This runner derives nothing. Every expected value is read from the vector file,
where the builder computed it with cbor2 and its own argument-width and
ordering logic, and asserted the subject against it.

Dependencies: none outside the standard library. It imports the encoder alone,
from reference/arp_cbor.py, and not the HTTP reference endpoint -- v0.1 of this
runner claimed no third-party dependency while importing a module whose first
act is `from cryptography.hazmat...`, and blocking that package produced a bare
traceback rather than the instruction standing rule 4 requires.

Two-sided, and the negative side is held to a stricter test than v0.1 used:

  * Each mutant encoder is written out in full here. It does not delegate any
    part of its work to the subject, so it cannot be merely "defective
    relative to the subject" -- under v0.1 a subject that was itself
    length-first produced a mutant byte-identical to it, and the control was
    still credited.
  * A mutant that agrees with the subject on every row is a FAILURE of the
    control, not a pass. A control that cannot distinguish itself from the
    thing it is testing is testing nothing.
  * Credit requires the caught-row set to EQUAL the designed set declared in
    the vector file. Membership is not enough: a control credited because some
    unrelated row happened to notice it is a suite claiming coverage it does
    not have. Standing rules 9 and 11.
"""

import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
import de_codec as C                                          # noqa: E402

ENCODER = os.path.join(ROOT, "reference", "arp_cbor.py")
NORMALISER = os.path.join(ROOT, "reference", "arp_uri.py")
VECTORS = os.path.join(ROOT, "vectors",
                       "arp-deterministic-encoding-v0.2.json")
RUN = os.path.join(ROOT, "runs", "deterministic_encoding_run.json")

_spec = importlib.util.spec_from_file_location("arp_cbor", ENCODER)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)

_uspec = importlib.util.spec_from_file_location("arp_uri", NORMALISER)
uri = importlib.util.module_from_spec(_uspec)
_uspec.loader.exec_module(uri)


def pre3986_normalise(target):
    """The normaliser this tree carried until 2026-08-18, written out in full.

    Scheme and host lowercased, default port dropped, and nothing else: no
    dot-segment removal, no percent-encoding normalisation, userinfo silently
    discarded. It is a mutant like the encoder mutants, not a call into the
    subject, so it cannot be merely defective relative to whatever the subject
    currently does.
    """
    from urllib.parse import urlsplit
    u = urlsplit(target)
    scheme = u.scheme.lower()
    host = u.hostname.lower() if u.hostname else ""
    port = u.port
    if port is not None and not ((scheme == "http" and port == 80) or
                                 (scheme == "https" and port == 443)):
        host = "%s:%d" % (host, port)
    path = u.path or "/"
    return "%s://%s%s%s" % (scheme, host, path,
                            ("?" + u.query) if u.query else "")


NORM_MUTANTS = {"pre-3986-normaliser": pre3986_normalise}


# --------------------------------------------------------- mutant encoders
# Each is a complete encoder. None calls the subject.

def _head_ok(major, arg):
    if arg < 24:
        return bytes([major << 5 | arg])
    for n, tag in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if arg < (1 << (8 * n)):
            return bytes([major << 5 | tag]) + arg.to_bytes(n, "big")
    raise ValueError("argument too large")


def _make(head, order, indefinite=False):
    def enc(v):
        if v is None:
            return b"\xf6"
        if v is True:
            return b"\xf5"
        if v is False:
            return b"\xf4"
        if isinstance(v, int):
            return head(0, v) if v >= 0 else head(1, -v - 1)
        if isinstance(v, bytes):
            return head(2, len(v)) + v
        if isinstance(v, str):
            b = v.encode("utf-8")
            return head(3, len(b)) + b
        if isinstance(v, (list, tuple)):
            body = b"".join(enc(x) for x in v)
            return (b"\x9f" + body + b"\xff") if indefinite else \
                head(4, len(v)) + body
        if isinstance(v, dict):
            items = sorted(((enc(k), enc(val)) for k, val in v.items()),
                           key=order)
            body = b"".join(k + val for k, val in items)
            return (b"\xbf" + body + b"\xff") if indefinite else \
                head(5, len(items)) + body
        raise TypeError("no deterministic encoding for %r" % type(v))
    return enc


def _head_nonshortest(major, arg):
    """Every argument one field wider than needed."""
    for n, tag in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if arg < (1 << (8 * n)):
            nxt = {24: (2, 25), 25: (4, 26), 26: (8, 27), 27: (8, 27)}[tag]
            return bytes([major << 5 | nxt[1]]) + arg.to_bytes(nxt[0], "big")
    raise ValueError("argument too large")


def _head_widestring(major, arg):
    """Length arguments of bstr/tstr/array/map widened once they reach 24.

    This is the defect that passed v0.1 of this class completely, because no
    v0.1 row contained a byte string of 24 octets or more, or a container of
    24 members or more. Every digest this document commits to is a 32-octet
    byte string.
    """
    if major in (2, 3, 4, 5) and 24 <= arg < 256:
        return bytes([major << 5 | 25]) + arg.to_bytes(2, "big")
    return _head_ok(major, arg)


BYTEWISE = lambda kv: kv[0]                                   # noqa: E731
LENGTHFIRST = lambda kv: (len(kv[0]), kv[0])                  # noqa: E731

MUTANTS = {
    "length-first-ordering": _make(_head_ok, LENGTHFIRST),
    "non-shortest-argument": _make(_head_nonshortest, BYTEWISE),
    "indefinite-length": _make(_head_ok, BYTEWISE, indefinite=True),
    "wide-string-length": _make(_head_widestring, BYTEWISE),
}


def evaluate(doc, encoder):
    """(caught_row_ids, unreachable) for one encoder over every row.

    A row the encoder cannot reach is recorded as unreachable with its reason
    and is NOT counted as caught. Silence is not a pass -- standing rule 4.
    """
    caught, unreachable = [], []
    for v in doc["vectors"]:
        try:
            value = C.parse(v["input"])
            got = encoder(value)
        except Exception as exc:
            unreachable.append({"id": v["id"],
                                "reason": "%s: %s" % (type(exc).__name__, exc)})
            continue
        if got.hex() != v["expected_hex"]:
            caught.append(v["id"])
    return caught, unreachable


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # A stale record left on disk after a crash reads as a result, so it is
    # invalidated before the first row runs. Removal is preferred; where the
    # filesystem forbids unlink -- a read-only mount, a bind mount, a
    # permissions model that allows write but not delete -- the record is
    # overwritten with a marker instead. Neither is allowed to abort the run
    # with a traceback: standing rule 4 asks for an instruction, and a runner
    # that dies before its first row on a filesystem quirk is the failure that
    # rule is about.
    if os.path.exists(RUN):
        try:
            os.remove(RUN)
        except OSError as exc:
            try:
                with open(RUN, "w", newline="\n") as fh:
                    json.dump({"deterministic_result": "INVALIDATED",
                               "reason": "a run was started and has not yet "
                                         "written its result; this file is "
                                         "not a result",
                               "unlink_error": str(exc)}, fh, indent=2,
                              sort_keys=True)
                    fh.write("\n")
            except OSError as exc2:
                sys.stderr.write(
                    "WARNING: the previous run record could not be removed or "
                    "overwritten:\n    %s\n    %s\n"
                    "  If this run does not complete, that file is STALE and "
                    "is not a result\n  for this tree. Check its "
                    "vectors_sha256 against the vector file before\n"
                    "  reading it.\n" % (exc, exc2))

    if not os.path.exists(VECTORS):
        sys.stderr.write(
            "The vector file is not where this runner expects it:\n\n    %s\n\n"
            "It is generated by runners/build_deterministic_encoding_vectors.py"
            ", which\nneeds cbor2. The runner does not.\n" % VECTORS)
        return 1
    with open(VECTORS, "r") as fh:
        doc = json.load(fh)

    w = sys.stdout.write
    w("ARP deterministic-encoding class %s\n" % doc["version"])
    w("vectors %s\nencoder %s\n\n" % (sha256_file(VECTORS),
                                      sha256_file(ENCODER)))

    failed = False

    # --- positive side ------------------------------------------------------
    caught, unreachable = evaluate(doc, ref.cbor)
    rows = []
    for v in doc["vectors"]:
        un = next((u for u in unreachable if u["id"] == v["id"]), None)
        if un:
            state, note = "UNREACHABLE", un["reason"]
            failed = True
        elif v["id"] in caught:
            state, note = "FAIL", "does not reproduce the expected bytes"
            failed = True
        else:
            state, note = "ok", ""
        rows.append({"id": v["id"], "state": state, "note": note})
        w("  %-11s %-6s %s\n" % (state, v["id"], note))

    # --- negative side ------------------------------------------------------
    w("\n")
    exercised, not_exercised, control_rows = [], [], []
    for spec in doc["defective_encoders"]:
        enc = MUTANTS.get(spec["defect"])
        if enc is None:
            not_exercised.append(spec["id"])
            control_rows.append({"id": spec["id"], "state": "NOT-IMPLEMENTED",
                                 "caught": [], "designed": spec["designed_rows"]})
            w("  %-11s %-14s %s\n" % ("gap", spec["id"],
                                      "declared in the vector file and not "
                                      "implemented in this runner"))
            continue
        mcaught, munreach = evaluate(doc, enc)
        # A mutant that agrees with the subject everywhere is not a control.
        distinct = any(enc(C.parse(v["input"])) != ref.cbor(C.parse(v["input"]))
                       for v in doc["vectors"]
                       if v["id"] not in [u["id"] for u in munreach])
        designed = spec["designed_rows"]
        exact = sorted(mcaught) == sorted(designed)
        if not distinct:
            state = "FAIL"
            failed = True
            note = ("the mutant is byte-identical to the subject on every "
                    "row, so this control cannot distinguish itself from the "
                    "thing it tests")
        elif exact:
            state, note = "ok", "caught by exactly its designed rows"
            exercised.append(spec["id"])
        else:
            state = "gap"
            not_exercised.append(spec["id"])
            extra = sorted(set(mcaught) - set(designed))
            missing = sorted(set(designed) - set(mcaught))
            note = ("caught set differs from designed: extra %s, missing %s"
                    % (extra or "none", missing or "none"))
        control_rows.append({"id": spec["id"], "state": state,
                             "caught": sorted(mcaught), "designed": designed,
                             "unreachable": munreach, "note": note})
        w("  %-11s %-14s %-22s %s\n"
          % (state, spec["id"], spec["defect"], note))

    # --- normalisation, positive then negative ------------------------------
    norm_rows, norm_controls = [], []
    norm_exercised, norm_not_exercised = [], []
    nrows = doc.get("normalisation", [])
    if nrows:
        w("\n")
        for nv in nrows:
            try:
                got = uri.normalise_target(nv["raw"])
                rb = hashlib.sha256(ref.cbor(
                    ["GET", got, "n-0000000000000001", "p-other"])).hexdigest()
                ok = (got == nv["expected_normalised"]
                      and rb == nv["expected_request_binding_hex"])
                state = "ok" if ok else "FAIL"
                note = "" if ok else ("got %s" % got)
            except Exception as exc:
                state = "UNREACHABLE"
                note = "%s: %s" % (type(exc).__name__, exc)
            if state != "ok":
                failed = True
            norm_rows.append({"id": nv["id"], "state": state, "note": note})
            w("  %-11s %-8s %s\n" % (state, nv["id"], note))

        for spec in doc.get("normalisation_controls", []):
            mut = NORM_MUTANTS.get(spec["defect"])
            if mut is None:
                norm_not_exercised.append(spec["id"])
                norm_controls.append({"id": spec["id"],
                                      "state": "NOT-IMPLEMENTED"})
                w("  %-11s %-14s declared and not implemented here\n"
                  % ("gap", spec["id"]))
                continue
            caught = [nv["id"] for nv in nrows
                      if mut(nv["raw"]) != nv["expected_normalised"]]
            distinct = any(mut(nv["raw"]) != uri.normalise_target(nv["raw"])
                           for nv in nrows)
            exact = sorted(caught) == sorted(spec["designed_rows"])
            if not distinct:
                state, failed = "FAIL", True
                note = ("the mutant agrees with the subject on every row, so "
                        "this control cannot distinguish itself from the "
                        "thing it tests")
            elif exact:
                state, note = "ok", "caught by exactly its designed rows"
                norm_exercised.append(spec["id"])
            else:
                state = "gap"
                norm_not_exercised.append(spec["id"])
                note = ("caught set differs: extra %s, missing %s"
                        % (sorted(set(caught) - set(spec["designed_rows"]))
                           or "none",
                           sorted(set(spec["designed_rows"]) - set(caught))
                           or "none"))
            norm_controls.append({"id": spec["id"], "state": state,
                                  "caught": sorted(caught),
                                  "designed": spec["designed_rows"],
                                  "note": note})
            w("  %-11s %-14s %-22s %s\n"
              % (state, spec["id"], spec["defect"], note))

    md = doc["measured_divergence"]
    w("\nrecorded divergence (measured by the builder, not here):\n")
    w("  Section 4.2.1   %s\n" % md["rfc8949_s421_hex"])
    w("  Section 4.2.3   %s\n" % md["rfc8949_s423_length_first_hex"])
    w("  cbor2 canonical %s\n" % md["cbor2_canonical_hex"])

    gaps = doc.get("does_not_establish", [])
    not_exercised = not_exercised + norm_not_exercised
    exercised = exercised + norm_exercised
    if failed:
        aggregate = "FAIL"
    elif not_exercised or gaps:
        aggregate = "PASS_WITH_DECLARED_GAPS"
    else:
        aggregate = "PASS"

    w("\nencoding rows        %d, %d reproduced the expected bytes\n"
      % (len(rows), sum(1 for r in rows if r["state"] == "ok")))
    w("normalisation rows   %d, %d reproduced the expected form and digest\n"
      % (len(norm_rows), sum(1 for r in norm_rows if r["state"] == "ok")))
    w("controls exercised   %d of %d\n"
      % (len(exercised), len(exercised) + len(not_exercised)))
    w("declared non-coverage %d\n" % len(gaps))
    w("\nDETERMINISTIC RESULT: %s\n" % aggregate)
    if aggregate == "PASS_WITH_DECLARED_GAPS":
        w("  No row failed. The result is not PASS because this class names\n"
          "  %d things it does not establish, and they are stated in the\n"
          "  vector file rather than left to a reader to infer.\n" % len(gaps))

    out = {
        "class": doc["class"],
        "version": doc["version"],
        "vectors_sha256": sha256_file(VECTORS),
        "encoder_sha256": sha256_file(ENCODER),
        "runner_sha256": sha256_file(os.path.abspath(__file__)),
        "codec_sha256": sha256_file(os.path.join(ROOT, "runners",
                                                 "de_codec.py")),
        "rows": rows,
        "normalisation_rows": norm_rows,
        "normalisation_controls": norm_controls,
        "normaliser_sha256": sha256_file(NORMALISER),
        "controls": control_rows + norm_controls,
        "controls_exercised": exercised,
        "controls_not_exercised": not_exercised,
        "recorded_divergence": md,
        "establishes": "that the deterministic encoder reproduces byte strings "
                       "computed without it, across every argument width of "
                       "every major type it emits, including nested map key "
                       "ordering, and that four named encoder defects are each "
                       "caught by exactly the rows designed to catch them.",
        "does_not_establish": gaps + [
            "that any OTHER class in this tree computes its expected bytes "
            "independently. Those classes still import the encoder under test. "
            "What this class establishes is that the imported encoder is "
            "pinned to bytes it did not compute, so a silent encoder defect "
            "would be caught here even though it remains invisible there."],
        "deterministic_result": aggregate,
    }
    with open(RUN, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    w("written %s\n" % RUN)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
