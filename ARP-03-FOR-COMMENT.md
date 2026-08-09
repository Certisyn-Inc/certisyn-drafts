# draft-hillier-scitt-arp-03 — proposed, for comment before filing

Joel David Hillier, Certisyn, Inc. — 9 August 2026

**-02 was filed on 8 August and is what is published.** This describes the
revision I propose to file on **Thursday 13 August**. It is written, it builds,
and it lints. I am circulating it first rather than filing it, because a
revision that goes up with your comments in it is worth more than a revision
that goes up a day sooner.

**Comments by end of Wednesday 12 August.** I will file on the 13th either way,
and anything that arrives after that goes into -04.

The full text is attached as `draft-hillier-scitt-arp-03.txt`.

---

## 1. Why there is a -03 at all, one day after -02

-02 closed the canonicalisation question. Reviewing it against a role-and-
lifecycle walkthrough — reading the document as each party in turn, from first
contact to final artefact — turned up something structural that six earlier
rounds had each papered over one mechanism at a time:

**The document added normative machinery faster than it defined the substrate
that machinery stands on.** Each round added a mechanism; each review found the
mechanism required something never defined; the next round added another
mechanism to patch the gap.

Three layers were missing outright.

- **No delivery statement.** The document never said that a Reconciliation
  Output is delivered to the party that asked for one. The only artefact the
  pipeline was stated to return to a requester was a failure advisory.
- **No entitlement model.** It knew the Output was a bearer artefact and said
  so. It never said who may hold one, how a holder demonstrates entitlement, or
  what a register's, a regulator's or an auditor's entitlement is.
- **No read binding.** It specified in detail *what* a ledger read returns and
  never once said how one is requested. No endpoint, no encoding, no media
  type, no error semantics, no signature over a response.

Every dead end in the discovery paths ran into one of those three. -03 writes
the substrate and adds no new capability.

---

## 2. What -03 changes

**Three substrate sections that did not exist.** `Delivery` states what the
pipeline returns and to whom. `Entitlement` gives every Output a sealed
Audience Set and a Reliance Horizon, so entitlement follows membership rather
than possession. `Output and Ledger Read Binding` is a wire binding: nine
operations, an RFC 9421 signing profile, signed responses that cover errors as
well as successes and carry the ledger head they were served against, and a
`404` for both not-entitled and not-found so that no endpoint is an existence
oracle.

**Two more the last round found.** `Reconciliation Request Binding` states how
a reconciliation is commissioned — the document had been imposing obligations
on "the response to the request that commissioned it" without defining that
request. `Audit Path` states who an auditor is; four requirements were
justified by what an auditor could reproduce, and the auditor was not a party
the document admitted.

**Every digest preimage and signature payload is now pinned** to a CBOR array
with a normative field order and null-substitution for absent fields — the
Claim Hash, Policy-Version Hash, Agreement Hash, Reconciliation Output and its
Sealing Signature, Partial Attestation, Per-Register Claim Projection, the
ledger entry chain, the Post-Seal Evaluation Record, the Non-Answer Statement,
Ledger Head Statement, Evaluation Sweep Statement, Sovereign Re-Notification,
Policy Parameters Document, Override Record, the read response, and both
Merkle trees with their inclusion-proof encoding. -02 left several as "the
canonical serialisation of the foregoing", which is not a preimage two
implementations can agree on. The Policy-Version Hash and the Agreement Hash
had no construction at all.

**Eight ways the protocol could be gamed, closed.** Per-principal query budget
(the shared counter was a denial of service granted by the countermeasure);
register-signed Non-Answer Statements (`register-refused` was an unattested
assertion by the party that transmitted the projection); Evaluation Sweep
Statements (a sweep never run and a sweep that found nothing were the same
observation); policy-resolved Verdict Arithmetic (the requester could otherwise
choose the operator and therefore the verdict); a fourth Requester-Binding
class, `agent-key-verified`; a bounded revocation window; an operator-signed
Override Record with a ledger-visible indicator; and Continuation ledger
entries with a type discriminator.

**One citation correction that matters to more than this draft.** Every digest
in ARP was defined by reference to "the deterministic encoding requirements of
RFC 9052". Section 9 of RFC 9052 narrows those requirements to COSE's own
Sig/Enc/MAC structures and states no map-key ordering rule, so it does not
support what was built on it. The correct citation is **Section 4.2.1 of
RFC 8949**, the Core Deterministic Encoding Requirements, which was not cited
anywhere in -02. Every use is retargeted and RFC 8949 is now normative. If any
of your drafts define a digest by pointing at RFC 9052 for deterministic
encoding, this is worth ten minutes of your time.

**Other things that were claimed and are not true.** RFC 9943 defines no
Identity Manager and no Aggregator role. The referenced agent-accountability
draft never uses the word "capsule" and freezes no conformance vectors, so an
unsourced claim about twenty-two pinned vectors is gone. `+ld+json` is not a
registered structured syntax suffix. The EU consolidated sanctions list and the
OFAC SDN list now point at the resources that publish them.

**Two removals.** Homomorphic Aggregation Mode is gone: it named no primitive,
defined no encrypted-contribution structure, had no class in the upgrade path
for one to be declared in, and the server must read every per-register verdict
in the clear anyway to verify the signature, recompute the Query Binding, check
the echoed Policy-Version Hash and apply re-typing. The privacy property it
advertised was not available under it. And the server-to-register wire binding
is now **explicitly out of scope**, with the claim withdrawn that enumerating
the Per-Register Claim Projection lets two register operators build
interoperable endpoints. The document says what that channel must achieve and
leaves the transport to the Bilateral Register Agreement. That is the honest
state of it, and it is the obvious candidate for -04.

**A Privacy Considerations section**, which a document about beneficial
ownership, sanctions and customs records did not have.

---

## 3. What is acknowledged rather than fixed

Each of these is stated plainly in the text. Push on any of them.

- **The subject has no standing.** It is not notified, cannot object, and
  cannot learn it was reconciled. Deliberate in a screening protocol, and a
  real cost.
- **The Audit Identity is broad.** Every agreement declares one, and each reads
  every Output of every reconciliation addressing its register irrespective of
  Audience Set. It is not given the Deployment Blinding Value, so it can
  establish that the disclosed policy elements are the ones the server used,
  and not that the resulting hash is correct. The stronger property needs a
  jointly appointed identity, which the text says and does not build.
- **Budget exhaustion is a suppression channel.** Any non-answering register
  makes a decisive verdict unreachable, the reason is server-observed, and the
  determinism carve-out tells the auditor to disregard the divergence. Both
  available mitigations cost more than they buy; the text says so.
- **Fork detection is opportunistic.** An operator publishing to two audiences
  at disjoint sequence numbers never emits a colliding pair. What the mechanism
  establishes is that where two heads at one sequence number are observed
  together, neither can be disowned.
- **The ledger head discloses deployment size and rate** at the notarisation
  interval. Republished per interval rather than per append, to bound that.
- **`register-unresponsive` is indistinguishable from a network failure** by
  construction. A server can still downgrade a reconciliation by asserting a
  server-observed reason. What it can no longer do is dress suppression as an
  act of the register.
- **Sweep falsifiability holds for three triggers in four.** A
  credential-revocation trigger is observable to the credential's issuer and
  the affected principal and to nobody else.

---

## 4. What I would most like each of you to attack

Not a request for a full read. Each of these is one section.

**Steven** — the RFC 8949 §4.2.1 correction above, against your own drafts. And
the read binding's central claim: that a signed read response carrying the
as-of sequence number and self-entry hash turns "nothing found" into a
statement about a named head, rather than a report of a query. That is the same
distinction as the supersession-check point on the list, and if it is worth a
shared vector class I would rather build it with you than beside you.

**Songbo** — the two-sided property, on one claim specifically: that no read
endpoint is an existence oracle, because not-entitled and not-found both return
`404`. That is falsifiable by a suite, and a positive-only suite would report
success on a violation of it.

**Tom** — the Merkle construction and the inclusion-proof encoding. Leaf input,
domain separation and proof ordering are pinned for the first time in -03 and
your CT leaf experience reaches them directly. If the framing does not match
what a real log does, that is a defect in my construction.

**Iman** — the Claim Hash is a digest over a canonical serialisation preceded
by a Deployment Blinding Value, so it is deployment-scoped by construction and
not a global identifier. I want to know whether that is compatible with joining
on a material identifier a CAID action type declares, or whether the two
approaches have to be chosen between.

---

## 5. State of the artefact

| | |
|---|---|
| Source | 4,691 lines of kramdown-rfc markdown |
| Text | 6,888 lines, 326,196 bytes |
| Source SHA-256 | `89059b9823ee3c3ae85d45bcae1da7bb5d2fe600dcaa1f84b159a916fcabb109` |
| Text SHA-256 | `715513d49b10d0e8ad1379db28a073b24cccb295153a210b3b8abe1f9fe6ac28` |
| Review | five dimensions, twenty independent adversarial passes, 0 open findings |
| idnits | 3.1.0 — 1 error, 11 warnings, 0 comments |

Built twice on unrelated toolchains — kramdown-rfc 1.7.39 under Ruby 3.2 on
Linux, and the Windows build — from the same source, to byte-identical text.
That is stated because the alternative is trusting one build.

**The one idnits error is deliberate and documented in the draft.** RFC 8785 is
a normative reference to an Informational document and is not in the downref
registry, so it needs calling out at IETF Last Call under Section 2 of
RFC 8067. The Note to the RFC Editor says exactly that, and says why the
reference cannot be demoted: the Canonical Claim is a digest over an RFC 8785
serialisation, and an implementation substituting any other canonicalisation
computes a different value for the same claim.

Of the eleven warnings: three are downrefs already in the registry (RFC 6839,
RFC 9053, RFC 9334), one is a style preference for citing BCP 14 over
RFC 2119 and RFC 8174, and seven are idnits 3.1.0 objecting to how xml2rfc lays
out appendix titles.

---

## 6. Why the pace

I am pushing this hard because people are building against it now, not later —
the agentic AI trust stack work and two other collaborations need a spec that
is stable enough to implement against. A revision that leaves the substrate
undefined costs each of them the same week of guessing, separately. That is the
whole reason -03 is substrate and not features.

It is also why I would rather have your objections on the 12th than your
agreement in October.
