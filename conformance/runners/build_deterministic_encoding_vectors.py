#!/usr/bin/env python3
"""Regenerates vectors/arp-deterministic-encoding-v0.2.json.

    python3 runners/build_deterministic_encoding_vectors.py

WHAT CHANGED FROM v0.1, AND WHY. v0.1 claimed its expected bytes were "fixed
outside the implementation under test". They were not: the builder called
`ref.cbor(value)` and wrote the result into the file, filtered through one
equality check against cbor2. Regenerating v0.1 against a deliberately broken
encoder produced a byte-identical vector file, so "regenerate and diff rather
than trusting it" detected nothing. Three separate encoder defects passed the
whole v0.1 suite with PASS. Found in red team on 2026-08-18, before the class
was relied on.

v0.2 computes every expected byte string WITHOUT the implementation under test:

  * Scalars, strings and arrays are encoded by cbor2, which shares no code
    with this tree.
  * Maps are assembled HERE: each key and each value is encoded by cbor2
    independently, the encoded KEY byte strings are sorted by this file's own
    bytewise comparison, and the head is emitted by this file's own `_head`.
    The implementation under test contributes nothing to the expectation --
    in particular it does not contribute the ordering, which is the rule it
    is most likely to get wrong.
  * `ref` is then loaded and ASSERTED to reproduce every expected value. A
    mismatch is a build failure naming the row, not a rewritten expectation.

cbor2's canonical mode is never called. It implements the length-first
ordering of RFC 8949 Section 4.2.3, not the bytewise ordering of Section
4.2.1 that ARP cites, and calling it here would compare the subject against a
known-divergent implementation. The divergence is measured and recorded
instead.

The builder needs cbor2. The runner must not, and does not.
"""

import hashlib
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "runners"))
sys.path.insert(0, os.path.join(ROOT, "reference"))
import de_codec as C                                          # noqa: E402

REF = os.path.join(ROOT, "reference", "arp_cbor.py")
URI = os.path.join(ROOT, "reference", "arp_uri.py")
OUT = os.path.join(ROOT, "vectors", "arp-deterministic-encoding-v0.2.json")

try:
    import cbor2
    import importlib.metadata as _md
    CBOR2_VERSION = _md.version("cbor2")
except Exception:
    sys.stderr.write(
        "This builder computes its expected bytes with cbor2 and cannot run\n"
        "without it:  pip install cbor2\n"
        "The runner has no dependency on cbor2 and must not acquire one.\n")
    raise SystemExit(2)

_spec = importlib.util.spec_from_file_location("arp_cbor", REF)
ref = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ref)

_uspec = importlib.util.spec_from_file_location("arp_uri", URI)
uri = importlib.util.module_from_spec(_uspec)
_uspec.loader.exec_module(uri)


# --------------------------------------------------------- builder-local head
# Written here rather than imported, so the expectation does not borrow the
# subject's argument-width logic -- the logic a whole class of defects lives in.

def head(major, arg):
    if arg < 24:
        return bytes([major << 5 | arg])
    for n, tag in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if arg < (1 << (8 * n)):
            return bytes([major << 5 | tag]) + arg.to_bytes(n, "big")
    raise ValueError("argument too large")


def expect(value):
    """Expected bytes, computed without the implementation under test."""
    if isinstance(value, dict):
        pairs = [(expect(k), expect(v)) for k, v in value.items()]
        pairs.sort(key=lambda kv: kv[0])          # RFC 8949 4.2.1, applied here
        return head(5, len(pairs)) + b"".join(k + v for k, v in pairs)
    if isinstance(value, (list, tuple)):
        return head(4, len(value)) + b"".join(expect(x) for x in value)
    return cbor2.dumps(value)                     # independent implementation


# ------------------------------------------------------------------- the rows

DIGEST = hashlib.sha256(b"arp-deterministic-encoding-v0.2").digest()

CASES = [
    ("DE-01", "unsigned integers at every argument-width boundary",
     [0, 1, 23, 24, 255, 256, 65535, 65536, 2**32 - 1, 2**32]),
    ("DE-02", "negative integers at every argument-width boundary. v0.1 tested "
              "three of these and none above one byte",
     [-1, -24, -25, -256, -257, -65536, -65537, -2**32, -2**32 - 1]),
    ("DE-03", "byte strings at every length-argument boundary. **A 32-octet "
              "byte string is the shape of every digest this document "
              "commits to, and v0.1 contained none**, so a defect widening "
              "the bstr length argument passed the whole suite",
     [b"", b"\x01", bytes(23), bytes(24), DIGEST, bytes(255), bytes(256)]),
    ("DE-04", "text strings at every length-argument boundary, and multi-octet "
              "UTF-8",
     ["", "a", "IETF", "u" * 23, "u" * 24, "u" * 255, "u" * 256, "ü",
      "水"]),
    ("DE-05", "arrays at every length-argument boundary, and nesting",
     [[], [1, 2, 3], [1, [2, 3], [4, 5]], list(range(24)), list(range(256))]),
    ("DE-06", "maps at every length-argument boundary",
     [{}, {"a": 1},
      {"k%02d" % i: i for i in range(23)},
      {"k%03d" % i: i for i in range(24)}]),
    ("DE-07", "THE ORDERING ROW. Keys whose encoded forms have three different "
              "lengths, which is the only condition under which Section 4.2.1 "
              "and Section 4.2.3 can differ",
     {10: 1, 100: 2, -1: 3, "z": 4, "aa": 5}),
    ("DE-08", "ordering across major types: integer, byte-string and "
              "text-string keys in one map, which no v0.1 row contained",
     {1: "a", -1: "b", b"\x01": "c", "1": "d", b"": "e", "": "f"}),
    ("DE-09", "keys straddling the 24-octet encoded-length boundary, chosen "
              "so a short encoding with a HIGH first octet competes with a "
              "long encoding with a LOW one -- the condition under which the "
              "two orderings disagree most. A first draft of this row used "
              "four text keys of 22, 23 and 24 characters plus an integer; "
              "their two orderings coincided and the row discriminated "
              "nothing, which the exact-set control check caught",
     {bytes(24): 1, "z": 2, "k" * 24: 3, 1000000: 4}),
    ("DE-10", "**NESTED map ordering.** v0.1 had no map below the top level, "
              "so a depth-dependent ordering defect passed. This is the shape "
              "of the `{4: kid}` unprotected header inside every COSE_Sign1 "
              "this document signs",
     ["Signature1", {100: 1, -1: 2}, {"outer": {100: 1, -1: 2, "aa": 3}}]),
    ("DE-11", "the Section 6.4.1 request-binding preimage: the deterministic "
              "CBOR array of the four covered values",
     ["GET", "https://arp.example/arp/outputs/R_present",
      "n-0000000000000001", "p-other"]),
    ("DE-12", "the RFC 9052 Section 4.4 Sig_structure preimage, with the "
              "EdDSA protected header built from literal bytes rather than "
              "from the subject. v0.1 took this input FROM the subject, so a "
              "map defect in the protected header was baked into the input "
              "and the row still passed",
     ["Signature1", bytes.fromhex("a10127"), b"", b"payload-under-test"]),
    ("DE-13", "the signed read-response payload shape of Section 6.4.3, which "
              "carries two 32-octet digests and is the structure a defect in "
              "DE-03 would corrupt in production",
     ["arp-read-v1", DIGEST, 404, "2026-08-18T00:00:00Z", 4211, DIGEST, []]),
]

# Each control names the EXACT set of rows it must be caught by. Membership is
# not enough: a control credited because some unrelated row happened to notice
# it is a suite claiming coverage it does not have. Standing rules 9 and 11.
CONTROLS = [
    {"id": "NV-ARP-DE-01", "defect": "length-first-ordering",
     "channel": "map keys sorted by encoded length then bytewise, RFC 8949 "
                "Section 4.2.3 where Section 4.2.1 is required",
     "designed_rows": ["DE-07", "DE-08", "DE-09", "DE-10"]},
    {"id": "NV-ARP-DE-02", "defect": "non-shortest-argument",
     "channel": "a length or value argument encoded in a wider field than "
                "needed, in ANY major type",
     "designed_rows": ["DE-01", "DE-02", "DE-03", "DE-04", "DE-05", "DE-06",
                       "DE-07", "DE-08", "DE-09", "DE-10", "DE-11", "DE-12",
                       "DE-13"]},
    {"id": "NV-ARP-DE-03", "defect": "indefinite-length",
     "channel": "indefinite-length containers, which Section 4.2.1 forbids. "
                "Every row is designed to catch this one, because every row's "
                "value is or contains a container. A control that everything "
                "catches is weak evidence about any single row and is still "
                "worth carrying: what it establishes is that the suite refuses "
                "the defect at all",
     "designed_rows": ["DE-01", "DE-02", "DE-03", "DE-04", "DE-05", "DE-06",
                       "DE-07", "DE-08", "DE-09", "DE-10", "DE-11", "DE-12",
                       "DE-13"]},
    {"id": "NV-ARP-DE-04", "defect": "wide-string-length",
     "channel": "byte-string, array and map length arguments widened to two "
                "octets once they reach 24. **This is the defect that passed "
                "v0.1 completely**, because no v0.1 row reached a length of "
                "24 in those major types",
     "designed_rows": ["DE-03", "DE-04", "DE-05", "DE-06", "DE-09", "DE-11",
                       "DE-13"]},
]

# RFC 3986 Sections 6.2.2 and 6.2.3. Every expected normalised form below is
# WRITTEN OUT HERE, not produced by the subject, and the subject is asserted
# against it. The request-binding digest is then computed from the literal
# normalised string with the builder's own encoder, so neither half of the row
# comes from the implementation under test.
NONCE = "n-0000000000000001"
KEYID = "p-other"

NORMALISATION = [
    ("NORM-01", "6.2.2.1 host case",
     "https://ARP.Example/arp/outputs/R1",
     "https://arp.example/arp/outputs/R1"),
    ("NORM-02", "6.2.2.1 scheme case, and 6.2.3 default port dropped",
     "HTTPS://arp.example:443/arp/outputs/R1",
     "https://arp.example/arp/outputs/R1"),
    ("NORM-03", "6.2.3 a non-default port is kept",
     "https://arp.example:8443/arp/outputs/R1",
     "https://arp.example:8443/arp/outputs/R1"),
    ("NORM-04", "6.2.2.3 dot-segment removal",
     "https://arp.example/arp/./outputs/../outputs/R1",
     "https://arp.example/arp/outputs/R1"),
    ("NORM-05", "6.2.2.2 a percent-encoded unreserved character is decoded",
     "https://arp.example/arp/outputs/R%5fpresent",
     "https://arp.example/arp/outputs/R_present"),
    ("NORM-06", "6.2.2.1 and 6.2.2.2: %2F is a reserved character, so its "
                "hexadecimal digits are uppercased and it is NOT decoded. "
                "Decoding it would change the path's segment structure, which "
                "is a different resource",
     "https://arp.example/arp/outputs/r%2fpresent",
     "https://arp.example/arp/outputs/r%2Fpresent"),
    ("NORM-07", "6.2.3 an empty path becomes /",
     "https://arp.example",
     "https://arp.example/"),
    ("NORM-08", "userinfo is preserved. Dropping it makes two distinct "
                "targets normalise to one binding, which is the failure this "
                "normalisation exists to prevent",
     "https://joel@arp.example/arp/outputs/R1",
     "https://joel@arp.example/arp/outputs/R1"),
    ("NORM-09", "a fragment is not sent on the wire and is excluded",
     "https://arp.example/arp/outputs/R1#frag",
     "https://arp.example/arp/outputs/R1"),
    ("NORM-10", "5.2.4 dot segments that would climb above the root are "
                "discarded rather than escaping it",
     "https://arp.example/a/b/../../../c",
     "https://arp.example/c"),
]

NORM_CONTROLS = [
    {"id": "NV-ARP-NM-01", "defect": "pre-3986-normaliser",
     "channel": "the normaliser this tree carried until 2026-08-18: scheme "
                "and host lowercased and a default port dropped, but no "
                "dot-segment removal, no percent-encoding normalisation, and "
                "userinfo discarded silently",
     "designed_rows": ["NORM-04", "NORM-05", "NORM-06", "NORM-08",
                       "NORM-10"]},
]

UNTESTED = [
    "Floating-point values. The encoder raises TypeError on a float and this "
    "document commits to none, so the shortest-float rule of Section 4.2.1 is "
    "out of scope by construction rather than untested by omission. Stated "
    "here so the omission is a decision and not a gap.",
    "Tags. The encoder emits no major type 6; the COSE_Sign1 tag 0xd2 is "
    "prepended by hand in arp_read_ref.py and is not produced by this encoder.",
    "Duplicate map keys. Python cannot express one, so no vector in this file "
    "can carry it. An implementation reading CBOR must still refuse them.",
    "Internationalised domain names. No NORM row carries a non-ASCII host, "
    "and this class states no position on whether a target is normalised to "
    "A-labels before digesting. Two parties disagreeing about that compute "
    "different bindings.",
]


def build():
    vectors = []
    for vid, purpose, value in CASES:
        exp = expect(value)
        node = C.emit(value)
        if C.parse(node) != value:
            raise SystemExit("%s: typed input does not round-trip" % vid)
        got = ref.cbor(value)
        if got != exp:
            raise SystemExit(
                "%s: the implementation under test does not reproduce the "
                "independently computed bytes.\n  expected %s\n  got      %s"
                % (vid, exp.hex(), got.hex()))
        vectors.append({
            "id": vid,
            "purpose": purpose,
            "input": node,
            "expected_hex": exp.hex(),
        })

    for nid, _purpose, raw, norm in NORMALISATION:
        got = uri.normalise_target(raw)
        if got != norm:
            raise SystemExit(
                "%s: the normaliser under test does not reproduce the "
                "expected form.\n  raw      %s\n  expected %s\n  got      %s"
                % (nid, raw, norm, got))

    div = {10: 1, 100: 2, -1: 3, "z": 4, "aa": 5}
    pairs = [(expect(k), expect(v)) for k, v in div.items()]
    s421 = head(5, len(pairs)) + b"".join(
        k + v for k, v in sorted(pairs, key=lambda kv: kv[0]))
    s423 = head(5, len(pairs)) + b"".join(
        k + v for k, v in sorted(pairs, key=lambda kv: (len(kv[0]), kv[0])))
    can = cbor2.dumps(div, canonical=True)

    return {
        "class": "arp-deterministic-encoding",
        "version": "v0.2",
        "supersedes": "v0.1, which three encoder defects passed. See "
                      "runners/build_deterministic_encoding_vectors.py.",
        "spec": "RFC 8949 Section 4.2.1, as cited by draft-hillier-scitt-arp "
                "for every digest preimage and every signed payload",
        "property": "The deterministic encoder reproduces byte strings the "
                    "implementation under test did not compute.",
        "expectation_provenance":
            "Scalars, strings and arrays: encoded by cbor2 %s, which shares no "
            "code with this tree. Maps: each key and value encoded by cbor2 "
            "independently, the encoded key byte strings sorted by the "
            "builder's own bytewise comparison, the head emitted by the "
            "builder's own argument-width logic. The implementation under test "
            "contributes NOTHING to any expectation and is asserted against "
            "them. cbor2's canonical mode is never called." % CBOR2_VERSION,
        "built_against": {
            "encoder_sha256": _sha256_file(REF),
            "normaliser_sha256": _sha256_file(URI),
            "independent_implementation": "cbor2 %s" % CBOR2_VERSION,
        },
        "corroboration_boundary":
            "cbor2 is an independent implementation of CBOR item encoding. It "
            "is NOT an independent implementation of the Section 4.2.1 map "
            "ordering: its canonical mode emits the Section 4.2.3 ordering, so "
            "on that rule it is a second implementation that DISAGREES. The "
            "ordering in this file is therefore the builder's own application "
            "of the RFC text to independently encoded keys. Two "
            "implementations are not a vote and the RFC decides it. Standing "
            "rule 8.",
        "measured_divergence": {
            "input_repr": "{10: 1, 100: 2, -1: 3, 'z': 4, 'aa': 5}",
            "rfc8949_s421_hex": s421.hex(),
            "rfc8949_s423_length_first_hex": s423.hex(),
            "cbor2_canonical_hex": can.hex(),
            "cbor2_canonical_matches_s423": can == s423,
            "cbor2_canonical_matches_s421": can == s421,
            "measured_by": "the builder, not the runner. The runner has no "
                           "cbor2 and copies this block forward as a recorded "
                           "measurement rather than repeating it.",
            "finding": "cbor2 %s in canonical mode emits the Section 4.2.3 "
                       "ordering. Both orderings are well-formed CBOR and only "
                       "one is the one this document cites, so an "
                       "implementation computing ARP digests with it ships "
                       "non-conforming bytes and raises no error."
                       % CBOR2_VERSION,
        },
        "normalisation": [
            {"id": nid, "purpose": purpose, "raw": raw,
             "expected_normalised": norm,
             "expected_request_binding_hex":
                 hashlib.sha256(expect(["GET", norm, NONCE, KEYID])).hexdigest()}
            for nid, purpose, raw, norm in NORMALISATION
        ],
        "normalisation_note":
            "Section 6.4.1 digests a NORMALISED target so that two clients "
            "addressing one resource compute one binding. Each expected "
            "normalised form here is written into the builder rather than "
            "produced by the subject, and each request-binding digest is "
            "computed from that literal string with the builder's own "
            "encoder, so neither half of a row comes from the implementation "
            "under test. Nonce %r, keyid %r." % (NONCE, KEYID),
        "normalisation_controls": NORM_CONTROLS,
        "defective_encoders": CONTROLS,
        "does_not_establish": UNTESTED,
        "vectors": vectors,
    }


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    doc = build()
    with open(OUT, "w", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    sys.stdout.write("written %s\n" % OUT)
    sys.stdout.write("  %d encoding rows, %d encoder controls\n"
                     % (len(doc["vectors"]), len(doc["defective_encoders"])))
    sys.stdout.write("  %d normalisation rows, %d normalisation controls\n"
                     % (len(doc["normalisation"]),
                        len(doc["normalisation_controls"])))
    sys.stdout.write("  %d declared non-coverage items\n"
                     % len(doc["does_not_establish"]))
    md = doc["measured_divergence"]
    sys.stdout.write("  cbor2 canonical == S4.2.3: %s   == S4.2.1: %s\n"
                     % (md["cbor2_canonical_matches_s423"],
                        md["cbor2_canonical_matches_s421"]))
