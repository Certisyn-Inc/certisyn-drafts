#!/bin/sh
# CAP-1 — the whole class, one command.
#
# Parts 1, 2, 3, 5 and 6 need Node 18+ and Python 3 and nothing else.
# Part 4 additionally needs playwright and a chromium build, because it runs the
# single-file HTML verifier in a real browser engine. If playwright is absent,
# part 4 declares itself not run rather than passing quietly, and the rest of the
# class still completes. A class that reports green over a part it skipped is the
# exact defect this profile exists to refuse.
set -e
cd "$(dirname "$0")"
echo; echo "################ 1  CONFORMANCE CLASS ################"; node run.mjs
echo; echo "################ 2  VERIFIER MUTATION ################"; node mutate.mjs
echo; echo "################ 3  CROSS-IMPLEMENTATION #############"; node crosscheck.mjs >/dev/null; python3 crosscheck.py
echo; echo "################ 4  BROWSER IMPLEMENTATION ###########"
if node browsercheck.mjs; then :; else
  status=$?
  if [ "$status" -eq 3 ]; then
    echo "PART 4 NOT RUN — playwright absent. Disposition: unavailable."
    echo "The other five parts are unaffected. Record this, do not ignore it."
  else
    echo "PART 4 FAILED"; exit "$status"
  fi
fi
echo; echo "################ 5  SELF-ATTESTATION #################"; node selfattest.mjs
echo; echo "################ 6  LIVE ENGINE, TWO RUNS ############"; node demo-live.mjs
echo; echo "################ ALL PARTS ACCOUNTED #################"
