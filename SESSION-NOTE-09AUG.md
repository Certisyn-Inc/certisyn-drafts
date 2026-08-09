# What changed this session — email, repo, draft

9 August 2026. Three things: a real finding in the conformance tree, three
updated drafts, and two corrections to the ARP source.

---

## 1. Steven replied at 05:14 today

His message post-dates the -02 filing and the handoff. Eight numbered points.
The five that need something from you:

**He ran the reciprocal.** Your v2.1 tree at `25baafd`, fresh extraction at a
different path, all six documented commands plus the vector-regen check, no
environment set, git-initialised pristine so the zero-diff check is an actual
`git diff`. Every SELF-CHECK passes, the regenerated
`arp-outcome-vectors-v0.2.json` is byte-identical, `git diff` after the run is
empty, and 6 of 7 pinned hashes match. Report and transcripts attached to his
mail.

**One mismatch, and he is right.** `REPRODUCE.md` §5 recorded
`cc94f74e…` for `cpb_run.json`; the actual digest is `c39d204c…`. His reading —
§5 not refreshed after the last regeneration, nothing wrong with the artefact —
is correct.

**He asks for the 24 differential rows as a contributed vector class under your
name**, by PR against the AAC suite, with your finding that the frozen set
cannot reach the disputed code written into the class rather than left in an
email. The updated draft accepts, by PR.

**Corrected counts at main.** PR #67 merged. Without the transparent extra:
615 passed / 8 skipped / 4 errors. With it: 620 passed / 7 skipped. Your
pinned-commit 583/9 stands at its pin and should keep being described that way.

**"Send them when ready and we run both directions"** — the typed-reference
vectors are now invited rather than offered.

---

## 2. The second stale hash, and why both were possible

Checking Steven's finding turned up one he did not reach. §5 also recorded
`arp_adapter_run.json` as `16cf2f06…` — which is the *typed-reference run's*
digest, copy-pasted onto the line above. Two distinct files carrying one
documented digest, which is impossible on its face. Actual: `a25629f0…`.

Both stale entries are in §5. Neither is in §6. That is not chance.
`verify_manifest.py` reads a one-line `<digest> <path>` layout; §5 uses a
two-line layout, path and headline result on one line and the digest on the
next. The script's own comment excluded runs deliberately, on the grounds that
they "change legitimately whenever a corpus moves". So §5 was the one part of
the manifest nothing checked, and both errors landed there.

**Fixed, on your disk, uncommitted on `wip/revision-03`:**

- `conformance/REPRODUCE.md` — both digests corrected. CRLF preserved; the
  true diff is two lines, though the Linux mount will show the whole file.
- `conformance/runners/verify_manifest.py` — now parses §5's layout, checks
  every run digest, reports a run file present but unrecorded, and hard-fails
  when two §5 entries share a digest, which is the exact shape the adapter
  defect took.

**Two things to do with it.** I could not run `verify_manifest.py` from here —
through the Linux mount every file is CRLF, so all 14 §6 hashes mismatch and
the run is meaningless. Run it on Windows. And both stale hashes exist on
`feat/revision-02-canonicalization` too, which is the branch the emails cite, so
the fix needs to land there as well: commit on `wip/revision-03` and cherry-pick
onto the -02 branch, or apply directly there. The typed-reference draft describes
this as a follow-up change on top of `ae54748` and explicitly not part of it, so
please do not fold it into that commit.

---

## 3. The three drafts, updated

All three are still unsent and all three now reference **-02**, which is what is
published.

**Typed-reference vectors** (Steven, Songbo, Tom, Iman). New opening section
answering his point 6: confirms his mismatch, reports the second one, and gives
the structural cause. It also retracts a claim of mine that his run falsified —
part 3 said `verify_manifest.py` made a stale hash "a hard failure rather than
something a reader finds later", which was true of §6 and false of §5. Left the
original claim visible and corrected it rather than editing it out. Accepts the
PR ask, adopts his corrected counts, notes the SCRAPI status change. "Filed
today" now reads "filed on 8 August". The bib.ietf.org note is now dated to 8
August and marked as not re-tested.

**Contributor credit** (Steven, Songbo). Dates fixed. Adds a timing line, since
his point 2 says the composition draft's -01 edit is in flight under author
review and the two replacement sentences need to land before it closes. Adds
the corrected `cpb_run.json` digest so the method draft does not quote the stale
one. Adds a third method rule earned this round: a manifest is only as good as
the part of it something checks, and errors accumulate wherever a check silently
does not match.

**SCITT list reply** (Walter, Tiago, scitt@ietf.org). Dates fixed. Adds a short
observation on item 8 that an absence is only evidence if something states what
it was an absence from — which is the shape of the signed-read-response work in
-03 — offered as a distinction rather than as machinery. Adds the SCRAPI status.
Same dating hedge on the bib.ietf.org note.

**One thing to check before sending.** The typed-reference mail says "Attached:
the conformance tree and a git bundle of the branch." Re-attach after you commit
the REPRODUCE/verify_manifest fix, or the tree you send will not match what the
mail describes.

---

## 4. Two corrections to the ARP source

Both are the same class of defect the external fact-check found earlier —
empirical claims a reviewer would ask you to source.

**`{{construction-distinctness}}`** said the two normalisation cases "were
observed against a published conformance corpus", naming no corpus. They do not
need observing: both follow from the two constructions as the document defines
them, and either can be computed from the four named inputs. Restated as that.

**The -01 history entry** on the 24-input agreement now names the pair as one Go
and one Python implementation, and says why the pair is named — two
implementations from one source would have shown code identity rather than
agreement. That is Steven's point 2 in his own words, and it makes the draft's
strongest interop claim precise instead of merely true.

The draft is at 85 hunks against `625ee31`, builds clean at 6,832 lines, and all
cross-references resolve. Everything in `ARP-03-FILING-STATUS.md` still stands,
including the two open decisions: file -03 as it is, and run idnits on Windows.
