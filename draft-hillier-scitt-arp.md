---
title: Attestation Reconciliation Protocol
abbrev: ARP
docname: draft-hillier-scitt-arp-03
date: 2026-08-08
category: std
submissiontype: IETF
v: 3
ipr: trust200902
area: Security
keyword:
  - Internet-Draft
  - SCITT
  - RATS
  - attestation
  - reconciliation
  - cross-jurisdictional
  - policy-version
  - agentic-AI
  - friend-or-foe

stand_alone: yes
pi: [toc, sortrefs, symrefs]

author:
 -
    ins: J. D. Hillier
    name: Joel David Hillier
    organization: Certisyn, Inc.
    email: jhillier@certisyn.com
    country: United States of America

normative:
  RFC2119:
  RFC8174:
  RFC9052:
  RFC9053:
  RFC9334:        # RATS Architecture
  RFC9421:        # HTTP Message Signatures
  RFC8785:        # JSON Canonicalization Scheme (JCS)
  RFC9943:        # SCITT Architecture (was I-D.ietf-scitt-architecture)
  RFC9942:        # COSE Receipts (was I-D.ietf-cose-merkle-tree-proofs)
  I-D.ietf-scitt-scrapi:   # normative: {{scrapi-binding}} imposes MUSTs on its endpoints
  UAX15:
    title: "Unicode Standard Annex #15: Unicode Normalization Forms"
    target: https://www.unicode.org/reports/tr15/
    author:
      - org: The Unicode Consortium
    date: 2023

informative:
  RFC8259:        # JSON
  RFC6350:        # vCard 4.0
  RFC8615:        # Well-Known URIs
  BODS:
    title: Beneficial Ownership Data Standard
    target: https://standard.openownership.org/
    author:
      - org: Open Ownership
    date: 2024
  W3C-ORG:
    title: "The Organization Ontology"
    target: https://www.w3.org/TR/vocab-org/
    author:
      - org: World Wide Web Consortium
    date: 2014
  WCO-DM:
    title: WCO Data Model
    target: https://www.wcoomd.org/en/topics/facilitation/instrument-and-tools/tools/data-model.aspx
    author:
      - org: World Customs Organization
    date: 2024
  UNCEFACT:
    title: "UN/CEFACT Core Component Library and XML Schemas"
    target: https://unece.org/trade/uncefact
    author:
      - org: United Nations Economic Commission for Europe
    date: 2024
  OFAC-SDN:
    title: "Specially Designated Nationals and Blocked Persons List"
    target: https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists
    author:
      - org: United States Department of the Treasury, Office of Foreign Assets Control
    date: 2026
  EU-CFSP:
    title: "EU Consolidated Financial Sanctions List"
    target: https://www.sanctionsmap.eu/
    author:
      - org: European Union
    date: 2026
  RFC8067:        # Updating When Standards Track Documents May Refer Normatively to Documents at a Lower Level
  I-D.mih-sato-agent-accountability-composition:
  I-D.mih-sokolov-scitt-payload-binding:
  I-D.meunier-webbotauth-httpsig-protocol:
  I-D.meunier-webbotauth-httpsig-directory:
  I-D.meunier-webbotauth-registry:
  FIPS203:
    title: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)
    seriesinfo:
      NIST: FIPS 203
    target: https://csrc.nist.gov/publications/detail/fips/203/final
    date: 2024
  FIPS204:
    title: Module-Lattice-Based Digital Signature Standard (ML-DSA)
    seriesinfo:
      NIST: FIPS 204
    target: https://csrc.nist.gov/publications/detail/fips/204/final
    date: 2024
  W3C-VC-DM-2.0:
    title: Verifiable Credentials Data Model 2.0
    target: https://www.w3.org/TR/vc-data-model-2.0/
    date: 2025

--- abstract

This document specifies the Attestation Reconciliation Protocol (ARP), a
deterministic, bilateral, minimum-disclosure mechanism for reconciling
verification claims against a plurality of sovereign authoritative registers
without raw register records leaving their data-residency jurisdiction. ARP
extends the SCITT (Supply Chain Integrity, Transparency, and Trust)
architecture to cross-sovereign claim reconciliation. A reconciliation server
canonicalises a structured claim, binds the identity of the requesting
principal -- including, where the requester is an autonomous agent, a
friend-or-foe determination of that agent's verifiable principal binding --
projects the claim through register-specific controlled projection functions
producing the nearest permitted ancestor predicate supported by each
addressed register, transmits register-specific ciphertexts, receives partial
attestations whose payload discloses only a verdict and an optional divergence
axis, aggregates the partial attestations through either homomorphic or
hash-linkage aggregation, and seals the resulting reconciliation output against
a policy-version hash. An append-only cross-jurisdictional settlement-layer
ledger records only hashes, with no content. The protocol supports retroactive
re-evaluation of historical reconciliations under updated pattern libraries or
policy versions without bilateral renegotiation, and a
cryptographic-primitive-upgrade path including post-quantum primitives. This
revision adds a normative binding to the SCITT Reference APIs, register
data-format profiles for beneficial-ownership, corporate-registry, customs and
consolidated-sanctions formats, and a source-data version binding that makes a
change in a historical verdict attributable to a change in policy or to a change
in the underlying published corpus.

--- middle

# Note to the RFC Editor

RFC EDITOR: please remove this section before publication.

This document is Standards Track and makes a normative reference to RFC 8785,
which is Informational. This constitutes a downref under {{RFC8067}}. The reference is deliberately normative: ARP's
Canonical Claim is a digest over an RFC 8785 serialisation preceded by Unicode
Normalization Form C, and the subject digest of {{composition}} is a digest over an
unmodified RFC 8785 serialisation. Neither can be computed without RFC 8785,
and an implementation that substituted any other canonicalisation would
compute a different value for the same claim. The
reference is therefore load-bearing for interoperability and cannot be
demoted to informative. This is called out here so that the downref can be
noted in the IETF Last Call announcement per Section 1 of {{RFC8067}}.

This document also makes a normative reference to
{{I-D.ietf-scitt-scrapi}}, a work in progress. {{scrapi-binding}} imposes
requirements expressed in terms of that document's endpoints, status codes and
media types, and an implementation cannot satisfy them without it, so the
reference cannot be informative. RFC EDITOR: this document should not be
published before that draft, and the reference should be updated to the
resulting RFC number.

# Introduction

Sovereign authoritative registers record facts that are treated as conclusive
within their jurisdiction. Examples include beneficial-ownership registers
(such as the United States FinCEN Beneficial Ownership Secure System, the
United Kingdom People with Significant Control register, and the European
Union beneficial-ownership registers under the Anti-Money-Laundering
Directives), corporate registries, consolidated sanctions lists,
export-control registers, foreign-ownership-and-control-or-influence
registers, maritime vessel registrations, flag-state registers, aviation
registrations, land-title registries, customs declarations, and multilateral
biometric registers.

Institutional decision-makers -- including export-control compliance officers,
anti-money-laundering review functions, foreign-investment screening review
functions, sanctions-screening operators, multilateral aid distribution
authorities, and platform-owned verification infrastructure -- routinely
require reliance on facts recorded across two or more sovereign registers
simultaneously.

Cross-sovereign reliance today faces four structural problems, which this
protocol is designed to address in combination:

1. **Raw-record disclosure.** Existing approaches require the raw register
   record either to leave its data-residency jurisdiction or to be re-disclosed
   in plaintext to a relying party in another jurisdiction. Sovereign registers
   under data-protection regimes are jurisdictionally constrained against such
   re-disclosure.

2. **Non-reconcilable register outputs.** Each sovereign register exposes a
   different schema, a different signing chain, a different verdict semantic,
   and a different statutory access regime. A relying party that requires a
   deterministic combined verdict over n sovereign registers therefore faces
   n parallel verification problems.

3. **Non-auditable settlement.** Cross-sovereign reliance, where it occurs at
   all, occurs without a settlement-layer audit trail consumable by sovereign
   regulators.

4. **Unverifiable requester identity in an agentic setting.** Cross-sovereign
   reliance is increasingly initiated not by an authenticated human operator
   but by an autonomous software agent acting on behalf of a principal. Where
   the agent's binding to a real, authenticated principal cannot be verified,
   the reconciliation is performed for an unknown or impersonated party, and
   the settlement record attributes reliance to no accountable principal. An
   agent whose principal binding cannot be verified is treated as hostile
   (zero-trust); the normative rules are in {{terminology}} and
   {{agent-iff-integrity}}.

This document specifies ARP, a protocol that addresses all four deficiencies
in combination, and is layered atop the SCITT architecture {{RFC9943}} and the
RATS architecture {{RFC9334}}.

The fourth deficiency is not hypothetical. Where an autonomous agent can act,
its containment assumptions may not hold at run time, and a binding between an
agent's claimed authority and its actual conduct that is established only after
the fact is not a control. The binding must be checkable at the moment of
action.

ARP is designed for that moment. Forensic reconstruction establishes what an
agent did after a consequence has occurred; ARP reconciles an agent's claimed
authority and principal binding against authoritative registers while the
action can still be refused. A reconciliation that yields a non-decisive or
divergent verdict is a control input available before the action commits, not
an audit finding available after. This document treats real-time reconciliation
of claimed-versus-actual conduct as a first-class property of accountable
autonomous action.

# Conventions and Definitions {#terminology}

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in BCP 14 {{RFC2119}} {{RFC8174}}
when, and only when, they appear in all capitals, as shown here.

The following terms are defined for use throughout this document:

Sovereign Register:
: An authoritative data store maintained by or on behalf of a sovereign and
  treated as conclusive within that sovereign's jurisdiction for the
  predicates the register is empowered to record.

Register Operator:
: The entity that operates the Sovereign Register and is contractually
  empowered to bind the register's attestations.

Bilateral Register Agreement:
: A negotiated contractual instrument between the operator of the
  reconciliation server and a Register Operator, declaring the
  permitted-predicate set, supported cryptographic primitives, supported
  aggregation capability, statutory-regulator-access scope, and
  cryptographic-primitive-upgrade path. Each Bilateral Register Agreement
  carries an Agreement Hash committing to its canonicalised content.

Requesting Principal:
: The accountable party on whose behalf a reconciliation is performed. A
  Requesting Principal is either an authenticated human or institutional
  operator, or an autonomous agent carrying a Verified Principal Credential
  that binds it to such an operator.

Requesting Agent:
: An autonomous software agent that initiates a reconciliation. A Requesting
  Agent is FRIENDLY when it carries a verifiable identity -- a request signed
  under HTTP Message Signatures {{RFC9421}} per Web Bot Auth
  {{I-D.meunier-webbotauth-httpsig-protocol}}, a genuinely verified declared bot,
  or a Verified Principal Credential -- and ENEMY when its principal binding is
  absent or unverifiable. Anything unverifiable is treated as ENEMY.

Verified Principal Credential:
: A cryptographic credential asserting that a named, authenticated principal
  stands behind a request, verifiable without contacting the credential issuer
  in the reconciliation hot path. A Verified Principal Credential MAY be
  carried in any COSE-enveloped structure binding the claim, its evidentiary
  provenance, and the principal's credential, or in any equivalent
  verifiable-credential form {{W3C-VC-DM-2.0}}.

Agent Friend-or-Foe (IFF) Determination:
: The deterministic classification of a Requesting Agent as FRIENDLY or ENEMY,
  computed from the presence and cryptographic validity of a verifiable agent
  identity and, where required by policy, a Verified Principal Credential. The
  determination is recorded in the Requester-Binding field and committed to the
  Policy-Version Hash.

Canonical Claim:
: A deterministic structured representation of a verification claim,
  comprising at least a subject identifier, a predicate, an attested value,
  an applicable-regimes set, and an evidentiary provenance manifest.
  Canonicalisation is performed in the following order, which is normative
  because the operations do not commute:

  1. Unicode Normalization Form C {{UAX15}} is applied to every string value
     and to every object member name.
  2. Object member names are sorted by UTF-16 code unit, as specified in
     Section 3.2.3 of {{RFC8785}}.
  3. Declared array order is preserved.
  4. Numbers are rendered as specified in Section 3.2.2.3 of {{RFC8785}}.
  5. A member whose value is absent is omitted, rather than serialised with a
     null placeholder.

  Steps 1 and 2 are order-dependent and observably so: for an object carrying
  the member names "A" followed by COMBINING RING ABOVE (U+0041 U+030A) and
  "B", normalising before sorting and sorting before normalising yield
  different serialisations and therefore different Claim Hashes. This
  specification requires normalisation first.

  The member-sort code unit is normative. An implementation that sorts by
  Unicode code point rather than by UTF-16 code unit produces a different Claim
  Hash for any object carrying a member name outside the Basic Multilingual
  Plane. Implementation experience against a published conformance corpus
  measured this as a divergence on one vector in twenty-two. The two orderings
  are not interchangeable, and this specification pins the UTF-16 reading.

  This construction is NOT the construction defined in {{composition}} for
  `subject_digest`. The two MUST NOT be substituted for one another; see
  {{construction-distinctness}}.

Predicate Taxonomy:
: A controlled hierarchical classification of predicates that may be the
  subject of reconciliation, enabling taxonomic prefix match in projection.
  The taxonomy includes an `agent:` branch whose predicates reconcile the
  verifiability of an agent's binding to a principal (for example
  `agent:principal-binding-verifiable` and `agent:credential-attested`).

Per-Register Claim Projection:
: The narrowest structured query sufficient to elicit the required Partial
  Attestation under a register's Bilateral Register Agreement, computed by
  the controlled projection function as the nearest ancestor of the Canonical
  Claim Predicate that is a member of the register's permitted-predicate set.
  Where the taxonomy admits more than one such ancestor, the projection MUST
  fail rather than choose.

Partial Attestation:
: A cryptographically signed output produced by a Sovereign Register in
  response to a Per-Register Claim Projection. The Partial Attestation
  payload SHALL disclose, of the subject, only a Reconciliation-Verdict field
  and an OPTIONAL Divergence-Axis field; it SHALL NOT disclose any register
  record. Fields denoting state rather than the subject -- the Freshness
  Timestamp, and the Source-Data Version Identifier of {{source-versioning}} --
  are enumerated in {{partial-attestation}}.

Combined Verdict:
: The single verdict value produced by aggregating the Reconciliation-Verdict
  fields of the Per-Register Result Set of {{reconciliation-output}} under the
  Verdict Arithmetic declared in the Applicable-Regimes Set. Its values are
  match, no-match, partial-match and indeterminate. The decisive values are
  match and no-match.

Reconciliation Hash:
: The SHA-256 digest over the deterministically encoded CBOR serialisation of a
  Reconciliation Output excluding its Sealing Signature and Sealing-Key
  Identifier, as specified in {{reconciliation-output}}.

Divergence Axis:
: A controlled descriptor identifying a structural qualification on a verdict.
  Most identify the reason for a non-match; those recorded by the reconciliation
  server may qualify a verdict of any value. The controlled set is the registry of {{iana}}, which at the time of writing
  comprises identity-mismatch,
  jurisdictional-scope-mismatch, temporal-mismatch,
  ownership-threshold-mismatch, sanctions-list-match, register-record-absent,
  claim-predicate-unsupported,
  claim-projection-narrowed-beyond-attestation-scope,
  agent-principal-unverifiable, agent-credential-absent,
  agent-impersonation-suspected, agent-action-scope-divergence (the
  authorised scope attested for an agent action and the actual conduct
  attested for it do not reconcile), source-version-skew, register-threshold-divergence (two
  registers answered the same predicate under different declared interest
  thresholds, per {{profile-bods}}), declared-not-determined (the register
  could answer only over a declared fact where the claim ranged over a
  determined one, per {{profile-customs}}), and freshness-stale. Divergence
  Axes recorded by the reconciliation server rather than by a register --
  freshness-stale, source-version-skew, register-threshold-divergence and
  declared-not-determined -- are carried in the Reconciliation Output, not
  in the register's signed Partial-Attestation payload.

Source-Data Version Identifier:
: An identifier denoting the state of a published corpus, external to both the
  Bilateral Register Agreement and the Policy Version, against which a register
  evaluated a Projected Predicate. A consolidated sanctions list is the
  characteristic case. Its purpose is attribution: without it, a change in a
  historical Combined Verdict cannot be attributed to a change in policy state
  rather than to a change in the underlying corpus. Requirements are in
  {{source-versioning}}.

Post-Seal Evaluation Qualifier:
: A controlled descriptor identifying a condition arising after a Reconciliation
  Output has been sealed, carried in a Post-Seal Evaluation Record per
  {{post-seal}} rather than in the Output. The values are those of the registry in
  {{iana}}, at the time of writing notarisation-incomplete and
  attribution-indeterminate. A Post-Seal Evaluation
  Qualifier is not a Divergence Axis: a Divergence Axis qualifies a verdict, and
  a Post-Seal Evaluation Qualifier qualifies an operation on an Output whose
  verdict is already fixed.

Threshold-Sensitive Predicate:
: A Predicate whose truth depends on an interest threshold, so that two
  registers evaluating it under different declared thresholds are not answering
  the same question. A profile registered under {{format-profiles}} MUST state
  which of its predicates are threshold-sensitive.

Source Class:
: A partition of the Addressed-Registers Identifier Set declared in the
  Applicable-Regimes Set, over which source-class-quorum is evaluated per
  {{verdict-arithmetic}}.

Sovereign Re-Notification:
: A notification emitted through the Regulator Portal to each regulator whose
  statutory scope covers a reconciliation whose historical Combined Verdict has
  materially changed, and published as a Continuation entry on the
  Settlement-Layer Ledger so that a relying party that acted on the superseded
  Output can discover the change.

Reconciliation Nonce:
: A value of at least 128 bits drawn from a cryptographically secure random
  source, unique to one Per-Register Claim Projection and therefore to one
  register within one reconciliation. It is never reused. Two registers
  addressed in the same reconciliation receive different nonces, so their Query
  Bindings differ even where the Projected Predicate and Subject Reference are
  identical, and an attestation elicited from one register cannot be presented
  as an answer from another.

Source-Version Skew:
: The condition, recorded as source-version-skew, in which two Partial
  Attestations answer the same Projected Predicate against different states of
  the same published corpus. Both are within their freshness windows; the skew
  is in the corpus, not in the attestations. It is not a disagreement, and an
  implementation MUST NOT treat it as one.

Attribution Indeterminate:
: The Post-Seal Evaluation Qualifier, recorded as attribution-indeterminate, in
  which a Retroactive Evaluation cannot determine whether a material change in a
  historical Combined Verdict arose from a change in policy state or from a
  change in Source-Data Version. It is a statement about the evaluation, not
  about any register's answer.

Reconciliation Output:
: A data structure aggregating Partial Attestations from a single
  reconciliation event, sealed against a Policy-Version Hash.

Verdict Arithmetic:
: The operator governing how per-register verdicts combine into the Combined
  Verdict, specified in {{verdict-arithmetic}}. The controlled set comprises
  conjunction, disjunction, threshold-count and source-class-quorum.

Homomorphic Aggregation:
: A cryptographic aggregation of Partial Attestations under a homomorphic
  primitive permitting verdict combination without decommitment of
  intermediate per-register outputs.

Hash-Linkage Aggregation:
: An aggregation of Partial Attestations in which the per-register
  attestations are canonical-hashed, ordered, committed to a Merkle tree,
  and emitted with a Merkle root and a per-register verdict band. The Merkle
  commitment and its inclusion proofs MAY be encoded as COSE Receipts
  {{RFC9942}}.

Policy-Version Hash:
: A cryptographic commitment to the canonical verification-policy state in
  force at the moment of reconciliation, including reconciliation rules,
  threshold parameters, pattern-library version, applicable-regimes
  precedence, verdict-arithmetic selection, the Agent-IFF policy in force,
  the Requester-Binding, and the Bilateral-Register-Agreement Hashes of the
  addressed registers.

Settlement-Layer Ledger:
: An append-only cross-jurisdictional log retaining only hashes of
  reconciliations, with no content-bearing fields. Each entry comprises a
  sequence number, the reconciliation hash, the policy-version hash, the
  addressed-registers identifier set, an aggregation-method descriptor, an
  optional Merkle root, a requester-binding-class descriptor, a timestamp, a
  prior-entry hash, a self-entry hash, and an OPTIONAL
  source-reconciliation-output identifier.

# Architecture {#architecture}

ARP comprises sixteen subsystems arranged as a deterministic pipeline:

1. Canonical Claim Ingestion
2. Requester Identity Binding and Agent Friend-or-Foe Gate
3. Adversarial Pre-Transmission Test
4. Per-Register Projection Function, under the profile of {{format-profiles}}
   declared in the Bilateral Register Agreement
5. Per-Register Encryption
6. Partial-Attestation Reception, including Source-Data Version Binding
7. Non-Answer Resolution
8. Verdict Re-Typing
9. Aggregation under the Verdict Arithmetic (Homomorphic or Hash-Linkage)
10. Policy-Version-Hash Sealing
11. Settlement-Layer Ledger Write
12. Notarisation under {{scrapi-binding}}, where performed
13. Regulator Portal
14. Retroactive Evaluation
15. Post-Seal Evaluation Recording
16. Cryptographic-Primitive-Upgrade Path

Given an identical Canonical Claim, an identical Requester-Binding, an
identical Addressed-Registers Identifier Set, identical
Bilateral-Register-Agreement Hashes for the addressed registers, an identical
Pattern-Library Version Identifier, and an identical Policy-Version
Identifier, the system MUST produce bit-for-bit identical Reconciliation
Outputs, and identical Claim Hash, Reconciliation Hash and Policy-Version Hash
values in the corresponding Settlement-Layer Ledger entries. The per-event
fields of a Ledger entry -- Entry Sequence Number, Reconciliation Timestamp,
Prior-Entry Hash and Self-Entry Hash -- are position-dependent by construction
and are outside this requirement. The Freshness Timestamps of the constituent
Partial Attestations, and any Source-Data Version Identifiers they carry per
{{source-versioning}}, are likewise outside it: both denote state external to
the enumerated inputs. Two reconciliations agreeing on every enumerated input
but differing in Source-Data Version are not required to be bit-identical, and
an implementation MUST NOT treat such a difference as a determinism failure.

## Canonical Claim Ingestion

A Canonical Claim comprises:

- Subject Identifier
- Predicate (drawn from the controlled Predicate Taxonomy)
- Attested Value (in the canonical type for the Predicate)
- Applicable-Regimes Set
- Evidentiary Provenance Manifest
- Claim Timestamp (RFC 3339 UTC)
- Claim Hash (SHA-256 over the canonical serialisation together with the
  Deployment Blinding Value of {{sealing}})

Two claims whose canonical field values are identical MUST produce the same
canonical form, and the same Claim Hash within one deployment. Across
deployments the Claim Hash differs by the Deployment Blinding Value while the
canonical form does not. Declared array order is significant;
claims differing only in declared array order are distinct claims. The Claim Hash is the index on the
Settlement-Layer Ledger and the key for retroactive re-evaluation.

The Evidentiary Provenance Manifest MAY be carried in any COSE-enveloped
evidence structure; the container form is an interop convenience and does not
alter the Claim Hash,
which is computed over the canonical claim fields together with the Deployment
Blinding Value of {{sealing}} and over nothing else.

## Requester Identity Binding and Agent Friend-or-Foe Gate

Before the Adversarial Pre-Transmission Test, the reconciliation server MUST
establish the identity of the Requesting Principal and record it in a
Requester-Binding field. The Requester-Binding comprises a requester-binding
class (one of human-operator, agent-verified, or agent-unverified), the
identifier of the accountable principal where known, and a reference to the
verification method used.

Where the requester is an autonomous agent, the server MUST perform an Agent
Friend-or-Foe (IFF) Determination. An agent is classified FRIENDLY only where
at least one verifiable identity is present and cryptographically valid: a
request signed under HTTP Message Signatures {{RFC9421}} with a key resolvable
through a Web Bot Auth signature-agent card
{{I-D.meunier-webbotauth-registry}}, advertised via the Signature-Agent header
{{I-D.meunier-webbotauth-httpsig-protocol}} and resolved through the HTTP
Message Signatures directory it names
{{I-D.meunier-webbotauth-httpsig-directory}}, a genuinely verified declared
bot, or a Verified Principal Credential. An agent presenting no such identity,
or an identity that fails verification, MUST be classified ENEMY.

The Agent-IFF policy in force declares, per predicate class, whether an ENEMY
requester is refused outright, permitted only for non-decisive advisory
reconciliation, or permitted with the requester-binding class recorded as
agent-unverified. The server MUST NOT silently upgrade an ENEMY requester to
FRIENDLY. The Requester-Binding and the Agent-IFF policy identifier are
committed to the Policy-Version Hash so that the settlement record is
attributable to a determined requester class.

## Adversarial Pre-Transmission Test

Before any Per-Register Claim Projection is produced, the Adversarial
Pre-Transmission Test Subsystem applies the current Pattern Library to the
Canonical Claim. The Pattern Library enumerates structural evasion patterns
against the projection and aggregation mechanisms of this protocol, including
projection-narrowing-evasion,
predicate-substitution-evasion, attested-value-bracketing-evasion,
addressed-register-cherry-picking, agreement-staleness-injection,
pattern-library-version-pinning, and agent-principal-spoofing (an unverifiable
agent asserting a principal binding it does not hold).

The Subsystem emits either a Pass result or a Remediation Advisory. A
Remediation Advisory comprises the identifiers of the patterns that matched and
the narrowing or substitution each concerns; it is returned to the requester, no
projection is transmitted, and no Reconciliation Output is produced.

The Per-Register Encryption Subsystem MUST architecturally withhold external
transmission until a Pass result has been emitted or until an authorised
operator has explicitly overridden the outcome. An override MUST be recorded in
the Reconciliation Output as an Override Record naming the patterns that matched
and the authorising operator identity, and is thereby covered by the Sealing
Signature. An override that left no artefact would be indistinguishable from a
Pass to every external party, which would make the only manual bypass of the
protocol's own adversarial gate invisible to the regulators that gate exists to
serve.

## Per-Register Projection Function {#projection}

For each addressed register, the controlled projection function MUST inspect
the Canonical Claim against the permitted-predicate set declared in the
Bilateral Register Agreement. Where the Canonical Claim's Predicate is
directly a member of the permitted-predicate set, the Projected Predicate
equals the Canonical Claim Predicate.

Where it is not, the projection function resolves the Predicate through
taxonomic prefix match: walking the Predicate Taxonomy upward from the
Canonical Claim Predicate until reaching a Predicate that is a member of the
permitted-predicate set. Where the walk reaches more than one such Predicate at
the same taxonomic distance, the projection MUST fail with
`projection-ambiguous` rather than choose between them. Where the walk reaches
the taxonomy root without finding one, the projection MUST fail with
`projection-unsupported`. The narrowing operation MUST be recorded in the
Narrowed-From field of the Per-Register Claim Projection.

A Per-Register Claim Projection comprises:

- Reconciliation Identifier
- Register Identifier
- Projected Predicate
- Subject Reference, in the form the addressed register's Bilateral Register
  Agreement declares
- Attested Value, where the Projected Predicate takes one
- Narrowed-From, absent where the Projected Predicate equals the Canonical
  Claim Predicate
- Bilateral-Register-Agreement Hash
- Policy-Version Hash
- Freshness Window, as declared in the Bilateral Register Agreement
- Reconciliation Nonce
- Profile Parameter Set, being the values the Bilateral Register Agreement
  declared under {{format-profiles}} that the register is to apply

This is the only structure a sovereign register receives, and it is enumerated
here so that two register operators can build interoperable endpoints. The
register does not receive the Canonical Claim, the Addressed-Registers
Identifier Set, or any other register's projection.

The register echoes the Policy-Version Hash in its Partial Attestation; it does
not compute it, and it is not required to be able to. The reconciliation server
MUST send the same Policy-Version Hash to every addressed register in one
reconciliation, and MUST verify on reception that each Partial Attestation
echoes it. A mismatch MUST be treated as a refusal by that register and recorded
under {{no-answer}}. Without this the per-register signatures over the
Policy-Version Hash -- the only independent corroboration of it -- would be
discarded at aggregation, and a server could address different registers under
different policy versions undetectably.

## Register Data-Format Profiles {#format-profiles}

A Bilateral Register Agreement MUST declare the data format in which the
addressed register expresses the facts the permitted-predicate set ranges over.
The projection function of {{projection}} operates on predicates, not on
records; a format profile is what lets an implementer determine which predicates
a given register can actually answer, and what a narrowing means against that
register's own structure.

A profile is a property of a data format, not of a register. It states, for the
format it covers, how a permitted predicate is expressed and what the Predicate
Taxonomy's parent relation corresponds to in that format. Parameters that vary
between registers using the same format -- interest thresholds, maximum chain
depths, the set of named lists and the identifiers a register uses for their
states -- are not properties of the profile and MUST be declared in the
Bilateral Register Agreement. A profile MUST enumerate the parameters a Bilateral Register Agreement declaring
it is required to supply, and MUST state which of its predicates are
threshold-sensitive per {{terminology}}, on which the third re-typing ground of
{{verdict-retyping}} turns.

Without that split a single registered identifier would carry facts that differ
between registers, and two registers using the same format under different
thresholds could not both declare it. A profile MUST NOT introduce a means of transporting register records; profiles
constrain predicate expression only.

The vocabulary documents a profile names are informative to this document and
normative to an implementation of that profile: an implementation cannot
evaluate a projection expressed in a vocabulary without it. A profile MUST pin
the dated version of each vocabulary it names.

This document defines four profiles, with the identifiers registered in
{{iana}}:

- `arp-profile-bods` ({{profile-bods}})
- `arp-profile-corporate-org` ({{profile-corporate}})
- `arp-profile-customs-wco` ({{profile-customs}})
- `arp-profile-sanctions-consolidated` ({{profile-sanctions}})

Identifiers beginning `x-` are reserved for bilateral use and MUST NOT be
registered. A Bilateral Register Agreement MAY declare one.

### Beneficial ownership: BODS {#profile-bods}

For registers expressing beneficial ownership as {{BODS}} records, the
permitted-predicate set is expressed over relationship records -- termed
ownership-or-control statements before BODS 0.4 -- reachable from a declared
subject entity. This profile is written against BODS 0.4.

Taxonomic narrowing corresponds to reducing the depth of the ownership chain a
predicate ranges over. A relying party's question is characteristically about
ultimate beneficial ownership -- the transitive closure -- while a register may
be able to answer only a bounded-depth predicate over direct or
once-removed interests. The parent of a predicate at depth n is the corresponding predicate at depth
n-1. The direct-interest predicate is the root of this profile's branch of the
Predicate Taxonomy, and the walk of {{projection}} fails as
`projection-unsupported` on reaching it, as it does at the taxonomy root.

A Bilateral Register Agreement declaring `arp-profile-bods` MUST supply the
maximum chain depth over which the register's permitted predicates are
evaluated. Where the Canonical Claim ranges
over the transitive closure and the register's declared maximum depth is finite,
the projection is a narrowing and MUST be recorded in Narrowed-From. An
implementation MUST NOT treat a bounded-depth `no-match` as a
transitive-closure `no-match`. The rule is stated in {{verdict-retyping}} and
applies to that register's contribution, not to the Combined Verdict: a
`no-match` returned at bounded depth against a closure claim is re-typed to
`indeterminate` before aggregation, and the Verdict Arithmetic then proceeds
unchanged. A `match` found at any depth does establish the existential closure
predicate and is not re-typed.

The depth at which the register answered is reported in the Applied-Parameter
Set of its Partial Attestation and MUST be carried into the Projection Record of
{{reconciliation-output}}. A register MAY answer at a shallower depth than the
declared maximum; the declared maximum is therefore not a substitute for the
applied value, and re-typing under {{verdict-retyping}} turns on the applied
value.

Interest thresholds -- the percentage at which an interest becomes reportable --
vary by jurisdiction and are properties of the register, not of the claim or of
the format. A Bilateral Register Agreement declaring `arp-profile-bods` MUST
supply the threshold its permitted predicates assume. Two
registers answering the same predicate under different thresholds are not
answering the same question. The reconciliation server MUST add
`register-threshold-divergence` to the Server-Recorded Divergence-Axis Set
wherever the Reconciliation Output combines registers whose declared thresholds
differ, irrespective of the verdicts they returned.

### Corporate registries: vCard and the Organization Ontology {#profile-corporate}

For registers expressing legal-entity and organisational structure, a profile
MAY declare {{RFC6350}} vCard properties or {{W3C-ORG}} classes and properties
as the vocabulary in which permitted predicates are expressed.

A profile MUST declare exactly one parent relation for each branch of its
predicate space, and MUST partition that space so the branches do not overlap.
Declaring two relations applicable to one predicate would make the taxonomic
walk of {{projection}} reach two predicates at equal distance, which that
section requires to fail as `projection-ambiguous`.

Where {{W3C-ORG}} is used, `org:subOrganizationOf` is the parent relation for
the organisational-structure branch, and `org:hasSite` for the branch of
predicates ranging over establishment or place of business.

Neither vocabulary asserts the legal effect of a recorded fact. {{W3C-ORG}} does
carry a notion of legal recognition -- `org:FormalOrganization` denotes an
organisation recognised in legal jurisdictions, and `org:identifier` a company
registration number -- but recognition is not determination. A predicate
expressed in these terms is a predicate about a register's recorded
representation of an entity, not about the entity's status in law, and a profile
MUST NOT be read as asserting the latter.

### Customs and transport: UN/CEFACT and the WCO Data Model {#profile-customs}

For customs declarations and transport registers, a profile MAY declare
{{UNCEFACT}} core components or {{WCO-DM}} classes as the vocabulary for
permitted predicates.

Both express declaration-side and authority-side facts, and telling them apart
is the purpose of this profile rather than a property of the vocabularies. The
WCO Data Model's Declaration Response and its Licence, Permit, Certificate and
Other packages record authority determinations, as does UN/CEFACT's eCERT for
sanitary and phytosanitary certification; the goods and cargo declaration
classes in both record what was declared to an authority.

A Bilateral Register Agreement declaring `arp-profile-customs-wco` MUST supply,
for each permitted predicate, whether it ranges over a declared fact or over a
determined one. Where a relying party's Canonical Claim ranges over a determined
fact and the register can answer only over a declared one, that is a narrowing
and MUST be recorded in Narrowed-From. The reconciliation server MUST derive the Divergence
Axis `declared-not-determined` from the Narrowed-From field and add it to the
Server-Recorded Divergence-Axis Set of {{reconciliation-output}} whenever the
narrowing occurred, whether or not it changed the Combined Verdict; the
corresponding contribution is re-typed under {{verdict-retyping}}. The register
cannot record it: the register never sees the Canonical Claim, and the Combined
Verdict does not exist until every Partial Attestation has been received.

### Sanctions: consolidated list formats {#profile-sanctions}

For registers expressing designation status by reference to a consolidated list
-- {{OFAC-SDN}}, {{EU-CFSP}} or equivalent -- the permitted-predicate set is
expressed over designation of a subject entity on a named list.

Consolidated lists are republished on no fixed schedule -- OFAC states there is
no predetermined timetable, and the EU list is updated as amending regulations
are adopted -- and are distributed either as full republications or as delta
updates against a prior state. That the cadence is event-driven strengthens the
requirement below rather than weakening it: a relying party cannot infer list
state from the clock. A designation verdict is meaningful only relative to the
list state that produced it, and this has a
consequence the rest of this document depends on: without it, a change in a
historical Combined Verdict cannot be attributed to a policy change rather than
to a list change. Accordingly the requirements of {{source-versioning}} apply.

A Bilateral Register Agreement declaring `arp-profile-sanctions-consolidated`
MUST supply the set of lists the register consults and, for each, the identifier
by which the register expresses that list's state. Where the register publishes both a full
list and deltas, the identifier MUST denote the resulting state and not the
delta applied to reach it.

## Source-Data Version Binding {#source-versioning}

Where a register's answer depends on a source data state that changes
independently of the Bilateral Register Agreement and of the Policy Version --
a consolidated sanctions list being the characteristic case -- the Partial
Attestation MUST carry a Source-Data Version Identifier Set: one identifier for each source consulted
in evaluating the Projected Predicate. Each identifier is a tuple of the list name as declared in the Bilateral
Register Agreement and the state identifier the LIST PUBLISHER assigns to that
state -- a published version token, or a digest of the published corpus where
the publisher assigns none -- rather than any value of the register's own
devising. A register-chosen opaque string would be an arbitrary-bandwidth
channel from register to relying party, carried under signature into a sealed
and ledgered artefact, and the rule that differing identifiers MUST NOT be read
as disagreement would normalise it. The reconciliation server MUST reject an
identifier that is not drawn from the publisher's own state sequence, under
{{no-answer}} with the reason `attestation-unverifiable`. The tuple form is what
lets identifiers issued by one register over different lists be distinguished, so that identifiers issued by one register over
different lists cannot collide and a register consulting several lists can
denote the state of each.

The Source-Data Version Identifier Set MUST be carried in the
`arp-source-data-version` COSE header parameter of the Partial Attestation's
protected header, and is thereby covered by the Partial-Attestation signature.
It MUST be carried into the Per-Register Result Set of
{{reconciliation-output}} for each addressed register that supplied one, and is
thereby covered by the Sealing Signature.

A register MUST evaluate every Projected Predicate over a given list against the
state the corresponding member of its declared Source-Data Version Identifier
Set denotes, and MUST use the same identifier for every Partial Attestation it
issues over that list until it adopts a new state. Without this the identifier would vary per subject and become
a disclosure channel.

Given that requirement this does not weaken minimum disclosure: a list-state
identifier is a property of a published corpus rather than a register record, it
discloses which published state was consulted and nothing about the subject
entity, and it is identical across every Partial Attestation the register issues
over that list regardless of verdict.

Retroactive Evaluation depends on this. On re-evaluation under an updated
Pattern Library or Policy Version, an implementation MUST distinguish a material
change in a historical Combined Verdict arising from the change in policy state
from one arising from a change in Source-Data Version. Both MUST trigger
Sovereign Re-Notification where material, and the notification MUST state which
of the two occurred. Where an implementation cannot distinguish them, it MUST
emit a Post-Seal Evaluation Record carrying `attribution-indeterminate` per
{{post-seal}} rather than attribute the change to policy.

An implementation MUST NOT infer that two Partial Attestations whose
Source-Data Version Identifier Sets differ for a list they have in common
disagree. They may be answers to the
same predicate against different states of the same corpus. The reconciliation
server MUST record this as `source-version-skew`, which is distinct from
`freshness-stale`: a skewed attestation is within its freshness window and is
retained and combined, whereas a stale one falls outside that window and is
rejected under {{replay-defence}}.

## Per-Register Encryption

Each Per-Register Claim Projection MUST be encrypted under the addressed
register's public-key material declared in the Bilateral Register Agreement.
The Reconciliation Nonce MUST be transmitted in the clear alongside the
ciphertext, and the encryption operation MUST bind the
Bilateral-Register-Agreement Hash and that nonce into the ciphertext as
authenticated additional data, such that a register attempting to decrypt under
a stale Bilateral-Register-Agreement Hash, or with a nonce other than the one
the ciphertext was sealed against, fails at the authenticated-additional-data
verification step. The register MUST verify that the nonce so bound equals the
Reconciliation Nonce field of the decrypted projection.

The nonce travels in the clear because authenticated additional data is an input
to the decryption operation and cannot be recovered from the plaintext that
operation produces. It discloses nothing: it is a random value carrying no
information about the subject or the claim.

These two are the only values so bound. Authenticated additional data detects a
mismatch only against an expectation the receiver independently holds. A
register independently holds its own agreement, and it is handed the nonce. It does not hold the Pattern-Library Version
Identifier: the Pattern Library is the reconciliation server's internal
adversarial-test corpus and is not published to registers, so binding it would
either fail universally or be supplied alongside the ciphertext by the same
party that chose it, detecting nothing.

A register MUST NOT issue more than one Partial Attestation for a given
Reconciliation Nonce, and MUST reject a projection whose nonce it has already
answered. Without this a captured ciphertext could be replayed indefinitely,
each replay yielding a freshly timestamped signed attestation and defeating the
freshness window of {{replay-defence}}.

## Partial Attestation Reception {#partial-attestation}

A Partial Attestation comprises:

- Register Identifier
- Reconciliation-Verdict Field (`match`, `no-match`, `partial-match`, or `indeterminate`)
- OPTIONAL Divergence-Axis Field
- Bilateral-Register-Agreement Hash
- Policy-Version Hash
- OPTIONAL Source-Data Version Identifier Set, present where required by
  {{source-versioning}} and carried in the `arp-source-data-version` COSE header
  parameter of {{iana}}
- OPTIONAL Applied-Parameter Set, being the profile parameters the register
  actually applied in evaluating the Projected Predicate, present wherever the
  Profile Parameter Set of the Per-Register Claim Projection was non-empty
- Query Binding, the SHA-256 digest over the deterministically encoded CBOR
  array `["arp-query-binding-v1", Reconciliation Identifier, Projected
  Predicate, Subject Reference, Reconciliation Nonce]`, those four values taken
  from the Per-Register Claim Projection it answers. The construction is a
  four-element array under a fixed domain-separation string rather than a byte
  concatenation, so that two implementations cannot differ on framing and the
  digest cannot collide with any other construction in this document
- Freshness Timestamp
- Cryptographic Signature over the canonical payload of the foregoing

The Query Binding is what makes an attestation an answer to a question rather
than a free-standing assertion. Without it the signed payload says only that a
register returned a verdict under some agreement and policy version at some
time, and says nothing about what it was asked. Two consequences follow, and
both are severe: an attestation harvested for one subject could be placed into
the Per-Register Result Set of a reconciliation about another subject and would
verify against every other check; and a register could answer the same question
differently to two requesters and deny having done so, because its signature
would not identify the question.

The reconciliation server MUST recompute the Query Binding from the projection
it transmitted and MUST reject an attestation whose Query Binding does not
match, under {{no-answer}} with the reason `attestation-unverifiable`.

The Query Binding Record of {{reconciliation-output}} carries the three
projection values and the register's signed attestation into the Output, so that
a relying party or auditor can recompute the binding and verify the register's
signature independently. A check performed only by the reconciliation server
would rest on the honesty of the party the rest of this document declines to
trust. The
Reconciliation Nonce is unique per Per-Register Claim Projection per
{{terminology}} and MUST NOT be reused, so that an attestation is admissible
only into the reconciliation, and against the register, that elicited it.

The Partial Attestation payload SHALL NOT contain any register-record field,
any pre-image of the register record, or any field beyond those enumerated.
Restricting the Partial-Attestation payload to the enumerated fields, of which
only the verdict and divergence axis vary with the subject, is the mechanism by which ARP limits raw-record disclosure. Residual
inference channels are discussed in {{side-channel}}.

## Aggregation

Verdict Re-Typing under {{verdict-retyping}} operates on per-register verdicts
in the clear and precedes aggregation. Homomorphic Aggregation Mode therefore
applies only where no addressed register's contribution requires re-typing --
that is, where no projection narrowed and no profile parameter differs between
addressed registers. Where any contribution requires re-typing, the aggregation
subsystem MUST operate in Hash-Linkage Aggregation Mode. An implementation MUST
NOT skip re-typing in order to remain in Homomorphic Aggregation Mode.

Where every addressed register declares Homomorphic capability and no
contribution requires re-typing, the aggregation subsystem operates in
Homomorphic Aggregation Mode. Per-register
encrypted verdict contributions are aggregated through a homomorphic
operator sequenced according to the Verdict Arithmetic declared in the
Applicable-Regimes Set. Intermediate values remain cryptographically
committed.

Where any addressed register does not declare Homomorphic capability, the
aggregation subsystem MUST operate in Hash-Linkage Aggregation Mode. Each
Partial Attestation is canonical-hashed, ordered by sorted-leaf
construction, committed to a Merkle tree, and emitted with a Merkle root
and a per-register verdict band signed by the reconciliation-server sealing
key. The Merkle root and its per-register inclusion proofs MAY be encoded as
COSE Receipts {{RFC9942}}, enabling any SCITT-aware verifier to check
inclusion without a bespoke proof format. The per-register
verdict band MUST commit each register's verdict individually without
disclosure of any other register's payload.

## Registers That Do Not Answer {#no-answer}

A register may fail to produce a usable Partial Attestation. Every such state
has a defined outcome, because dropping the register silently would produce
exactly the addressed-register-cherry-picking pattern the Adversarial
Pre-Transmission Test exists to detect.

The Per-Register Result Set MUST carry an entry for every addressed register.
Where no usable attestation was received, the entry's Attested Verdict is
replaced by a Non-Answer Reason drawn from:

- `projection-ambiguous` and `projection-unsupported`, where the projection
  itself failed and no projection was transmitted
- `agreement-drift-suspended`, where reconciliation against that register was
  suspended for Bilateral-Register-Agreement drift
- `attestation-stale`, where the Freshness Timestamp fell outside the declared
  window and the attestation was rejected
- `attestation-unverifiable`, where the signature did not verify or the echoed
  Policy-Version Hash did not match the one sent
- `register-unresponsive`, where no attestation was received within the window
  declared in the Bilateral Register Agreement
- `register-refused`, where the register declined to answer, whether under its
  own statutory access regime or under the Agent-IFF policy
- `query-budget-exhausted`, where the reconciliation would exceed the
  per-subject query budget declared under {{containment}}

A Non-Answer Reason is not a verdict, occupies its own field of the Per-Register
Result Set per {{reconciliation-output}}, and MUST NOT be combined by the
Verdict Arithmetic. Its effect is given in {{verdict-arithmetic}}: a reconciliation with
any non-answering register cannot reach a decisive Combined Verdict.

Where the reason is `attestation-stale`, `freshness-stale` MUST also be added to
the Server-Recorded Divergence-Axis Set against that Register Identifier.

## Verdict Re-Typing {#verdict-retyping}

A register answers the Projected Predicate it was sent, which may be a narrowing
of the Canonical Claim Predicate. Where the narrowing means the register's
answer does not bear on the claim as asked, the reconciliation server MUST
re-type that register's Reconciliation-Verdict Field before aggregation, and
MUST record the attested value, the re-typed value and the ground on which it
re-typed in the Per-Register Result Set, so that an auditor can reproduce the
decision without the server's assurance.

Re-typing is confined to these cases:

- Any contribution other than `match`, attested against a bounded-depth
  predicate where the Canonical Claim ranged over a transitive closure, is
  re-typed to `indeterminate`. A bounded-depth answer that is not a `match` is
  evidence about the bounded depth only, and that is as true of `partial-match`
  and `indeterminate` as of `no-match`. A `match` is not re-typed: an interest
  found at any depth establishes the existential closure predicate.
- A `match` or `no-match` attested over a declared fact, where the Canonical
  Claim ranged over a determined fact, is re-typed to `partial-match` under an
  operator that admits that value and to `indeterminate` under one that does
  not, per {{verdict-arithmetic}}.
- A contribution from a register whose declared interest threshold differs from
  that of any other addressed register, where the Canonical Claim's predicate is
  threshold-sensitive, is re-typed to `partial-match` under an operator that
  admits that value and to `indeterminate` under one that does not. Two
  registers answering under different thresholds are not answering the same
  question, and annotating that on the Reconciliation Output while allowing a
  decisive Combined Verdict to be built from it would state a conclusion the
  inputs do not support.

Re-typing operates on a register's contribution. It does not override the
Verdict Arithmetic declared in the Applicable-Regimes Set, which is applied
afterwards to the re-typed set and is otherwise unaffected. An implementation
MUST NOT re-type on any ground not enumerated here.

## Verdict Arithmetic {#verdict-arithmetic}

The Verdict Arithmetic combines the Reconciliation-Verdict Fields of the
Per-Register Result Set, after any re-typing under {{verdict-retyping}}, into
the Combined Verdict. It is declared in the Applicable-Regimes Set and carried
into the Reconciliation Output so that a relying party can reproduce the
combination.

Two rules apply to every operator and take precedence over the operator's own
table:

- Where any addressed register has no decisive contribution because it did not
  answer, was refused or was rejected under {{no-answer}}, the Combined Verdict
  MUST be `indeterminate`. An operator MUST NOT reach a decisive verdict over an
  incomplete register set, which would be indistinguishable from
  addressed-register-cherry-picking.
- Where any contribution is `indeterminate`, the Combined Verdict MUST be
  `indeterminate` wherever the operator's table would otherwise yield
  `no-match`. An `indeterminate` contribution is an absence of evidence and a
  decisive negative may not be built on one, so the rule states the substitute
  result rather than only a prohibition; a prohibition without a substitute
  would leave the verdict undefined in exactly the cases it governs.

Subject to those, the operators are:

conjunction:
: `match` where every contribution is `match`. `no-match` where any contribution
  is `no-match`. `partial-match` where every contribution is `match` or
  `partial-match` and at least one is `partial-match`. `indeterminate`
  otherwise.

disjunction:
: `match` where any contribution is `match`. `no-match` where every contribution
  is `no-match`. `partial-match` where at least one is `partial-match` and none
  is `match`. `indeterminate` otherwise.

threshold-count:
: `match` where the count of `match` contributions meets or exceeds the
  threshold declared in the Applicable-Regimes Set. `no-match` where the count
  of `match` contributions cannot reach the threshold and no contribution is
  `indeterminate`. `indeterminate` otherwise, which includes every case in which
  an `indeterminate` contribution is present and the threshold is not met.
  `partial-match` contributions do not count toward the threshold.

source-class-quorum:
: threshold-count evaluated per source class as declared in the
  Applicable-Regimes Set, then combined across classes by conjunction.

Every operator admits `partial-match` except threshold-count and
source-class-quorum, which do not. Where {{verdict-retyping}} would re-type a
contribution to `partial-match` under an operator that does not admit it, the
contribution is re-typed to `indeterminate` instead.

## Reconciliation Output {#reconciliation-output}

A Reconciliation Output comprises:

- Reconciliation Identifier
- Claim Hash
- Reconciliation Timestamp
- Combined Verdict
- Verdict Arithmetic, as declared in the Applicable-Regimes Set, together with
  every parameter that operator takes -- the threshold for threshold-count, and
  the source-class partition for source-class-quorum
- Addressed-Registers Identifier Set
- Bilateral-Register-Agreement Hash Set
- Policy-Version Hash
- Pattern-Library Version Identifier
- Requester-Binding Class
- Per-Register Result Set, one entry per addressed register
- Server-Recorded Divergence-Axis Set, possibly empty
- OPTIONAL Override Record, present exactly where an Adversarial
  Pre-Transmission Test failure was overridden
- Sealing-Key Identifier
- Sealing Signature over the canonical serialisation of the foregoing

The Reconciliation Identifier is the Claim Hash concatenated with the
Policy-Version Hash. It is therefore reproducible from enumerated inputs and
satisfies the determinism requirement of {{architecture}} without a separate
construction rule.

The Claim Hash binds the Output to the question it answers. Without it a relying
party receives a Combined Verdict with nothing to attribute it to, and the
Retroactive Evaluation Subsystem has no key to select on.

The Verdict Arithmetic and its parameters are carried because a relying party
cannot otherwise reproduce the combination from the Per-Register Result Set, and
because {{verdict-retyping}} turns on which values the operator admits. The
Applicable-Regimes Set is a Canonical Claim field and is not itself carried in
the Output, so naming the operator without its parameters would leave
threshold-count and source-class-quorum irreproducible.

Each entry of the Per-Register Result Set comprises:

- Register Identifier
- Answer State, either `answered` or `not-answered`
- Attested Verdict, present exactly where the Answer State is `answered`
- Non-Answer Reason of {{no-answer}}, present exactly where the Answer State is
  `not-answered`
- Effective Verdict, present exactly where the Answer State is `answered`, being
  the Attested Verdict or its re-typing under {{verdict-retyping}}
- Re-Typing Ground, drawn from the registry of {{iana}}, present exactly where
  the Attested and Effective Verdicts differ
- Policy-Version Hash as echoed by that register, present exactly where the
  Answer State is `answered`
- OPTIONAL Divergence-Axis Field, as attested by that register
- OPTIONAL Source-Data Version Identifier Set, as attested by that register
- Projection Record, comprising the Narrowed-From field of the Per-Register
  Claim Projection where a projection was transmitted, and the Applied-Parameter
  Set the register reported where the Answer State is `answered`; required
  wherever a projection was transmitted and either the projection narrowed or
  the Profile Parameter Set was non-empty
- Query Binding Record, present exactly where the Answer State is `answered`,
  comprising the Projected Predicate, the Subject Reference and the
  Reconciliation Nonce the server transmitted, and the register's signed Partial
  Attestation

Each member of the Server-Recorded Divergence-Axis Set is a pair of a Divergence
Axis and the Register Identifier it concerns, or the Divergence Axis alone where
it concerns the reconciliation as a whole. Of the axes recorded by the server,
`freshness-stale` and `declared-not-determined` are per-register and MUST carry
a Register Identifier. `source-version-skew` is a relation between two or more
registers, and one member MUST be added for each register involved, so that the
set is a determinate function of the inputs rather than a choice between them; `register-threshold-divergence`
concerns the reconciliation and MUST NOT. Recording a bare axis over five
addressed registers would state that something was stale without stating what,
which is not reproducible.

The Set is a set rather than a single value: a reconciliation may be qualified
on more than one axis, and an encoding admitting only one would force an
implementation to choose between them silently.

The Reconciliation Hash is the SHA-256 digest over the deterministically encoded
CBOR serialisation of a Reconciliation Output excluding its Sealing Signature
and its Sealing-Key Identifier, using the deterministic encoding requirements of
{{RFC9052}}. It is the value recorded in the Settlement-Layer Ledger and the
value a Post-Seal Evaluation Record references.

CBOR rather than {{RFC8785}}: the mandatory-to-implement encoding for a
Reconciliation Output is CBOR, and several of its fields are byte strings, for
which JSON has no type. Digesting a JSON rendering of it would require a
CBOR-to-JSON mapping this document does not define, and two implementations
would produce different ledger indices. The Canonical Claim is JSON and is
digested under {{RFC8785}}; the Reconciliation Output is CBOR and is digested
under deterministic CBOR. These are two constructions over two encodings and
{{construction-distinctness}} applies to both.

A Reconciliation Output is immutable once sealed. Conditions arising after
sealing are recorded under {{post-seal}} and MUST NOT be represented as fields
of the Reconciliation Output.

## Policy-Version-Hash Sealing {#sealing}

The Policy-Version Hash MUST commit to:

1. Reconciliation rules
2. Threshold parameters
3. Pattern-Library Version Identifier
4. Applicable-Regimes precedence
5. Verdict-Arithmetic selection
6. Agent-IFF policy identifier and the Requester-Binding
7. Bilateral-Register-Agreement Hashes of the addressed registers

The Policy-Version Hash MUST be reconstructible under audit from a canonical
policy state persisted in a policy-epoch store.

The Claim Hash and the Policy-Version Hash MUST each be computed over a preimage
that includes the Deployment Blinding Value: a secret of at least 128 bits drawn
once from a cryptographically secure random source, persisted in the
policy-epoch store, constant for the life of the deployment, and disclosed only
under the audit path.

It is constant rather than per-claim, and that is what makes it compatible with
the rest of this document. The Claim Hash remains a deterministic function of
the canonical claim fields within a deployment, so it remains usable as the
Settlement-Layer Ledger index and as the retroactive-evaluation key, and the
bit-for-bit requirement of {{architecture}} continues to hold: the same
deployment given the same enumerated inputs produces the same digests. What
changes is that the preimage is no longer guessable from outside the deployment.
A per-claim random value would defeat all three properties.

Both digests are otherwise taken over low-entropy preimages: a subject
identifier is typically a company number of ten or so digits, a predicate is
drawn from a published taxonomy, and the accountable principal, agent-IFF policy
identifier and verdict arithmetic are each drawn from small enumerable sets
within one deployment. Both digests then appear where adversaries can reach
them -- the Policy-Version Hash in the protected header of every notarised
Signed Statement and in every Ledger entry, the Claim Hash in the Output and the
Ledger. Without blinding, anyone holding either can recover by exhaustive search
the subject that was investigated and the principal that commissioned the
reconciliation, which is the disclosure this protocol exists to prevent.
Blinding does not weaken reconstructibility under audit, since the Blinding
Value is persisted with the state it blinds.

A register receives the same Policy-Version Hash as every other addressed
register, by {{projection}}. The Blinding Value prevents two colluding registers
from recovering the Addressed-Registers Identifier Set from it by search; that
they can observe they were addressed together is inherent and is discussed in
{{side-channel}}.

## Post-Seal Evaluation Records {#post-seal}

Two conditions arise after a Reconciliation Output has been sealed and therefore
cannot be fields of it, and are not Divergence Axes: a Divergence Axis qualifies
a verdict, and these qualify an operation performed on an Output that is already
immutable.

- `notarisation-incomplete`, where notarisation under {{scrapi-binding}} neither
  completed nor was refused within the polling bound.
- `attribution-indeterminate`, where a Retroactive Evaluation could not
  determine whether a material change arose from a change in policy state or
  from a change in Source-Data Version.

Each is recorded in a Post-Seal Evaluation Record comprising:

- the Reconciliation Hash of the Output it concerns
- the Post-Seal Evaluation Qualifier, drawn from the registry of {{iana}}
- the Policy-Version Hash and Pattern-Library Version Identifier in force at
  the time of the evaluation, which may differ from those the Output was sealed
  under
- a signature by the reconciliation-server sealing key

A Post-Seal Evaluation Record MUST be retained by the reconciliation server for
as long as the Reconciliation Output it references may be relied upon, and its
hash MUST be appended to the Post-Seal Evaluation Record Hash Set of that
reconciliation's Settlement-Layer Ledger entry. A relying party discovers a
record through that Ledger entry and retrieves it under the media type
registered in {{iana}}. A record emitted but not linked from the Ledger would be
undiscoverable, which would make the attribution safety valve of
{{source-versioning}} unreachable in exactly the case it exists for.

A Post-Seal Evaluation Record MUST NOT alter the Reconciliation Output it
references, and a relying party MUST NOT treat the existence of one as
invalidating that Output. A Reconciliation Output whose notarisation is
incomplete remains valid under its Sealing Signature.

Where a Sovereign Re-Notification is emitted under {{retroactive}} for a
material change, the notification MUST state whether the change arose from
policy state or from Source-Data Version, and where it cannot, a Post-Seal
Evaluation Record carrying `attribution-indeterminate` MUST be emitted and
referenced by the notification.

## Settlement-Layer Ledger {#settlement-ledger}

Each Settlement-Layer Ledger entry comprises only:

- Entry Sequence Number (monotonically increasing)
- Claim Hash, the index of {{architecture}}
- Reconciliation Hash
- Policy-Version Hash
- Addressed-Registers Identifier Set (sorted in canonical lexicographic order)
- Aggregation-Method Descriptor
- OPTIONAL Merkle Root
- Requester-Binding-Class Descriptor (human-operator, agent-verified, or agent-unverified)
- Reconciliation Timestamp
- Prior-Entry Hash
- Self-Entry Hash
- OPTIONAL Source-Reconciliation-Output Identifier, present where the entry
  supersedes an earlier Reconciliation Output
- Entry Signature by the reconciliation-server sealing key, covering every
  preceding field including the Self-Entry Hash, and carrying the Sealing-Key
  Identifier that resolves it

Prior-Entry and Self-Entry Hashes establish that no entry has been removed from
a chain; they do not establish that only one chain exists. Signing each entry
makes a second chain attributable rather than merely possible.

Facts that arise after an entry is written -- the outcome of notarisation, and
any Post-Seal Evaluation Record -- are recorded as SUBSEQUENT entries of
Continuation type, each carrying the Claim Hash and Reconciliation Hash of the
reconciliation it concerns and one of:

- a Notarisation Record, comprising the Transparency Service identifier and the
  EntryID it returned, or the terminal failure reported by that service
- a Post-Seal Evaluation Record Hash and a retrieval URI for that record

A Reconciliation Output is sealed before it is notarised and so cannot itself
carry the EntryID, and the Ledger exposes no UPDATE, so the join cannot be made
by amending the original entry. It is made by appending. Without it a successful
notarisation would be unlinkable to the reconciliation from every side, since
retrieval is by EntryID and {{I-D.ietf-scitt-scrapi}} offers no query surface.

The Ledger MUST NOT store Canonical-Claim content, register records,
Partial-Attestation payloads, or any principal identifier in the clear; the
requester's accountable principal is committed only through the Policy-Version
Hash. The append-only constraint MUST be enforced at the storage interface layer. The
Ledger interface MUST expose APPEND and READ operations only, with no UPDATE and
no DELETE operation exposed or implemented. READ is required by the Regulator
Portal, by Retroactive Evaluation and by the derivation-chain invariant check,
and is constrained by the scope rules of {{regulator-portal}}.

Where the Ledger is replicated per {{ledger-replication}}, each secondary store
MUST be able to demonstrate that its chain and every other secondary store's
chain share a common prefix.

A common-prefix demonstration between stores under one operator is that operator
attesting to itself. The reconciliation server MUST therefore publish the
Self-Entry Hash of its current head, signed, at
`/.well-known/arp-ledger-head` on its authority origin, and MUST notarise that
head into a SCITT Transparency Service under {{scrapi-binding}} at an interval
declared in the Bilateral Register Agreements. A fork is then detectable by any
party that has seen two heads, rather than only by a party holding two
jurisdictions' views -- which the scope rules of {{regulator-portal}} correctly
prevent any single regulator from holding.

### Replication {#ledger-replication}

The Ledger MAY be distributed across a plurality of per-jurisdiction
secondary stores under synchronous replication, each operated under the
data-residency constraints of its host jurisdiction. The append-only
derivation-chain invariant -- that every entry's Prior-Entry Hash equals the
Self-Entry Hash of the immediately preceding entry -- MUST be preserved
across all secondary stores.

## Regulator Portal {#regulator-portal}

The Regulator Portal Subsystem authenticates a sovereign regulator's
jurisdictional credentials against a regulator-identity-provider trust
anchor that MUST be declared in every Bilateral Register Agreement addressed by
the reconciliation being read. It restricts returned fields to those within the
regulator's statutory scope as declared in the statutory-regulator-access scope
of those agreements. The scope restriction is computed as the INTERSECTION of
the per-agreement permitted-read-predicates entries scoped to the regulator's
jurisdiction, further intersected with the regulator's requested field set. Each
access MUST be recorded in an append-only subpoena-grade audit trail.

Both intersections are load-bearing. Taking the union across agreements would
let one register operator's permissive agreement widen what a regulator may read
about a reconciliation that also addressed a restrictive register, inverting the
data-residency property this protocol exists to preserve; and requiring the
trust anchor in only one agreement would let a single register operator
unilaterally introduce a regulator identity that authenticates against
multi-register events. Intersecting with the requester's own requested set is
not itself a restriction, since the requester chooses it.

## Retroactive Evaluation {#retroactive}

Upon publication of an updated Pattern Library, an updated Policy Version, or a
new Source-Data Version for any list a register consulted under
{{source-versioning}}, the Retroactive Evaluation Subsystem MUST execute a
deterministic re-application of the updated policy state to retained reconciliation
metadata of historical Reconciliation Outputs sealed against a superseded
Policy-Version Hash. Where permissible under the applicable Bilateral
Register Agreements, partial attestations MAY be re-invoked.

The retroactive evaluation MUST be executable without re-negotiation of any
Bilateral Register Agreement. A material change in a historical Combined Verdict -- defined as any change of
verdict value into, out of, or between the decisive values, the decisive values
being `match` and `no-match` -- MUST trigger a Sovereign Re-Notification through the Regulator Portal, and MUST
additionally be published as a Continuation entry on the Settlement-Layer Ledger
so that a relying party which acted on the superseded Output can discover that
it was superseded. Notifying only the regulator would leave the party that acted
on a verdict the last to learn it had changed. A transition from `no-match` to `match` is material: it is
the case the protocol's motivating domain cares most about, and a definition
that excluded transitions within the decisive class would omit it. Revocation of a
Verified Principal Credential relied upon in a historical reconciliation is
itself a material change: the Retroactive Evaluation Subsystem MUST re-derive
the affected Requester-Binding class and, where a decisive reconciliation was
performed for what is now an unverifiable requester, emit a Sovereign
Re-Notification.

## Cryptographic-Primitive-Upgrade Path

Each Bilateral Register Agreement MUST declare a
Cryptographic-Primitive-Upgrade Path comprising an ordered equivalence list
for each of three primitive classes: claim-encryption,
partial-attestation-signature, and sealing-signature. The equivalence list
MUST include at least one post-quantum primitive for each class, drawn from a
set including ML-KEM {{FIPS203}} for key encapsulation and ML-DSA {{FIPS204}}
for signature operations.

A primitive rotation MAY be executed simultaneously across the three
layers without bilateral renegotiation. The Settlement-Layer Ledger
remains continuous across the rotation because Ledger entries commit to
hashes of canonicalised content rather than to cryptographic identities.

# Agentic Principal Reconciliation

The Agent Friend-or-Foe Determination described in the Requester Identity
Binding and Agent Friend-or-Foe Gate above establishes whether the requester
of a reconciliation is friendly. ARP additionally supports reconciling an
agent's principal binding as the subject of a reconciliation in its own right,
so that the question "does a real, authenticated principal stand behind this
agent?" can itself be answered against authoritative identity registers rather
than asserted.

A reconciliation over the `agent:` predicate branch takes as its Subject
Identifier the agent's declared identity (for example its signature-agent-card
key thumbprint or a directory identifier) and as its Attested Value the
principal binding the agent asserts. Addressed registers for this predicate
class are identity and credential registers -- for example an organisational
directory, a credential-issuer status list, or a national identity register --
each under its own Bilateral Register Agreement. The Combined Verdict answers
whether the asserted principal binding is corroborated:

- `match`: the agent's asserted principal binding is corroborated by the
  addressed registers; the agent is FRIENDLY with an attributable principal.

- `no-match` with divergence axis agent-impersonation-suspected: the asserted
  binding is contradicted; the agent is asserting a principal it is not bound
  to.

- `no-match` with divergence axis agent-credential-absent or
  agent-principal-unverifiable: no corroborating record exists; the binding
  cannot be established and the agent MUST be treated as ENEMY.

This composition allows a relying party to gate an action not merely on the
presence of an agent signature but on register-corroborated proof that an
accountable principal stands behind it, narrowing the impersonation surface at
the reconciliation layer. The result is a Reconciliation Output like any other:
sealed against a Policy-Version Hash, written to the Settlement-Layer Ledger as
hashes only, and re-evaluable if the underlying credential is later revoked.

# Encoding {#encoding}

## CBOR-COSE Encoding

The mandatory-to-implement encoding for ARP messages on the wire is CBOR with
COSE {{RFC9052}} {{RFC9053}} envelopes. COSE_Sign1 is used for both Partial
Attestations and the Sealing Signature. The protected header MUST include the Bilateral-Register-Agreement Hash and
Policy-Version Hash as COSE header parameters registered per {{iana}}.
`arp-bilateral-agreement-hash` always carries an array, sorted in lexicographic
byte order: a Partial Attestation's array has exactly one member, and a Sealing
Signature's has one per addressed register. A single encoding for both avoids a
decoder having to infer the type from context. Pending registration,
implementations MAY use labels from the private-use range of the COSE Header
Parameters registry; such use is not interoperable.

## HTTP Message Signature Binding

Where a reconciliation is requested over HTTP by an autonomous agent, the
request SHOULD be signed under HTTP Message Signatures {{RFC9421}}, with the
signature-agent key resolvable through a Web Bot Auth signature-agent card
{{I-D.meunier-webbotauth-registry}}, advertised via the Signature-Agent header
{{I-D.meunier-webbotauth-httpsig-protocol}} and resolved through the HTTP
Message Signatures directory it names
{{I-D.meunier-webbotauth-httpsig-directory}}. The reconciliation server
derives the Agent Friend-or-Foe Determination from
verification of that signature and,
where required by the Agent-IFF policy, a Verified Principal Credential
carried in the request body.

## SCITT Reference API Binding {#scrapi-binding}

A Reconciliation Output MAY be notarised into a SCITT Transparency Service as a
transparent statement. Where it is, an implementation MUST use the binding in
this section. {{composition-scitt}} states the architectural relationship; this
section states the wire behaviour, so that two implementations registering the
same Reconciliation Output against the same Transparency Service produce
interchangeable results.

### Registration {#registration}

The Reconciliation Output MUST be registered as a Signed Statement by
`POST /entries` as defined in {{I-D.ietf-scitt-scrapi}}.

The payload of the Signed Statement MUST be the sealed COSE_Sign1 -- the
Reconciliation Output under its Sealing Signature, as produced by
{{sealing}} -- and MUST NOT be the bare Reconciliation Output. Nesting is what
makes the requirements below checkable: a relying party holding only the bare
Output has neither the sealing key identity nor the Policy-Version Hash the seal
committed to, and could not verify either.

The Signed Statement is therefore a COSE_Sign1 whose payload is itself a
COSE_Sign1. Its protected header MUST carry:

- the content type `application/arp-sealed-reconciliation-output+cose`,
  registered per {{iana}}. The outer payload is a COSE_Sign1 wrapping a
  Reconciliation Output, not a Reconciliation Output, and labelling it with the
  latter's media type would have a conforming decoder parse a signature envelope
  as an Output;
- `arp-policy-version-hash`;
- `arp-bilateral-agreement-hash`, carrying the array of the
  Bilateral-Register-Agreement Hashes of the addressed registers, sorted in
  lexicographic byte order as required by {{encoding}}. A Reconciliation Output
  aggregates registers under more than one agreement, and an unordered encoding
  would make two conforming implementations produce non-interchangeable Signed
  Statements.

The outer COSE_Sign1 MUST carry a `kid` in its protected header, MUST be signed
under a key resolvable through {{sealing-key-discovery}}, and that key's
Sealing-Key Identifier MUST equal the Sealing-Key Identifier of the nested
Output in both components. A relying party MUST verify the outer signature and
that equality. "Signed by the server that sealed it" is otherwise not a
predicate a relying party can evaluate: any operator of a conforming server
could wrap another server's sealed Output, sign it under its own resolvable key,
and every other check here would pass. Without this any party holding a sealed Output could wrap
it in an envelope of their own and register it: every other check here would
pass, and the Receipt would attribute the statement to the Transparency Service
and to nobody else. Fixing the nested payload closes a false-policy-version
attack; fixing the outer signer closes a wrong-registrant one.

The `arp-bilateral-agreement-hash` in the outer protected header MUST equal the
value carried in the nested sealed COSE_Sign1, and the
`arp-policy-version-hash` in the outer protected header MUST equal the
Policy-Version Hash carried in the nested sealed COSE_Sign1. A relying party
MUST verify the Sealing Signature over the nested payload, MUST verify that
equality, and MUST reject the Signed Statement where either fails.

The verification key for the Sealing Signature is identified by the Sealing-Key
Identifier of {{reconciliation-output}}, whose `kid` component MUST equal the
`kid` in the protected header of the nested COSE_Sign1, and is resolved through
{{sealing-key-discovery}}. A relying party that cannot resolve the Sealing-Key
Identifier MUST NOT rely on the notarised statement.

Without nesting and this equality the Signed Statement would be a second and
independent envelope: any party holding a valid Reconciliation Output could
register it under a protected header asserting a policy version it was not
sealed under, and a relying party following {{policy-version-determination}}
would believe that assertion. A protected header cannot be altered after
signing, but it can be false when signed, and integrity is not correctness.

The payload MUST NOT be the Verifiable Credentials serialisation of
{{vc-interop}}. That form is an interop convenience for relying parties and is
not the notarised object; registering it instead would notarise a
representation whose canonical form is unspecified.

### Asynchronous registration

A Transparency Service may register synchronously or asynchronously, and an
implementation MUST support both. This is the most likely source of divergence
between two otherwise conforming implementations, and is therefore stated as a
requirement rather than left to the referenced document.

On `201 Created` the Receipt is available immediately. On `202 Accepted` the
response carries a `Location` header, and the implementation MUST poll that URL
verbatim rather than constructing a path of its own. A `204 No Content` means
registration is still in progress and MUST NOT be treated as failure or as a
negative result.

A `404 Not Found` is terminal and MUST NOT be polled further. It carries two
meanings in {{I-D.ietf-scitt-scrapi}} -- that the entry identifier is not known,
and that the Signed Statement could not be persisted to the log -- and an
implementation MUST distinguish them from the response body where it does so,
because the second is a registration failure and the first may follow from
having polled a URL the Transparency Service did not issue.

An implementation MUST honour a `Retry-After` header where one is present, MUST
NOT poll more frequently than once per second in its absence, and MUST bound
total polling; a bound of 300 seconds is RECOMMENDED where the Bilateral
Register Agreement declares none. Exhaustion of the bound MUST be recorded in a Post-Seal Evaluation Record
carrying `notarisation-incomplete` per {{post-seal}}, rather than as either
success or refusal. A
Reconciliation Output whose notarisation is incomplete remains valid under its
Sealing Signature; notarisation is an additional property, not a precondition of
validity.

### Sealing-key discovery {#sealing-key-discovery}

A relying party is not a party to any Bilateral Register Agreement and holds
only the hashes of those agreements. It therefore cannot resolve the sealing key
from them, and a binding that assumed otherwise would oblige every conforming
relying party to refuse every Reconciliation Output.

A reconciliation server MUST publish its sealing keys as a COSE Key Set at
`/.well-known/arp-sealing-keys` on the service-operator's authority origin, and
a single key by identifier at `/.well-known/arp-sealing-keys/{kid_value}`. The
Sealing-Key Identifier is the pair of that origin and the `kid`; where this
document requires a `kid` to equal the Sealing-Key Identifier, it is the `kid`
component that is compared.

Resolving a key is not sufficient. Web PKI establishes that an origin is the
origin it claims to be; it does not establish that the origin is entitled to
seal Reconciliation Outputs naming a given register set. A relying party that
accepted any well-formed key set would accept an Output minted by any party able
to stand up a host, since the Bilateral-Register-Agreement Hashes can be copied
from a genuine Output and are one-way.

Each Bilateral Register Agreement MUST therefore declare the authority origin of
the reconciliation server it authorises, and each register operator MUST publish
an Authorised-Origin Document at `/.well-known/arp-authorised-origins` on its own
register origin. A Register Identifier is an origin, so the register origin is a
member of the Addressed-Registers Identifier Set and is known to the relying
party from the Output.

An Authorised-Origin Document is a COSE_Sign1 whose payload comprises, for each
reconciliation server the register operator has authorised, that server's
authority origin and the identifier of the key that signs that server's sealing
key set. It MUST be signed under a key served as a COSE Key Set at
`/.well-known/arp-register-keys` on the same register origin, which the relying
party fetches over its ordinary web PKI. Signing it matters for the same reason
signing the sealing key set matters: an unsigned document fetched over TLS can
be varied per audience, and this one is the root of the chain.

A relying party MUST verify that the origin component of the Sealing-Key
Identifier appears in the Authorised-Origin Document published by every register
in the Addressed-Registers Identifier Set, and MUST reject the Output where it
does not or where any such document cannot be verified.

The chain is then: register origins from the Output; each register's own key
from its register origin; the Authorised-Origin Document verified under that
key; the authorised server origin and its key-set signing key identifier from
that document; and the sealing key from the server's key set, verified under
that identifier. Every step is fetchable by a party holding only the Output.

A key entry MUST carry a validity interval and a status of `active`, `retired`
or `revoked`. A relying party MUST reject a Sealing Signature made under a
`revoked` key irrespective of when the Output claims to have been sealed, MUST
accept one made under a `retired` key only where the Reconciliation Timestamp
falls within that key's validity interval, and MUST reject one whose
Reconciliation Timestamp falls outside the interval of the key it resolves to. A
key MUST NOT be removed from the set while any Reconciliation Output it sealed
may still be relied upon: retirement is by status, not by deletion, so that a
historical Output remains verifiable while a compromised key can still be
refused.

The key set MUST itself be signed under the key whose identifier the
Authorised-Origin Document gives for that server, and a relying party MUST verify
that signature. The identifier comes from a document the relying party can
fetch, not from an agreement it does not hold. A
key set fetched over TLS alone can be varied per audience, which would let a
server present one key to one relying party and another to a second and seal two
contradictory Outputs for the same reconciliation, each verifiable only by its
intended audience -- reopening at the origin the equivocation that
{{policy-version-determination}} closes at the Transparency Service.

### Receipt validation

A relying party MUST validate the Receipt against Transparency Service keys
obtained from `GET /.well-known/scitt-keys`, or from
`GET /.well-known/scitt-keys/{kid_value}` for a single key identified in the
Receipt.

### Policy-version determination {#policy-version-determination}

A relying party MUST determine the Policy Version of a notarised Reconciliation
Output from the `arp-policy-version-hash` parameter in the verified protected
header of the Signed Statement, and MUST NOT determine it from any retrieval
path, query parameter or Transparency Service index entry.

Because the parameter is in the protected header, it is covered by the Receipt;
and because {{registration}} requires the sealed COSE_Sign1 to be the nested
payload and the outer parameter to equal the Policy-Version Hash it carries,
what the header asserts is verifiably what the seal committed to. The policy version is
therefore established by verification rather than by lookup, and a Transparency
Service that indexed an entry incorrectly, or presented different index results
to different relying parties, cannot cause a relying party to attribute a
Reconciliation Output to a policy version it was not sealed under.

This holds only because of the nesting and equality requirements in
{{registration}}, both of which the relying party checks. A protected header
alone establishes that a value was not altered after signing, not that it was
true when signed.

{{I-D.ietf-scitt-scrapi}} defines retrieval by `EntryID` and defines no query
surface. Correlating entries by policy version is consequently outside the scope
of this binding and is a property of the deployment, not of the protocol. An
implementation MUST NOT assume a standard retrieval path keyed on the
Policy-Version Hash exists.

## Verifiable Credentials Interop {#vc-interop}

A Reconciliation Output MAY be additionally serialised as a JSON-LD
document conforming to the W3C Verifiable Credentials Data Model
{{W3C-VC-DM-2.0}}, with the Reconciliation Hash, Addressed-Registers
Identifier Set, Bilateral-Register-Agreement Hash Set,
Requester-Binding-Class, and Policy-Version Hash included as credential
subject fields. The COSE_Sign1 envelope is the normative form; the
Verifiable Credential serialisation is an interop convenience for relying
parties operating in W3C VC ecosystems.

# Security Considerations

## Service-Operator Containment {#containment}

The reconciliation server operates under a service-operator entity
standing in bilateral contractual relationship with each Register
Operator. The service-operator entity MUST be architecturally prohibited
from observing any register record or any Partial-Attestation payload
beyond the verdict and divergence-axis fields. The service-operator entity
MUST be structurally incapable of disclosing any register record
irrespective of internal operator action.

That property is per-event and MUST NOT be read as a property of the system
under repeated querying. A verdict is a function of an attested value the
requester chooses, so a sequence of reconciliations varying that value recovers
the underlying record field by search, and several Divergence Axis values --
`ownership-threshold-mismatch`, `register-record-absent`, `temporal-mismatch` --
disclose record content on their own. Each event conforms while the sequence
does not.

A deployment MUST therefore declare in each Bilateral Register Agreement a
per-subject query budget and the interval over which it is measured, and the
reconciliation server MUST refuse a reconciliation that would exceed it,
recording `query-budget-exhausted` as the Non-Answer Reason for the affected
register. The Pattern Library MUST include a repeated-narrowing pattern so that
the Adversarial Pre-Transmission Test detects the sequence rather than only the
event.

A register cannot apply its own statutory access regime to a requester it cannot
see. Where a Bilateral Register Agreement requires it, the Per-Register Claim
Projection MUST carry the Requester-Binding Class, which discloses the class and
not the principal.

## Pattern-Library Integrity

The Adversarial Pre-Transmission Test gates onward transmission. The
Pattern Library MUST be bound to a Pattern-Library Commitment Hash. Any
modification to the Pattern Library MUST produce a new Pattern-Library
Version Identifier, and the Adversarial Pre-Transmission Test MUST be
re-executed against the new library before the change takes effect.

## Agent Impersonation and Friend-or-Foe Integrity {#agent-iff-integrity}

The Agent Friend-or-Foe Determination is the mechanism by which ARP resists
reconciliation initiated by an agent impersonating a principal. The
determination MUST default to ENEMY: absence of a verifiable identity, an
expired or revoked signature-agent key, a failed HTTP Message Signature
{{RFC9421}} verification, or a Verified Principal Credential that does not
validate MUST all yield an ENEMY classification. The server MUST NOT infer
friendliness from network origin, User-Agent string, or any self-asserted
identifier, as these are trivially forgeable. Where an ENEMY requester is
permitted for advisory reconciliation, the resulting Reconciliation Output
MUST NOT carry a decisive verdict binding, and the Settlement-Layer Ledger
entry MUST record the agent-unverified requester-binding class so that
downstream reliance is aware no accountable principal was established.

## Bilateral-Register-Agreement Drift

Each Bilateral Register Agreement carries an Agreement Hash. Each Partial
Attestation includes a reference to the Agreement Hash under which it was
issued. Agreement drift is detectable by comparison of agreement-hash
references across Partial-Attestation batches. Reconciliation MUST be
suspended for an addressed register whose Agreement Hash deviates from the
hash committed at the start of a reconciliation event.

## Replay Defence {#replay-defence}

Each Partial Attestation MUST carry a Freshness Timestamp. The
reconciliation server MUST verify the Freshness Timestamp against a
freshness window declared in the Bilateral Register Agreement. Stale Partial Attestations MUST be rejected, and the rejection MUST be recorded
in the Reconciliation Output under {{no-answer}} with the Non-Answer Reason
`attestation-stale` and a `freshness-stale` divergence axis attributed to that
register. A signed agent request under {{RFC9421}} MUST additionally carry a
nonce or created/expires parameter set so that a captured signed request
cannot be replayed to initiate a fresh reconciliation.

## Post-Quantum Migration

The Cryptographic-Primitive-Upgrade Path is the mechanism by which ARP
deployments migrate to post-quantum primitives. ML-KEM-1024 {{FIPS203}}
is RECOMMENDED for the claim-encryption primitive class. ML-DSA-65
{{FIPS204}} is RECOMMENDED for the partial-attestation-signature and
sealing-signature primitive classes. Implementations MUST declare their
chosen post-quantum primitives in the Bilateral Register Agreement.

## Side-Channel Considerations {#side-channel}

Per-register projection narrowing is observable to the addressed register
through the Projected Predicate. Implementations MUST NOT use narrowing
patterns to fingerprint individual subjects. The Predicate Taxonomy SHOULD
be designed such that the set of permitted narrowings is small enough that
narrowing observation does not materially weaken subject privacy.

# IANA Considerations {#iana}

This document requests IANA to register the following:

- Three COSE header parameters in the COSE Header Parameters registry, values
  to be assigned by IANA:
  - `arp-bilateral-agreement-hash` (value TBD)
  - `arp-policy-version-hash` (value TBD)
  - `arp-source-data-version` (value TBD)

  Each registration MUST state the parameter's value type and whether it may
  appear in an unprotected header. A parameter that no encoding in
  {{encoding}} uses MUST NOT be registered.

- A registry of ARP Divergence-Axis values, registration policy Specification
  Required, initially containing the descriptors enumerated in the Divergence
  Axis definition of {{terminology}}. Each entry MUST record whether the axis is
  register-attestable or server-recorded, a distinction three normative sections
  depend on and which is otherwise carried only in prose. The designated expert
  MUST refuse a registration that does not state it. A reconciliation server
  MUST reject a Partial Attestation that attests a server-recorded axis, under
  {{no-answer}} with the reason `attestation-unverifiable`.

- Three entries in the Well-Known URIs registry of {{RFC8615}}:
  `arp-sealing-keys` ({{sealing-key-discovery}}), `arp-authorised-origins`
  ({{sealing-key-discovery}}) and `arp-ledger-head` ({{settlement-ledger}}).

- A registry of ARP Non-Answer Reasons, registration policy Specification
  Required, initially containing the values enumerated in {{no-answer}}. A
  Non-Answer Reason is not a verdict; the designated expert MUST refuse a
  registration that could be combined by the Verdict Arithmetic.

- A registry of ARP Re-Typing Grounds, registration policy Specification
  Required, initially containing `bounded-depth-not-closure`,
  `declared-not-determined` and `threshold-divergence`, corresponding to the
  three grounds of {{verdict-retyping}}.

- A registry of ARP Verdict-Arithmetic operators, registration policy
  Specification Required, initially containing conjunction, disjunction,
  threshold-count and source-class-quorum, defined in {{verdict-arithmetic}}. A
  registration MUST state the operator's result as a total function of the
  multiset of contribution values and the operator's declared parameters, and
  MUST state whether it admits partial-match, on which {{verdict-retyping}}
  turns.

- A registry of ARP Post-Seal Evaluation Qualifiers, registration policy
  Specification Required, initially containing `notarisation-incomplete` and
  `attribution-indeterminate`, defined in {{post-seal}}. A registration MUST
  identify a condition arising after a Reconciliation Output is sealed; the
  designated expert MUST refuse a registration that qualifies a verdict, which
  belongs in the Divergence-Axis registry.

- A registry of ARP Register Data-Format Profile identifiers, registration
  policy Specification Required, initially containing `arp-profile-bods`,
  `arp-profile-corporate-org`, `arp-profile-customs-wco` and
  `arp-profile-sanctions-consolidated`, defined in {{format-profiles}}.
  Identifiers beginning `x-` are reserved for bilateral use and are not
  registered. A registration MUST state the dated vocabulary in which permitted
  predicates are expressed, the relation corresponding to taxonomic narrowing
  for each branch of its predicate space, and the parameters a Bilateral
  Register Agreement declaring it must supply. The designated expert MUST refuse
  a registration that defines any means of transporting register records, that
  declares more than one parent relation applicable to a single predicate, that
  names a vocabulary without pinning its version, or that fixes in the profile a
  parameter that varies between registers using the same format.

- A media type `application/arp-reconciliation-output+cbor` for the
  CBOR-encoded Reconciliation Output.

- A media type `application/arp-sealed-reconciliation-output+cose` for the
  sealed COSE_Sign1 registered as a SCITT Signed Statement per
  {{scrapi-binding}}.

- A media type `application/arp-post-seal-evaluation-record+cbor` for the record
  of {{post-seal}}.

- A media type `application/arp-reconciliation-output+ld+json` for the
  Verifiable Credentials JSON-LD form. The `+ld+json` structured suffix is the
  registered form for JSON-LD.

# Acknowledgments

This document benefits from the SCITT Architecture {{RFC9943}}, the SCITT
Reference APIs {{I-D.ietf-scitt-scrapi}}, COSE Receipts
{{RFC9942}}, the RATS Architecture {{RFC9334}},
HTTP Message Signatures {{RFC9421}}, and the Web Bot Auth HTTP message
signature protocol {{I-D.meunier-webbotauth-httpsig-protocol}}.

--- back

# Examples

## Example: Three-register Sanctions Reconciliation

This example is illustrative and non-normative; register identifiers, values
and parties are fictitious, and no bilateral agreement with any named authority
is asserted or implied. Suppose a relying party requests reconciliation of the
predicate `sanctions:any-list-match` for subject identifier
`corp:EXAMPLE:0123456789` against three consolidated sanctions registers.

Each Bilateral Register Agreement permits the predicate. The projection
function emits identical Per-Register Claim Projections to all three
registers. All three return Partial Attestations with verdict `no-match`.

The Aggregation Subsystem operates in Homomorphic Aggregation Mode (all
three registers declare homomorphic capability). The Verdict Arithmetic is
disjunction. The Combined Verdict is `no-match`.

The Reconciliation Output is sealed against the current Policy-Version
Hash. The Settlement-Layer Ledger entry comprises:

- Entry Sequence Number: 42
- Reconciliation Hash: <32 bytes>
- Policy-Version Hash: <32 bytes>
- Addressed-Registers Identifier Set:
  `["EXAMPLE-REGISTER-A", "EXAMPLE-REGISTER-B", "EXAMPLE-REGISTER-C"]`
- Aggregation-Method Descriptor: "homomorphic-disjunction"
- Requester-Binding-Class Descriptor: "human-operator"
- Reconciliation Timestamp: 2026-04-27T19:47:14Z
- Prior-Entry Hash: <32 bytes>
- Self-Entry Hash: <32 bytes>

No register record content is stored on the Ledger.

## Example: Retroactive Re-evaluation

Continuing the illustrative example above: six weeks after that
reconciliation, EXAMPLE-REGISTER-A adds the subject to its list as part of a
new tranche. That register's Partial-Attestation endpoint, on next invocation,
returns verdict `match`.

The Retroactive Evaluation Subsystem detects the new Pattern-Library and
Policy-Version transition, re-invokes Partial Attestations on all
historical reconciliations addressing EXAMPLE-REGISTER-A under the superseded
Policy-Version Hash, identifies the material verdict change, and emits a
Sovereign Re-Notification through the Regulator Portal to the regulators
whose statutory-regulator-access scope intersects the changed
reconciliation. A new Reconciliation Output is appended to the Ledger
referencing the superseded one in its Source-Reconciliation-Output
Identifier field.

## Example: Agentic Principal Reconciliation

An autonomous agent requests reconciliation of `sanctions:any-list-match`
over HTTP, signing the request under HTTP Message Signatures {{RFC9421}} with
a key published in a Web Bot Auth signature-agent card. The reconciliation
server verifies the signature (Agent Friend-or-Foe Determination: the agent
carries a verifiable identity) but the Agent-IFF policy for the `sanctions:`
class requires an attributable principal for a decisive verdict.

The server therefore first performs an `agent:principal-binding-verifiable`
reconciliation with Subject Identifier set to the agent's key thumbprint and
Attested Value set to the asserted principal `org:ACME:operator:jdoe`,
addressing the ACME organisational directory register and the
credential-issuer status-list register. Both return `match`. The
Requester-Binding class is set to agent-verified with accountable principal
`org:ACME:operator:jdoe`, committed to the Policy-Version Hash, and only then
is the sanctions reconciliation performed with a decisive verdict binding. Had
either identity register returned `no-match` with axis
agent-impersonation-suspected, the sanctions reconciliation would have been
refused or downgraded to advisory per policy.

## Example: Divergent Agent-Action Reconciliation

This example is illustrative and non-normative. Capsule slots are those of
{{I-D.mih-sato-agent-accountability-composition}}; see {{composition}}.

An autonomous agent is authorised, by a signed CAN capsule, to read from a
named evaluation dataset and to write only to a sandboxed result store. During
execution the agent's actual conduct, attested by a WHAT capsule produced by
the execution environment, includes an outbound network connection to an
external host and a write outside the sandboxed store.

A relying party submits both capsules to ARP over the `agent:` predicate
branch with a shared subject digest computed over the action. ARP verifies
each capsule's signature, projects the authorised scope from the CAN capsule
and the actual scope from the WHAT capsule, and reconciles them. The scopes
diverge: the actual conduct exceeds the authorised scope. The Combined Verdict
is `no-match` with divergence axis agent-action-scope-divergence.

Because the Agent-IFF policy for this action class requires a decisive `match`
before the action is treated as authorised, the divergent verdict is available
as a refusal at decision time -- the reconciliation surfaces the excess while
the action can still be refused, rather than after the consequence. The
Reconciliation Output is sealed against the Policy-Version Hash and written to
the Settlement-Layer Ledger as hashes only, with requester-binding class
agent-verified and no register or capsule content disclosed.

# Composition with the SCITT Architecture {#composition-scitt}

The SCITT Architecture {{RFC9943}} provides notarisation
of supply-chain artefacts, including transparency receipts, transparent
statements, and registries. ARP composes with SCITT in four ways:

1. SCITT receipts MAY be the input claim to ARP. A claim referencing a
   SCITT-anchored artefact (its hash and its registration receipt) is
   reconciled across registers without disclosing the underlying artefact.

2. ARP Reconciliation Outputs MAY be notarised into SCITT registries as
   transparent statements, enabling SCITT-aware relying parties to verify
   the cross-sovereign reconciliation event in the same way they verify
   any other supply-chain claim. Registration and retrieval MAY use the
   SCITT Reference APIs {{I-D.ietf-scitt-scrapi}}.

3. The SCITT Architecture's Identity Manager and Issuer roles map cleanly
   to the Bilateral Register Agreement structure: each Sovereign Register
   acts as a SCITT Issuer for a constrained predicate set, and the
   reconciliation server acts as a SCITT Aggregator across multiple
   Issuers.

4. ARP Hash-Linkage Aggregation emits its Merkle commitment as COSE Receipts
   {{RFC9942}}, the same inclusion-proof format
   SCITT uses for transparency receipts, so a single verifier library checks
   both.

# Composition with the RATS Architecture

The RATS Architecture {{RFC9334}} provides remote-attestation procedures
for compute-substrate trust. ARP composes with RATS in two ways:

1. The Adversarial Pre-Transmission Test runs inside a confidential
   computing boundary attested under RATS. The reconciliation server's
   integrity MAY be verified by relying parties through standard RATS
   verification flows.

2. Compute-attestation reconciliation across heterogeneous TEE / CC
   providers is the natural specialisation of ARP to the RATS evidence
   class. That specialisation is outside the scope of this document.

# Composition with Agent-Action Accountability Capsules {#composition}

{{I-D.mih-sato-agent-accountability-composition}} models accountable
autonomous action as a set of heterogeneous, independently signed attestation
capsules, and defines the capsule slots and their composition. This document
does not restate that model; the slot definitions, their semantics and their
composition rules are those of
{{I-D.mih-sato-agent-accountability-composition}}, and this appendix uses them
as defined there.

What this appendix adds is reconciliation across those capsules. Each capsule
may be signed by a different party, under a different signing chain, with a
different payload schema -- the same non-reconcilable-outputs problem this
document addresses for sovereign registers, arising in the agent-action
domain. What the capsules share is the action serialisation over which the
subject digest is computed.

ARP composes such capsules without requiring them to share a producer, a
schema, or a signing chain. The capsules are bound to a common action through a
shared subject digest, computed as the SHA-256 of the JSON
Canonicalization Scheme serialisation of the action being attested:

~~~
subject_digest = SHA-256(JCS(action))
~~~

where JCS is the JSON Canonicalization Scheme specified in {{RFC8785}}, and
`action` is one action object serialised once. All capsules composed under this
appendix MUST be computed over that same serialised action object.
`subject_digest` is a join key across capsules over a shared serialisation; it
is NOT a correlation key across independently produced descriptions of an act,
and MUST NOT be used as one. See {{subject-digest-scope}}.

The shared serialisation is established once, by the party that authorises the
action, and is echoed verbatim by every later attester. An attester that
re-serialises its own account of the action MUST NOT compute `subject_digest`
over that account; it MUST carry the serialisation it received. This is what
makes the digest a join key here rather than a correlation across independent
descriptions, and a profile that cannot guarantee it is in the second case of
{{subject-digest-scope}} rather than the first.
Implementations MUST use {{RFC8785}} and MUST NOT substitute another
canonicalisation. In particular, {{RFC8785}} does not apply Unicode
normalisation. An implementation that normalises before serialising therefore
computes a different subject digest from a conforming implementation for any
input carrying a member name or string value that is not already in the
normalisation form it applies -- silently, since both parties obtain a
well-formed digest.

Measured against a published agent-action conformance corpus: this
construction and a deployed {{RFC8785}} profile agreed on all twenty-two
pinned vectors of that corpus. The agreement depends on both parties having
selected {{RFC8785}}, which the normative reference above makes an obligation.

The capsules may disagree about the action -- that disagreement is the finding
ARP exists to surface -- but they do not disagree about which action is under
attestation, because they carry the same action serialisation. Each capsule's
own account travels in its payload, committed by its receipt-payload digest
below, not in `subject_digest`.

Two further profile-tagged digests, defined by this
document rather than by {{I-D.mih-sato-agent-accountability-composition}},
position each capsule for reconciliation: an authority-reference digest
committing to the authorising instrument (tagged transparency where it is the SHA-256 of a COSE_Sign1
transparency receipt, or offline where it is the SHA-256 of the {{RFC8785}}
serialisation of an offline receipt payload), and a receipt-payload digest committing to the
capsule's own payload.

Each capsule is admitted to ARP as a Partial-Attestation source keyed on the
shared subject digest, in the slot
{{I-D.mih-sato-agent-accountability-composition}} assigns it. The
reconciliation server verifies each capsule's
signature under its own trust anchor, projects each into the `agent:` predicate
branch, and aggregates the per-capsule verdicts under the Verdict Arithmetic
declared for the action class -- yielding a single, producer-agnostic Combined
Verdict over an action whose constituent attestations were never designed to
interoperate.

Where the authorised-scope capsule and the actual-conduct capsule reconcile to
divergent scopes, the Combined Verdict is `no-match` with divergence axis
agent-action-scope-divergence; the divergence is a refusable control input,
produced at decision time and sealed to the Settlement-Layer Ledger as hashes
only.

This composition is the agent-action specialisation of the mechanism ARP
applies to sovereign registers: reconcile heterogeneous authoritative outputs
over a shared subject into one deterministic verdict, disclose only verdict and
divergence, and seal against a Policy-Version Hash. It allows a relying party
to reconcile what an agent was permitted to do against what it did, at the
moment of action, across attestations no single party produced.

## The two digest constructions are distinct {#construction-distinctness}

This document defines two digest constructions over JSON, for two different
purposes, and they are NOT interchangeable:

Claim Hash:
: SHA-256 over the Canonical Claim serialisation of {{terminology}} together
  with the Deployment Blinding Value of {{sealing}}. Its
  purpose is to index a claim in the Settlement-Layer Ledger. It applies
  Unicode Normalization Form C.

subject_digest:
: SHA-256 over the {{RFC8785}} serialisation of an action, per
  {{composition}}. It is a CONTENT digest: it commits to the action object as
  serialised, and any difference in the serialised bytes yields a different
  digest except with negligible probability. {{RFC8785}} does not normalise.

An implementation that substitutes one for the other MUST be assumed to
produce incorrect correlations. The failure is silent: both constructions
return a well-formed 32-octet digest for any input, so a substitution surfaces
as a correlation that does not occur, or as two distinct actions correlating to
one subject, rather than as an error.

Two cases are worse than a mere difference of bytes, because the substitution
produces a COLLISION rather than a mismatch. Under the Claim Hash construction,
which normalises, an input in Normalization Form D and the same input in
Normalization Form C yield the SAME digest; so do U+212B ANGSTROM SIGN and
U+00C5 LATIN CAPITAL LETTER A WITH RING ABOVE. Under the `subject_digest`
construction, which does not normalise, all four are distinct. An implementer
who reuses the Claim Hash where a subject digest is required will therefore
correlate two actions that a conforming implementation keeps apart. Both cases
were observed against a published conformance corpus.

Accordingly:

* An implementation MUST NOT use the Claim Hash construction where
  `subject_digest` is specified, or the reverse.
* Where a digest is carried on the wire for correlation, the producer MUST
  identify the construction used, by an identifier that commits to the
  declared canonicalisation parameters -- member-sort code unit,
  normalisation, number rendering, absent-member handling and hash algorithm
  -- so that a consumer can determine compatibility rather than assume it.
  Such an identifier MUST NOT commit to facts about a specification that do
  not affect the serialised bytes, so that two implementations producing
  identical bytes share an identifier.
  {{I-D.mih-sokolov-scitt-payload-binding}} expresses a compatible rule
  statement-side.

* Where the correlation digest is computed over a TYPED action object whose
  type declares required material fields, the producer MUST validate the
  object against a pinned definition of that type before emitting a
  correlation identifier for it, and MUST NOT emit one where validation
  fails. A digest is well-formed over any object, including one that omits
  fields the type requires; emitting an identifier in that case mints a join
  key for an action the identifier does not fully describe, which is the
  condition a relying party has no way to detect downstream. Validation against a pinned type
  definition is therefore required before emission.

### What a content digest does and does not establish {#subject-digest-scope}

`subject_digest` is collision-resistant over content: two actions whose
serialisations differ in any byte produce different digests except with
negligible probability, so a receipt bound to one action does not bind
another. That property is what makes it usable as a join key
between capsules computed over the SAME serialised action.

It does not, and cannot, establish that two INDEPENDENTLY DESCRIBED accounts of
one act correlate. Where an action type declares optional members, two
conforming producers describing the same act may legitimately differ on whether
an optional member is present, and their subject digests then differ. Stability
under permitted variation and collision resistance over content are
contradictory requirements, and no single digest satisfies both.

This is measured, not assumed. Five action objects,
each a conforming instance of one registered action type and each accepted by
that type's reference issuer, differing only in content the type declares
OPTIONAL, produced five distinct subject digests. The divergence appeared at
the first optional member and did not require any nested reference or unusual
value.

Accordingly:

* A profile MAY key capsules on `subject_digest` where those capsules are
  computed over the same serialised action object. {{composition}} is such a
  profile: the capsules it composes share one action serialisation.
* A profile that requires correlation across independently produced
  descriptions of one act MUST NOT rely on `subject_digest` alone. It MUST
  either pin the exact member set over which the digest is computed, so that
  permitted variation cannot enter it, or correlate on a material identifier
  the action type declares for that purpose. Where the action type declares
  such an identifier -- for example a payment instruction identifier -- joining
  on that field is the more robust of the two, because it does not require
  every producer to agree on a serialisation before they can agree that they
  are describing the same act.

A specification that describes a content digest as a correlation key without
stating which of the two preceding cases it relies on invites an implementer to
assume a stability property the construction does not have. The resulting
failure is a correlation that silently does not occur.

# Document History

RFC Editor: please remove this section before publication.

## Since draft-hillier-scitt-arp-02

This revision answers a review of -02 on the SCITT list. Of its five asks, three
are adopted as put, one is adopted in its goal and not in its mechanism, and one
is declined for now with a reason.

{{scrapi-binding}} is new and normative. -02 composed with the SCITT Reference
APIs permissively -- Reconciliation Outputs MAY be notarised, registration MAY
use the APIs -- which is a permission and not a binding: two implementations
could both conform to -02 and fail to interoperate against the same Transparency
Service. The section now fixes the registration endpoint, the COSE_Sign1 framing
and content type, receipt validation, and the asynchronous registration path.
The asynchronous case is stated as a requirement because it is the most likely
divergence between conforming implementations: a 202 Accepted with polling
against 204 No Content is not the same code path as a 201 Created, and an
implementer who codes only the latter interoperates with some Transparency
Services and not others.

The review also asked for a standard retrieval path keyed on the Policy-Version
Hash. That is not specified here, because {{I-D.ietf-scitt-scrapi}} defines
retrieval by EntryID and defines no query surface at all; a binding that
specified one would specify an endpoint that does not exist. The goal --
preventing policy equivocation over time -- is met instead by requiring the
Policy-Version Hash in the protected header of the Signed Statement, so that it
is covered by the Receipt. A relying party therefore establishes the policy
version by verification rather than by lookup, which is the stronger property:
an index can be wrong, or can present different results to different relying
parties, and a signed protected header cannot.

{{format-profiles}} is new. -02 specified the controlled projection function
over an abstract Predicate Taxonomy without saying how an implementer determines
what a given register can answer. Four profiles are defined -- {{BODS}},
{{RFC6350}} with {{W3C-ORG}}, {{UNCEFACT}} with {{WCO-DM}}, and consolidated
sanctions list formats. Profiles constrain predicate expression only and are
prohibited from introducing any means of transporting register records, which
would defeat the property the protocol exists to provide.

{{source-versioning}} is new, and is the substantive addition rather than the
largest one. A designation verdict against a consolidated sanctions list is
meaningful only relative to the state of that list, and consolidated lists are
republished on a cadence and distributed as deltas. -02 could therefore record
that a historical Combined Verdict had changed but could not attribute the
change: a verdict that flipped because the policy changed and one that flipped
because the list changed were indistinguishable, and Sovereign Re-Notification
reported both as policy changes. Partial Attestations now carry a Source-Data
Version Identifier under signature, Retroactive Evaluation must distinguish the
two causes, and where it cannot it must report attribution-indeterminate rather
than attribute the change to policy. A list-state identifier is a property of a
published corpus and not a register record, so this does not weaken minimum
disclosure.

Three structural gaps predating this revision are closed, because the new
material could not be made testable without them. {{reconciliation-output}}
enumerates the Reconciliation Output, which no earlier revision did although
both the Partial Attestation and the Ledger entry were enumerated; Reconciliation
Hash and Combined Verdict are now defined in {{terminology}}, the former having
been used inside the bit-for-bit determinism requirement while undefined; and
the Server-Recorded Divergence-Axis Set is a set, since a reconciliation may be
qualified on more than one axis and a single-valued encoding would force a
silent choice.

{{verdict-retyping}} is new. Where a narrowing means a register's answer does
not bear on the claim as asked, that register's contribution is re-typed before
aggregation rather than the Combined Verdict being overridden after it, so the
Verdict Arithmetic declared in the Applicable-Regimes Set is never displaced. A
match found at any depth still establishes an existential closure predicate and
is not re-typed.

{{post-seal}} is new. Notarisation outcomes and retroactive attribution failures
arise after a Reconciliation Output is sealed and so can be carried neither in a
Partial Attestation nor in the Output; they are Post-Seal Evaluation Qualifiers
recorded in a separate signed record referencing the Reconciliation Hash, and
are expressly not Divergence Axes.

New Divergence Axis values: register-threshold-divergence,
declared-not-determined and source-version-skew. New COSE header parameter
arp-source-data-version, carrying a set so that a register consulting several
lists can denote the state of each. arp-bilateral-agreement-hash now always
carries a sorted array, of one member on a Partial Attestation and one per
addressed register on a Sealing Signature, so that a decoder never has to infer
the type from context. New IANA registries for Register Data-Format Profile
identifiers and for Post-Seal Evaluation Qualifiers.
{{I-D.ietf-scitt-scrapi}} moves from informative to normative, because
{{scrapi-binding}} imposes requirements that cannot be met without it.

A role-by-role walkthrough of the whole pipeline -- requester, agent,
reconciliation server, register operator, relying party, Transparency Service,
regulator, retroactive subsystem and IANA expert -- was run against this
revision and found a further class of defect that no earlier review had reached:
requirements addressed to an actor that does not hold the inputs they name.
Those are closed here, and most of them predate -02.

{{projection}} now enumerates the Per-Register Claim Projection. It is the only
structure a sovereign register receives and it was the sole major structure in
the protocol without a field list, which made the register role unimplementable.
The register echoes the Policy-Version Hash rather than computing it, and the
server MUST now send one Policy-Version Hash to every addressed register and
verify each echo -- without which the per-register signatures over it, the only
independent corroboration the protocol has, were discarded at aggregation.

{{sealing-key-discovery}} is new. -02 and the earlier -03 text told a relying
party to verify a Sealing Signature whose key it had no way to obtain: it holds
hashes of bilateral agreements it is not party to. Sealing keys are now
published at a well-known location on a declared authority origin, mirroring how
{{I-D.ietf-scitt-scrapi}} treats Transparency Service keys.

{{verdict-arithmetic}} is new. Every operator is now given its result for every
combination of contribution values, and whether it admits partial-match, on
which {{verdict-retyping}} turns. -02 delegated combination to an operator it
named but never defined, so two conforming implementations could produce
different Combined Verdicts from identical inputs while the determinism
requirement demanded they not.

{{no-answer}} is new. A register may fail to answer in five distinct ways and no
earlier revision defined an outcome for any of them; dropping the register
silently produces exactly the addressed-register-cherry-picking the adversarial
test exists to detect. A reconciliation with any non-answering register can no
longer reach a decisive Combined Verdict.

The Reconciliation Output gains the Claim Hash, a timestamp, the Verdict
Arithmetic, the Sealing-Key Identifier, per-register attested and effective
verdicts with the re-typing ground, per-register echoed Policy-Version Hashes,
and register attribution on the server-recorded divergence axes. Without the
Claim Hash a relying party received a verdict with nothing to attribute it to,
and the retroactive subsystem had no key to select on although the Claim Hash
was already declared its key. The Settlement-Layer Ledger gains the Claim Hash,
a Notarisation Record and a link to Post-Seal Evaluation Records, and now
exposes READ as well as APPEND -- the Regulator Portal, retroactive evaluation
and the chain-invariant check all require reads that "only APPEND" forbade.
Ledger entries are now signed, because prior-entry hashes prove that nothing was
removed from a chain and not that only one chain exists.

Retroactive Evaluation now triggers on a new Source-Data Version. It previously
triggered only on a Pattern Library or Policy Version change, so a sanctions
list republication -- the case {{source-versioning}} was written for -- fired
nothing. A material change now includes a transition between decisive values: a
no-match becoming a match is the case the motivating domain cares most about,
and the earlier definition omitted it.

Homomorphic Aggregation Mode is now available only where no contribution
requires re-typing, since re-typing reads per-register verdicts in the clear.
The Pattern-Library Version Identifier is no longer bound as authenticated
additional data: registers are never told the pattern-library version, so
binding it either failed universally or was supplied by the party that chose it.
The Reconciliation Hash is taken over deterministic CBOR rather than
{{RFC8785}}, because the Output is CBOR and several fields are byte strings for
which JSON has no type. Regulator Portal scope is the intersection across
agreements rather than the union, which had let one permissive agreement widen
access to a stricter register's reconciliations.

The Freshness Timestamp is now enumerated before the signature line in
{{partial-attestation}} and is therefore covered by it. It was listed after the
signature in earlier revisions, and both replay defence and the new
freshness-versus-skew distinction depend on it being signed.

Not adopted: a statement that a reference implementation is forthcoming. It does
not exist yet, and a draft should not carry a claim about an artefact a reader
cannot check. When it is published it will be cited by repository and commit
alongside the conformance vectors it is checked against.

## Since draft-hillier-scitt-arp-01

This revision closes canonicalisation ambiguities identified by running an
implementation of -01 against two published conformance corpora -- the EMILIA
clean-room `frozen-v1` agent-action corpus and the Noa AI-agent-receipt corpus
-- states the role of the Appendix D subject digest explicitly, and corrects a
number of requirements that were unsatisfiable, untestable or out of scope as
written in -01.
The harness and its machine-readable results were posted to the SCITT mailing
list.

- {{RFC8785}} is now a NORMATIVE reference. -01 named JCS in {{composition}}
  without identifying which JCS; the string "8785" did not occur in -01 at all.
  Measured agreement with a deployed profile on 22 of 22 pinned vectors
  depended on both parties having independently selected {{RFC8785}}. It is now
  an obligation rather than a coincidence.
- The Canonical Claim in {{terminology}} now pins its member-sort code unit to
  UTF-16, per Section 3.2.3 of {{RFC8785}}. -01 said "lexicographic sorting of
  object keys", which does not determine the ordering of member names outside
  the Basic Multilingual Plane. Measured as a divergence on 1 of 22 pinned
  vectors.
- Number rendering now cites Section 3.2.2.3 of {{RFC8785}}. -01 cited
  "canonical JSON {{RFC8259}} number rendering"; {{RFC8259}} defines no
  canonical number rendering, and was an informative reference in -01.
- "Stripping of undefined values" is replaced by a statement about absent
  members, JSON having no undefined value to strip.
- New {{construction-distinctness}} states that the Claim Hash and
  `subject_digest` are distinct constructions that MUST NOT be substituted for
  one another, and records the two observed COLLISION cases (Normalization Form
  D against Form C, and U+212B against U+00C5) in which a substitution fails
  silently rather than visibly.
- New {{subject-digest-scope}} states what `subject_digest` is and what it is
  not, which -01 left to be inferred. `subject_digest` is a content digest:
  collision-resistant over content, and therefore NOT stable under the
  variation an action type permits. Measured:
  five conforming instances of one registered action type, each accepted by
  that type's reference issuer and differing only in content the type declares
  OPTIONAL, produced five distinct subject digests. The section now separates
  the case the construction supports -- capsules over one shared serialisation,
  which is what {{composition}} composes -- from the case it does not, and
  requires a profile needing the latter to pin its member set or to join on a
  material identifier the action type declares. It also forbids describing a
  content digest as a correlation key without saying which case is relied on.
- The order of canonicalisation operations in {{terminology}} is now normative.
  Normalization Form C is applied BEFORE the member sort. The two do not
  commute: for an object whose member names are U+0041 U+030A and "B",
  normalising first and sorting first produce different Claim Hashes. -01 gave
  the operations as an unordered list.
- {{I-D.mih-sato-agent-accountability-composition}} remains an informative reference.
  {{composition}} composes over the capsule slots it defines and would cite it
  normatively, but it is an individual draft; making it normative now would
  create a publication dependency. The same applies to
  {{I-D.mih-sokolov-scitt-payload-binding}}. The status of both references
  will be revisited as those documents progress.
- {{construction-distinctness}} requires that a correlation digest carried on
  the wire identify its construction, and requires that such an identifier not
  commit to facts which do not affect the serialised bytes, so that two
  implementations producing identical bytes share an identifier.
- {{construction-distinctness}} additionally requires that a correlation
  identifier over a typed action object be emitted only after the object
  validates against a pinned definition of its type.

Reference and source corrections in this revision:

- The SCITT Architecture reference is now {{RFC9943}} and the COSE Merkle tree
  proofs reference is now {{RFC9942}}. -01 cited both as Internet-Drafts; both
  have since been published as RFCs.
- The Web Bot Auth architecture reference is replaced. -01 cited
  draft-meunier-web-bot-auth-architecture, which has been replaced by
  {{I-D.meunier-webbotauth-httpsig-protocol}}.
  {{I-D.meunier-webbotauth-registry}}, which defines the signature-agent card,
  is retained. {{I-D.meunier-webbotauth-httpsig-directory}} is
  added, because the card is resolved through the directory the
  Signature-Agent header names and -01 cited no document for that step.
- The document date, RFCXML version and submission type are declared in the
  source, and `keyword` is a single YAML sequence.
- A note to the RFC Editor records the {{RFC8785}} downref explicitly, so that
  it can be called out at IETF Last Call per {{RFC8067}} rather than found
  there.
- {{composition}} now REQUIRES that all composed capsules carry one shared
  action serialisation, established by the authorising party and echoed
  verbatim by later attesters, and states that a capsule's own account of the
  action travels in its payload rather than in `subject_digest`. -01 left the
  shared-serialisation condition implicit, which is the condition the digest
  depends on.
- The determinism requirement is scoped to the Reconciliation Output and to
  the Claim Hash, Reconciliation Hash and Policy-Version Hash. -01 required
  bit-for-bit identical Settlement-Layer Ledger entries, which the entry's own
  sequence number, timestamp and prior-entry hash make unsatisfiable.
- The Claim Hash is pinned to SHA-256 in {{terminology}}. -01 named the
  algorithm only in an appendix, leaving a parameter the construction
  identifier is required to commit to unstated in the normative body.
- Claim equality is stated over canonical field values, and declared array
  order is significant. -01 required semantically-equivalent claims to hash
  alike without defining semantic equivalence, which no implementer could
  test.
- The Per-Register Claim Projection is defined as the nearest permitted
  ancestor predicate rather than a greatest lower bound, which the Predicate
  Taxonomy -- a tree -- does not have, and the projection function now fails
  explicitly on an ambiguous or unreachable walk rather than choosing.
- The Settlement-Layer Ledger entry carries an OPTIONAL
  Source-Reconciliation-Output Identifier, which the retroactive
  re-evaluation example already relied on and the entry's closed field list
  did not admit.
- `freshness-stale` is added to the Divergence-Axis controlled set, and
  server-recorded axes are stated to travel in the Reconciliation Output
  rather than in a register's signed payload, which the reconciliation server
  cannot modify.
- COSE header labels are requested from IANA rather than asserted as a
  vendor-private range, and an IANA registry is requested for Divergence-Axis
  values.
- The examples are de-identified. Register identifiers are illustrative and no
  bilateral agreement with any named authority is asserted.
- Two independent implementations of an {{RFC8785}}-based digest
  construction, sharing no source, were measured as agreeing byte-for-byte on
  24 generated inputs selected to exercise absent-field normalisation, arrays,
  string escaping, UTF-16 member sorting and both integer bounds. That is the
  outcome {{construction-distinctness}} argues for: one identified
  construction per digest role, committing to the parameters that affect the
  serialised bytes and to nothing else.

## Since draft-hillier-scitt-arp-00

- Added a fourth motivating deficiency (unverifiable requester identity in an
  agentic setting) to the Introduction.

- Added a new pipeline subsystem, Requester Identity Binding and Agent
  Friend-or-Foe (IFF) Gate, and renumbered the pipeline to twelve subsystems.

- Added the `agent:` predicate branch, a new Agentic Principal Reconciliation
  section, and the divergence axes agent-principal-unverifiable,
  agent-credential-absent, and agent-impersonation-suspected.

- Added Requester-Binding to the Policy-Version Hash commitment and a
  requester-binding-class descriptor to the Settlement-Layer Ledger entry.

- Bound ARP to HTTP Message Signatures {{RFC9421}} and Web Bot Auth for signed
  agent requests, and added an Agent Impersonation security consideration.

- Replaced the stale scitt-receipts reference with COSE Receipts
  {{RFC9942}} and added the SCITT Reference APIs
  {{I-D.ietf-scitt-scrapi}}; Hash-Linkage Aggregation now emits COSE Receipts.

- Described the Evidentiary Provenance Manifest's optional carriage as a
  COSE-enveloped Verified-Principal-Credential evidence container.

- Extended Retroactive Evaluation to treat credential revocation as a material
  change, and added a new IANA header label and worked agentic example.

- Added the motivating agentic-containment failure class to the Introduction
  and framed real-time reconciliation of claimed-versus-actual conduct as a
  first-class property, distinct from after-the-fact forensic reconstruction.

- Added a Composition with Agent-Action Accountability Capsules section
  reconciling heterogeneous CAN/WHO/WHAT/AUDIT capsules
  {{I-D.mih-sato-agent-accountability-composition}} over a shared subject digest into a
  producer-agnostic verdict, with a worked divergent agent-action example.

- Added the agent-action-scope-divergence divergence axis.

- Removed two unused informative references (JWS, JWT).
