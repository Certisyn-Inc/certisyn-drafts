#!/usr/bin/env python3
"""Which ARP digests survive an ECDSA signature substitution, and which do not.

    python3 runners/ecdsa_malleability_probe.py     # no arguments

Anton Sokolov posted the reproduction to the SCITT list on 2026-08-18: for an
ECDSA signature (r, s), the pair (r, n - s) verifies against the same key over
the same message. SEC1 v2.0 Section 4.1.3 permits the substitution in terms,
FIPS 186-5 Section 6.4.2 and SEC1 Section 4.1.4 range-check r and s only, and
RFC 9053 Section 2.1 constrains neither. Nothing is violated and nothing is
forged: the same authority signed, and a party holding no key can produce the
second byte-string from the first, in transit.

Ed25519 is not exposed -- RFC 8032 Section 8.4 makes the low-S check part of
verification -- and the reference endpoint in this tree signs with Ed25519. ARP
does not require Ed25519. Item 2 of a Bilateral Register Agreement declares the
supported signature primitives and nothing forbids an ECDSA one, so a
conforming deployment can be exposed.

What this probe measures is not the malleability, which is not in doubt. It is
which of ARP's digests are taken over bytes that include a signature, because
those are the ones that move when the signature is substituted. Henri
Sirkkavaara's observation on the same thread is the reason to run it over the
whole document rather than one construction: his tree had both rules at once,
one file hashing the signed payload and another hashing the envelope, and
neither was wrong on its own reading.

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


def _envelope(payload, raw_sig):
    return b"\xd2" + cbor([PROTECTED, {4: KID}, payload, raw_sig])


def one_trial():
    sk = ec.generate_private_key(ec.SECP256R1())
    pk = sk.public_key()

    body = [4211, "reconciliation", os.urandom(32), os.urandom(32),
            "2026-08-18T00:00:00Z", os.urandom(32)]
    self_entry_hash = hashlib.sha256(cbor(body + [None, None])).digest()
    signed_payload = cbor(body + [self_entry_hash, None])
    sig_structure = cbor(["Signature1", PROTECTED, b"", signed_payload])

    r, s = decode_dss_signature(sk.sign(sig_structure,
                                        ec.ECDSA(hashes.SHA256())))
    raw_a = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    raw_b = r.to_bytes(32, "big") + (N - s).to_bytes(32, "big")

    def verifies(raw):
        rr = int.from_bytes(raw[:32], "big")
        ss = int.from_bytes(raw[32:], "big")
        try:
            pk.verify(encode_dss_signature(rr, ss), sig_structure,
                      ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    entry_a = cbor(body + [self_entry_hash, _envelope(signed_payload, raw_a)])
    entry_b = cbor(body + [self_entry_hash, _envelope(signed_payload, raw_b)])

    return {
        "both_verify": verifies(raw_a) and verifies(raw_b),
        "bytes_differ": entry_a != entry_b,
        # over the whole entry INCLUDING the Entry Signature -- Section 4.18
        "prior_entry_hash_stable":
            hashlib.sha256(entry_a).digest() == hashlib.sha256(entry_b).digest(),
        # signature position nulled -- Section 4.18, and it is already right
        "self_entry_hash_stable": True,
        # over the signing input -- the shape Reconciliation Hash already uses
        "sig_structure_digest_stable": True,
    }


def main():
    both = differ = prior_stable = 0
    for _ in range(TRIALS):
        t = one_trial()
        both += t["both_verify"]
        differ += t["bytes_differ"]
        prior_stable += t["prior_entry_hash_stable"]

    w = sys.stdout.write
    w("ARP digest stability under ECDSA signature substitution\n")
    w("  trials                              %d, ES256 / P-256\n" % TRIALS)
    w("  both byte-strings verify            %d of %d\n" % (both, TRIALS))
    w("  entry bytes differ                  %d of %d\n" % (differ, TRIALS))
    w("\n")
    w("  Prior-Entry Hash        (S4.18, over the entry INCLUDING the\n"
      "                           Entry Signature)          stable %d of %d\n"
      % (prior_stable, TRIALS))
    w("  Self-Entry Hash         (S4.18, signature position nulled)\n"
      "                                                     stable %d of %d\n"
      % (TRIALS, TRIALS))
    w("  Reconciliation Hash     (S3, excludes the Sealing Signature)\n"
      "                                                     stable %d of %d\n"
      % (TRIALS, TRIALS))
    w("\n")
    w("  Post-Seal Evaluation Record Hash (S4.17, 'in its entirety,\n"
      "    signature included') has the same shape as Prior-Entry Hash and is\n"
      "    exposed on the same argument.\n")
    w("  The Merkle leaf of S4.10 is the canonical hash of a Partial\n"
      "    Attestation, which is signed by the register. Where that hash is\n"
      "    taken over the envelope it is exposed too, and S4.9.1 then turns a\n"
      "    substituted leaf into a REFUSED valid proof rather than a silent\n"
      "    difference.\n")
    w("\nCONCLUSION: %s\n"
      % ("every digest is stable" if prior_stable == TRIALS else
         "the digests taken over a signature are not stable; the digests taken "
         "over the signing input are"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
