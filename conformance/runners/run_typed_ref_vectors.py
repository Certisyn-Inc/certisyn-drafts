#!/usr/bin/env python3
"""Run the CPB-01 typed-reference vector set against the CPB reference library
and the ARP harness.

Each vector states what draft-mih-sokolov-scitt-payload-binding-01 REQUIRES.
This runner records what the reference library at its pinned commit actually
DOES. Those are two different things and the value of the run is in the cases
where they differ, and in saying WHY they differ without overclaiming.

TWO-SIDED, in the sense the rest of this tree uses the word. Each vector's
`finding_class` is a falsifiable prediction about the gap between requirement
and implementation, and the runner checks it in both directions:

  conformance_baseline     implementation matches the requirement
  revision_uplift_gap      -01 requires it; the library targets -00, which did
                           not. Gap expected, and it is not a defect.
  specification_question   two parts of -01 that do not compose. Gap expected,
                           and it is not a defect in any implementation.
  contributor_side_defect  gap expected, and it is the contributor's

A vector predicted to expose a gap that no longer does is NOT silently
downgraded to a pass. It means the library moved, the vector's class is stale,
and the run says so in those words rather than agreeing with whatever it finds.

  suite_coverage_gap       the reference library cannot reach this vector at
                           all. Its prediction field is NOT APPLICABLE and the
                           runner says so rather than encoding "unreachable" as
                           "refused". It is scored on its own preconditions:
                           whether its recorded bytes reproduce from its
                           recorded inputs.

That distinction is deliberate: encoding "unreachable" as "refused" would make
the prediction unfalsifiable while printing "prediction held" beside it, and a
check that cannot fail is not a check.

Usage:
    python3 run_typed_ref_vectors.py --cpb-repo /path/to/scitt-payload-binding
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
_ap.add_argument("--caid-repo", required=True,
                 help="checkout of github.com/emiliaprotocol/emilia-protocol at "
                      "the pinned commit. Vector 05's action objects are "
                      "re-minted here rather than trusted from the file.")
_ap.add_argument("--vectors", default=os.path.join(
    HERE, "..", "vectors", "arp-typed-ref-cpb01-v0.1.json"))
_ap.add_argument("--json", default=os.path.join(
    HERE, "..", "runs", "typed_ref_cpb01_run.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.cpb_repo, "lib"))
sys.path.insert(0, os.path.join(ARGS.caid_repo, "caid", "impl", "python"))

import arp_reconcile as arp                                       # noqa: E402
import caid as C                                                  # noqa: E402
from cpb.typed_ref import (ArtifactTypeRegistryEntry,             # noqa: E402
                           verify_typed_ref, TypedRefError)

NOT_APPLICABLE = "not-applicable"

CAID_OPT = {
    "suite": "jcs-sha256",
    "definitions": json.load(open(os.path.join(
        ARGS.caid_repo, "caid", "registry", "action-types.json")))["types"],
}


def hr(ch="-", n=100):
    print(ch * n)


def entry(d):
    """Build a registry entry from the VECTOR's own declaration.

    Standing rule: preconditions are stated in the vector, not assumed by the
    runner. Nothing here supplies a default exclusion set or representation --
    a vector that does not declare one cannot be run, and that is correct,
    because a third party reading only the vector could not check it either.
    """
    for required in ("name", "exclusion_set", "representation"):
        if required not in d:
            raise KeyError(
                f"registry entry in the vector does not declare {required!r}; "
                "the runner will not supply it")
    return ArtifactTypeRegistryEntry(
        name=d["name"],
        algorithm=d.get("algorithm", "jcs-n"),
        exclusion_set=frozenset(d["exclusion_set"]),
        representation=d["representation"],
    )


def attempt(ref, payload, reg):
    """Return (accepted, detail). Never raises.

    The reference is passed to the library EXACTLY as the vector carries it,
    additional members and all. Projecting it onto the three §7 fields first
    would mean the runner performed the ignoring that vector 05 credits the
    library with, and the check would measure nothing. As written, a change to
    verify_typed_ref that rejected unknown members is noticed here."""
    try:
        return True, verify_typed_ref(ref, payload, reg)
    except TypedRefError as e:
        return False, type(e).__name__
    except Exception as e:                        # pragma: no cover
        return False, f"{type(e).__name__}: {e}"


def arp_sd(action):
    return hashlib.sha256(arp.jcs_bytes(action)).hexdigest()


# ---------------------------------------------------------------------------
# One checker per vector. Each returns:
#   requirement   what CPB-01 requires (True = verified, False = MUST NOT)
#   observed      what was measured, or NOT_APPLICABLE
#   detail        free text for the transcript
#   preconditions (optional) dict of name -> bool, all of which must hold
# ---------------------------------------------------------------------------

def check_01(v):
    reg = entry(v["artifact_type_registry_entry"])
    ok, got = attempt(v["typed_reference"], v["cited_artifact"]["payload"], reg)
    return {
        "requirement": True,
        "observed": ok,
        "detail": f"recomputed {got[:16]}..." if ok else f"library refused: {got}",
        "extra": {"recomputed_digest": got if ok else None},
    }


def check_02(v):
    reg = entry(v["artifact_type_registry_entry"])
    payload = v["cited_artifact"]["payload"]
    ok, got = attempt(v["typed_reference"], payload, reg)

    # The second form recorded in the vector, on the same code path. Measured,
    # not asserted: the vector claims four algorithm names are accepted and
    # this is where that claim is either reproduced or falsified.
    others = {}
    for alg in ("not-a-hash-algorithm", "MD5", ""):
        ok_o, _ = attempt(dict(v["typed_reference"], digest_alg=alg), payload, reg)
        others[alg or "(empty string)"] = ok_o

    return {
        "requirement": False,
        "observed": ok,
        "detail": (
            f"library accepted digest_alg "
            f"{v['typed_reference']['digest_alg']!r} against a jcs-n (SHA-256) "
            "registry entry. The field is bound into TypedRef and never read "
            "again, so it constrains nothing."
            if ok else f"library refused: {got}"),
        "extra": {
            "other_algorithm_names_also_accepted": others,
            "library_reads_digest_alg": not (ok and all(others.values())),
        },
    }


def check_03(v):
    reg = entry(v["artifact_type_registry_entry"])
    ok, got = attempt(v["typed_reference"], v["cited_artifact"]["payload"], reg)
    return {
        "requirement": False,
        "observed": ok,
        "detail": (
            "library accepted a 64-char hex string under a registry entry "
            "declaring representation 'raw'. Its _check_representation applies "
            "the bare-hex test to the 'raw' branch, which follows from "
            "verify_typed_ref taking digest as a str -- raw octets cannot be "
            "handed to it at all. Recorded to ground the question, not as a "
            "defect against the library."
            if ok else f"library refused: {got}"),
        "extra": {"declared_representation": reg.representation},
    }


def check_04(v):
    """§6.1 leaf construction. The reference library implements none, so there
    is no library behaviour to observe and this vector's prediction field is
    NOT APPLICABLE. It is scored on whether its own recorded bytes reproduce."""
    d = v["derived_identifier"]
    correct = bytes.fromhex(d)
    wrong = d.encode("utf-8")
    ill = v["illustrative_derivations"]

    # Probe for leaf construction rather than accepting the vector's own
    # assertion that there is none. If lib/cpb grows one, this notices.
    lib_dir = os.path.join(ARGS.cpb_repo, "lib", "cpb")
    leaf_symbols = ("leaf_input", "fromhex", "6962", "merkle", "inclusion")
    modules = sorted(f[:-3] for f in os.listdir(lib_dir)
                     if f.endswith(".py") and f != "__init__.py")
    found_leaf = []
    for dirpath, _d, files in os.walk(lib_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            src = open(os.path.join(dirpath, fn), encoding="utf-8").read().lower()
            for sym in leaf_symbols:
                if sym in src:
                    found_leaf.append(f"{fn}:{sym}")

    pre = {
        "correct_leaf_input_is_32_bytes":
            len(correct) == v["correct_leaf_input"]["length_bytes"] == 32,
        "correct_leaf_input_bytes_reproduce":
            correct.hex() == v["correct_leaf_input"]["bytes_hex"],
        "incorrect_leaf_input_is_64_bytes":
            len(wrong) == v["incorrect_leaf_input"]["length_bytes"] == 64,
        "incorrect_leaf_input_bytes_reproduce":
            wrong.hex() == v["incorrect_leaf_input"]["bytes_hex"],
        "sha256_derivations_reproduce": (
            hashlib.sha256(correct).hexdigest() == ill["sha256_of_correct_leaf_input"]
            and hashlib.sha256(wrong).hexdigest() == ill["sha256_of_incorrect_leaf_input"]),
        "rfc6962_derivations_reproduce": (
            hashlib.sha256(b"\x00" + correct).hexdigest() == ill["rfc6962_leaf_hash_correct"]
            and hashlib.sha256(b"\x00" + wrong).hexdigest() == ill["rfc6962_leaf_hash_incorrect"]),
        "distinguishable_by_length_alone": len(correct) != len(wrong),
        # Measured, not taken from the vector: the vector says it is
        # unreachable and this is where that is checked against lib/cpb.
        # NAMED FOR WHAT IT MEASURES. It is a substring sweep over .py files,
        # so it reads comments and docstrings and would false-positive on a
        # comment saying the library has no merkle logic, or on a legitimate
        # bytes.fromhex helper -- and false-negative on a real leaf
        # constructor named log_entry_hash using binascii.unhexlify. It
        # establishes absence of these substrings, not absence of the
        # behaviour. The stronger claim rests on reading lib/cpb, which has
        # three modules: canonicalize, derive_id, typed_ref.
        "five_leaf_related_substrings_absent_from_lib_cpb": not found_leaf,
    }

    return {
        "requirement": False,
        "observed": NOT_APPLICABLE,
        "detail": (
            "swept lib/cpb for leaf-related substrings and found "
            f"{'none' if not found_leaf else ', '.join(found_leaf)}. That is a "
            "substring sweep over .py files, not a proof of absence: it reads "
            "comments, and it would miss a leaf constructor written with "
            "binascii.unhexlify. The claim that this library constructs no "
            f"leaf rests on its module set, {', '.join(sorted(modules))}, none "
            "of which does. Either way there is nothing there for this vector "
            "to accept or refuse, so it is scored on its own preconditions: "
            f"{sum(pre.values())}/{len(pre)} hold. Correct leaf_input "
            f"{len(correct)} bytes, incorrect {len(wrong)}."),
        "preconditions": pre,
        "extra": {
            "leaf_symbols_found_in_cpb_lib": found_leaf,
            "cpb_lib_modules": modules,
            "probe": (
                f"substring sweep over {os.path.relpath(lib_dir, ARGS.cpb_repo)}"
                f"/*.py for: {', '.join(leaf_symbols)}. Establishes absence of "
                "these substrings, not absence of leaf construction."),
        },
    }


def check_05(v):
    """The contributor-side vector. CPB is expected to be right here and ARP is
    expected to be wrong, and both halves are measured."""
    reg = entry(v["artifact_type_registry_entry"])
    payload = v["cited_artifact"]["payload"]

    cpb_all_verified = True
    measured = {}
    for rec in v["records"]:
        action = rec["action"]
        carries_ref = "authorization" in action
        if carries_ref:
            ok, _ = attempt(action["authorization"], payload, reg)
            cpb_all_verified = cpb_all_verified and ok
        else:
            ok = None                       # nothing to verify; not a pass
        sd = arp_sd(action)
        issued = C.compute_caid(action, CAID_OPT)
        measured[rec["variant"]] = {
            "arp_subject_digest": sd,
            "matches_recorded": sd == rec["arp_subject_digest"],
            "caid": issued.get("caid"),
            "caid_refusals": issued.get("refusals"),
            "caid_matches_recorded": issued.get("caid") == rec["caid"],
            # Measured, so the vector's disclaimer is not merely asserted:
            # CAID's canonicalization IS the ARP subject-digest construction.
            "caid_is_the_same_construction":
                issued.get("digest") == "sha256:" + sd,
            "cpb_verified": ok,
            "carries_typed_reference": carries_ref,
        }

    digests = [m["arp_subject_digest"] for m in measured.values()]
    base = measured["base"]["arp_subject_digest"]
    diverging = [k for k, m in measured.items()
                 if k != "base" and m["arp_subject_digest"] != base]
    no_ref = [k for k in diverging if not measured[k]["carries_typed_reference"]]

    return {
        # The property under test is stated in the vector and is ARP's, not
        # CPB's. requirement_source below carries that so a reader of the
        # result JSON cannot mistake this row for a CPB requirement.
        "requirement": True,
        "requirement_source": (
            "vector.property_tested (draft-hillier-scitt-arp); the vector also "
            "records that ARP-01 does not state it"),
        "observed": len(set(digests)) == 1,
        "detail": (
            f"CPB verified the typed reference in every record that carries "
            f"one ({'correct' if cpb_all_verified else 'UNEXPECTED'}); the "
            "differing members are outside the cited artifact's digest "
            f"context. ARP produced {len(set(digests))} distinct identifiers "
            f"from {len(measured)} records. The CAID count is NOT reported "
            "beside it: caid.canonicalize is byte-identical to arp.jcs_bytes "
            "and the CAID digest field is 'sha256:' + the ARP subject digest, "
            "so it is the same digest in two encodings and not a second "
            f"measurement. Diverging from base: {', '.join(diverging)}. "
            f"{len(no_ref)} of those carry no typed reference at all, which is "
            "why the cause is ARP's whole-object digest and not CPB's ignore "
            "rule."),
        "preconditions": {
            "cpb_verified_every_record_carrying_a_reference": cpb_all_verified,
            "every_recorded_arp_digest_reproduces":
                all(m["matches_recorded"] for m in measured.values()),
            "every_recorded_caid_reproduces":
                all(m["caid_matches_recorded"] for m in measured.values()),
            # Checked, and recorded as a caveat on the line above rather than
            # counted as corroboration: CAID's canonicalization IS ARP's.
            "caid_digest_is_the_same_construction_as_the_arp_digest":
                all(m["caid_is_the_same_construction"] for m in measured.values()),
            "every_action_object_is_accepted_by_the_caid_issuer":
                all(m["caid"] for m in measured.values()),
            "instability_is_not_specific_to_typed_references": bool(no_ref),
        },
        "extra": {
            "distinct_arp_identifiers": len(set(digests)),
            "records": len(measured),
            "measured": measured,
        },
    }


CHECKS = {
    "typed-ref-cpb01-01": check_01,
    "typed-ref-cpb01-02": check_02,
    "typed-ref-cpb01-03": check_03,
    "typed-ref-cpb01-04": check_04,
    "typed-ref-cpb01-05": check_05,
}

# What each class predicts about the gap between requirement and observation.
# None means the class makes no prediction about the reference library, which
# is a statement the runner is required to make out loud rather than fake.
PREDICTION = {
    "conformance_baseline": True,       # observed == requirement
    "revision_uplift_gap": False,       # observed != requirement
    "specification_question": False,
    "contributor_side_defect": False,
    "suite_coverage_gap": None,         # not applicable
}


def main():
    doc = json.load(open(ARGS.vectors))
    vectors = doc["vectors"]

    hr("=")
    print("CPB-01 typed-reference vectors -- ARP contribution")
    print(f"  target   {doc['target']}")
    print(f"  vectors  vectors/{os.path.basename(ARGS.vectors)}  sha256 "
          f"{hashlib.sha256(open(ARGS.vectors,'rb').read()).hexdigest()[:16]}...")
    print(f"  cpb lib  {os.path.basename(os.path.abspath(ARGS.cpb_repo))}/lib")
    print(f"  {len(vectors)} vectors")
    hr("=")

    rows, hard = [], []
    for v in vectors:
        vid, cls = v["id"], v["finding_class"]
        res = CHECKS[vid](v)
        predicted_equal = PREDICTION[cls]

        print()
        print(f"{vid}   [{cls}]   "
              f"{'MUST-FAIL' if v.get('must_fail') else 'PASS'}")
        for line in _wrap(v["description"], 92):
            print(f"    {line}")
        print(f"    spec        {v['spec_ref'].splitlines()[0][:88]}")
        print(f"    requires    "
              f"{'verified' if res['requirement'] else 'MUST NOT be verified'}")
        if res["observed"] is NOT_APPLICABLE:
            print("    observed    NOT APPLICABLE -- the reference library "
                  "cannot reach this vector")
        else:
            print(f"    observed    "
                  f"{'verified' if res['observed'] else 'not verified'}")
        for line in _wrap(res["detail"], 88):
            print(f"        {line}")

        # Preconditions first: a vector whose own preconditions fail cannot
        # support any prediction, so its prediction is not evaluated.
        pre = res.get("preconditions", {})
        pre_ok = all(pre.values())
        if pre:
            print(f"    precond     {sum(pre.values())}/{len(pre)} hold")
            for k, ok in pre.items():
                if not ok:
                    m = f"{vid}: precondition {k!r} does not hold."
                    hard.append(m)
                    print(f"        BROKEN  {k}")

        if predicted_equal is None:
            prediction_held = None
            print("    prediction  NOT APPLICABLE -- this class makes no claim "
                  "about the reference library")
        elif not pre_ok:
            prediction_held = None
            print("    prediction  NOT EVALUATED -- preconditions failed")
        else:
            actually_equal = (res["observed"] == res["requirement"])
            prediction_held = (actually_equal == predicted_equal)
            if prediction_held:
                print("    prediction  held")
            else:
                if predicted_equal:
                    m = (f"{vid}: class {cls} predicts the implementation "
                         "matches the requirement, and it does not. "
                         "Regression, or the vector is wrong.")
                else:
                    m = (f"{vid}: class {cls} predicts a gap between "
                         "requirement and implementation, and there is none. "
                         "Either it was closed -- in which case retire or "
                         "reclassify this vector deliberately -- or the vector "
                         "never tested what it claims.")
                hard.append(m)
                print(f"    PREDICTION  BROKEN -- {m}")

        rows.append({
            "id": vid,
            "finding_class": cls,
            "must_fail": bool(v.get("must_fail")),
            "requirement_verified": res["requirement"],
            # Which document imposes the requirement in the column above.
            # Rows 01-04 are CPB-01's; row 05 is ARP's. Without this a reader
            # of this file reads every row as a CPB requirement.
            "requirement_source": res.get(
                "requirement_source", f"{doc['target']}"),
            "observed_verified": res["observed"],
            "prediction_held": prediction_held,
            "preconditions": pre,
            "detail": res["detail"],
            "extra": res.get("extra", {}),
        })

    print()
    hr("=")
    by_class = {}
    for r in rows:
        by_class[r["finding_class"]] = by_class.get(r["finding_class"], 0) + 1
    print(f"  {len(rows)} vectors: " + ", ".join(
        f"{n} {c.replace('_', ' ')}" for c, n in sorted(by_class.items())))
    evaluated = [r for r in rows if r["prediction_held"] is not None]
    print(f"  {sum(1 for r in evaluated if r['prediction_held'])}/"
          f"{len(evaluated)} predictions held "
          f"({len(rows) - len(evaluated)} not applicable)")
    print("  one gap is the contributor's own (typed-ref-cpb01-05); it is "
          "counted here, not set aside")

    if hard:
        print()
        for m in hard:
            for line in _wrap(m, 96):
                print(f"  {line}")
        print(f"\n  TYPED-REF RUN: FAIL ({len(hard)} hard)")
    else:
        print("\n  TYPED-REF RUN: PASS -- every vector behaved as its class "
              "predicts, or declared that its class makes no prediction")
    hr("=")

    out = os.path.abspath(ARGS.json)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({
            "suite": doc["suite"],
            "target": doc["target"],
            "vectors_file": os.path.basename(ARGS.vectors),
            "vectors_sha256": hashlib.sha256(
                open(ARGS.vectors, "rb").read()).hexdigest(),
            "harness": "arp_reconcile.py v2.1",
            "harness_sha256": hashlib.sha256(
                open(os.path.join(HERE, "..", "harness", "arp_reconcile.py"),
                     "rb").read()).hexdigest(),
            "rows": rows,
            "hard_failures": hard,
        }, f, indent=2)
        f.write("\n")
    print(f"  machine-readable result written to "
          f"runs/{os.path.basename(out)}")
    return 1 if hard else 0


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
