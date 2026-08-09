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

# Files section 6 is expected to account for. Runs are not section 6's business;
# their hashes live in section 5 and are checked separately below.
TRACKED_DIRS = ("harness", "runners", "vectors")
TRACKED_SUFFIX = (".py", ".json", ".go")

# Section 5 records run hashes in a two-line layout -- the path with its
# headline result on one line, the digest on the next -- which the section 6
# regex does not match. That is why section 5 was the one part of this manifest
# nothing checked, and why two of its entries went stale without anything
# noticing: cpb_run.json after a regeneration, and arp_adapter_run.json by a
# copy-paste that gave it the typed-reference run's digest. A run hash changing
# is exactly the event section 5 exists to record, so it is checked here rather
# than excused.
SECTION5 = re.compile(
    r"^\s{4}(runs/\S+)[^\n]*\n(?:[^\n]*\n)?\s+sha256 ([0-9a-f]{64})", re.M)

CRLF_NOTE = """\
  Every digest above that is marked (line endings) matches once CRLF is
  normalised to LF. That is a checkout artefact, not a content difference:
  git's core.autocrlf rewrote these files on the way out of the object store,
  so the bytes on disk are not the bytes the manifest records and no
  content-addressed check over them can pass.

  This repository ships a .gitattributes that pins the working tree to LF, so
  a fresh checkout does not have the problem. A working tree created before
  that file existed still does. Either re-checkout the affected paths

      git rm --cached -r . && git reset --hard

  or clone afresh with

      git -c core.autocrlf=false clone <url>

  and re-run. Reported rather than normalised away, because a reader who does
  not have the recorded bytes should be told so."""


def digest_of(path, recorded):
    """SHA-256 of the file, plus whether a mismatch is a line-ending artefact.

    Returns (actual_digest, is_crlf_artefact). A file whose LF-normalised form
    matches the record has the right content and the wrong bytes, which is a
    different failure from a file that has changed, and saying which is the
    whole point of a manifest.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    actual = hashlib.sha256(raw).hexdigest()
    if actual == recorded or b"\r\n" not in raw:
        return actual, False
    normalised = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    return actual, normalised == recorded


def main():
    manifest = os.path.join(ROOT, "REPRODUCE.md")
    text = io.open(manifest, encoding="utf-8").read()

    recorded = {}
    for m in re.finditer(r"^\s{4,}([0-9a-f]{64})\s+(\S+)", text, re.M):
        recorded[m.group(2)] = m.group(1)

    problems = []
    crlf_hits = 0

    def check(rel, digest, where=""):
        nonlocal crlf_hits
        path = os.path.join(ROOT, rel)
        tag = f"  ({where})" if where else ""
        if not os.path.exists(path):
            problems.append(
                f"MISSING   {rel}{tag}  (recorded {digest[:12]})")
            return
        actual, crlf = digest_of(path, digest)
        if actual == digest:
            return
        if crlf:
            crlf_hits += 1
        problems.append(
            f"MISMATCH  {rel}{tag}"
            + ("  [line endings]" if crlf else "") + "\n"
            f"            recorded {digest}\n"
            f"            actual   {actual}")

    for rel, digest in sorted(recorded.items()):
        check(rel, digest)

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

    # Section 5: the run hashes.
    run_recorded = {}
    for m in SECTION5.finditer(text):
        run_recorded[m.group(1)] = m.group(2)
    for rel, digest in sorted(run_recorded.items()):
        check(rel, digest, "section 5")
    seen = {}
    for rel, digest in run_recorded.items():
        seen.setdefault(digest, []).append(rel)
    for digest, rels in sorted(seen.items()):
        if len(rels) > 1:
            problems.append(
                "DUPLICATE section 5 digest " + digest[:12] + " recorded for "
                + ", ".join(sorted(rels)) + " -- two distinct files cannot "
                "share a digest, so at least one entry is a copy-paste")
    run_dir = os.path.join(ROOT, "runs")
    if os.path.isdir(run_dir):
        on_disk = {"runs/" + fn for fn in os.listdir(run_dir)
                   if fn.endswith(".json")}
        for u in sorted(on_disk - set(run_recorded)):
            print(f"  note: {u} is in runs/ and is not recorded in section 5")

    print(f"REPRODUCE.md section 6 records {len(recorded)} digests over "
          f"{len(present)} tracked files; section 5 records "
          f"{len(run_recorded)} run digests.")
    if problems:
        print()
        for p in problems:
            print("  " + p)
        print(f"\n{len(problems)} problem(s). MANIFEST: FAIL")
        if crlf_hits:
            print()
            print(CRLF_NOTE)
        return 1
    print("Every recorded digest matches, every listed path exists, and no "
          "tracked file is unlisted.")
    print("MANIFEST: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
