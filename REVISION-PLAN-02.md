# `-02` revision plan

**Blocked on `RECOVERY.md`.** Do not start drafting until the `-01` source is
in this repository. Every item below is an edit *to `-01` text*, and `-01` text
is not here yet.

Each item records where the commitment was made, so nothing is quietly dropped.

---

## A. Pin the canonicalization — the commitment that matters most

**Origin:** measured against the EMILIA `EP-CANONICALIZATION-v1` vectors
(commit `125e4f4311f1319fef3f6d55c935c9ea4da5fc1b`) and reported to the SCITT
list. Raised independently by Iman Schrock (EMILIA, 25 Jul) and Anton Sokolov
(Tyche Institute, 25 Jul).

### A1. Appendix D — name the profile

Appendix D currently says the subject digest is
`SHA-256(canonical JSON of the action)` without naming a canonicalization
profile. §2 separately defines a Canonical Claim canonicalization that applies
Unicode NFC. The two readings produce different bytes on real input:

| reading | agrees with the EP pinned digests |
|---|---|
| RFC 8785 JCS | 22 / 22 |
| §2 Canonical Claim, member sort = code point | 19 / 22 |
| §2 Canonical Claim, member sort = UTF-16 code unit | 20 / 22 |

Two of the divergences are **collisions**, not merely different bytes:

- NFD "café" collapses onto the NFC digest
  `a84c174531ab46d58aaeb9c85aed22981d418f25bead412cd282e97f427a0ba1`;
- U+212B ANGSTROM SIGN collapses onto U+00C5.

Appendix D's premise is that producers with no shared schemas correlate on a
common subject digest. Unpinned, two conformant producers can compute different
digests for one action, or one digest for two actions.

**Edit:** state the profile by normative reference (RFC 8785 JCS is the reading
that matches the deployed corpus and the one Anton adopted for CPB), and state
explicitly that it is *not* §2's Canonical Claim construction.

### A2. §2 — pin the member sort and the NFC scope

- "lexicographic sorting of object keys" does not pin the code unit. Say
  UTF-16 code unit (RFC 8785) or Unicode code point, normatively.
- "Unicode Normalization Form C of string fields" does not say whether member
  *names* are included. Say so.
- "stripping of undefined values" has no meaning in a JSON transport that has
  `null` but no `undefined`. Define it or remove it.
- §2 says RFC 8259 number rendering; RFC 8785 / ES6 rendering is what
  interoperating implementations use. Resolve which is normative.

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
