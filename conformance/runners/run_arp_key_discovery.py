#!/usr/bin/env python3
"""Independent check of the Sealing-key discovery documents of draft-hillier-scitt-arp.

    python3 runners/run_arp_key_discovery.py EMISSION.json

EMISSION.json is written by the platform pipeline: the signed sealing key set
(/.well-known/arp-sealing-keys), the single-key documents, the signed operator key
set, the issuer JWKS, and a credential sealed under the epoch key. Nothing here
imports the platform. The checks are hand-written over `cbor2` and `cryptography`:

  A  key set      COSE_Sign1 over a deterministic COSE_KeySet, signed by the key-set signer
  B  entries      kid = RFC 7638 thumbprint of x, status and validity on every entry,
                  revoked entries carry a revocation time, order is bytewise by kid
  C  resolution   the credential's kid resolves in the set, the key's status and validity admit
                  the Reconciliation Timestamp, and the credential verifies under it
  D  JOSE         the issuer JWKS names the same key under the same kid
  E  operator     the operator key set is distinct from, and signed apart from, the sealing set

Red team: mutants of the platform's emission, each refused at its designed check.
"""
import base64, datetime, hashlib, json, sys
import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

STATUS, VALIDITY = -65539, -65540


class Refuse(Exception):
    def __init__(self, check): self.check = check


def u(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def ts(z): return datetime.datetime.fromisoformat(z.replace("Z", "+00:00"))


def thumbprint(x_b64):
    return b64u(hashlib.sha256(('{"crv":"Ed25519","kty":"OKP","x":"%s"}' % x_b64).encode()).digest())


def sign1(payload, priv, kid, cty):
    prot = cbor2.dumps({1: -8, 4: kid.encode(), 3: cty})
    sig = priv.sign(cbor2.dumps(["Signature1", prot, b"", payload]))
    return cbor2.dumps(cbor2.CBORTag(18, [prot, {}, payload, sig]))


def open_sign1(doc, x, kid, cty):
    t = cbor2.loads(doc)
    if not (isinstance(t, cbor2.CBORTag) and t.tag == 18): raise Refuse("cose-tag")
    prot, _, payload, sig = t.value
    ph = cbor2.loads(prot)
    if ph.get(1) != -8: raise Refuse("alg")
    if ph.get(3) != cty: raise Refuse("cty")
    if ph.get(4) != kid.encode(): raise Refuse("signer-kid")
    try:
        Ed25519PublicKey.from_public_bytes(u(x)).verify(sig, cbor2.dumps(["Signature1", prot, b"", payload]))
    except InvalidSignature:
        raise Refuse("signature")
    return payload


def check_entries(keys):
    last, seen = None, set()
    for k in keys:
        if k.get(1) != 1 or k.get(-1) != 6 or k.get(3) != -8: raise Refuse("key-type")
        x = b64u(k[-2]); kid = k[2].decode()
        if kid != thumbprint(x): raise Refuse("kid-thumbprint")
        if kid in seen: raise Refuse("duplicate")
        seen.add(kid)
        if last is not None and not (last.encode() < kid.encode()): raise Refuse("order")
        last = kid
        st, val = k.get(STATUS), k.get(VALIDITY)
        if st not in ("active", "retired", "revoked"): raise Refuse("status")
        if not isinstance(val, list) or len(val) not in (2, 3): raise Refuse("validity")
        if (st == "revoked") != (len(val) == 3): raise Refuse("revocation-time")
        if not ts(val[0]) < ts(val[1]): raise Refuse("validity")
    return {k[2].decode(): k for k in keys}


def admits(entry, at):
    st, val = entry[STATUS], entry[VALIDITY]
    if st == "revoked": return at < ts(val[2])      # a revoked key admits only Outputs sealed before its revocation time
    return ts(val[0]) <= at < ts(val[1])


def kset(em, doc=None):
    payload = open_sign1(doc or bytes.fromhex(em["sealing_key_set_hex"]), em["key_set_signer"]["x"], em["key_set_signer"]["kid"], "application/cose-key-set")
    keys = cbor2.loads(payload)
    if not isinstance(keys, list): raise Refuse("key-set-shape")
    by = check_entries(keys)
    if em["key_set_signer"]["kid"] not in by: raise Refuse("signer-not-in-set")
    return by


def jws_kid_alg(jws):
    h = json.loads(u(jws.split(".")[0])); return h["kid"], h["alg"]


def resolve(em, by, at=None):
    kid, alg = jws_kid_alg(em["credential_jwt"])
    if alg != "EdDSA" or kid not in by: raise Refuse("kid-unresolved")
    entry = by[kid]
    at = at or ts(em["reconciled_at"])
    if not admits(entry, at): raise Refuse("key-not-admitted")
    h, p, s = em["credential_jwt"].split(".")
    try:
        Ed25519PublicKey.from_public_bytes(entry[-2]).verify(u(s), (h + "." + p).encode("ascii"))
    except InvalidSignature:
        raise Refuse("credential-signature")
    return entry


def jwks_alias(em, entry):
    kid = entry[2].decode()
    hit = [k for k in em["jwks"]["keys"] if k.get("kid") == kid]
    if not hit or hit[0]["x"] != b64u(entry[-2]) or hit[0]["crv"] != "Ed25519": raise Refuse("jwks-alias")


def single(em, kid, by):
    doc = bytes.fromhex(em["sealing_key_hex_by_kid"][kid])
    key = cbor2.loads(open_sign1(doc, em["key_set_signer"]["x"], em["key_set_signer"]["kid"], "application/cose-key"))
    if key != by[kid]: raise Refuse("single-differs")


def operator(em, by):
    op = em["operator_signer"]
    if op["kid"] == em["key_set_signer"]["kid"]: raise Refuse("operator-not-distinct")
    keys = cbor2.loads(open_sign1(bytes.fromhex(em["operator_key_set_hex"]), op["x"], op["kid"], "application/cose-key-set"))
    ob = check_entries(keys)
    if set(ob) & set(by): raise Refuse("operator-overlap")


def full(em):
    by = kset(em)
    entry = resolve(em, by)
    jwks_alias(em, entry)
    single(em, entry[2].decode(), by)
    operator(em, by)
    return "accept"


def main():
    em = json.load(open(sys.argv[1]))
    rows, fails = [], 0
    ksk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(em["key_set_signer"]["raw_hex"]))
    ks_kid = em["key_set_signer"]["kid"]
    def case(name, expect, fn):
        nonlocal fails
        try: got = (fn(), None)
        except Refuse as r: got = ("refuse", r.check)
        ok = (expect == "accept" and got[0] == "accept") or (expect != "accept" and got == ("refuse", expect))
        fails += 0 if ok else 1
        print("%s %-40s expect=%-20s got=%s" % ("OK  " if ok else "FAIL", name, expect, got)); rows.append([name, expect, list(got), ok])
    base = bytes.fromhex(em["sealing_key_set_hex"])
    keys = cbor2.loads(cbor2.loads(base).value[2])
    by0 = {k[2].decode(): k for k in keys}
    cred_kid, _ = jws_kid_alg(em["credential_jwt"])

    def resign(edit):
        ks = [dict(k) for k in keys]; ks = edit(ks)
        return sign1(cbor2.dumps(ks), ksk, ks_kid, "application/cose-key-set")

    case("sealing set, credential, JWKS, single, operator", "accept", lambda: full(em))
    def flip():
        t = cbor2.loads(base); p = bytearray(t.value[2]); p[-1] ^= 1
        return cbor2.dumps(cbor2.CBORTag(18, [t.value[0], {}, bytes(p), t.value[3]]))
    case("key set payload altered", "signature", lambda: kset(em, flip()))
    other = Ed25519PrivateKey.generate()
    case("key set signed by another key", "signature", lambda: kset(em, sign1(cbor2.dumps(keys), other, ks_kid, "application/cose-key-set")))
    case("key set names another signer", "signer-kid", lambda: kset(em, sign1(cbor2.dumps(keys), ksk, "x" + ks_kid[1:], "application/cose-key-set")))
    case("key set content type wrong", "cty", lambda: kset(em, sign1(cbor2.dumps(keys), ksk, ks_kid, "application/cose-key")))
    def drop_status(ks): ks[0].pop(STATUS); return ks
    case("entry without arp-key-status", "status", lambda: kset(em, resign(drop_status)))
    def drop_validity(ks): ks[0].pop(VALIDITY); return ks
    case("entry without arp-key-validity", "validity", lambda: kset(em, resign(drop_validity)))
    def revoked_no_time(ks): ks[0][STATUS] = "revoked"; return ks
    case("revoked entry without revocation time", "revocation-time", lambda: kset(em, resign(revoked_no_time)))
    def time_not_revoked(ks): ks[0][VALIDITY] = ks[0][VALIDITY][:2] + ["2026-10-20T00:00:00Z"]; return ks
    case("revocation time on a live entry", "revocation-time", lambda: kset(em, resign(time_not_revoked)))
    def bad_kid(ks): ks[0][2] = b"A" * 43; return ks
    case("kid is not the thumbprint of x", "kid-thumbprint", lambda: kset(em, resign(bad_kid)))
    case("entries out of order", "order", lambda: kset(em, resign(lambda ks: list(reversed(ks)))))
    case("duplicate entry", "duplicate", lambda: kset(em, resign(lambda ks: ks + [ks[0]])))
    case("key-set signer absent from the set", "signer-not-in-set", lambda: kset(em, resign(lambda ks: [k for k in ks if k[2].decode() != ks_kid])))
    def drop_credential_key(ks): return [k for k in ks if k[2].decode() != cred_kid]
    case("credential key removed from the set", "kid-unresolved", lambda: resolve(em, kset(em, resign(drop_credential_key))))
    def revoke_before(ks):
        for k in ks:
            if k[2].decode() == cred_kid: k[STATUS] = "revoked"; k[VALIDITY] = k[VALIDITY][:2] + ["2020-01-01T00:00:00Z"]
        return ks
    case("key revoked before the Output was sealed", "key-not-admitted", lambda: resolve(em, kset(em, resign(revoke_before))))
    def revoke_after(ks):
        for k in ks:
            if k[2].decode() == cred_kid: k[STATUS] = "revoked"; k[VALIDITY] = k[VALIDITY][:2] + ["2099-01-01T00:00:00Z"]
        return ks
    case("key revoked after the Output was sealed", "accept", lambda: (resolve(em, kset(em, resign(revoke_after))), "accept")[1])
    def retire_elsewhere(ks):
        for k in ks:
            if k[2].decode() == cred_kid: k[STATUS] = "retired"; k[VALIDITY] = ["2025-01-01T00:00:00Z", "2025-02-01T00:00:00Z"]
        return ks
    case("retired key, Output outside its interval", "key-not-admitted", lambda: resolve(em, kset(em, resign(retire_elsewhere))))
    case("Output evaluated before the key's interval", "key-not-admitted", lambda: resolve(em, by0, ts("2026-01-01T00:00:00Z")))
    def swap_x(ks):
        for k in ks:
            if k[2].decode() == cred_kid: k[-2] = bytes(32)
        return ks
    case("entry carries a different public key", "kid-thumbprint", lambda: kset(em, resign(swap_x)))
    jwt = em["credential_jwt"]
    def tamper(jws):
        h, p, s = jws.split("."); o = json.loads(u(p)); o["credentialSubject"]["combinedVerdict"] = "match"
        return h + "." + b64u(json.dumps(o, separators=(",", ":")).encode()) + "." + s
    case("credential altered after sealing", "credential-signature", lambda: resolve({**em, "credential_jwt": tamper(jwt)}, by0))
    case("JWKS without the thumbprint kid", "jwks-alias", lambda: jwks_alias({**em, "jwks": {"keys": [k for k in em["jwks"]["keys"] if k["kid"] != cred_kid]}}, by0[cred_kid]))
    case("single-key document differs from the set", "single-differs", lambda: single({**em, "sealing_key_hex_by_kid": {**em["sealing_key_hex_by_kid"], cred_kid: em["sealing_key_hex_by_kid"][ks_kid]}}, cred_kid, by0))
    case("operator set not distinct", "operator-not-distinct", lambda: operator({**em, "operator_signer": em["key_set_signer"]}, by0))
    print("\n%d of %d credited" % (len(rows) - fails, len(rows)))
    json.dump({"rows": rows, "credited": len(rows) - fails, "total": len(rows)}, open("runs/arp_key_discovery_run.json", "w"), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
