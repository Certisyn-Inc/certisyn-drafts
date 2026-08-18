#!/usr/bin/env python3
"""Regenerates vectors/arp-deterministic-encoding-v0.1.json.

Why this class exists. Every other class in this tree computes its expected
bytes with `cbor()` imported from the implementation under test, so an encoder
defect is shared by the subject and the checker and nothing fires. That is the
encoder-independence gap the existence-oracle run record has carried since it
was first published. This class closes it the only way a suite can: the
expected bytes are FIXED IN THE VECTOR FILE and the runner derives nothing.

Provenance, stated per vector and not rounded up. Two different things are
being corroborated and they have different evidence:

  * ITEM ENCODINGS -- head bytes, integer arguments, string lengths, array and
    map framing -- are corroborated against cbor2, an implementation neither
    written for this tree nor derived from it. Where cbor2 and the harness
    agree on the bytes of an item, that is two implementations agreeing.

  * MAP KEY ORDER is NOT corroborated by cbor2, and saying so is the point of
    this file. cbor2's canonical mode applies the length-first ordering of
    RFC 8949 Section 4.2.3, not the bytewise-on-encoded-form ordering of
    Section 4.2.1 that ARP cites. Measured, cbor2 6.1.4:

        {10:1, 100:2, -1:3, "z":4, "aa":5}
        Section 4.2.1  a50a011864022003617a0462616105   <- what ARP requires
        cbor2 canonical a50a012003186402617a0462616105   <- Section 4.2.3

    So for the ordering rule the evidence is the RFC text and the harness, and
    a second implementation that DISAGREES. That disagreement is recorded as a
    finding rather than resolved by picking the majority, because a majority of
    two is not evidence and the RFC decides it.

This builder needs cbor2. The RUNNER does not, and must not: standing rule 10,
a package is an artefact only if it runs unpacked with no arguments.

    python3 runners/build_deterministic_encoding_vectors.py
"""

import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "reference", "arp_read_ref.py")

try:
    import cbor2
    import importlib.metadata as _md
    CBOR2_VERSION = _md.version("cbor2")
except Exception:
    sys.stderr.write(
        "This builder corroborates item encodings against cbor2 and cannot\n"
        "run without it:  pip install cbor2\n"
        "The runner has no dependency on it. Only the builder does.\n")
    raise SystemExit(2)

_spec = importlib.util.spec_from_file_location("arp_read_ref", REF)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)


def corroborate(value):
    """Encode with the harness and with cbor2, and say what agreed.

    cbor2 is called WITHOUT canonical=True. Its canonical mode implements a
    different ordering rule, and calling it here would compare the harness
    against a known-divergent implementation and report the divergence as a
    harness defect. Non-canonical cbor2 preserves insertion order, so for a
    map its agreement is about item encodings only -- which is exactly the
    part being corroborated, and the part this function is allowed to claim.
    """
    ours = ref.cbor(value)
    if isinstance(value, dict):
        ordered = {k: value[k] for k in sorted(value, key=lambda k: ref.cbor(k))}
        theirs = cbor2.dumps(ordered)
        note = ("item encodings corroborated by cbor2 %s; the key ORDER is "
                "this document's, from RFC 8949 Section 4.2.1, and cbor2's "
                "canonical mode disagrees with it" % CBOR2_VERSION)
    else:
        theirs = cbor2.dumps(value)
        note = "corroborated by cbor2 %s" % CBOR2_VERSION
    if ours != theirs:
        raise SystemExit("harness and cbor2 disagree on %r: %s vs %s"
                         % (value, ours.hex(), theirs.hex()))
    return ours, note


# The ordering-divergent map. Chosen so the encoded key forms have three
# different lengths, which is the only condition under which Section 4.2.1 and
# Section 4.2.3 can produce different byte strings.
DIVERGENT = {10: 1, 100: 2, -1: 3, "z": 4, "aa": 5}

CASES = [
    ("DE-01", "integers across every argument-width boundary",
     [0, 1, 10, 23, 24, 25, 100, 1000, -1, -10, -100]),
    ("DE-02", "shortest-form arguments: 24 is one extra byte, not two",
     [23, 24, 255, 256, 65535, 65536]),
    ("DE-03", "byte and text strings, empty and multi-octet UTF-8",
     [b"", b"\x01\x02\x03\x04", "", "a", "IETF", "ü", "水"]),
    ("DE-04", "nested definite-length arrays",
     [[], [1, 2, 3], [1, [2, 3], [4, 5]]]),
    ("DE-05", "map whose keys encode to equal lengths, so the two orderings "
              "cannot diverge and this row isolates the item encodings",
     {"a": 1, "b": 2, "c": 3}),
    ("DE-06", "map whose keys encode to DIFFERENT lengths. This is the row "
              "that separates RFC 8949 Section 4.2.1 from Section 4.2.3, and "
              "the row a length-first encoder fails",
     DIVERGENT),
]


def build():
    vectors = []
    for vid, purpose, value in CASES:
        enc, note = corroborate(value)
        vectors.append({
            "id": vid,
            "purpose": purpose,
            "input_repr": repr(value),
            "expected_hex": enc.hex(),
            "expected_sha256": hashlib.sha256(enc).hexdigest(),
            "provenance": note,
        })

    # ARP-specific known-answer rows. The preimage is spec-supplied here --
    # written into this file -- rather than produced by calling the harness at
    # run time, which is the whole point of the class.
    rb_args = ["GET", "https://arp.example/arp/outputs/R_present",
               "n-0000000000000001", "p-other"]
    rb_pre = ref.cbor(rb_args)
    _, rb_note = corroborate(rb_args)
    vectors.append({
        "id": "DE-07",
        "purpose": "Section 6.4.1 request-binding: the deterministic CBOR "
                   "array of the four covered values, and the SHA-256 over it",
        "input_repr": repr(rb_args),
        "expected_hex": rb_pre.hex(),
        "expected_sha256": hashlib.sha256(rb_pre).hexdigest(),
        "provenance": rb_note,
        "note": "the target is already in its RFC 3986 Sections 6.2.2 and "
                "6.2.3 normalised form; normalisation is tested by DE-08, not "
                "here, so a normalisation defect cannot hide in this row",
    })

    sig_args = ["Signature1", ref.cbor({1: -8}), b"", b"payload-under-test"]
    sig_pre = ref.cbor(sig_args)
    _, sig_note = corroborate(sig_args)
    vectors.append({
        "id": "DE-08",
        "purpose": "RFC 9052 Section 4.4 Sig_structure preimage as this "
                   "document builds it, with the EdDSA protected header",
        "input_repr": repr(sig_args),
        "expected_hex": sig_pre.hex(),
        "expected_sha256": hashlib.sha256(sig_pre).hexdigest(),
        "provenance": sig_note,
    })

    divergent_lengthfirst = _length_first(DIVERGENT)
    out = {
        "class": "arp-deterministic-encoding",
        "version": "v0.1",
        "spec": "RFC 8949 Section 4.2.1, as cited by draft-hillier-scitt-arp "
                "for every digest preimage and every signed payload",
        "property": "The deterministic encoder is conformant to bytes fixed "
                    "outside it. No expected value in this file is derived at "
                    "run time by the implementation under test.",
        "closes": "the encoder-independence gap declared by the "
                  "arp-existence-oracle class",
        "builder": "runners/build_deterministic_encoding_vectors.py",
        "built_against": {
            "reference_sha256": _sha256_file(REF),
            "corroborating_implementation": "cbor2 %s" % CBOR2_VERSION,
        },
        "corroboration_boundary":
            "cbor2 corroborates item encodings only. It does NOT corroborate "
            "map key order: its canonical mode implements the length-first "
            "ordering of RFC 8949 Section 4.2.3 and not the bytewise ordering "
            "of Section 4.2.1 that this document requires. Two numbers "
            "produced by one construction are one measurement, and two "
            "implementations that disagree are not a vote -- the RFC decides "
            "it. Standing rule 8.",
        "measured_divergence": {
            "input_repr": repr(DIVERGENT),
            "rfc8949_s421_hex": ref.cbor(DIVERGENT).hex(),
            "rfc8949_s423_length_first_hex": divergent_lengthfirst.hex(),
            "cbor2_canonical_hex": cbor2.dumps(DIVERGENT, canonical=True).hex(),
            "cbor2_canonical_matches_s423": (
                cbor2.dumps(DIVERGENT, canonical=True) == divergent_lengthfirst),
            "finding": "cbor2 %s in canonical mode emits the Section 4.2.3 "
                       "ordering. An implementation that computes ARP digests "
                       "with it ships non-conforming bytes and raises no "
                       "error, because both orderings are well-formed CBOR "
                       "and only one is the one this document cites."
                       % CBOR2_VERSION,
        },
        "defective_encoders": [
            {"id": "NV-ARP-DE-01", "defect": "length-first-ordering",
             "channel": "map keys sorted by encoded length then bytewise, "
                        "RFC 8949 Section 4.2.3 instead of Section 4.2.1",
             "discriminator": "DE-06 expected_hex mismatch"},
            {"id": "NV-ARP-DE-02", "defect": "non-shortest-argument",
             "channel": "arguments encoded in a wider field than needed",
             "discriminator": "DE-01 expected_hex mismatch"},
            {"id": "NV-ARP-DE-03", "defect": "indefinite-length",
             "channel": "indefinite-length containers, which Section 4.2.1 "
                        "forbids",
             "discriminator": "DE-04 expected_hex mismatch"},
        ],
        "vectors": vectors,
    }
    return out


def _length_first(d):
    items = sorted(((ref.cbor(k), ref.cbor(v)) for k, v in d.items()),
                   key=lambda kv: (len(kv[0]), kv[0]))
    return ref._head(5, len(items)) + b"".join(k + v for k, v in items)


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    doc = build()
    path = os.path.join(ROOT, "vectors",
                        "arp-deterministic-encoding-v0.1.json")
    with open(path, "w", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    sys.stdout.write("written %s\n" % path)
    sys.stdout.write("  %d vectors, %d defective encoders\n"
                     % (len(doc["vectors"]), len(doc["defective_encoders"])))
    md = doc["measured_divergence"]
    sys.stdout.write("  divergence measured: cbor2 canonical == S4.2.3 -> %s\n"
                     % md["cbor2_canonical_matches_s423"])
