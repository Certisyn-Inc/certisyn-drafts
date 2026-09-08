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

## SECOND ROUND: the OPEN list worked through

Every item on the earlier OPEN list was put to a verification pass instructed to
REFUTE it. Results:

| # | Verdict | Outcome |
|---|---|---|
| O-1 | confirmed in part | Privacy Considerations existed and was substantive; what was missing was an RFC 6973 threat walk and any treatment of erasure against an append-only record. Both added. |
| O-2 | confirmed | Notarising an Output exports Subject References to a third-party log with no deletion path. Now normatively prohibited where the disclosure has not been accounted for, and the Ledger is barred from carrying personal data at all. |
| O-3 | CONFIRMED | The requester supplies the Claim Hash preimage octets and no rule required the server to check they are canonical. NFD and NFC of one claim gave two ledger indices and two retroactive-evaluation keys. Check added. |
| O-4 | **REFUTED** | The limit is stated in two places, and the premise was wrong: the requester holds the Canonical Claim. No change. |
| O-5 | CONFIRMED | The Evidentiary Provenance Manifest is inside the Claim Hash preimage and may carry a COSE_Sign1. A **seventh** carrier, and the only one the class rule cannot reach: the preimage is JCS JSON with no byte-string type, and the octets are the requester's. Signed artefacts now prohibited inside it. |
| O-6 | CONFIRMED | The projection function produces the nearest permitted **ancestor**, so a register answers a broader question, and re-typing covered only narrowing. A decisive `match` on "some US sanctions list" answered a claim about the OFAC SDN list. Fourth re-typing ground added. The one Divergence Axis that names this condition appears exactly once in the document, is register-attestable, optional, and connected to no rule. |
| O-7 | CONFIRMED on all three limbs | The Reconstruction Proof had no pinned preimage, no wire representation, and compares a server-produced value against a server-produced value under a server-held key. Preimage and wire form fixed; the stated limit was one step too generous and is corrected. |
| O-8 | confirmed in part | Two such logs, not three. The Regulator Portal trail was called "subpoena-grade" with no sequence, chain, head or notarisation, while the same document applies all four to the Ledger a few sections above. Both logs now chained, headed and notarised. |
| O-9 | confirmed in part | The examined count is not derivable from the Root — the document's own deduplication rule says so. The materially-changed count is attributable and dated, not verifiable. "Not bare assertions" corrected. |
| O-10 | **REFUTED** | `notarisation-incomplete` already distinguishes pending, terminal refusal and never-attempted, and Output notarisation is a MAY, so there is no benefit to fabricating it. No change. |
| O-11 | verified, disclosed | Unchanged; the register leg remains per-Agreement and the document says so. |
| O-12 | worked through | Ten highest-impact implementer items verified: eight confirmed and repaired, one refuted, one narrowed. Detail below. |

### From the implementer pass

Confirmed and repaired: the Predicate Taxonomy had no stated edges, and the
`agent:` branch had no parent relation at all; the reproducibility requirement
was unsatisfiable, three necessarily-fresh fields sitting outside its carve-out;
the Query Binding preimage had no element types though two parties compute it
independently; the Audience Member Identifier had no normalisation or comparison
rule while serving as a sort key in two signed digests; a key identifier had
three spellings across payload, COSE header and path segment with equality tests
between them; the freshness window had no reference instant and no direction;
`fields=linkage` returned three values where the chain condition it exists to
serve needs four, making that condition uncomputable by the only party required
to compute it; suspension had no defined exit; and the response freshness
tolerance every reader must apply was readable only by the parties who do not
have to apply it.

**REFUTED:** the register key discovery root has an encoding, a media type and a
trust anchor. One residue -- whether the root key set is itself signed -- was a
wording ambiguity and is corrected.

**Narrowed:** the containment requirement is satisfiable, because the
prohibition binds the service-operator entity and not the reconciliation server.
What was true is that its named enforcement measure cannot reach six fields the
server is obliged to read in the clear, and the conformance test asked only
about a register record, so the payload half had no test. Both now stated.

---

## STILL OPEN after two rounds

Not a residue of things thought unimportant. These are what a second full pass
would start from.

- **The ~50 remaining implementer-pass items.** Ten were verified and nine
  repaired. The rest are unverified, and on this round's hit rate roughly two in
  three of a pass survives contact. They are wire-format, state-machine and
  error-path items rather than integrity defects.
- **The adversary pass's privacy and abuse items beyond those repaired.** The
  open screening oracle, the Remediation Advisory disclosing Pattern-Library
  identifiers to a prober, Audience-Set flooding, and the Policy-Version Hash as
  a stable requester pseudonym. Each is plausible, none verified.
- **The register leg.** Per-Agreement by design, and the principal thing that
  keeps this document from being end-to-end interoperable.

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
