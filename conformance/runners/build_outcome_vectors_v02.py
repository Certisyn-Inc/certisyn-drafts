#!/usr/bin/env python3
"""Build arp-outcome-vectors-v0.2.json.

v0.1 shipped four vectors whose action object was

    {"action_type": "payment.release.1",
     "amount": "10.00", "currency": "USD", "destination": "acct:demo"}

That object is NOT a conforming instance of the registered CAID type
payment.release.1. The registry entry requires four material fields --
amount, currency, beneficiary_account, payment_instruction_id -- and my
object carried two of them plus an unregistered field named `destination`.
Run against the CAID reference issuer it does not produce a weak identifier;
it produces no identifier at all:

    {"refusals": ["missing_material_field:beneficiary_account",
                  "missing_material_field:payment_instruction_id"]}

which is the registry working exactly as designed. The vectors still
exercised the two outcome axes correctly, because those axes read the
RECORD and not the action; but the action object could not have been joined
on a CAID by any conforming party, so the vectors could not have been run
end to end against a CAID-issuing implementation.

v0.2 fixes it in the only way worth doing:

  1. All four vectors carry a registry-conforming action object. It is the
     SAME object in all four, so the record remains the only variable.
  2. A fifth vector is added -- reject_underspecified_action_object -- which
     pins the v0.1 shape as a NEGATIVE control with the two refusal codes
     the reference issuer emits. The defect becomes a test.

Everything below is computed, never transcribed.
"""

import argparse
import base64
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--caid-repo", required=True,
                 help="path to a checkout of github.com/emiliaprotocol/emilia-protocol "
                      "at the pinned commit")
_ap.add_argument("--out", default=os.path.join(HERE, "..", "vectors", "arp-outcome-vectors-v0.2.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.caid_repo, "caid", "impl", "python"))

import arp_reconcile as arp          # noqa: E402
import caid as C                     # noqa: E402

REGISTRY = os.path.join(ARGS.caid_repo, "caid", "registry", "action-types.json")
_reg = json.load(open(REGISTRY))
DEFS = _reg["types"]
OPT = {"suite": "jcs-sha256", "definitions": DEFS}

ACCOUNT = "acct:demo"

ACTION = {
    "action_type": "payment.release.1",
    "amount": "10.00",
    "currency": "USD",
    "beneficiary_account": "sha256:" + hashlib.sha256(ACCOUNT.encode()).hexdigest(),
    "payment_instruction_id": "pi_demo_0001",
}

ACTION_V01 = {
    "action_type": "payment.release.1",
    "amount": "10.00",
    "currency": "USD",
    "destination": ACCOUNT,
}


def issue(obj):
    return C.compute_caid(obj, OPT)


def arp_subject_digest(obj):
    return hashlib.sha256(arp.jcs_bytes(obj)).hexdigest()


def caid_from_digest(action_type, digest_hex):
    raw = base64.urlsafe_b64encode(bytes.fromhex(digest_hex)).decode().rstrip("=")
    return f"caid:1:{action_type}:jcs-sha256:{raw}"


# --- the cross-check, run here so the file cannot ship a stale value -------
issued = issue(ACTION)
assert "caid" in issued, issued
SD = arp_subject_digest(ACTION)
CAID = caid_from_digest(ACTION["action_type"], SD)
assert issued["digest"] == "sha256:" + SD, (issued["digest"], SD)
assert issued["caid"] == CAID, (issued["caid"], CAID)
assert C.verify_caid(ACTION, CAID, {"definitions": DEFS})["valid"] is True
CLAIM_HASH = arp.claim_hash(ACTION)
JCS = arp.jcs_bytes(ACTION).decode("utf-8")

refused = issue(ACTION_V01)
assert "caid" not in refused and refused["refusals"], refused
REFUSALS = refused["refusals"]


def vec(vid, record, axes, comment=None, extra=None):
    v = {"id": vid}
    if comment:
        v["comment"] = comment
    v["action"] = ACTION
    v["caid"] = CAID
    v["record"] = record
    v["expect"] = {
        "arp_disposition": "INDETERMINATE",
        "axes": axes,
        "admission_effect": "UNCHANGED",
        "post_effect_reconciliation": "REQUIRED",
    }
    if extra:
        v["expect"].update(extra)
    return v


VECTORS = [
    vec("accept_outcome_reported_only",
        {"verdict": "EXECUTED", "reversible": True, "rollback_ref": None,
         "attestors": ["actor"]},
        ["outcome-reported-only"]),

    vec("accept_physical_completion_unproven",
        {"verdict": "EXECUTED", "reversible": False, "rollback_ref": None,
         "attestors": ["actor"]},
        ["outcome-reported-only", "physical-completion-unproven"]),

    vec("reject_approver_treated_as_outcome_corroboration",
        {"verdict": "EXECUTED", "reversible": False, "rollback_ref": None,
         "attestors": ["actor"],
         "approval": {"by": "HUMAN:reviewer-1", "at": "2026-07-27T00:00:00Z"}},
        ["outcome-reported-only", "physical-completion-unproven"],
        comment=("Negative control. An ex ante human approval MUST NOT clear "
                 "either axis. An approval establishes that the act was "
                 "PERMITTED; corroborating an outcome requires an attestation "
                 "that it OCCURRED. A conformant implementation still holds at "
                 "INDETERMINATE here.")),

    vec("accept_outcome_corroborated_clears_both",
        {"verdict": "EXECUTED", "reversible": False,
         "rollback_ref": None,
         "attestors": ["actor", "settlement-observer"],
         "ex_post_attestation": {
             "by": "settlement-observer",
             "over_subject_digest": "sha256:" + SD,
             "at": "2026-07-27T01:00:00Z"}},
        [],
        comment=("Positive control. The axes must be falsifiable rather than "
                 "always-on. An ex post attestation over the SAME subject "
                 "digest, from a party other than the actor, clears both."),
        extra={"arp_disposition": "APPROVE",
               "post_effect_reconciliation": "NOT_REQUIRED"}),
]

# --- vector 5: the v0.1 defect, pinned as a control -----------------------
VECTORS.append({
    "id": "reject_underspecified_action_object",
    "comment": (
        "Negative control ADDED IN v0.2, and it is this file's own former "
        "defect. The action object below is exactly what ARP-OUTCOME-VECTORS "
        "v0.1 shipped in all four of its vectors. It is not a conforming "
        "instance of the registered type payment.release.1: it omits two of "
        "the four required material fields and carries an unregistered field "
        "`destination` in their place. A conforming CAID issuer MUST refuse "
        "it and emit NO identifier. The refusal codes below are the literal "
        "output of the CAID reference implementation, not a transcription. "
        "The point of the vector is that there is nothing to join on: an "
        "implementation that produced a payment.release.1 CAID for this "
        "object would be minting an identifier for an underspecified action, "
        "which is the failure the registry exists to prevent."),
    "action": ACTION_V01,
    "caid": None,
    "record": {"verdict": "EXECUTED", "reversible": False,
               "rollback_ref": None, "attestors": ["actor"]},
    "expect": {
        "caid_issuance": "REFUSED",
        "caid_refusals": REFUSALS,
        "arp_disposition": "INDETERMINATE",
        "axes": ["caid-binding-unverified"],
        "admission_effect": "UNCHANGED",
        "post_effect_reconciliation": "REQUIRED",
        "note": ("ARP holds rather than refuses. An unissuable identifier is "
                 "an absence of evidence, not evidence of tampering. "
                 "caid-binding-unverified is a SOFT axis in ARP and never "
                 "produces a REFUSE."),
    },
})

DOC = {
    "@version": "ARP-OUTCOME-VECTORS-v0.2",
    "status": "proposed-for-shared-set",
    "supersedes": "ARP-OUTCOME-VECTORS-v0.1",
    "supersession_reason": (
        "v0.1's action object was not a conforming instance of the registered "
        "CAID type payment.release.1. Independently flagged by two reviewers. "
        "v0.2 makes all four action objects registry-conforming and adds the "
        "v0.1 shape back as a fifth vector, a negative control."),
    "construction": {
        "id": "ep-arp-reconciliation-join/0.2",
        "arp_subject_digest_profile": "arp-subject-digest/1",
        "arp_subject_digest_profile_id": arp.construction_id_digest("arp-subject-digest/1"),
        "caid_suite": "jcs-sha256",
        "caid_action_type_registry": {
            "registry": _reg["meta"]["registry"],
            "registry_version": _reg["meta"]["registry_version"],
            "updated": _reg["meta"]["updated"],
        },
        "rule": (
            "Both outcome axes are SOFT in ARP: they HOLD a verdict at "
            "INDETERMINATE and never produce a REFUSE. Neither is a "
            "reconciliation failure; both are statements about what the "
            "artefact does not establish."),
        "digest_coincidence": (
            "For this action object, arp-subject-digest/1 and the CAID "
            "jcs-sha256 digest are byte-identical, computed independently by "
            "two implementations. That is a property of THIS input, not a "
            "general equivalence: both are SHA-256 over an RFC 8785 "
            "serialisation and this object has no member name outside the "
            "BMP and no string whose normalization form differs. ARP's "
            "Section 2 Canonical Claim applies NFC and would diverge on an "
            "input where those conditions do not hold."),
    },
    "pinned": {
        "action": ACTION,
        "canonical_jcs_utf8": JCS,
        "arp_subject_digest": "sha256:" + SD,
        "arp_canonical_claim_hash": "sha256:" + CLAIM_HASH,
        "caid": CAID,
        "caid_reference_impl_digest": issued["digest"],
        "caid_reference_impl_agrees": issued["caid"] == CAID,
        "caid_verify_valid": C.verify_caid(ACTION, CAID, {"definitions": DEFS})["valid"],
    },
    "axes": [
        {
            "axis": "outcome-reported-only",
            "class": "indeterminate",
            "predicate": ("The record asserts that an action was EXECUTED, and "
                          "the only attesting party is the one that acted."),
            "clears_on": ("An ex post attestation, over the same subject "
                          "digest, from a party other than the actor."),
            "does_not_clear_on": ("A named human approver. Approval is ex ante "
                                  "and establishes that the act was permitted, "
                                  "not that it occurred."),
            "implementation": "arp_reconcile.py v2.1, leg source 'outcome'.",
        },
        {
            "axis": "physical-completion-unproven",
            "class": "indeterminate",
            "predicate": ("As above, and the action is declared irreversible "
                          "with no rollback reference, so the assertion "
                          "concerns an effect outside the attestation system "
                          "and nothing in the artefact can settle it."),
            "relation": ("Fires ADDITIONALLY to outcome-reported-only, never "
                         "instead of it. A strict subset."),
            "clears_on": ("A settlement or delivery attestation from the party "
                          "that observed the effect."),
            "implementation": "arp_reconcile.py v2.1, leg source 'completion'.",
        },
        {
            "axis": "caid-binding-unverified",
            "class": "indeterminate",
            "predicate": ("No CAID could be issued or verified for the action, "
                          "so there is no join key. Reached in v0.2 by "
                          "reject_underspecified_action_object."),
            "clears_on": "A CAID that issues and verifies under a pinned type definition.",
            "implementation": "arp_reconcile.py v2.1, leg source 'caid-binding'.",
        },
    ],
    "vectors": VECTORS,
}

out = ARGS.out
with open(out, "w") as f:
    json.dump(DOC, f, indent=2, sort_keys=False)
    f.write("\n")

print("wrote", out)
print("caid                :", CAID)
print("arp subject digest  : sha256:" + SD)
print("claim hash (NFC)    : sha256:" + CLAIM_HASH)
print("v0.1 refusals       :", REFUSALS)
print("sha256(file)        :", hashlib.sha256(open(out, "rb").read()).hexdigest())
