---
title: Attestation Reconciliation Protocol
abbrev: ARP
docname: draft-hillier-scitt-arp-02
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
  UAX15:
    title: "Unicode Standard Annex #15: Unicode Normalization Forms"
    target: https://www.unicode.org/reports/tr15/
    author:
      - org: The Unicode Consortium
    date: 2023

informative:
  RFC8259:        # JSON
  RFC8067:        # Updating When Standards Track Documents May Refer Normatively to Documents at a Lower Level
  I-D.mih-sato-agent-accountability-composition:
  I-D.mih-sokolov-scitt-payload-binding:
  I-D.ietf-scitt-scrapi:
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
revision adds agentic-principal reconciliation, requester identity binding,
alignment with HTTP Message Signatures and COSE Receipts, and composition of
heterogeneous agent-action accountability attestations into a single
producer-agnostic reconciled verdict evaluated at decision time.

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
  payload SHALL disclose only a Reconciliation-Verdict field and an
  OPTIONAL Divergence-Axis field; it SHALL NOT disclose any register
  record.

Divergence Axis:
: A controlled descriptor identifying the structural reason for a non-match
  verdict, drawn from a controlled set including identity-mismatch,
  jurisdictional-scope-mismatch, temporal-mismatch,
  ownership-threshold-mismatch, sanctions-list-match, register-record-absent,
  claim-predicate-unsupported,
  claim-projection-narrowed-beyond-attestation-scope,
  agent-principal-unverifiable, agent-credential-absent,
  agent-impersonation-suspected, agent-action-scope-divergence (the
  authorised scope attested for an agent action and the actual conduct
  attested for it do not reconcile), and freshness-stale. A Divergence Axis
  recorded by the reconciliation server rather than by a register --
  freshness-stale is the only such value defined here -- is carried in the
  Reconciliation Output, not in the register's signed Partial-Attestation
  payload.

Reconciliation Output:
: A data structure aggregating Partial Attestations from a single
  reconciliation event, sealed against a Policy-Version Hash.

Verdict Arithmetic:
: The operator governing how per-register verdicts combine into the Combined
  Verdict, drawn from a controlled set including conjunction, disjunction,
  threshold-count, and source-class-quorum.

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

# Architecture

ARP comprises twelve subsystems arranged as a deterministic pipeline:

1. Canonical Claim Ingestion
2. Requester Identity Binding and Agent Friend-or-Foe Gate
3. Adversarial Pre-Transmission Test
4. Per-Register Projection Function
5. Per-Register Encryption
6. Partial-Attestation Reception
7. Aggregation (Homomorphic or Hash-Linkage)
8. Policy-Version-Hash Sealing
9. Settlement-Layer Ledger Write
10. Regulator Portal
11. Retroactive Evaluation
12. Cryptographic-Primitive-Upgrade Path

Given an identical Canonical Claim, an identical Requester-Binding, an
identical Addressed-Registers Identifier Set, identical
Bilateral-Register-Agreement Hashes for the addressed registers, an identical
Pattern-Library Version Identifier, and an identical Policy-Version
Identifier, the system MUST produce bit-for-bit identical Reconciliation
Outputs, and identical Claim Hash, Reconciliation Hash and Policy-Version Hash
values in the corresponding Settlement-Layer Ledger entries. The per-event
fields of a Ledger entry -- Entry Sequence Number, Reconciliation Timestamp,
Prior-Entry Hash and Self-Entry Hash -- are position-dependent by construction
and are outside this requirement.

## Canonical Claim Ingestion

A Canonical Claim comprises:

- Subject Identifier
- Predicate (drawn from the controlled Predicate Taxonomy)
- Attested Value (in the canonical type for the Predicate)
- Applicable-Regimes Set
- Evidentiary Provenance Manifest
- Claim Timestamp (RFC 3339 UTC)
- Claim Hash (SHA-256 over the canonical serialisation)

Two claims whose canonical field values are identical MUST produce the same
canonical form and the same Claim Hash. Declared array order is significant;
claims differing only in declared array order are distinct claims. The Claim Hash is the index on the
Settlement-Layer Ledger and the key for retroactive re-evaluation.

The Evidentiary Provenance Manifest MAY be carried in any COSE-enveloped
evidence structure; the container form is an interop convenience and does not
alter the Claim Hash,
which is computed over the canonical claim fields alone.

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

The Subsystem emits either a Pass result or a Remediation Advisory. The
Per-Register Encryption Subsystem MUST architecturally withhold external
transmission until a Pass result has been emitted or until an authorised
operator has explicitly overridden the outcome.

## Per-Register Projection Function

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

## Per-Register Encryption

Each Per-Register Claim Projection MUST be encrypted under the addressed
register's public-key material declared in the Bilateral Register Agreement.
The encryption operation MUST bind the Bilateral-Register-Agreement Hash and
the Pattern-Library Version Identifier into the ciphertext as authenticated
additional data, such that a register attempting to decrypt under a stale
Bilateral-Register-Agreement Hash or Pattern-Library Version Identifier
fails at the authenticated-additional-data verification step.

## Partial Attestation Reception

A Partial Attestation comprises:

- Register Identifier
- Reconciliation-Verdict Field (`match`, `no-match`, `partial-match`, or `indeterminate`)
- OPTIONAL Divergence-Axis Field
- Bilateral-Register-Agreement Hash
- Policy-Version Hash
- Cryptographic Signature over the canonical payload of the foregoing
- Freshness Timestamp

The Partial Attestation payload SHALL NOT contain any register-record field,
any pre-image of the register record, or any field beyond those enumerated.
Restricting the Partial-Attestation payload to verdict and divergence-axis
fields is the mechanism by which ARP limits raw-record disclosure. Residual
inference channels are discussed in {{side-channel}}.

## Aggregation

Where every addressed register declares Homomorphic capability, the
aggregation subsystem operates in Homomorphic Aggregation Mode. Per-register
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

## Policy-Version-Hash Sealing

The Policy-Version Hash MUST commit to:

1. Reconciliation rules
2. Threshold parameters
3. Pattern-Library Version Identifier
4. Applicable-Regimes precedence
5. Verdict-Arithmetic selection
6. Agent-IFF policy identifier and the Requester-Binding
7. Bilateral-Register-Agreement Hashes of the addressed registers

The Policy-Version Hash MUST be reconstructible under audit from a
canonical policy state persisted in a policy-epoch store.

## Settlement-Layer Ledger

Each Settlement-Layer Ledger entry comprises only:

- Entry Sequence Number (monotonically increasing)
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

The Ledger MUST NOT store Canonical-Claim content, register records,
Partial-Attestation payloads, or any principal identifier in the clear; the
requester's accountable principal is committed only through the Policy-Version
Hash. The append-only constraint MUST be enforced at the storage interface
layer; the Ledger interface MUST expose only an APPEND operation, with no
UPDATE or DELETE operation exposed or implemented.

The Ledger MAY be distributed across a plurality of per-jurisdiction
secondary stores under synchronous replication, each operated under the
data-residency constraints of its host jurisdiction. The append-only
derivation-chain invariant -- that every entry's Prior-Entry Hash equals the
Self-Entry Hash of the immediately preceding entry -- MUST be preserved
across all secondary stores.

## Regulator Portal

The Regulator Portal Subsystem authenticates a sovereign regulator's
jurisdictional credentials against a regulator-identity-provider trust
anchor declared in at least one Bilateral Register Agreement. It restricts
returned fields to those within the regulator's statutory scope as declared
in the statutory-regulator-access scope of the Bilateral Register
Agreements of the addressed registers. The scope restriction is computed
as the union of per-agreement permitted-read-predicates entries scoped to
the regulator's jurisdiction, intersected with the regulator's requested
field set. Each access MUST be recorded in an append-only subpoena-grade
audit trail.

## Retroactive Evaluation

Upon publication of an updated Pattern Library or an updated Policy
Version, the Retroactive Evaluation Subsystem MUST execute a deterministic
re-application of the updated policy state to retained reconciliation
metadata of historical Reconciliation Outputs sealed against a superseded
Policy-Version Hash. Where permissible under the applicable Bilateral
Register Agreements, partial attestations MAY be re-invoked.

The retroactive evaluation MUST be executable without re-negotiation of any
Bilateral Register Agreement. A material change in a historical Combined
Verdict -- defined as any transition into or out of a decisive verdict
value (the decisive values being `match` and `no-match`) -- MUST trigger a
Sovereign Re-Notification through the Regulator Portal. Revocation of a
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

# Encoding

## CBOR-COSE Encoding

The mandatory-to-implement encoding for ARP messages on the wire is CBOR with
COSE {{RFC9052}} {{RFC9053}} envelopes. COSE_Sign1 is used for both Partial
Attestations and the Sealing Signature. The protected header MUST include the
Bilateral-Register-Agreement Hash and Policy-Version Hash as COSE header
parameters registered per {{iana}}. Pending registration,
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

## Verifiable Credentials Interop

A Reconciliation Output MAY be additionally serialised as a JSON-LD
document conforming to the W3C Verifiable Credentials Data Model
{{W3C-VC-DM-2.0}}, with the Reconciliation Hash, Addressed-Registers
Identifier Set, Bilateral-Register-Agreement Hash Set,
Requester-Binding-Class, and Policy-Version Hash included as credential
subject fields. The COSE_Sign1 envelope is the normative form; the
Verifiable Credential serialisation is an interop convenience for relying
parties operating in W3C VC ecosystems.

# Security Considerations

## Service-Operator Containment

The reconciliation server operates under a service-operator entity
standing in bilateral contractual relationship with each Register
Operator. The service-operator entity MUST be architecturally prohibited
from observing any register record or any Partial-Attestation payload
beyond the verdict and divergence-axis fields. The service-operator entity
MUST be structurally incapable of disclosing any register record
irrespective of internal operator action.

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

## Replay Defence

Each Partial Attestation MUST carry a Freshness Timestamp. The
reconciliation server MUST verify the Freshness Timestamp against a
freshness window declared in the Bilateral Register Agreement. Stale
Partial Attestations MUST be rejected, and the rejection MUST be recorded in
the Reconciliation Output with the `freshness-stale` divergence axis. A signed agent request under {{RFC9421}} MUST additionally carry a
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

- Five COSE header parameters in the COSE Header Parameters registry, values
  to be assigned by IANA:
  - `arp-bilateral-agreement-hash` (value TBD)
  - `arp-policy-version-hash` (value TBD)
  - `arp-pattern-library-hash` (value TBD)
  - `arp-divergence-axis` (value TBD)
  - `arp-requester-binding-class` (value TBD)

- A registry of ARP Divergence-Axis values, registration policy Specification
  Required, initially containing the descriptors enumerated in
  {{terminology}} together with `freshness-stale`.

- A media type `application/arp-reconciliation-output+cbor` for the
  CBOR-encoded Reconciliation Output.

- A media type `application/arp-reconciliation-output+json` for the
  Verifiable Credentials JSON-LD form.

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

# Composition with the SCITT Architecture

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
: SHA-256 over the Canonical Claim serialisation of {{terminology}}. Its
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
