#!/usr/bin/env python3
"""
ARP reconcile legs over the Tyche EATF / AEP envelope corpus  --  v2
=====================================================================

Anton Sokolov (27 Jul): the EATF negatives are envelope-integrity classes.
Which of them are visible at the reconcile layer AT ALL?

v2 supersedes a first pass that overstated the answer. Every change was forced
by adversarial review of v1, and each is noted so the delta is auditable:

  * v1 asserted the corpus ships no trust anchor. It does --
    test-vectors/keys/dev-rsa-4096.pem. v2 loads it, the issuer-trust leg
    becomes decisive, and untrusted-issuer separates from a plain bad
    signature. v1 could not tell them apart.
  * v1 classified bad-timestamp as HELD. Its leg vector is bit-identical to
    three valid packages, so ARP emits zero bits about it. v2 classifies by
    observability and reports which legs are constant.
  * v1 compared 4 hand-picked metadata/receipt pairs and called it a general
    cross-claim property. The AEP profile cross-checks 6 pairs including
    camelCase alternates. v2 implements the profile's set and drops the
    generality claim.
  * v1's DigestInfo fallback compared only trailing bytes -- it accepted a
    SHA-1 AlgorithmIdentifier carrying a SHA-256 digest. v2 parses the
    DigestInfo and checks the OID.
  * v1 marked string comparisons crypto-verified. v2 labels legs by what they
    did.
  * v1 never read overt_receipt.sig, the one place in this corpus where the
    receipt is independently signed. v2 verifies it.
  * v1's required-entry list omitted timestamp.tsr, so a package missing that
    entry was invisible. v2 uses the AEP required-entry set.

Classification:
  SEEN     decisive REFUSE on a binding ARP independently recomputed
  HELD     INDETERMINATE, and at least one leg carried information about it
  BENEATH  ARP's output is indistinguishable from some valid package

BENEATH is the layer boundary, not a miss: those faults are the producer's
verification surface.

Usage:
    python3 arp_eatf.py --corpus <clone>/test-vectors [--json out.json]
                        [--no-trust-anchor]
"""

import argparse, base64, hashlib, json, os, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arp_reconcile import jcs_bytes, subject_digest, CRYPTO, DERIVED, COMPUTED

try:
    from cryptography.hazmat.primitives.serialization import (
        load_pem_public_key, Encoding, PublicFormat)
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.exceptions import InvalidSignature
    _CRYPTO = True
except ImportError:
    _CRYPTO = False

# --------------------------------------------------------------------------
# Local axis algebra. v1 reused arp_reconcile.compose(), which fails OPEN: an
# axis absent from HARD_AXES (including a typo) silently yields INDETERMINATE.
# Here every axis is declared with its class and an unknown axis is an error.
# --------------------------------------------------------------------------
HARD = {
    "artifact-tampered", "signature-invalid", "signature-malformed",
    "digest-mismatch", "agent-principal-unverifiable",
    "capsule-component-absent", "profile-cross-check-divergent",
}
SOFT = {
    "caid-binding-unverified", "metadata-not-signature-bound",
    "issuer-trust-unevaluated", "leg-not-independently-verified",
    "cross-check-not-applicable",
}


def compose_ex(legs):
    """v2 parity with arp_reconcile.compose_ex: fail closed AND report the gate.

    v1 of this module already failed closed on an undeclared axis, but it
    returned a bare verdict. A reader could not tell whether a REFUSE was
    reached before or after the evidence downstream of it had been evaluated
    -- which matters here, because the EATF profile refuses several packages
    at the signature gate and never reaches the timestamp token at all.

    Returns (verdict, refused_at, deciding_axis).
    """
    for _, _, ax, _ in legs:
        if ax and ax not in HARD and ax not in SOFT:
            raise SystemExit(
                f"undeclared divergence axis {ax!r}. Every axis MUST be "
                "declared HARD or SOFT before it can carry a verdict. "
                "Refusing to compose."
            )
    for src, _v, ax, _p in legs:
        if ax in HARD:
            return "REFUSE", src, ax
    for src, v, ax, _p in legs:
        if v != "match":
            return "INDETERMINATE", src, ax
    return "APPROVE", None, None


def compose(legs):
    return compose_ex(legs)[0]


def checked(ret, where):
    """v2 ADDITION, ported from arp_reconcile v2.1.

    Assert that a reconciler's reported disposition is the one its own legs
    compose to. In arp_reconcile v2 one suite reported a hand-written
    disposition beside a leg set that composed to something else, and the run
    did not notice for a whole corpus. A convention that can be broken
    silently is not a guarantee; this makes it one.

    Tolerates the 4-tuple return shape this module uses.
    """
    legs, disp = ret[1], ret[2]
    expected = compose(legs)
    if disp != expected:
        raise SystemExit(
            f"disposition/leg disagreement in {where}: reported {disp!r} but "
            f"the legs {legs!r} compose to {expected!r}. A disposition MUST be "
            "the output of the Verdict Arithmetic over the legs, never written "
            "beside them. Refusing to report."
        )
    return ret


# AEP required-entry set, verbatim from lib-python/eatf_verifier/verifier.py.
REQUIRED = ("response.txt", "canonical.bin", "hash.sha256", "signature.sig",
            "public_key.pem", "metadata.json", "timestamp.tsr")

# The AEP profile's own metadata<->receipt cross-checks, verbatim from
# lib-python/eatf_verifier/overt.py, camelCase alternates included.
CROSS = (
    (("created_at", "createdAt"),           ("event", "timestamp")),
    (("agent_id", "agentId"),               ("subject", "agent_id")),
    (("tenant_id_hash", "tenantIdHash"),    ("subject", "tenant_hash")),
    (("action_type", "actionType"),         ("event", "action_type")),
    (("policy_version", "policyVersion"),   ("policy", "version")),
    (("policy_decision", "policyDecision"), ("policy", "decision")),
)

SHA256_OID = bytes.fromhex("608648016503040201")   # 2.16.840.1.101.3.4.2.1


def _digestinfo_rsa(key, signature, expected_digest):
    """Raw RSA public op, strip PKCS#1 v1.5 padding, then PARSE the DigestInfo
    and check the OID. The AEP reference verifier accepts a BouncyCastle
    encoding omitting the SHA-256 AlgorithmIdentifier NULL parameters, so a
    strict-only verifier falsely rejects conforming packages. v1 implemented
    that leniency as a trailing-byte comparison, which also accepted a SHA-1
    AlgorithmIdentifier carrying a SHA-256 digest. This does not."""
    try:
        if len(expected_digest) != 32 or not signature:
            return False
        n, e = key.public_numbers().n, key.public_numbers().e
        k = (n.bit_length() + 7) // 8
        if len(signature) != k:
            return False
        enc = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
        if len(enc) < 11 or enc[0] != 0x00 or enc[1] != 0x01:
            return False
        sep = enc.find(b"\x00", 2)
        if sep < 0 or any(b != 0xFF for b in enc[2:sep]):
            return False
        di = enc[sep + 1:]
        if len(di) < 34 or di[0] != 0x30:
            return False
        if SHA256_OID not in di[:len(di) - 32]:
            return False                      # wrong or absent digest OID
        if di[-34] != 0x04 or di[-33] != 0x20:
            return False                      # trailing OCTET STRING(32)
        return di[-32:] == expected_digest
    except Exception:
        return False


def _spki(pem_bytes):
    try:
        k = load_pem_public_key(pem_bytes)
        return k.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
    except Exception:
        return None


def _entries(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def _first(d, keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d[k]
    return None


def _action(rec):
    if not isinstance(rec, dict):
        return None
    ev = rec.get("event") or {}
    su = rec.get("subject") or {}
    po = rec.get("policy") or {}
    return {"action_type": ev.get("action_type"), "event_type": ev.get("type"),
            "timestamp": ev.get("timestamp"), "agent_id": su.get("agent_id"),
            "system": su.get("system"), "policy_id": po.get("id"),
            "policy_decision": po.get("decision")}


def reconcile_aep(path, anchors):
    legs, info = [], {}
    e = _entries(path)

    # Leg 1 -- capsule completeness, against the AEP required-entry set.
    missing = [n for n in REQUIRED if n not in e]
    if missing:
        legs.append(("completeness", "no-match", "capsule-component-absent", COMPUTED))
        info["missing"] = missing
        return checked((None, legs, compose(legs), info),
                       "reconcile_eatf/early")
    legs.append(("completeness", "match", None, COMPUTED))

    canonical, response = e["canonical.bin"], e["response.txt"]

    # Leg 2 -- content binding. ARP recomputes this itself.
    stated = e["hash.sha256"].decode("ascii", "replace").strip().lower()
    actual = hashlib.sha256(canonical).hexdigest()
    content_ok = (stated == actual)
    legs.append(("content-binding", "match" if content_ok else "no-match",
                 None if content_ok else "artifact-tampered", CRYPTO))

    # Leg 3 -- is metadata inside the signed surface at all?
    meta = None
    try:
        meta = json.loads(e["metadata.json"])
        if canonical == response + b"\n" + jcs_bytes(meta):
            legs.append(("metadata-binding", "match", None, COMPUTED))
            info["metadata_signature_bound"] = True
        elif canonical == response:
            # Legacy response-only form: metadata is NOT covered by the hash,
            # the signature, or the timestamp. Anything reading metadata
            # downstream is reading an unauthenticated file.
            legs.append(("metadata-binding", "indeterminate",
                         "metadata-not-signature-bound", COMPUTED))
            info["metadata_signature_bound"] = False
        else:
            legs.append(("metadata-binding", "no-match", "artifact-tampered", COMPUTED))
            info["metadata_signature_bound"] = False
    except Exception:
        legs.append(("metadata-binding", "no-match", "artifact-tampered", COMPUTED))

    # Leg 4 -- signature under the key carried by the package.
    sig_path = None
    if _CRYPTO:
        try:
            key = load_pem_public_key(e["public_key.pem"])
            sig = base64.b64decode(e["signature.sig"].decode("ascii").strip())
            try:
                key.verify(sig, canonical, padding.PKCS1v15(), hashes.SHA256())
                ok, sig_path = True, "strict-pkcs1v15"
            except InvalidSignature:
                ok = _digestinfo_rsa(key, sig, hashlib.sha256(canonical).digest())
                sig_path = "digestinfo-no-null" if ok else None
        except Exception:
            ok, sig_path = False, "malformed"
    else:
        ok = None
    info["signature_path"] = sig_path
    if ok is None:
        legs.append(("signature", "indeterminate", "leg-not-independently-verified", DERIVED))
    elif ok:
        legs.append(("signature", "match", None, CRYPTO))
    else:
        legs.append(("signature", "no-match",
                     "signature-malformed" if sig_path == "malformed" else "signature-invalid",
                     CRYPTO))

    # Leg 5 -- issuer trust against the corpus's published anchor set. ARP-01
    # S6.3 forbids inferring trust from a self-asserted identifier. With an
    # anchor supplied this is decisive; without one the output is non-decisive.
    if anchors:
        packaged = _spki(e["public_key.pem"])
        trusted = packaged is not None and packaged in anchors
        legs.append(("issuer-trust", "match" if trusted else "no-match",
                     None if trusted else "agent-principal-unverifiable", CRYPTO))
        info["issuer_in_anchor_set"] = trusted
    else:
        legs.append(("issuer-trust", "indeterminate", "issuer-trust-unevaluated", COMPUTED))

    # Leg 6 -- receipt binding. String equality between two in-package values;
    # meaningful only if leg 2 held, so gated on it.
    rec = None
    if "overt_receipt.json" in e:
        try:
            rec = json.loads(e["overt_receipt.json"])
            if not content_ok:
                legs.append(("receipt-binding", "indeterminate",
                             "leg-not-independently-verified", COMPUTED))
            elif rec.get("content_hash") != f"sha256:{stated}":
                legs.append(("receipt-binding", "no-match", "digest-mismatch", COMPUTED))
            else:
                legs.append(("receipt-binding", "match", None, COMPUTED))
        except Exception:
            legs.append(("receipt-binding", "no-match", "artifact-tampered", COMPUTED))

    # Leg 7 -- separately signed receipt, where present. The only case in this
    # corpus where the receipt is an independently authenticated claim rather
    # than a second unsigned file in the same archive.
    if "overt_receipt.sig" in e and _CRYPTO and rec is not None:
        try:
            key = load_pem_public_key(e["public_key.pem"])
            rsig = base64.b64decode(e["overt_receipt.sig"].decode("ascii").strip())
            body = e["overt_receipt.json"]
            try:
                key.verify(rsig, body, padding.PKCS1v15(), hashes.SHA256())
                rok = True
            except InvalidSignature:
                rok = _digestinfo_rsa(key, rsig, hashlib.sha256(body).digest())
            legs.append(("receipt-signature", "match" if rok else "no-match",
                         None if rok else "signature-invalid", CRYPTO))
            info["receipt_independently_signed"] = bool(rok)
        except Exception:
            legs.append(("receipt-signature", "no-match", "signature-malformed", CRYPTO))

    # Leg 8 -- RFC 3161. ARP does not implement it. Constant across the corpus
    # and therefore information-free; reported so that is visible, not implied.
    if "timestamp.tsr" in e:
        legs.append(("timestamp", "indeterminate", "leg-not-independently-verified", DERIVED))

    # Leg 9 -- the AEP profile's metadata<->receipt cross-check, full field set.
    # NOT a general reconcile property: it is this profile's own check, and in
    # the legacy canonical form both files sit outside the signature, so they
    # are not independent claims.
    if isinstance(rec, dict) and isinstance(meta, dict):
        compared, diverged = 0, []
        for mkeys, (sec, rkey) in CROSS:
            mv = _first(meta, mkeys)
            rv = (rec.get(sec) or {}).get(rkey)
            if mv is None or rv is None:
                continue
            compared += 1
            if str(mv) != str(rv):
                diverged.append({"field": f"{sec}.{rkey}", "metadata": mv, "receipt": rv})
        info["cross_check_fields_compared"] = compared
        info["cross_check_divergences"] = diverged
        if diverged:
            legs.append(("profile-cross-check", "no-match",
                         "profile-cross-check-divergent", COMPUTED))
        elif compared == 0:
            # v1 asserted a positive match here having compared nothing.
            legs.append(("profile-cross-check", "indeterminate",
                         "cross-check-not-applicable", COMPUTED))
        else:
            legs.append(("profile-cross-check", "match", None, COMPUTED))

    # Leg 10 -- CAID guardrail. EATF's content_hash is SHA-256 over the AEP
    # canonical form; ARP's subject_digest is SHA-256(JCS(action)). Different
    # preimages. ARP does not assume they correspond.
    action = _action(rec)
    sd = subject_digest(action) if action else None
    if rec is not None:
        legs.append(("caid-binding", "indeterminate", "caid-binding-unverified", COMPUTED))

    info.update({"action": action, "content_hash": stated, "arp_subject_digest": sd})
    return checked((sd, legs, compose(legs), info), "reconcile_eatf")


def observable(legs):
    """What a consumer could actually see from a run."""
    return tuple(f"{s}|{v}|{ax}" for s, v, ax, _ in legs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--json")
    ap.add_argument("--no-trust-anchor", action="store_true")
    a = ap.parse_args()

    anchors = set()
    kd = os.path.join(a.corpus, "keys")
    if not a.no_trust_anchor and os.path.isdir(kd):
        for fn in sorted(os.listdir(kd)):
            if fn.endswith(".pem"):
                d = _spki(open(os.path.join(kd, fn), "rb").read())
                if d:
                    anchors.add(d)

    print()
    print("=" * 100)
    print("ARP reconcile legs over the Tyche EATF / AEP envelope corpus  (v2)")
    print("=" * 100)
    print("Question (A. Sokolov, 27 Jul): which envelope-integrity negatives are")
    print("visible at the reconcile layer at all?")
    print()
    print(f"  cryptography backend : {_CRYPTO}")
    print(f"  trust anchors loaded : {len(anchors)}"
          + (f"  from {kd}" if anchors else "   (issuer-trust unproven)"))
    print()

    rows = []
    for kind in ("valid", "invalid"):
        d = os.path.join(a.corpus, kind)
        if not os.path.isdir(d):
            continue
        print("-" * 100)
        print(f"{kind.upper()}  (corpus expects verify={'true' if kind == 'valid' else 'false'})")
        print("-" * 100)
        for name in sorted(os.listdir(d)):
            pkg = os.path.join(d, name, "package.aep")
            if not os.path.exists(pkg):
                continue
            exp = os.path.join(d, name, "verify-expected.txt")
            expected, diag = True, ""
            if os.path.exists(exp):
                t = open(exp).read()
                expected = "verify=true" in t
                for ln in t.splitlines():
                    if ln.startswith("diagnostic="):
                        diag = ln[11:].strip()
            sd, legs, disp, info = reconcile_aep(pkg, anchors)
            rows.append({"vector": name, "kind": kind, "expected_valid": expected,
                         "arp_disposition": disp, "producer_diagnostic": diag,
                         "legs": [{"source": s, "verdict": v, "axis": ax, "provenance": p}
                                  for s, v, ax, p in legs],
                         "observable": list(observable(legs)), **info})
            print(f"  {name:<28}{disp:<15}"
                  + "  ".join(f"{s}:{v}" + (f"[{ax}]" if ax else "")
                              for s, v, ax, _ in legs))
        print()

    # Classification by OBSERVABILITY, not charity: a vector whose leg vector
    # matches some valid package is invisible, whatever its disposition.
    valid_sigs = {tuple(r["observable"]) for r in rows if r["expected_valid"]}
    for r in rows:
        if r["expected_valid"]:
            r["class"] = "FALSE-REFUSE" if r["arp_disposition"] == "REFUSE" else "OK"
        elif r["arp_disposition"] == "REFUSE":
            r["class"] = "SEEN"
        elif tuple(r["observable"]) in valid_sigs:
            r["class"] = "BENEATH"
        else:
            r["class"] = "HELD"

    neg = [r for r in rows if not r["expected_valid"]]
    pos = [r for r in rows if r["expected_valid"]]
    by = lambda c: [r["vector"] for r in neg if r["class"] == c]

    print("=" * 100)
    print("LAYERING RESULT")
    print("=" * 100)
    print(f"  valid packages   : {len(pos)}   falsely refused: "
          f"{sum(1 for r in pos if r['class'] == 'FALSE-REFUSE')}")
    print(f"  invalid packages : {len(neg)}")
    for c in ("SEEN", "HELD", "BENEATH"):
        print(f"    {c:<8}: {len(by(c))}  {by(c)}")
    print()
    print("  Leg information content across the corpus:")
    names = []
    for r in rows:
        for l in r["legs"]:
            if l["source"] not in names:
                names.append(l["source"])
    for n in names:
        vals = {f"{l['verdict']}[{l['axis']}]" for r in rows for l in r["legs"]
                if l["source"] == n}
        mark = "   <- constant, carries no information" if len(vals) == 1 else ""
        print(f"    {n:<22}{len(vals)} distinct value(s){mark}")
    print()
    print("  Signature encodings observed:")
    for p in sorted({r.get("signature_path") for r in rows if r.get("signature_path")}):
        v = [r["vector"] for r in rows if r.get("signature_path") == p]
        print(f"    {p:<22}{len(v)}  {v}")
    nb = [r["vector"] for r in rows if r.get("metadata_signature_bound") is False]
    print(f"\n  metadata.json OUTSIDE the signed surface: {len(nb)} package(s)")
    print(f"    {nb}")

    if a.json:
        json.dump({"rows": rows, "anchors_loaded": len(anchors),
                   "summary": {"valid": len(pos), "invalid": len(neg),
                               "false_refuse": sum(1 for r in pos if r["class"] == "FALSE-REFUSE"),
                               "seen": len(by("SEEN")), "held": len(by("HELD")),
                               "beneath": len(by("BENEATH"))}},
                  open(a.json, "w"), indent=1, sort_keys=True, default=str)
        print(f"\n  machine-readable: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
