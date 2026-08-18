#!/usr/bin/env python3
"""Checks the deterministic encoder against bytes it did not produce.

    python3 runners/run_deterministic_encoding_vectors.py    # no arguments

Every other class in this tree computes its expected bytes with `cbor()`
imported from the implementation under test. An encoder defect is therefore
shared by the subject and the checker, and nothing fires -- including an
RFC 8949 Section 4.2.1 map-ordering violation, which is the defect most likely
to be shipped by accident because both orderings are well-formed CBOR.

This runner derives nothing. Every expected value is read from
vectors/arp-deterministic-encoding-v0.1.json, where it was fixed once by the
builder and committed. The runner has no third-party dependency, so the tree
still runs unpacked with no arguments -- standing rule 10.

Two-sided by construction. A suite that only checks a correct encoder cannot
be distinguished from one that checks nothing, so three defective encoders are
implemented below and each must be refused by the row it targets. Standing
rule 3, and standing rule 9: each defective encoder declares the row it is
designed to trip and is credited only when that row is what caught it.
"""

import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "reference", "arp_read_ref.py")
VECTORS = os.path.join(ROOT, "vectors", "arp-deterministic-encoding-v0.1.json")

_spec = importlib.util.spec_from_file_location("arp_read_ref", REF)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)


# --------------------------------------------------------- defective encoders
# Each reintroduces exactly one violation of Section 4.2.1 and nothing else.

def enc_length_first(v):
    """Section 4.2.3 ordering where Section 4.2.1 is required."""
    if isinstance(v, dict):
        items = sorted(((enc_length_first(k), enc_length_first(val))
                        for k, val in v.items()),
                       key=lambda kv: (len(kv[0]), kv[0]))
        return ref._head(5, len(items)) + b"".join(k + x for k, x in items)
    if isinstance(v, (list, tuple)):
        return ref._head(4, len(v)) + b"".join(enc_length_first(x) for x in v)
    return ref.cbor(v)


def enc_non_shortest(v):
    """Arguments in a wider field than needed."""
    if isinstance(v, int) and 0 <= v < 24:
        return bytes([0 << 5 | 24]) + v.to_bytes(1, "big")
    if isinstance(v, (list, tuple)):
        return ref._head(4, len(v)) + b"".join(enc_non_shortest(x) for x in v)
    if isinstance(v, dict):
        items = sorted(((enc_non_shortest(k), enc_non_shortest(val))
                        for k, val in v.items()), key=lambda kv: kv[0])
        return ref._head(5, len(items)) + b"".join(k + x for k, x in items)
    return ref.cbor(v)


def enc_indefinite(v):
    """Indefinite-length containers, which Section 4.2.1 forbids."""
    if isinstance(v, (list, tuple)):
        return b"\x9f" + b"".join(enc_indefinite(x) for x in v) + b"\xff"
    if isinstance(v, dict):
        items = sorted(((enc_indefinite(k), enc_indefinite(val))
                        for k, val in v.items()), key=lambda kv: kv[0])
        return b"\xbf" + b"".join(k + x for k, x in items) + b"\xff"
    return ref.cbor(v)


DEFECTIVE = {
    "length-first-ordering": enc_length_first,
    "non-shortest-argument": enc_non_shortest,
    "indefinite-length": enc_indefinite,
}


def evaluate(doc, encoder):
    """Return (rows, mismatched_ids) for one encoder over every vector."""
    rows, bad = [], []
    for v in doc["vectors"]:
        value = eval(v["input_repr"], {"__builtins__": {}}, {})
        got = encoder(value)
        ok = (got.hex() == v["expected_hex"]
              and hashlib.sha256(got).hexdigest() == v["expected_sha256"])
        rows.append({"id": v["id"], "match": ok, "got_hex": got.hex()})
        if not ok:
            bad.append(v["id"])
    return rows, bad


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.exists(VECTORS):
        sys.stderr.write("vector file missing: %s\n" % VECTORS)
        return 1
    with open(VECTORS, "r") as fh:
        doc = json.load(fh)

    w = sys.stdout.write
    w("ARP deterministic-encoding class %s\n" % doc["version"])
    w("vectors   %s\n" % sha256_file(VECTORS))
    w("reference %s\n\n" % sha256_file(REF))

    failed = False

    # --- positive side: the harness against bytes it did not produce --------
    rows, bad = evaluate(doc, ref.cbor)
    for r in rows:
        w("  %s %-8s expected bytes fixed in the vector file\n"
          % ("ok  " if r["match"] else "FAIL", r["id"]))
        if not r["match"]:
            exp = next(v["expected_hex"] for v in doc["vectors"]
                       if v["id"] == r["id"])
            w("        expected %s\n        got      %s\n" % (exp, r["got_hex"]))
    if bad:
        failed = True

    # --- negative side: each defective encoder must be caught, by its row ---
    w("\n")
    exercised, unexercised = [], []
    for spec in doc["defective_encoders"]:
        enc = DEFECTIVE[spec["defect"]]
        _, dbad = evaluate(doc, enc)
        designed = spec["discriminator"].split()[0]
        fired = designed in dbad
        refused = bool(dbad)
        if not refused:
            failed = True
        (exercised if (refused and fired) else unexercised).append(spec["id"])
        w("  %s %-14s %-24s caught by %s\n"
          % ("ok  " if (refused and fired) else
             ("FAIL" if not refused else "gap "),
             spec["id"], spec["defect"], ", ".join(dbad) or "NOTHING"))
        if refused and not fired:
            w("        ! designed discriminator %s did not fire\n" % designed)

    md = doc["measured_divergence"]
    w("\nmeasured divergence, recorded not adjudicated:\n")
    w("  Section 4.2.1   %s\n" % md["rfc8949_s421_hex"])
    w("  Section 4.2.3   %s\n" % md["rfc8949_s423_length_first_hex"])
    w("  cbor2 canonical %s  (== 4.2.3: %s)\n"
      % (md["cbor2_canonical_hex"], md["cbor2_canonical_matches_s423"]))

    aggregate = "FAIL" if failed else (
        "PASS_WITH_DECLARED_GAPS" if unexercised else "PASS")
    w("\ncontrols exercised     %d of %d\n"
      % (len(exercised), len(exercised) + len(unexercised)))
    w("DETERMINISTIC RESULT: %s\n" % aggregate)

    out = {
        "class": doc["class"],
        "version": doc["version"],
        "vectors_sha256": sha256_file(VECTORS),
        "reference_sha256": sha256_file(REF),
        "runner_sha256": sha256_file(os.path.abspath(__file__)),
        "positive_rows": rows,
        "controls_exercised": exercised,
        "controls_not_exercised": unexercised,
        "measured_divergence": md,
        "establishes": "that the deterministic encoder of the reference "
                       "implementation reproduces byte strings fixed outside "
                       "it, including the map key order of RFC 8949 Section "
                       "4.2.1, and that a suite checking it refuses three "
                       "named encoder defects.",
        "does_not_establish": "that any OTHER class in this tree computes its "
                              "expected bytes independently. Those classes "
                              "still import the encoder under test. What this "
                              "class establishes is that the imported encoder "
                              "is itself pinned to fixed bytes, so a silent "
                              "encoder defect would be caught here even though "
                              "it remains invisible there.",
        "deterministic_result": aggregate,
    }
    path = os.path.join(ROOT, "runs", "deterministic_encoding_run.json")
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    w("written %s\n" % path)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
