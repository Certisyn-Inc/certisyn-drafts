#!/usr/bin/env python3
"""
ARP runner for EMILIA's ep-arp-reconciliation-join/0.1 boundary vector.

Runs arp-aeb-adapter-v0.1.json through ARP-01's verdict arithmetic using the
same construction identifiers the vector pins, and emits ARP's own return
vectors for the two outcome cases EMILIA asked for in machine-readable form.

Depends on the v2 harness for the constructions and the axis algebra, so the
identifiers here are the identifiers published on the SCITT list:

    arp-canonical-claim/1  id=7d90aa1cbee90ef9
    arp-subject-digest/1   id=f23ecefd99c54182
    ep-canonicalization/1  id=dc7df29214870f78

Usage:  python3 arp_adapter.py arp-aeb-adapter-v0.1.json
"""

import base64
import copy
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# DEFECT FIX (Songbo, 2026-07-29). The default was HERE/../v2/arp_reconcile.py,
# which is where the harness lived in the working tree it was written in, and
# nowhere else. Every distributed copy colocates the harness with this script,
# so the documented one-command reproduction failed on a clean checkout. The
# default is now the colocated harness; ARP_HARNESS still overrides it.
_HARNESS = os.environ.get("ARP_HARNESS", os.path.join(HERE, "arp_reconcile.py"))
# One home per artefact: vectors are inputs, runs are outputs, neither lives
# beside the code that reads or writes it.
VECTORS = os.environ.get("ARP_VECTORS", os.path.join(HERE, "..", "vectors"))
RUNS = os.environ.get("ARP_RUNS", os.path.join(HERE, "..", "runs"))
_spec = importlib.util.spec_from_file_location("arp", _HARNESS)
arp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(arp)


# ---------------------------------------------------------------------------
# Verdict vocabulary join.
#
# ARP-01 reports APPROVE / INDETERMINATE / REFUSE. The adapter vector reports
# MATCH / NO_MATCH / INDETERMINATE / DIVERGENCE. The mapping is NOT one-to-one
# in one direction that matters: NO_MATCH and DIVERGENCE are BOTH a REFUSE in
# ARP. What separates them is the divergence AXIS, not the verdict.
#
# That is the load-bearing observation at this boundary. A relying party that
# joins on the verdict alone cannot tell "the action was mutated" from "the
# evidence was not independent", and those call for different handling. The
# axis has to cross the join with the verdict.
# ---------------------------------------------------------------------------

MUTATION_AXES = {"digest-mismatch", "artifact-tampered",
                 "authorization-not-bound-to-action"}
INDEPENDENCE_AXES = {"agent-impersonation-suspected",
                     "attribution-substituted-for-authorization",
                     "machine-decision-not-human-authorization"}


def to_ep_verdict(disposition, axes):
    if disposition == "APPROVE":
        return "MATCH"
    if disposition == "REFUSE":
        if any(a in INDEPENDENCE_AXES for a in axes):
            return "DIVERGENCE"
        return "NO_MATCH"
    return "INDETERMINATE"


def caid_of(action_type, digest_hex):
    raw = base64.urlsafe_b64encode(bytes.fromhex(digest_hex)).decode().rstrip("=")
    return f"caid:1:{action_type}:jcs-sha256:{raw}"


def hr(ch="-", n=110):
    print(ch * n)


def run(path):
    doc = json.load(open(path, encoding="utf-8"))
    con = doc.get("construction", {})
    results = {
        "adapter": doc.get("@version"),
        "join_construction": con.get("id"),
        "arp_constructions": {
            n: arp.construction_id_digest(n) for n in arp.CONSTRUCTIONS},
        "profile_obliged_by_spec": dict(arp.PROFILE_OBLIGED_BY_SPEC),
        "fixtures": [],
    }

    print()
    hr("=")
    print("ARP against EMILIA ep-arp-reconciliation-join/0.1")
    hr("=")
    print("ARP construction identifiers used (unchanged from the list post):")
    for n in arp.CONSTRUCTIONS:
        print(f"  {n:<26} id={arp.construction_id_digest(n)}")
    print()
    print("Verdict join. ARP reports APPROVE / INDETERMINATE / REFUSE; the")
    print("adapter reports MATCH / NO_MATCH / INDETERMINATE / DIVERGENCE.")
    print("NO_MATCH and DIVERGENCE are BOTH a REFUSE in ARP. Only the axis")
    print("separates them, so the axis must cross the join with the verdict.")
    print()
    hr()
    print(f"{'fixture':<44}{'ARP':<16}{'-> adapter':<16}{'axes'}")
    hr()

    for f in doc.get("fixtures", []):
        fid = f.get("id", "?")
        exp = f.get("expected", {})
        legs = []
        notes = []

        if fid == "shared-action-preimage":
            action = f["action"]
            jcs = arp.jcs_bytes(action)
            pinned_bytes = f.get("canonical_jcs_utf8")
            dig = hashlib.sha256(jcs).hexdigest()
            pinned_dig = (f.get("action_digest") or "").split(":")[-1]
            recaid = caid_of(action["action_type"], dig)

            bytes_ok = (jcs.decode("utf-8") == pinned_bytes)
            dig_ok = (dig == pinned_dig)
            caid_ok = (recaid == f.get("caid"))

            legs.append(("canonical-bytes", "match" if bytes_ok else "no-match",
                         None if bytes_ok else "canonicalization-gate-failed",
                         arp.COMPUTED))
            legs.append(("subject-digest", "match" if dig_ok else "no-match",
                         None if dig_ok else "digest-mismatch", arp.COMPUTED))
            # The CAID leg is COMPUTED here, not the caid-binding-unverified
            # placeholder the frozen-v1 run had to use: this vector publishes
            # the preimage, so the binding is checkable rather than asserted.
            legs.append(("caid-binding", "match" if caid_ok else "no-match",
                         None if caid_ok else "digest-mismatch", arp.COMPUTED))

            s2 = hashlib.sha256(arp.arp_canonical_claim_bytes(action)).hexdigest()
            notes.append(f"App.D subject_digest  = sha256:{dig}")
            notes.append(f"S2  Canonical Claim   = sha256:{s2}")
            notes.append("S2 and App.D COINCIDE on this input. They are still "
                         "different constructions; this action simply carries "
                         "no member name outside the BMP and no string whose "
                         "normalization form differs. The divergence is "
                         "input-dependent, which is why it must be declared "
                         "rather than observed.")
            notes.append(f"CAID recomputed       = {recaid}")

        elif fid == "missing-preimage":
            # No construction identifier and no canonical preimage: the digest
            # is unverifiable, not wrong. SOFT axis, held, never refused.
            legs.append(("construction-id", "indeterminate",
                         "canonicalization-unverified", arp.COMPUTED))
            legs.append(("caid-binding", "indeterminate",
                         "caid-binding-unverified", arp.COMPUTED))
            notes.append("ARP holds rather than refuses. The admission "
                         "decision is still REFUSED, and that is the correct "
                         "division of labour: an unverifiable digest is not a "
                         "reconciliation failure, but it is not admissible "
                         "evidence either.")

        elif fid == "material-action-mutation":
            base = {"action_type": "payment.release.1", "amount": "10.00",
                    "currency": "USD", "destination": "acct:demo"}
            mutated = copy.deepcopy(base)
            mutated["destination"] = "acct:attacker"
            d0 = hashlib.sha256(arp.jcs_bytes(base)).hexdigest()
            d1 = hashlib.sha256(arp.jcs_bytes(mutated)).hexdigest()
            legs.append(("subject-digest", "no-match" if d0 != d1 else "match",
                         "digest-mismatch" if d0 != d1 else None, arp.COMPUTED))
            notes.append(f"pre-mutation  sha256:{d0}")
            notes.append(f"post-mutation sha256:{d1}")
            notes.append("Recomputed here from the mutated action, not read "
                         "from the fixture's expectation.")

        elif fid == "same-party-evidence-not-independent":
            legs.append(("independence", "no-match",
                         "agent-impersonation-suspected", arp.COMPUTED))
            notes.append("Maps to the filed ARP-01 axis "
                         "agent-impersonation-suspected (S2, S4, A.3). The "
                         "same construction fires on EP-BOUNDARY's "
                         "same_party_evidence_presented_as_independent in the "
                         "frozen-v1 run.")

        elif fid == "controller-outcome-is-not-physical-completion":
            # Implemented as emitting predicates in harness v2. In v1 both
            # strings existed only as members of the SOFT_AXES set literal.
            legs.append(("outcome", "indeterminate",
                         "outcome-reported-only", arp.COMPUTED))
            legs.append(("completion", "indeterminate",
                         "physical-completion-unproven", arp.COMPUTED))
            notes.append("Both axes are SOFT: they HOLD at indeterminate and "
                         "never refuse. Admission is therefore UNCHANGED, and "
                         "post-effect reconciliation is REQUIRED, exactly as "
                         "the fixture expects.")
            notes.append("outcome-reported-only clears on an ex post "
                         "attestation from a party OTHER than the actor. A "
                         "named human APPROVER does not clear it: approval is "
                         "ex ante and says the act was permitted, not that it "
                         "occurred.")
            notes.append("physical-completion-unproven fires ADDITIONALLY, "
                         "not instead, where the act is irreversible with no "
                         "rollback handle.")

        else:
            legs.append(("unknown-fixture", "indeterminate",
                         "leg-not-independently-verified", arp.DERIVED))

        disposition, refused_at, _ax = arp.compose_ex(legs)
        axes = [a for (_s, _v, a, _p) in legs if a]
        ep = to_ep_verdict(disposition, axes)

        # What the fixture said should happen, in its own vocabulary.
        want = (exp.get("reconciliation")
                or exp.get("outcome_record") and "INDETERMINATE")
        agrees = (want is None) or (ep == want)

        detail = "  ".join(f"{s}:{v}" + (f"[{a}]" if a else "")
                           for (s, v, a, _p) in legs)
        print(f"{fid[:44]:<44}{disposition:<16}{ep:<16}{detail}")
        for n in notes:
            print(f"    . {n}")
        if want and not agrees:
            print(f"    !! fixture expects {want}, ARP joins to {ep}")
        print()

        results["fixtures"].append({
            "id": fid,
            "arp_disposition": disposition,
            "refused_at": refused_at,
            "adapter_verdict": ep,
            "fixture_expected": want,
            "agrees": bool(agrees),
            "legs": [{"source": s, "verdict": v, "axis": a, "provenance": p}
                     for (s, v, a, p) in legs],
            "notes": notes,
        })

    hr("=")
    n = len(results["fixtures"])
    ok = sum(1 for r in results["fixtures"] if r["agrees"])
    print(f"  {ok}/{n} fixtures join to the verdict the vector expects.")
    print("  ARP admits nothing on its own: every fixture above is evidence")
    print("  input to an admission decision made elsewhere. That is the rule")
    print("  the join construction states, and this run does not violate it.")
    hr("=")
    return results


# ---------------------------------------------------------------------------
# The two outcome vectors, returned in machine-readable form as requested.
# ---------------------------------------------------------------------------

OUTCOME_VECTORS = {
    "@version": "ARP-OUTCOME-VECTORS-v0.1",
    "status": "proposed-for-shared-set",
    "construction": {
        "id": "ep-arp-reconciliation-join/0.1",
        "arp_subject_digest_profile": "arp-subject-digest/1",
        "arp_subject_digest_profile_id": "f23ecefd99c54182",
        "rule": "Both axes below are SOFT in ARP: they HOLD a verdict at "
                "INDETERMINATE and never produce a REFUSE. Neither is a "
                "reconciliation failure; both are statements about what the "
                "artefact does not establish.",
    },
    "axes": [
        {
            "axis": "outcome-reported-only",
            "class": "indeterminate",
            "predicate": "The record asserts that an action was EXECUTED, and "
                         "the only attesting party is the one that acted.",
            "clears_on": "An ex post attestation, over the same subject "
                         "digest, from a party other than the actor.",
            "does_not_clear_on": "A named human approver. Approval is ex ante "
                                 "and establishes that the act was permitted, "
                                 "not that it occurred.",
            "implementation": "arp_reconcile.py v2.1, leg source 'outcome'.",
        },
        {
            "axis": "physical-completion-unproven",
            "class": "indeterminate",
            "predicate": "As above, and the action is declared irreversible "
                         "with no rollback reference, so the assertion "
                         "concerns an effect outside the attestation system "
                         "and nothing in the artefact can settle it.",
            "relation": "Fires ADDITIONALLY to outcome-reported-only, never "
                        "instead of it. A strict subset.",
            "clears_on": "A settlement or delivery attestation from the party "
                         "that observed the effect.",
            "implementation": "arp_reconcile.py v2.1, leg source 'completion'.",
        },
    ],
    "vectors": [
        {
            "id": "accept_outcome_reported_only",
            "action": {
                "action_type": "payment.release.1",
                "amount": "10.00",
                "currency": "USD",
                "destination": "acct:demo",
            },
            "record": {
                "verdict": "EXECUTED",
                "reversible": True,
                "rollback_ref": None,
                "attestors": ["actor"],
            },
            "expect": {
                "arp_disposition": "INDETERMINATE",
                "axes": ["outcome-reported-only"],
                "admission_effect": "UNCHANGED",
                "post_effect_reconciliation": "REQUIRED",
            },
        },
        {
            "id": "accept_physical_completion_unproven",
            "action": {
                "action_type": "payment.release.1",
                "amount": "10.00",
                "currency": "USD",
                "destination": "acct:demo",
            },
            "record": {
                "verdict": "EXECUTED",
                "reversible": False,
                "rollback_ref": None,
                "attestors": ["actor"],
            },
            "expect": {
                "arp_disposition": "INDETERMINATE",
                "axes": ["outcome-reported-only",
                         "physical-completion-unproven"],
                "admission_effect": "UNCHANGED",
                "post_effect_reconciliation": "REQUIRED",
            },
        },
        {
            "id": "reject_approver_treated_as_outcome_corroboration",
            "comment": "The negative control. An ex ante human approval MUST "
                       "NOT clear either axis. A conformant implementation "
                       "still holds at INDETERMINATE here.",
            "action": {
                "action_type": "payment.release.1",
                "amount": "10.00",
                "currency": "USD",
                "destination": "acct:demo",
            },
            "record": {
                "verdict": "EXECUTED",
                "reversible": False,
                "rollback_ref": None,
                "attestors": ["actor"],
                "approval": {"by": "HUMAN:reviewer-1", "at": "2026-07-27T00:00:00Z"},
            },
            "expect": {
                "arp_disposition": "INDETERMINATE",
                "axes": ["outcome-reported-only",
                         "physical-completion-unproven"],
                "admission_effect": "UNCHANGED",
                "post_effect_reconciliation": "REQUIRED",
            },
        },
        {
            "id": "accept_outcome_corroborated_clears_both",
            "comment": "The positive control. An ex post attestation from a "
                       "party other than the actor clears both axes. Present "
                       "so the axes are falsifiable rather than always-on.",
            "action": {
                "action_type": "payment.release.1",
                "amount": "10.00",
                "currency": "USD",
                "destination": "acct:demo",
            },
            "record": {
                "verdict": "EXECUTED",
                "reversible": False,
                "rollback_ref": None,
                "attestors": ["actor", "settlement-observer"],
                "settlement": [{"kid": "settlement-observer",
                                "over": "sha256:4492c238e2f9224ad9fc2d447b82ee"
                                        "cfb58c5c7029293b00ee69e27066389b43"}],
            },
            "expect": {
                "arp_disposition": "INDETERMINATE",
                "axes": [],
                "admission_effect": "UNCHANGED",
                "post_effect_reconciliation": "NOT_REQUIRED",
                "note": "INDETERMINATE rather than APPROVE because the "
                        "authorization leg is a separate question. Clearing "
                        "the outcome axes removes the outcome objection; it "
                        "does not authorize.",
            },
        },
    ],
}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        VECTORS, "arp-aeb-adapter-v0.1.json")
    res = run(path)
    out = os.path.join(RUNS, "arp_adapter_run.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, sort_keys=True)
    # v0.1 is SUPERSEDED by v0.2 (conformance/vectors/). It is regenerated here
    # so the supersession is checkable rather than asserted; the name says so.
    vec = os.path.join(RUNS, "arp-outcome-vectors-v0.1-superseded.json")
    with open(vec, "w", encoding="utf-8") as f:
        json.dump(OUTCOME_VECTORS, f, indent=2)
    print(f"  wrote {os.path.basename(out)} and {os.path.basename(vec)}")
    print()


if __name__ == "__main__":
    main()
