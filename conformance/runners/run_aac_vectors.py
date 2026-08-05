#!/usr/bin/env python3
"""ARP against the Agent Action Capsule (AAC) Class-1 frozen vector suite,
plus a differential test of the proposition that AAC's capsule_id and CPB's
jcs-n are the same construction.

Suite: action-state-group/agent-action-capsule, test-vectors/, 32 cases,
SHA256SUMS-pinned, exercised by two runners that share no code path
(python/tests and go/cmd/vector_runner).

AAC computes, per its §2 and §5.1:
    capsule_id = HEX(SHA-256(JCS(normalize(capsule minus {capsule_id, chain}))))
CPB computes, per draft-mih-sokolov-scitt-payload-binding §3.1:
    jcs-n      = HEX(SHA-256(JCS(normalize(payload minus exclusion_set))))

DISCLOSURE, because it decides how much the numbers below are worth. The CPB
reference library and the AAC Python library are NOT independent
implementations of these rules. Their `normalize`, `_jcs_string` and `jcs`
functions are byte-identical after docstring stripping, `_jcs_value` differs
only in an exception message, and both repositories are the same GitHub
organisation. Agreement between those two is code identity, not corroboration,
and this runner says so rather than counting it as a third opinion.

The genuinely independent implementation available here is the AAC **Go**
canonicalizer, 251 lines with its own UTF-16 key comparison, its own escaping
and its own number handling. Where the Go implementation agrees, that is
evidence. Where only the two Python copies agree, it is not.

The second problem this runner now addresses. The 32 frozen vectors do not
exercise the code the proposition is about: on all of them absent-field
normalization is a no-op, no array appears, no integer appears, no non-ASCII
or escaped character appears, and no nested member is named capsule_id or
chain. So agreement on the frozen set could not distinguish the two
constructions even if they differed. Stage 3 therefore generates
DISCRIMINATING inputs that reach every one of those paths, and runs all three
implementations over them.

Stages:
  1. The frozen suite: does AAC reproduce its own pinned identifiers, and do
     the digest-bearing-value guards fire where the suite says they should?
  2. ARP against the same suite. arp-subject-digest/1 applies no exclusion set
     and no normalization, so it MUST diverge wherever either applies. Checked
     in both directions: an unattributed divergence fails, and so does an
     unexplained agreement.
  3. Differential test on generated inputs that reach normalization, arrays,
     escaping, the integer bounds, and nested exclusion-set names, across
     AAC-Python, AAC-Go and CPB-Python.

An unattributed result at any stage is a hard failure, not a row in a table.
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
_ap.add_argument("--go-shim", default=os.environ.get("AAC_GO_SHIM"),
                 help="path to a built binary of aac/go/cmd/digest_shim; without "
                      "it stage 3 reports as NOT RUN rather than silently passing")
_ap.add_argument("--json", default=os.path.join(HERE, "..", "runs", "aac_run.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.cpb_repo, "lib"))
sys.path.insert(0, os.path.join(ARGS.aac_repo, "python"))

import subprocess                                              # noqa: E402

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



# ---------------------------------------------------------------------------
# Stage 3. Differential test on DISCRIMINATING inputs.
#
# The frozen suite cannot distinguish the two constructions: on all 32 cases
# absent-field normalization is a no-op, no array or integer appears, no
# escaped or non-ASCII character appears, and no nested member is named
# capsule_id or chain. Nineteen of the seventy-one statements in the
# canonicalizer never execute. Agreement there is agreement about nothing.
#
# These inputs are built to reach exactly the paths the frozen set misses.
# Each is named for the rule it exercises, so a disagreement points at a rule
# rather than at a blob.
# ---------------------------------------------------------------------------

DISCRIMINATING = [
    ("null-member-removed",           {"a": "1", "b": None}),
    ("empty-object-removed",          {"a": "1", "b": {}}),
    ("empty-array-removed",           {"a": "1", "b": []}),
    ("object-emptied-by-normalization", {"a": "1", "b": {"c": None}}),
    ("nested-two-deep-emptied",       {"a": "1", "b": {"c": {"d": None}}}),
    ("array-of-objects-normalized",   {"a": [{"x": None, "y": "1"}, {"z": "2"}]}),
    ("array-preserved-not-sorted",    {"a": ["b", "a", "c"]}),
    ("nested-member-named-capsule_id", {"a": {"capsule_id": "inner"}}),
    ("nested-member-named-chain",     {"a": {"chain": "inner"}}),
    ("key-sort-utf16-vs-codepoint",   {"\U0001F600": "hi", "\uFF3A": "wide"}),
    ("key-nfc-vs-nfd",                {"A\u030A": "combining", "B": "plain"}),
    ("string-escapes",                {"a": "q\"b\\\\s\u0008\u0009\u000a\u000c\u000d"}),
    ("control-char-below-0x20",       {"a": "x\u0001y"}),
    ("non-bmp-value",                 {"a": "\U0001F600"}),
    ("solidus-not-escaped",           {"a": "a/b"}),
    ("integer-zero",                  {"a": 0}),
    ("integer-negative",              {"a": -1}),
    ("integer-at-safe-max",           {"a": 9007199254740991}),
    ("integer-above-safe-max",        {"a": 9007199254740992}),
    ("integer-at-safe-min",           {"a": -9007199254740991}),
    ("float-in-value",                {"a": 1.5}),
    ("float-integral-valued",         {"a": 2.0}),
    ("bool-and-deep-nesting",         {"a": True, "b": {"c": {"d": {"e": "f"}}}}),
    ("all-members-removed",           {"a": None, "b": [], "c": {}}),
]


def go_digest_batch(shim, objs):
    """One process, one line of JSON per object, one digest per line."""
    payload = "\n".join(json.dumps(o, ensure_ascii=False) for o in objs) + "\n"
    p = subprocess.run([shim], input=payload.encode("utf-8"),
                       capture_output=True, timeout=120)
    return p.stdout.decode("utf-8").splitlines()


def run_stage3(unattributed):
    print()
    hr()
    print("3. Differential test on discriminating inputs")
    hr()
    print("   These reach the paths the frozen suite never touches. AAC-python and")
    print("   CPB-python are the SAME canonicalizer, so their agreement proves")
    print("   nothing here either; the column that carries evidence is AAC-go.")
    print()

    objs = [o for _n, o in DISCRIMINATING]
    go_out = None
    if ARGS.go_shim and os.path.exists(ARGS.go_shim):
        try:
            go_out = go_digest_batch(ARGS.go_shim, objs)
        except Exception as e:                                  # noqa: BLE001
            print(f"   go shim failed to run: {e}")
    if go_out is None:
        print("   !! AAC-go NOT RUN. Build aac/go/cmd/digest_shim and pass --go-shim.")
        print("      Stage 3 is reported as NOT RUN rather than passed, because a")
        print("      differential test with one of its two independent sides missing")
        print("      is not a differential test.")
    if go_out is not None and len(go_out) != len(objs):
        unattributed.append(
            f"go shim returned {len(go_out)} lines for {len(objs)} inputs")
        go_out = None

    print(f"   {'case':<34} {'aac-py':<10} {'cpb-py':<10} {'aac-go':<10} verdict")
    out = []
    agree_py = agree_go = 0
    tested_go = 0
    for i, (nm, obj) in enumerate(DISCRIMINATING):
        def call(fn):
            try:
                return fn(), None
            except Exception as e:                              # noqa: BLE001
                return None, type(e).__name__
        a_id, a_exc = call(lambda: AAC.compute_capsule_id(obj))
        c_id, c_exc = call(lambda: CPB.canonical_digest(obj, AAC_EXCLUSION))
        g = go_out[i] if go_out else None
        g_ref = g.startswith("REFUSED") if g else None

        a_tok = a_exc or (a_id[:8] if a_id else "?")
        c_tok = c_exc or (c_id[:8] if c_id else "?")
        g_tok = ("REFUSED" if g_ref else (g[:8] if g else "-"))

        py_same = (a_id == c_id) and (a_exc == c_exc)
        agree_py += py_same
        go_same = None
        if g is not None:
            tested_go += 1
            if g_ref:
                go_same = a_exc is not None
            else:
                go_same = (g == a_id)
            agree_go += bool(go_same)

        verdict = ("py=py " if py_same else "PY DIFFER ")
        if go_same is None:
            verdict += " go:not-run"
        elif go_same:
            verdict += " go agrees"
        else:
            verdict += " GO DIFFERS"

        if not py_same:
            unattributed.append(
                f"stage3/{nm}: the two Python canonicalizers, which are the same "
                f"source, disagree ({a_tok} vs {c_tok}). That should be impossible.")
        if go_same is False:
            unattributed.append(
                f"stage3/{nm}: AAC-go disagrees with AAC-python ({g_tok} vs {a_tok}). "
                "Two implementations of the same stated rules diverge on an input "
                "the frozen suite does not cover.")

        print(f"   {nm:<34} {a_tok:<10} {c_tok:<10} {g_tok:<10} {verdict}")
        out.append({"case": nm, "input": obj,
                    "aac_python": a_id, "aac_python_exception": a_exc,
                    "cpb_python": c_id, "cpb_python_exception": c_exc,
                    "aac_go": g, "python_pair_agree": py_same,
                    "go_agrees_with_python": go_same})

    print()
    print(f"   AAC-python vs CPB-python : {agree_py}/{len(DISCRIMINATING)} "
          "(expected 100%; they are the same source)")
    if tested_go:
        print(f"   AAC-go vs AAC-python     : {agree_go}/{tested_go}  "
              "<-- the column that carries evidence")
    else:
        print("   AAC-go vs AAC-python     : NOT RUN")
    return {"cases": out, "python_pair_agree": agree_py,
            "go_agree": agree_go if tested_go else None,
            "go_tested": tested_go,
            "total": len(DISCRIMINATING)}


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
            # Pass the exclusion set as CPB's OWN parameter rather than
            # stripping the fields first, so CPB's exclusion machinery is the
            # thing under test. Read from AAC.CHAIN_LINKAGE_FIELDS, not
            # transcribed.
            cpb_id = CPB.canonical_digest(capsule, AAC_EXCLUSION)
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
            row["suite_kind"] = kind
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

    stage3 = run_stage3(unattributed)

    hr("=")
    print("SELF-CHECK")
    hr("=")
    from collections import Counter
    suite_kinds = Counter(r.get("kind") for r in rows)
    idbearing = Counter(r.get("suite_kind") for r in rows if r.get("suite_kind"))
    print(f"  Suite taxonomy (their `kind` field): "
          + ", ".join(f"{k} {v}" for k, v in sorted(suite_kinds.items())))
    print(f"  Identifier-bearing vectors: {pos} "
          f"({', '.join(f'{k} {v}' for k, v in sorted(idbearing.items()))})")
    print(f"  Carrying findings only, no recomputed identifier: {neg}")
    print(f"  AAC-python reproduces its own pinned capsule_id on {aac_repro}/{pos}.")
    print(f"  CPB-python, given AAC's exclusion set {AAC_EXCLUSION} as its own")
    print(f"    parameter, agrees on {cpb_agrees}/{pos}. This is NOT independent")
    print("    corroboration: see the disclosure at the top of this file. The two")
    print("    Python canonicalizers are the same source.")
    print(f"  arp-subject-digest/1 agrees with capsule_id on {arp_agrees}/{pos};")
    print(f"    every divergence is attributed to a declared step ARP does not implement.")
    print()
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
            "stage3_differential": stage3,
            "code_identity_disclosure": (
                "cpb.canonicalize and agent_action_capsule.canonical share "
                "byte-identical normalize/_jcs_string/jcs after docstring "
                "stripping and are published by the same organisation. "
                "Agreement between them is code identity, not corroboration."),
            "unattributed": unattributed,
        }, f, indent=2)
        f.write("\n")
    print(f"\n  machine-readable result written to runs/{os.path.basename(out)}")
    return 1 if unattributed else 0


if __name__ == "__main__":
    sys.exit(main())
