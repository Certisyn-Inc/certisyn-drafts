#!/usr/bin/env python3
"""Check every hash REPRODUCE.md records against the tree it describes.

Two hashes in REPRODUCE.md were stale when this was written: arp_eatf.py and
run_outcome_vectors.py had both changed in the transcript-path fix and their
recorded digests were never refreshed. Nothing caught it, because a manifest
that is only read by humans is not checked by anything.

A reproduction manifest whose own numbers are wrong is worse than no manifest:
it invites a reader to conclude the artefact was tampered with when in fact
the record was simply not updated. So the manifest is now machine-checked.

Run with no arguments. Exit 0 iff every recorded digest matches, every listed
path exists, and no script or vector in the tree is missing from the manifest.
"""

import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# Files the manifest is expected to account for. Runs are excluded: their
# hashes live in section 5 and change legitimately whenever a corpus moves.
TRACKED_DIRS = ("harness", "runners", "vectors")
TRACKED_SUFFIX = (".py", ".json", ".go")


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    manifest = os.path.join(ROOT, "REPRODUCE.md")
    text = io.open(manifest, encoding="utf-8").read()

    recorded = {}
    for m in re.finditer(r"^\s{4,}([0-9a-f]{64})\s+(\S+)", text, re.M):
        recorded[m.group(2)] = m.group(1)

    problems = []
    for rel, digest in sorted(recorded.items()):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            problems.append(f"MISSING   {rel}  (recorded {digest[:12]})")
            continue
        actual = sha256(path)
        if actual != digest:
            problems.append(
                f"MISMATCH  {rel}\n"
                f"            recorded {digest}\n"
                f"            actual   {actual}")

    # The other direction: a script in the tree that the manifest never names.
    # A manifest that silently omits a file cannot be used to check the tree.
    present = set()
    for d in TRACKED_DIRS:
        base = os.path.join(ROOT, d)
        for dirpath, _dirs, files in os.walk(base):
            if "__pycache__" in dirpath:
                continue
            for fn in files:
                if fn.endswith(TRACKED_SUFFIX):
                    present.add(os.path.relpath(
                        os.path.join(dirpath, fn), ROOT).replace(os.sep, "/"))
    unlisted = sorted(present - set(recorded))
    for u in unlisted:
        problems.append(f"UNLISTED  {u}  (in the tree, absent from REPRODUCE.md)")

    print(f"REPRODUCE.md records {len(recorded)} digests; "
          f"{len(present)} tracked files in the tree.")
    if problems:
        print()
        for p in problems:
            print("  " + p)
        print(f"\n{len(problems)} problem(s). MANIFEST: FAIL")
        return 1
    print("Every recorded digest matches, every listed path exists, and no "
          "tracked file is unlisted.")
    print("MANIFEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
