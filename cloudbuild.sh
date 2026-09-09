#!/usr/bin/env bash
# Cloud-container equivalent of build-draft.ps1.
#
# Verified 2026-08-09: from the unmodified wip/revision-03 source this
# reproduces the Windows-built draft-hillier-scitt-arp.txt byte-for-byte
# (3,752 lines, zero diff after CRLF normalisation).
#
# Why it is built the way it is:
#   - rubygems.org is not on this container's proxy allowlist, so
#     `gem install kramdown-rfc2629` returns 403. github.com IS reachable,
#     so 1.7.39 is run straight from a clone of cabo/kramdown-rfc.
#   - apt's ruby-kramdown-rfc2629 is 1.6.22 and does NOT match: it drops the
#     <?line?> markers, the list type="1" attributes and the combined
#     <references> wrapper. Do not fall back to it.
#   - Deps come from apt (ruby-kramdown 2.4.0, ruby-kramdown-parser-gfm,
#     ruby-unicode-blocks, ruby-net-http-persistent) and must be run under
#     /usr/bin/ruby3.2, not the rbenv ruby, which cannot see them.
#   - bib.ietf.org AND datatracker.ietf.org are both blocked here, so the
#     refcache cannot be seeded or renewed. It is copied from the Windows
#     machine. KRAMDOWN_REFCACHETTL is set absurdly high so kramdown-rfc
#     never tries to renew a "stale" entry and die on the 403.
#
# Judge success on the artifact, not the exit code (same lesson as Windows).

set -uo pipefail
cd "$(dirname "$0")"

DRAFT=draft-hillier-scitt-arp
export KRAMDOWN_REFCACHEDIR="$PWD/.refcache"
export KRAMDOWN_REFCACHETTL=999999999
export RUBYLIB=/tmp/kramdown-rfc/lib

if [ ! -d "$KRAMDOWN_REFCACHEDIR" ]; then
  echo "FAIL: no .refcache/. Re-stage it from the Windows repo." >&2; exit 1
fi
if [ ! -f /tmp/kramdown-rfc/bin/kramdown-rfc2629 ]; then
  echo "FAIL: kramdown-rfc clone missing. git clone --depth 1 https://github.com/cabo/kramdown-rfc /tmp/kramdown-rfc" >&2; exit 1
fi

if grep -qE '^(<<<<<<<|>>>>>>>|=======$)' "$DRAFT.md"; then
  echo "FAIL: conflict markers in $DRAFT.md" >&2; exit 1
fi

echo "=== kramdown-rfc: $DRAFT.md -> $DRAFT.xml ==="
/usr/bin/ruby3.2 /tmp/kramdown-rfc/bin/kramdown-rfc2629 "$DRAFT.md" > "$DRAFT.xml" 2> /tmp/kdrfc.err
if [ ! -s "$DRAFT.xml" ] || ! tail -3 "$DRAFT.xml" | grep -q '</rfc>'; then
  echo "FAIL: no </rfc> in output" >&2; cat /tmp/kdrfc.err >&2; exit 1
fi
echo "  wrote $DRAFT.xml ($(wc -c < "$DRAFT.xml") bytes)"
[ -s /tmp/kdrfc.err ] && { echo "  warnings:"; cat /tmp/kdrfc.err; }

# kramdown-rfc warnings are fatal here: "no end tag for X" means an
# angle-bracketed literal in an example was parsed as an HTML tag and swallowed.
if grep -q 'no end tag' /tmp/kdrfc.err 2>/dev/null; then
  echo "FAIL: kramdown-rfc swallowed an angle-bracketed literal" >&2; exit 1
fi

echo "=== xml2rfc: $DRAFT.xml -> $DRAFT.txt ==="
# A failed xml2rfc run leaves the PREVIOUS .txt in place, so existence proves
# nothing. Delete it first and treat any "Error:" as fatal, or a broken build
# reports the last good artifact as its own output.
rm -f "$DRAFT.txt"
xml2rfc --text "$DRAFT.xml" -o "$DRAFT.txt" > /tmp/x2r.log 2>&1
sed 's/^/  /' /tmp/x2r.log
if grep -q 'Error:' /tmp/x2r.log || [ ! -s "$DRAFT.txt" ]; then
  echo "FAIL: xml2rfc errored" >&2; exit 1
fi
echo "  wrote $DRAFT.txt ($(wc -l < "$DRAFT.txt") lines)"

if [ -f /tmp/baseline.txt ]; then
  echo "=== diff vs baseline ==="
  diff /tmp/baseline.txt "$DRAFT.txt" > /tmp/baseline.diff
  echo "  $(wc -l < /tmp/baseline.diff) diff lines -> /tmp/baseline.diff"
fi
