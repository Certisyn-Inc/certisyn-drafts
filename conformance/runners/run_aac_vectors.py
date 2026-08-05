#!/usr/bin/env python3
"""ARP against the Agent Action Capsule (AAC) Class-1 frozen vector suite.

Suite: action-state-group/agent-action-capsule, test-vectors/, 32 cases,
SHA256SUMS-pinned, exercised by two independent runners (Python and Go) that
share no code path.

AAC computes, per draft-mih-scitt-agent-action-capsule §2 and §5.1:

    capsule_id = HEX(SHA-256(JCS(normalize(capsule minus {capsule_id, chain}))))

`normalize` is absent-field normalization. That is the SAME SHAPE as CPB's
jcs-n: an exclusion set, then absent-field normalization, then JCS, then
SHA-256, with the same float and unsafe-integer refusals. The exclusion set is
just fixed rather than declared per type.

So this runner asks three questions, in increasing order of usefulness:

  1. Does AAC reproduce its own pinned capsule_id on every positive vector,
     and REFUSE every negative one? (Their claim, checked by us.)

  2. Does ARP's arp-subject-digest/1 agree? It should not, on any capsule that
     carries a null or empty member or a `chain` block, because ARP applies
     neither the exclusion set nor the normalization. Every divergence must be
     attributable, in both directions, or this runner fails.

  3. THE ONE WORTH RUNNING. Does CPB's jcs-n derived-identifier mechanism,
     given the exclusion set {capsule_id, chain}, reproduce AAC's capsule_id
     EXACTLY -- on a third implementation that has never seen an AAC capsule?

     If yes, AAC's capsule_id is not a new construction. It is a CPB derived
     identifier with a fixed exclusion set, and the composition draft can cite
     the binding draft rather than restate the mechanism. That is a
     cite-don't-restate finding of the same kind ARP-02 already took, and it
     is only worth asserting if a third implementation agrees byte-for-byte.

An unattributed agreement or divergence is a hard failure of this runner, not
a row in a table.
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--aac-repo", required=True,
                 help="checkout of github.com/action-state-group/agent-action-capsule "
                      "at the pinned commit")
_ap.add_argument("--cpb-repo", required=True,
                 help="checkout of github.com/action-state-group/scitt-payload-binding "
                      "at the pinned commit; supplies the third implementation")
_ap.add_argument("--json", default=os.path.join(HERE, "..", "runs", "aac_run.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.cpb_repo, "lib"))
sys.path.insert(0, os.path.join(ARGS.aac_repo, "python"))

import arp_reconcile as arp                                    # noqa: E402

from agent_action_capsule import canonical as AAC              # noqa: E402
from cpb import canonicalize as CPB                            # noqa: E402
from cpb.canonicalize import (FloatInDigestError,              # noqa: E402
                              UnsafeIntegerError)

# AAC's fixed exclusion set, read from THEIR module rather than transcribed.
AAC_EXCLUSION = list(AAC.CHAIN_LINKAGE_FIELDS)


def hr(ch="-", n=100):
    print(ch * n)


def arp_subject_digest(obj):
    return hashlib.sha256(arp.jcs_bytes(obj)).hexdigest()


def structural_cause(capsule):
    """The declared jcs-n/AAC steps that ARP does not implement, if any of
    them actually change THIS input. Returns a list, possibly empty."""
    causes = []
    stripped = {k: v for k, v in capsule.items() if k not in AAC_EXCLUSION}
    if stripped != capsule:
        causes.append("exclusion-set-applied")
    if CPB.normalize(stripped) != stripped:
        causes.append("absent-field-normalization-applied")
    return causes


def main():
    vdir = os.path.join(ARGS.aac_repo, "test-vectors")
    cases = sorted(d for d in os.listdir(vdir)
                   if os.path.isdir(os.path.join(vdir, d)))

    print()
    hr("=")
    print("ARP against the AAC Class-1 frozen vector suite")
    hr("=")
    print(f"  cases                : {len(cases)}")
    print(f"  AAC exclusion set    : {AAC_EXCLUSION}  (read from their module)")
    print()
    print("  Three constructions in this run:")
    print(f"    arp-subject-digest/1  id={arp.construction_id_digest('arp-subject-digest/1')}"
          "   SHA-256(JCS(v)), no exclusion, no normalization")
    print("    aac capsule_id        SHA-256(JCS(normalize(v minus {capsule_id, chain})))")
    print("    cpb jcs-n derived id  SHA-256(JCS(normalize(v minus <declared exclusion set>)))")
    print()

    rows = []
    unattributed = []
    pos = neg = 0
    aac_repro = cpb_agrees = arp_agrees = 0

    hr()
    print("1. Per-vector")
    hr()
    print(f"  {'vector':<42} {'kind':<5} {'aac':<8} {'cpb=aac':<9} {'arp=aac':<9} cause")

    for name in cases:
        cdir = os.path.join(vdir, name)
        capsule = json.load(open(os.path.join(cdir, "input.json")))
        expected = json.load(open(os.path.join(cdir, "expected.json")))
        kind = expected.get("kind", "?")
        pinned = expected.get("capsule_id_recomputed")

        # --- 1. AAC checks itself -------------------------------------------
        aac_id = None
        aac_exc = None
        try:
            aac_id = AAC.compute_capsule_id(capsule)
        except Exception as e:                                  # noqa: BLE001
            aac_exc = type(e).__name__

        # --- 3. CPB, third implementation, same declared exclusion set ------
        cpb_id = None
        cpb_exc = None
        try:
            stripped = {k: v for k, v in capsule.items() if k not in AAC_EXCLUSION}
            cpb_id = CPB.canonical_digest(stripped, [])
        except (FloatInDigestError, UnsafeIntegerError) as e:
            cpb_exc = type(e).__name__
        except Exception as e:                                  # noqa: BLE001
            cpb_exc = type(e).__name__

        # --- 2. ARP, no exclusion set, no normalization ---------------------
        arp_id = arp_subject_digest(capsule)
        arp_causes = set()
        arp._ep_walk(capsule, 0, arp_causes)

        causes = structural_cause(capsule)

        row = {
            "vector": name, "kind": kind,
            "pinned_capsule_id": pinned,
            "aac_capsule_id": aac_id, "aac_exception": aac_exc,
            "cpb_derived_id": cpb_id, "cpb_exception": cpb_exc,
            "arp_subject_digest": arp_id,
            "arp_gate_causes": sorted(arp_causes),
            "divergence_causes": causes,
        }

        if pinned is not None:
            pos += 1
            row["aac_reproduces_pinned"] = (aac_id == pinned)
            row["cpb_agrees_with_aac"] = (cpb_id == aac_id and aac_id is not None)
            row["arp_agrees_with_aac"] = (arp_id == aac_id)
            aac_repro += bool(row["aac_reproduces_pinned"])
            cpb_agrees += bool(row["cpb_agrees_with_aac"])
            arp_agrees += bool(row["arp_agrees_with_aac"])

            if not row["aac_reproduces_pinned"]:
                unattributed.append(
                    f"{name}: AAC did not reproduce its own pinned capsule_id")
            if not row["cpb_agrees_with_aac"]:
                unattributed.append(
                    f"{name}: CPB jcs-n over the SAME exclusion set does not "
                    f"reproduce AAC's capsule_id ({cpb_id} vs {aac_id}) -- the two "
                    "constructions are not the same after all, and that has to be "
                    "explained rather than tabulated")
            # Two-directional check on ARP, as in the CPB runner.
            if not row["arp_agrees_with_aac"] and not causes:
                unattributed.append(
                    f"{name}: arp-subject-digest/1 diverges from capsule_id with no "
                    "declared cause")
            if row["arp_agrees_with_aac"] and causes:
                unattributed.append(
                    f"{name}: arp-subject-digest/1 AGREES although {causes} should "
                    "have changed the bytes")
            print(f"  {name:<42} {kind:<5} "
                  f"{('repro' if row['aac_reproduces_pinned'] else 'MISMATCH'):<8} "
                  f"{('agree' if row['cpb_agrees_with_aac'] else 'DIFFER'):<9} "
                  f"{('agree' if row['arp_agrees_with_aac'] else 'diverge'):<9} "
                  f"{','.join(causes) or '-'}")
        else:
            neg += 1
            # A negative vector carries findings, not a recomputed id. What is
            # checkable here is whether the digest-bearing-value guards fire in
            # all three implementations, since those are the only negatives
            # that are a CANONICALIZATION matter rather than a semantic one.
            guard_case = aac_exc is not None or cpb_exc is not None
            row["guard_case"] = guard_case
            row["expected_findings"] = [f.get("code") if isinstance(f, dict) else f
                                        for f in expected.get("findings", [])]
            if guard_case:
                row["arp_gate_refused"] = bool(arp_causes)
                if not arp_causes:
                    unattributed.append(
                        f"{name}: AAC and/or CPB refuse this input on a "
                        f"digest-bearing-value guard ({aac_exc or cpb_exc}) but ARP's "
                        "strict-parse gate accepts it -- a gap, not a difference")
            print(f"  {name:<42} {kind:<5} "
                  f"{(aac_exc or 'findings'):<8} "
                  f"{(cpb_exc or '-'):<9} "
                  f"{(','.join(sorted(arp_causes)) or '-'):<9} "
                  f"{'digest-value-guard' if guard_case else 'semantic, not canonicalization'}")
        rows.append(row)

    hr("=")
    print("SELF-CHECK")
    hr("=")
    print(f"  Positive vectors: {pos}   Negative vectors: {neg}   Total: {len(cases)}")
    print(f"  AAC reproduces its own pinned capsule_id on {aac_repro}/{pos}.")
    print(f"  CPB jcs-n, given AAC's exclusion set {AAC_EXCLUSION}, reproduces AAC's")
    print(f"    capsule_id on {cpb_agrees}/{pos} -- a THIRD implementation, no shared code.")
    print(f"  arp-subject-digest/1 agrees with capsule_id on {arp_agrees}/{pos};")
    print(f"    every divergence is attributed to a declared step ARP does not implement.")
    print()
    if cpb_agrees == pos and pos:
        print("  FINDING. AAC's capsule_id is not a distinct construction. It is a CPB")
        print("  jcs-n derived identifier under a FIXED exclusion set {capsule_id, chain}.")
        print("  Three implementations agree byte-for-byte on all "
              f"{pos} positive vectors.")
        print("  The composition draft can therefore CITE the binding draft's mechanism")
        print("  rather than restate it, exactly as ARP-02 cites rather than restates the")
        print("  capsule slots. One rule in the ecosystem beats two that almost agree.")
    print()
    if unattributed:
        print("  !! UNATTRIBUTED RESULTS -- defects, not table rows:")
        for u in unattributed:
            print(f"     {u}")
        print("  SELF-CHECK: FAIL")
    else:
        print("  No unattributed agreement or divergence.")
        print("  SELF-CHECK: PASS")

    out = os.path.abspath(ARGS.json)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "suite": "agent-action-capsule test-vectors (Class-1 frozen)",
            "harness": "arp_reconcile.py v2.1",
            "harness_sha256": hashlib.sha256(
                open(os.path.join(HERE, "..", "harness", "arp_reconcile.py"),
                     "rb").read()).hexdigest(),
            "aac_exclusion_set": AAC_EXCLUSION,
            "counts": {"positive": pos, "negative": neg,
                       "aac_reproduces_pinned": aac_repro,
                       "cpb_agrees_with_aac": cpb_agrees,
                       "arp_agrees_with_aac": arp_agrees},
            "rows": rows,
            "unattributed": unattributed,
        }, f, indent=2)
        f.write("\n")
    print(f"\n  machine-readable result written to runs/{os.path.basename(out)}")
    return 1 if unattributed else 0


if __name__ == "__main__":
    sys.exit(main())
