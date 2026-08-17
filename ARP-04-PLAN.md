# ARP-04 execution plan and the road to an RFC

Companion to `ARP-04.md`. That file states what `-04` has to carry. This one
states the order it has to be done in, why that order and not another, and what
the end of the road actually looks like.

Prepared 2026-08-17. Baseline: `draft-hillier-scitt-arp.md` at
`e8cb3b93...`, 291,282 B, the byte-identical source of the `-03` filing;
repository `scitt-arp-f39` on `wip/revision-03` at `843ea3b`, working tree
clean, level with `origin`.

---

## Part I — What "the end" is

### 1. The honest position today

`draft-hillier-scitt-arp-03` is an **individual submission**. The datatracker
records it with no stream, no working group, no responsible Area Director, and
IESG state `I-D Exists`. It is Standards Track *by declaration in its own front
matter* — `category: std` — and that declaration carries no weight until a
stream adopts it. An individual draft that nobody adopts does not become a
Standards Track RFC. It expires, gets refiled, and expires again.

That is not a criticism of the document. It is the starting position of every
draft that ever became an RFC. But it means the work between here and an RFC
number is **not more specification work**. `-03` is 127 pages with an executable
conformance tree and six named reviewers. The document is not the bottleneck.
The bottleneck is a stream.

### 2. How adoption actually works

Four routes exist. They are not equally open to ARP.

**Route A — Working group adoption.** The chairs of a WG issue a *call for
adoption* on the WG mailing list, usually two weeks. What decides it is not the
chairs' opinion of the document; it is how many people post "I have read this
and support adoption" and, critically, how many say "I will review it" or "I
will implement it". If it carries, the draft is refiled as
`draft-ietf-scitt-arp-00` and the WG owns it. From there: WG revisions →ceased
WG Last Call → shepherd write-up by a chair → IESG submission → IETF Last Call
(four weeks) → IESG telechat ballot → approval → RFC Editor queue → AUTH48 →
RFC. Realistic elapsed time from adoption to RFC number: **two to four years**.

**Route B — AD sponsorship.** An Area Director can sponsor an individual draft
directly to IETF Last Call without a WG. It skips adoption and WG process
entirely. It is used for documents that are clearly useful, clearly finished,
and clearly not a fit for any existing WG. It requires an AD willing to spend
their own credibility on it, and ADs are stingy with it for 127-page Standards
Track documents. Faster when it works — **twelve to twenty-four months**.

**Route C — Independent Submission Stream.** The ISE publishes documents
outside IETF process. It can publish **Informational and Experimental**, and it
**cannot publish Standards Track**. Taking this route means changing
`category: std` to `category: info` or `exp`. The ISE commissions external
reviews, then the IESG runs a *conflict review* to check the document does not
conflict with IETF work. Elapsed time: **six to eighteen months**. The result is
a permanent, citable RFC number that is explicitly not a standard.

**Route D — Refile indefinitely.** Repost every six months before expiry. The
draft stays citable at a stable name (`draft-hillier-scitt-arp`), the archive
copies are permanent, and the conformance tree keeps working. This is a real
outcome, not a failure state, if the purpose is a stable technical reference
that implementers and counterparties can point at. It yields no RFC number.

### 3. Which route ARP is actually on

**SCITT's chartered work is finished.** RFC 9943 (the Architecture) published
June 2026. `draft-ietf-scitt-scrapi` is in the RFC Editor queue.
`draft-ietf-scitt-receipts-ccf-profile` is at the IESG with publication
requested. Every milestone in the charter is delivered or in the publication
pipeline. The WG is still marked Active, chairs Jon Geater and Nicole Bates,
Security Area, AD Christopher Inacio — but a WG with no remaining milestones is
a WG heading for either a recharter or a close.

**And ARP is a charter-fit question even if SCITT stays open.** The SCITT
charter is about *software* supply chain integrity: issuers, notaries,
consumers, transparency registries. ARP is cross-sovereign reconciliation of
claims against authoritative government registers — sanctions lists, beneficial
ownership, customs. The mechanism is SCITT-shaped. The problem domain is not the
one the charter names. The first question a chair asks on an adoption request is
"is this in our charter", and on the current charter the answer is arguable at
best.

So the realistic reading:

- **Route A via the current SCITT charter: unlikely.** Not because the document
  is weak, but because the WG has nothing left to do and the charter does not
  reach the problem.
- **Route A via a rechartered SCITT, or a new WG: possible, and the highest-value
  outcome.** This is what a BOF is for. IETF 127's BOF proposal cutoff is
  **18 September 2026**.
- **Route B: worth one direct conversation**, no more, and only after `-04` is
  filed and the gaps in `ARP-04.md` §2.3–2.5 are closed. An AD will not sponsor
  a document whose own record says specification adequacy is untested.
- **Route C: the pragmatic fallback**, and the one most likely to produce an RFC
  number. It costs the Standards Track claim.
- **Route D: the default**, and it is already running.

### 4. The one asset that changes the odds

Six people are named in the `-03` Acknowledgments with specific technical
findings — Songbo Bu, Steven Mih, Iman Schrock, Walter Hawkins, Tiago Pinto,
Tom Sato. Two of them contributed standing rules to the conformance tree. Two
are authors of their own SCITT-adjacent drafts that ARP cites and that cite ARP.

**That list is the adoption constituency.** An adoption call is decided by how
many people post support. Six named reviewers who already found real defects and
had them adopted is a stronger position than most drafts have at adoption. The
`-04` filing notification should not be a courtesy note. It should be the moment
this group is asked, explicitly, whether they would support adoption and say so
on the list.

That ask cannot be made credibly until §2.3, §2.4 and §2.5 of `ARP-04.md` are
closed, because those are the items that say, in the document's own record, what
the evidence does not establish.

### 5. Dated calendar

IETF 127 is **14 November 2026, San Francisco**.

| Date | Gate | What has to be true |
|---|---|---|
| 18 Sep 2026 | BOF proposal cutoff | If a BOF is the route, the proposal is in by this date |
| 2 Oct 2026 | WG meeting requests cutoff | Agenda-time request to SCITT chairs made before this |
| 2 Nov 2026 | **I-D submission cutoff, all drafts including -00** | `-04` filed. Target **mid-September**, not November — the draft needs weeks on the list before the agenda closes |
| 14 Nov 2026 | IETF 127 | Present, or have the adoption question already asked on the list |
| 14 Feb 2027 | `-03` expires | Moot if `-04` lands in September |

**Target: file `-04` in the week of 14 September 2026.** That leaves four weeks
of list time before the meeting-request cutoff and seven before the submission
cutoff, and it is the only schedule under which the adoption question can be
asked at IETF 127 rather than at IETF 128.

---

## Part II — The `-04` critical path

### 6. The constraint that fixes the order

From `ARP-04.md` §4: `runs/existence_oracle_run.json` records
`spec_source_sha256` over `../draft-hillier-scitt-arp.md`. Its digest changes
whenever the draft changes. A run generated before the last edit to the draft
fails the manifest.

Therefore: **every edit to the draft source happens before any run is
regenerated, and the manifest check is last.** Any ordering that interleaves
them burns a full regeneration cycle per draft edit.

This single constraint determines the whole sequence. It also means that from
the first draft edit until the freeze, the tree is *knowingly* in a failing
state — that is correct behaviour, not a defect, and should not be "fixed" by
regenerating early.

### 7. The sequence

```
STAGE A — draft text, all of it, no runs
  A1  2.1  Section 4.9 / RFC 6962                        [DONE this session]
  A2  2.2  witness set and quorum rule
  A3  2.7  register binding  (2.2 lands inside it)
  A4  2.6  timing: confirm no claim added; no text change
  A5  Document History "Since -03" completed for A2-A4
  A6  Note to the RFC Editor: recheck the SCRAPI paragraph
      -- scrapi is in the RFC Editor queue; if it gets its number
         before -04 files, that paragraph changes
  >>> FREEZE THE DRAFT SOURCE <<<

STAGE B — conformance tree, after the freeze
  B1  2.3  NV-ARP-EO-04 fixture: endpoint reaches budget before answering
  B2  2.3  NV-ARP-EO-05: wire-observable discriminator, or retire with reason
  B3  2.5  encoder independence: expected bytes fixed in the vector file,
           or computed by an encoder not imported from the harness
  B4  README.md: rules 11+ if B1-B3 produce any
  B5  REPRODUCE.md: command list updated if it changed

STAGE C — regenerate, in this order and no other
  C1  python3 runners/run_existence_oracle_vectors.py
  C2  python3 runners/verify_manifest.py            -> MANIFEST: PASS
  C3  rebuild conformance-tree.zip; unpack into a clean directory
      with no repository present and run with no arguments (Rule 10)

STAGE D — build, check, file, verify
  D1  .refcache already carries RFC 6962 and RFC 9162           [DONE, see §9]
  D2  kramdown-rfc 1.7.39 -> xml2rfc 3.34.0     (superman-1 only)
  D3  idnits, NETWORKED ONLY. Expect 1 error (RFC 8785 downref).
      Warnings: expect 11 + 1. The new one is the obsolete informative
      reference to RFC 6962, which is deliberate and answered in the text
      of 4.9. An offline run reported 18 errors on -03 and is not a result.
  D4  set `date:` in the front matter to the actual filing date
  D5  submit; record the submission status URL
  D6  fetch https://www.ietf.org/archive/id/draft-hillier-scitt-arp-04.txt
      back and hash it against the local build. Byte-identical or it did
      not file correctly.
  D7  update STANDARDS-REGISTER.md; run verify-filings.py --dir .
  D8  push wip branch; fetch the three artefacts back out of the GitHub API
      and hash them rather than trusting the working copy

STAGE E — the part that decides whether any of it matters
  E1  Notify the six reviewers with the digests, tree and run record
  E2  Ask them, explicitly, to state support for adoption on the SCITT list
  E3  Mail the SCITT list: what changed in -04, what each reviewer found,
      and the adoption question
  E4  Approach the chairs on charter fit and agenda time  [before 2 Oct]
  E5  If the charter answer is no: BOF proposal              [before 18 Sep]
      -- note this cutoff is EARLIER than E4's; if a BOF is plausible,
         E4 and E5 run in parallel starting now
```

### 8. Why this order and not another

**2.1 first** because it is text-only, needs no vector regeneration, and is the
item most likely to prevent a wrong implementation. `ARP-04.md` §2.1 already
established that `typed-ref-cpb01-04` pins no digest as its expected result and
its `illustrative_derivations` are already the RFC 6962 forms. Nothing
downstream moves. Cheapest item, highest ratio, zero coupling — it goes first
by construction.

**2.2 inside 2.7, not before it.** The witness quorum is a property of the
register binding. Specifying it standalone and then writing the binding around
it means writing it twice.

**2.3 after the draft freeze** and not before, because a fixture rebuild that
changes the tree while the draft is still moving means regenerating the run
record twice.

**2.4 is not on this path.** Getting a third party to write an endpoint from the
text alone is the only item here that cannot be scheduled — it depends on
someone else's calendar. Start the ask now, in parallel with everything, and let
`-04` file with §2.4 still declared open in `does_not_establish`. It is the
single most valuable thing on the list for Route B and for a serious adoption
call, and it is the one thing that cannot be done by working harder.

**2.6 costs nothing** as long as no timing claim is added. The correct action is
to confirm no text introduces one, and move on.

**Family coherence (§3) is deliberately last** and off the critical path, except
for one item: the cross-references are pinned one revision behind, and the fix
is to repoint at `-03` "when the family is next co-filed". If ARP files `-04`
alone in September, the family is not co-filed and the cross-references go stale
by two revisions instead of one. **Decide before D5 whether `-04` files alone or
the family co-files.** That is a scheduling decision, not a technical one, and
it is the only §3 item with a deadline.

### 9. Prerequisites that will bite

**`.refcache` — done, no action needed.** `-03` cited 27 references; `-04` cites
29. `reference.RFC.6962.xml` and `reference.RFC.9162.xml` are written to
`.refcache\` and `seed-refcache.ps1` now carries both in its embedded RFC table,
so a reseed is idempotent rather than a regression. The generator that wrote
them was checked by regenerating the existing `reference.RFC.9334.xml` and
comparing byte-for-byte with the device copy — 823 B, identical — before writing
anything. `build-draft.ps1`'s cache-completeness threshold is raised from 27 to
29; leaving it at 27 would have let a build run against an incomplete cache and
hang on `bib.ietf.org`, which is exactly the failure the threshold exists to
prevent.

**The build cannot happen in the cloud.** `rubygems.org` returns 403 from this
container, so kramdown-rfc 1.7.39 cannot be installed here. `xml2rfc` 3.34.0
installs fine, but without kramdown-rfc the markdown never becomes XML. Stages
D2 and D3 are **superman-1 only**. idnits was already superman-1 only, because
it has to run networked.

**`git` writes from the remote session are unreliable.** `git status` works
against the mounted folder, but index operations hit
`unable to unlink '.git/index.lock': Operation not permitted`. File writes back
to the folder are fine; **commits are yours to run locally.**

**`ARP-04.md` §1 says the source is on `wip/revision-03` at `2e1993a`.** HEAD is
`843ea3b`, five commits later — `2e1993a` is the `-03` filing candidate and the
five since are ARP-04 working-document commits. The statement in §1 is about the
filing, so it is correct as written, but a reader will take it as "where the
tree is now". Worth one clarifying word.

**Section numbers are load-bearing.** Walter cites `draft-hillier-scitt-arp`
unpinned with section references to **6.4.3** and **6.4.4**. Those citations are
stable across `-03` only because nothing shifted them. Any new **top-level**
section inserted before Section 6 renumbers them and silently breaks an external
citation in someone else's draft. The `-04` register binding must go in as a
subsection of an existing top-level section, or after Section 6.4, or Walter's
citation has to be renegotiated. Confirmed for A1: the §4.9 edit adds no
headings and shifts nothing.

**The SCRAPI paragraph in the Note to the RFC Editor has a shelf life.**
`draft-ietf-scitt-scrapi` is in the RFC Editor queue *now*. If it gets its RFC
number before `-04` files, that paragraph and the `I-D.ietf-scitt-scrapi`
normative reference both change. Check it at D1, not at D5.

---

## Part III — Done this session

### A1 — item 2.1, Section 4.9 / RFC 6962: closed

Three edits to `draft-hillier-scitt-arp.md`, plus `docname` bumped to `-04`:

1. **`informative:` block** — `RFC9162` and `RFC6962` added. Informative, not
   normative: the construction is fully specified in ARP and an implementation
   needs nothing from either to build it. **No new downref**, so the Note to the
   RFC Editor is unchanged and the idnits error count should stay at 1.
2. **Section 4.9** — three paragraphs added after the construction definition
   and before the inclusion-proof paragraph. No new headings, so no section
   number anywhere in the document moves.
3. **Document History** — new `## Since draft-hillier-scitt-arp-03` section,
   crediting Tom Sato.

The equivalence claim was verified by executing both constructions, not by
comparing prose, and the range was extended well past what `ARP-04.md` §2.1
recorded:

| | `ARP-04.md` §2.1 | verified here |
|---|---|---|
| identical roots | leaf counts 1–128 | **leaf counts 1–1024** |
| identical sibling arrays | 2,080 pairs, ≤64 leaves | **32,896 pairs, ≤256 leaves** |
| divergences found | empty tree only | **empty tree only** |

Empty tree, ARP 4.9: `0000…0000` (32 zero octets).
Empty tree, RFC 6962: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Script: `merkle_equiv.py`, delivered alongside this plan. It implements both
constructions independently — ARP level-by-level with the odd node carried up,
RFC 6962 by recursive split at the largest power of two below the leaf count —
and compares roots and audit paths. Runs in ~22 s on CPython 3.13, no
dependencies. **It should go into `conformance/runners/` and be run on every
revision that touches Section 4.9**, because the equivalence claim is now
normative text and an unexecuted claim in normative text is exactly the class of
defect Rules 9 and 10 exist to catch.

### RFC 6962 is obsolete, and citing it anyway is the right call

`ARP-04.md` §2.1 says to add RFC 6962 as an informative reference. **RFC 6962
was obsoleted by RFC 9162, Certificate Transparency Version 2.0, in December
2021.** Citing only RFC 6962 would have drawn an idnits warning and, worse, a
reviewer comment on an otherwise clean finding.

Citing only RFC 9162 would have been wrong in a different way. Tom Sato's
finding is specifically that *"any implementer arriving from Certificate
Transparency will assume RFC 6962"* — and he is right, because RFC 6962 is what
deployed CT logs run. Naming only the replacement leaves the reader who is
actually at risk holding a document the text does not mention.

So both are cited, and the text says why. The construction is unchanged between
them: RFC 9162 Section 2.1.1 is RFC 6962 Section 2.1. Section 4.9 now cites
9162 §2.1.1 as the definition and 9162 §2.1.3 for the inclusion-proof shape,
names 6962 explicitly as the deployed version, and the Document History records
the reasoning. **Expect one additional idnits warning** — obsolete informative
reference — and expect it to stay, because it is intentional and answered in the
text.

### One finding the ARP-04 working document did not carry

`ARP-04.md` §2.1 frames the RFC 6962 relationship as a *tree* question — the
odd-node rule and the empty tree. Executing both constructions surfaced two more
places a Certificate Transparency implementer goes wrong, neither of which is a
difference in the tree:

- **Leaf ordering.** ARP sorts leaves in bytewise lexicographic order and
  deduplicates before building. RFC 6962 commits to entries **in the order the
  log received them**. A CT implementation ported over unchanged builds the
  right tree over the wrong leaf sequence and produces a root that verifies
  against nothing.
- **Proof shape.** ARP's inclusion proof carries the leaf, the index and the
  leaf count alongside the sibling array. An RFC 6962 audit path is the sibling
  array alone.

Both are now stated in Section 4.9 with `MUST`/`MUST NOT` on the ordering, in
the same place the reader is already looking for the RFC 6962 relationship. The
deduplication rule was in `-03` but two paragraphs away from anything that
mentioned Certificate Transparency, which is to say invisible to the reader who
most needed it.

### State of the tree right now

- Draft source edited: `d7916da7d024aa44e2110c13591bb8d5c2adeacc53afcf928f5214c8509e6614`,
  296,623 B (was `e8cb3b93…`, 291,282 B). One heading added — `## Since
  draft-hillier-scitt-arp-03`, in Document History, after every numbered
  section. Section 4.9 gains no heading, so **no section number in the document
  moves and 6.4.3 / 6.4.4 are unchanged.**
- `seed-refcache.ps1` `d018eea0…`, `build-draft.ps1` `ef419260…`,
  `merkle_equiv.py` `5a136557…`,
  `.refcache\reference.RFC.6962.xml` `653624e2…` (611 B),
  `.refcache\reference.RFC.9162.xml` `cff5c2a9…` (633 B).
- `runs/existence_oracle_run.json` is **now stale by design.** Its
  `spec_source_sha256` no longer matches the draft. `verify_manifest.py` will
  fail until Stage C. **This is the intended state and must not be "fixed"
  early** — regenerating now just means regenerating again after A2–A6.
- Nothing regenerated, nothing built, nothing filed.
- Working tree on the device now differs from `843ea3b` by one file. **The
  commit is yours to make.**

---

## Part IV — What to decide

Three decisions gate the rest, and none of them are technical.

1. **Does `-04` file alone in September, or does the family co-file?** Drives
   the cross-reference repointing in §3 and the whole Stage E calendar.
2. **Is the target Route A (adoption, needs a recharter or a BOF, BOF cutoff
   18 September) or Route C (ISE, needs `category: std` to change)?** These
   pull in opposite directions and the BOF cutoff is a month away.
3. **Who writes the independent endpoint for §2.4?** It is the only item that
   depends on somebody else's calendar, it is the strongest thing that could be
   said at an adoption call, and it has to be asked for now to land by November.

Everything in Stage A and Stage B can proceed while those are open.
