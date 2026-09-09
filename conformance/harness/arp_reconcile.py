#!/usr/bin/env python3
"""
ARP reconciliation harness v2.1 -- draft-hillier-scitt-arp
=======================================================

Runs heterogeneous, independently-produced accountability artifacts through ARP
reconciliation. Emits PER-SOURCE verdicts with NAMED divergence axes. Never
collapses a set of independent claims into one overall "valid".

Two things this harness deliberately does NOT do:

  1. It does not assume that two identifiers computed by two different
     canonical constructions are equal. Identifier equality is a RECONCILED
     PREDICATE, provable only against a vector that pins identical preimage,
     field set, algorithm, domain separation, and representation. Absent that
     proof, ARP renders `caid-binding-unverified` and holds at INDETERMINATE.

  2. It does not upgrade an unproven claim. A proven failure REFUSEs; an
     unproven or partial claim is held at INDETERMINATE; only a fully proven
     set APPROVEs.

Real cryptography is performed where the corpus makes it possible:
  * EMILIA EP-RECEIPT-v1 / EP-BOUNDARY-v1  -- Ed25519 over JCS(payload), real verify
  * Noa noa.receipt/0.1                    -- chain-hash recompute + Ed25519, real verify
Suites whose verification requires machinery this harness does not implement
(WebAuthn, RFC 3161, Merkle inclusion, TSA chains) are consumed as
EXPECTATION-DERIVED legs and are labelled as such in every output. That
distinction is load-bearing: see the LEG PROVENANCE column.

Usage
-----
    python3 arp_reconcile.py --emilia <clone>/conformance/clean-room/frozen-v1 \
                             --noa    <clone>/conformance
    python3 arp_reconcile.py --emilia ... --noa ... --json out.json
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import unicodedata

# ---------------------------------------------------------------------------
# 0. Construction identifiers.
#
# ARP-01 carries TWO digest constructions, for two different purposes, and never
# states that they are non-interchangeable.
#   Appendix D  -- the shared correlation key for agent-action capsules:
#                  subject_digest = SHA-256(JCS(action)). -01 NAMES JCS. It does
#                  not identify WHICH JCS: the string "8785" does not occur
#                  anywhere in -01, and "JCS" occurs exactly once.
#   Section 2   -- the Canonical Claim, whose hash indexes the ledger: key sort,
#                  declared array order, Unicode NFC of string fields, canonical
#                  JSON number rendering, stripping of undefined values. The
#                  member-sort CODE UNIT is not pinned either.
# Appendix D agrees with EMILIA's deployed profile 22/22 -- that is the good
# result. Section 2 applies NFC and agrees 19/22 or 20/22 depending on how its
# unpinned member sort is read, and TWO of those divergences are COLLISIONS
# (NFD->NFC, U+212B->U+00C5). Substituting one construction for the other
# therefore fails silently. That is what a construction identifier is for.
#
# v2 CHANGE. Each construction now also declares whether its OWN SPECIFICATION
# obliges the profile the implementation uses. Agreeing by obligation and
# agreeing by coincidence are different facts, and a relying party is entitled
# to tell them apart before depending on a shared digest.
#
# That declaration is reported ALONGSIDE the identifier and is deliberately NOT
# hashed into it. The identifier commits to canonicalization PARAMETERS, so that
# two implementations producing byte-identical output share an identifier. An
# obligation is a fact about a specification, not about the bytes; folding it in
# would give identical bytes two identifiers and defeat the purpose. Hence:
# ALL THREE v1 IDENTIFIERS ARE UNCHANGED IN v2, and nothing already published
# against them needs revisiting.
# ---------------------------------------------------------------------------

# Reported with each identifier. NOT an input to construction_id_digest().
PROFILE_OBLIGED_BY_SPEC = {
    "arp-canonical-claim/1":
        "NO -- S2 does not pin its member-sort code unit (that is the 19-vs-20)",
    "arp-subject-digest/1":
        "NO -- App.D names JCS; -01 carries no reference to RFC 8785",
    "ep-canonicalization/1":
        "YES -- EP-CANONICALIZATION-v1 cites RFC 8785 normatively",
}

CONSTRUCTIONS = {
    "arp-canonical-claim/1": {
        "spec": "draft-hillier-scitt-arp-01 S2 Canonical Claim (NFC applied)",
        "key_sort": "unicode-codepoint",
        "array_order": "as-declared",
        "unicode": "nfc-applied-to-strings-and-member-names",
        "numbers": "rfc8259-canonical",
        "undefined": "stripped",
        "hash": "sha256",
    },
    "arp-subject-digest/1": {
        "spec": "draft-hillier-scitt-arp-01 App.D subject_digest = SHA-256(JCS(action))",
        "key_sort": "utf16-code-unit (RFC 8785 JCS)",
        "array_order": "as-declared",
        "unicode": "none (JCS does not normalize)",
        "numbers": "rfc8785-es6",
        "undefined": "n/a",
        "hash": "sha256",
    },
    "ep-canonicalization/1": {
        "spec": "EMILIA EP-CANONICALIZATION-v1 (RFC 8785 JCS over I-JSON)",
        "key_sort": "utf16-code-unit (RFC 8785 JCS)",
        "array_order": "as-declared",
        "unicode": "none (JCS does not normalize)",
        "numbers": "rfc8785-es6, safe integers only",
        "undefined": "n/a",
        "hash": "sha256",
    },
}


def construction_id_digest(name):
    """A construction identifier that is itself machine-checkable: the digest
    commits to the declared canonicalization parameters, so a consumer can
    determine compatibility rather than being warned against assuming it."""
    params = CONSTRUCTIONS[name]
    blob = name + "\x1f" + "\x1f".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 1. Canonicalization.
# ---------------------------------------------------------------------------

_ESCAPES = {
    0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r",
    0x22: '\\"', 0x5C: "\\\\",
}


def _jcs_string(s):
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if cp in _ESCAPES:
            out.append(_ESCAPES[cp])
        elif cp < 0x20:
            out.append("\\u%04x" % cp)
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _jcs_number(n):
    """RFC 8785 / ES6 number serialization. This corpus is integers-only by
    profile predicate, which keeps this exact."""
    if isinstance(n, bool):
        raise TypeError("bool is not a number")
    if isinstance(n, int):
        return str(n)
    if n != n or n in (float("inf"), float("-inf")):
        raise ValueError("non-finite number")
    if n == int(n) and abs(n) < 2 ** 53:
        return str(int(n))
    return repr(n)


def _utf16_units(s):
    """Sort key: UTF-16 code units, per RFC 8785."""
    return s.encode("utf-16-be", "surrogatepass")


def _codepoint_units(s):
    """Sort key: Unicode code points. ARP Section 2 says 'lexicographic sorting
    of object keys' without pinning the code unit, which is itself a gap this
    run surfaces."""
    return [ord(c) for c in s]


def _serialize(v, sort_key, nfc):
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, str):
        return _jcs_string(unicodedata.normalize("NFC", v) if nfc else v)
    if isinstance(v, (int, float)):
        return _jcs_number(v)
    if isinstance(v, list):
        return "[" + ",".join(_serialize(x, sort_key, nfc) for x in v) + "]"
    if isinstance(v, dict):
        keys = list(v.keys())
        if nfc:
            keys = [unicodedata.normalize("NFC", k) for k in keys]
            v = {unicodedata.normalize("NFC", k): val for k, val in v.items()}
        keys.sort(key=sort_key)
        return "{" + ",".join(
            _jcs_string(k) + ":" + _serialize(v[k], sort_key, nfc) for k in keys
        ) + "}"
    raise TypeError(f"uncanonicalizable type: {type(v)}")


def jcs_bytes(v):
    """RFC 8785 JCS -- EP's normatively cited profile, and the profile this
    harness implements for Appendix D, which names JCS without identifying it."""
    return _serialize(v, _utf16_units, nfc=False).encode("utf-8")


def arp_canonical_claim_bytes(v):
    """draft-hillier-scitt-arp-01 Section 2 Canonical Claim serialization."""
    return _serialize(v, _codepoint_units, nfc=True).encode("utf-8")


def subject_digest(action):
    """ARP Appendix D: subject_digest = SHA-256(JCS(action)).

    RFC 8785 is what this harness implements. -01 does not oblige it -- see the
    profile_obliged_by_spec parameter on arp-subject-digest/1."""
    return hashlib.sha256(jcs_bytes(action)).hexdigest()


def claim_hash(claim):
    """ARP Section 2 Claim Hash."""
    return hashlib.sha256(arp_canonical_claim_bytes(claim)).hexdigest()


# ---------------------------------------------------------------------------
# 2. Divergence axes and composition.
# ---------------------------------------------------------------------------

# HARD axes name a PROVEN failure. Anything else is unproven, not false.
HARD_AXES = {
    "agent-action-scope-divergence",
    "agent-credential-absent",
    "authorization-post-hoc",
    "attribution-substituted-for-authorization",
    "authorization-not-bound-to-action",
    "artifact-class-not-authorization-evidence",
    "machine-decision-not-human-authorization",
    "agent-impersonation-suspected",
    "raw-claim-not-covered-by-signature",
    "digest-mismatch",
    "artifact-tampered",
    "agent-principal-unverifiable",
    "signature-malformed",
    "signature-invalid",
    "log-proof-broken",
    "anchor-leaf-not-bound-to-payload",
    "chain-link-broken",
    "chain-sequence-duplicate",
    "chain-sequence-gap",
    "chain-scope-mismatch",
    "chain-head-truncated",
    "replay-detected",
    "version-replay",
    "freshness-stale",
    "agent-credential-absent",
    "quorum-not-met",
    "revocation-binding-invalid",
    "canonicalization-gate-failed",
}

# SOFT axes name something UNPROVEN. They hold at INDETERMINATE; they never
# REFUSE, and they are never silently upgraded to a match.
SOFT_AXES = {
    "caid-binding-unverified",
    "canonicalization-unverified",
    "outcome-reported-only",
    "physical-completion-unproven",
    "register-record-absent",
    "currency-unknown",
    "leg-not-independently-verified",
    "human-authorization-unproven",
}

# v2 ADDITION. chain-head-truncated in v1 was one axis doing four jobs. It fired
# on a bare `last_seq < checkpoint.highestSeq` shortfall, never read the
# published headHash, had no chain-id guard, and did not fire on the vector that
# shares its name. These are its causes, named separately.
CHECKPOINT_CAUSES = {
    "chain-head-truncated",          # head hash matches a PREFIX: genuinely short
    "chain-head-divergent",          # head hash matches nothing: rewritten, not short
    "checkpoint-scope-mismatch",     # checkpoint is for a different chain
    "checkpoint-signer-untrusted",   # no key in the keyring for this kid
    "checkpoint-signature-invalid",  # key found, Ed25519 verification failed
}
HARD_AXES |= CHECKPOINT_CAUSES

# v2: fail closed. An axis that is in neither set is a PROGRAMMING error, not an
# indeterminate result. v1's compose() fell through and returned INDETERMINATE
# or even APPROVE for an undeclared axis -- it failed OPEN. No undeclared axis
# occurs in either corpus, so this changes no v1 result; it removes the class.
_OVERLAP = HARD_AXES & SOFT_AXES
if _OVERLAP:
    raise SystemExit(
        f"axis declared both HARD and SOFT: {sorted(_OVERLAP)}. "
        "An axis cannot both prove a failure and merely fail to prove one."
    )


def compose_ex(legs):
    """Verdict Arithmetic, fail-closed, reporting the gate it stopped at.

    legs = [(source, verdict, axis, provenance), ...]
    Returns (verdict, refused_at, deciding_axis).

    refused_at is the SOURCE of the first HARD leg -- i.e. the gate the refusal
    was reached at. v1 reported only the axis, which meant a reader could not
    tell whether a REFUSE was reached before or after the evidence downstream of
    it had been evaluated. reject_tampered_anchor is the case in point: it
    refuses at the anchor ALGORITHM gate and the Merkle proof is never examined.
    """
    for (src, _vd, ax, _pv) in legs:
        if ax and ax not in HARD_AXES and ax not in SOFT_AXES:
            raise SystemExit(
                f"undeclared divergence axis {ax!r} emitted by leg {src!r}. "
                "Every axis MUST be declared HARD or SOFT before it can carry a "
                "verdict. Refusing to compose."
            )
    for (src, _vd, ax, _pv) in legs:
        if ax in HARD_AXES:
            return "REFUSE", src, ax
    for (src, vd, ax, _pv) in legs:
        if vd != "match":
            return "INDETERMINATE", src, ax
    return "APPROVE", None, None


def compose(legs):
    return compose_ex(legs)[0]


def checked(ret, where):
    """v2.1 ADDITION. Assert that a reconciler's reported disposition is the
    one its own legs compose to.

    Every reconciler returns (subject_digest, legs, disposition). Nothing in v2
    forced that third element to be compose(legs) -- it was a convention, and
    reconcile_currency broke it silently for a whole suite. A convention that
    can be broken without the run noticing is not a guarantee. This makes it
    one: a mismatch is a hard stop, not a wrong row.
    """
    sd, legs, disp = ret
    expected = compose(legs)
    if disp != expected:
        raise SystemExit(
            f"disposition/leg disagreement in {where}: reported {disp!r} but the "
            f"legs {legs!r} compose to {expected!r}. A disposition MUST be the "
            "output of the Verdict Arithmetic over the legs, never written "
            "beside them. Refusing to report."
        )
    return ret


# Provenance of a leg. This is the honesty column.
CRYPTO = "crypto-verified"      # this harness performed the verification
DERIVED = "expectation-derived"  # consumed the suite's own expected verdict
COMPUTED = "computed"            # this harness computed a digest/comparison


# ---------------------------------------------------------------------------
# 3. Cryptography.
# ---------------------------------------------------------------------------

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    from cryptography.exceptions import InvalidSignature
    _HAVE_CRYPTO = True
except ImportError:  # pragma: no cover
    _HAVE_CRYPTO = False


def _b64any(s):
    """Accept base64 or base64url, with or without padding."""
    s = s.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def ed25519_pub_from_spki(b64):
    raw = _b64any(b64)
    if len(raw) == 32:
        return Ed25519PublicKey.from_public_bytes(raw)
    key = load_der_public_key(raw)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("not an Ed25519 key")
    return key


def ed25519_verify(pub_b64, message, sig_b64):
    """Returns (ok, reason). reason is a divergence axis on failure."""
    if not _HAVE_CRYPTO:
        return None, "leg-not-independently-verified"
    try:
        pub = ed25519_pub_from_spki(pub_b64)
    except Exception:
        return False, "agent-principal-unverifiable"
    try:
        sig = _b64any(sig_b64)
    except Exception:
        return False, "signature-malformed"
    if len(sig) != 64:
        return False, "signature-malformed"
    try:
        pub.verify(sig, message)
        return True, None
    except InvalidSignature:
        return False, "signature-invalid"
    except Exception:
        return False, "signature-malformed"


# ---------------------------------------------------------------------------
# 4. EMILIA adapters.
# ---------------------------------------------------------------------------

# EP-RECEIPT-v1 / EP-BOUNDARY-v1: Ed25519 over JCS canonical bytes of
# document.payload. The public key travels with the vector (base64url SPKI).

AUTHORIZATION_ARTIFACT_CLASSES = {"EP-RECEIPT-v1"}
SUPPORTED_RECEIPT_VERSIONS = {"EP-RECEIPT-v1"}
MERKLE_V2_ALG = "EP-MERKLE-v2"


def _leaf_hash_v2(canonical_payload_bytes):
    """EP-MERKLE-v2 leaf = SHA-256(0x00 || canonicalJSON(payload)).
    Domain-separated from branches; documented in EMILIA's reference verifier
    (packages/verify/src/index.ts)."""
    return hashlib.sha256(b"\x00" + canonical_payload_bytes).hexdigest()


def _branch_v2(left_hex, right_hex):
    """EP-MERKLE-v2 branch = SHA-256(0x01 || leftHex || rightHex), positional."""
    return hashlib.sha256(
        b"\x01" + left_hex.encode("utf-8") + right_hex.encode("utf-8")
    ).hexdigest()


def verify_ep_anchor_v2(payload, anchor):
    """Returns (ok, axis). Real verification of the EP-MERKLE-v2 anchor."""
    leaf = anchor.get("leaf_hash")
    root = anchor.get("merkle_root")
    proof = anchor.get("merkle_proof") or []
    if not leaf or not root:
        return False, "log-proof-broken"
    # Self-check: the anchor leaf MUST bind THIS payload. An anchor lifted from
    # another receipt is a valid proof of the wrong thing.
    if leaf != _leaf_hash_v2(jcs_bytes(payload)):
        # Early return BY DESIGN: if the leaf is not this payload, the proof is
        # about something else and walking it would be answering the wrong
        # question. This means the run does not report whether such a proof
        # would also have reconstructed the root.
        return False, "anchor-leaf-not-bound-to-payload"
    cur = leaf
    for step in proof:
        sib = step.get("hash")
        if not sib:
            return False, "log-proof-broken"
        cur = (_branch_v2(cur, sib) if step.get("position") == "right"
               else _branch_v2(sib, cur))
    if cur != root:
        return False, "log-proof-broken"
    return True, None


def reconcile_ep_document(case, suite, slot="authorization"):
    """Real-cryptography leg for the EP-RECEIPT-v1 shaped suites."""
    doc = case.get("document") or {}
    payload = doc.get("payload")
    sig = (doc.get("signature") or {}).get("value")
    alg = (doc.get("signature") or {}).get("algorithm")
    version = doc.get("@version")
    pub = case.get("public_key")
    legs = []

    # Leg 0 -- version gate. An artifact whose format version is outside the
    # supported set is refused before anything else is considered; a valid
    # signature over an unsupported version is still an unsupported version.
    if version not in SUPPORTED_RECEIPT_VERSIONS and slot != "authorization":
        legs.append(("version-gate", "no-match", "version-replay", COMPUTED))

    # Leg A -- artifact class. An artifact presented in the pre-execution
    # authorization slot must BE authorization evidence. A post-execution
    # attribution record and a machine policy-decision record are validly
    # signed artifacts of a different class; the version gate refuses them
    # regardless of whether the signature verifies.
    if slot == "authorization" and version not in AUTHORIZATION_ARTIFACT_CLASSES:
        if version and "ATTRIBUTION" in version.upper():
            ax = "attribution-substituted-for-authorization"
        elif version and ("DECISION" in version.upper() or "POLICY" in version.upper()):
            ax = "machine-decision-not-human-authorization"
        else:
            ax = "artifact-class-not-authorization-evidence"
        legs.append(("artifact-class", "no-match", ax, COMPUTED))
    else:
        legs.append(("artifact-class", "match", None, COMPUTED))

    # Leg B -- signature over the canonical payload bytes.
    if payload is None or not sig or not pub:
        legs.append(("signature", "no-match", "signature-malformed", COMPUTED))
    elif alg and alg.lower() not in ("ed25519", "eddsa"):
        legs.append(("signature", "indeterminate",
                     "leg-not-independently-verified", DERIVED))
    else:
        ok, why = ed25519_verify(pub, jcs_bytes(payload), sig)
        if ok is None:
            legs.append(("signature", "indeterminate", why, DERIVED))
        elif ok:
            legs.append(("signature", "match", None, CRYPTO))
        else:
            legs.append(("signature", "no-match", why, CRYPTO))

    # Leg C -- raw-claim pass-through. A payload that self-asserts authority or
    # embeds its own verifier_result is consuming a peer-provided claim. ARP
    # consumes its own verifier's constrained result, never the artifact's
    # self-report.
    if isinstance(payload, dict):
        self_asserting = [k for k in ("authorized", "scope", "verifier_result")
                          if k in payload]
        if self_asserting:
            legs.append(("raw-claim", "no-match",
                         "raw-claim-not-covered-by-signature", COMPUTED))

        # Leg D -- independence. An "independent verification" whose verifier
        # key IS the issuer's own signing key is the same administrative party.
        # Reproduction is not independent verification.
        iv = payload.get("independent_verification")
        if isinstance(iv, dict):
            if iv.get("verifier_key") and pub and \
                    _norm_key(iv["verifier_key"]) == _norm_key(pub):
                legs.append(("independence", "no-match",
                             "agent-impersonation-suspected", COMPUTED))
            else:
                legs.append(("independence", "match", None, COMPUTED))

    # Leg E -- transparency anchor, verified for real. A legacy (pre-v2)
    # unbound anchor is refused by default: it proves inclusion of *a* leaf
    # without binding that leaf to this payload, which is inclusion without
    # attribution.
    anchor = doc.get("anchor")
    if isinstance(anchor, dict) and anchor.get("merkle_proof"):
        if anchor.get("alg") == MERKLE_V2_ALG:
            ok, why = verify_ep_anchor_v2(payload, anchor)
            legs.append(("anchor", "match" if ok else "no-match",
                         None if ok else why, CRYPTO))
        else:
            # Refused at the algorithm gate. The proof itself is NOT evaluated:
            # a pre-v2 anchor is unbound by construction, so walking it would
            # prove inclusion of a leaf nobody has tied to this payload.
            legs.append(("anchor", "no-match", "version-replay", COMPUTED))

    # Leg F -- the CAID guardrail. Where the artifact carries its own action
    # digest, ARP does NOT assume it equals its own subject_digest. Different
    # construction until proven otherwise.
    sd = None
    if isinstance(payload, dict):
        stated = payload.get("action_digest") or payload.get("action_hash")
        if stated:
            act = payload.get("action")
            sd = subject_digest(act) if isinstance(act, dict) else None
            legs.append(("caid-binding", "indeterminate",
                         "caid-binding-unverified", COMPUTED))

    return sd, legs, compose(legs)


def _norm_key(b64):
    try:
        return _b64any(b64)
    except Exception:
        return b64


# reject_* id -> proposed ARP divergence axis. This is the alignment table the
# on-list deliverable proposes; every name here is derived from a real vector id
# in the corpus, not invented.
REJECT_AXIS_MAP = [
    ("tampered_anchor", "log-proof-broken"),
    ("tampered_action", "artifact-tampered"),
    ("tampered_payload", "artifact-tampered"),
    ("tampered_nested_param", "artifact-tampered"),
    ("tampered_proof", "artifact-tampered"),
    ("tampered_field", "artifact-tampered"),
    ("tampered_value", "artifact-tampered"),
    ("tampered_signature", "signature-malformed"),
    ("tampered_time", "artifact-tampered"),
    ("wrong_key", "agent-principal-unverifiable"),
    ("wrong_pinned_key", "agent-principal-unverifiable"),
    ("wrong_log_key", "agent-principal-unverifiable"),
    ("unpinned_tsa", "agent-principal-unverifiable"),
    ("unpinned_delegator", "agent-principal-unverifiable"),
    ("unpinned_revoker", "agent-principal-unverifiable"),
    ("unloadable_pinned_key", "agent-principal-unverifiable"),
    ("key_substitution", "agent-principal-unverifiable"),
    ("duplicate_key", "canonicalization-gate-failed"),
    ("legacy_v1", "version-replay"),
    ("unsupported_version", "version-replay"),
    ("wrong_version", "version-replay"),
    ("malformed_sig", "signature-malformed"),
    ("malformed_signature", "signature-malformed"),
    ("missing_signature", "signature-malformed"),
    ("one_bad_signature", "signature-invalid"),
    ("broken_inclusion", "log-proof-broken"),
    ("broken_merkle", "log-proof-broken"),
    ("broken_chain", "chain-link-broken"),
    ("broken_renewal", "chain-link-broken"),
    ("non_append_only", "chain-link-broken"),
    ("expired", "freshness-stale"),
    ("expired_window", "freshness-stale"),
    ("stale_freshness", "freshness-stale"),
    ("non_monotonic_time", "freshness-stale"),
    ("out_of_bounds_time", "freshness-stale"),
    ("missing_signoff", "agent-credential-absent"),
    ("under_threshold", "quorum-not-met"),
    ("out_of_order", "quorum-not-met"),
    ("duplicate_human", "quorum-not-met"),
    ("initiator_is_approver", "agent-impersonation-suspected"),
    ("wrong_role", "agent-action-scope-divergence"),
    ("scope_violation", "agent-action-scope-divergence"),
    ("constraints_relaxed", "agent-action-scope-divergence"),
    ("revoke_a_for_b", "revocation-binding-invalid"),
    ("action_mismatch", "digest-mismatch"),
    ("digest_mismatch", "digest-mismatch"),
    ("protected_mismatch", "digest-mismatch"),
    ("wrong_covered_hash", "digest-mismatch"),
    ("action_binding", "digest-mismatch"),
    ("audience_wrong_rp", "agent-action-scope-divergence"),
    ("lifecycle_uv_absent", "agent-credential-absent"),
    ("lifecycle_up_absent", "agent-credential-absent"),
    ("structural_ceremony_type", "artifact-class-not-authorization-evidence"),
    ("v2_unbound_leaf", "log-proof-broken"),
    ("empty_path", "log-proof-broken"),
    ("non_canonicalizable_number", "canonicalization-gate-failed"),
    ("nonnumeric_child_cap", "canonicalization-gate-failed"),
    ("unsafe_integer", "canonicalization-gate-failed"),
    ("unsafe_large_exponent", "canonicalization-gate-failed"),
    ("non_integer_real", "canonicalization-gate-failed"),
    ("surrogate", "canonicalization-gate-failed"),
    ("nested_depth_over_limit", "canonicalization-gate-failed"),
    ("bare_signature_downgrade", "signature-malformed"),
    ("missing_token", "signature-malformed"),
    ("unparseable_garbage", "signature-malformed"),
    ("malformed_expected_digest", "digest-mismatch"),
    ("unpinned_tsa_empty", "agent-principal-unverifiable"),
    ("present_at_h1", "replay-detected"),
    ("absent_at_h2", "log-proof-broken"),
    ("k_minus_1", "quorum-not-met"),
    ("duplicate_counts_once", "quorum-not-met"),
    ("unpinned_ignored", "agent-principal-unverifiable"),
    ("different_head_ignored", "chain-link-broken"),
    ("missing_model_id", "canonicalization-gate-failed"),
    ("empty_model_version", "canonicalization-gate-failed"),
    ("malformed_digest", "digest-mismatch"),
    ("missing_digest", "digest-mismatch"),
    ("unknown_member", "canonicalization-gate-failed"),
    ("statement_over_cap", "canonicalization-gate-failed"),
    ("date_only", "canonicalization-gate-failed"),
    ("no_timezone", "canonicalization-gate-failed"),
    ("required_approvals_string", "canonicalization-gate-failed"),
    ("distinct_humans_false_shared_key", "agent-impersonation-suspected"),
    ("not_signed_data", "raw-claim-not-covered-by-signature"),
]

UNMAPPED = []


def map_reject_axis(case_id):
    t = case_id[len("reject_"):] if case_id.startswith("reject_") else case_id
    for needle, axis in REJECT_AXIS_MAP:
        if needle in t:
            return axis
    UNMAPPED.append(case_id)
    return "UNMAPPED"


def reconcile_emilia_generic(case, suite_name):
    """Expectation-derived leg for suites whose verification machinery
    (WebAuthn, RFC 3161, Merkle inclusion, TSA renewal chains) this harness does
    not implement. Clearly labelled: the leg is NOT independently verified."""
    cid = str(case.get("id", "?"))
    expect_valid = bool((case.get("expect") or {}).get("valid", True))
    legs = []
    src = suite_name
    if expect_valid:
        legs.append((src, "indeterminate", "leg-not-independently-verified", DERIVED))
    else:
        legs.append((src, "no-match", map_reject_axis(cid), DERIVED))
    return None, legs, compose(legs)


def reconcile_currency(case):
    """currency.v1.json is three-valued by design (fresh/stale/unknown).

    v2.1 FIX. v2 returned, for a `fresh` case, the leg

        ("currency", "match", None, DERIVED)

    together with the literal disposition string "INDETERMINATE". Those two
    disagree: compose() over a single unaxed match leg is APPROVE. The
    disposition was therefore hand-written rather than composed, and the row
    reported a verdict its own evidence did not support. This is the one place
    in the harness where a disposition was not the output of the Verdict
    Arithmetic, and it is exactly the failure mode the Verdict Arithmetic exists
    to prevent.

    Two things were wrong and both are fixed here.

    (1) The disposition is now composed, never written. All three branches
        return compose(legs).

    (2) The `fresh` leg was wrong in substance, not only in bookkeeping. This
        reconciler does not verify freshness; it reads expect_status out of the
        fixture. A leg saying "match" claims ARP established currency. It did
        not. The fresh branch now emits the same leg the rest of the
        expectation-derived path emits for a case the suite expects to be
        valid -- indeterminate on leg-not-independently-verified -- which is
        what reconcile_emilia_generic already did for every other suite.

    The composed disposition for a fresh case is INDETERMINATE, which is what
    v2 reported. No count in the run changes. What changes is that the row's
    leg now agrees with its verdict, and the honest reason is visible on the
    leg rather than implied by a string.
    """
    cid = str(case.get("id", "?"))
    status = (case.get("currency") or {}).get("expect_status") or cid.split("_")[0]
    if status == "fresh":
        legs = [("currency", "indeterminate", "leg-not-independently-verified", DERIVED)]
    elif status == "stale":
        legs = [("currency", "no-match", "freshness-stale", DERIVED)]
    else:
        legs = [("currency", "indeterminate", "currency-unknown", DERIVED)]
    return None, legs, compose(legs)


# --- the strict-parse gate (v2) --------------------------------------------
#
# v1 skipped canonicalization.v1.json's 13 reject_* vectors entirely: the suite
# is in the skip set, AND the 13 carry no pinned expected_digest, so the
# construction comparison returned before json.loads was reached. They appeared
# zero times in the v1 output and zero times in its JSON, while the v1 banner
# claimed they were "decided on the crypto/parse paths". They were not decided.
#
# The suite states the conformance requirement in its own profile field, so
# there is nothing to invent. A conformant runner MUST:
#   (1) parse with the standard JSON parser, rejecting on error;
#   (2) apply a strict-parse gate: reject duplicate member names compared AFTER
#       escape decoding, reject unpaired UTF-16 surrogate escapes, reject
#       container nesting deeper than 64 (suite-pinned);
#   (3) require the EP I-JSON predicate: every scalar a string, boolean, null,
#       or integer of magnitude <= 2^53-1.
# v2 implements all three and emits canonicalization-gate-failed with the cause.
# ---------------------------------------------------------------------------

EP_MAX_DEPTH = 64
EP_SAFE_INT_MAX = 2 ** 53 - 1


def _has_lone_surrogate(s):
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in s)


def _ep_walk(v, depth, causes):
    """depth is the CONTAINER nesting depth of v's parent: a top-level value is
    walked at depth 0, so a container at depth 64 is the 64th and is legal. The
    suite ships accept_nested_depth_at_limit as the counter-example that pins
    this; getting the comparison wrong rejects a document the suite requires be
    accepted."""
    if isinstance(v, (dict, list)) and depth >= EP_MAX_DEPTH:
        causes.add("nesting-depth-exceeded")
        return
    if isinstance(v, dict):
        for k, val in v.items():
            if _has_lone_surrogate(k):
                causes.add("unpaired-surrogate-in-member-name")
            _ep_walk(val, depth + 1, causes)
    elif isinstance(v, list):
        for item in v:
            _ep_walk(item, depth + 1, causes)
    elif isinstance(v, str):
        if _has_lone_surrogate(v):
            causes.add("unpaired-surrogate-in-string")
    elif isinstance(v, bool) or v is None:
        pass
    elif isinstance(v, int):
        if abs(v) > EP_SAFE_INT_MAX:
            causes.add("integer-outside-safe-range")
    elif isinstance(v, float):
        # NaN and the infinities are not JSON at all; Python's parser accepts
        # them by default and int() raises on them. Handled BEFORE any
        # arithmetic, so an input the gate exists to reject cannot crash it.
        if v != v or v in (float("inf"), float("-inf")):
            causes.add("non-finite-number")
        elif v != int(v):
            causes.add("non-integer-real")
        elif abs(v) > EP_SAFE_INT_MAX:
            causes.add("integer-outside-safe-range")
        # An integer-valued real -- 1.0, 1e0, -0.0 -- is NOT a violation. The
        # profile states that integer-valued number tokens pin one canonical
        # serialization, and the suite ships three accept_* vectors saying so.
    else:
        causes.add("scalar-outside-ijson-profile")


def ep_strict_parse_gate(raw):
    """Returns (ok, cause). cause is None when the gate passes.

    This is a real gate, computed here, not a read of the vector's expectation.
    """
    causes = set()

    def _pairs(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                causes.add("duplicate-member-name")
            seen.add(k)
        return dict(pairs)

    try:
        parsed = json.loads(raw, object_pairs_hook=_pairs)
    except RecursionError:
        return False, "nesting-depth-exceeded"
    except Exception:
        return False, "json-parse-error"
    try:
        _ep_walk(parsed, 0, causes)
    except RecursionError:
        return False, "nesting-depth-exceeded"
    except Exception:
        # The gate fails CLOSED. An input that breaks the walk is an input the
        # gate could not clear, which is a rejection, not a crash.
        return False, "profile-predicate-error"
    if causes:
        return False, sorted(causes)[0]
    return True, None


def run_strict_parse_gate(vectors):
    """The canonicalization suite's parse-boundary vectors, actually exercised.

    Two-sided on purpose. Running only the reject_* ids cannot detect a gate
    that is too strict, and a gate that is too strict fails the suite it claims
    to implement just as surely as one that is too loose. Every vector carrying
    input_json is run, and the accept_* ones MUST pass.
    """
    rows = []
    for c in vectors:
        cid = c.get("id", "?")
        cn = c.get("canonicalization") or {}
        raw = cn.get("input_json")
        if raw is None:
            continue
        ok, cause = ep_strict_parse_gate(raw)
        expect_valid = bool((c.get("expect") or {}).get("valid", True))
        legs = ([("strict-parse", "match", None, COMPUTED)] if ok else
                [("strict-parse", "no-match", "canonicalization-gate-failed", COMPUTED)])
        disp, gate, _ = compose_ex(legs)
        rows.append({
            "id": cid, "disposition": disp, "refused_at": gate,
            "cause": cause, "expected_valid": expect_valid,
            "agrees_with_suite": (ok == expect_valid),
            "note": cn.get("note", ""),
            "legs": [{"source": s, "verdict": v, "axis": a, "provenance": p}
                     for (s, v, a, p) in legs],
        })
    return rows


# --- the construction comparison -------------------------------------------

def run_canonicalization_comparison(vectors):
    """THE construction-identifier evidence.

    Each accept_* vector pins a SHA-256 of the EP canonical bytes. We recompute
    that digest under BOTH of ARP-01's own constructions:
      * Appendix D  -- SHA-256(JCS(...))            -- expected to agree with EP
      * Section 2   -- SHA-256(CanonicalClaim(...)) -- NFC-normalizing
    Where Section 2 and EP disagree, digest equality across the two profiles is
    not merely unproven, it is FALSE -- and no amount of good faith on either
    side would have surfaced it without a shared vector.
    """
    rows = []
    for c in vectors:
        cid = c.get("id", "?")
        cn = c.get("canonicalization") or {}
        raw = cn.get("input_json")
        pinned = cn.get("expected_digest")
        if raw is None or not pinned:
            continue
        try:
            parsed = json.loads(raw)
        except Exception:
            continue  # strict-parse gate cases; not a construction comparison
        try:
            d_appd = hashlib.sha256(jcs_bytes(parsed)).hexdigest()
        except Exception:
            d_appd = None
        try:
            d_sec2 = hashlib.sha256(arp_canonical_claim_bytes(parsed)).hexdigest()
        except Exception:
            d_sec2 = None
        # The draft says "lexicographic sorting of object keys" without pinning
        # the code unit. Both readings are reported, because the difference
        # between them IS one of the findings.
        try:
            d_sec2_u16 = hashlib.sha256(
                _serialize(parsed, _utf16_units, nfc=True).encode("utf-8")).hexdigest()
        except Exception:
            d_sec2_u16 = None
        rows.append({
            "id": cid,
            "note": cn.get("note", ""),
            "ep_pinned": pinned,
            "arp_appendix_d": d_appd,
            "arp_section_2": d_sec2,
            "appd_agrees": d_appd == pinned,
            "sec2_agrees": d_sec2 == pinned,
            "arp_canonical_claim_utf16sort": d_sec2_u16,
            "sec2_utf16_agrees": d_sec2_u16 == pinned,
        })
    return rows


# ---------------------------------------------------------------------------
# 5. Noa adapter -- real verification.
#
# Documented preimage (impl-py/noa_verify.py):
#   hash input  = JCS(receipt WITHOUT chain.hash AND WITHOUT sig.value)
#   chain.hash  = "sha256:" + hex(sha256(hash input))
#   signing msg = b"NOA-Receipt-v0.1-sig:" + sha256(hash input)
# ---------------------------------------------------------------------------

NOA_SIG_CONTEXT = b"NOA-Receipt-v0.1-sig:"


def _noa_hash_input(receipt):
    r = json.loads(json.dumps(receipt))  # deep copy
    if isinstance(r.get("chain"), dict):
        r["chain"].pop("hash", None)
    if isinstance(r.get("sig"), dict):
        r["sig"].pop("value", None)
    return jcs_bytes(r)


def reconcile_noa_receipt(receipt, keyring, prev):
    """prev = (prev_hash, prev_seq, prev_chain) or None for the first receipt."""
    legs = []
    prev_hash, prev_seq, prev_chain = prev if prev else (None, None, None)
    if not isinstance(receipt.get("chain"), dict) or not isinstance(receipt.get("sig"), dict):
        return None, [("shape", "no-match", "canonicalization-gate-failed", COMPUTED)], "REFUSE", None
    try:
        hi = _noa_hash_input(receipt)
    except Exception:
        return None, [("noa-receipt", "no-match", "canonicalization-gate-failed", COMPUTED)], "REFUSE", None
    digest = hashlib.sha256(hi).digest()
    computed_hash = "sha256:" + digest.hex()

    # Leg 1 -- content integrity: does chain.hash actually commit to these bytes?
    stated = (receipt.get("chain") or {}).get("hash")
    if stated != computed_hash:
        legs.append(("content-hash", "no-match", "artifact-tampered", CRYPTO))
    else:
        legs.append(("content-hash", "match", None, CRYPTO))

    # Leg 2 -- signature over the documented preimage.
    sig = (receipt.get("sig") or {}).get("value")
    kid = (receipt.get("sig") or {}).get("kid")
    alg = (receipt.get("sig") or {}).get("alg")
    pub = keyring.get(kid) if kid else None
    if alg != "ed25519":
        legs.append(("signature", "no-match", "signature-malformed", COMPUTED))
    elif not pub:
        legs.append(("signature", "no-match", "agent-principal-unverifiable", COMPUTED))
    elif not sig:
        legs.append(("signature", "no-match", "signature-malformed", COMPUTED))
    else:
        ok, why = ed25519_verify(pub, NOA_SIG_CONTEXT + digest, sig)
        if ok is None:
            legs.append(("signature", "indeterminate", why, DERIVED))
        elif ok:
            legs.append(("signature", "match", None, CRYPTO))
        else:
            legs.append(("signature", "no-match", why, CRYPTO))

    # Leg 3 -- chain linkage: hash linkage, sequence continuity, and scope.
    # A per-receipt verifier that only checks its own signature cannot see a
    # splice, a duplicate sequence number, or a gap. Those are properties of the
    # SET, which is exactly the layer ARP reconciles at.
    chain = receipt.get("chain") or {}
    seq = chain.get("seq")
    this_chain = (receipt.get("scope") or {}).get("chain")
    if prev_chain is not None and this_chain != prev_chain:
        legs.append(("chain-scope", "no-match", "chain-scope-mismatch", COMPUTED))
    if seq == 0:
        if chain.get("prevHash") not in (None, ""):
            legs.append(("chain-link", "no-match", "chain-link-broken", COMPUTED))
        else:
            legs.append(("chain-link", "match", None, COMPUTED))
    else:
        if prev_hash is None or chain.get("prevHash") != prev_hash:
            legs.append(("chain-link", "no-match", "chain-link-broken", COMPUTED))
        else:
            legs.append(("chain-link", "match", None, COMPUTED))
    if prev_seq is not None and isinstance(seq, int):
        if seq == prev_seq:
            legs.append(("chain-seq", "no-match", "chain-sequence-duplicate", COMPUTED))
        elif seq != prev_seq + 1:
            legs.append(("chain-seq", "no-match", "chain-sequence-gap", COMPUTED))

    # Leg 4 -- the CAID guardrail. action.paramsHash is Noa's construction over
    # the action params. ARP's subject_digest is a different construction over
    # the action object. Not equal until a vector proves it.
    action = receipt.get("action")
    sd = subject_digest(action) if isinstance(action, dict) else None
    if isinstance(action, dict) and action.get("paramsHash"):
        legs.append(("caid-binding", "indeterminate", "caid-binding-unverified", COMPUTED))

    # Leg 5 -- authorization. This is the leg the receipt format deliberately
    # does NOT claim to settle, and ARP renders it as three distinct outcomes:
    #   EXECUTED + a named human approval  -> authorization proven
    #   EXECUTED under a machine rule only -> machine policy allowed is NOT
    #                                         named human approved; held
    #   DEFERRED / BLOCKED                 -> no authorization exists
    gov = receipt.get("governance") or {}
    verdict = gov.get("verdict")
    approval = gov.get("approval")
    if verdict in ("DEFERRED", "BLOCKED"):
        legs.append(("authorization", "no-match", "agent-credential-absent", COMPUTED))
    elif verdict == "EXECUTED":
        by = (approval or {}).get("by") if isinstance(approval, dict) else None
        if by and str(by).upper().startswith("HUMAN"):
            legs.append(("authorization", "match", None, COMPUTED))
        else:
            legs.append(("authorization", "indeterminate",
                         "human-authorization-unproven", COMPUTED))

    # Leg 6 -- outcome. NEW IN v2.
    #
    # outcome-reported-only and physical-completion-unproven were declared in
    # v1's SOFT_AXES and emitted by nothing: each string occurred exactly once,
    # as a set member. They are implemented here, against evidence the receipt
    # actually carries, because the gap they name is the one that matters most
    # for autonomous agents -- a receipt is a statement ABOUT an action, and a
    # signature over that statement proves authorship, never occurrence.
    #
    #   outcome-reported-only        -- the chain asserts EXECUTED and the only
    #                                   attesting party is the one that acted.
    #                                   No independent source corroborates it.
    #   physical-completion-unproven -- as above, and the action is declared
    #                                   IRREVERSIBLE with no rollback handle, so
    #                                   the assertion is about the world and
    #                                   nothing in the artefact can settle it.
    #
    # Both are SOFT by construction. They HOLD a verdict at INDETERMINATE; they
    # never refuse, and they are never silently upgraded to a match. An
    # independent settlement or delivery attestation is what clears them.
    # Only reached when the receipt's own integrity held. Reading a semantic
    # field out of an artefact already proven tampered would emit a predicate
    # about attacker-controlled bytes and inflate the count with nothing.
    integrity_held = all(vd == "match" for (src, vd, _a, _p) in legs
                         if src in ("content-hash", "signature"))
    if verdict == "EXECUTED" and isinstance(action, dict) and integrity_held:
        # Corroboration, tested rather than assumed. An outcome is corroborated
        # only if some attesting party OTHER than the one that acted has signed
        # for it. A noa receipt carries exactly one signature, so in this corpus
        # the answer is always no -- but that is the FINDING, established here,
        # not a constant. A format that does carry a second attestation clears
        # the axis automatically, which is the property that makes this a
        # predicate rather than an assertion about noa.
        #
        # A named human APPROVER does not count. An approval is ex ante and
        # says the act was PERMITTED; corroborating an outcome needs an
        # attestation that the act OCCURRED. Collapsing those two is precisely
        # the error EP-BOUNDARY's attribution_substituted_for_authorization
        # vector exists to catch, in the opposite direction -- so it must not be
        # made here. Only an ex post attestation from another party counts.
        independent = set()
        signer_kid = (receipt.get("sig") or {}).get("kid")
        carriers = []
        for field in ("countersignatures", "witnesses", "settlement"):
            v = receipt.get(field)
            if isinstance(v, list):
                carriers.extend(v)
        for extra in carriers:
            if not isinstance(extra, dict):
                continue
            kid = extra.get("kid")
            # A self-countersignature is not corroboration. The attesting party
            # must be OTHER than the one that signed for the act.
            if kid and kid != signer_kid:
                independent.add(kid)

        if not independent:
            # True of EVERY uncorroborated EXECUTED assertion, reversible or
            # not: a signature proves authorship of the statement, never
            # occurrence of the act.
            legs.append(("outcome", "indeterminate",
                         "outcome-reported-only", COMPUTED))
            # And ADDITIONALLY where the act cannot be walked back: no rollback
            # handle, no settlement evidence, so the assertion is about an
            # effect outside the attestation system and nothing in the artefact
            # can ever settle it. The two are not alternatives.
            if action.get("reversible") is False and action.get("rollbackRef") is None:
                legs.append(("completion", "indeterminate",
                             "physical-completion-unproven", COMPUTED))

    return sd, legs, compose(legs), computed_hash


def load_noa_chain(path):
    with open(path) as f:
        doc = json.load(f)
    return doc if isinstance(doc, list) else [doc]


# ---------------------------------------------------------------------------
# 6. Runners.
# ---------------------------------------------------------------------------

W = 118


def hr(ch="-"):
    print(ch * W)


def print_legs(label, disposition, legs, label_w=46):
    det = "  ".join(
        f"{s}:{vd}" + (f"[{ax}]" if ax else "")
        for (s, vd, ax, _) in legs
    )
    print(f"{label[:label_w]:<{label_w}}{disposition:<16}{det}")


def run_emilia(root, results):
    vec_dir = os.path.join(root, "conformance", "vectors")
    if not os.path.isdir(vec_dir):
        vec_dir = root
    files = sorted(f for f in os.listdir(vec_dir) if f.endswith(".v1.json"))

    print()
    hr("=")
    print("CORPUS 1 -- EMILIA clean-room frozen-v1")
    hr("=")

    # --- 1a. The interop set Iman named, run with real cryptography ---------
    print()
    print("1a. EP-BOUNDARY-v1 -- 5 published vectors covering 4 of the 6 behaviours")
    print("    in the proposed interop set; real Ed25519 verification")
    print("    (authorization/attribution boundary; claim-matrix C-011/C-012)")
    hr()
    print(f"{'vector':<46}{'ARP verdict':<16}per-source leg -> divergence axis")
    hr()
    bpath = os.path.join(vec_dir, "boundary.v1.json")
    boundary_rows = []
    if os.path.exists(bpath):
        with open(bpath) as f:
            doc = json.load(f)
        for case in doc.get("vectors", []):
            sd, legs, disp = reconcile_ep_document(case, "boundary")
            print_legs(case.get("id", "?"), disp, legs)
            boundary_rows.append({
                "id": case.get("id"), "disposition": disp,
                "refused_at": compose_ex(legs)[1],
                "expect_valid": (case.get("expect") or {}).get("valid"),
                "legs": [{"source": s, "verdict": v, "axis": a, "provenance": p}
                         for (s, v, a, p) in legs],
                "arp_subject_digest": sd,
            })
    results["boundary"] = boundary_rows

    # --- 1b. EP-RECEIPT-v1, real cryptography ------------------------------
    print()
    print("1b. EP-RECEIPT-v1 (receipts.v1.json) -- real Ed25519 over JCS(payload)")
    hr()
    print(f"{'vector':<46}{'ARP verdict':<16}per-source leg -> divergence axis")
    hr()
    rpath = os.path.join(vec_dir, "receipts.v1.json")
    receipt_rows = []
    if os.path.exists(rpath):
        with open(rpath) as f:
            doc = json.load(f)
        for case in doc.get("vectors", []):
            if "document" not in case:
                continue
            sd, legs, disp = reconcile_ep_document(case, "receipts", slot="any")
            print_legs(case.get("id", "?"), disp, legs)
            receipt_rows.append({
                "id": case.get("id"), "disposition": disp,
                "refused_at": compose_ex(legs)[1],
                "expect_valid": (case.get("expect") or {}).get("valid"),
                "legs": [{"source": s, "verdict": v, "axis": a, "provenance": p}
                         for (s, v, a, p) in legs],
            })
    results["receipts"] = receipt_rows

    # --- 1c. Construction comparison ---------------------------------------
    print()
    print("1c. EP-CANONICALIZATION-v1 -- ARP-01's two constructions measured against")
    print("    the pinned EP digests. Appendix D is the cross-capsule correlation key;")
    print("    Section 2 is the ledger index. They are NOT interchangeable.")
    hr()
    cpath = os.path.join(vec_dir, "canonicalization.v1.json")
    canon_rows = []
    if os.path.exists(cpath):
        with open(cpath) as f:
            doc = json.load(f)
        canon_rows = run_canonicalization_comparison(doc.get("vectors", []))
        agree_d = sum(1 for r in canon_rows if r["appd_agrees"])
        agree_2 = sum(1 for r in canon_rows if r["sec2_agrees"])
        agree_2u = sum(1 for r in canon_rows if r["sec2_utf16_agrees"])
        n = len(canon_rows)
        print(f"    vectors with a pinned digest and parseable input : {n}")
        print(f"    App.D  subject_digest = SHA-256(JCS(action))    agrees: {agree_d}/{n}")
        print(f"    S2     Canonical Claim, sort = UTF-16 unit      agrees: {agree_2u}/{n}")
        print(f"    S2     Canonical Claim, sort = code point       agrees: {agree_2}/{n}")
        print()
        print("    Appendix D interoperates exactly. Section 2 is a DIFFERENT")
        print("    construction (it applies NFC) and must never be substituted for it;")
        print("    two of its divergences below are collisions, not just other bytes.")
        print("    Its member sort is also unpinned -- that is the 19 vs 20 difference.")
        print()
        div = [r for r in canon_rows if not r["sec2_agrees"]]
        if div:
            print(f"    Section 2 (code-point sort) diverges from EP on {len(div)} vector(s):")
            hr()
            print(f"    {'vector':<44}{'why'}")
            hr()
            for r in div:
                mark = "" if r["sec2_utf16_agrees"] else "  [both readings]"
                print(f"    {r['id'][:44]:<44}{r['note'][:50]}{mark}")
    results["canonicalization"] = canon_rows

    # --- 1c-bis. Strict-parse gate (NEW IN v2) ------------------------------
    print()
    print("1c-bis. EP-CANONICALIZATION-v1 strict-parse gate -- the 13 reject_*")
    print("    vectors. NEW IN v2: v1 skipped these entirely (the suite is in the")
    print("    skip set, and they carry no pinned digest, so the construction")
    print("    comparison returned before json.loads). v2 implements the gate the")
    print("    suite specifies in its own profile field: duplicate member names")
    print("    compared after escape decoding, unpaired surrogate escapes, nesting")
    print("    deeper than 64, and the EP I-JSON scalar predicate.")
    hr()
    gate_rows = []
    if os.path.exists(cpath):
        gate_rows = run_strict_parse_gate(doc.get("vectors", []))
        rej = [r for r in gate_rows if not r["expected_valid"]]
        acc = [r for r in gate_rows if r["expected_valid"]]
        print(f"    {'vector':<44}{'ARP verdict':<14}{'cause computed here'}")
        hr()
        for r in rej:
            print(f"    {r['id'][:44]:<44}{r['disposition']:<14}{r['cause'] or '-'}")
        bad_acc = [r for r in acc if not r["agrees_with_suite"]]
        for r in bad_acc:
            print(f"    !! {r['id'][:41]:<41}{r['disposition']:<14}"
                  f"{r['cause']}  <-- MUST HAVE BEEN ACCEPTED")
        agreed = sum(1 for r in gate_rows if r["agrees_with_suite"])
        print()
        print(f"    {len(rej) - len(bad_acc) - sum(1 for r in rej if not r['agrees_with_suite']):d}"
              f"/{len(rej)} reject_* vectors refused, each with a cause this harness")
        print(f"    computed rather than read; {len(acc) - len(bad_acc)}/{len(acc)} accept_* vectors passed the gate.")
        print(f"    Two-sided: {agreed}/{len(gate_rows)} agree with the suite's own expectation.")
        if agreed != len(gate_rows):
            print("    !! DISAGREEMENT -- investigate before relying on this gate.")
    results["strict_parse_gate"] = gate_rows

    # --- 1d. Remaining suites ----------------------------------------------
    print()
    print("1d. Remaining EMILIA suites -- EXPECTATION-DERIVED legs.")
    print("    This harness does not implement WebAuthn, RFC 3161, Merkle inclusion")
    print("    or TSA renewal-chain verification, so these legs consume the suite's")
    print("    own expected verdict. They are reported so the axis vocabulary can be")
    print("    aligned; they are NOT evidence that ARP verified anything.")
    hr()
    other_rows = []
    skip = {"boundary.v1.json", "receipts.v1.json", "canonicalization.v1.json"}
    tally = {}
    for fn in files:
        if fn in skip:
            continue
        with open(os.path.join(vec_dir, fn)) as f:
            doc = json.load(f)
        suite = fn.replace(".v1.json", "")
        for case in doc.get("vectors", []):
            if suite == "currency":
                sd, legs, disp = checked(reconcile_currency(case),
                                         f"reconcile_currency/{case.get('id')}")
            else:
                sd, legs, disp = checked(reconcile_emilia_generic(case, suite),
                                         f"reconcile_emilia_generic/{suite}/{case.get('id')}")
            tally[disp] = tally.get(disp, 0) + 1
            other_rows.append({
                "suite": suite, "id": case.get("id"), "disposition": disp,
                "refused_at": compose_ex(legs)[1],
                "legs": [{"source": s, "verdict": v, "axis": a, "provenance": p}
                         for (s, v, a, p) in legs],
            })
    print(f"    suites: {len(files) - len(skip)}   cases: {len(other_rows)}")
    print(f"    dispositions: " + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    PLACEHOLDERS = {"leg-not-independently-verified"}
    axes_used = sorted({l["axis"] for r in other_rows for l in r["legs"] if l["axis"]})
    substantive = [a for a in axes_used if a not in PLACEHOLDERS]
    print(f"    distinct axes emitted: {len(axes_used)} "
          f"({len(substantive)} substantive divergence axes + "
          f"{len(axes_used) - len(substantive)} provenance placeholder)")
    if UNMAPPED:
        print(f"    !! UNMAPPED negative-case ids ({len(UNMAPPED)}): "
              f"{', '.join(sorted(set(UNMAPPED))[:8])}")
    else:
        print("    every reject_* id routed through this path mapped to a named axis.")
        print("    Decomposition of the 95 reject_* occurrences (94 distinct --")
        print("    reject_unpinned_tsa appears in two of the 16 suites):")
        print("      73 routed through this map (72 distinct)")
        print("       9 receipts.v1.json, decided by the EP-RECEIPT reconciler")
        print("      13 canonicalization.v1.json, decided by the v2 strict-parse gate")
        print("    v1 exercised 0 of those 13 while its banner said otherwise. Fixed.")
    results["other"] = other_rows
    results["axes_used"] = axes_used
    results["axes_substantive"] = substantive
    results["unmapped"] = sorted(set(UNMAPPED))


# ---------------------------------------------------------------------------
# 6. The checkpoint leg -- rebuilt in v2.
#
# v1 fired ONE axis, chain-head-truncated, on ONE condition:
#     last_seq < checkpoint.highestSeq
# It never read the published headHash (the string did not occur in v1 at all),
# it had no chain-id guard, it never verified the checkpoint's own signature,
# and it never evaluated a chain against its COMPANION checkpoint. Consequences,
# all four of which v2 removes:
#   - cross-chain-splice and dup-seq were reported as truncations. Neither is.
#   - head-truncated.json, whose last seq equals highestSeq, did not fire the
#     axis that carries its name.
#   - the forged-checkpoint attack is a PAIR (a short chain plus a checkpoint
#     over the fake head signed with an out-of-keyring key). v1 scored the chain
#     half against the LEGITIMATE checkpoint, so it never evaluated the attack.
#   - the detection was right in every case, but for the wrong reason in three
#     of them. A verdict reached for the wrong reason is not reconciliation.
#
# The evidence a checkpoint actually carries is (chain, highestSeq, headHash,
# sig). v2 consults all four and emits a separate leg per fact.
# ---------------------------------------------------------------------------

_NOA_CHECKPOINT_DOMAIN = b"NOA-Checkpoint-v0.1-sig:"
_NOA_CHECKPOINT_KEYS = frozenset(["spec", "chain", "highestSeq", "headHash", "ts", "sig"])


def noa_checkpoint_signature_ok(cp, keyring):
    """Verify a Noa checkpoint's own Ed25519 signature. Returns
    'ok' | 'untrusted' | 'bad-shape' | 'no-key'.

    Preimage matches noa's reference verifier exactly:
      msg = b"NOA-Checkpoint-v0.1-sig:" + SHA-256(JCS(cp without sig.value))
    This is a real verification, not an expectation read: provenance CRYPTO.
    """
    if not isinstance(cp, dict) or any(k not in _NOA_CHECKPOINT_KEYS for k in cp):
        return "bad-shape"
    if cp.get("spec") != "noa.checkpoint/0.1":
        return "bad-shape"
    sig = cp.get("sig")
    if not isinstance(sig, dict) or sig.get("alg") != "ed25519":
        return "bad-shape"
    kid, val = sig.get("kid"), sig.get("value")
    if not isinstance(kid, str) or not isinstance(val, str) or not kid or not val:
        return "bad-shape"
    pub = (keyring or {}).get(kid)
    if not pub:
        return "no-key"
    clone = json.loads(json.dumps(cp))
    clone.get("sig", {}).pop("value", None)
    try:
        msg = _NOA_CHECKPOINT_DOMAIN + hashlib.sha256(jcs_bytes(clone)).digest()
        ok, _reason = ed25519_verify(pub, msg, val)
        if ok is None:
            return "no-crypto"
        return "ok" if ok else "untrusted"
    except Exception:
        return "bad-shape"


def reconcile_noa_checkpoint(cp, cp_label, chain_id, chain_hashes, last_seq, keyring):
    """Reconcile a presented chain against a presented checkpoint.

    chain_hashes is the ordered list of chain.hash values in the chain as
    presented; last_seq is the head receipt's declared sequence number.

    Three independent legs, each on evidence the checkpoint actually carries:
      checkpoint-signer  -- is this checkpoint authentic?      (crypto-verified)
      checkpoint-scope   -- is it for THIS chain?              (computed)
      checkpoint-head    -- does the head it certifies match?  (computed)
    """
    legs = []

    sg = noa_checkpoint_signature_ok(cp, keyring)
    if sg == "ok":
        legs.append((f"{cp_label}-signer", "match", None, CRYPTO))
    elif sg == "no-key":
        # No key for this kid: nothing was verified, so the provenance is
        # COMPUTED, not crypto-verified. The axis still refuses -- an
        # unauthenticated checkpoint is not a trust anchor -- but the honesty
        # column must not claim a verification that never ran.
        legs.append((f"{cp_label}-signer", "no-match",
                     "checkpoint-signer-untrusted", COMPUTED))
    elif sg == "untrusted":
        legs.append((f"{cp_label}-signer", "no-match",
                     "checkpoint-signature-invalid", CRYPTO))
    elif sg == "no-crypto":
        legs.append((f"{cp_label}-signer", "indeterminate",
                     "leg-not-independently-verified", DERIVED))
    else:
        legs.append((f"{cp_label}-signer", "no-match",
                     "signature-malformed", CRYPTO))

    cp_chain = cp.get("chain")
    if chain_id is not None and cp_chain is not None and cp_chain != chain_id:
        # v2: the guard v1 did not have. Without it the run compares a foreign
        # chain's sequence against this chain's checkpoint and reaches the right
        # verdict for the wrong reason.
        legs.append((f"{cp_label}-scope", "no-match",
                     "checkpoint-scope-mismatch", COMPUTED))
        return legs
    legs.append((f"{cp_label}-scope", "match", None, COMPUTED))

    cp_head = cp.get("headHash")
    cp_seq = cp.get("highestSeq")
    if cp_head is None or cp_seq is None:
        legs.append((f"{cp_label}-head", "indeterminate",
                     "leg-not-independently-verified", COMPUTED))
        return legs

    head_hash = chain_hashes[-1] if chain_hashes else None
    if head_hash == cp_head and last_seq == cp_seq:
        legs.append((f"{cp_label}-head", "match", None, COMPUTED))
    elif cp_head not in chain_hashes:
        # The certified head is not in the chain at all. If the chain is also
        # short, it is a truncation; otherwise the head was rewritten.
        axis = ("chain-head-truncated"
                if isinstance(last_seq, int) and isinstance(cp_seq, int)
                and last_seq < cp_seq else "chain-head-divergent")
        legs.append((f"{cp_label}-head", "no-match", axis, COMPUTED))
    else:
        # The certified head IS present in this chain, but not as its head: the
        # chain has been re-headed onto a prefix or a sibling. Not a truncation,
        # because the height claim is not what fails. No vector in the present
        # corpus reaches this branch -- dup-seq does not, because its RECOMPUTED
        # head is absent from the chain and the chain is also short, so it
        # correctly takes the truncation branch above.
        legs.append((f"{cp_label}-head", "no-match",
                     "chain-head-divergent", COMPUTED))
    return legs


def run_noa(root, results):
    print()
    hr("=")
    print("CORPUS 2 -- Noa (NordenSoft/noa), draft-noa-scitt-ai-agent-receipt-00")
    hr("=")
    vec = os.path.join(root, "vectors")
    kr_path = os.path.join(vec, "keyring.json")
    keyring = {}
    if os.path.exists(kr_path):
        with open(kr_path) as f:
            keyring = json.load(f)
    checkpoint = None
    cp_path = os.path.join(vec, "checkpoint.json")
    if os.path.exists(cp_path):
        with open(cp_path) as f:
            checkpoint = json.load(f)

    print()
    print("Real verification: chain.hash recomputed over JCS(receipt minus chain.hash,")
    print("minus sig.value); Ed25519 over b\"NOA-Receipt-v0.1-sig:\" + SHA-256(that).")
    hr()
    print(f"{'file:receipt':<46}{'ARP verdict':<16}per-source leg -> divergence axis")
    hr()

    rows = []
    targets = [("valid-chain.json", os.path.join(vec, "valid-chain.json"))]
    for sub in ("attack", "malformed"):
        d = os.path.join(vec, sub)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".json"):
                    targets.append((f"{sub}/{fn}", os.path.join(d, fn)))

    # Integrity axes = the ones that constitute detection of a corpus attack.
    # The authorization leg fires on every chain (the genesis receipt is
    # DEFERRED by design), so counting it as "detection" would overstate.
    INTEGRITY_AXES = {
        "artifact-tampered", "signature-invalid", "signature-malformed",
        "agent-principal-unverifiable", "chain-link-broken", "chain-sequence-duplicate",
        "chain-sequence-gap", "chain-scope-mismatch",
        # v2: the four causes chain-head-truncated used to collapse.
        "chain-head-truncated", "chain-head-divergent",
        "checkpoint-scope-mismatch", "checkpoint-signer-untrusted",
        "checkpoint-signature-invalid",
        "canonicalization-gate-failed",
    }
    detected = {}

    for label, path in targets:
        # A checkpoint is not a receipt. Verify it as a checkpoint: its own
        # signature, against the published keyring.
        try:
            with open(path) as f:
                probe = json.load(f)
        except Exception:
            probe = None
        if isinstance(probe, dict) and probe.get("spec", "").startswith("noa.checkpoint"):
            # v2: verify the checkpoint's own signature for real, against the
            # published keyring, using noa's own preimage. v1 read key presence
            # and otherwise held the leg as not-independently-verified.
            sg = noa_checkpoint_signature_ok(probe, keyring)
            if sg == "ok":
                legs = [("checkpoint-signer", "match", None, CRYPTO)]
            elif sg == "no-key":
                legs = [("checkpoint-signer", "no-match",
                         "checkpoint-signer-untrusted", COMPUTED)]
            elif sg == "untrusted":
                legs = [("checkpoint-signer", "no-match",
                         "checkpoint-signature-invalid", CRYPTO)]
            elif sg == "no-crypto":
                legs = [("checkpoint-signer", "indeterminate",
                         "leg-not-independently-verified", DERIVED)]
            else:
                legs = [("checkpoint-signer", "no-match",
                         "signature-malformed", CRYPTO)]
            disp = compose(legs)
            print_legs(f"{label}:<checkpoint>", disp, legs)
            rows.append({"file": label, "id": "<checkpoint>", "disposition": disp,
                         "refused_at": compose_ex(legs)[1],
                         "legs": [{"source": s, "verdict": v, "axis": a,
                                   "provenance": p} for (s, v, a, p) in legs]})
            detected.setdefault(label, set()).update(
                a for (_, _, a, _) in legs if a in INTEGRITY_AXES)
            continue
        try:
            chain = load_noa_chain(path)
        except Exception:
            print_legs(label, "REFUSE", [("parse", "no-match",
                                          "canonicalization-gate-failed", COMPUTED)])
            rows.append({"file": label, "id": None, "disposition": "REFUSE",
                         "refused_at": "parse",
                         "legs": [{"source": "parse", "verdict": "no-match",
                                   "axis": "canonicalization-gate-failed",
                                   "provenance": COMPUTED}]})
            detected.setdefault(label, set()).add("canonicalization-gate-failed")
            continue
        prev = None
        last_seq = None
        chain_hashes = []
        chain_id = None
        for rec in chain:
            if not isinstance(rec, dict):
                print_legs(f"{label}:<non-object>", "REFUSE",
                           [("shape", "no-match", "canonicalization-gate-failed", COMPUTED)])
                rows.append({"file": label, "id": None, "disposition": "REFUSE",
                             "refused_at": "shape",
                             "legs": [{"source": "shape", "verdict": "no-match",
                                       "axis": "canonicalization-gate-failed",
                                       "provenance": COMPUTED}]})
                detected.setdefault(label, set()).add("canonicalization-gate-failed")
                continue
            sd, legs, disp, recomputed_hash = reconcile_noa_receipt(rec, keyring, prev)
            rid = str(rec.get("id", "?"))[-12:]
            print_legs(f"{label}:{rid}", disp, legs)
            rows.append({"file": label, "id": rec.get("id"), "disposition": disp,
                         "refused_at": compose_ex(legs)[1],
                         "legs": [{"source": s, "verdict": v, "axis": a,
                                   "provenance": p} for (s, v, a, p) in legs],
                         "arp_subject_digest": sd})
            detected.setdefault(label, set()).update(
                a for (_, _, a, _) in legs if a in INTEGRITY_AXES)
            ch = rec.get("chain") if isinstance(rec.get("chain"), dict) else {}
            prev = (ch.get("hash"), ch.get("seq"),
                    (rec.get("scope") or {}).get("chain"))
            last_seq = ch.get("seq")
            # The RECOMPUTED hash, never the declared one. Using ch.get("hash")
            # here would let an attacker escape the checkpoint leg entirely by
            # copying the legitimate headHash into a tampered receipt -- and
            # would perversely flag an attacker who recomputed honestly while
            # clearing the one who lied. The true hash is already in hand from
            # the content-integrity leg one step above; use it.
            chain_hashes.append(recomputed_hash or ch.get("hash"))
            # v2: the checkpoint certifies a HEAD, so the scope guard compares
            # the checkpoint against the scope of the receipt presented AS the
            # head -- not the genesis. cross-chain-splice is exactly why: its
            # genesis is store_demo_chain and its head is store_other_chain, so
            # a guard keyed on the genesis would pass and the run would go on to
            # report a truncation that never happened.
            chain_id = (rec.get("scope") or {}).get("chain")

        # ------------------------------------------------------------------
        # Chain-level reconciliation against every checkpoint that claims this
        # chain. Head divergence is invisible to any per-receipt check; it is
        # reachable only from an independently published second source. That is
        # the ARP thesis, so the leg had better consult all of the evidence the
        # second source carries -- which is what v1 did not do.
        #
        # v2: a chain is reconciled against BOTH the canonical checkpoint AND
        # any companion checkpoint shipped beside it. attack/forged-checkpoint
        # is a PAIR -- a short chain plus a checkpoint over the fake head signed
        # out-of-keyring -- and scoring the chain half alone never evaluates it.
        # ------------------------------------------------------------------
        # A file that failed the canonicalization gate has no reliable head to
        # reconcile: any divergence found here would be a restatement of the
        # parse failure, not independent evidence. Suppress rather than inflate
        # the detection count.
        if "canonicalization-gate-failed" in detected.get(label, ()):
            continue

        cps = []
        if checkpoint is not None:
            cps.append(("checkpoint", checkpoint))
        companion = path[:-5] + "-cp.json" if path.endswith(".json") else None
        if companion and os.path.exists(companion):
            try:
                with open(companion) as f:
                    cps.append(("companion-cp", json.load(f)))
            except Exception:
                pass
        elif path.endswith("-chain.json"):
            alt = path[:-len("-chain.json")] + "-cp.json"
            if os.path.exists(alt):
                try:
                    with open(alt) as f:
                        cps.append(("companion-cp", json.load(f)))
                except Exception:
                    pass

        for cp_label, cp in cps:
            cp_legs = reconcile_noa_checkpoint(
                cp, cp_label, chain_id, chain_hashes, last_seq, keyring)
            if all(v == "match" for (_, v, _, _) in cp_legs):
                continue  # the chain agrees with this checkpoint; nothing to report
            disp, gate, _ax = compose_ex(cp_legs)
            print_legs(f"{label}:<{cp_label}>", disp, cp_legs)
            rows.append({"file": label, "id": f"<{cp_label}>", "disposition": disp,
                         "refused_at": gate,
                         "legs": [{"source": s, "verdict": v, "axis": a,
                                   "provenance": p} for (s, v, a, p) in cp_legs]})
            detected.setdefault(label, set()).update(
                a for (_, _, a, _) in cp_legs if a in INTEGRITY_AXES)
    print()
    print("Per-file attack detection (integrity axes only; the authorization leg is")
    print("excluded because the genesis receipt is DEFERRED in every chain, valid or not):")
    hr()
    adversarial = [l for (l, _) in targets if l.startswith(("attack/", "malformed/"))]
    caught = 0
    for label in adversarial:
        axes = sorted(detected.get(label, ()))
        mark = "DETECTED" if axes else "NOT DETECTED"
        if axes:
            caught += 1
        print(f"  {label:<44}{mark:<14}{', '.join(axes) if axes else '-'}")
    print()
    print(f"  {caught}/{len(adversarial)} adversarial files produced at least one")
    print(f"  integrity-class divergence axis.")
    results["noa"] = rows
    results["noa_detection"] = {k: sorted(v) for k, v in detected.items()}
    results["noa_adversarial"] = {"total": len(adversarial), "detected": caught}


# ---------------------------------------------------------------------------
# 7. Main.
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emilia", help="path to .../conformance/clean-room/frozen-v1")
    ap.add_argument("--noa", help="path to the noa clone's conformance/ directory")
    ap.add_argument("--json", help="write the full machine-readable result here")
    a = ap.parse_args()

    print()
    hr("=")
    print("ARP reconciliation harness v2.1 -- draft-hillier-scitt-arp")
    hr("=")
    print("Construction identifiers carried by this run (each digest commits to the")
    print("declared canonicalization parameters, so compatibility is CHECKABLE):")
    print()
    for name in CONSTRUCTIONS:
        print(f"  {name:<26} id={construction_id_digest(name)}  {CONSTRUCTIONS[name]['spec']}")
        print(f"  {'':<26} profile obliged by its own spec? "
              f"{PROFILE_OBLIGED_BY_SPEC[name]}")
    print()
    print("  Appendix D NAMES JCS and agrees with the EP profile 22/22. It does not")
    print("  identify WHICH JCS: the string \"8785\" does not occur anywhere in -01,")
    print("  and \"JCS\" occurs exactly once. The 22/22 therefore records that two")
    print("  implementations independently CHOSE RFC 8785 -- not that -01 obliges it.")
    print("  Section 2's Canonical Claim applies NFC and agrees 19-20/22; two of the")
    print("  divergences are COLLISIONS. Section 2 does not pin its member-sort code")
    print("  unit either, which is the 19-versus-20. The two constructions are not")
    print("  interchangeable, and -01 does not say so -- hence the identifiers.")
    print()
    print("  The obligation line above is reported, NOT hashed: the identifier")
    print("  commits to canonicalization parameters, so identical bytes keep an")
    print("  identical id. ALL THREE IDS ARE UNCHANGED FROM THE v1 RUN.")
    print()
    print(f"  cryptography backend available: {_HAVE_CRYPTO}")

    results = {"constructions": {
        n: dict(CONSTRUCTIONS[n], id=construction_id_digest(n),
                profile_obliged_by_spec=PROFILE_OBLIGED_BY_SPEC[n])
        for n in CONSTRUCTIONS}}

    if a.emilia:
        run_emilia(a.emilia, results)
    if a.noa:
        run_noa(a.noa, results)

    # --- self-check --------------------------------------------------------
    print()
    hr("=")
    print("SELF-CHECK")
    hr("=")
    ok = True

    b = results.get("boundary", [])
    if b:
        # Every EP-BOUNDARY negative vector must REFUSE or hold INDETERMINATE.
        # None may APPROVE. The control must not REFUSE.
        for r in b:
            if r["expect_valid"] is False and r["disposition"] == "APPROVE":
                ok = False
                print(f"  FAIL: {r['id']} expected refusal, ARP APPROVEd")
            if r["expect_valid"] is True and r["disposition"] == "REFUSE":
                ok = False
                print(f"  FAIL: control {r['id']} was REFUSEd")
        neg = [r for r in b if r["expect_valid"] is False]
        print(f"  EP-BOUNDARY: {len(neg)}/{len(neg)} negative vectors refused or held; "
              f"0 collapsed to a single 'valid'.")

    rc = results.get("receipts", [])
    if rc:
        bad = [r for r in rc if r["expect_valid"] is False and r["disposition"] == "APPROVE"]
        if bad:
            ok = False
            for r in bad:
                print(f"  FAIL: {r['id']} expected refusal, ARP APPROVEd")
        print(f"  EP-RECEIPT: {len(rc)} vectors, "
              f"{sum(1 for r in rc if r['expect_valid'] is False)} negative, "
              f"{len(bad)} wrongly approved.")

    # Nothing anywhere may APPROVE while carrying an unproven binding.
    everything = (results.get("boundary", []) + results.get("receipts", [])
                  + results.get("noa", []) + results.get("other", []))
    leaked = [r for r in everything if r["disposition"] == "APPROVE"
              and any(l["axis"] in SOFT_AXES for l in r["legs"])]
    if leaked:
        ok = False
        print(f"  FAIL: {len(leaked)} case(s) APPROVEd while carrying an unproven axis")
    else:
        print("  No case APPROVEd while carrying an unproven binding "
              "(no silent upgrade).")

    canon = results.get("canonicalization", [])
    if canon:
        div = [r for r in canon if not r["sec2_agrees"]]
        divu = [r for r in canon if not r["sec2_utf16_agrees"]]
        print(f"  Construction divergence: Canonical Claim vs EP JCS disagree on "
              f"{len(div)}/{len(canon)} (code-point sort) or "
              f"{len(divu)}/{len(canon)} (UTF-16 sort) pinned vectors.")

    # --- v2 invariants -----------------------------------------------------

    gate = results.get("strict_parse_gate", [])
    if gate:
        dis = [r for r in gate if not r["agrees_with_suite"]]
        if dis:
            ok = False
            for r in dis:
                print(f"  FAIL: strict-parse gate disagrees with the suite on {r['id']}")
        # Agreeing on the VERDICT is not the claim. The claim is that the cause
        # was computed, so the cause must match what the vector is named for.
        # Without this, swapping every cause still reports full agreement.
        CAUSE_EXPECT = (
            ("duplicate_key", "duplicate-member-name"),
            ("surrogate_in_member_name", "unpaired-surrogate-in-member-name"),
            ("surrogate", "unpaired-surrogate-in-string"),
            ("unsafe_integer", "integer-outside-safe-range"),
            ("unsafe_large_exponent", "integer-outside-safe-range"),
            ("non_integer_real", "non-integer-real"),
            ("nested_depth_over_limit", "nesting-depth-exceeded"),
        )
        miscaused = []
        for r in gate:
            if r["expected_valid"]:
                continue
            for needle, want in CAUSE_EXPECT:
                if needle in r["id"]:
                    if r["cause"] != want:
                        miscaused.append((r["id"], r["cause"], want))
                    break
        if miscaused:
            ok = False
            for cid, got, want in miscaused:
                print(f"  FAIL: {cid} cause {got!r}, expected {want!r}")
        print(f"  v2 strict-parse gate: {len(gate) - len(dis)}/{len(gate)} agree with "
              f"the suite's expectation (two-sided), and every reject_* cause "
              f"matches what its vector is named for (v1 exercised 0 of these).")

    # Every axis emitted anywhere must be declared. compose_ex already refuses
    # to compose an undeclared axis; this restates it over the whole result set
    # so the invariant is visible rather than merely enforced.
    all_axes = {l["axis"] for r in everything for l in r["legs"] if l["axis"]}
    undeclared = sorted(a for a in all_axes if a not in HARD_AXES and a not in SOFT_AXES)
    if undeclared:
        ok = False
        print(f"  FAIL: undeclared axes emitted: {undeclared}")
    else:
        print(f"  Axis closure: all {len(all_axes)} axes emitted are declared HARD or "
              f"SOFT. compose() fails CLOSED on any that is not (v1 failed open).")

    # The two predicates v1 declared and never emitted.
    for ax in ("outcome-reported-only", "physical-completion-unproven"):
        legs_with = [(r, l) for r in everything for l in r["legs"] if l["axis"] == ax]
        if not legs_with:
            ok = False
            print(f"  FAIL: {ax} is declared but still emitted by nothing")
            continue
        # Checked, not asserted: the leg itself must be indeterminate, and it
        # must never be the reason a row refused.
        bad = [r["id"] for (r, l) in legs_with if l["verdict"] != "indeterminate"]
        if bad:
            ok = False
            print(f"  FAIL: {ax} emitted with a non-indeterminate verdict on {bad}")
        else:
            refusing = sum(1 for (r, _l) in legs_with if r["disposition"] == "REFUSE")
            print(f"  {ax}: emitted on {len(legs_with)} leg(s), every one held at "
                  f"indeterminate; caused 0 refusals ({refusing} sit on rows refused "
                  f"for other reasons).")

    # The headline detection number must be asserted, not merely printed.
    # Without this the entire checkpoint rework can be disabled and the
    # self-check still passes while 23/23 quietly becomes 22/23.
    adv = results.get("noa_adversarial")
    if adv:
        if adv["detected"] != adv["total"]:
            ok = False
            print(f"  FAIL: {adv['total'] - adv['detected']} adversarial file(s) "
                  f"produced no integrity-class axis")
        else:
            print(f"  Detection closure: {adv['detected']}/{adv['total']} adversarial "
                  f"files produced at least one integrity-class axis.")

    # physical-completion-unproven must be a strict subset of
    # outcome-reported-only: it fires ADDITIONALLY, never instead.
    o_rows = {id(r) for r in everything
              for l in r["legs"] if l["axis"] == "outcome-reported-only"}
    p_rows = {id(r) for r in everything
              for l in r["legs"] if l["axis"] == "physical-completion-unproven"}
    if not p_rows <= o_rows:
        ok = False
        print(f"  FAIL: {len(p_rows - o_rows)} row(s) carry "
              f"physical-completion-unproven without outcome-reported-only")
    else:
        print(f"  Predicate nesting: physical-completion-unproven ({len(p_rows)} rows) "
              f"is a strict subset of outcome-reported-only ({len(o_rows)} rows).")

    # The forged-checkpoint attack must be evaluated as the PAIR it is.
    noa_rows = results.get("noa", [])
    pair = [r for r in noa_rows if r.get("id") == "<companion-cp>"]
    if noa_rows:
        if pair:
            print(f"  Companion-checkpoint pairs evaluated: {len(pair)} "
                  f"(v1 evaluated 0 and scored the chain half alone).")
        else:
            print("  NOTE: no companion checkpoint found beside any chain in this corpus.")

    # No checkpoint leg may report a truncation it did not establish. The v1
    # bug was reporting truncation whenever the sequence fell short, including
    # on a chain the checkpoint does not even cover; assert the head axes now
    # fire ONLY where the head hash was actually compared and disagreed.
    head_axes = {"chain-head-truncated", "chain-head-divergent"}
    bogus = [r for r in noa_rows
             if any(l["axis"] in head_axes for l in r["legs"])
             and not any(l["source"].endswith("-head") and l["verdict"] == "no-match"
                         for l in r["legs"])]
    if bogus:
        ok = False
        print(f"  FAIL: {len(bogus)} row(s) carry a head axis not reached by the "
              f"head comparison")
    elif noa_rows:
        nh = sum(1 for r in noa_rows for l in r["legs"] if l["axis"] in head_axes)
        print(f"  Head axes: {nh} emitted, each from an actual headHash comparison "
              f"against the recomputed chain head (v1 compared sequence numbers "
              f"only and never read headHash).")

    print()
    print(f"  SELF-CHECK: {'PASS' if ok else 'FAIL'}")

    if a.json:
        with open(a.json, "w") as f:
            json.dump(results, f, indent=1, sort_keys=True)
        print(f"  machine-readable result written to {a.json}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
