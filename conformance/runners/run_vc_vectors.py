#!/usr/bin/env python3
"""Verifies the ARP Verifiable Credentials profile (Section 7.6) against
vectors/arp-vc-profile-v0.1.json.

    python3 runners/run_vc_vectors.py                # no arguments

Two independent verifiers decide every vector and must agree:

  A. a hand-written COSE_Sign1 parser and RFC 8785 serialiser in this file,
     using `cryptography` for Ed25519 and SHA-256 only;
  B. `pycose` for the COSE_Sign1 and `jcs` for RFC 8785, when installed.

Each vector declares the outcome it was designed to produce and the single
check designed to produce it. A vector is credited when both verifiers return
the declared outcome AND the failing check is the designed one.

Dependencies: cryptography. pycose and jcs are optional (verifier B).
"""
import base64
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORS = os.path.join(ROOT, "vectors", "arp-vc-profile-v0.1.json")
RUN = os.path.join(ROOT, "runs", "arp_vc_profile_run.json")

CTYPE = "application/arp-reconciliation-output+json"
TYP = "application/vc+cose"
VCDM2 = "https://www.w3.org/ns/credentials/v2"
VERDICTS = {"match", "no-match", "partial-match", "indeterminate"}
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
REQUIRED_SUBJECT = [
    "reconciliationHash", "claimHash", "policyVersionHash", "combinedVerdict",
    "requesterBindingClass", "addressedRegisters",
    "bilateralRegisterAgreementHashes", "reconciliationTimestamp",
    "relianceHorizon", "audienceSet", "sealedOutput"]


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# ---- minimal CBOR reader: enough for COSE_Sign1 (RFC 9052) -----------------
def _read(b, i):
    ib = b[i]; mt = ib >> 5; ai = ib & 31; i += 1
    if ai < 24:
        arg = ai
    elif ai in (24, 25, 26, 27):
        n = 1 << (ai - 24)
        arg = int.from_bytes(b[i:i + n], "big"); i += n
    else:
        raise ValueError("indefinite or reserved length")
    if mt == 0:
        return arg, i
    if mt == 1:
        return -1 - arg, i
    if mt == 2:
        return bytes(b[i:i + arg]), i + arg
    if mt == 3:
        return b[i:i + arg].decode(), i + arg
    if mt == 4:
        out = []
        for _ in range(arg):
            v, i = _read(b, i); out.append(v)
        return out, i
    if mt == 5:
        out = {}
        for _ in range(arg):
            k, i = _read(b, i); v, i = _read(b, i); out[k] = v
        return out, i
    if mt == 6:
        v, i = _read(b, i)
        return ("tag", arg, v), i
    raise ValueError("unsupported major type %d" % mt)


def parse_sign1(raw):
    v, end = _read(raw, 0)
    if end != len(raw):
        raise ValueError("trailing bytes")
    if isinstance(v, tuple) and v[0] == "tag":
        if v[1] != 18:
            raise ValueError("not COSE_Sign1")
        v = v[2]
    if not (isinstance(v, list) and len(v) == 4):
        raise ValueError("not a COSE_Sign1 array")
    prot_b, unprot, payload, sig = v
    prot, _ = _read(prot_b, 0)
    return prot_b, prot, payload, sig


def _bstr_head(n):
    if n < 24:
        return bytes([0x40 | n])
    if n < 256:
        return bytes([0x58, n])
    if n < 65536:
        return bytes([0x59]) + n.to_bytes(2, "big")
    return bytes([0x5A]) + n.to_bytes(4, "big")


def sig_structure(prot_b, payload):
    # ["Signature1", protected, external_aad = h'', payload]
    return (b"\x84" + b"\x6aSignature1" + _bstr_head(len(prot_b)) + prot_b
            + b"\x40" + _bstr_head(len(payload)) + payload)


# ---- RFC 8785 for the value space this profile uses ------------------------
def jcs_A(v):
    if isinstance(v, dict):
        items = sorted(v.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(jcs_A(k) + ":" + jcs_A(x) for k, x in items) + "}"
    if isinstance(v, list):
        return "[" + ",".join(jcs_A(x) for x in v) + "]"
    if isinstance(v, str):
        out = ['"']
        for ch in v:
            o = ord(ch)
            if ch == '"': out.append('\\"')
            elif ch == "\\": out.append("\\\\")
            elif ch == "\b": out.append("\\b")
            elif ch == "\f": out.append("\\f")
            elif ch == "\n": out.append("\\n")
            elif ch == "\r": out.append("\\r")
            elif ch == "\t": out.append("\\t")
            elif o < 0x20: out.append("\\u%04x" % o)
            else: out.append(ch)
        out.append('"')
        return "".join(out)
    if v is True: return "true"
    if v is False: return "false"
    if v is None: return "null"
    if isinstance(v, int): return str(v)
    raise ValueError("number form outside this profile")


def parse_ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class Reject(Exception):
    def __init__(self, check):
        self.check = check


TOP_MEMBERS = {"@context", "type", "id", "issuer", "validFrom", "validUntil",
               "credentialSubject"}
SUBJECT_MEMBERS = set(REQUIRED_SUBJECT)
VOCAB = "https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/vocab#"


def strict_b64u(s, n=None):
    """Unpadded base64url that round-trips; n = required decoded length."""
    if not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", s):
        return None
    try:
        b = unb64u(s)
    except Exception:
        return None
    if b64u(b) != s or (n is not None and len(b) != n):
        return None
    return b


def cbor_text_key(t):
    """Sort key: the deterministic CBOR encoding of a text string."""
    u = t.encode("utf-8"); n = len(u)
    head = bytes([0x60 | n]) if n < 24 else (bytes([0x78, n]) if n < 256
                                             else bytes([0x79]) + n.to_bytes(2, "big"))
    return head + u


# checks that a control run may switch off (see run_controls)
DISABLED = set()


def _raise(check):
    if check not in DISABLED:
        raise Reject(check)


def check_profile(prot, payload, doc, sealed, evaluate_at):
    """Returns 'accept' or 'stale'; raises Reject(check) otherwise.
    Order of checks is fixed so the designed check is the first to fire."""
    # headers
    if prot.get(16) != TYP:
        raise Reject("typ")
    if prot.get(3) != CTYPE:
        raise Reject("cty")
    if prot.get(1) != -8:
        raise Reject("alg")
    kid = prot.get(4)
    if kid != doc["test_key"]["kid"].encode():
        raise Reject("key")
    # signature is checked by the caller before this function
    c = json.loads(payload.decode("utf-8"))
    # canonical form
    if payload.decode("utf-8") != jcs_A(c):
        raise Reject("canonical")
    ctx = c.get("@context")
    if not (isinstance(ctx, list) and ctx and ctx[0] == VCDM2):
        raise Reject("context")
    if ctx != [VCDM2, {"@vocab": VOCAB}]:
        _raise("context-exact")
    if c.get("type") != ["VerifiableCredential", "ArpReconciliationOutput"]:
        raise Reject("type")
    if set(c) - TOP_MEMBERS:
        _raise("members")
    if c.get("issuer") != doc["test_key"]["origin"]:
        raise Reject("issuer")
    s = c.get("credentialSubject", {})
    if isinstance(s, dict) and set(s) - SUBJECT_MEMBERS:
        _raise("members")
    for k in REQUIRED_SUBJECT:
        if k not in s:
            raise Reject("audience" if k == "audienceSet" else "subject")
    aud = s["audienceSet"]
    if not (isinstance(aud, list) and len(aud) >= 1
            and all("id" in m and "verificationMethod" in m for m in aud)):
        raise Reject("audience")
    for ts in (c.get("validFrom"), s["reconciliationTimestamp"],
               s["relianceHorizon"], c.get("validUntil")):
        if ts is None:
            if ts is c.get("validUntil"):
                raise Reject("horizon")
            raise Reject("timestamp")
        if not TS_RE.match(ts):
            raise Reject("timestamp")
    if c["validFrom"] != s["reconciliationTimestamp"]:
        raise Reject("timestamp")
    if not parse_ts(c["validFrom"]) < parse_ts(c["validUntil"]):
        _raise("horizon-order")
    if c["validUntil"] != s["relianceHorizon"]:
        raise Reject("horizon")
    if s["combinedVerdict"] not in VERDICTS:
        raise Reject("verdict")
    # byte-string renderings: one form only (Section 7.7)
    for k in ("reconciliationHash", "claimHash", "policyVersionHash"):
        if strict_b64u(s[k], 32) is None:
            _raise("encoding")
    bra = s["bilateralRegisterAgreementHashes"]
    if not (isinstance(bra, list) and all(strict_b64u(x, 32) for x in bra)):
        _raise("encoding")
    else:
        raw_bra = [unb64u(x) for x in bra]
        if raw_bra != sorted(set(raw_bra)):
            _raise("order")
    ids = [m["id"] for m in aud]
    if ids != sorted(set(ids), key=cbor_text_key):
        _raise("order")
    for m in aud:
        if strict_b64u(m["verificationMethod"], 32) is None:
            _raise("encoding")
    if c["id"] != "urn:arp:reconciliation:" + s["reconciliationHash"]:
        _raise("id-binding")
    so = s["sealedOutput"]
    if strict_b64u(so.get("digest"), 32) is None:
        _raise("encoding")
    if so.get("mediaType") != "application/arp-sealed-reconciliation-output+cose":
        _raise("binding")
    if so.get("digestAlgorithm") != "sha-256" or \
            so.get("digest") != b64u(hashlib.sha256(sealed).digest()):
        raise Reject("binding")
    if parse_ts(s["relianceHorizon"]) < evaluate_at:
        return "stale"
    return "accept"


def verify_A(raw, doc, sealed, evaluate_at):
    try:
        prot_b, prot, payload, sig = parse_sign1(raw)
    except Exception:
        return "reject", "cose"
    pub = Ed25519PublicKey.from_public_bytes(unb64u(doc["test_key"]["x"]))
    try:
        pub.verify(sig, sig_structure(prot_b, payload))
    except InvalidSignature:
        return "reject", "signature"
    try:
        return check_profile(prot, payload, doc, sealed, evaluate_at), None
    except Reject as r:
        return "reject", r.check


def verify_B(raw, doc, sealed, evaluate_at):
    from pycose.keys import OKPKey
    from pycose.keys.curves import Ed25519
    from pycose.messages import Sign1Message
    import jcs
    import cbor2
    try:
        # cbor2 6.x yields tuples for arrays, which Sign1Message.decode
        # refuses; the tagged value is handed over as a list instead.
        tagged = cbor2.loads(raw)
        if getattr(tagged, "tag", None) != 18:
            return "reject", "cose"
        obj = list(tagged.value)
        obj[1] = dict(obj[1])     # cbor2 6.x yields an immutable map
        m = Sign1Message.from_cose_obj(obj, True)
    except Exception:
        return "reject", "cose"
    m.key = OKPKey(crv=Ed25519, x=unb64u(doc["test_key"]["x"]))
    if not m.verify_signature():
        return "reject", "signature"
    # reuse the profile checks with jcs as the canonical oracle
    prot = {(k if isinstance(k, int) else k.identifier):
            (v.identifier if hasattr(v, "identifier") else v)
            for k, v in m.phdr.items()}
    pay = m.payload
    c = json.loads(pay.decode("utf-8"))
    if jcs.canonicalize(c) != pay:
        # same ordering as A: header checks first
        for chk, ok in (("typ", prot.get(16) == TYP),
                        ("cty", prot.get(3) == CTYPE),
                        ("alg", prot.get(1) == -8),
                        ("key", prot.get(4) == doc["test_key"]["kid"].encode())):
            if not ok:
                return "reject", chk
        return "reject", "canonical"
    try:
        # A's jcs_A equals jcs here when canonical, so the shared checks apply
        return check_profile(prot, pay, doc, sealed, evaluate_at), None
    except Reject as r:
        return "reject", r.check


CONTROLLED = ["context-exact", "members", "horizon-order", "encoding",
              "order", "id-binding"]


def run_controls(doc, sealed, t_ok):
    """Mutant verifiers. Each switches one red-team check off and must let
    at least one vector through that the full verifier refuses. A check no
    vector can distinguish from its absence is not covered."""
    out = {}
    for name in CONTROLLED:
        DISABLED.clear(); DISABLED.add(name)
        flipped = []
        for v in doc["vectors"]:
            if v["designed_failure"] != name:
                continue
            r = verify_A(bytes.fromhex(v["cose_hex"]), doc, sealed, t_ok)
            if r[0] != "reject" or r[1] != name:
                flipped.append(v["id"])
        out[name] = flipped
    DISABLED.clear()
    return out


def main():
    with open(VECTORS) as f:
        doc = json.load(f)
    sealed = bytes.fromhex(doc["sealed_output_hex"])
    t_ok = parse_ts(doc["evaluate_at"])
    t_stale = parse_ts(doc["evaluate_at_stale"])
    try:
        import pycose, jcs  # noqa: F401
        have_b = True
    except ImportError:
        have_b = False

    rows, failures = [], 0
    for v in doc["vectors"]:
        raw = bytes.fromhex(v["cose_hex"])
        at = t_stale if v["designed_failure"] == "horizon-elapsed" else t_ok
        a = verify_A(raw, doc, sealed, at)
        b = verify_B(raw, doc, sealed, at) if have_b else a
        want = v["expect"]
        want_chk = None if want == "accept" else (
            "horizon" if v["designed_failure"] == "horizon-elapsed"
            else v["designed_failure"])
        ok = (a[0] == want and b[0] == want and
              (want == "accept" or a[1] == want_chk or want == "stale")
              and a == b)
        if not ok:
            failures += 1
        rows.append({"id": v["id"], "title": v["title"], "expect": want,
                     "A": list(a), "B": list(b), "credited": ok})
        print("%s %-4s %-7s A=%-18s B=%-18s %s" % (
            "OK  " if ok else "FAIL", v["id"], want, a, b, v["title"]))

    controls = run_controls(doc, sealed, t_ok)
    for name, fl in controls.items():
        ok = bool(fl)
        if not ok:
            failures += 1
        print("%s control %-14s mutant admits %s" % (
            "OK  " if ok else "FAIL", name, fl or "NOTHING"))
    out = {"controls": controls, "vector_file_sha256": hashlib.sha256(
        open(VECTORS, "rb").read()).hexdigest(),
        "verifier_b_present": have_b,
        "vectors": len(rows), "credited": len(rows) - failures,
        "rows": rows}
    os.makedirs(os.path.dirname(RUN), exist_ok=True)
    with open(RUN, "w", newline="\n") as f:
        json.dump(out, f, indent=1); f.write("\n")
    print("\n%d of %d credited; verifier B %s" % (
        len(rows) - failures, len(rows), "present" if have_b else "ABSENT"))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
