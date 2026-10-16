#!/usr/bin/env python3
"""Independent check of the JOSE securing forms of the Section 7.6 credential.

    python3 runners/run_vc_jose_forms.py EMISSION.json

EMISSION.json is written by the platform pipeline (credential_jwt, credential_sd_jwt,
credential_hex, the Sealing key's x and kid, and origin). Nothing here imports the
platform. The checks are hand-written over `cryptography`, `cbor2` and `jcs`:

  A  vc+jwt        compact JWS, typ vc+jwt, cty vc, EdDSA, RFC 8785 payload
  B  dc+sd-jwt     issuer JWT, salted-hash digests, disclosures rebuild the subject
  C  one statement the three forms (vc+cose, vc+jwt, SD-JWT VC) state the same credential

Red team: mutants of the platform's own emission, each of which must be refused at
its designed check.
"""
import base64, hashlib, json, sys
import cbor2, jcs
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SUBJECT_CLEAR = {"reconciliationHash", "combinedVerdict", "reconciliationTimestamp", "relianceHorizon"}
SUBJECT_SD = {"claimHash", "policyVersionHash", "requesterBindingClass", "addressedRegisters",
              "bilateralRegisterAgreementHashes", "audienceSet", "sealedOutput"}


class Refuse(Exception):
    def __init__(self, check): self.check = check


def u(s):
    if not s or "=" in s or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in s):
        raise Refuse("base64url")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def jws_parts(jws):
    p = jws.split(".")
    if len(p) != 3: raise Refuse("jws-shape")
    return p


def verify_jws(jws, x, kid, typ, cty=None):
    h, p, s = jws_parts(jws)
    header = json.loads(u(h))
    if header.get("alg") != "EdDSA": raise Refuse("alg")
    if header.get("typ") != typ: raise Refuse("typ")
    if cty is not None and header.get("cty") != cty: raise Refuse("cty")
    if header.get("kid") != kid: raise Refuse("kid")
    if set(header) - {"alg", "kid", "typ", "cty"}: raise Refuse("header-members")
    try:
        Ed25519PublicKey.from_public_bytes(u(x)).verify(u(s), (h + "." + p).encode("ascii"))
    except InvalidSignature:
        raise Refuse("signature")
    payload_b = u(p)
    obj = json.loads(payload_b)
    if jcs.canonicalize(obj) != payload_b: raise Refuse("jcs")
    return header, obj


def check_vc_jwt(jws, em):
    _, cred = verify_jws(jws, em["x"], em["kid"], "vc+jwt", "vc")
    if cred.get("issuer") != em["origin"]: raise Refuse("issuer")
    if cred.get("id") != "urn:arp:reconciliation:" + cred["credentialSubject"]["reconciliationHash"]: raise Refuse("id")
    return cred


def parse_sd(compact):
    parts = compact.split("~")
    if len(parts) < 2 or parts[-1] != "": raise Refuse("sd-shape")      # no key-binding JWT in this form
    return parts[0], parts[1:-1]


def check_sd_jwt(compact, em):
    jwt, ds = parse_sd(compact)
    header, pl = verify_jws(jwt, em["x"], em["kid"], "dc+sd-jwt")  # SD-JWT payloads are not JCS-bound
    return header, pl, ds


def rebuild(pl, ds):
    if pl.get("_sd_alg") != "sha-256": raise Refuse("sd-alg")
    want = set(pl["_sd"]); seen = set(); out = {k: pl[k] for k in SUBJECT_CLEAR}
    if sorted(pl["_sd"]) != pl["_sd"]: raise Refuse("sd-order")
    for d in ds:
        dig = b64u(hashlib.sha256(d.encode("ascii")).digest())
        if dig not in want or dig in seen: raise Refuse("disclosure-digest")
        seen.add(dig)
        salt, name, value = json.loads(u(d))
        if name in out or name not in SUBJECT_SD: raise Refuse("disclosure-name")
        out[name] = value
    return out


def check_sd_core(compact, em):
    header, pl, ds = check_sd_jwt(compact, em)
    if pl.get("iss") != em["origin"]: raise Refuse("issuer")
    if pl.get("vct", "").rsplit("#", 1)[-1] != "reconciliation-output": raise Refuse("vct")
    if not (pl["nbf"] == pl["iat"] < pl["exp"]): raise Refuse("window")
    return pl, ds


def full(em):
    cose = cbor2.loads(bytes.fromhex(em["credential_hex"]))
    cose_cred = json.loads(cose.value[2])
    jwt_cred = check_vc_jwt(em["credential_jwt"], em)
    pl, ds = check_sd_core(em["credential_sd_jwt"], em)
    subj = rebuild(pl, ds)
    if subj != jwt_cred["credentialSubject"]: raise Refuse("sd-subject")
    if cose_cred != jwt_cred: raise Refuse("forms-differ")
    if pl["jti"] != jwt_cred["id"]: raise Refuse("sd-id")
    return "accept"


def mutate(em, form, fn):
    m = dict(em); m[form] = fn(m[form]); return m


def tamper_payload(jws):
    h, p, s = jws.split("."); o = json.loads(u(p)); o["combinedVerdict"] = "match"
    return h + "." + b64u(jcs.canonicalize(o)) + "." + s


def main():
    em = json.load(open(sys.argv[1]))
    rows, fails = [], 0
    def case(name, expect, fn):
        nonlocal fails
        try: got = (fn(), None)
        except Refuse as r: got = ("refuse", r.check)
        ok = (expect == "accept" and got[0] == "accept") or (expect != "accept" and got == ("refuse", expect))
        fails += 0 if ok else 1
        print("%s %-34s expect=%-18s got=%s" % ("OK  " if ok else "FAIL", name, expect, got)); rows.append([name, expect, list(got), ok])
    case("three forms, one credential", "accept", lambda: full(em))
    case("vc+jwt payload altered", "signature", lambda: full(mutate(em, "credential_jwt", tamper_payload)))
    case("vc+jwt typ vc+cose", "typ", lambda: check_vc_jwt(em["credential_jwt"].replace(em["credential_jwt"].split(".")[0], b64u(json.dumps({"alg":"EdDSA","kid":em["kid"],"typ":"JWT","cty":"vc"}).encode())), em))
    case("vc+jwt alg none", "alg", lambda: check_vc_jwt(b64u(b'{"alg":"none","kid":"x","typ":"vc+jwt","cty":"vc"}') + "." + em["credential_jwt"].split(".",1)[1], em))
    case("vc+jwt wrong key", "signature", lambda: check_vc_jwt(em["credential_jwt"], {**em, "x": b64u(bytes(32))}))
    def sd_swap(c):
        jwt, ds = parse_sd(c); i = ds.index(next(d for d in ds if json.loads(u(d))[1] == "claimHash"))
        forged = b64u(json.dumps([json.loads(u(ds[i]))[0], "claimHash", "AAAA"]).encode()); ds[i] = forged
        return jwt + "~" + "~".join(ds) + "~"
    case("sd-jwt disclosure altered", "disclosure-digest", lambda: full(mutate(em, "credential_sd_jwt", sd_swap)))
    def sd_dup(c):
        jwt, ds = parse_sd(c); return jwt + "~" + "~".join(ds + [ds[0]]) + "~"
    case("sd-jwt disclosure repeated", "disclosure-digest", lambda: full(mutate(em, "credential_sd_jwt", sd_dup)))
    def sd_clear_name(c):
        jwt, ds = parse_sd(c); extra = b64u(json.dumps(["s", "combinedVerdict", "match"]).encode())
        return jwt + "~" + "~".join(ds + [extra]) + "~"
    case("sd-jwt disclosure not in _sd", "disclosure-digest", lambda: full(mutate(em, "credential_sd_jwt", sd_clear_name)))
    case("sd-jwt payload altered", "signature", lambda: full(mutate(em, "credential_sd_jwt", lambda c: tamper_payload(c.split("~")[0]) + "~" + "~".join(c.split("~")[1:]))))
    case("sd-jwt key-binding suffix", "sd-shape", lambda: full(mutate(em, "credential_sd_jwt", lambda c: c + "x.y.z")))
    case("sd-jwt subset presentation", "accept", lambda: (lambda pl_ds: rebuild(*pl_ds) and "accept")((lambda c: (check_sd_core(c, em)[0], [d for d in parse_sd(c)[1] if json.loads(u(d))[1] == "claimHash"]))(em["credential_sd_jwt"])))
    print("\n%d of %d credited" % (len(rows) - fails, len(rows)))
    json.dump({"rows": rows, "credited": len(rows) - fails, "total": len(rows)}, open("runs/arp_vc_jose_forms_run.json", "w"), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
