# Continuation-entry round: what it closed, what it opened

> **Status.** This is the round-B inventory, written before the repair. Rounds C
> (repair), D (review), and E (correction) followed; most findings below are now
> closed or explicitly acknowledged in the text, and section 3's recommendation
> was carried out. `ARP-HANDOFF-2.md` has the outcome and, in its section 4, the
> diagnosis this document could not yet make. Keep this file for its line-level
> detail, not for its conclusions.

Written 2026-08-09. Scope: the eleven-hunk change to `draft-hillier-scitt-arp.md`
on top of `wip/revision-03` @ `625ee31` that gave the Settlement-Layer Ledger an
Entry Type discriminator and per-type field lists.

Reviewed by three independent adversarial passes, run without sight of each
other: dimension 1 (normative rigour), dimension 3 (role and lifecycle
walkthrough), dimension 4 (adversarial security). 48 raw findings, deduplicated
below to 19. Line numbers are the post-edit source.

**Verdict: this round did not converge.** It closed six defects and opened
roughly fifteen. That is the same ratio as rounds 1-6 and it is the reason the
handoff said to stop rather than any single unresolved item.

---

## 1. What the round actually closed

These were real, and they are closed:

1. Continuation entries now have a type discriminator and an enumerated field
   list per type. The document no longer says "comprises only" and then
   describes entries carrying other fields.
2. `{{post-seal}}` no longer requires a hash to be appended to a
   `Post-Seal Evaluation Record Hash Set` that never existed, on an entry that
   was already signed, through an UPDATE the Ledger does not expose.
3. The Self-Entry Hash is defined. It was previously used in three normative
   sentences and never constructed.
4. The terminology definition of the Settlement-Layer Ledger is no longer two
   fields short of the normative section.
5. The determinism exemption list now names the Entry Signature, the Override
   Record and accumulated query-budget state.
6. The Cryptographic-Primitive-Upgrade Path no longer claims Ledger entries
   commit to no cryptographic identity, which the Entry Signature made false.

Two of the four items the handoff said would collapse into this one did
collapse: the Continuation form, and the post-seal in-place write. The other
two — relying-party discoverability and fork detection — were attempted and are
worse than before, for the reasons below.

---

## 2. Introduced defects, by what they block

### Blocking — a party cannot do what is required

**2.1 The continuation-scope authorisation predicate is unevaluable, and
excludes the party it was written for.** (lines 1424-1427)
"authenticated under the same Requester-Binding as the reconciliation that
Reconciliation Hash identifies" cannot be checked by the Ledger: 1413-1415
forbids it from storing any principal identifier in the clear, and the
Requester-Binding is committed only through the blinded Policy-Version Hash. The
Output carries only the Requester-Binding *Class*. Worse, the relying party is
characteristically not the Requesting Principal — that is what makes the Output
a bearer artefact in the first place — so the scope written to serve relying
parties admits requesters instead. Where the class is `agent-unverified` there is
no principal at all, so the scope is either empty for that whole population or,
under the class-equality reading an implementer will reach for, lets any
unverified agent read every unverified agent's continuations.

**2.2 `continuation-supersession` dead-ends at a bare hash.** (1376-1381)
It carries a Superseding-Reconciliation Hash and nothing else.
`continuation-post-seal-record` carries a hash *and a retrieval URI*; this one
does not. Continuation scope MUST NOT return a reconciliation entry (1427),
regulator scope needs credentials the relying party does not hold, SCRAPI
retrieves by EntryID only. The worked example at 2118-2124 has the party "follow
the Superseding-Reconciliation Hash"; there is nothing to follow it to. The party
learns it was superseded and cannot learn by what.

**2.3 `continuation-notarisation` is never required to be written, and cannot
express the outcome that is.** (1364-1368)
The pre-edit text stated declaratively that notarisation outcomes are recorded
as Continuation entries. That sentence was deleted and replaced by a field list
with no obligation attached. `continuation-post-seal-record` has a MUST,
`continuation-supersession` has a MUST, this one has none. Separately, the type
admits "the EntryID … or the terminal failure it reported" — polling-bound
exhaustion is neither, so `notarisation-incomplete`, the one state the protocol
names for this, is unrepresentable in the entry type built for it. The failure
path is mandatory and the success path is optional.

**2.4 Sovereign Re-Notification on credential revocation has no superseding
Output.** (414-415 against 1531-1536, 1376-1379)
The reworded definition makes *every* Sovereign Re-Notification a
`continuation-supersession` entry. Revocation of a Verified Principal Credential
is a material change requiring a Re-Notification but produces no new
Reconciliation Output, and the Superseding-Reconciliation Hash is unconditional
with no absent case. The server must omit a mandatory field, which the
discriminator was added to make impossible to distinguish from malformed.

**2.5 "Both records are REQUIRED" contradicts `{{retroactive}}`.** (1403-1404
against 1522-1528)
Here it is unconditional; there the `continuation-supersession` entry is required
only on a material change, while the Source-Reconciliation-Output Identifier is
present on any supersession. So a non-materially superseded Output gets a forward
pointer and no back pointer, and the field designed to say so — Material-Change
Indicator with value `false` — is unreachable, since the entry carrying it is
only written when the change is material.

**2.6 The storage-layer rejection rule and replication cannot both be
satisfied.** (1389-1391 against 1408-1411, 1483-1488)
Rejecting a Continuation entry "whose Reconciliation Hash matches no earlier
reconciliation entry in the same chain" bars the append in exactly the
cross-jurisdiction case cited eight lines later to justify recording supersession
from both ends. If the store rejects, the next entry's Prior-Entry Hash points at
nothing. "In the same chain" is undefined where each store has its own chain
sharing only a common prefix. No error surface is defined for a rejected APPEND.

**2.7 The Regulator Portal's scope algorithm has no inputs for a Continuation
entry.** (1383-1385 against 1494-1499)
The Portal intersects per-agreement permitted-read-predicates across every
agreement addressed by the reconciliation being read. A Continuation entry names
no registers and no agreements, by explicit design. No join rule to the
reconciliation entry is stated. The intersection is over an empty set — which by
the paragraph's own reasoning is either no access or unrestricted access.

**2.8 "Exactly three scopes and no other" forecloses three roles the document
requires.** (1420-1421)
The auditor, whose path the Policy-Version Hash must be reconstructible under
(1227-1234); the addressed register, which can no longer observe whether the
head-notarisation interval it declared is honoured; and the secondary store,
required at 1442-1444 to demonstrate a common prefix with every other store's
chain, which matches none of the three scopes. The pre-edit text listed READ's
consumers without making the list exhaustive. Making it exhaustive was the error.

### Security — reachable attacks

**2.9 Head-consistency scope recovers redacted fields by offline search.**
(1428-1430, 1332-1334)
The Self-Entry Hash preimage carries no blinding value. A party holding the
leading fields — a regulator that read the entry under a restrictive
intersection, or anyone holding a Reconciliation Output — brute-forces the
withheld type-specific block: register subsets, a controlled aggregation
descriptor, three binding classes, a timestamp bounded by the Entry Timestamp.
Order 10^9-10^10 SHA-256. This defeats the Regulator Portal's field redaction
*off the audit trail*, since 1500 audits Portal access and this is a different
scope. It is the same low-entropy-preimage argument the draft already makes at
1245-1254 to justify the Deployment Blinding Value, not applied here.

**2.10 Unauthenticated head-consistency sweep leaks entry count, write rate and
retroactive-burst timing.** (1428-1430)
Binary-search the largest answering sequence number for the exact ledger size;
poll for the write rate; watch for the burst of `continuation-supersession`
entries after a public sanctions-list republication and read off how many
reconciliations that listing materially changed across the whole deployment. No
authentication, rate limit, audit or budget applies to this scope. `{{side-channel}}`
addresses per-register projection narrowing only and does not cover any of it.

**2.11 The fork test is unsound in both directions.** (1467-1472)
*False positive:* Entry Sequence Number is only "monotonically increasing", not
globally unique, and replication explicitly permits chains that diverge past a
common prefix — so two honest stores produce the same sequence number with
different Self-Entry Hashes, which the text calls a fork on its face. The Head
Statement carries no store, chain or jurisdiction identifier to tell them apart.
*False negative:* a dishonest operator publishes branch A's heads at sequence
1000, 2000 and branch B's at 1500, 2500. No two collected statements ever share a
sequence number, so the collision test never fires, and the fallback — reading
the lower sequence number under head-consistency — returns an unsigned,
unattributable digest that the operator answers per audience.

**2.12 The Entry Signature is outside the chain hash.** (1332-1337, 1393-1395)
The Self-Entry Hash covers every field preceding it; the Entry Signature is
enumerated after it, and the next entry's Prior-Entry Hash is the Self-Entry
Hash. So no signature is covered by anything. An operator can strip, replace or
re-sign every historical Entry Signature and every Self-Entry Hash, every
Prior-Entry Hash and every published and notarised head still verifies. The
field the document says "makes a second chain attributable" is the one field
left outside the chain. Structurally pre-existing — the pre-edit text had the
same ordering — but only visible now that the Self-Entry Hash is constructed.

**2.13 The Ledger Head Statement has no authorisation anchor.** (1451-1458)
Sealing-key discovery is rooted in the Addressed-Registers Identifier Set of a
specific Output: the reader checks the key's origin against every addressed
register's Authorised-Origin Document (1767-1770), and 1744-1749 says explicitly
that skipping this "would accept an Output minted by any party able to stand up
a host". A Head Statement names no register set, so a third-party fork detector —
the actor 1476-1477 widens the mechanism to serve, who holds no Output at all —
can verify the signature only against a key set fetched from the same origin
that served the statement. That is TLS-equivalent trust, which 1792-1797
identifies as varying per audience.

**2.14 Suppressing a `continuation-supersession` is undetectable.** (1424-1427)
The relying party queries continuation scope and gets an empty set. The scope
specifies no completeness statement, no "as of head sequence N" binding, no
freshness bound and no signature on the response. Nothing distinguishes
suppression from not-yet-appended, from held-in-another-jurisdiction, from
nothing-happened. The remedy at 1527-1528 is a MUST that is unfalsifiable from
every position outside the server.

**2.15 Continuation scope does not disclose "nothing about the
reconciliation".** (1435-1436)
The Material-Change Indicator states whether the Combined Verdict crossed the
decisive boundary. The post-seal record behind the carried URI carries the
Policy-Version Hash and Pattern-Library Version *in force at evaluation time* —
values the requester never held, stable within the deployment, and therefore
durable correlators. The `continuation-notarisation` EntryID resolves at the
Transparency Service to the full sealed Output, Per-Register Result Set
included, with no authorisation requirement stated anywhere.

**2.16 The `query-budget-exhausted` determinism carve-out is an unfalsifiable
suppression channel.** (518-523)
Any non-answering register makes a decisive verdict unreachable. The operator
returns `query-budget-exhausted` for one register on any reconciliation it
dislikes. An auditor replaying the enumerated inputs now gets a different result
and is *required* not to treat it as a determinism failure. The budget is state
the operator alone holds, declared in an agreement the relying party cannot
read. This is a new interaction with the known requester-independent-budget
defect, not that defect.

### Consistency and encoding

**2.17 The Self-Entry Hash is not reproducible.** (1332-1334, 1352-1381,
1986-1988)
Three separate gaps. The sentence "every field of the entry preceding it" reads
either as this entry's earlier fields or as the preceding entry's fields — under
the second reading it collapses into the Prior-Entry Hash. The type-specific
lists say "additionally comprises" with no ordering statement, while the IANA
text requires every future registration to state its order — so the four initial
types fail the rule they impose. And nothing says whether an entry is a CBOR
array or a map (a map re-sorts by key under RFC 9052 deterministic encoding,
overriding the stated order), whether an absent OPTIONAL field is omitted or
encoded as null, or how the `continuation-notarisation` "exactly one of" union
is discriminated. Two conforming implementations compute different chains, which
the fork test then reports as an attack.

**2.18 The determinism carve-outs contradict the Reconciliation Hash
preimage.** (507-518 against 1196-1199)
The Reconciliation Hash is the digest over the Output excluding *only* the
Sealing Signature and Sealing-Key Identifier. The Reconciliation Timestamp and
the Override Record are therefore inside its preimage. Declaring them outside
the determinism requirement, in a paragraph whose first sentence requires
identical Reconciliation Hashes, makes that requirement unattainable. The
underlying tension predates this change; the edit made it explicit and did not
resolve it.

**2.19 The IANA expert instruction refuses the registry's own first entry.**
(1988-1990)
"MUST refuse a registration whose type carries a field that restates one already
bound by the Reconciliation Hash" — the Reconciliation Hash binds nearly the
whole Output, so the Policy-Version Hash, Addressed-Registers Identifier Set,
Requester-Binding-Class Descriptor and Reconciliation Timestamp carried by the
`reconciliation` type are all caught. "Restates" is undefined. The registry also
never states the Entry Type's value space (text string or CBOR integer) and does
not require a registration to state each field's value type, which the COSE
registrations at 1947-1949 do require.

**Also:** the Ledger definition still reads "retaining only hashes … with no
content-bearing fields" (470-472) while the new types carry a Transparency
Service Identifier, an EntryID and a retrieval URI. Nothing requires a retrieved
Post-Seal Evaluation Record to digest to the hash carried beside it, or
constrains the URI's scheme or path — a path segment naming the requester would
breach 1413-1415 with nothing to catch it. The blinding rationale at 1250-1251
("in every Ledger entry") is now false for Continuation entries. Head Statement
notarisation is unsatisfiable under `{{scrapi-binding}}`, whose protected header
demands a Policy-Version Hash and an agreement hash a head does not have; "each
published" collides with "at an interval"; and a head notarisation that exhausts
its polling bound can be recorded nowhere, since a Post-Seal Evaluation Record
requires a Reconciliation Hash.

---

## 3. Reading of the result

The structural half of the change is sound and should be kept: two entry kinds,
a discriminator, per-type field lists, a constructed Self-Entry Hash, and
Continuation entries replacing the impossible in-place write. Those close real
defects and nothing in the review argues for reverting them.

The half that overreached is the read surface. Three of the four worst findings
— 2.9, 2.10, 2.11 — exist only because head-consistency scope was invented to
make fork detection work, and it created an unauthenticated, unblinded,
unaudited oracle over the whole ledger. Two more — 2.1, 2.14 — exist because
continuation scope was invented to make post-seal records discoverable, and the
authorisation predicate for it cannot be evaluated from anything the protocol
stores. Both were attempts to close handoff items that the handoff had correctly
identified as blocking; both need a design cycle, not an edit.

The cheap, contained subset — 2.3, 2.4, 2.5, 2.17, 2.18, 2.19, and the
consistency items — is roughly an evening and would leave the round net
positive on defect count. The read-surface subset is not.

## 4. Method note for the next round

Dimension 3 remained the highest-yield pass and dimension 4 found everything
that made the round net negative. Running dimension 4 *before* committing to a
new externally-reachable surface, rather than after, would have caught 2.9 and
2.10 at design time: both follow directly from an argument the document already
makes about low-entropy preimages, applied to a digest the change introduced.
