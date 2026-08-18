# ARP-04

**Read this file first. Everything else in this folder is derived from it or superseded by it.**

Working document for `draft-hillier-scitt-arp-04`. Owner: Joel Hillier.
Opened 2026-08-14, the day `-03` posted. Last updated 2026-08-16. Supersedes
every `-03`-era note in `archive/arp-03/`.

**Status, 2026-08-18.** Stage A of `ARP-04-PLAN.md` is substantially complete.
Items 2.1, 2.2 and 2.7 are closed in the draft source, along with five findings
that were not on the list of seven -- three of them defects in `-03` text. The
draft source is no longer the `-03` bytes and `runs/existence_oracle_run.json`
is stale **by design** until the Stage C freeze; do not regenerate it early.
`ARP-04-PLAN.md` holds the sequence, the dated calendar and the adoption route.
This file holds what `-04` carries.

**Sections 13 and 14 are the live edge.** Section 13 is the 17 August SCITT
traffic; section 14 is the red-team result on the new text.

---

## 1. Where `-03` landed

`draft-hillier-scitt-arp-03` posted **2026-08-14 at 04:24:24 UTC**, submitted as
xml2rfc v2 XML built by kramdown-rfc 1.7.39, logged in as `jhillier`. Standards
Track, Individual Submission, 127 pages, expires 14 February 2027.

Submission status page:
`https://datatracker.ietf.org/submit/status/167720/e055c01d780f5fb3720db4783868aa12/`

| artefact | sha256 | size |
|---|---|---|
| `draft-hillier-scitt-arp.md` | `e8cb3b93dcea2f0b1e0a35da03f95d04ce425bb6717e15e8eafad9ecf85641d1` | 291,282 B |
| `draft-hillier-scitt-arp-03.txt` | `fe7ba656ef07842c365ce93938610cd874668c29f0fa06031d37d0e4e72b395d` | 7,112 lines, 339,537 B |
| `conformance-tree.zip` | `ea1c326522913b7cb8e3959837b4d17876e15904f0b160dc3968c4411314f64d` | 265,566 B |
| `runners/run_existence_oracle_vectors.py` | `1b2ff11dcb46f42bdab4e2eba34a996d91f7bbe174e768ec9d55c8e04cc888f6` | |
| `runs/existence_oracle_run.json` | `74df0c9aae6a6d230c1ecc1a9fc92be2ace571be411c50666e7cf8bfb5199869` | |

**The archive copy was fetched back and hashed.**
`https://www.ietf.org/archive/id/draft-hillier-scitt-arp-03.txt` is `fe7ba656...`,
339,537 bytes, byte-identical to the local build. Do this on every filing. It is
the only check that establishes the datatracker served what was built.

Source and evidence are on `wip/revision-03` at commit `2e1993a`, pushed and
verified by fetching the three files back out of the GitHub API rather than
trusting the working copy. All three match the digests above.

idnits on the filed bytes, networked: **1 error, 11 warnings**. The error is the
RFC 8785 downref, deliberate and disclosed in the Note to the RFC Editor per
Section 2 of RFC 8067.

---

## 2. What `-04` has to carry

Seven items. Each states who found it, what the evidence is, and what closing it
looks like. Nothing here is a claim `-03` makes.

### 2.1 Section 4.9 has to state its relationship to RFC 6962

**Found by Tom Sato, 2026-08-14, on the CPB-01 thread.** He read the empty-tree
rule as a defect and was right to.

Section 4.9 defines a Merkle construction and never mentions RFC 6962 anywhere in
the document. Any implementer arriving from Certificate Transparency will assume
RFC 6962 and will get the empty tree wrong.

Measured, by executing both constructions rather than comparing prose:

- ARP's odd-node rule, where the last node at a level is carried up unchanged
  rather than duplicated, and RFC 6962's recursive split at k equal to the
  largest power of two below n, produce **identical roots for every leaf count
  from 1 to 128**.
- **Identical inclusion-proof sibling arrays for all 2,080 (leaf count, index)
  pairs up to 64 leaves.**
- They diverge at exactly one point in that whole range: the empty tree. ARP
  gives thirty-two zero octets. RFC 6962 gives MTH of the empty set equal to
  SHA-256 of the empty string, `e3b0c442...`.

The divergence is deliberate and worth keeping. `e3b0c442...` is a well formed
digest that a verifier reproduces successfully and may then treat as a root that
commits to something. Thirty-two zero octets is a value no commitment produces,
so it cannot be mistaken for one. Section 4.9 already requires a verifier to
reject any proof presented against the empty root, and that rule does the work
under either convention.

**CLOSED 2026-08-17.** Section 4.9 states the relationship. Two corrections to
the framing above were made in the doing.

**RFC 6962 is obsoleted by RFC 9162** (Certificate Transparency 2.0, December
2021). Citing 6962 alone draws an idnits warning and a reviewer comment. Citing
9162 alone inverts Tom's point, which is that implementers arrive from 6962
because that is what deployed CT logs run. Both are cited: 9162 Section 2.1.1 as
the definition and 2.1.3 for the proof shape, 6962 named as the deployed
version, and the text says why. **Expect idnits warnings to go 11 to 12.** The
new one is the obsolete informative reference; it is intentional and stays.

**RFC 9162 Section 2.1.1 parameterises the hash algorithm** where RFC 6962 fixes
SHA-256. The equivalence claim in the draft is to 2.1.1 *instantiated with
SHA-256*, not to 2.1.1 unqualified.

Every number in the draft was verified by executing both constructions
(`conformance/runners/merkle_equiv.py`, ~2 min, no dependencies, reproduced on
two interpreters). The range is well past what is recorded above:

| | recorded above | in the draft |
|---|---|---|
| identical roots | leaf counts 1-128 | **1-4200** |
| identical sibling arrays | 2,080 pairs, <=64 leaves | **131,328 pairs, <=512 leaves** |
| divergences | empty tree only | empty tree only |

Three things the note above did not carry, all now in 4.9:

- **Leaf ordering.** ARP sorts and deduplicates; a CT log commits to submission
  order. A ported implementation builds the right tree over the wrong sequence.
- **Proof shape.** RFC 9162's inclusion proof carries the index and the tree
  size, as ARP does. **The leaf is the only field that differs.** An earlier
  draft of the -04 text said CT carried the sibling array alone; that is false
  and red team caught it before it reached a build.
- **The duplicate-last convention agrees at every power of two.** Measured: it
  matches at exactly 11 of the first 1024 leaf counts, all of them powers of
  two, because no level of such a tree is ever odd. A conformance vector at four
  or eight leaves does not detect an implementation that ported it. That is now
  stated in the section.

**No vector regeneration is required.** `typed-ref-cpb01-04` does not pin a digest
as its expected result. Its `expected` block is `verified: false`, checked by
comparing `leaf_input`, 32 raw bytes against the 64-byte hex encoding,
distinguishable by length alone. Its `vds_note` records that CPB-01 Section 6 is
VDS-agnostic and Section 6.1 constrains the input only. The digests it carries
sit in an `illustrative_derivations` block marked non-normative and are already
the 0x00-prefixed RFC 6962 forms, `47558aa8...` correct and `35258dc3...`
incorrect. All four digests in that block were recomputed on 2026-08-14 and
verify. GAR-04's move to RFC 6962 Section 2.1 brought GAR onto the values the
vector already recorded.
### 2.2 The witness quorum Section 6.4.3 names but does not specify

**Found by Walter Hawkins, adopted into `-03`.** Section 6.4.3 now says an empty
result is falsifiable to the extent the reader holds head-consistency evidence
for the served chain from an observer independent of the responding service, and
carries a SHOULD on the relying party with witness countersignature over the head
preferred to an independently anchored head digest.

`-03` names the evidence that bounds the gap. It does not specify a quorum, and
says so.

**CLOSED 2026-08-18**, inside 2.7 as predicted, as Section 4.23.2. Summary in
2.7; the parts worth carrying here are that the quorum counts only entries with
**pairwise distinct Operating-Party Identifiers** -- standing rule 8 promoted to
normative text -- and that the effective set and quorum are published in the
Policy Parameters Document, because a relying party holds only Agreement Hashes
and could not otherwise read the test it is obliged to run.

### 2.3 Two conformance channels that have never been exercised

The aggregate reads `PASS_WITH_DECLARED_GAPS`, six of eight controls exercised.
The two that are not:

- **`NV-ARP-EO-05`.** The same-work requirement of Section 6.4.4 is structural and
  is not decidable by response comparison. Recorded with
  `designed_discriminator: null`, which is the finding rather than a missing one.
- **`NV-ARP-EO-04`.** Refuses, but through a fallback branch. The defective
  endpoint answers 404 before charging the rate-limit counter, so it never
  reaches 429, so the designed discriminator, an equal 404 and 429 transition
  index, never executes. The budget-ordering channel is untested. **Found by
  Songbo Bu, by reading the aggregate rather than the verdicts.**

**Close them by:** giving `NV-ARP-EO-05` a wire-observable discriminator or
retiring it and saying why; and rebuilding the `NV-ARP-EO-04` fixture so the
endpoint reaches its budget before answering.

Rule 11 names the cause of `NV-ARP-EO-04` rather than only its symptom: the
suite indexes that control by the stage that catches the violation rather than
by the predicate violated, so a fixture whose 404 fires before the budget
counter is charged refuses through the wrong gate and the budget-ordering
channel is never reached. Rebuild it against the predicate.

### 2.4 The class is one-sided

Every negative control is fault injection into an endpoint written by the
specification's author from his own reading of his own text. That is the one
configuration that cannot surface a specification defect.

**Close it by:** getting the class to refuse an endpoint written by somebody else
working only from the text. Until then, specification adequacy is untested and
the run record says so in `does_not_establish`.

### 2.5 Encoder independence

Request-binding and deterministic CBOR are computed with functions imported from
the implementation under test. An encoder defect, including an RFC 8949 Section
4.2.1 map-ordering violation, is invisible to this class.

This matters beyond the document. A widely used CBOR library, in its canonical
mode, applies a different map-ordering rule than RFC 8949 Section 4.2.1, so an
implementation importing it ships non-conforming bytes with no error.

**Close it by:** computing the expected bytes with an independent encoder, or by
adding a vector whose expected bytes are fixed in the file rather than derived at
run time.

### 2.6 Timing

`NV-ARP-EO-06`, the statistical timing row of the class as designed, is not
carried as a conformance row. It is reported as `timing_observation` and is not
adjudicated. No timing-resistance claim is made and none is tested. The loopback
observation is not evidence about a deployed path.

**Close it by:** leaving it alone unless a timing claim is added. If a claim is
added, it needs a test on a deployed path, not on loopback.

**CHECKED 2026-08-18, no change.** Swept the whole draft for timing language.
Section 6.4.4 continues to state that response timing is a separate claim from
the deterministic requirements and MUST be stated separately, that an
implementation claiming resistance to timing-based existence inference MUST
publish its measurement population, sample count, network placement, decision
rule and acceptance threshold, and that an implementation making no such claim
is not for that reason non-conforming. Section 7.8 makes no timing claim. `-04`
adds none. The item stays closed by inaction, which is what it asked for.

### 2.7 The register binding

Already the `-04` headline before any of the above. Section 2.2's quorum belongs
inside it.

**CLOSED 2026-08-18** as new **Section 4.23, The Bilateral Register Agreement**,
appended at the end of Section 4 so that it renumbers nothing: 4.9, 6.4.3 and
6.4.4 all hold, and Walter's external citation still resolves. Four subsections:
declared items, witness set and quorum, the Agreement Hash, and what an
Agreement does not establish.

`-03` defined the Agreement inside a **definition-list entry in Section 3** --
one paragraph enumerating twenty-six declared items plus the Agreement Hash
construction. Normative content with MUST-level force, sited where a reader
looks for a definition. It is now a numbered list, and the numbering is what
fixes the Agreement Hash order.

**Gathering it surfaced two obligations that sat outside the Agreement Hash.**
Section 6.4.3 obliges a deployment to declare a response freshness tolerance in
its Agreements; Section 6.4.1 obliges an Agreement to declare the keys under
which a regulator reads, and item 5's trust anchor is not a key. Neither was
enumerated. Two deployments could differ on either term and **compute the same
Agreement Hash** -- a hash that does not cover a term the Agreement is required
to carry, which is the class of defect this document exists to prevent. They are
items 26 and 30. Item 31 does the same for the re-invocation permission Section
4.21 already conditions on.

**The Agreement Hash was not independently computable and now is.** Determinism
under RFC 8949 Section 4.2.1 fixes how a given value is encoded; it does not fix
which CBOR *type* an item takes, nor the order of elements *within* a
set-valued item. Eight of the items are sets. 4.23.3 now carries a type table,
requires every set to be sorted in bytewise lexicographic order of the
deterministic encoding of each element -- the rule this document already applies
to the Audience Set and two other places -- fixes the array at thirty-one
elements, and states that an absent, inapplicable or empty item is CBOR null
with the element still present. `-03` said only that an absent *optional* item
was null while seven items admit absence. Since Section 7.5 suspends
reconciliation on a deviating Agreement Hash, each of these was an outage rather
than a warning.

**Price this before filing.** Five items enter the Agreement Hash and the type
rules change the encoding, so **every existing Agreement computes a different
hash under `-04`** even where no negotiated term changed. Agreements must be
recomputed; a deployment that does not will observe drift where none exists.
4.23.3 also now states that an Agreement Hash change is a renegotiation event
and that the parties must agree the new hash *before* the operation causing it
-- otherwise a routine key rotation under the item 3 upgrade path suspends the
deployment's own reconciliation by its own drift rule.

### 2.8 Found while doing the above, not on the list of seven

**2.8.1 Section 4.9 did not bind the leaf to the object. CLOSED 2026-08-18.**
Found by **Nenad Vasic**, 17 August, on the SCITT list, from running code
against a third-party corpus. `-03` defined the inclusion proof as carrying the
leaf and said nothing about where a verifier gets the leaf it checks against. A
proof whose carried leaf is lifted unchanged from another object's valid proof
folds to the correct root under a sibling array that verifies, because it is a
correct proof -- of the other object. A verifier that walks first and trusts the
carried leaf concludes the object it holds was committed. Nothing in the walk
depends on the object, so no amount of path checking detects it. In ARP the bite
is Section 4.10: present register A's inclusion proof alongside register B's
Partial Attestation.

New Section 4.9.1 requires the verifier to compute the leaf from the object and
use that value, and no value taken from the proof, as input to the walk. Stated
over the *object* and not over the carried field, because Section 4.10 permits
COSE Receipts (RFC 9942), whose inclusion proof **carries no leaf** -- a rule
written only as a comparison against a carried leaf would be vacuous under
exactly the encoding a SCITT-aware verifier is most likely to use. That scope
error was caught in red team, not in drafting.

This is the first defect in ARP found by somebody running code against it who
did not write the specification. That is the gap 2.4 says is untested.

**2.8.2 Two errors in `-03` text of Section 4.9. CLOSED 2026-08-18.**

- The sibling-derivation rule said the verifier halves "the index and the level
  width" as it ascends. **The level width halves by ceiling, not by
  truncation.** Measured: truncation gives the wrong width at 1013 of the first
  1024 leaf counts -- every count that is not a power of two, which is the
  entire range the paragraph exists to pin down. Five leaves give widths 5, 3,
  2, 1 and not 5, 2, 1. This has been wrong since the construction was first
  written.
- Section 4.10 described COSE Receipts as "the same inclusion-proof format".
  They are a different format: no leaf, and defined over the RFC 9162 tree whose
  empty root ARP deliberately rejects. Now "a compatible inclusion-proof
  encoding".

Also fixed: a double comma and a duplicated clause in Section 4.10, present
identically in `-03`.

**2.8.3 A digest-suite transition has no defined outcome. OPEN, decide before
the freeze.** Raised by **Nenad Vasic**, same message, item 2. Records under a
predecessor digest suite stay valid at their recorded positions, while a
retroactive re-digest of the same bytes under the successor must refuse. His
discriminating property: *a naive engine that re-hashes history under the new
suite agrees with the forged digest and accepts.* In ARP this sits between
Section 4.22, which says the chain is unbroken across a rotation without saying
what a re-digest of historical bytes must do, and Section 4.21. **Either a
Divergence Axis or an explicit statement that suite transition belongs to the
verifier contract.**

**2.8.5 The head-linkage projection was a live head oracle. CLOSED 2026-08-18,
the same day it was introduced.** Section 4.23.2 obliges a relying party to link
two ledger heads, and a relying party is entitled to no read that would let it,
so a `fields=linkage` projection was added to Section 6.4.2 returning one
entry's sequence number and its two hashes to any signed requester. Unbounded,
that is a live head oracle: the Ledger is contiguous, so a requester
binary-searches the current head between publications and polls it for the write
rate. That is exactly the disclosure Section 4.18 publishes the Ledger Head
Statement only once per notarisation interval to prevent, and the new read would
have defeated it. The projection is now bounded at the head of the most recently
published Statement, and a request above it is refused `404` whether or not the
entry exists. Section 6.4.4 states why a projection answering `200` where the
full read answers `404` is not an existence oracle, and what would make it one.

Worth naming the pattern: **a new entitlement is a new disclosure surface, and
the surface it opens is not always the one it was reasoned about.** This one was
reasoned about as "digests disclose nothing readable", which is true, and missed
that the sequence numbers disclose the head.

**2.8.4 The response freshness tolerance is decided across two clocks. OPEN.**
Raised indirectly by **Emek Can Doğru**, 17 August, from his own draft, where a
three-second difference between two time sources turned a boundary artefact into
an accusation. ARP's tolerance is compared between the responder's stamp and the
reader's clock, and neither Section 6.4.3 nor item 26 names the two clocks or
bounds skew. `-03` does not use the words "clock" or "skew" anywhere. Bounded
above by the notarisation interval, unlike his unbounded window, so this is a
question and not yet a defect. Ten minutes before the freeze.

---

## 3. Family coherence

The three drafts share one Verification Reconciliation Object, one issuing-partner
framework, and one cryptographic-continuity model. A change to any of these five
rows in one draft is a change to the family.

| element | ARP | E8V | AIGV |
|---|---|---|---|
| VRO content model | Reconciliation Output | Section 6 | Section 6 |
| Issuing-partner framework | Bilateral Register Agreement | Section 7 | Section 7 |
| Anchor and continuity | Sections 3.8, 3.12 | Section 8 | Section 8 |
| Maturity or verdict scale | match, no-match, partial, indeterminate | One, Two, Three | Documented, Operational, Adversarial-ready |
| Registry | Settlement-Layer Ledger | public attestation registry | public attestation registry |

Open family items, none of them blocking:

- **Cross-references are pinned one revision behind.** Each `-02` cites the other
  at `-01`. Repoint both at `-03` when the family is next co-filed.
- **`essential-eight` has no postal address.** The datatracker author record reads
  "unknown country" where `ai-governance` reads "United States". Add the same
  street, region, code and country block.
- **`essential-eight` Section 9 has no reciprocal SCITT composition paragraph** to
  match `ai-governance` Section 9. The family should read symmetrically.
- **Author name** renders "Hillier, J." in reference blocks and "J. D. Hillier" on
  the title page. Cosmetic. Fix in the datatracker author record.
- **`chorale-protocol` is unfiled, and its docname is wrong for a first
  filing.** Checked against the datatracker on 2026-08-16: zero documents and
  zero submissions under `draft-hillier-chorale-protocol`. The local source
  carries `docname: draft-hillier-chorale-protocol-03`, but a name with no
  filing history must enter at `-00`. Set it to `-00` before submitting. It also
  carries no `date:`, so a build stamps it with whatever day it ran. The author
  email is already `jhillier@certisyn.com`; the earlier note that it read
  `joel@certisyn.com` is stale and is corrected here. `category: exp`,
  `submissionType: IETF`, `ipr: trust200902`, and `country: US` with no street
  or postal detail.
---

## 4. How to reproduce anything in section 1

From the conformance tree, whether cloned or unpacked:

```
unzip conformance-tree.zip
cd conformance
python3 runners/run_existence_oracle_vectors.py     # no arguments
python3 runners/verify_manifest.py
```

Expected: `DETERMINISTIC RESULT: PASS_WITH_DECLARED_GAPS`, exit 0, run digest
`74df0c9a...`, and `MANIFEST: PASS`.

Ordering constraint. `runs/existence_oracle_run.json` records
`spec_source_sha256` over `../draft-hillier-scitt-arp.md`, so it is evidence about
one revision of the draft and its digest changes whenever the draft does. Freeze
the draft source first, then run the existence-oracle runner, then run the
manifest check. A run generated before the last edit to the draft fails the
manifest, which is intended behaviour and not a defect in the runner.

Full command list, nine items, is in `conformance/REPRODUCE.md`.

To check the filing record itself against the IETF rather than against itself:

```
python3 verify-filings.py --dir .
```

in `drafts/ietf/` or in the OneDrive folder at
`02 - Strategy and IP/Current/Standards/IETF-Drafts/`. It asks the datatracker
submission API which revisions are actually posted and fails on any the register
omits, then fetches each `.FILED.txt` from the archive and fails unless the local
copy is byte-identical. Exit 2, not 0, if either service is unreachable.

Build the document with kramdown-rfc 1.7.39 and xml2rfc 3.34.0. Run idnits on a
networked machine only. An offline idnits run reported 18 errors on `-03` where
the networked run reported 1. Do not treat an offline idnits run as a result.

---

## 5. Standing rules in the conformance tree

Rules 1 through 8 are in `conformance/README.md`. The two added during `-03`:

**Rule 9.** A negative control declares the discriminator it is designed to trip,
and is credited only when that discriminator is what fired. A control that refuses
through some other check is recorded `control_exercised: false` and is excluded
from any complete-pass claim. *Attributed to Songbo Bu.*

**Rule 10.** A package is an artefact only if it runs unpacked. Prove it by
unpacking into a clean directory with no repository present and running with no
arguments. *Attributed to Walter Hawkins and Songbo Bu.*

Added during `-04`:

**Rule 11.** A vector is indexed by the predicate it violates, not by the stage
that catches the violation. Where a violation is caught is implementation
topology; the predicate is the contract. One vector per predicate keeps two
engines comparable when their gate placement differs. *Attributed to Nenad
Vasic, who observed seven of nine malformed inputs in his own run refused at a
shape gate rather than at the purpose-built check.* This is rule 9 stated
constructively: rule 9 refuses credit when the designed discriminator did not
fire, and rule 11 says how to build a suite in which it does. It bears directly
on `NV-ARP-EO-04`, which fails for exactly this reason.

**Rule 12.** An equivalence a normative section asserts is executed on every
revision that touches that section, and the executing script lives in
`runners/`. An unexecuted equivalence in normative text is a gate reporting
success over inputs it never examined, which is the class rules 9 and 10 exist
for. `merkle_equiv.py` is the first of these.

The class of defect both rules address is one gate reporting success over inputs
it never examined. Fix that class at three levels every time: the instance, the
class, and the enforcement, with a negative control proving the fix.

---

## 6. Who found what

Named findings are carried in the Acknowledgments, because a specification
improved by review should say by whom.

| person | finding carried in `-03` |
|---|---|
| Songbo Bu | The indistinguishability requirement of Section 6.4.4 could not be satisfied as `-02` stated it. The normalised observation, its enumeration of HTTP metadata and cache behaviour, and the separation of deterministic requirements from any statistical timing claim are his design, contributed as an executable vector class. Also rule 9. |
| Steven Mih | The empty-result contradiction is conditional on reader and later observer having been served one chain. The boundary now stated in Section 6.4.3 is his finding. Also confirmed the deterministic encoding requirements are RFC 8949 Section 4.2.1 and not RFC 9052 Section 9. |
| Iman Schrock | With Anton Sokolov, that a content digest cannot serve as a correlation key across independently produced descriptions of one act. The requirements in Section 3 on pinning action type and version, the selected field, and its normalisation and comparison rules are his, substantially as drafted. |
| Walter Hawkins | The falsifiability condition of Section 6.4.3 is bounded by observer diversity rather than by any stronger single-log property. Naming the independent observer and the ordering of witness countersignature over independently anchored head digest is his. Also rule 10. |
| Tiago Pinto | The obligation to answer with a signed response carrying a log position belongs on the party making the claim rather than the party relying on it. Section 6.4.3 takes that shape at his argument. |
| Tom Sato | Leaf-construction work on Certificate Transparency logs informed the inclusion-proof requirements. Section 2.1 above is his, and **landed in `-04` on 17 August**. |
| Nenad Vasic | That an inclusion proof whose carried leaf is lifted from another object's valid proof folds to the correct root, so a verifier walking the path before recomputing the leaf accepts a proof bound to bytes it does not hold. Section 4.9.1 is his, contributed as an executable vector against a third-party corpus. Also rule 11, and the open item at 2.8.3. |

Addresses for all seven are in the private copy of this file, not here.

**Attribution note on Nenad Vasic.** The message is sent from his address and
signed "Composed and sent by Elara, this project's AI maintainer, acting under
its receipted on-chain mandate", with an act receipt. The Acknowledgments credit
the human sender by name. Whether the draft should say more than that is a
judgement call and is Joel's; it is flagged rather than decided. Nothing about
the finding depends on it -- the vector was executed and the defect is real
either way.

Cited alongside: `draft-sato-soos-gar-04` and `draft-hawkins-scitt-attested-agent-payment`.
Walter cites `draft-hillier-scitt-arp` unpinned with section references to 6.4.3
and 6.4.4. Those section numbers are unchanged in `-03`, so the citation is stable.

Confirmation of the `-03` filing went to all six on 2026-08-14 at 17:21 to 17:22
UTC, each carrying the digests in section 1, with `conformance-tree.zip` and
`existence_oracle_run.json` attached.
---

## 7. Working method

Written down because it is the reason the reviews above produced what they did.

- **Ground every claim in bytes.** State digests, line counts and sizes. Fetch the
  published copy back and hash it rather than assume the upload was faithful.
- **Reproduce on a second machine before claiming reproducibility.** The `-03` text
  and its run record both reproduce on Linux with CPython 3.11 from the same
  source, byte for byte, as well as on Windows with CPython 3.13.
- **Declare gaps in the record, not in a covering message.** A summary stronger
  than the record it summarises is the defect, not the record.
- **Distinguish what a run establishes from what it does not.** Reproduction of
  fixed bytes under a published runner is not independent verification.
- **Credit findings by name.**
- **Never diff against a local copy of the archive. Diff against the archive.**
  Truncated `.FILED.txt` reference copies were the root cause of the `-01`
  reconstruction losses, and they survived in the source-of-record folder until
  2026-08-14. They are now renamed `.TRUNCATED-DO-NOT-USE.txt` with a warning file
  beside each.

---

## 8. Where things live

| what | where |
|---|---|
| this file | `scitt-arp-f39/ARP-04.md`, mirrored to the OneDrive `IETF-Drafts` folder |
| draft source | `scitt-arp-f39/draft-hillier-scitt-arp.md` |
| conformance tree | `scitt-arp-f39/conformance/` |
| reproduction runbook | `scitt-arp-f39/conformance/REPRODUCE.md` |
| standing rules | `scitt-arp-f39/conformance/README.md` |
| filing register | `certisyn-app/drafts/ietf/STANDARDS-REGISTER.md`, mirrored to OneDrive |
| register self-check | `drafts/ietf/verify-filings.py` |
| immutable filed text, every revision | OneDrive `IETF-Drafts/*.FILED.txt`, with `PROVENANCE.md` |
| externally cited conformance evidence | OneDrive `IETF-Drafts/cpb-interop-evidence/`, with its own README |
| superseded `-03` working notes | `scitt-arp-f39/archive/arp-03/` |

Repositories. `scitt-arp-f39` is its own repository at
`github.com/Certisyn-Inc/scitt-arp-f39` and is PUBLIC, currently on
`wip/revision-03`. `2e1993a` is the `-03` filing commit; `d789862` carries the
4.9 Certificate Transparency work. The IETF drafts other than ARP live in
`certisyn-app` under `drafts/ietf/`. `certisyn-app` is private and stays private.

---

## 9. Open elsewhere, not `-04`

Standards-adjacent, carried so a new session does not have to rediscover them:

- W3C CCG prior-art post.
- Consider replying to `draft-maintainer-1f916-agent-record-00` on the SCITT list.
- Consider supporting the RATS adoption call for `draft-poirier-rats-eat-da-10`.
- **Four outbound messages bounced on 17 August**, all Google-hosted recipients,
  all rejected by `mx.google.com` as "content presents a potential security
  issue": `cameron@kelley.vc`, `info@mobasi.ai`, `justin.grover@gmail.com`,
  `hexordia@hexordia.com`. Four in one day from `certisyn.com` is a sender-side
  reputation or filter posture question, not four coincidences, and none of
  those recipients know a message was attempted. Not standards work; recorded
  because it silently costs outreach.

Programme, legal and repository-hygiene items are held in the private copy of this
file in the OneDrive `IETF-Drafts` folder, not here, because this repository is
public.

---

## 10. Open commitments to others, with dates

### 10.1 CPB out-of-scope wording. CLOSED 2026-08-16

The out-of-scope reasons in `cpb_run.json` described ARP in language ARP does
not use. "Correlation digest" appears nowhere in `-01`, "by design" asserted an
intent the draft does not state, and the typed-refs reason made a normative
claim about another document's obligations that ARP is not entitled to make.
Replacement wording was agreed with Steven Mih on 9 August. It reached the
runner and the record on 16 August, before his
`draft-mih-agent-accountability-conformance-01` filed.

The strings are emitted by `run_cpb_vectors.py` rather than stored, so the fix
went into the runner and the record was regenerated from it. Editing the record
directly would have produced a run record no run produced.

    branch feat/revision-02-canonicalization   commit ec354e5
    branch wip/revision-03                     commit 5930f5c

| artefact | was | now |
|---|---|---|
| `runs/cpb_run.json` | `c39d204c...` 10,470 B | `ddf063bb23ade16a729bc6ba8baada5c30a4f4ef3ec0f5b52a103f45fbe0208e` 11,972 B |
| `runs/cpb_run.txt` | `0ae0ea71...` 4,550 B | `186cc728e8661505f16f1449f865bdad143b96ae199e229b991665481a705e41` 4,886 B |
| `runners/run_cpb_vectors.py` | `4170baf3...` | `ecaee0cc29127d61abb27ebbf190a07226abff48c2b910d55c8bf1ec3655d774` |

Regenerated against the pinned CPB corpus,
`github.com/action-state-group/scitt-payload-binding` at
`bc08d78a210f8e77d4abfd8c04c10ea9b57d4390`. That repository was not on the
machine and was cloned fresh from the pin in REPRODUCE.md section 2.

**Controls run before committing anything.** The unmodified runner was executed
first and confirmed to reproduce `c39d204c...` and `0ae0ea71...` exactly, so the
delta is attributable. A structural comparison of old against new shows eight
changed leaves, every one a `reason` string under `out_of_scope`. Every row,
digest, verdict and count is identical: ten positive vectors, three agreeing,
seven diverging with five absent-field-normalization and two exclusion-set, one
must-fail refused by both, zero unattributed, SELF-CHECK PASS. REPRODUCE.md
sections 5 and 6 re-pinned, MANIFEST PASS on both branches. The pushed bytes
were fetched back out of GitHub and hashed, and the withdrawn strings return
zero occurrences on the remote.

### 10.2 Stale record at the commit Steven cited. CLOSED 2026-08-16

Steven's draft pointed at `ae54748`, where REPRODUCE.md section 5 recorded
`cpb_run.json` as `cc94f74e...`, contradicting both the file and the digest his
own draft states. A reader following the citation would have found a flat
contradiction with no way to tell which side was wrong.

Superseded by `ec354e5`, where the record and the file agree and the manifest
passes. Three lines had differed between `ae54748` and `6034be6` and nothing
else. One of them, `runs/arp_adapter_run.json`, had been carrying
`typed_ref_cpb01_run.json`'s digest: a transposition between adjacent rows,
which is the failure a checker reading only one layout cannot see. All eight
outputs named in section 5 were fetched at both commits and every one matched
the `6034be6` record, so the artefacts had never changed. Only the record was
wrong.

### 10.3 Two wording problems in Steven's draft text. OPEN, with him

Both checked against `cpb_run.json` rather than against any summary of it.

**The three-conjunct sentence misreads.** It attributes every divergence to
three declared canonicalization steps including the digest-bearing guard. No
positive row carries that cause; it appears on kat-10 alone. The seven positive
divergences are explained by two steps. Split so the seven attach to the
exclusion set and the absent-field-normalization rule and the must-fail row
attaches to the digest-bearing guard.

**"Exactly as an unattributed divergence did" should read "would have".** The
`unattributed` array is empty, so the past tense claims an event that did not
happen.

Sent 16 August. He files Wednesday 19 August.

### 10.4 Iman Schrock's Gap 6 reproduction receipt. CLOSED

Run it and send back the generated `reproduction-receipt.json`.

    https://github.com/emiliaprotocol/emilia-protocol
    commit 14eee68e64a4f8b0b5950e2ddfab753c48d202a9
    node conformance/composition/gap6-execution-evidence-v0.1/run.mjs

Run from the repository root. It writes `report.json` and
`reproduction-receipt.json`. Committed 14-case reference digest is
`sha256:d79e68656441dcf231a4802c1b5c973fa798ca7d48d7e6acacd2c5683148b239`.

`run.mjs` was read before recommending it: 41,882 bytes, no network calls, one
`execFileSync` running `git rev-parse HEAD` to stamp the receipt. The runner's
header states the boundary correctly, that running it externally is a
reproduction of pinned checks and not an independent implementation result.
Keep that framing when reporting.

**CLOSED 2026-08-16.** Reproduced on win32-arm64, Node v24.14.1.
`results_digest` sha256:d79e68656441dcf231a4802c1b5c973fa798ca7d48d7e6acacd2c5683148b239
matches the committed reference, `matches_committed_reference: true`, runner
exit 0, fourteen of fourteen cases at their stated verdict.
`reproduction-receipt.json` is
`3e6e5aee1c37e2926f323e77638bd8452082495d28da680390dd2ddb72f8d9be`, 535 B, and
is staged at `_send/gap6-reproduction-receipt.json`.

Finding returned to Iman: the published instruction does not run on a clean
clone. `@emilia-protocol/require-receipt` is a `file:` dependency resolved
through the lockfile and the root `package.json` declares no `workspaces`, so
`node run.mjs` terminates in ERR_MODULE_NOT_FOUND until `npm ci --ignore-scripts`
runs first. Standing rule 10 applied to somebody else's tree.

### 10.6 Anton Sokolov, 17 August. Precedent worth citing

On `draft-mih-sato-agent-accountability-composition-01`, cc Tom Sato, Steven
Mih, Iman Schrock and Songbo Bu -- four of the seven on one thread. No ARP
content and nothing asked. One line worth keeping: he commits to running another
author's vectors before writing his `-02`, *"since the general obligation should
be stated so that both of your paths discharge it visibly, and the honest way to
check that is against a profile I did not write."* That is 2.4's argument in
somebody else's words, on the SCITT list, this week. Cite it when making the 2.4
ask.

### 10.5 Anton Sokolov, 16 August. No action

His 16 August message to Tora, with ARP copied, asks nothing. One idea worth
taking: a multi-implementation gap register should say which implementation each
row was measured against and on what commit, because the common failure is a fix
landing in the reference implementation while the others keep accepting the
input and the register records the row as closed. That is rule 9 seen from the
register side rather than the control side.

---

## 11. New tree finding, closed the same day

**A run record that pins its own digest must pin its own line endings.**

`run_cpb_vectors.py` wrote with the platform default newline. The record was LF
as committed and CRLF when regenerated on Windows: identical content, different
digest, and nothing in the record to tell a reader whether they were looking at
a line-ending artefact or a tampered artefact. Measured: 197 lines, 10,470 bytes
as committed against 10,667 regenerated, and LF-normalising the fresh output
reproduced the committed digest exactly.

This is the same class as the environment block that used to sit inside
`existence_oracle_run.json`, and it is the general form of standing rule four:
a reproduction manifest is a claim about bytes, and the checkout and the writer
are both part of the measurement. The writer now pins LF.

Worth applying to every other writer in the tree that emits a pinned record.
That check has not been done yet.

---

## 12. Update log

| date | what changed |
|---|---|
| 2026-08-14 | Opened, the day `-03` posted. Sections 1 to 9. |
| 2026-08-16 | Added sections 10 to 12. Closed the 9 August CPB wording commitment in the runner and the record, and the stale-record citation, both verified from the remote. Recorded the line-ending finding. Sections 10.3 and 10.4 remain open. |
| 2026-08-17 | 2.1 closed. RFC 9162 correction, equivalence re-measured to 4200 leaves, `merkle_equiv.py` added to `runners/`. 2.8.1 opened and closed the same day on Nenad Vasic's finding. |
| 2026-08-18 | 2.2 and 2.7 closed as Section 4.23. 2.8.2 closed. 2.8.3 and 2.8.4 opened. Rules 11 and 12 added. Sections 13 and 14 added. Two red-team passes, 28 then 9 findings, all closed. Committed `67723fc`. |
| 2026-08-18 | A4 and A6 checked, closed with no text change. 2.8.5 opened and closed. |

### Current Stage A digests

| artefact | sha256 | size |
|---|---|---|
| `draft-hillier-scitt-arp.md` | `8403896faa356a269fce441a74687689e5ee735d84dae7a2ca667ef1e6e7f64a` | 333,442 B |
| `conformance/runners/merkle_equiv.py` | `366b3868c60758468e40f83de61a74389a2639cd720ac5df7674f0286617c294` | |
| `conformance/README.md` | `6d65e1cada2134a11603cfa811263c120832a721b172927b0332d67df04fddf3` | |

`-03` filed at `e8cb3b93...`, 291,282 B. Stage A is not frozen and these move.
`runs/existence_oracle_run.json` still pins `e8cb3b93...` and the manifest will
fail until Stage C. That is intended.

---

## 13. SCITT list, 17 August

Three threads. What each is worth to `-04` is in 2.8 and 10.6; this is the index.

| from | subject | bearing |
|---|---|---|
| Nenad Vasic | ARP reconciliation run against the EMILIA and Noa corpora | Item 4 is 2.8.1, closed. Item 2 is 2.8.3, open. Item 3 is rule 11. Item 5 corroborates 2.5 from outside: *"spec-supplied bytes-plus-expected-digest vectors are what make the upgrade durable -- deployment-authored vectors measure self-consistency, not conformance."* Item 1 supports the Section 3 agent-axis split unchanged. **He has a git-apply-able patch ready and asked for the slot.** |
| Emek Can Doğru | draft-dogru-scitt-disclosure-evidence-02 | 2.8.4. His own fix -- name both clocks, declare a skew bound, make a boundary-only miss indeterminate rather than an accusation -- is the shape ARP's item 26 may need. |
| Anton Sokolov | draft-mih-sato-agent-accountability-composition-01 | 10.6. Precedent for the 2.4 ask. |

Taking Vasic's patch is the cheapest available move on 2.4 and the strongest
single thing that could be said at an adoption call.

---

## 14. Red team on the `-04` text

Run 2026-08-18 against the new Section 4.9 and Section 4.23 before any build.
Two adversarial passes, instructed to refute rather than confirm. Twenty-eight
findings. What they caught, by class:

**False statements that would have shipped.** The RFC 9162 inclusion-proof
claim (2.8.2 above), the hash-agility overclaim, the "diverges at exactly one
input" sentence whose antecedent resolved to the wrong pair, and the
duplicate-last convention described as simply producing different roots when it
agrees at every power of two.

**Unimplementable requirements in the new Section 4.23.** The Head Consistency
Statement had no media type, no registered header parameter and no defined
signing input -- three implementers, three incompatible signatures. Its
freshness window was measured from a timestamp that made the window close before
any witness could see the head. The Agreement Hash fixed an item order but not
item types or set ordering. All fixed; the media type and header parameter are
registered in Section 9.

**Two security holes in text written the same day.** The witness exclusion ran
*upward* only -- a server incorporating three subsidiaries declares three
distinct operating parties, satisfies a quorum of three and controls every
observation in it. And a Head Consistency Statement over a *higher* head
established nothing without a link back to the named head, since a fork at
disjoint sequence numbers is precisely a pair of heads neither of which
contradicts the other. Both closed.

**One that makes the whole quorum evaluable.** A relying party holds only
Agreement Hashes, so a quorum declared solely inside an Agreement is a test the
party obliged to run it cannot read. The effective set and quorum now go in the
Policy Parameters Document.

Deferred, recorded rather than fixed: items 13, 14, 20, 24 and 25 of the
Agreement anchor normative declarable terms into Section 7, Security
Considerations, which is conventionally non-normative and which an AD review
will flag. Moving them renumbers Section 7 and is a `-05` decision.

**A second pass over the repairs found nine more.** The repairs were themselves
red-teamed rather than assumed, and that pass found: the Agreement Hash type
table covered thirty of thirty-one items; a Witness Entry had no defined key
retrieval path, so the first quorum condition was unsatisfiable; the higher-head
linkage tied neither end of the chain to anything, so a server serving its own
internally consistent entries satisfied it; the effective quorum across several
Agreements could exceed the effective set; two items were typed as sorted
arrays when their order carries meaning; four compound items were given scalar
types; and four statements in the Document History did not match what the draft
said. All fixed. Two passes found twenty-eight and nine.

The lesson generalises the working method in section 7: **text written today is
not evidence, including text written today to close a finding.** Two of the
three defects in 2.8.2 were in `-03` and survived a filing and a networked
idnits run. The scope error in 2.8.1's first draft was written and caught within
the hour. The nine above were all written to close red-team findings and were
themselves defective. Red-team the repairs, not just the original.

### Confirmed by measurement, not by reading

The second pass independently reproduced every number in Section 4.9:
identical roots for leaf counts 1 to 4200, identical sibling arrays for all
131,328 (leaf count, index) pairs to 512 leaves, the duplicate-last convention
agreeing at exactly the powers of two and nowhere else, and the ceiling-halving
correction with the n=5 example. It also confirmed against RFC 9162 that an
`InclusionProofDataV2` carries `tree_size` and `leaf_index` and no leaf.

### Structure, confirmed

84 headings to 100, and **no section anyone cites moved**. 4.9 is 4.9, 6.4.3 is
6.4.3, 6.4.4 is 6.4.4. New material was appended at points that add rather than
insert: 4.9.1, 4.23 with 4.23.1 to 4.23.4 and 4.23.2.1 to 4.23.2.5, and a new
Document History subsection. The only numbers that moved are inside Document
History, which the RFC Editor removes. `tocdepth="4"` was added to the front
matter, since xml2rfc defaults to 3 and would otherwise omit 4.23.2.x from the
table of contents.