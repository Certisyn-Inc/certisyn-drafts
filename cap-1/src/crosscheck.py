#!/usr/bin/env python3
"""Cross-implementation agreement check.

Runs BOTH verifiers over the identical vector bytes and reports any disagreement.
A disagreement is not a bug to be silenced. It is a specification ambiguity, and
the text is what gets corrected.
"""
import json, subprocess, sys, hashlib, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from verify import verify as py_verify

man = json.load(open(os.path.join(HERE, "vectors", "manifest.json"), encoding="utf-8"))

def js_result(path):
    p = subprocess.run(["node", os.path.join(HERE, "verify.mjs"), path],
                       capture_output=True, text=True)
    return p.returncode == 0, p.stdout

rows, disagree, wrong = [], [], []
print("CROSS-IMPLEMENTATION AGREEMENT")
print("=" * 78)
print("  JavaScript verify.mjs  against  Python verify.py, over identical bytes")
print()
for m in man:
    path = os.path.join(HERE, "vectors", m["id"] + ".json")
    doc = json.load(open(path, encoding="utf-8"))
    py_ok, py_f = py_verify(doc)
    js_ok, js_out = js_result(path)
    agree = (py_ok == js_ok)
    expect_ok = (m["expect"] == "conform")
    correct = (py_ok == expect_ok) and (js_ok == expect_ok)
    # for negatives, both must also fire the targeted rule
    rule_ok = True
    if m["kind"] == "negative":
        py_rules = {x["rule"] for x in py_f}
        rule_ok = (m["rule"] in py_rules) and (m["rule"] in js_out)
    ok = agree and correct and rule_ok
    if not agree: disagree.append(m["id"])
    if not (correct and rule_ok): wrong.append(m["id"])
    rows.append({"id": m["id"], "kind": m["kind"], "expect": m["expect"],
                 "js": "conform" if js_ok else "refuse",
                 "py": "conform" if py_ok else "refuse",
                 "rule_targeted": m.get("rule"), "agree": agree, "ok": ok})
    mark = "OK  " if ok else ("DISAGREE" if not agree else "WRONG")
    print("  %-6s %-8s js=%-8s py=%-8s %s" %
          (m["id"], m["kind"], rows[-1]["js"], rows[-1]["py"], mark))

print()
print("=" * 78)
print("  vectors            %d" % len(rows))
print("  disagreements      %s" % (", ".join(disagree) if disagree else "none"))
print("  incorrect outcomes %s" % (", ".join(wrong) if wrong else "none"))
rec = {
    "class": "cap-1-cross-implementation/1.0.0",
    "implementations": ["verify.mjs (JavaScript, Node built-ins)",
                        "verify.py (Python, standard library)"],
    "vectors": len(rows), "disagreements": disagree, "incorrect": wrong,
    "agreement": len(disagree) == 0 and len(wrong) == 0,
    "establishes": ("Implementation independence: two implementations in two languages, "
                    "written from the specification text rather than ported, agree on every "
                    "vector and every targeted rule."),
    "does_not_establish": ("Author independence. Both implementations and the vectors "
                           "originate with the same party, so a misreading shared between "
                           "them is invisible to this check. The class becomes two-sided the "
                           "first time it refuses a document written elsewhere."),
    "results": rows,
}
rec["record_digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
json.dump(rec, open(os.path.join(HERE, "runs", "cross_implementation_run.json"), "w"), indent=1)
print()
print("RESULT  %s" % ("PASS   two implementations, full agreement"
                      if rec["agreement"] else "FAIL   see disagreements above"))
print("RECORD  runs/cross_implementation_run.json   sha256 %s" % rec["record_digest"])
sys.exit(0 if rec["agreement"] else 1)
