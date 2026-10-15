#!/usr/bin/env python3
"""End-to-end conformance of the platform emitter (certisyn-app lib/arp).

    python3 runners/run_platform_emission.py EMISSION.json

EMISSION.json is written by the platform's own pipeline (runArp with the
output04 option): the sealed Reconciliation Output as a COSE_Sign1, and the
credential secured as application/vc+cose. Nothing here imports the platform.

Two independent checks decide each property. The sealed Output is read with
cbor2 and verified by hand-written Ed25519 plus pycose. The credential goes
through verifier A and verifier B of run_vc_vectors.py. The two are then
tied together: the credential must state exactly what the sealed Output
holds, and the Reconciliation Hash recomputed from the Output must equal the
one the credential carries (Section 7.6.3 step 8).

Red team: mutants of the platform's own emission, each signed by the genuine
Sealing key, each of which must be refused at its designed check.
"""
import base64, hashlib, json, os, sys
import cbor2, jcs
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pycose.keys import OKPKey
from pycose.keys.curves import Ed25519
from pycose.messages import Sign1Message
from pycose.headers import Algorithm, KID, ContentType
from pycose.algorithms import EdDSA

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_vc_vectors as R  # noqa: E402

b64u = R.b64u
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "runs", "arp_platform_emission_run.json")
FIELDS = ["eventId", "reconciliationId", "claimHash", "reconciledAt", "relianceHorizon",
          "audience", "combinedVerdict", "arithmetic", "addressed", "braHashes",
          "policyVersionHash", "patternLibraryVersion", "requesterBindingClass",
          "perRegister", "aggregationMethod", "merkleRoot", "divergence", "override",
          "sealingKeyId", "sealingSignature"]


SKIP = set()


class Refuse(Exception):
    def __init__(self, check):
        self.check = check


def parse_cose(raw):
    t = cbor2.loads(raw)
    if not (isinstance(t, cbor2.CBORTag) and t.tag == 18):
        raise Refuse("cose")
    prot_b, unprot, payload, sig = t.value
    return prot_b, cbor2.loads(prot_b), payload, sig


def merkle(leaves):
    # RFC 9162 Section 2.1.1 recursion, independent of the platform's iterative form
    leaves = sorted(set(leaves))
    if not leaves:
        return bytes(32)
    def mth(xs):
        if len(xs) == 1:
            return hashlib.sha256(b"\x00" + xs[0]).digest()
        k = 1
        while k * 2 < len(xs):
            k *= 2
        return hashlib.sha256(b"\x01" + mth(xs[:k]) + mth(xs[k:])).digest()
    return mth(leaves)


def check_output(sealed_raw, x_b64u, origin, kid):
    """Verify the sealed Output; returns (fields dict, reconciliation hash)."""
    prot_b, prot, payload, sig = parse_cose(sealed_raw)
    if prot.get(1) != -8:
        raise Refuse("alg")
    if prot.get(4) != kid.encode():
        raise Refuse("key")
    if -65537 not in prot or -65538 not in prot:
        raise Refuse("headers")
    pub = R.Ed25519PublicKey.from_public_bytes(R.unb64u(x_b64u))
    try:
        pub.verify(sig, R.sig_structure(prot_b, payload))
    except R.InvalidSignature:
        raise Refuse("signature")
    # second implementation of the signature check
    tagged = cbor2.loads(sealed_raw)
    obj = list(tagged.value)
    obj[1] = dict(obj[1])
    try:
        m = Sign1Message.from_cose_obj(obj, True)
    except Exception:
        raise Refuse("cose")
    m.key = OKPKey(crv=Ed25519, x=R.unb64u(x_b64u))
    if not m.verify_signature():
        raise Refuse("signature")
    arr = cbor2.loads(payload)
    if not (isinstance(arr, list) and len(arr) == len(FIELDS)):
        raise Refuse("shape")
    f = dict(zip(FIELDS, arr))
    if f["sealingSignature"] is not None:
        raise Refuse("payload-signature-position")
    if f["sealingKeyId"] != [origin, kid]:
        raise Refuse("sealing-key-id")
    if f["reconciliationId"] != f["claimHash"] + f["policyVersionHash"] + f["eventId"]:
        raise Refuse("reconciliation-id")
    if len(f["eventId"]) != 16 or len(f["merkleRoot"]) != 32:
        raise Refuse("lengths")
    if prot[-65538] != f["policyVersionHash"]:
        raise Refuse("header-binding")
    if prot[-65537] != f["braHashes"]:
        raise Refuse("header-binding")
    if f["braHashes"] != sorted(set(f["braHashes"])):
        raise Refuse("order")
    if f["addressed"] != sorted(f["addressed"], key=lambda s: s.encode()):
        raise Refuse("order")
    if not f["audience"]:
        raise Refuse("audience")
    keys = [cbor2.dumps(a[0]) for a in f["audience"]]
    if keys != sorted(set(keys)):
        raise Refuse("order")
    ids = [e[0] for e in f["perRegister"]]
    if ids != sorted(ids, key=lambda s: s.encode()):
        raise Refuse("order")
    leaves = [hashlib.sha256(e[10][3]).digest() for e in f["perRegister"] if e[10]]
    if "merkle" not in SKIP and merkle(leaves) != f["merkleRoot"]:
        raise Refuse("merkle")
    # Reconciliation Hash: the array with positions 18 and 19 null, length unchanged
    pre = list(arr); pre[18] = None; pre[19] = None
    return f, hashlib.sha256(cbor2.dumps(pre, canonical=True)).digest()


def tie(cred, f, rh, sealed_raw):
    """Step 8 and the consistency of credential with Output."""
    s = cred["credentialSubject"]
    exp = {
        "reconciliationHash": b64u(rh),
        "claimHash": b64u(f["claimHash"]),
        "policyVersionHash": b64u(f["policyVersionHash"]),
        "combinedVerdict": f["combinedVerdict"],
        "requesterBindingClass": f["requesterBindingClass"],
        "addressedRegisters": f["addressed"],
        "bilateralRegisterAgreementHashes": [b64u(h) for h in f["braHashes"]],
        "reconciliationTimestamp": f["reconciledAt"],
        "relianceHorizon": f["relianceHorizon"],
        "audienceSet": [{"id": a[0], "verificationMethod": b64u(a[1])} for a in f["audience"]],
    }
    for k, v in exp.items():
        if k in SKIP:
            continue
        if s.get(k) != v:
            raise Refuse("tie:" + k)
    if cred["issuer"] != f["sealingKeyId"][0]:
        raise Refuse("tie:issuer")
    if s["sealedOutput"]["digest"] != b64u(hashlib.sha256(sealed_raw).digest()):
        raise Refuse("tie:digest")


def evaluate(em, cred_raw, sealed_raw, at):
    doc = {"test_key": {"x": em["x"], "kid": em["kid"], "origin": em["origin"]}}
    a = R.verify_A(cred_raw, doc, sealed_raw, at)
    b = R.verify_B(cred_raw, doc, sealed_raw, at)
    if a != b:
        return ("reject", "verifiers-disagree:%s/%s" % (a, b))
    if a[0] == "reject":
        return a
    try:
        f, rh = check_output(sealed_raw, em["x"], em["origin"], em["kid"])
        prot_b, prot, payload, sig = R.parse_sign1(cred_raw)
        tie(json.loads(payload), f, rh, sealed_raw)
    except Refuse as r:
        return ("reject", r.check)
    return a


def resign(em, cred, **kw):
    """Credential changes signed by the genuine Sealing key."""
    priv = serialization.load_pem_private_key(em["private_pem"].encode(), None)
    seed = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                              serialization.NoEncryption())
    pubraw = R.unb64u(em["x"])
    m = Sign1Message(phdr={Algorithm: EdDSA, KID: em["kid"].encode(), 16: R.TYP,
                           ContentType: R.CTYPE}, payload=jcs.canonicalize(cred))
    m.key = OKPKey(crv=Ed25519, d=seed, x=pubraw)
    return m.encode(tag=True), priv


def reseal(em, priv, mutate):
    """A sealed Output altered and re-signed by the genuine Sealing key."""
    prot_b, prot, payload, sig = parse_cose(bytes.fromhex(em["sealed_hex"]))
    arr = cbor2.loads(payload)
    mutate(arr)
    seed = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                              serialization.NoEncryption())
    # hand-built COSE_Sign1 over the unchanged protected header bytes
    new_payload = cbor2.dumps(arr, canonical=True)
    sig = priv.sign(R.sig_structure(prot_b, new_payload))
    return cbor2.dumps(cbor2.CBORTag(18, [prot_b, {}, new_payload, sig]), canonical=True)


def main():
    em = json.load(open(sys.argv[1]))
    sealed = bytes.fromhex(em["sealed_hex"])
    cred_raw = bytes.fromhex(em["credential_hex"])
    t_ok = R.parse_ts(em["reconciled_at"]) 
    at = t_ok + __import__("datetime").timedelta(hours=1)
    stale_at = R.parse_ts(em["horizon"]) + __import__("datetime").timedelta(hours=1)
    prot_b, prot, payload, sig = R.parse_sign1(cred_raw)
    cred = json.loads(payload)
    rows = []

    def row(name, want, got):
        ok = got[0] == want[0] and (want[1] is None or got[1] == want[1])
        rows.append({"id": name, "expect": list(want), "got": list(got), "credited": ok})
        print("%s %-34s want=%-26s got=%s" % ("OK  " if ok else "FAIL", name, want, got))

    row("P01 platform emission accepted", ("accept", None), evaluate(em, cred_raw, sealed, at))
    row("P02 after the Reliance Horizon", ("stale", None), evaluate(em, cred_raw, sealed, stale_at))

    # sealed Output tampered after signing
    t = bytearray(sealed); t[len(t) // 2] ^= 1
    row("P03 sealed Output byte altered", ("reject", None), evaluate(em, cred_raw, bytes(t), at))

    # other sealed Output offered for this credential
    other = bytearray(sealed); other[-1] ^= 1
    row("P04 different sealed Output offered", ("reject", None), evaluate(em, cred_raw, bytes(other), at))

    c = json.loads(json.dumps(cred)); c["credentialSubject"]["combinedVerdict"] = "match"
    raw, priv = resign(em, c)
    row("P05 verdict changed, genuine re-sign", ("reject", "tie:combinedVerdict"), evaluate(em, raw, sealed, at))

    c = json.loads(json.dumps(cred))
    c["validUntil"] = c["credentialSubject"]["relianceHorizon"] = "2027-10-15T18:00:00Z"
    raw, _ = resign(em, c)
    row("P06 horizon extended, genuine re-sign", ("reject", "tie:relianceHorizon"), evaluate(em, raw, sealed, at))

    c = json.loads(json.dumps(cred))
    c["credentialSubject"]["audienceSet"][0]["id"] = "https://evil.example/ops/x"
    raw, _ = resign(em, c)
    row("P07 audience swapped, genuine re-sign", ("reject", "tie:audienceSet"), evaluate(em, raw, sealed, at))

    c = json.loads(json.dumps(cred))
    c["credentialSubject"]["requesterBindingClass"] = "principal-verified"
    raw, _ = resign(em, c)
    row("P08 binding class raised, re-sign", ("reject", "tie:requesterBindingClass"), evaluate(em, raw, sealed, at))

    # Output altered and re-sealed by the genuine key: credential digest no longer binds
    s2 = reseal(em, priv, lambda a: a.__setitem__(6, "match"))
    row("P09 Output verdict altered, resealed", ("reject", "binding"), evaluate(em, cred_raw, s2, at))

    # Output re-sealed and credential rebuilt to match digest but hash not recomputed
    def m_aud(a): a[5] = [[a[5][0][0] + "x", a[5][0][1]]]
    s3 = reseal(em, priv, m_aud)
    c = json.loads(json.dumps(cred)); c["credentialSubject"]["sealedOutput"]["digest"] = b64u(hashlib.sha256(s3).digest())
    raw, _ = resign(em, c)
    row("P10 digest rebound, hash not recomputed", ("reject", "tie:reconciliationHash"), evaluate(em, raw, s3, at))

    # merkle root forged and resealed
    s4 = reseal(em, priv, lambda a: a.__setitem__(15, bytes(32)))
    c = json.loads(json.dumps(cred)); c["credentialSubject"]["sealedOutput"]["digest"] = b64u(hashlib.sha256(s4).digest())
    raw, _ = resign(em, c)
    row("P11 Merkle root forged, resealed", ("reject", "merkle"), evaluate(em, raw, s4, at))

    # empty audience in Output
    s5 = reseal(em, priv, lambda a: a.__setitem__(5, []))
    c = json.loads(json.dumps(cred)); c["credentialSubject"]["sealedOutput"]["digest"] = b64u(hashlib.sha256(s5).digest())
    raw, _ = resign(em, c)
    row("P12 Audience Set emptied, resealed", ("reject", "audience"), evaluate(em, raw, s5, at))

    # mutant verifiers: each check removed must admit its designed mutant
    controls = {}
    c0 = json.loads(json.dumps(cred))
    for chk, mutate in (
        ("combinedVerdict", lambda c: c["credentialSubject"].__setitem__("combinedVerdict", "match")),
        ("relianceHorizon", lambda c: (c.__setitem__("validUntil", "2027-10-15T18:00:00Z"),
                                       c["credentialSubject"].__setitem__("relianceHorizon", "2027-10-15T18:00:00Z"))),
        ("audienceSet", lambda c: c["credentialSubject"]["audienceSet"][0].__setitem__("id", "https://evil.example/ops/x")),
        ("requesterBindingClass", lambda c: c["credentialSubject"].__setitem__("requesterBindingClass", "principal-verified")),
    ):
        c = json.loads(json.dumps(cred)); mutate(c)
        rawm, _ = resign(em, c)
        SKIP.add(chk)
        controls[chk] = evaluate(em, rawm, sealed, at)[0] == "accept"
        SKIP.discard(chk)
    s4b = reseal(em, priv, lambda a: a.__setitem__(15, bytes(32)))
    SKIP.add("merkle")
    _, rh4 = check_output(s4b, em["x"], em["origin"], em["kid"])
    c = json.loads(json.dumps(cred))
    c["credentialSubject"]["sealedOutput"]["digest"] = b64u(hashlib.sha256(s4b).digest())
    c["credentialSubject"]["reconciliationHash"] = b64u(rh4)
    c["id"] = "urn:arp:reconciliation:" + b64u(rh4)
    raw4, _ = resign(em, c)
    controls["merkle"] = evaluate(em, raw4, s4b, at)[0] == "accept"
    SKIP.discard("merkle")
    for k, v in controls.items():
        rows.append({"id": "control:" + k, "expect": ["mutant admits"], "got": [v], "credited": bool(v)})
        print("%s control %-22s mutant verifier admits its mutant: %s" % ("OK  " if v else "FAIL", k, v))
    bad = sum(1 for r in rows if not r["credited"])
    json.dump({"emission_sha256": hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest(),
               "rows": rows, "credited": len(rows) - bad},
              open(RUN, "w", newline="\n"), indent=1)
    print("\n%d of %d credited" % (len(rows) - bad, len(rows)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
