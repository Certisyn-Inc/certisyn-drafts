#!/usr/bin/env python3
"""Builds vectors/arp-vc-profile-v0.1.json: the Verifiable Credentials profile
of a Reconciliation Output (Section 7.6) secured as application/vc+cose.

    python3 runners/build_vc_vectors.py            # rewrites the vector file

The sealing key is derived from a published test seed, so the vector file is
byte-identical on every run. Ed25519 signatures are deterministic (RFC 8032).
The key protects nothing and appears in the file as `test_key`.

Independent of the subject: the RFC 8785 serialisation here is the `jcs`
package, the COSE_Sign1 is built by `pycose`. The runner verifies with a
separate hand-written parser and checks the same bytes with `pycose` again.
Nothing in this file imports the runner.

Dependencies (BUILDER ONLY): cbor2, pycose, jcs, cryptography.
"""
import base64
import copy
import hashlib
import json
import os

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from pycose.keys import OKPKey
from pycose.keys.curves import Ed25519
from pycose.messages import Sign1Message
from pycose.headers import Algorithm, KID, ContentType
from pycose.algorithms import EdDSA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "vectors", "arp-vc-profile-v0.1.json")

SEED = bytes.fromhex("a1" * 32)
ORIGIN = "https://arp.example.org"
CTYPE = "application/arp-reconciliation-output+json"
TYP = "application/vc+cose"
VOCAB = "https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/vocab#"
VCDM2 = "https://www.w3.org/ns/credentials/v2"
TS = "2026-10-14T18:00:00Z"
HORIZON = "2026-10-15T18:00:00Z"


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def thumbprint(pub_raw):
    # RFC 7638 for an OKP key: members crv, kty, x in lexicographic order
    j = '{"crv":"Ed25519","kty":"OKP","x":"%s"}' % b64u(pub_raw)
    return b64u(hashlib.sha256(j.encode()).digest())


priv = Ed25519PrivateKey.from_private_bytes(SEED)
pub_raw = priv.public_key().public_bytes(
    serialization.Encoding.Raw, serialization.PublicFormat.Raw)
KID_TXT = thumbprint(pub_raw)

# Stand-in for the sealed COSE_Sign1 of the normative Output. The profile
# binds to its bytes through a SHA-256 digest and inspects nothing inside it.
SEALED = bytes.fromhex("d28443a10127a0") + b"arp-test-fixture-sealed-output" \
    + bytes(range(64))
RECON_HASH = hashlib.sha256(b"arp-test-fixture-preimage").digest()
CLAIM_HASH = hashlib.sha256(b"claim:sanctions:any-list-match").digest()
POLICY_HASH = hashlib.sha256(b"policy-version-fixture").digest()
BRA = sorted([hashlib.sha256(b"bra-1").digest(), hashlib.sha256(b"bra-2").digest()])


def base_credential():
    return {
        "@context": [VCDM2, {"@vocab": VOCAB}],
        "type": ["VerifiableCredential", "ArpReconciliationOutput"],
        "id": "urn:arp:reconciliation:" + b64u(RECON_HASH),
        "issuer": ORIGIN,
        "validFrom": TS,
        "validUntil": HORIZON,
        "credentialSubject": {
            "reconciliationHash": b64u(RECON_HASH),
            "claimHash": b64u(CLAIM_HASH),
            "policyVersionHash": b64u(POLICY_HASH),
            "combinedVerdict": "no-match",
            "requesterBindingClass": "agent-verified",
            "addressedRegisters": [
                "https://ofac.example.gov", "https://sanctions.example.eu"],
            "bilateralRegisterAgreementHashes": [b64u(h) for h in BRA],
            "reconciliationTimestamp": TS,
            "relianceHorizon": HORIZON,
            "audienceSet": [
                {"id": "https://acme.example.com/operators/jdoe",
                 "verificationMethod": b64u(hashlib.sha256(b"aud-key-1").digest())}],
            "sealedOutput": {
                "digestAlgorithm": "sha-256",
                "digest": b64u(hashlib.sha256(SEALED).digest()),
                "mediaType": "application/arp-sealed-reconciliation-output+cose"},
        },
    }


def secure(cred, kid=KID_TXT, typ=TYP, cty=CTYPE, payload=None, key=None):
    payload = payload if payload is not None else jcs.canonicalize(cred)
    m = Sign1Message(
        phdr={Algorithm: EdDSA, KID: kid.encode(), 16: typ, ContentType: cty},
        payload=payload)
    k = key or OKPKey(crv=Ed25519, d=SEED, x=pub_raw)
    m.key = k
    return m.encode(tag=True)


def vec(vid, title, cose, expect, why, note=None):
    d = {"id": vid, "title": title, "cose_hex": cose.hex(),
         "expect": expect, "designed_failure": why}
    if note:
        d["note"] = note
    return d


def main():
    good = base_credential()
    vectors = []
    vectors.append(vec("V01", "conforming credential", secure(good),
                       "accept", None))

    # M: payload altered after signing (byte flip inside the JSON)
    s = secure(good)
    i = s.index(b"no-match")
    t = bytearray(s); t[i] ^= 0x01
    vectors.append(vec("V02", "payload byte altered after signing",
                       bytes(t), "reject", "signature"))

    # M: verdict changed and re-signed under the sealing key (still a valid
    # signature; the digest of the sealed output does not move, so only the
    # ledger or the sealed envelope can expose it. Profile rule: verifier
    # that holds the sealed envelope compares reconciliationHash; here the
    # vector carries a mismatching sealedOutput digest instead).
    c = copy.deepcopy(good)
    c["credentialSubject"]["sealedOutput"]["digest"] = b64u(
        hashlib.sha256(SEALED + b"x").digest())
    vectors.append(vec("V03", "sealedOutput digest does not match the sealed envelope",
                       secure(c), "reject", "binding",
                       "Verifier is given the sealed COSE_Sign1 bytes."))

    c = copy.deepcopy(good); del c["credentialSubject"]["audienceSet"]
    vectors.append(vec("V04", "audienceSet absent", secure(c), "reject",
                       "audience"))

    c = copy.deepcopy(good); c["credentialSubject"]["audienceSet"] = []
    vectors.append(vec("V05", "audienceSet empty without the empty-set marker",
                       secure(c), "reject", "audience"))

    c = copy.deepcopy(good); del c["validUntil"]
    vectors.append(vec("V06", "validUntil absent", secure(c), "reject",
                       "horizon"))

    c = copy.deepcopy(good); c["validUntil"] = "2027-10-15T18:00:00Z"
    vectors.append(vec("V07", "validUntil differs from relianceHorizon",
                       secure(c), "reject", "horizon"))

    c = copy.deepcopy(good); c["issuer"] = "https://other.example.org"
    vectors.append(vec("V08", "issuer origin differs from the sealing origin",
                       secure(c), "reject", "issuer"))

    vectors.append(vec("V09", "kid is not the sealing key thumbprint",
                       secure(good, kid="AAAA"), "reject", "key"))

    # re-ordered keys, valid signature over non-RFC 8785 bytes
    raw = json.dumps(good, indent=1).encode()
    vectors.append(vec("V10", "payload is not RFC 8785 canonical",
                       secure(good, payload=raw), "reject", "canonical"))

    vectors.append(vec("V11", "typ header is not application/vc+cose",
                       secure(good, typ="application/cose"), "reject", "typ"))

    vectors.append(vec("V12", "content type header is application/vc, not the ARP subtype",
                       secure(good, cty="application/vc"), "reject", "cty",
                       "W3C permits application/vc; the ARP profile fixes the subtype."))

    c = copy.deepcopy(good); c["@context"] = [VOCAB]
    vectors.append(vec("V13", "VCDM 2.0 base context absent", secure(c),
                       "reject", "context"))

    c = copy.deepcopy(good); c["validFrom"] = "2026-10-14T18:00:00+00:00"
    c["credentialSubject"]["reconciliationTimestamp"] = c["validFrom"]
    vectors.append(vec("V14", "timestamp with numeric offset instead of Z",
                       secure(c), "reject", "timestamp"))

    c = copy.deepcopy(good); c["credentialSubject"]["combinedVerdict"] = "clear"
    vectors.append(vec("V15", "verdict outside the four defined values",
                       secure(c), "reject", "verdict"))

    # wrong signer: valid COSE, signed by another key, kid still the sealing kid
    other = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("b2" * 32))
    opub = other.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ok = OKPKey(crv=Ed25519, d=bytes.fromhex("b2" * 32), x=opub)
    vectors.append(vec("V16", "signed by a key other than the sealing key",
                       secure(good, key=ok), "reject", "signature"))

    # stale: genuine and unforged, evaluated after the horizon
    vectors.append(vec("V17", "genuine credential evaluated after its Reliance Horizon",
                       secure(good), "stale", "horizon-elapsed",
                       "Evaluation time set after relianceHorizon. Outcome is stale, not forged."))


    # ---- red-team vectors: each is signed by the genuine sealing key ----
    # context hijack: base context first, second element redefines terms
    c = copy.deepcopy(good)
    c["@context"] = [VCDM2, {"@vocab": VOCAB, "combinedVerdict": "https://evil.example/benign"}]
    vectors.append(vec("V18", "second context element redefines a term",
                       secure(c), "reject", "context-exact",
                       "Signed by the sealing key. JSON-LD processors would read combinedVerdict as another property."))

    c = copy.deepcopy(good); c["credentialSubject"]["perRegisterResults"] = [["https://ofac.example.gov", "match"]]
    vectors.append(vec("V19", "subject carries a member outside the profile",
                       secure(c), "reject", "members",
                       "Register content must not ride in the credential."))

    c = copy.deepcopy(good); c["evidence"] = {"id": "https://evil.example/x", "type": "Any"}
    vectors.append(vec("V20", "credential carries a top-level member outside the profile",
                       secure(c), "reject", "members"))

    c = copy.deepcopy(good)
    c["id"] = "urn:arp:reconciliation:" + b64u(hashlib.sha256(b"other").digest())
    vectors.append(vec("V21", "id names a different reconciliation than reconciliationHash",
                       secure(c), "reject", "id-binding"))

    c = copy.deepcopy(good); c["validFrom"] = "2026-10-16T18:00:00Z"
    c["credentialSubject"]["reconciliationTimestamp"] = c["validFrom"]
    vectors.append(vec("V22", "validFrom after validUntil", secure(c),
                       "reject", "horizon-order"))

    c = copy.deepcopy(good)
    c["credentialSubject"]["claimHash"] = b64u(CLAIM_HASH) + "="
    vectors.append(vec("V23", "padded base64url byte string", secure(c),
                       "reject", "encoding"))

    c = copy.deepcopy(good)
    c["credentialSubject"]["policyVersionHash"] = base64.b64encode(
        b"\xfb\xff" * 16).decode()
    vectors.append(vec("V24", "standard base64 alphabet in a byte string",
                       secure(c), "reject", "encoding"))

    c = copy.deepcopy(good)
    c["credentialSubject"]["bilateralRegisterAgreementHashes"] = list(reversed(
        c["credentialSubject"]["bilateralRegisterAgreementHashes"]))
    vectors.append(vec("V25", "agreement hashes out of sorted order",
                       secure(c), "reject", "order"))

    c = copy.deepcopy(good)
    m = c["credentialSubject"]["audienceSet"][0]
    c["credentialSubject"]["audienceSet"] = [m, dict(m)]
    vectors.append(vec("V26", "duplicate Audience Member", secure(c),
                       "reject", "order"))

    # duplicate JSON key, hand-assembled: last wins in a naive parser
    canon = jcs.canonicalize(good).decode()
    dup = canon.replace('"combinedVerdict":"no-match"',
                        '"combinedVerdict":"match","combinedVerdict":"no-match"')
    vectors.append(vec("V27", "duplicate JSON member in the signed payload",
                       secure(good, payload=dup.encode()), "reject", "canonical"))

    # escape smuggling: same string value, non-canonical spelling
    esc = canon.replace('"no-match"', '"no\\u002dmatch"', 1)
    vectors.append(vec("V28", "string spelled with a unicode escape",
                       secure(good, payload=esc.encode()), "reject", "canonical"))

    # typ and cty only in the unprotected header: hand-built COSE_Sign1
    import cbor2
    m1 = Sign1Message(phdr={Algorithm: EdDSA, KID: KID_TXT.encode()},
                      uhdr={16: TYP, ContentType: CTYPE},
                      payload=jcs.canonicalize(good))
    m1.key = OKPKey(crv=Ed25519, d=SEED, x=pub_raw)
    vectors.append(vec("V29", "typ and content type carried unprotected",
                       m1.encode(tag=True), "reject", "typ"))

    # extra credential type
    c = copy.deepcopy(good); c["type"] = ["VerifiableCredential", "ArpReconciliationOutput", "AnyOther"]
    vectors.append(vec("V30", "additional credential type", secure(c),
                       "reject", "type"))

    doc = {
        "profile": "ARP Verifiable Credentials profile, Section 7.6",
        "version": "0.1",
        "test_key": {"alg": "EdDSA", "crv": "Ed25519",
                     "seed_hex": SEED.hex(), "x": b64u(pub_raw),
                     "kid": KID_TXT, "origin": ORIGIN,
                     "note": "published test seed; protects nothing"},
        "sealed_output_hex": SEALED.hex(),
        "evaluate_at": "2026-10-14T19:00:00Z",
        "evaluate_at_stale": "2026-10-16T00:00:00Z",
        "vectors": vectors,
    }
    with open(OUT, "w", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote", OUT, len(vectors), "vectors")


if __name__ == "__main__":
    main()
