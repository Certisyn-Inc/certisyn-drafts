# `-02` revision plan

**Blocked on `RECOVERY.md`.** Do not start drafting until the `-01` source is
in this repository. Every item below is an edit *to `-01` text*, and `-01` text
is not here yet.

Each item records where the commitment was made, so nothing is quietly dropped.

---

## A. Separate the two canonicalizations — the commitment that matters most

**Origin:** measured against the EMILIA `EP-CANONICALIZATION-v1` vectors
(commit `125e4f4311f1319fef3f6d55c935c9ea4da5fc1b`) and reported to the SCITT
list. Raised independently by Iman Schrock (EMILIA, 25 Jul) and Anton Sokolov
(Tyche Institute, 25 Jul).

### A1. State that the two constructions are distinct

Appendix D pins its profile correctly — `subject_digest = SHA-256(JCS(action))`
— and it agrees with EMILIA's deployed canonicalization profile on **22 / 22**
pinned vectors. Nothing to fix there; it interoperates.

The defect is that `-01` never says the Appendix D subject digest and the §2
Claim Hash are *different constructions that must not be substituted for one
another*. §2 applies Unicode NFC; JCS does not. Measured:

| construction | agrees with the EP pinned digests |
|---|---|
| Appendix D — `SHA-256(JCS(action))` | 22 / 22 |
| §2 Canonical Claim, member sort = UTF-16 code unit | 20 / 22 |
| §2 Canonical Claim, member sort = code point | 19 / 22 |

Two of the §2 divergences are **collisions**, not merely different bytes:

- NFD "café" folds onto the NFC digest
  `a84c174531ab46d58aaeb9c85aed22981d418f25bead412cd282e97f427a0ba1`;
- U+212B ANGSTROM SIGN folds onto U+00C5, landing on the pinned digest for
  `accept_latin_a_ring_distinct`.

NFC folding is defensible for a ledger index — the same claim spelled two ways
should fold. It is not defensible as a silent adjacency: an implementer who
reads §2, finds a canonicalization defined for this document, and applies it
where Appendix D says "canonical JSON" loses injectivity without any error.

**Edit:** add a normative statement that the Claim Hash and the subject digest
are distinct constructions serving distinct purposes, and that an
implementation MUST NOT substitute one for the other.

### A2. Fix the three §2 under-specifications

- **Member sort is unpinned.** "Lexicographic sorting of object keys" does not
  say by what unit. Code point and UTF-16 code unit diverge on
  `accept_astral_key_utf16_sort_order` — that is the 19 vs 20 difference. Pin
  it normatively.
- **"Canonical JSON {{RFC8259}} number rendering" has no referent.** RFC 8259
  defines no canonical number rendering; RFC 8785 does. RFC 8259 is also only
  an *informative* reference in `-01` while doing normative work here. Fix the
  citation and promote or replace it.
- **"Stripping of undefined values" has no meaning** in a JSON transport, which
  has `null` but no `undefined`. Define it or delete it.
- **NFC scope.** Say whether NFC applies to member names as well as string
  values.

### A3. Carry an explicit construction identifier

Committed publicly to Iman and Anton. A claim carries its canonicalization
parameters, so a consumer can *determine* compatibility rather than being
warned against assuming it. Reference implementation emits:

```
arp-canonical-claim/1   id=7d90aa1cbee90ef9
arp-subject-digest/1    id=7630fc125d8b77a0
```

where the identifier's digest commits to the declared parameters.

### A4. Identifier equality is a reconciled predicate

A CAID or signed reference travels as a **separate field** and is never
conflated with the digest. Equality holds only against a vector proving
identical preimage, field set, algorithm, domain separation and representation.
Absent that, render a divergence axis; never a silent match.

---

## B. New divergence axes

Two new indeterminate-class axes, committed to Iman and Anton:

| axis | class | meaning |
|---|---|---|
| `caid-binding-unverified` | indeterminate | a typed identifier is present but its binding to the subject digest is not proven |
| `canonicalization-unverified` | indeterminate | the producer's canonicalization parameters are absent or unmatched |

Neither may be upgraded to a match. This mirrors the existing §3.2 / §6.3 rule
that an ENEMY requester MUST NOT be silently upgraded to FRIENDLY — the same
discipline one layer over, at the artifact level rather than the requester
level.

One new hard axis, proposed on the list:

| axis | class | meaning |
|---|---|---|
| `anchor-leaf-not-bound-to-payload` | no-match | a valid inclusion proof for a leaf that is not this artifact's payload |

Distinguishable from a broken proof: it is a genuine proof of a proposition
nobody asked about. **Caveat:** no vector in the EMILIA corpus isolates it —
`reject_v2_unbound_leaf` is both unbound and proof-broken. A vector that is
unbound but otherwise proof-valid should exist before this axis is normative.

Naming questions to settle, raised on the list:

- `agent-credential-absent` currently covers both "no authorising credential
  exists" and "a required signoff is missing." Same axis or two?
- `version-replay` covers both "unsupported format version" and "legacy anchor
  refused by default." Same axis or two?
- `canonicalization-gate-failed` covers three distinct things: parse-boundary
  failures, I-JSON profile-predicate failures, and representation-canonicality
  failures (a timestamp without an offset). One axis or three?

**Convention:** kebab-case, matching the axes already filed. Do not introduce
snake_case variants — Iman is already citing `agent-action-scope-divergence` by
name in correspondence.

---

## C. Normative citation of the composition work

Appendix D composes over the CAN / WHO / WHAT / AUDIT slots. Those are defined
in *Agent Accountability: Composition and Conformance* (5 July 2026 — Schrock,
Mih, Sato, Bu). `-02` should cite it normatively rather than describe it.

Related work to reference:

- `draft-schrock-action-evidence-boundary` (AEB `-02`, 21 July) — executor-side
  admission boundary. AEB admits; ARP reconciles. Show the seam explicitly.
- `draft-mih-sokolov-scitt-payload-binding` (CPB) — pins payload binding
  beneath; ARP reconciles the verdict above. Anton's Related Work
  characterisation of ARP is accurate and should be reciprocated.
- `draft-noa-scitt-ai-agent-receipt` — Tora Toraman's `-01` is expected after
  15 August and is defining the shared action-digest construction. Converge
  Appendix D with it rather than in parallel.

---

## D. Conformance

The reference harness (`arp_reconcile.py`) runs ARP composition against the
EMILIA `frozen-v1` and Noa corpora and is the evidence behind §A. Bring it into
this repository under `conformance/` so the spec ships with running code.

Chain-level axes the harness exercises that no per-receipt verifier can reach,
and which `-02` should name:

`chain-link-broken`, `chain-sequence-duplicate`, `chain-sequence-gap`,
`chain-scope-mismatch`, `chain-head-truncated`.

Two behaviours in the proposed six-vector interop set have **no vector** in any
published corpus: controller-reported outcome, and physical-completion
non-claim. ARP defines predicates for both (`outcome-reported-only`,
`physical-completion-unproven`). Either contribute the vectors or mark the
predicates as unexercised — do not imply coverage that does not exist.

---

## E. Appendix E

Add `E.2 Since -01` listing every change above. Reviewers read it first.
