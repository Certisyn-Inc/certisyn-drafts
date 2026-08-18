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
  A1  2.1  Section 4.9 / Certificate Transparency        [DONE]
  A3  2.7  register binding -> new Section 4.23          [DONE]
  A2  2.2  witness set and quorum rule -> 4.23.2         [DONE, inside A3]
  A8  4.9.1 leaf binding                     (Vasic)  [DONE]
  A11 4.9 corrections: RFC 9162 not 6962; hash agility; the CT
      inclusion-proof claim; ceiling-halving; 4.10 typos    [DONE]
  A12 4.23 red-team repairs: witness encoding, discovery, control
      exclusion, consistency linkage, Agreement Hash types  [DONE]
  A4  2.6  timing: no claim added, no text change              [CHECKED]
  A6  Note to the RFC Editor: SCRAPI paragraph                 [CHECKED]
      -- scrapi is IESG state "RFC Ed Queue", RFC Editor state
         "Awaiting First editor", no number assigned, checked
         2026-08-18. The Note's paragraph is accurate as written.
         Re-check at D1: if a number lands, that paragraph and the
         I-D.ietf-scitt-scrapi normative reference both change.
  A13 6.4.2 fields=linkage projection, bounded at the published
      head; 6.4.4 states why it is not an oracle               [DONE]
  A7  reference implementation citation -- see §10, NOT in ARP-04.md
  A9  DECIDE: digest-suite transition -- axis, or verifier contract?
      (Vasic item 2; sits between 4.21 and 4.22)      [OPEN, §9a]
  A10 CHECK: two-clock skew on the response freshness tolerance
      (Dogru; question not defect)                    [OPEN, §9a]
  A5  Document History "Since -03" completed for A4, A6, A9, A10
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

### A3 + A2 — items 2.7 and 2.2, the register binding: closed

New **Section 4.23, The Bilateral Register Agreement**, appended at the end of
Section 4. Placement is deliberate: it renumbers nothing, so 4.9 and 6.4.3 and
6.4.4 all hold. Four subsections — `bra-items`, `bra-witness`, `bra-hash`,
`bra-limits`.

`-03` defined the Agreement inside a **definition-list entry in Section 3**: one
paragraph enumerating twenty-six declared items plus the Agreement Hash
construction. Normative content with MUST-level force, sited where a reader
looks for a definition rather than a requirement. It is now a numbered list, and
the numbering is what fixes the Agreement Hash order. The terminology entry
shrinks to a definition and a pointer, and gains `Witness Set` and
`Witness Quorum`.

**A defect fell out of gathering it.** Section 6.4.3 obliges a deployment to
declare a **response freshness tolerance** in its Bilateral Register Agreements.
That item was not among the twenty-six the Agreement Hash covered. Two
deployments could hold Agreements that differ on the tolerance and **compute the
same Agreement Hash** — a hash that does not cover a term the Agreement is
required to carry. That is the exact class of defect the document exists to
prevent, and it was sitting in `-03`. It is now item 26.

**The witness quorum.** Item 27 is a Witness Set — zero or more entries, each an
identifier, a key thumbprint and an **Operating-Party Identifier**. Item 28 is
the quorum `t`. No entry may name the reconciliation server, the Transparency
Service, or a party controlling either. The substance is the distinctness rule:
the `t` entries satisfying a quorum MUST have **pairwise distinct
Operating-Party Identifiers**, because countersignatures from witnesses under
one operating party are one observation reported `t` times. That is standing
rule 8 of the conformance tree — *two numbers produced by one construction are
one measurement* — promoted to a normative requirement.

`bra-limits` says what it does not establish: Operating-Party Identifiers are
**declared, not proven**. Two witnesses under common control that declare
distinct parties satisfy the rule as written and no mechanism here detects it.
Stated anyway, because it converts an unexamined property into an asserted one
an Audit Identity can be given to examine. A met quorum is proof that observer
diversity was declared, not that it exists.

**Consequence you need to price.** Three items enter the Agreement Hash, so
**every existing Agreement computes a different hash under `-04`**, even where
no negotiated term changed. Agreements must be recomputed; a hash recorded
before `-04` names an Agreement under the old item list. A deployment that does
not recompute observes Bilateral-Register-Agreement drift where none exists.
The section says this in terms.

Four sections had no anchor and now have one — `crypto-upgrade`, `cbor-cose`,
`agreement-drift`, `post-quantum` — so 4.23 can cite them. No heading text
changed. Every `{{...}}` in the document resolves; checked mechanically.

### State of the tree right now

- Draft source edited: **see `ARP-04.md` section 12 for the current digest.**
  The figure moves with every Stage A edit and is recorded there rather than
  duplicated here.
- Headings 85 → 90. Section 4 gains one subsection **at the end** (4.23) and
  Document History gains `## Since draft-hillier-scitt-arp-03`. **4.1–4.22, all
  of Section 5 and all of Section 6 keep their numbers, so 4.9, 6.4.3 and 6.4.4
  are unchanged and Walter's external citation still resolves.**
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

## §9a — From the SCITT list, 17 August 2026

Three threads landed today. One of them changes `-04`.

### Nenad Vasic — implementation experience against `-03`

Subject: *"Re: draft-noa-scitt-ai-agent-receipt-00 — ARP reconciliation run
against the EMILIA and Noa corpora"*, `nenadvasic@protonmail.com`, 21:11 UTC.
Five numbered items; four bear on `-04`. Composed and sent by "Elara", the
project's AI maintainer, under a receipted mandate — **the attribution wording
in the Acknowledgments is yours to settle**; I have credited Nenad Vasic by
name and said the finding was contributed as an executable vector.

**Item 4 is a defect in ARP and it is now closed.** He describes a proof whose
carried leaf is lifted verbatim from another object's valid proof: the path
folds, the root matches, the signature verifies, and the leaf is bound to
another receipt's bytes. A path-only verifier accepts. `-03` §4.9 defined the
inclusion proof as carrying the leaf and **said nothing about where a verifier
should get the leaf it checks against** — so ARP had exactly this hole. §4.9 now
requires the verifier to recompute the leaf from the object whose inclusion is
being proved, **before** walking the sibling array, and to refuse on mismatch
regardless of whether the walk would reach the root. In ARP the bite is §4.10:
present register A's inclusion proof alongside register B's Partial Attestation
and a path-only verifier concludes B was committed.

This one is worth taking seriously beyond the text fix. It is the first defect
in ARP found by somebody running code against it who did not write the
specification, which is the exact gap `ARP-04.md` §2.4 says is untested.

**Item 2 is a new `-04` candidate, not yet actioned.** A digest-suite transition
of the evidence itself: records under a predecessor suite stay valid at their
recorded positions, while a retroactive re-digest of the same bytes under the
successor must refuse. His discriminating property — *a naive engine that
re-hashes history under the new suite agrees with the forged digest and
accepts*. In ARP this sits between §4.22 (Cryptographic-Primitive-Upgrade Path)
and §4.21 (Retroactive Evaluation), and §4.22 currently says the chain is
unbroken across a rotation without saying what a re-digest of historical bytes
under the new primitive must do. **Either a Divergence Axis or an explicit
statement that suite transition belongs to the verifier contract.** Needs a
decision before the Stage A freeze.

**Item 3 generalises standing rule 9.** He recommends indexing vectors by *the
predicate violated* rather than by *the stage that caught the violation*,
noting seven of nine malformed files in his own run were refused at a shape gate
rather than the purpose-built check. Rule 9 says a control is credited only when
its designed discriminator fired; his point is the constructive form — one
vector per predicate keeps engines comparable when their gate placement differs.
**Candidate rule 11**, and it bears directly on `NV-ARP-EO-04`, which fails for
precisely this reason.

**Item 5 corroborates §2.5 from outside.** *"Spec-supplied
bytes-plus-expected-digest vectors are what make the upgrade durable —
deployment-authored vectors measure self-consistency, not conformance."* That is
`ARP-04.md` §2.5's own proposed fix, arrived at independently by someone
shipping the same discipline. Useful to cite when §2.5 lands.

Item 1 supports the §3 agent-axis split surviving registry review unchanged.

**He has a git-apply-able patch ready and asked for the slot.** Taking it is
cheap and it is the strongest single move available on §2.4.

### Emek Can Doğru — a question for ARP, not a defect in it

Subject: *draft-dogru-scitt-disclosure-evidence-02*, 20:28 UTC, cc Walter and
Iman. Mostly about his own draft, where he found that a three-second clock
difference between two time sources turned a boundary artefact into an
accusation, and is fixing `-04` to name both clocks and declare a skew bound.

The transferable question: **ARP's response freshness tolerance is also decided
across two clocks** — the responding service stamps `response-time`, the reader
compares it against its own — and neither §6.4.3 nor the new item 26 names them
or bounds skew. `-03` does not use the words "clock" or "skew" either. I am
flagging this as a question rather than asserting a defect, because ARP's
tolerance is bounded above by the notarisation interval and Doğru's case
involved an unbounded window. **Worth ten minutes before the freeze.**

### Anton Sokolov — precedent for the §2.4 ask

Subject: *draft-mih-sato-agent-accountability-composition-01*, 16:09 UTC, cc
Tom Sato, Steven Mih, Iman Schrock, Songbo Bu — four of your six reviewers on
one thread. No ARP content. Worth one line anyway: he commits to running someone
else's vectors before writing his `-02`, because *"the honest way to check that
is against a profile I did not write."* That is §2.4's argument in someone
else's mouth, on the SCITT list, this week. Cite it when you make the ask.

### Not ARP: four bounced outreach messages today

`cameron@kelley.vc`, `info@mobasi.ai`, `justin.grover@gmail.com` and
`hexordia@hexordia.com` all rejected by `mx.google.com` — *"blocked because its
content presents a potential security issue"*. Four in one day, all
Google-hosted, all outbound from `certisyn.com`. That reads as a sender-side
reputation or content-filter problem rather than four coincidences, and none of
those people know you tried to reach them.

---

## §10 — Two things carried forward that `ARP-04.md` does not list

**The reference-implementation citation was promised to `-04`.**
`_notes-local/ARP-03-adoption-plan.md` §3 declines to write "is being developed
in parallel" into `-03`, on the ground that a draft should not announce an
artefact that does not exist, and commits instead to: publish the implementation
first, then cite it by repository and commit alongside the vectors it is checked
against — *"The citation lands in -04."* That commitment is not in `ARP-04.md`'s
seven items. Either it lands in `-04` or `-04` should say why it did not, on the
same reasoning that kept it out of `-03`.

**A7 and §2.4 are the same item wearing two hats.** The independent endpoint
that would let the existence-oracle class surface a specification defect, and a
published reference implementation, are both "code written from the text by
someone who is not holding the author's intent". If one person can be found to
write the endpoint, the artefact is both.

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


---

## §11 — Red team, 2026-08-18

Two adversarial passes over the new Section 4.9 and Section 4.23 before any
build, instructed to refute rather than confirm. Twenty-eight findings; the
substance is in `ARP-04.md` section 14. Three things to carry into the rest of
Stage A:

**Red-team the new text, not just the old.** Two of the three defects corrected
in 4.9 were in `-03` and survived a filing and a networked idnits run. The scope
error in the first draft of 4.9.1 was written and caught inside an hour. Neither
class is reachable by reading more carefully; both were found by an adversary
instructed to break the claim.

**Every measured number in normative text gets executed.** Three of the
overclaims were numbers or equivalences that read as obviously true. The
duplicate-last convention "produces different roots" is false at every power of
two. The level width "halves" — it does not, it halves by ceiling, wrong at 1013
of the first 1024 leaf counts. That is standing rule 12.

**An encoding that two parties must compute independently needs a type table.**
The Agreement Hash fixed an item order and nothing else. Determinism under RFC
8949 §4.2.1 fixes how a value encodes, not which type an item takes or how a set
orders. Eight of thirty-one items are sets. Apply the same test to every other
digest this document defines before the freeze — that check has not been done.

Deferred to `-05`, recorded not fixed: Agreement items 13, 14, 20, 24 and 25
anchor normative declarable terms into Section 7, Security Considerations, which
is conventionally non-normative and which an AD review will flag. Moving them
renumbers Section 7.
