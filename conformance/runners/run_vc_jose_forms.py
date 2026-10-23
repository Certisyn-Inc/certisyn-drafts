#!/usr/bin/env python3
"""Independent check of the JOSE securing forms of the Section 7.6 credential.

    python3 runners/run_vc_jose_forms.py EMISSION.json

EMISSION.json is written by the platform pipeline (credential_jwt, credential_sd_jwt,
credential_hex, the Sealing key's x and kid, and origin). Nothing here imports the
platform. The checks are hand-written over `cryptography`, `cbor2` and `jcs`:

  A  vc+jwt        compact JWS, typ vc+jwt, cty vc, EdDSA, RFC 8785 payload
  B  dc+sd-jwt     issuer JWT, salted-hash digests, disclosures rebuild the subject
  C  one statement the four forms (vc+cose, vc+jwt, SD-JWT VC, mdoc) state the same credential
  D  key binding   holder-signed kb+jwt over a presentation: signature under cnf.jwk,
                   audience, nonce, freshness, sd_hash over the presented bytes
  E  mdoc          ISO/IEC 18013-5 IssuerSigned: issuerAuth COSE_Sign1 under the Sealing key,
                   Mobile Security Object digests of every IssuerSignedItem, docType, validity,
                   device key equal to the SD-JWT holder key

Red team: mutants of the platform's own emission, each of which must be refused at
its designed check.
"""
import base64, hashlib, json, sys
import cbor2, jcs
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding, PublicFormat
import datetime

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


# ---------------------------------------------------------------------------
# D  key binding
# ---------------------------------------------------------------------------
def holder_priv(em): return load_pem_private_key(em["holder_private_pem"].encode(), None)
def holder_x(em): return b64u(holder_priv(em).public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def jws_sign(priv, header, payload):
    hh = b64u(json.dumps(header, separators=(",", ":")).encode())
    pp = b64u(json.dumps(payload, separators=(",", ":")).encode())
    return hh + "." + pp + "." + b64u(priv.sign((hh + "." + pp).encode("ascii")))


def subset(compact, names):
    parts = compact.split("~")
    ds = [d for d in parts[1:-1] if json.loads(u(d))[1] in names]
    return parts[0] + "~" + ("~".join(ds) + "~" if ds else "")


def present(em, names, aud, nonce, iat, priv=None):
    pres = subset(em["credential_sd_jwt"], names)
    kb = jws_sign(priv or holder_priv(em), {"alg": "EdDSA", "typ": "kb+jwt"},
                  {"iat": iat, "aud": aud, "nonce": nonce, "sd_hash": b64u(hashlib.sha256(pres.encode("ascii")).digest())})
    return pres + kb


def check_presentation(pres, em, aud, nonce, now, max_age=300):
    parts = pres.split("~")
    if len(parts) < 2: raise Refuse("sd-shape")
    kb, ds, jwt = parts[-1], parts[1:-1], parts[0]
    _, pl = verify_jws(jwt, em["x"], em["kid"], "dc+sd-jwt")
    if now >= pl["exp"]: raise Refuse("expired")
    if now < pl["nbf"]: raise Refuse("not-yet-valid")
    seen = set()
    for d in ds:
        dig = b64u(hashlib.sha256(d.encode("ascii")).digest())
        if dig not in pl["_sd"] or dig in seen: raise Refuse("disclosure-digest")
        seen.add(dig)
    if "cnf" not in pl: raise Refuse("cnf")
    if kb == "": raise Refuse("key-binding-missing")
    try:
        kh, kp, ks = kb.split(".")
        hdr = json.loads(u(kh))
        if hdr.get("alg") != "EdDSA" or hdr.get("typ") != "kb+jwt": raise Refuse("kb-header")
        Ed25519PublicKey.from_public_bytes(u(pl["cnf"]["jwk"]["x"])).verify(u(ks), (kh + "." + kp).encode("ascii"))
    except InvalidSignature:
        raise Refuse("kb-signature")
    k = json.loads(u(kp))
    if k.get("aud") != aud: raise Refuse("kb-aud")
    if k.get("nonce") != nonce: raise Refuse("kb-nonce")
    if abs(now - k.get("iat", -10**12)) > max_age: raise Refuse("kb-stale")
    covered = pres[:len(pres) - len(kb)]
    if k.get("sd_hash") != b64u(hashlib.sha256(covered.encode("ascii")).digest()): raise Refuse("kb-sd-hash")
    return pl, ds


# ---------------------------------------------------------------------------
# E  mdoc
# ---------------------------------------------------------------------------
DOCTYPE = "com.certisyn.arp.reconciliation.1"


def mdoc_check(b64, em, cred, at, holder_key_x):
    iss = cbor2.loads(u(b64))
    if not isinstance(iss, dict) or set(iss) != {"nameSpaces", "issuerAuth"}: raise Refuse("mdoc-shape")
    prot, unprot, payload, sig = iss["issuerAuth"]
    ph = cbor2.loads(prot)
    if ph.get(1) != -8: raise Refuse("alg")
    if ph.get(4) != em["kid"].encode(): raise Refuse("kid")
    try:
        Ed25519PublicKey.from_public_bytes(u(em["x"])).verify(sig, cbor2.dumps(["Signature1", prot, b"", payload]))
    except InvalidSignature:
        raise Refuse("signature")
    t = cbor2.loads(payload)
    if not (isinstance(t, cbor2.CBORTag) and t.tag == 24): raise Refuse("mso-tag")
    mso = cbor2.loads(t.value)
    if mso.get("version") != "1.0" or mso.get("digestAlgorithm") != "SHA-256": raise Refuse("mso-version")
    if mso.get("docType") != DOCTYPE: raise Refuse("doctype")
    vi = mso["validityInfo"]
    at_dt = datetime.datetime.fromtimestamp(at, datetime.timezone.utc)
    if not (vi["validFrom"] <= at_dt < vi["validUntil"]): raise Refuse("validity")
    dk = mso["deviceKeyInfo"]["deviceKey"]
    if dk.get(1) != 1 or dk.get(-1) != 6 or dk.get(-2) != u(holder_key_x): raise Refuse("device-key")
    items = iss["nameSpaces"].get(DOCTYPE, [])
    digests = mso["valueDigests"].get(DOCTYPE, {})
    subj, ids = {}, set()
    for it in items:
        if not (isinstance(it, cbor2.CBORTag) and it.tag == 24): raise Refuse("item-tag")
        item = cbor2.loads(it.value)
        did = item["digestID"]
        if did in ids: raise Refuse("digest-id-repeat")
        ids.add(did)
        if digests.get(did) != hashlib.sha256(cbor2.dumps(it)).digest(): raise Refuse("digest")
        subj[item["elementIdentifier"]] = item["elementValue"]
    if ids != set(digests): raise Refuse("digest-unmatched")
    if subj != cred["credentialSubject"]: raise Refuse("mdoc-subject")
    return "accept"


def mdoc_resign(b64, em, edit_mso=None, edit_items=None):
    """Rebuild an IssuerSigned with the platform Sealing key after an edit, so each mutant reaches its designed check."""
    priv = load_pem_private_key(em["private_pem"].encode(), None)
    iss = cbor2.loads(u(b64))
    prot, unprot, payload, _ = iss["issuerAuth"]
    mso = cbor2.loads(cbor2.loads(payload).value)
    if edit_items: edit_items(iss, mso)
    if edit_mso: edit_mso(mso)
    payload = cbor2.dumps(cbor2.CBORTag(24, cbor2.dumps(mso)))
    sig = priv.sign(cbor2.dumps(["Signature1", prot, b"", payload]))
    iss["issuerAuth"] = [prot, unprot, payload, sig]
    return b64u(cbor2.dumps(iss))


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

    # --- D key binding
    cred = check_vc_jwt(em["credential_jwt"], em)
    now = int(datetime.datetime.fromisoformat(cred["validFrom"].replace("Z", "+00:00")).timestamp()) + 60
    AUD, NON = "https://verifier.example", "n-0001"
    good = present(em, {"claimHash"}, AUD, NON, now)
    case("key binding presentation", "accept", lambda: (check_presentation(good, em, AUD, NON, now), "accept")[1])
    case("key binding wrong audience", "kb-aud", lambda: check_presentation(good, em, "https://other.example", NON, now))
    case("key binding wrong nonce", "kb-nonce", lambda: check_presentation(good, em, AUD, "n-0002", now))
    case("key binding stale", "kb-stale", lambda: check_presentation(good, em, AUD, NON, now + 3600))
    case("key binding missing", "key-binding-missing", lambda: check_presentation(subset(em["credential_sd_jwt"], {"claimHash"}), em, AUD, NON, now))
    case("key binding other holder key", "kb-signature", lambda: check_presentation(
        present(em, {"claimHash"}, AUD, NON, now, priv=Ed25519PrivateKey.generate()), em, AUD, NON, now))
    def widen():
        kb = good[good.rfind("~") + 1:]
        full = em["credential_sd_jwt"].split("~")
        return full[0] + "~" + "~".join(full[1:-1]) + "~" + kb
    case("key binding presentation widened", "kb-sd-hash", lambda: check_presentation(widen(), em, AUD, NON, now))
    case("key binding issuer payload altered", "signature", lambda: check_presentation(
        tamper_payload(good.split("~")[0]) + "~" + "~".join(good.split("~")[1:]), em, AUD, NON, now))
    case("key binding expired credential", "expired", lambda: check_presentation(good, em, AUD, NON, now + 10**6, max_age=10**9))
    # --- E mdoc
    hx = holder_x(em)
    mdoc = em["credential_mdoc"]
    def forms_equal():
        pl, ds = check_sd_core(em["credential_sd_jwt"], em)
        if pl["cnf"]["jwk"]["x"] != hx: raise Refuse("cnf-holder")
        return mdoc_check(mdoc, em, cred, now, pl["cnf"]["jwk"]["x"])
    case("mdoc, four forms one credential", "accept", forms_equal)
    def flip_payload(b):
        iss = cbor2.loads(u(b)); p = bytearray(iss["issuerAuth"][2]); p[-1] ^= 1
        iss["issuerAuth"][2] = bytes(p); return b64u(cbor2.dumps(iss))
    case("mdoc MSO altered", "signature", lambda: mdoc_check(flip_payload(mdoc), em, cred, now, hx))
    def alter_item(iss, mso):
        items = iss["nameSpaces"][DOCTYPE]; i = next(i for i, t in enumerate(items) if cbor2.loads(t.value)["elementIdentifier"] == "combinedVerdict")
        it = cbor2.loads(items[i].value); it["elementValue"] = "match"; items[i] = cbor2.CBORTag(24, cbor2.dumps(it))
    case("mdoc element altered", "digest", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_items=alter_item), em, cred, now, hx))
    def drop_digest(mso): mso["valueDigests"][DOCTYPE].pop(0)
    case("mdoc digest removed", "digest", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_mso=drop_digest), em, cred, now, hx))
    def extra_digest(mso): mso["valueDigests"][DOCTYPE][99] = b"\x00" * 32
    case("mdoc digest without item", "digest-unmatched", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_mso=extra_digest), em, cred, now, hx))
    def doctype(mso): mso["docType"] = "org.example.other.1"
    case("mdoc docType swapped", "doctype", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_mso=doctype), em, cred, now, hx))
    def expired(mso): mso["validityInfo"]["validUntil"] = mso["validityInfo"]["validFrom"] + datetime.timedelta(seconds=30)
    case("mdoc validity elapsed", "validity", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_mso=expired), em, cred, now, hx))
    def other_dk(mso): mso["deviceKeyInfo"]["deviceKey"][-2] = bytes(32)
    case("mdoc device key swapped", "device-key", lambda: mdoc_check(mdoc_resign(mdoc, em, edit_mso=other_dk), em, cred, now, hx))
    case("mdoc wrong Sealing key", "signature", lambda: mdoc_check(mdoc, {**em, "x": b64u(bytes(32))}, cred, now, hx))
    case("mdoc kid swapped", "kid", lambda: mdoc_check(mdoc, {**em, "kid": ("y" if em["kid"][0] == "x" else "x") + em["kid"][1:]}, cred, now, hx))
    print("\n%d of %d credited" % (len(rows) - fails, len(rows)))
    json.dump({"rows": rows, "credited": len(rows) - fails, "total": len(rows)}, open("runs/arp_vc_jose_forms_run.json", "w"), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
