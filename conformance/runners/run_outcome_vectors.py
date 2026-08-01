#!/usr/bin/env python3
"""Two-sided runner for ARP-OUTCOME-VECTORS v0.2.

Publishing vectors with declared expectations and no runner would be the
exact thing this work argues against, so here is the runner. It is
two-sided by construction: three vectors expect the axes to FIRE and two
expect them NOT to. A suite that only ever asserts a refusal cannot detect
an implementation that is too strict.

Nothing here reimplements the Verdict Arithmetic. HARD_AXES, SOFT_AXES and
compose() are imported from the harness, so a vector that emitted an
undeclared axis would stop this runner the same way it stops a corpus run.

The CAID side is not reimplemented either: identifiers are issued and
verified by the CAID reference implementation, and ARP recomputes its own
subject digest independently. The two agreeing is a result, not a
convention.
"""

import argparse
import base64
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--vectors", default=os.path.join(HERE, "..", "vectors", "arp-outcome-vectors-v0.2.json"),
                 help="ARP-OUTCOME-VECTORS json (default: alongside this script)")
_ap.add_argument("--caid-repo", required=True,
                 help="path to a checkout of github.com/emiliaprotocol/emilia-protocol "
                      "at the pinned commit; the CAID reference implementation and "
                      "action-type registry are read from <repo>/caid/")
_ap.add_argument("--json", default=os.path.join(HERE, "..", "runs", "arp_outcome_vectors_v02_run.json"),
                 help="where to write the machine-readable result")
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.caid_repo, "caid", "impl", "python"))

import arp_reconcile as arp          # noqa: E402
import caid as C                     # noqa: E402

VECTORS = ARGS.vectors
REGISTRY = os.path.join(ARGS.caid_repo, "caid", "registry", "action-types.json")
DEFS = json.load(open(REGISTRY))["types"]


def hr(ch="-", n=100):
    print(ch * n)


def caid_from_digest(action_type, digest_hex):
    raw = base64.urlsafe_b64encode(bytes.fromhex(digest_hex)).decode().rstrip("=")
    return f"caid:1:{action_type}:jcs-sha256:{raw}"


def outcome_legs(record):
    """The two outcome axes, over the vector's neutral record shape.

    Same predicate as reconcile_noa_receipt: an EXECUTED assertion is
    corroborated only by an ex post attestation from a party OTHER than the
    actor. A named human approver does not count -- an approval is ex ante
    and says the act was PERMITTED, not that it OCCURRED.
    """
    legs = []
    if record.get("verdict") != "EXECUTED":
        return legs

    actors = set(record.get("attestors") or [])
    ex_post = record.get("ex_post_attestation")
    independent = set()
    if isinstance(ex_post, dict):
        by = ex_post.get("by")
        # Corroboration requires a DIFFERENT party and an ex post attestation
        # over the subject digest. An approval object is deliberately not read
        # here; that is the negative control.
        if by and by != "actor" and ex_post.get("over_subject_digest"):
            independent.add(by)

    if independent:
        return legs

    legs.append(("outcome", "indeterminate", "outcome-reported-only", arp.COMPUTED))
    if record.get("reversible") is False and record.get("rollback_ref") is None:
        legs.append(("completion", "indeterminate",
                     "physical-completion-unproven", arp.COMPUTED))
    return legs


def main():
    doc = json.load(open(VECTORS))
    print()
    hr("=")
    print(f"{doc['@version']}  --  two-sided runner")
    hr("=")
    print(f"  supersedes            : {doc.get('supersedes')}")
    print(f"  CAID suite            : {doc['construction']['caid_suite']}")
    reg = doc["construction"]["caid_action_type_registry"]
    print(f"  action-type registry  : {reg['registry']} v{reg['registry_version']} "
          f"(updated {reg['updated']})")
    print(f"  ARP construction id   : arp-subject-digest/1 = "
          f"{doc['construction']['arp_subject_digest_profile_id']}")
    print()

    rows = []
    passed = failed = 0

    for v in doc["vectors"]:
        vid = v["id"]
        action = v["action"]
        exp = v["expect"]

        # --- CAID side: reference implementation issues, ARP recomputes ----
        issued = C.compute_caid(action, {"suite": "jcs-sha256", "definitions": DEFS})
        sd = hashlib.sha256(arp.jcs_bytes(action)).hexdigest()
        recomputed = caid_from_digest(action["action_type"], sd)

        caid_checks = []
        if "caid" in issued:
            caid_checks.append(("issuer emitted a caid", True))
            caid_checks.append(("ARP recomputation agrees", issued["caid"] == recomputed))
            ver = C.verify_caid(action, issued["caid"], {"definitions": DEFS})
            caid_checks.append(("verify_caid valid", ver["valid"] is True))
            caid_checks.append(("pinned caid matches", v.get("caid") == issued["caid"]))
            issuance = "ISSUED"
            refusals = []
        else:
            issuance = "REFUSED"
            refusals = issued["refusals"]
            caid_checks.append(("issuer refused", True))
            caid_checks.append(("no caid emitted", v.get("caid") is None))

        # --- ARP side -----------------------------------------------------
        legs = outcome_legs(v["record"])
        if issuance == "REFUSED":
            # No join key exists. That is an absence of evidence, not evidence
            # of tampering, so it HOLDS -- it does not refuse.
            legs = [("caid-binding", "indeterminate",
                     "caid-binding-unverified", arp.COMPUTED)]

        disposition, refused_at, deciding = arp.compose_ex(legs)
        axes = [a for (_s, _v, a, _p) in legs if a]

        # --- comparison ---------------------------------------------------
        checks = list(caid_checks)
        checks.append(("disposition", disposition == exp["arp_disposition"]))
        checks.append(("axes", axes == exp["axes"]))
        if "caid_issuance" in exp:
            checks.append(("caid_issuance", issuance == exp["caid_issuance"]))
            checks.append(("caid_refusals", refusals == exp["caid_refusals"]))

        ok = all(c[1] for c in checks)
        passed += ok
        failed += (not ok)

        print(f"  {vid}")
        print(f"    caid issuance : {issuance}"
              + (f"  {refusals}" if refusals else f"  {issued.get('caid','')}"))
        print(f"    arp subject   : sha256:{sd}")
        print(f"    legs          : "
              + (", ".join(f"{s}/{vd}/{a}" for (s, vd, a, _p) in legs) or "(none)"))
        print(f"    disposition   : {disposition}   expected {exp['arp_disposition']}")
        print(f"    axes          : {axes or '[]'}   expected {exp['axes'] or '[]'}")
        print(f"    -> {'PASS' if ok else 'FAIL'}"
              + ("" if ok else "   failing checks: "
                 + ", ".join(n for n, r in checks if not r)))
        print()

        rows.append({
            "id": vid, "caid_issuance": issuance, "caid_refusals": refusals,
            "caid": issued.get("caid"), "arp_subject_digest": "sha256:" + sd,
            "disposition": disposition, "axes": axes,
            "expected_disposition": exp["arp_disposition"], "expected_axes": exp["axes"],
            "checks": [{"name": n, "ok": r} for n, r in checks],
            "pass": ok,
        })

    hr("=")
    print("SELF-CHECK")
    hr("=")
    fired = sum(1 for r in rows if r["axes"] and "outcome-reported-only" in r["axes"])
    cleared = sum(1 for r in rows if not r["axes"])
    print(f"  {passed}/{len(rows)} vectors agree with their pinned expectation.")
    print(f"  Two-sided: {fired} vector(s) expect an axis to FIRE, "
          f"{cleared} expect BOTH axes to CLEAR, "
          f"{sum(1 for r in rows if r['caid_issuance'] == 'REFUSED')} expect CAID issuance "
          f"to be REFUSED.")
    print("  The axes are therefore falsifiable rather than always-on: an "
          "implementation")
    print("  that always fired them would fail accept_outcome_corroborated_clears_both,")
    print("  and one that never fired them would fail the other three.")
    nest_o = {r["id"] for r in rows if "outcome-reported-only" in r["axes"]}
    nest_p = {r["id"] for r in rows if "physical-completion-unproven" in r["axes"]}
    print(f"  Predicate nesting: physical-completion-unproven ({len(nest_p)}) is a "
          f"strict subset of outcome-reported-only ({len(nest_o)}): "
          f"{nest_p < nest_o or (nest_p == set() and True)}")
    print(f"  Axis closure: every axis emitted is declared HARD or SOFT "
          f"(compose_ex fails closed otherwise).")
    print()
    print(f"  RESULT: {passed} passed, {failed} failed")

    out = ARGS.json
    with open(out, "w") as f:
        # DEFECT FIX (Songbo, 2026-07-29). This recorded the ABSOLUTE path of
        # the vector file, so the run JSON was not byte-identical across
        # checkout locations even when every verdict in it was. A result file
        # that changes with the reader's directory layout cannot be compared by
        # hash, which is the whole point of publishing the hash. The basename
        # identifies the file; the sha256 pins its content. Neither depends on
        # where the checkout sits.
        json.dump({"vectors_file": os.path.basename(VECTORS),
                   "vectors_file_sha256": hashlib.sha256(
                       open(VECTORS, "rb").read()).hexdigest(),
                   "harness": "arp_reconcile.py v2.1",
                   "harness_sha256": hashlib.sha256(
                       open(os.path.join(HERE, "..", "harness", "arp_reconcile.py"), "rb").read()).hexdigest(),
                   "passed": passed, "failed": failed, "rows": rows}, f, indent=2)
        f.write("\n")
    print(f"  machine-readable result written to {out}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
