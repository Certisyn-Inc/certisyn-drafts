#!/usr/bin/env python3
"""Defeat check_self_claims.py nine times, on purpose.

A checker that has never failed is indistinguishable, in a run transcript, from
a checker that cannot fail. This applies the rule the conformance tree already
carries for every other class: each check is credited only where a mutant
designed to break it actually broke it, and broke NOTHING ELSE. A mutant that
fails the class for an unintended reason credits nothing.

Nine checks, nine mutants, nine kills, each on its own designed row.

No arguments. Standard library only. The draft is never modified on disk.
"""
import re, sys, os, importlib
import check_self_claims as C

DRAFT = os.path.join(os.path.dirname(__file__), "..", "..", "draft-hillier-scitt-arp.md")

# (check name it must break, description, old, new)
MUTANTS = [
    ("Bilateral Register Agreement declared items",
     "understate the Agreement array length by one",
     "array has **exactly thirty-three", "array has **exactly thirty-two"),

    ("Well-Known URI registrations",
     "drop one from the registry lead sentence",
     "Seven entries are requested in the Well-Known", "Six entries are requested in the Well-Known"),

    ("Verdict Arithmetic operators",
     "claim a fifth verdict operator",
     "initial four are", "initial five are"),

    ("Server-recorded Divergence Axes with a stated member form",
     "revert the member-form rule to four axes",
     "the rule is stated for all five axes and not four",
     "the rule is stated for all four axes and not three"),

    ("Retroactive evaluation triggers",
     "leave the fifth trigger out of the defining section, as it was two hours ago",
     "`credential-revocation` or `register-record-correction`, and the identifier",
     "`credential-revocation`, and the identifier"),

    ("Signature carriers named in Signature Malleability",
     "claim a seventh signature carrier",
     "The sixth was found after the first five had been repaired",
     "The seventh was found after the first six had been repaired"),

    ("Verification Outcomes",
     "claim a fifth verification outcome",
     "four conditions that arrive at \"refuse\"", "five conditions that arrive at \"refuse\""),

    ("Representation classes",
     "claim a ninth representation class",
     "The section names the eight representation classes",
     "The section names the nine representation classes"),

    ("'this document already requires that ordering of' names sets that are ordered",
     "leave the assertion standing and silence the sort rule on the very "
     "collection it names, which is the defect the assertion actually had",
     "identifiers, sorted in bytewise lexicographic order of the deterministic CBOR\n  encoding of each element;",
     "identifiers;"),

    ("Policy Parameters Document elements",
     "understate the Policy Parameters payload arity by one",
     "the six-element CBOR array of: a Publication Timestamp",
     "the five-element CBOR array of: a Publication Timestamp"),
]


def run_against(text):
    """Return {check name: 'ok'|'FAIL'|'SKIP'}."""
    out = {}
    for name, fn in C.CHECKS:
        try:
            stated, actual, _ = fn(text)
        except Exception:
            out[name] = "FAIL"; continue
        if stated is None or actual is None:
            out[name] = "SKIP"
        else:
            out[name] = "ok" if stated == actual else "FAIL"
    return out


def main():
    base_text = open(DRAFT, encoding="utf-8").read()
    base = run_against(base_text)

    print("=" * 78)
    print("MUTATION TEST  --  one designed kill per check, and nothing else broken")
    print("=" * 78)

    unclean = [k for k, v in base.items() if v != "ok"]
    if unclean:
        print("  The unmutated document does not pass cleanly, so no mutant can be")
        print("  credited. Not ok:", ", ".join(unclean))
        return 1
    print(f"  baseline: {len(base)} checks, all ok\n")

    kills = 0
    for target, why, old, new in MUTANTS:
        if base_text.count(old) != 1:
            print(f"  NO-OP    {target}")
            print(f"           anchor matched {base_text.count(old)} times, mutant not applied")
            continue
        got = run_against(base_text.replace(old, new, 1))
        broke = {k for k, v in got.items() if v != "ok"}
        if broke == {target}:
            kills += 1
            print(f"  KILL     {target}")
            print(f"           mutant: {why}")
        elif target not in broke:
            print(f"  SURVIVED {target}")
            print(f"           mutant: {why}")
            print(f"           the check did not notice. It is not testing what it claims to test.")
        else:
            print(f"  IMPRECISE {target}")
            print(f"           mutant: {why}")
            print(f"           also broke: {', '.join(sorted(broke - {target}))}")
            print(f"           credited to no check: a mutant that fails the class for an")
            print(f"           unintended reason establishes nothing about the intended one.")

    print("-" * 78)
    print(f"{len(MUTANTS)} mutants, {kills} killed on their designed row")
    print()
    print("Does not establish: that the checks cover every self-claim the document")
    print("makes. Only that each check that exists detects the defect it was written")
    print("for, and does not report it for a different reason.")
    return 0 if kills == len(MUTANTS) else 1


if __name__ == "__main__":
    sys.exit(main())
