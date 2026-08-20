"""Run Anton Sokolov's two 395-byte secure-element files through ARP's
constructions, and report what the ledger verifier does with the twin.

Files, as received 2026-08-20:
  receipt.cose        87044ba3...  high-S as the secure element produced it
  receipt-twin.cose   d374e5d4...  the (r, n-s) substitution and nothing else
  attested-pub.pem                 P-256 key from the device attestation cert
"""
import hashlib, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "conformance", "runners"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "conformance", "reference"))

from ecdsa_malleability_probe import dec, sig_structure_of, N
from arp_cbor import cbor

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import ec, utils as asym_utils
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature

def sha(b): return hashlib.sha256(b).hexdigest()

HERE = os.path.dirname(os.path.abspath(__file__))

def _find(name):
    """The files may sit beside this script or one level up in _audit/.

    Resolved against the script's own location rather than the caller's
    working directory, so the run does not depend on where it was invoked.
    """
    for d in (HERE, os.path.dirname(HERE)):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit("cannot find %s in %s or its parent" % (name, HERE))

orig = open(_find("receipt.cose"), "rb").read()
twin = open(_find("receipt-twin.cose"), "rb").read()
pub  = load_pem_public_key(open(_find("attested-pub.pem"), "rb").read())

print("=" * 74)
print("0. FILES AS RECEIVED")
print("=" * 74)
for n, b in (("receipt.cose", orig), ("receipt-twin.cose", twin)):
    print(f"  {n:20s} {len(b):4d} B  sha256 {sha(b)}")

# ---------------------------------------------------------------- parse
def parse(b):
    # strip COSE_Sign1 tag 18 (0xd2) if present
    arr, _ = dec(b)
    return arr

o = parse(orig); t = parse(twin)
o_prot, o_unprot, o_pay, o_sig = o
t_prot, t_unprot, t_pay, t_sig = t

print()
print("=" * 74)
print("1. WHAT DIFFERS BETWEEN THEM")
print("=" * 74)
print(f"  protected header identical : {o_prot == t_prot}")
print(f"  unprotected header identical: {o_unprot == t_unprot}")
print(f"  payload identical          : {o_pay == t_pay}")
print(f"  signature identical        : {o_sig == t_sig}")
print(f"  protected header (hex)     : {o_prot.hex()}")
print(f"  protected header (decoded) : {dec(o_prot)[0]}")
print(f"  unprotected header         : {o_unprot}")
print(f"  payload length             : {len(o_pay)} B")

r1 = int.from_bytes(o_sig[:32], "big"); s1 = int.from_bytes(o_sig[32:], "big")
r2 = int.from_bytes(t_sig[:32], "big"); s2 = int.from_bytes(t_sig[32:], "big")
print()
print(f"  r equal                    : {r1 == r2}")
print(f"  s2 == n - s1               : {s2 == N - s1}")
print(f"  s1 low-S (s1 <= n/2)       : {s1 <= N // 2}")
print(f"  s2 low-S (s2 <= n/2)       : {s2 <= N // 2}")

# ---------------------------------------------------------------- verify both
print()
print("=" * 74)
print("2. DO BOTH VERIFY, AGAINST THE ATTESTATION-CERT KEY")
print("=" * 74)
for name, arr, sig in (("original", o, o_sig), ("twin", t, t_sig)):
    si = cbor(["Signature1", arr[0], b"", arr[2]])
    der = asym_utils.encode_dss_signature(
        int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big"))
    try:
        pub.verify(der, si, ec.ECDSA(hashes.SHA256()))
        ok = "VERIFIES"
    except InvalidSignature:
        ok = "REJECTED"
    print(f"  {name:9s} {ok}")

si_o = sig_structure_of(orig); si_t = sig_structure_of(twin)
print()
print(f"  Sig_structure byte-identical : {si_o == si_t}")
print(f"  Signing Input Digest, orig   : {sha(si_o)}")
print(f"  Signing Input Digest, twin   : {sha(si_t)}")

# ------------------------------------------------- ARP ledger constructions
print()
print("=" * 74)
print("3. ARP LEDGER CONSTRUCTIONS, -03 AND -04 SIDE BY SIDE")
print("=" * 74)

def entry(env, prior):
    """A Settlement-Layer Ledger entry carrying this artefact.

    -03 chained on the enveloped bytes. -04 chains on the Signing Input
    Digest. Both shown over the same two files.
    """
    return {
        "-03 Prior-Entry Hash": sha(prior + env),
        "-04 Prior-Entry Hash": sha(prior + bytes.fromhex(sha(sig_structure_of(env)))),
    }

PRIOR = bytes(32)
eo = entry(orig, PRIOR); et = entry(twin, PRIOR)
for k in eo:
    same = "SAME" if eo[k] == et[k] else "DIFFER"
    print(f"  {k:24s} {same}")
    print(f"      original {eo[k]}")
    print(f"      twin     {et[k]}")

# ------------------------------------------------- what a verifier concludes
print()
print("=" * 74)
print("4. WHAT ARP'S LEDGER VERIFIER DOES WITH THE TWIN")
print("=" * 74)

leaf_o_03 = sha(orig)
leaf_t_03 = sha(twin)
leaf_o_04 = sha(sig_structure_of(orig))
leaf_t_04 = sha(sig_structure_of(twin))

print("  Merkle leaf under -03 (over the served envelope):")
print(f"      distinct leaves: {leaf_o_03 != leaf_t_03}  -> two entries for one signing act")
print("  Merkle leaf under -04 (over the Sig_structure):")
print(f"      distinct leaves: {leaf_o_04 != leaf_t_04}  -> one entry for one signing act")

print()
print("  Section 4.9.1 leaf binding: a verifier recomputes the leaf from the")
print("  object rather than trusting the leaf a proof carries.")
print("    Holder has ORIGINAL, proof was issued over TWIN:")
print(f"      -03: recomputed {leaf_o_03[:16]}... vs carried {leaf_t_03[:16]}...  MISMATCH -> proof REFUSED")
print(f"      -04: recomputed {leaf_o_04[:16]}... vs carried {leaf_t_04[:16]}...  {'MATCH -> proof ACCEPTED' if leaf_o_04 == leaf_t_04 else 'MISMATCH'}")
