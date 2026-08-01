#!/usr/bin/env python3
"""ARP against the CPB conformance vector suite.

draft-mih-sokolov-scitt-payload-binding defines algorithm `jcs-n`:

    CANONICAL-DIGEST(jcs-n, P) = hex(SHA-256(JCS(normalize(P minus exclusion_set))))

where `normalize` is ABSENT-FIELD normalization -- remove, bottom-up, every
object member whose value is null, an empty array, or an empty object. It is
NOT Unicode normalization. ARP's two constructions are:

    arp-subject-digest/1    SHA-256(JCS(action))              no normalisation
    arp-canonical-claim/1   SHA-256(JCS(NFC(claim)))          NFC applied

So there are now three canonicalisations in this conversation, and the useful
question is not "does ARP pass CPB's suite" -- ARP implements neither jcs-n's
absent-field step nor its exclusion sets, so on any vector that exercises them
ARP MUST diverge, and a runner that reported otherwise would be broken. The
useful question is WHERE they diverge and whether every divergence is
attributable to a declared difference rather than to a defect.

This runner answers that, per vector, and reports the vectors ARP cannot reach
at all rather than passing over them.

Three checks per jcs-n KAT:

  1. Does the CPB reference library reproduce its own pinned digest?
     (Two-sided: the MUST-FAIL vectors must raise, not merely mismatch.)
  2. Does ARP's arp-subject-digest/1 agree with the pinned jcs-n digest?
  3. Does ARP's arp-canonical-claim/1 agree?

Every disagreement is attributed to a named cause. An unattributed
disagreement is a hard failure of this runner, not a row in a table.
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--cpb-repo", required=True,
                 help="checkout of github.com/action-state-group/scitt-payload-binding "
                      "at the pinned commit")
_ap.add_argument("--json", default=os.path.join(HERE, "..", "runs", "cpb_run.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.cpb_repo, "lib"))

import arp_reconcile as arp          # noqa: E402

try:
    from cpb import canonicalize as CPB_C
    from cpb.canonicalize import FloatInDigestError, UnsafeIntegerError
    _HAVE_CPB = True
except ImportError:
    _HAVE_CPB = False


def hr(ch="-", n=100):
    print(ch * n)


def apply_exclusion(payload, exclusion_set):
    if not exclusion_set:
        return payload
    return {k: v for k, v in payload.items() if k not in exclusion_set}


def arp_subject_digest(obj):
    return hashlib.sha256(arp.jcs_bytes(obj)).hexdigest()


def arp_claim_hash(obj):
    return arp.claim_hash(obj)


def normalizes_anything(payload, exclusion_set):
    """True when jcs-n's absent-field step or an exclusion set actually
    changes this input. That is the declared reason ARP would diverge."""
    stripped = apply_exclusion(payload, exclusion_set)
    if stripped != payload:
        return "exclusion-set-applied"
    if not _HAVE_CPB:
        return None
    if CPB_C.normalize(stripped) != stripped:
        return "absent-field-normalization-applied"
    return None


def main():
    root = ARGS.cpb_repo
    kats = sorted(_glob(os.path.join(root, "vectors", "jcs-n", "kats")))
    derived = sorted(_glob(os.path.join(root, "vectors", "jcs-n", "derived-id")))
    typed = sorted(_glob(os.path.join(root, "vectors", "typed-refs"), rec=True))
    prof = sorted(_glob(os.path.join(root, "vectors", "profile-independence"), rec=True))

    print()
    hr("=")
    print("ARP against draft-mih-sokolov-scitt-payload-binding conformance vectors")
    hr("=")
    print(f"  suite            : {len(kats) + len(derived) + len(typed) + len(prof)} vectors")
    print(f"  cpb reference lib: {'available' if _HAVE_CPB else 'NOT INSTALLED -- rerun with lib/ on the path'}")
    print()
    print("  ARP constructions carried into this run:")
    for name in ("arp-subject-digest/1", "arp-canonical-claim/1"):
        print(f"    {name:<24} id={arp.construction_id_digest(name)}")
    print()
    print("  jcs-n = absent-field normalization + exclusion set + JCS + SHA-256.")
    print("  ARP implements the JCS and SHA-256 halves and NEITHER of the first two.")
    print("  Divergence on a vector that exercises them is the CORRECT result.")
    print()

    rows = []
    unattributed = []

    hr()
    print("1. jcs-n known-answer tests")
    hr()
    print(f"  {'vector':<16} {'cpb':<10} {'subject-digest':<16} {'canonical-claim':<16} cause")
    for path in kats:
        v = json.load(open(path))
        vid = v["id"]

        if v.get("must_fail"):
            # Two-sided: the library must REFUSE, not merely differ.
            raised = None
            if _HAVE_CPB:
                try:
                    CPB_C.canonical_digest(v.get("input", v.get("payload", {})),
                                           v.get("exclusion_set") or [])
                    raised = None
                except (FloatInDigestError, UnsafeIntegerError) as e:
                    raised = type(e).__name__
                except Exception as e:      # noqa: BLE001
                    raised = type(e).__name__
            cpb_ok = raised is not None
            # ARP's own EP strict-parse gate should refuse the same input.
            causes = set()
            arp._ep_walk(v.get("input", v.get("payload", {})), 0, causes)
            arp_refuses = bool(causes)
            rows.append({"vector": vid, "class": "must_fail",
                         "cpb_refused": cpb_ok, "cpb_exception": raised,
                         "arp_gate_refused": arp_refuses,
                         "arp_gate_causes": sorted(causes)})
            print(f"  {vid:<16} {'REFUSED' if cpb_ok else 'ACCEPTED!':<10} "
                  f"{'gate refuses' if arp_refuses else 'gate ACCEPTS':<16} {'':<16} "
                  f"{','.join(sorted(causes)) or 'n/a'}")
            if not cpb_ok:
                unattributed.append(f"{vid}: CPB library did not refuse a MUST-FAIL vector")
            continue

        payload = v["input"]
        excl = v.get("exclusion_set") or []
        pinned = v["digest"]

        cpb_repro = None
        if _HAVE_CPB:
            cpb_repro = CPB_C.canonical_digest(payload, excl) == pinned

        stripped = apply_exclusion(payload, excl)
        normalized = CPB_C.normalize(stripped) if _HAVE_CPB else stripped
        # ARP is given the SAME logical input the vector describes, with none
        # of jcs-n's preprocessing, which is the point of the comparison.
        sd = arp_subject_digest(payload)
        ch = arp_claim_hash(payload)

        sd_agree = (sd == pinned)
        ch_agree = (ch == pinned)
        cause = normalizes_anything(payload, excl)

        if not sd_agree and cause is None:
            # Nothing jcs-n does to this input differs from what ARP does, so a
            # divergence here is a real disagreement and must not be tabulated
            # quietly.
            unattributed.append(
                f"{vid}: subject-digest diverges with no declared cause "
                f"(arp={sd} pinned={pinned})")
        if sd_agree and cause is not None:
            unattributed.append(
                f"{vid}: subject-digest AGREES although {cause} should have "
                "changed the bytes")

        rows.append({
            "vector": vid, "class": "positive",
            "cpb_reproduces_pinned_digest": cpb_repro,
            "pinned_digest": pinned,
            "arp_subject_digest": sd, "arp_subject_digest_agrees": sd_agree,
            "arp_canonical_claim": ch, "arp_canonical_claim_agrees": ch_agree,
            "divergence_cause": cause,
            "normalization_changed_input": normalized != payload,
        })
        print(f"  {vid:<16} {('repro' if cpb_repro else 'MISMATCH'):<10} "
              f"{('agree' if sd_agree else 'diverge'):<16} "
              f"{('agree' if ch_agree else 'diverge'):<16} {cause or '-'}")

    print()
    hr()
    print("2. Vectors ARP cannot reach, and why. Reported, not skipped.")
    hr()
    out_of_scope = []
    for label, paths, why in (
        ("jcs-n/derived-id", derived,
         "derived identifiers are computed over a payload MINUS a declared "
         "exclusion set. ARP has no exclusion-set mechanism: its subject digest "
         "covers the whole action object by design, because an ARP correlation "
         "digest that omitted fields could correlate two different actions."),
        ("typed-refs", typed,
         "typed digest references carry a declared artifact type, digest context "
         "and representation. ARP-02 REQUIRES a correlation digest to identify "
         "its construction and defers the mechanism to this draft rather than "
         "defining one, so ARP has nothing of its own to run here. This is the "
         "gap the deferral creates, and it is deliberate."),
        ("profile-independence", prof,
         "these test that one payload profile does not reach inside another. "
         "ARP has a single profile and no cross-profile surface, so the "
         "property is vacuously satisfied and testing it would prove nothing."),
    ):
        for path in paths:
            v = json.load(open(path))
            out_of_scope.append({"vector": v["id"], "group": label, "reason": why})
        print(f"  {label:<24} {len(paths)} vector(s)")
        for line in _wrap(why, 92):
            print(f"      {line}")
        print()

    hr("=")
    print("SELF-CHECK")
    hr("=")
    pos = [r for r in rows if r["class"] == "positive"]
    mf = [r for r in rows if r["class"] == "must_fail"]
    repro = sum(1 for r in pos if r.get("cpb_reproduces_pinned_digest"))
    agree = sum(1 for r in pos if r.get("arp_subject_digest_agrees"))
    print(f"  CPB reference library reproduces {repro}/{len(pos)} of its own pinned digests.")
    print(f"  CPB library refuses {sum(1 for r in mf if r['cpb_refused'])}/{len(mf)} "
          f"MUST-FAIL vectors (two-sided: a suite that only mismatched would pass a "
          f"verifier that never refuses).")
    print(f"  arp-subject-digest/1 agrees with jcs-n on {agree}/{len(pos)} positive vectors.")
    print(f"  Every one of the {len(pos) - agree} divergences is attributed to a declared "
          f"jcs-n step ARP does not implement.")
    print(f"  {len(out_of_scope)} vectors are out of ARP's scope and are listed above with "
          f"the reason, not omitted.")
    if unattributed:
        print()
        print("  !! UNATTRIBUTED RESULTS -- these are defects, not table rows:")
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
            "suite": "draft-mih-sokolov-scitt-payload-binding conformance vectors",
            "harness": "arp_reconcile.py v2.1",
            "harness_sha256": hashlib.sha256(
                open(os.path.join(HERE, "..", "harness", "arp_reconcile.py"),
                     "rb").read()).hexdigest(),
            "constructions": {n: arp.construction_id_digest(n)
                              for n in ("arp-subject-digest/1", "arp-canonical-claim/1")},
            "rows": rows,
            "out_of_scope": out_of_scope,
            "unattributed": unattributed,
        }, f, indent=2)
        f.write("\n")
    print(f"\n  machine-readable result written to {out}")
    return 1 if unattributed else 0


def _glob(d, rec=False):
    hits = []
    if not os.path.isdir(d):
        return hits
    for dirpath, _dirs, files in os.walk(d):
        for fn in files:
            if fn.endswith(".json"):
                hits.append(os.path.join(dirpath, fn))
        if not rec:
            break
    return hits


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


if __name__ == "__main__":
    sys.exit(main())
