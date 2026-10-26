#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 b7n0de
"""Generate five CAP-1 duplicate-name probes from PV-01 and PV-03.
The base vectors are read from the input directory. The generated files are modified copies.

usage: generate_probes.py <cap-1/src/vectors> <output directory>
Originally written against cap-1 at 0980d32. The supplied PV-01 and PV-03 inputs reproduce the five recorded probe hashes.
"""
import json, os, re, sys


def main(v, out):
    os.makedirs(out, exist_ok=True)
    pv1 = json.load(open(os.path.join(v, "PV-01.json"), encoding="utf-8"))
    roh1 = json.dumps(pv1, indent=1)
    roh3 = open(os.path.join(v, "PV-03.json"), encoding="utf-8").read()
    el = pv1["strata"][0]["eligible"]
    alt = f'"eligible": {el},'
    assert roh1.count(alt) == 1

    def write(name, text):
        json.loads(text)  # still readable by a last-wins parser
        # LF on every platform, as .gitattributes keeps the checked-out files
        open(os.path.join(out, name + ".json"), "w", encoding="utf-8", newline="\n").write(text)

    # S11: PV-01, eligible twice with the same value
    write("S11_same_value", roh1.replace(alt, f'"eligible": {el},\n   "eligible": {el},', 1))
    # S12: PV-01, a second spelling of eligible through an escape, with a value that breaks R1
    write("S12_escaped_spelling", roh1.replace(alt, f'"eligible": {el},\n   "\\u0065ligible": {el + 7},', 1))
    # S13: PV-01, top-level profile twice, first cap/0, then cap/1
    t = roh1.replace('"profile": "cap/1",', '"profile": "cap/0",\n "profile": "cap/1",', 1)
    assert t != roh1
    write("S13_top_level_profile", t)
    # S14: PV-01, subject.digest.algorithm twice, first SHA-256, then MD5
    t = roh1.replace('"algorithm": "SHA-256",', '"algorithm": "SHA-256",\n   "algorithm": "MD5",', 1)
    assert t != roh1
    write("S14_deep_algorithm", t)
    # S15: PV-03, integrity.complete three times, true, false, true
    m = re.search(r'("complete"\s*:\s*)(true|false)', roh3)
    write("S15_threefold_complete", roh3[:m.start()] + '"complete": true,\n  "complete": false,\n  '
          + roh3[m.start():].replace('"complete": false', '"complete": true', 1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
