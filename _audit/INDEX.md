# Type-table sweep, 2026-08-19/20

Three adversarial passes over every digest construction the draft defines,
applying one test: for each item of each preimage, does the normative text fix
(a) the CBOR major type, (b) the ordering rule where the item is a collection,
(c) omit-or-null where the item is OPTIONAL, and (d) transmitted bytes or a
re-encoding where the item came from another party?

The test is the document's own, stated at the head of the Agreement Hash
section: *"Determinism under Section 4.2.1 of RFC 8949 fixes how a given value
is encoded. It does not fix which CBOR type an item takes, nor the order of
elements within an item that is a set."* That paragraph is discharged for one
construction out of the fourteen audited.

**Status: CANDIDATE FINDINGS, NONE VERIFIED.** Nothing below is a defect until
it has been checked against the text by a second reading that is trying to
prove the finding wrong. Prior experience in this cycle is that roughly a
third of an adversarial pass survives contact.

## Passes

| pass | scope | candidates | file |
|---|---|---|---|
| 1 | Claim Hash, Merkle construction, Aggregation, Examined-Set Root, Partial Attestation / Query Binding, Source-Data Version Identifier Set | 21 BLOCKING, 9 LATENT | table below |
| 2 | Reconciliation Hash, Policy-Version Hash, Post-Seal Evaluation Record Hash, Superseding-Reconciliation Hash, verdict inputs, Non-Answer Statements, Agreement Hash | see file | `pass2-output-policy-digests.md` |
| 3 | ledger entry hashes, witness entries, head consistency, request binding, read signing, Pattern-Library Commitment Hash, audit path | 19 BLOCKING, 9 LATENT | table below |

## Clean results, recorded because a clean result is a result

- **The Merkle construction.** Pass 1 could not break it. Leaf sort and dedup,
  domain separation, the carry-up odd-node rule, the empty-tree value, and the
  ceiling-halving sibling walk are all pinned, and the three divergent
  conventions it could have been confused with are each named and excluded.
- **The Agreement Hash type table.** All 31 items typed, sets given ordering
  rules, empty Witness Set pinned to `null` rather than `[]`. This is the model
  the other constructions are to be brought up to.
- **The ledger entry absence rule and type registration.** Absence MUST be
  encoded as `null` and MUST NOT be expressed by a shorter array; the IANA
  registration types ten field classes.
- **The Signing Input Digest.** `external_aad` pinned at zero length, protected
  header taken as transmitted and MUST NOT be re-encoded.
- **The global timestamp rendering.**
- **The RFC 9421 read-signing profile**, for everything RFC 9421 asks a profile
  to state.

## Highest-value candidates to verify first

Ordered by blast radius, not by pass.

1. **"authority origin" is used sixteen times and defined nowhere.** It is a
   sort key in the Addressed-Registers Identifier Set, a field of ledger
   entries, an item of the Agreement Hash, and a path segment. If true, one
   term fixes four digests.
2. **The Policy-Version Hash preimage has no type table** while the text
   requires it to be reconstructible under audit. Nine of eleven elements
   untyped; `Requester-Binding` has a "where known" element with no
   omit-or-null rule.
3. **The key thumbprint** (RFC 7638 3.4 octets vs 3.5 base64url) appears in
   Witness Entries, Audience Members and the Audit Identity, and is a sort key
   in two of the three.
4. **The Source-Data Version Identifier Set has no ordering rule.** Five other
   sets in the document are sorted explicitly; this one is called a Set in its
   own section heading and is carried into two signatures.
5. **The Self-Entry Hash preimage is not required to be deterministically
   encoded.** Four sibling constructions say it inline; this one says only "a
   CBOR array". Definite vs indefinite length is the divergence, and the
   document's own remedy for a mismatch is to declare a fork.
6. **The Pattern-Library Commitment Hash is named once and defined nowhere.**
7. **The linkage triple served under `fields=linkage`** carries no Entry
   Signature, so the quorum rule's chain condition may not be computable by the
   party required to compute it.
8. **The Reconstruction Proof** (HMAC-SHA-256 under the Deployment Blinding
   Value) fixes neither its message serialisation nor the key's octet form.

## Next

- Verify each candidate against the text, adversarially, trying to prove the
  finding wrong. Discard what does not survive.
- For what survives: extend the Agreement Hash table format to every
  construction. Item, CBOR type, ordering rule, absence rule, one row each.
- Type table before vectors, per Tiago Marques' sequencing rule.
- This is `-04` work only where a survivor is BLOCKING between two conforming
  implementations. The rest is `-05`.
