# `-04` adversarial sweep: what was found, what is fixed, what is not

Six adversarial passes run 2026-08-20, each carrying the method of a specific
reviewer now active on the SCITT list, plus two lenses no one on the list has
applied yet.

| pass | lens | posture |
|---|---|---|
| 1 | Sokolov | the arithmetic of counting; false merge and false split, swept in both directions |
| 2 | Sirkkavaara | breadth and depth; vocabulary reach; fail-open hunt |
| 3 | Doğru | what ground does each claim stand on; tail blindness; placement |
| 4 | AD / Gen-ART / SecDir | what generates a DISCUSS at IESG evaluation |
| 5 | independent implementer | build it from the text alone, with no author to ask |
| 6 | hostile party and privacy regulator | defeat it while conforming; harm the data subjects |

Roughly two hundred candidate findings. **Nothing here is a defect because a
pass said so.** Everything in the FIXED table below was verified against the
text by a second reading before it was repaired. Everything in the OPEN table is
a candidate that has not been verified, or has been verified and not yet
repaired, and is labelled as which.

---

## FIXED in `-04`, verified before repair

### The one that was already in an outgoing email

**The falsifiability count was rounded up.** Section 4.20.1 claimed the sweep
deadline argument holds for three of four retroactive triggers, "stated rather
than rounded up". Only `source-data-version` rested on an event outside the
reconciliation server. The other two rested on a transition array published by
the server, under the server's own key, in a Policy Parameters Document with no
publication time, no notarisation and no chain. A transition omitted from the
array started no clock and no party could date the Document well enough to show
it had been. On that footing the count was **one** in four, in the one sentence
where the document congratulated itself on not rounding up.

Repaired by fixing the mechanism rather than the sentence: the Document now
carries a Publication Timestamp, MUST be notarised on the ledger-head interval,
and MUST be republished on that interval whether or not its contents changed.
The last is what makes silence readable. The claim is now three in four *and
conditional on that anchoring*, and the document says so.

This was in the drafted reply to the closing-omission thread. Corrected there
before sending.

### Fail-open: a decisive verdict out of nothing

**An empty Addressed-Registers Identifier Set produced a decisive `match`.**
Every verdict operator is defined by a condition universally quantified over the
contributions, and both precedence rules begin "where any". At zero
contributions every operator is vacuously satisfied and neither rule fires:
conjunction yields `match`. Nothing required the set to be non-empty. Two
further guards go vacuous at the same point -- the sealing-key authority check
quantified over "every register in the Addressed-Registers Identifier Set", and
the regulator field restriction taken as an intersection over the applicable
Agreements. Three independent guards fail together, not because an operator
misbehaves but because every guard is true of nothing.

**A source class with no members produced a decisive `no-match`.**
`source-class-quorum` runs threshold-count per class over a partition resolved
from the policy-epoch store rather than from the registers actually addressed. An
empty class cannot reach a threshold of one and carries no `indeterminate`
contribution, so it yields a decisive negative, which conjunction propagates.
The `indeterminate`-substitution rule does not reach it: that rule governs
evidence that is present and inconclusive, and this is evidence that is absent.
In a sanctions deployment that is a signed, sealed, ledgered `no-match`
assembled out of the partition.

Both repaired with explicit rules and the reasoning stated.

### A sixth signature carrier, missed by two prior sweeps

**The Override Record's operator signature sits inside the Reconciliation Hash
preimage.** Section 7.9 enumerated five constructions taken over signed
artefacts and the Reconciliation Hash named two carriers to be replaced by
Signing Input Digests. The Override Record is a COSE_Sign1 by the authorising
operator -- deliberately not the server -- in a field the preimage carries. A
third party substitutes `(r, n-s)`, the Reconciliation Hash moves, and with it
the ledger index, the Self-Entry Hash, the Entry Signature payload and the next
entry's Prior-Entry Hash. A reader concludes the chain is broken when the
operator equivocated about nothing.

It failed no test that was applied to it. No test was applied to it.

Repaired by stating the rule **over the class** rather than over an
enumeration: in any preimage this document defines, every signature made by a
party other than the party computing the digest is replaced by its Signing Input
Digest. An enumeration of carriers is correct until someone adds a field.

### The subject-mapping step

**Nothing recorded, constrained or exposed the transformation from the claim's
Subject Identifier to the Subject Reference each register was actually asked
about.** Every signature can verify, every Query Binding can recompute, the
Merkle Root can be correct, the entry can chain and the notarised Signed
Statement can pass every check, while every register answered honestly and
completely about a different person. Invisible to the requester, to an Audience
Member, to a regulator, to an Audit Identity, and to the registers, none of
which is shown the Canonical Claim.

Repaired with a Subject Mapping Record carrying the Subject Reference and a
registered Subject Mapping Descriptor naming the transformation, which must be a
function of the Subject Identifier and declared terms alone. A holder of the
Canonical Claim recomputes and compares. A party without it gets an attributable
signed statement of which subject was asked about: the substitution stays
possible and stops being deniable, which is the trade Section 4.11 already makes
for a suppressed register answer.

### Evidence obtainable only from the party it is evidence about

**Head Consistency Statements had no retrieval path.** The document specified the
artefact, the quorum arithmetic, the linkage chain and the freshness window, and
specified no channel. The obvious implementation is that the responding service
hands them over with its response, which satisfies every stated condition. The
witness signature prevents forgery and does nothing to prevent selection, so
under exactly the fork the mechanism exists to detect, each branch's reader
receives the witnesses that branch was fed and the quorum is met on both.

Repaired: witnesses publish at `/.well-known/arp-head-consistency` on the
Authority Origin of their Operating-Party Identifier, and a relying party MUST
NOT accept for quorum purposes a Statement obtained from the responding service.

**A quorum of `t` was satisfiable by one key.** Distinctness was tested on the
Operating-Party Identifier alone. Two entries declaring one key under two party
identifiers satisfy a quorum of two with a single COSE_Sign1. Distinct from the
declared-independence limit Section 4.23.5 concedes and cannot close: that one
is untestable, this one is one thumbprint compared against another. Repaired by
requiring pairwise distinct Verification Method References.

**The effective Witness Set was an intersection with no equality relation.**
Over whole entries it empties on a difference in the first element and the
deployment must stop serving reads; over the Operating-Party Identifier alone
two entries with different keys merge and an unauthorised key is accepted. Both
readings available from the bare word. Relation now stated.

### Identity arithmetic

**No value in a Reconciliation Output was unique to the reconciliation event.**
The Reconciliation Identifier was the Claim Hash concatenated with the
Policy-Version Hash, both reproducible functions of enumerated inputs, so two
reconciliations over one claim under one policy state shared it -- which is not
a contrived case but the one a Source-Data Version supersession constructs, since
that trigger leaves policy state unchanged by definition. Three mechanisms key
on that identifier and each assumes it names one event: the register's own audit
read, the Query Binding admissibility rule, and the Non-Answer replay defence.
All three were relying on a property nothing established.

Repaired with a 16-octet random Reconciliation Event Identifier, carried as its
own Output field and appended to the Reconciliation Identifier.

### Encoding determinism

- **The Reconciliation Output had no CBOR type table**, while Section 4.23.3
  supplies one for the Agreement Hash and states the exact argument for why one
  is needed, and IANA supplies one for a Ledger entry. The Reconciliation Hash
  is the ledger index, the retrieval key, and a value the requester computes
  independently. Table added.
- **The Self-Entry Hash preimage had no deterministic-encoding requirement**,
  where four sibling constructions state it inline. A definite-length and an
  indefinite-length encoding of one entry give two Self-Entry Hashes, and the
  head comparison treats that as a fork, which obliges a regulatory report
  against an operator that equivocated about nothing. Stated.
- **`authority origin` was used seventeen times and defined nowhere.** No RFC
  6454 and no RFC 9110 in the reference list. A sort key inside signed sets, a
  path segment, and an equality target against a Sealing-Key Identifier. Now
  defined as an Authority Origin with RFC 6454 normative, and rejection rather
  than normalisation required, because a value normalised on receipt is a value
  two parties hash differently before they compare it.
- **The Source-Data Version Identifier Set** had no ordering rule, a disjunctive
  state identifier with no discriminator and no named algorithm, and no equality
  rule though carried twice. All three repaired, including the corpus-bytes rule
  -- the digest branch is taken over the octets the publisher serves, before any
  decompression, because a list published as an archive has two byte sequences
  with an equal claim to being the corpus.
- **The fifth server-recorded Divergence Axis had no member form**, and the Set
  is inside the Reconciliation Hash preimage.
- **The query budget was keyed per subject with no subject equality relation.**
  The principal half was pinned in three tiers; the subject half was pinned
  nowhere, so the bound on recovery-by-search was evadable by respelling and the
  per-subject ceiling was a shared counter whose key could be collided with a
  victim's.

### Vocabulary that did not reach the output

- **A verifier told to refuse a proof had no way to say which refusal it made.**
  Four conditions arrive at "refuse" and are evidence about four different
  things. Repaired with a Verification Outcome registry, and one rule that
  matters: where the artefact held and the artefact committed to have equal
  Signing Input Digests and unequal enveloped bytes, a verifier MUST report
  `same-act-distinct-encodings` and MUST NOT report a leaf or root mismatch.
  Same-act-two-encodings is evidence of a re-encoding and of nothing else.
- **One reason code carried five distinct causes.** Four other sections directed
  implementations to `attestation-unverifiable` for conditions its own
  definition never named. A failed signature, an echo mismatch, a query-binding
  mismatch, a fabricated source-data identifier and a scope excess are not
  variants of one condition, and two of them are server-side faults recorded
  against the register. Split into five values.

---

## OPEN

Recorded rather than repaired. Each is labelled with whether it has been
verified against the text.

| # | Finding | Verified? | Why not yet fixed |
|---|---|---|---|
| O-1 | No Privacy Considerations section meeting RFC 6973; no erasure, rectification, lawful-basis or controller/processor treatment against an append-only ledger and an external transparency service | not verified | Needs a section, not an edit. Flagged by two independent passes as DISCUSS-level. Highest-value remaining item. |
| O-2 | Notarisation exports Subject References and Audience Member identifiers into an external append-only log with no deletion path | not verified | Interacts with O-1; fix them together |
| O-3 | The Claim Hash preimage is supplied by the requester and no rule requires the server to check it is canonical | not verified | Plausible and serious; needs a check of the request-binding section |
| O-4 | The Claim Hash is asserted to bind an Output to its question, and only the server can compute it; the parallel limit is stated for the Policy-Version Hash and not for this | not verified | Likely a stated-limit fix rather than a mechanism change |
| O-5 | The Evidentiary Provenance Manifest is a Canonical Claim field inside the Claim Hash preimage with no defined structure | not verified | May carry signatures, in which case it is a seventh carrier |
| O-6 | A decisive `match` can rest on a predicate broader than the one asked; no re-typing ground covers taxonomic broadening off the depth axis | not verified | Needs a fourth re-typing ground or a move of an axis from register-attestable to server-recorded |
| O-7 | The Reconstruction Proof compares a server-produced value against a server-produced value under a server-only key, over an unpinned preimage | not verified | The vacuity is the substantive half |
| O-8 | Three "append-only" logs specified with no sequence, chain, head, notarisation or signature, held by the party they record | not verified | "Subpoena-grade" is currently self-attestation |
| O-9 | The Examined-Set Root's two counts are bare assertions; the "materially changed" count is committed to nothing | not verified | The document already discloses the leaf-count arithmetic; the claim beside it may over-read |
| O-10 | `notarisation-incomplete` does not distinguish a genuine polling timeout from a submission never attempted | not verified | Same class as the reason-code split already done |
| O-11 | The register-leg transport is per-Agreement, so ARP is interoperable in its artefacts and not in that leg | verified, disclosed | Already stated in the document as the principal item left for the next revision |
| O-12 | Numerous smaller encoding, state-machine and wire-format gaps from the implementer pass | not verified | ~60 items; triage before acting |

**The IESG pass, the implementer pass and the adversary pass are recorded in
full at `_audit/pass-iesg.md`, `_audit/pass-implementer.md` and
`_audit/pass-adversary.md`.** Between them they contain more candidate findings
than this revision can carry. Working through them is `-05`.

---

## What the sweep says about method

Three of the repairs above were to claims this document made **about its own
rigour**: the falsifiability count that said "stated rather than rounded up",
the enumeration of signature carriers that said "every digest in this document",
and the witness rule that said two instances of one observer are not two
observers. Each was a sentence written to close a question, and each closed it
for the cases the author was looking at.

That is the same shape as the probe that computed `sha256(X) == sha256(X)` and
the vector builder that certified three encoder defects using the encoder under
test. The claim and the check were produced by one mind, so the check confirmed
the claim rather than testing it.

The rule that follows, and the reason six passes were run rather than one: **a
sentence asserting that a document has been thorough is the sentence most likely
to be false, because nothing was pointed at it.**
