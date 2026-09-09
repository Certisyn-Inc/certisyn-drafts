#!/usr/bin/env python3
"""Which ARP digests move when an ECDSA signature is replaced by its twin.

    python3 runners/ecdsa_malleability_probe.py     # no arguments

Anton Sokolov posted the reproduction to the SCITT list on 2026-08-18: for an
ECDSA signature (r, s), the pair (r, n - s) verifies against the same key over
the same message. SEC1 v2.0 Section 4.1.4 and FIPS 186-5 Section 6.4.2
range-check r and s only, and RFC 9053 Section 2.1 constrains neither, so the
substitution is outside every check any of them imposes. Nothing is violated
and nothing is forged: the same authority signed, and a party holding no key
produces the second byte-string from the first, in transit.

What this measures is not the malleability, which is not in doubt. It is which
of ARP's digests move when it happens.

EVERY REPORTED NUMBER IS DERIVED FROM THE TWO SERVED BYTE-STRINGS. The first
version of this probe computed its -04 leg as sha256(X) == sha256(X) -- it
rebuilt the Sig_structure from the same local it had signed, so the
substitution never reached the value under test -- and printed two further rows
from hardcoded literals. It reported 200 of 200 for measurements that were not
taken. Every value below is now recovered by PARSING entry_a and entry_b, so a
leg that does not actually apply the substitution cannot report stability.

Standard library plus `cryptography`.
"""

import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "reference"))
from arp_cbor import cbor                                     # noqa: E402

from cryptography.hazmat.primitives import hashes             # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec      # noqa: E402
from cryptography.hazmat.primitives.asymmetric.utils import ( # noqa: E402
    decode_dss_signature, encode_dss_signature)

N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
PROTECTED = cbor({1: -7})            # ES256
KID = b"arp-seal-1"
TRIALS = 200


# ------------------------------------------------------------ minimal decoder
# Definite lengths only, which is all Section 4.2.1 permits and all this tree
# emits. It exists so the probe can recover values from SERVED bytes rather
# than reuse the locals it signed.

def dec(b, i=0):
    m, a = b[i] >> 5, b[i] & 0x1F
    i += 1
    if a < 24:
        v = a
    elif a == 24:
        v, i = b[i], i + 1
    elif a == 25:
        v, i = int.from_bytes(b[i:i + 2], "big"), i + 2
    elif a == 26:
        v, i = int.from_bytes(b[i:i + 4], "big"), i + 4
    elif a == 27:
        v, i = int.from_bytes(b[i:i + 8], "big"), i + 8
    else:
        raise ValueError("indefinite length")
    if m == 0:
        return v, i
    if m == 1:
        return -1 - v, i
    if m in (2, 3):
        raw = b[i:i + v]
        return (raw if m == 2 else raw.decode()), i + v
    if m == 4:
        out = []
        for _ in range(v):
            x, i = dec(b, i)
            out.append(x)
        return out, i
    if m == 5:
        out = {}
        for _ in range(v):
            k, i = dec(b, i)
            x, i = dec(b, i)
            out[k if not isinstance(k, list) else tuple(k)] = x
        return out, i
    if m == 6:
        return dec(b, i)                       # skip the tag, return content
    if m == 7 and a == 22:
        return None, i
    raise ValueError("unsupported major type %d" % m)


def sig_structure_of(envelope_bytes):
    """Recover ["Signature1", protected, b"", payload] from a served COSE_Sign1.

    The protected header is taken as the byte string that was transmitted and
    is NOT re-encoded: those bytes are the signer's and are what the signature
    covers.
    """
    arr, _ = dec(envelope_bytes)
    protected, _unprotected, payload, _sig = arr
    return cbor(["Signature1", protected, b"", payload])


def _envelope(payload, raw_sig):
    return b"\xd2" + cbor([PROTECTED, {4: KID}, payload, raw_sig])


def one_trial():
    sk = ec.generate_private_key(ec.SECP256R1())
    pk = sk.public_key()

    body = [4211, "reconciliation", os.urandom(32), os.urandom(32),
            "2026-08-18T00:00:00Z", os.urandom(32)]
    self_entry_hash = hashlib.sha256(cbor(body + [None, None])).digest()
    signed_payload = cbor(body + [self_entry_hash, None])
    to_sign = cbor(["Signature1", PROTECTED, b"", signed_payload])

    r, s = decode_dss_signature(sk.sign(to_sign, ec.ECDSA(hashes.SHA256())))
    raw_a = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    raw_b = r.to_bytes(32, "big") + (N - s).to_bytes(32, "big")

    def verifies(raw):
        rr = int.from_bytes(raw[:32], "big")
        ss = int.from_bytes(raw[32:], "big")
        try:
            pk.verify(encode_dss_signature(rr, ss), to_sign,
                      ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    env_a = _envelope(signed_payload, raw_a)
    env_b = _envelope(signed_payload, raw_b)
    entry_a = cbor(body + [self_entry_hash, env_a])
    entry_b = cbor(body + [self_entry_hash, env_b])

    # --- every value below is recovered from the SERVED bytes ---------------

    # -03 Prior-Entry Hash: over the whole preceding entry, signature included.
    old_a = hashlib.sha256(entry_a).digest()
    old_b = hashlib.sha256(entry_b).digest()

    # -04 Prior-Entry Hash: the Signing Input Digest, rebuilt by PARSING each
    # served entry rather than by reusing the local that was signed.
    def sid_of_entry(entry_bytes):
        arr, _ = dec(entry_bytes)
        return hashlib.sha256(sig_structure_of(arr[-1])).digest()
    new_a, new_b = sid_of_entry(entry_a), sid_of_entry(entry_b)

    # Self-Entry Hash: recomputed from each served entry, signature position
    # and self-hash position nulled.
    def seh_of_entry(entry_bytes):
        arr, _ = dec(entry_bytes)
        return hashlib.sha256(cbor(arr[:-2] + [None, None])).digest()
    seh_a, seh_b = seh_of_entry(entry_a), seh_of_entry(entry_b)

    # Reconciliation Hash: Section 3 excludes the SEALING signature only, and
    # Section 4.14 puts the register's signed Partial Attestation inside a
    # Query Binding Record, which is inside the Output. So the preimage carries
    # a register signature. Built here with the two attestation encodings.
    def output_with(att_envelope):
        query_binding_record = ["qbr", b"\x01" * 8, b"\x02" * 8,
                                b"\x03" * 8, att_envelope]
        out = ["arp-output-v1", b"\x44" * 32, "match", [query_binding_record],
               b"\x55" * 32]                       # sealing sig excluded
        return hashlib.sha256(cbor(out)).digest()
    rh_a, rh_b = output_with(env_a), output_with(env_b)

    return {
        "both_verify": verifies(raw_a) and verifies(raw_b),
        "bytes_differ": entry_a != entry_b,
        "prior_entry_hash_03_stable": old_a == old_b,
        "prior_entry_hash_04_stable": new_a == new_b,
        "self_entry_hash_stable": seh_a == seh_b,
        "reconciliation_hash_stable": rh_a == rh_b,
    }


def main():
    k = ["both_verify", "bytes_differ", "prior_entry_hash_03_stable",
         "prior_entry_hash_04_stable", "self_entry_hash_stable",
         "reconciliation_hash_stable"]
    tally = dict((x, 0) for x in k)
    for _ in range(TRIALS):
        t = one_trial()
        for x in k:
            tally[x] += t[x]

    w = sys.stdout.write
    w("ARP digest stability under ECDSA signature substitution\n")
    w("  trials                              %d, ES256 / P-256\n" % TRIALS)
    w("  both byte-strings verify            %d of %d\n"
      % (tally["both_verify"], TRIALS))
    w("  entry bytes differ                  %d of %d\n\n"
      % (tally["bytes_differ"], TRIALS))
    rows = [
        ("Prior-Entry Hash  -03", "over the entry, signature included",
         "prior_entry_hash_03_stable"),
        ("Prior-Entry Hash  -04", "Signing Input Digest, parsed from the "
         "served entry", "prior_entry_hash_04_stable"),
        ("Self-Entry Hash", "signature position nulled, recomputed from the "
         "served entry", "self_entry_hash_stable"),
        ("Reconciliation Hash", "S3 excludes the SEALING signature; the "
         "preimage still carries a REGISTER signature via the Query Binding "
         "Record of S4.14", "reconciliation_hash_stable"),
    ]
    for name, note, key in rows:
        w("  %-22s stable %3d of %d\n" % (name, tally[key], TRIALS))
        w("  %-22s %s\n\n" % ("", note))
    w("CONCLUSION:\n")
    if tally["reconciliation_hash_stable"] != TRIALS:
        w("  The Reconciliation Hash is NOT outside the signature. It excludes\n"
          "  the sealing signature and carries register signatures inside its\n"
          "  preimage. It is a field of every Ledger entry, so it is inside\n"
          "  the Entry Signature payload and therefore inside the -04\n"
          "  Prior-Entry Hash: the fix is undone at one remove.\n")
    else:
        w("  Every digest reported above is stable under the substitution.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
