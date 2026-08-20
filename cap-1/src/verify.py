#!/usr/bin/env python3
# =============================================================================
# CAP-1 CONFORMANCE VERIFIER — SECOND IMPLEMENTATION
#
# Written from the prose of the eight normative rules in
# CS-SPEC-CAP-1-Coverage-Attestation-Profile, not ported from verify.mjs.
# Standard library only. No dependencies, no network, no clock.
#
# WHAT THIS CLOSES AND WHAT IT DOES NOT.
#   Closes: IMPLEMENTATION independence. Two implementations, two languages,
#           two authors' readings of one text, agreeing on every vector.
#   Does NOT close: AUTHOR independence. Both implementations and the vectors
#           originate with the same party, so a misreading shared between them
#           is invisible to this check. The class becomes genuinely two-sided
#           the first time it refuses a document written elsewhere.
#
# Where this implementation had to make a judgement the text did not settle,
# the judgement is recorded in a DIVERGENCE NOTE beside the rule. Those notes
# are the specification defects this exercise exists to surface.
# =============================================================================
import json, re, sys

DISPOSITIONS = {
    "not_applicable", "disabled_by_policy", "unsupported_input",
    "resource_exhausted", "failed", "unavailable", "out_of_scope", "withheld",
}
BASIS_KINDS = {"catalogue", "enumeration", "declared"}
HEX = re.compile(r"^[0-9a-f]{32,128}$")

# A hard stop is a disposition that means the unit was dispatched or should have
# been, and did not produce a result. R7 turns on this set.
# DIVERGENCE NOTE (R7): the text says "failed, exhausted or was unavailable".
# It does not say whether out_of_scope or disabled_by_policy count. Read
# narrowly: both are deliberate, accounted decisions, not incomplete execution.
HARD_STOPS = {"failed", "resource_exhausted", "unavailable"}


def verify(doc):
    """Return (ok, failures). Each failure is (rule, grounds, evidence)."""
    f = []
    def fail(rule, grounds, evidence=None):
        f.append({"rule": rule, "grounds": grounds, "evidence": evidence or {}})

    # R0 — shape. Refuse rather than coerce.
    if not isinstance(doc, dict):
        return False, [{"rule": "R0-shape", "grounds": "not an object", "evidence": {}}]
    if doc.get("profile") != "cap/1":
        fail("R0-shape", "profile is not cap/1", {"profile": doc.get("profile")})
    subj = doc.get("subject")
    if not isinstance(subj, dict) or not isinstance(subj.get("ref"), str):
        fail("R0-shape", "subject.ref absent", {})
    strata = doc.get("strata")
    if not isinstance(strata, list) or not strata:
        fail("R0-shape", "no strata", {})
    integ = doc.get("integrity")
    if not isinstance(integ, dict) or not isinstance(integ.get("complete"), bool):
        fail("R0-shape", "integrity.complete absent", {})
    if f:
        return False, f

    ids = set()
    for s in strata:
        at = "strata[%s]" % s.get("id", "?")

        sid = s.get("id")
        if not isinstance(sid, str) or sid in ids:
            fail("R0-shape", "stratum id absent or duplicated", {"at": at})
        ids.add(sid)

        # R1 — no silent remainder.
        unex = s.get("unexamined")
        if not isinstance(unex, list):
            fail("R1-no-silent-remainder", "unexamined is not an array", {"at": at})
            continue
        eligible, examined = s.get("eligible"), s.get("examined")
        if isinstance(eligible, int) and isinstance(examined, int):
            if examined + len(unex) != eligible:
                fail("R1-no-silent-remainder",
                     "eligible does not equal examined plus accounted unexamined",
                     {"at": at, "eligible": eligible, "examined": examined,
                      "accounted": len(unex), "remainder": eligible - examined - len(unex)})

        for u in unex:
            # R2 — closed disposition vocabulary, and every unit names itself.
            if u.get("disposition") not in DISPOSITIONS:
                fail("R2-closed-disposition", "disposition outside the closed vocabulary",
                     {"at": at, "unit": u.get("unit"), "disposition": u.get("disposition")})
            if not isinstance(u.get("unit"), str) or not u.get("unit"):
                fail("R2-closed-disposition", "unexamined entry names no unit", {"at": at})
            # R3 — withholding is digest-bound.
            if u.get("disposition") == "withheld" and not HEX.match(str(u.get("withheld_digest", ""))):
                fail("R3-withholding-digest-bound",
                     "withheld unit carries no digest of the withheld value",
                     {"at": at, "unit": u.get("unit")})

        # R4 — the denominator has a basis.
        b = s.get("basis") or {}
        kind = b.get("kind")
        if kind not in BASIS_KINDS:
            fail("R4-denominator-basis", "basis.kind absent or outside vocabulary",
                 {"at": at, "kind": kind})
        elif kind == "catalogue" and not HEX.match(str(b.get("catalogue_digest", ""))):
            fail("R4-denominator-basis", "catalogue basis without a catalogue digest", {"at": at})
        elif kind == "enumeration" and not str(b.get("enumeration_method", "")):
            fail("R4-denominator-basis", "enumeration basis without a stated method", {"at": at})

        # R5 — counts well formed.
        if not (isinstance(eligible, int) and isinstance(examined, int)) \
           or isinstance(eligible, bool) or isinstance(examined, bool) \
           or eligible < 0 or examined < 0:
            fail("R5-counts-well-formed",
                 "eligible or examined is not a non-negative integer", {"at": at})
        elif examined > eligible:
            fail("R5-counts-well-formed", "examined exceeds eligible",
                 {"at": at, "eligible": eligible, "examined": examined})

    # R6 — absence is scoped.
    for a in doc.get("absence_assertions") or []:
        if not a.get("stratum") or a.get("stratum") not in ids:
            fail("R6-absence-is-scoped",
                 "absence assertion names no stratum, or an unknown one",
                 {"assertion": str(a.get("assertion", ""))[:90], "stratum": a.get("stratum")})

    # R7 — incomplete execution may not be reported as clean.
    stops = ["%s:%s:%s" % (s.get("id"), u.get("unit"), u.get("disposition"))
             for s in strata for u in (s.get("unexamined") or [])
             if u.get("disposition") in HARD_STOPS]
    if stops and integ.get("complete") is True:
        fail("R7-incomplete-not-clean",
             "integrity.complete is true while units failed, exhausted or were unavailable",
             {"stops": stops[:6], "count": len(stops)})
    if integ.get("complete") is False and not str(integ.get("capped_to") or ""):
        fail("R7-incomplete-not-clean",
             "integrity.complete is false and no capped_to verdict is stated", {})

    # R8 — supports bounds citation.
    cited = {a.get("stratum") for a in (doc.get("absence_assertions") or [])}
    for s in strata:
        if s.get("id") in cited:
            sup = s.get("supports")
            if not (isinstance(sup, list) and sup):
                fail("R8-supports-bounds-citation",
                     "stratum is cited by an absence assertion but states no supported claim classes",
                     {"at": "strata[%s]" % s.get("id")})

    return (len(f) == 0), f


def summarise(doc):
    rows = []
    for s in doc.get("strata") or []:
        by = {}
        for u in s.get("unexamined") or []:
            by[u.get("disposition")] = by.get(u.get("disposition"), 0) + 1
        el = s.get("eligible") or 0
        rows.append({"id": s.get("id"), "population": s.get("population"),
                     "eligible": el, "examined": s.get("examined"),
                     "fraction": (s.get("examined") / el) if el else 0.0,
                     "dispositions": by})
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 verify.py <cap-1.json>", file=sys.stderr); sys.exit(2)
    try:
        d = json.load(open(sys.argv[1], encoding="utf-8"))
    except Exception as e:
        print("REFUSED  unreadable or invalid JSON:", e); sys.exit(1)
    ok, fails = verify(d)
    if ok:
        print("CONFORMS  cap/1")
        for s in summarise(d):
            disp = "  ".join("%s=%d" % kv for kv in s["dispositions"].items()) or "none"
            print("  %-14s %6d / %-6d %5.1f%%   %s"
                  % (s["id"], s["examined"], s["eligible"], 100 * s["fraction"], disp))
        sys.exit(0)
    print("REFUSED  cap/1")
    for x in fails:
        print("  %s  %s\n      %s" % (x["rule"], x["grounds"], json.dumps(x["evidence"])))
    sys.exit(1)
