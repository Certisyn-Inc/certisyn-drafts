---
title: Attestation Reconciliation Protocol
abbrev: ARP
docname: draft-hillier-scitt-arp-04
date: 2026-08-13
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
pi: [toc, sortrefs, symrefs, tocdepth="4"]

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
  RFC3339:        # date/time on the wire
  RFC7638:        # JWK Thumbprint
  RFC3986:        # URI generic syntax, for target normalisation
  RFC6454:        # The Web Origin Concept, for the Authority Origin form
  RFC9530:        # Digest Fields, for Content-Digest
  RFC8615:        # Well-Known URIs, under which this document registers
  RFC6838:        # Media type registration procedures
  RFC6839:        # Structured syntax suffixes
  RFC8949:        # CBOR, incl. the core deterministic encoding requirements
  RFC6234:        # SHA-256, used by every digest this document defines
  RFC2104:        # HMAC, used by the Reconstruction Proof of {{audit-path}}
  RFC9052:
  RFC9053:
  RFC9334:        # RATS Architecture
  RFC9421:        # HTTP Message Signatures
  RFC8785:        # JSON Canonicalization Scheme (JCS)
  RFC9943:        # SCITT Architecture (was I-D.ietf-scitt-architecture)
  RFC9942:        # COSE Receipts (was I-D.ietf-cose-merkle-tree-proofs)
  I-D.ietf-scitt-scrapi:   # normative: {{scrapi-binding}} imposes MUSTs on its endpoints; see the Note to the RFC Editor
  UAX15:
    title: "Unicode Standard Annex #15: Unicode Normalization Forms"
    target: https://www.unicode.org/reports/tr15/
    author:
      - org: The Unicode Consortium
    date: 2025

informative:
  RFC6973:        # Privacy Considerations for Internet Protocols
  RFC6350:        # vCard 4.0
  RFC8032:        # EdDSA; S8.4 is why EdDSA is outside {{signature-malleability}}
  RFC9162:        # Certificate Transparency 2.0; {{merkle-construction}} states its relationship to Section 2.1.1
  RFC6962:        # Certificate Transparency, obsoleted by RFC 9162 and cited deliberately: it is what deployed CT logs implement
  I-D.schrock-canonical-action-identifier:
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
    target: https://sanctionslist.ofac.treas.gov/Home/SdnList
    author:
      - org: United States Department of the Treasury, Office of Foreign Assets Control
    date: 2026
  EU-CFSP:
    title: "EU Consolidated Financial Sanctions List"
    target: https://webgate.ec.europa.eu/fsd/fsf
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
    title: Module-Lattice-Based Key-Encapsulation Mechanism Standard
    seriesinfo:
      NIST: FIPS 203
    target: https://csrc.nist.gov/pubs/fips/203/final
    date: 2024
  FIPS204:
    title: Module-Lattice-Based Digital Signature Standard
    seriesinfo:
      NIST: FIPS 204
    target: https://csrc.nist.gov/pubs/fips/204/final
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
attestations whose payload discloses, of the subject, only a verdict, an optional
divergence axis, the applied profile parameters and a query binding digest,
aggregates those attestations under a verdict arithmetic the deployment's policy
resolves, committing each register's contribution to a Merkle tree, and seals the resulting reconciliation output against
a policy-version hash. An append-only cross-jurisdictional settlement-layer
ledger records digests and structural metadata, with no claim, register-record
or principal content. The protocol supports retroactive
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

This document is Standards Track and makes six normative references to
Informational documents: RFC 2104, RFC 6234, RFC 6839, RFC 8785, RFC 9053 and
RFC 9334. Each is a downref under {{RFC8067}}. RFC 6839, RFC 9053 and RFC 9334
are already recorded in the downref registry, so no Last Call action is required
for them. RFC 2104 and RFC 6234 are cited for HMAC and for SHA-256, which every
digest this document defines depends on and which earlier revisions used
throughout with no normative reference at all; RFC EDITOR, please confirm their
current downref-registry status, since it may have changed since this revision
was written. RFC 8785 is not registered, and it is the one that needs the
announcement below. That reference is
deliberately normative: ARP's Canonical Claim is a digest over an RFC 8785
serialisation preceded by Unicode Normalization Form C, and the subject digest
of {{composition}} is a digest over an unmodified RFC 8785 serialisation.
Neither can be computed without RFC 8785, and an implementation that
substituted any other canonicalisation would compute a different value for the
same claim. The reference is therefore load-bearing for interoperability and
cannot be demoted to informative. This is called out here so that the downref
can be noted in the IETF Last Call announcement, which Section 2 of {{RFC8067}}
strongly recommends without requiring.

This document also makes a normative reference to
{{I-D.ietf-scitt-scrapi}}, which at the time of writing has completed IETF
process and is in the RFC Editor queue with no RFC number yet assigned. {{scrapi-binding}} imposes
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
  reconciliation server and a Register Operator, declaring the terms under which
  a register is addressable under this document. {{bra}} enumerates the items an
  Agreement MUST declare, in the order that fixes them, and defines the
  Agreement Hash each Agreement carries.

Witness Set:
: The set of observers, declared in a Bilateral Register Agreement under
  {{witness-entries}}, whose Head Consistency Statements under
  {{head-consistency}} constitute head-consistency evidence independent of the
  responding service.

Witness Quorum:
: The number of Witness Entries, as {{witness-entries}} defines them, with
  pairwise distinct Operating-Party Identifiers whose Head Consistency
  Statements a relying party must hold before the evidence condition of
  {{read-responses}} is satisfied. Declared under {{bra-witness}} and evaluated
  under {{quorum-rule}}.

Policy-Epoch Store:
: The persisted, versioned record of a deployment's verification-policy state,
  from which the Policy-Version Hash of {{sealing}} is reconstructible and from
  which the reconciliation server resolves, per predicate and named regime set,
  the Verdict Arithmetic and its parameters and the reliance interval. It holds
  the Deployment Blinding Value and the Requester-Binding of each reconciliation.
  It is internal to the reconciliation server; this document constrains what it
  must be able to answer and not how it is built.

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
  Plane. The two orderings are not interchangeable, and this specification pins
  the UTF-16 reading, which is the one Section 3.2.3 of {{RFC8785}} specifies.

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
  payload SHALL disclose, of the subject, only a Reconciliation-Verdict field,
  an OPTIONAL Divergence-Axis field, the applied parameters of
  {{format-profiles}} and the Query Binding, which is a digest; it SHALL NOT
  disclose any register record. Fields denoting state rather than the subject --
  the Freshness Timestamp, and the Source-Data Version Identifier of
  {{source-versioning}} --
  are enumerated in {{partial-attestation}}.

Applicable-Regimes Set:
: The set of regulatory regimes a Canonical Claim names as applicable. It is a
  claim field chosen by the requester and states which law the requester asserts
  governs the question. It does not carry the Verdict Arithmetic, its parameters
  or the reliance interval; those are resolved by the reconciliation server from
  the policy-epoch store of {{sealing}}, keyed on the predicate and the named
  regimes, and are committed to the Policy-Version Hash. A requester names the
  regime; the deployment's policy determines how evidence under it combines and
  how long a verdict may be relied upon.

Combined Verdict:
: The single verdict value produced by aggregating the Reconciliation-Verdict
  fields of the Per-Register Result Set of {{reconciliation-output}} under the
  Verdict Arithmetic resolved under {{verdict-arithmetic}}. Its values are
  match, no-match, partial-match and indeterminate. The decisive values are
  match and no-match.

Reconciliation Hash:
: The SHA-256 digest over the deterministically encoded CBOR serialisation of a
  Reconciliation Output excluding its Sealing Signature and Sealing-Key
  Identifier, as specified in {{reconciliation-output}}, and with every
  signature made by a party other than the sealing reconciliation server
  replaced by the Signing Input Digest of that signature. Those are the register
  signature carried in each Query Binding Record, the register signature carried
  in each Non-Answer Statement, and the authorising operator's signature carried
  in the Override Record of {{adversarial-test}}. Excluding the Sealing
  Signature is not sufficient on its own: a Reconciliation Output embeds
  signatures made by parties other than the server, and a digest over those
  names whichever encoding the reader was handed, for the reason
  {{signature-malleability}} gives. The rule is stated over the class -- every
  signature not made by the sealing server -- and not over an enumeration,
  because an enumeration is complete only until a field is added, and the
  Override Record is the field that showed this.

Authority Origin:
: The serialisation of an origin as Section 6.2 of {{RFC6454}} defines it: the
  scheme, the U+003A COLON and two U+002F SOLIDUS characters, the host, and,
  where the port differs from the default for the scheme, a U+003A COLON and the
  port in decimal with no leading zeros. The scheme and the host are lowercased.
  There is no trailing solidus, no path, no query and no fragment, and no
  userinfo component: `https://register-a.example` and
  `https://register-a.example:8443` are Authority Origins and
  `https://register-a.example/`, `https://Register-A.example`,
  `https://register-a.example:443` and `register-a.example` are not.
  An implementation MUST reject a value in any of those other forms rather than
  normalise it, because a value that is normalised on receipt is a value two
  parties can hash differently before they compare it.

  This document uses Authority Origins as bytewise sort keys inside signed sets,
  as path segments, and as equality targets against the origin component of a
  Sealing-Key Identifier. Each of those three uses breaks on a different
  divergence: a sort key reorders, a path segment resolves elsewhere, and an
  equality test refuses a key that was in fact authorised. Fixing the form once,
  here, is what makes those three uses one term.

Signing Input Digest:
: The SHA-256 digest over the deterministically encoded CBOR `Sig_structure` of
  a COSE_Sign1, as Section 4.4 of {{RFC9052}} constructs it: the array of the
  context string `"Signature1"`, the protected header, the external additional
  authenticated data, and the payload. It is a digest of what the signer signed
  and not of the envelope carrying it, so it does not depend on the signature
  bytes and does depend on the protected header, which in this document carries
  the key identifier and the algorithm identifier under {{cbor-cose}}. This
  document supplies no external additional authenticated data: the third element
  is the zero-length byte string in every `Sig_structure` it defines, and an
  implementation MUST NOT supply another value, because a Signing Input Digest
  a third party cannot reproduce is not an identifier. The protected header is
  taken as the byte string transmitted and MUST NOT be re-encoded; those bytes
  are the signer's and are what the signature covers. Every digest in this
  document that identifies or chains a signed artefact is a Signing Input
  Digest, for the reason {{signature-malleability}} gives.

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
  Axes recorded by the reconciliation server rather than by a register, which the
  registry marks as such and which initially are freshness-stale,
  source-version-skew, register-threshold-divergence, declared-not-determined and
  agent-action-scope-divergence, are carried in the Reconciliation Output, not in
  the register's signed Partial-Attestation payload.

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
: A partition of the Addressed-Registers Identifier Set resolved for the named
  regimes under {{verdict-arithmetic}}, over which source-class-quorum is
  evaluated.

Sovereign Re-Notification:
: A signed notification emitted through the Regulator Portal to each regulator
  whose
  statutory scope covers a reconciliation whose historical Combined Verdict has
  materially changed. The supersession that occasions it is separately recorded
  as a `continuation-supersession` entry on the Settlement-Layer Ledger under
  {{settlement-ledger}}, so that a relying party that acted on the superseded
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

Hash-Linkage Aggregation:
: An aggregation of Partial Attestations in which the per-register
  attestations are reduced to their Signing Input Digests, ordered, committed to a
   Merkle tree,
  and emitted with a Merkle root and a per-register verdict band. The Merkle
  commitment and its inclusion proofs MAY be encoded as COSE Receipts
  {{RFC9942}}.

Policy-Version Hash:
: A cryptographic commitment to the canonical verification-policy state in
  force at the moment of reconciliation, including reconciliation rules,
  threshold parameters, pattern-library version, applicable-regimes
  precedence, verdict-arithmetic selection with every parameter it takes, the
  reliance interval, the Agent-IFF policy in force, the Requester-Binding, and
  the Bilateral-Register-Agreement Hashes of the addressed registers.

Settlement-Layer Ledger:
: An append-only cross-jurisdictional log retaining hashes of reconciliations
  and no Canonical-Claim, register-record or principal content. It carries
  entries of two kinds, discriminated by an entry type: a reconciliation entry,
  which records a sealed Reconciliation Output, and a Continuation entry, which
  records a notarisation outcome, a Post-Seal Evaluation Record or a supersession
  arising after that Output was sealed. Every entry carries a sequence number,
  the entry type, the claim hash, the reconciliation hash, an entry timestamp, a
  prior-entry hash, a self-entry hash and an entry signature; the fields each
  kind carries in addition are enumerated in {{settlement-ledger}}. A
  Continuation entry may also carry a transparency-service identifier, an entry
  identifier, an HTTP status code, a post-seal evaluation record hash, a
  material-change indicator, a superseding reconciliation hash and a superseding
  entry sequence number. Not every field is a digest -- the sequence
  numbers, the timestamps, the entry type, the descriptors and the indicators are
  not -- but no field carries Canonical-Claim, register-record or principal
  content, and no field is a retrieval address.

Audience Set:
: The set of Audience Members of a Reconciliation Output, sealed with it under
  {{entitlement}}. Each Audience Member is an accountable-principal identifier
  together with a verification method that can be presented after the
  reconciliation. The Requesting Principal is a member wherever it can be
  identified. Entitlement to
  read about a reconciliation follows membership, not possession of the artefact.

Reliance Horizon:
: The time after which an Audience Member MUST NOT treat a Combined Verdict as
  current without reading the Continuation entries for its Reconciliation Hash.
  It is the Reconciliation Timestamp advanced by the reliance interval that
  deployment policy declares for the predicate and the named regimes, resolved as
  {{verdict-arithmetic}} resolves the Verdict Arithmetic. It bounds reliance and
  does not affect the validity of the Sealing Signature.

Ledger Head Statement:
: A signed statement of the current head of the Settlement-Layer Ledger,
  published at a well-known URI and notarised at a declared interval, comprising
  the head's Entry Sequence Number, its Self-Entry Hash, its Entry Timestamp, the
  time the Statement was produced, and a pointer to the most recent completed
  head notarisation. Defined in {{settlement-ledger}}.

Evaluation Sweep Statement:
: A signed record that a retroactive evaluation was performed, comprising the
  trigger, the policy state applied, the ledger head at the start and end of the
  sweep, the counts examined and materially changed, a Merkle root over the Claim
  Hashes examined, a timestamp, a pointer to the
  notarisation of the previous Statement. Defined in {{sweep-statements}}. Its purpose is to make
  an evaluation that never ran a signed omission rather than a silence.

Non-Answer Statement:
: A statement signed by a register recording that it declined to answer, over the
  Reconciliation Identifier, the Projected Predicate, the Subject Reference, the
  Reconciliation Nonce and the reason. Required wherever a Non-Answer Reason is
  register-attested, per {{no-answer}}.

# Architecture {#architecture}

ARP comprises seventeen subsystems arranged as a deterministic pipeline:

1. Canonical Claim Ingestion
2. Requester Identity Binding and Agent Friend-or-Foe Gate
3. Adversarial Pre-Transmission Test
4. Per-Register Projection Function, under the profile of {{format-profiles}}
   declared in the Bilateral Register Agreement
5. Per-Register Encryption
6. Partial-Attestation Reception, including Source-Data Version Binding
7. Non-Answer Resolution
8. Verdict Re-Typing
9. Aggregation under the Verdict Arithmetic, per {{aggregation}}
10. Policy-Version-Hash Sealing
11. Settlement-Layer Ledger Write
12. Notarisation under {{scrapi-binding}}, where performed
13. Regulator Portal
14. Retroactive Evaluation
15. Output Delivery under {{delivery}}
16. Post-Seal Evaluation Recording
17. Cryptographic-Primitive-Upgrade Path

Given an identical Canonical Claim, an identical Requester-Binding, an identical
Audience Set, an identical Addressed-Registers Identifier Set, identical
Bilateral-Register-Agreement Hashes for the addressed registers, an identical
Pattern-Library Version Identifier, and an identical Policy-Version
Identifier, the system MUST produce Reconciliation Outputs identical in every
field save those enumerated below as outside this requirement, and identical
Claim Hash and Policy-Version Hash values in the corresponding Settlement-Layer
Ledger entries.

The Reconciliation Hash is deliberately not among those values. It is a content
commitment over one sealed Output, taken over a preimage that includes that
Output's Reconciliation Timestamp, and it is not reproducible across runs; the
Reconciliation Identifier of {{reconciliation-output}} is the reproducible index,
and it is the Claim Hash and Policy-Version Hash that make it so. Requiring an
identical Reconciliation Hash would require an identical timestamp, which no
implementation can deliver.

The per-event fields of a Ledger entry -- Entry Sequence Number, Entry Timestamp,
Prior-Entry Hash, Self-Entry Hash and Entry Signature -- are position-dependent
by construction and are outside this requirement; the Entry Signature is
further outside it because a signature scheme is not required to be
deterministic. Within the Reconciliation Output itself the Reconciliation
Timestamp, the Reliance Horizon computed from it, the Sealing Signature and any
Override Record are outside it: the
first is per-event, the second need not be deterministic, and an Override Record
records an operator's discretionary act rather than a function of the enumerated
inputs. The register-produced signatures the Output carries -- the Partial
Attestation inside each Query Binding Record, and each Non-Answer Statement --
are outside it on the same ground as the Sealing Signature: they are signatures,
and a signature scheme need not be deterministic. So is the Sealing-Key
Identifier, which is rotation state and not an enumerated input. So are the
Reconciliation Event Identifier, the Reconciliation Identifier that carries it,
and every Reconciliation Nonce carried in a Query Binding Record or a Non-Answer
Statement, together with the register signatures taken over them: each is drawn
fresh per reconciliation and is uniqueness state rather than an enumerated
input. Two reconciliations agreeing on every enumerated input MUST differ in all
three, and an implementation MUST NOT read that difference as a determinism
failure. Stating it matters because the requirement above is expressed as
identity in every field save those carved out here, so a field that is
necessarily fresh and not carved out makes the requirement unsatisfiable by any
implementation. So are `attestation-stale` and `register-unresponsive`, and the
Divergence-Axis and verdict consequences that follow from either: both are
functions of wall-clock timing and network conditions rather than of the
enumerated inputs, which is the same ground on which the Freshness Timestamps
themselves are outside it. A reconciliation driven to a `query-budget-exhausted`
or `subject-ceiling-exhausted` Non-Answer Reason
under {{no-answer}} is also outside it, because the budget is accumulated state
and not an enumerated input. The residual risk that carve-out creates, and why
this document does not close it, is set out in {{budget-suppression}}. The Freshness Timestamps of the constituent
Partial Attestations, and any Source-Data Version Identifiers they carry per
{{source-versioning}}, are likewise outside it: both denote state external to
the enumerated inputs. Two reconciliations agreeing on every enumerated input
but differing in Source-Data Version are not required to agree field for field, and
an implementation MUST NOT treat such a difference as a determinism failure.

## Canonical Claim Ingestion {#ingestion}

A Canonical Claim comprises:

- Subject Identifier
- Predicate (drawn from the controlled Predicate Taxonomy)
- Attested Value (in the canonical type for the Predicate)
- Applicable-Regimes Set
- Evidentiary Provenance Manifest
- Claim Timestamp ({{RFC3339}} UTC)
- Claim Hash: the SHA-256 digest over the deterministically encoded CBOR array
  `["arp-claim-v1", Deployment Blinding Value, canonical serialisation]`, where
  the canonical serialisation is the {{RFC8785}} form of the preceding fields as
  {{terminology}} constructs it, carried as a CBOR byte string. Framing the
  blinding value as an array element rather than concatenating it is what stops
  two deployments differing on order, separator or length prefix while claiming
  the same construction identifier

The reconciliation server MUST verify, before computing the Claim Hash, that
the octets it received under {{request-binding}} are the canonicalisation of the
claim they carry. It MUST parse them, re-serialise the parsed fields as this
section constructs them, and refuse a request whose received octets differ from
that re-serialisation, or whose member set is not exactly the fields enumerated
above, returning the `422` of {{request-binding}} with a Remediation Advisory
naming the difference.

{{request-binding}} has the requester supply the {{RFC8785}} serialisation as a
byte string and has the server hash the octets it received, for a reason that is
correct: re-serialising a natively encoded claim would let two servers receiving
identical bytes compute different Claim Hashes. The consequence not drawn was
that the preimage of the Settlement-Layer Ledger index is then chosen by the
requester. A claim submitted in NFD and the same claim in NFC have identical
canonical field values and produce two Claim Hashes, two ledger indices and two
retroactive-evaluation keys, and a sweep selecting on one misses the other. The
check above keeps the requester's octets as the preimage and makes them
canonical, which is what the rest of this section already assumes of them. The
same argument appears at {{terminology}} for the Authority Origin -- a value
normalised on receipt is a value two parties hash differently before they
compare it -- and it was applied there and not here.

Two claims whose canonical field values are identical MUST produce the same
canonical form, and the same Claim Hash within one deployment. Across
deployments the Claim Hash differs by the Deployment Blinding Value while the
canonical form does not. Declared array order is significant;
claims differing only in declared array order are distinct claims. The Claim Hash is the index on the
Settlement-Layer Ledger and the key for retroactive re-evaluation.

The Evidentiary Provenance Manifest is a JSON object, and this document does not
otherwise constrain its members. It **MUST NOT carry a signature, a COSE_Sign1,
or any other signed artefact, in any member at any depth**, and a reconciliation
server MUST refuse a claim whose Manifest carries one, returning the `422` of
{{request-binding}}.

Where the evidentiary provenance is itself a signed artefact -- a COSE-enveloped
evidence structure, or a Verified Principal Credential -- the Manifest carries
the Signing Input Digest of that artefact, rendered as a lowercase hexadecimal
text string, and the artefact travels outside the Canonical Claim.

The Manifest is a field of the Canonical Claim and therefore inside the Claim
Hash preimage, so a signature within it is a signature inside a digest preimage,
re-encodable in transit by a party holding no key, for the reason
{{signature-malleability}} gives. A claim carrying one indexes the
Settlement-Layer Ledger under a value that moves while the claim does not, and
no party outside the deployment can detect it, because the Claim Hash is blinded
and cannot be recomputed outside the deployment at all.

This is the seventh carrier and the only one the class rule of
{{signature-malleability}} could not have reached. That rule directs a party
computing a digest to substitute a Signing Input Digest for any signature made
by another party, and it is inoperable here for two reasons: the preimage is
{{RFC8785}} JSON, which has no byte-string type for the substituted value, and
{{request-binding}} has the server hash the requester's octets, so a server-side
substitution would produce a Claim Hash over bytes the requester never signed.
Where a construction cannot be repaired by the general rule, the content has to
be excluded rather than the rule extended, which is what the prohibition above
does. An earlier revision instead said the container form "does not alter the
Claim Hash", which is true of the container and false of what the container
holds.

## Requester Identity Binding and Agent Friend-or-Foe Gate

Before the Adversarial Pre-Transmission Test, the reconciliation server MUST
establish the identity of the Requesting Principal and record it in a
Requester-Binding field. The Requester-Binding comprises a requester-binding
class, the identifier of the accountable principal where known, and a reference
to the verification method used. The class is one of:

- `human-operator`, where an authenticated human or institutional operator is
  the accountable principal.
- `agent-verified`, where an agent's signing key verified AND the principal it
  asserts was corroborated by a reconciliation under {{agentic}} or by a Verified
  Principal Credential whose status was checked.
- `agent-key-verified`, where an agent's signing key verified but the principal
  it asserts was not corroborated.
- `agent-unverified`, where the request was signed under a bare key that resolves
  to no signature-agent card, carries no Verified Principal Credential, and
  asserts no principal. The key gives continuity of identity between requests and
  nothing else, which is why it is a class and not a refusal; a request that
  carries no verifying signature at all is not admitted, by {{read-signing}}.

`agent-key-verified` exists because possession of a key and binding to a
principal are different facts and earlier revisions recorded them as one. An
agent that signs correctly under a Web Bot Auth key has demonstrated that it is
the same agent as last time; it has not demonstrated that any accountable party
stands behind it. Recording that state as `agent-verified` overclaims to every
downstream reader, and recording it as `agent-unverified` discards a real and
useful fact. A relying party that requires an attributable principal should treat
`agent-key-verified` as it treats `agent-unverified`; one that requires only
continuity of identity may treat it as it treats `agent-verified`. This document
states no requirement on a relying party's own risk policy; what it requires is
that the two states be recorded distinctly so that the policy can be applied. The Agent-IFF
policy states which reconciliations may be decisive at each class.

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
`agent-unverified`, and whether an agent whose key verified but whose principal
was not corroborated -- class `agent-key-verified` -- may reach a decisive
verdict. The server MUST NOT silently upgrade an ENEMY requester to
FRIENDLY. The Requester-Binding and the Agent-IFF policy identifier are
committed to the Policy-Version Hash so that the settlement record is
attributable to a determined requester class.

## Adversarial Pre-Transmission Test {#adversarial-test}

Before any Per-Register Claim Projection is produced, the Adversarial
Pre-Transmission Test Subsystem applies the current Pattern Library to the
Canonical Claim. The Pattern Library enumerates structural evasion patterns
against the projection and aggregation mechanisms of this protocol, including
projection-narrowing-evasion,
predicate-substitution-evasion, attested-value-bracketing-evasion,
addressed-register-cherry-picking, agreement-staleness-injection,
pattern-library-version-pinning, and agent-principal-spoofing (an unverifiable
agent asserting a principal binding it does not hold).

The Subsystem emits either a Pass result or a Remediation Advisory. A Remediation
Advisory comprises:

- a Refusal Ground, one of `pattern-matched`, `regime-not-admitted`,
  `audience-member-not-enrolled` or `agent-iff-refused`
- the identifiers of the Pattern Library patterns that matched, and the narrowing
  or substitution each concerns, present exactly where the Ground is
  `pattern-matched`
- the regime, the Audience Member Identifier or the Agent-IFF ground the other
  three Grounds concern respectively, present under the corresponding Ground

It is encoded as a CBOR array in that field order under the media type registered
in {{iana}}, absent fields as CBOR null, and is returned to the requester as
{{request-binding}} provides. No projection is transmitted and no Reconciliation
Output is produced. The Advisory is the only artefact a refused requester
receives, so it carries the ground rather than leaving the requester to infer
it.

Where the Ground is `pattern-matched`, the second field MUST be encoded as CBOR
null in the Advisory returned to the requester, the array's field order being
unchanged, and the matched identifiers and the narrowing or substitution each
concerns MUST be retained by the server and disclosed only to a regulator under
{{regulator-portal}} and to an Audit Identity under {{audit-path}}.

A requester that can vary a claim and read back which pattern matched
enumerates, one refusal at a time, the corpus {{per-register-encryption}}
declines to disclose even to a register. The query budget does not bound the
probe, being keyed per principal per subject, so an evader varying subjects
probes without limit. An Advisory that names the pattern is a more efficient
route into the Pattern Library than the Library's confidentiality is a defence
of it, and the party it was handed to is the one party the Test exists to
defend against.

The Per-Register Encryption Subsystem MUST architecturally withhold external
transmission until a Pass result has been emitted or until an authorised
operator has explicitly overridden the outcome. An override MUST be recorded in
the Reconciliation Output as an Override Record and is thereby covered by the
Sealing Signature. An override that left no artefact would be indistinguishable
from a Pass to every external party, which would make the only manual bypass of
the protocol's own adversarial gate invisible to the regulators that gate exists
to serve.

An Override Record comprises:

- the identifiers of the Pattern Library patterns that matched
- the Pattern-Library Version Identifier under which they matched
- the Override Ground, drawn from the registry of {{iana}}
- the identifier of the authorising operator
- an Override Timestamp ({{RFC3339}} UTC)
- a signature by the authorising operator, a COSE_Sign1 whose payload is the CBOR
  array of the fields above in the order listed with the signature position
  encoded as CBOR null, encoded under Section 4.2.1 of {{RFC8949}}, and carrying
  as its key identifier the JWK thumbprint, computed as in {{RFC7638}}, of a key published
  in the reconciliation server's Operator Key Set at
  `/.well-known/arp-operator-keys` on its Authority Origin. That key set is
  published and validated as the sealing key set of {{sealing-key-discovery}} is,
  save that the Authorised-Origin Document MUST name a key identifier for the
  operator key set distinct from the one anchoring the sealing key set. Sealing
  keys and operator keys are separate sets because they are held by different
  parties for different purposes: a server able to sign an override with its
  sealing key could manufacture an operator's authorisation, and a server holding
  the only key that anchors its own operator key set could do the same one level
  up

The signature is by the operator and not by the server. A record the server
signs attests only that the server says an operator authorised the bypass; a
record the operator signs is a statement the operator made and cannot later
disown, which is what a manual override of an adversarial gate has to be for the
regulator reading it. The Override Ground is drawn from a registry so that
grounds are enumerable and comparable across deployments rather than free text
that no reviewer can aggregate.

The reconciliation entry that records an overridden reconciliation carries an
Override Indicator, so that a regulator reading the Ledger under
{{regulator-portal}} can see that a bypass occurred without holding the Output.
Having seen it, the regulator reads the Output itself under {{audit-path}} or
through the entitlement its statutory scope gives it, and reads the Record. An
Override Record visible only to the Audience Set the operator chose to serve
would be invisible to the party the mechanism exists for, which is the failure
this paragraph and the Indicator together close.

The Record names an operator in the clear, in an artefact whose Policy-Version
Hash is blinded under {{sealing}} precisely to keep principal identities out of
reach. That is not a contradiction: blinding protects the Ledger, which is
published, and the Reconciliation Output is confidential to its Audience Set
under {{entitlement}}. An override is a discretionary act by a named human
against a named pattern, and the parties entitled to the Output are the parties
entitled to know who performed it. Nothing about the override reaches the Ledger
except through the Reconciliation Hash, which is a digest.

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

The Predicate Taxonomy over which that walk is performed is the union of the
branches the Register Data-Format Profiles of {{format-profiles}} define, each
branch's parent relation being the one its profile declares and each branch's
root being the predicate that profile names as such. Taxonomic distance is
defined only between predicates within one branch. A predicate belonging to no
declared branch has no parent, and a walk that would leave the branch it began
in MUST fail with `projection-unsupported`. The `agent:` branch of {{agentic}}
is governed by no profile and is therefore flat: its predicates have no parent
and a walk beginning at one MUST fail on the same reason.

There is no registry of predicates and this document does not create one. The
taxonomy is a deployment artefact assembled from declared profiles, which is
what makes it checkable by the register: the permitted-predicate set is item 1
of {{bra-items}} and is therefore inside the Agreement Hash, so the second party
to a projection can test the walk against terms it negotiated. Earlier revisions
named the taxonomy and left the reader to infer where its edges came from.

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

- OPTIONAL Requester-Binding Class, present exactly where the Bilateral Register
  Agreement requires it under {{containment}}, disclosing the class and not the
  principal

A Per-Register Claim Projection is encoded as a CBOR array in the field order
above, an absent OPTIONAL or conditionally absent field encoded as CBOR null so
that position is preserved. This is the only structure a sovereign register receives, and it is enumerated
here so that its contents are determinate and its digest constructions
reproducible.

The wire binding over which it is transmitted is not specified by this document.
This document specifies what the channel must achieve -- the structure it
carries, the confidentiality and authenticated-additional-data properties of
{{per-register-encryption}}, and the Query Binding the register signs over -- and
leaves the transport, the endpoint, the framing and the concrete encryption
construction to be declared in each Bilateral Register Agreement.

That is a deliberate scoping decision and it is a real limitation, stated here
rather than left to be discovered: two reconciliation servers addressing the same
register do so over channels the register defined, so ARP is interoperable in its
artefacts and not yet in that leg's transport. Specifying it -- an endpoint, a
media type, and a COSE_Encrypt construction pinning the AEAD and the ordering of
its authenticated additional data -- is the principal item of work this revision
leaves for the next. The
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

### Subject Mapping Record {#subject-mapping}

The projection function transforms the Canonical Claim's Subject Identifier into
a Subject Reference in the form the addressed register's Bilateral Register
Agreement declares. Until this revision nothing recorded that transformation,
nothing constrained it, and no party outside the reconciliation server could
check it.

That is the gravest thing a reader can fail to notice about an Output. Every
signature in a Reconciliation Output can verify, every Query Binding can
recompute, the Merkle Root can be correct, the ledger entry can chain and the
notarised Signed Statement can pass every check in {{registration}}, while every
addressed register answered honestly and completely **about a different
person**. The registers answer about the Subject Reference they were sent. The
Output is read as an answer about the Subject Identifier in the claim. Nothing
joined the two, and a substitution at that step is invisible to the requester,
to an Audience Member, to a regulator reading the portal, to an Audit Identity,
and to the registers themselves, none of which is shown the Canonical Claim.

Each Per-Register Result Set entry for which a projection was transmitted MUST
therefore carry a **Subject Mapping Record**: the two-element CBOR array of the
Subject Reference transmitted to that register, and the **Subject Mapping
Descriptor** -- a text string, drawn from the registry of {{iana}}, naming the
transformation applied. The initial registrations are `identity`, where the
Subject Reference is the Subject Identifier unchanged; `profile-declared`, where
the transformation is the one the register's declared Data-Format Profile
specifies for the Subject Identifier's form; and `agreement-declared`, where the
Bilateral Register Agreement declares the transformation as one of its terms.
A registration MUST specify a transformation that is a function of the Subject
Identifier and of declared terms alone, so that a party holding the Canonical
Claim and the applicable Agreement can recompute the Subject Reference and
compare it. The designated expert MUST refuse a registration whose
transformation takes any input the server chooses at reconciliation time, since
such a descriptor would name the discretion rather than remove it.

A verifier holding the Canonical Claim MUST recompute the Subject Reference
under the named descriptor and MUST reject the Output where the recomputed value
differs from the one carried. A verifier not holding the Canonical Claim cannot
perform that check, and this document does not claim otherwise: what the record
gives that party is an attributable statement, signed and sealed and ledgered,
of which subject each register was actually asked about. The substitution
remains possible and stops being deniable, which is the same trade
{{no-answer}} makes for a suppressed register answer.

This does not close the case where the Subject Identifier in the claim was
already the wrong person. Nothing in a reconciliation protocol can, and
{{subject-digest-scope}} states the boundary.

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

Each of the four profiles below states the dated vocabulary it uses where it
names one, the parent relation for each branch of its predicate space over which
narrowing is defined, the parameters a Bilateral Register Agreement declaring it
must supply, and which of its predicates are threshold-sensitive within the
meaning of {{verdict-retyping}}.

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

In this profile the ownership and control predicates are
threshold-sensitive; the identity and existence predicates are not.

### Corporate registries: vCard and the Organization Ontology {#profile-corporate}

A profile in this class MUST declare {{W3C-ORG}} for any branch of its predicate
space over which taxonomic narrowing is defined. {{RFC6350}} expresses
organisational hierarchy only within one organisation's own `ORG` structured
value and defines no property relating one organisation to another, so a
vCard-only profile has no term capable of satisfying the parent-relation
requirement of {{format-profiles}} and MUST NOT declare a narrowing branch.
vCard remains available for the identifying and contact predicates, over which
no narrowing is defined.

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

The vocabulary is pinned to {{W3C-ORG}} as at its 2014 Recommendation and to
{{RFC6350}}. A Bilateral Register Agreement declaring this profile supplies the
register's jurisdiction identifier and the identifier scheme of its
`org:identifier` values. No predicate in this profile is threshold-sensitive:
corporate registries record recognition rather than a quantified interest.

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

The vocabulary is pinned to Version 4 of the {{WCO-DM}} and to the UN/CEFACT
Core Component Library release the Bilateral Register Agreement names, which it
MUST name. The Agreement also supplies the declaration types the register
answers over. No predicate in this profile is threshold-sensitive.

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

A profile in this class names no single vocabulary, consolidated sanctions lists
having no common schema. It instead pins, per register, the list identifier and
the publisher's state-identifier form that {{source-versioning}} requires, both
supplied by the Bilateral Register Agreement, together with the matching
predicate set the register answers over. No predicate in this profile is
threshold-sensitive: a designation is a listed-or-not fact.

## Source-Data Version Binding {#source-versioning}

Where a register's answer depends on a source data state that changes
independently of the Bilateral Register Agreement and of the Policy Version --
a consolidated sanctions list being the characteristic case -- the Partial
Attestation MUST carry a Source-Data Version Identifier Set: one identifier for
each source consulted in evaluating the Projected Predicate. Each identifier is
a two-element CBOR array of the list name as declared in the Bilateral Register
Agreement, as a text string, and the state identifier the LIST PUBLISHER
assigns to that state, rather than any value of the register's own devising.

The state identifier is itself a two-element CBOR array of a form discriminator
and a value. The discriminator is the text string `token` where the publisher
assigns a version token, and the value is that token as a text string exactly as
the publisher renders it, with no normalisation, trimming or case folding. The
discriminator is the text string `digest` where the publisher assigns none, and
the value is the SHA-256 digest, as a 32-octet CBOR byte string, of the octets
the publisher serves for that state, taken as served and before any
decompression, transcoding or reformatting the register applies.

The discriminator is present because the two branches are a text string and a
byte string in one position, and a reader that must infer which it holds from
the CBOR major type is a reader that will be wrong the first time a publisher
issues a token that happens to decode. The "as served, before decompression"
rule is present because a consolidated list published as a compressed archive
has at least two byte sequences with an equal claim to being the corpus, and two
registers that choose differently produce two identifiers for one state, which
{{retroactive}} would then read as a version change that never occurred.

The Source-Data Version Identifier Set MUST be encoded as a CBOR array sorted in
bytewise lexicographic order of the deterministic CBOR encoding of each member.
Every other set this document carries into a signature is ordered, and for the
reason {{audience}} gives: an unordered set gives one signed artefact as many
digests as it has permutations. A register consulting three lists would
otherwise have six conforming encodings of one attestation, each producing a
different Merkle leaf under {{aggregation}} and a different Reconciliation Hash. A register-chosen opaque string would be an arbitrary-bandwidth
channel from register to relying party, carried under signature into a sealed
and ledgered artefact, and the rule that differing identifiers MUST NOT be read
as disagreement would normalise it. The reconciliation server MUST reject an
identifier that is not drawn from the publisher's own state sequence, under
{{no-answer}} with the reason `attestation-source-version-invalid`. The tuple form is what
keeps identifiers issued by one register over different lists from colliding, so
that a register consulting several lists can denote the state of each.

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

## Per-Register Encryption {#per-register-encryption}

These are requirements on whatever bilateral channel {{projection}} leaves each
Bilateral Register Agreement to declare; they are properties the channel MUST
provide and not a wire construction this document pins.

Each Per-Register Claim Projection MUST be encrypted under the addressed
register's public key material declared in the Bilateral Register Agreement.
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
  five-element array whose first element is a fixed domain-separation string,
  rather than a byte concatenation, so that two implementations cannot differ on framing and the
  digest cannot collide with any other construction in this document. Within that
array the Reconciliation Identifier is a byte string of 80 octets as
{{reconciliation-output}} fixes it, the Projected Predicate is a text string,
the Reconciliation Nonce is a byte string of at least 16 octets, and the Subject
Reference takes the CBOR type the Subject Reference form of item 8 of
{{bra-items}} declares, which that Agreement MUST state. The register and the
reconciliation server compute this digest independently and MUST obtain the same
value, so an element whose type is left open is an element on which they can
differ while agreeing on every negotiated term
- Freshness Timestamp
- Cryptographic Signature, a COSE_Sign1 by the register whose payload is the
  CBOR array of the fields above in the order listed, with an absent OPTIONAL or
  conditionally absent field encoded as CBOR null so that position is preserved,
  encoded under Section 4.2.1 of {{RFC8949}}. The register's signing key is
  published in its key set under {{sealing-key-discovery}}, so that a relying
  party or auditor holding the attestation can resolve the key and verify the
  signature without the reconciliation server's assurance

The Query Binding is what makes an attestation an answer to a question rather
than a free-standing assertion. Without it the signed payload says only that a
register returned a verdict under some agreement and policy version at some
time, and says nothing about what it was asked. Two consequences follow, and
both are severe: an attestation harvested for one subject could be placed into
the Per-Register Result Set of a reconciliation about another subject and would
verify against every other check; and a register could answer the same question
differently to two requesters and deny having done so, because its signature
would not identify the question.

The `arp-policy-version-hash`, `arp-bilateral-agreement-hash` and
`arp-source-data-version` in a Partial Attestation's protected header MUST equal
the corresponding payload fields, and an implementation MUST reject an
attestation where they differ: a value carried twice with no equality rule is a
value an implementation may read either way. The third is included because
{{source-versioning}} carries the Source-Data Version Identifier Set in the
protected header and again into the Per-Register Result Set, which is the
condition this rule exists to govern, and an earlier revision applied the rule
to the first two only.

The reconciliation server MUST recompute the Query Binding from the projection
it transmitted and MUST reject an attestation whose Query Binding does not
match, under {{no-answer}} with the reason `attestation-binding-mismatch`.

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
the verdict, the divergence axis, the applied parameters and the Query
Binding -- a digest over the Subject Reference -- vary with the subject, is the
mechanism by which ARP limits raw-record disclosure. Residual
inference channels are discussed in {{side-channel}}.

## Merkle Construction {#merkle-construction}

Two structures in this document commit to a set of digests through a Merkle
tree: the Merkle Root of Hash-Linkage Aggregation, and the Examined-Set Root
of {{sweep-statements}}. Both use this construction, so that an inclusion proof
produced by one implementation verifies under another.

Leaves are the digests to be committed, sorted in bytewise lexicographic order
and deduplicated. Deduplication is why an Examined-Set Root commits to distinct
Claim Hashes and the count beside it counts Reconciliation Outputs: two Outputs
over one claim share a Claim Hash, so the leaf count and the examined count need
not be equal and neither is derivable from the other. A leaf node is `SHA-256(0x00 || leaf)`. An internal node is
`SHA-256(0x01 || left || right)`. Where a level has an odd number of nodes, the
last is carried up to the next level unchanged rather than duplicated. A tree
over one leaf has that leaf's leaf-node hash as its root; a tree over no leaves
has thirty-two zero octets as its root.

For every non-empty tree this is the Merkle Tree Hash of Section 2.1.1 of
{{RFC9162}} instantiated with SHA-256. The recursion of that section is the
recursion of Section 2.1 of {{RFC6962}}; the two differ only in that
{{RFC9162}} carries the hash algorithm as a log parameter where {{RFC6962}}
fixes SHA-256, and this document fixes SHA-256. Both are named here:
{{RFC9162}} because it is the current specification, and {{RFC6962}} because it
is what most deployed Certificate Transparency logs implement and so is what an
implementer is most likely to arrive from.

The odd-node rule stated above and that recursive split at the largest power of
two below the leaf count are two descriptions of one tree: at every leaf count
they produce the same root, and at every leaf count and index they produce the
same sibling array. An implementation may compute either way and interoperate
with one that computes the other. This is stated because the two rules do not
look alike, so a reader who knows Certificate Transparency has no way to
establish from the prose alone that they agree; and because a third convention
is in common use, in which the last node at an odd level is duplicated and
paired with itself. That convention produces the same root at every leaf count
that is a power of two, because no level of such a tree is ever odd, and a
different root at every other leaf count. A conformance vector taken at four or
eight leaves will therefore not detect it, and an implementation that ports it
will pass a test suite and diverge in production.

This document and Certificate Transparency diverge at exactly one input to the
tree function, the empty tree, and the divergence is deliberate. Certificate Transparency defines the Merkle Tree Hash of the empty
list as the hash of the empty string, which under SHA-256 is
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; this
document defines it as thirty-two zero octets. The Certificate Transparency
value is a well formed digest that a verifier reproduces successfully and may
then treat as a root that commits to something. Thirty-two zero octets is a
value no commitment in this document produces, so it cannot be mistaken for one.
An implementation MUST use the value defined in this section and MUST NOT
substitute the Certificate Transparency empty-tree value. The requirement below,
that a verifier reject any inclusion proof presented against the empty root,
applies to whichever value a construction gives the empty tree, and the reason
for it does not depend on which value that is.

Two further differences are matters of input and of encoding rather than of the
tree, and each is a place an implementation ported from a Certificate
Transparency log will be wrong if it is carried over unchanged. This document
sorts leaves in bytewise lexicographic order and deduplicates them before the
tree is built, where a Certificate Transparency log commits to entries in the
order it received them; an implementation MUST apply the ordering and
deduplication stated above and MUST NOT assume submission order. And this
document's inclusion proof carries the leaf alongside the index, the leaf count
and the sibling array, where the inclusion proof of Section 2.1.3 of
{{RFC9162}} carries the index and the tree size but not the leaf, which its
verifier is assumed already to hold. The leaf is the only field that differs,
and {{leaf-binding}} states what a verifier must do with it.

An inclusion proof is a CBOR array of the leaf, its zero-based index, the leaf
count, and the array of sibling hashes from the leaf's level upward. Domain
separation between leaf and internal nodes is what stops a proof of an internal
node being presented as a proof of a leaf.

Three properties of that array are stated here because each is a place two
implementations otherwise diverge while both believing they conform. The array
carries one entry for each level at which the node being proved has a sibling,
and no entry for a level at which it was carried up unchanged, so its length is
not in general the base-two logarithm of the leaf count and a verifier MUST NOT
derive the expected length that way. No direction bit is carried: at each level
the verifier derives whether the sibling is the left or the right operand from
the index and the leaf count, taking the floor of half the index and the
**ceiling** of half the level width as it ascends. Halving the width by
truncation instead gives the wrong width at every leaf count that is not a power
of two -- five leaves give widths 5, 3, 2, 1 and not 5, 2, 1 -- which is
precisely the range of leaf counts this section exists to pin down. The
derivation is well defined because the shape of the tree is fixed by the leaf
count alone. And the empty tree's root of thirty-two zero octets admits no
inclusion proof; a verifier MUST reject any proof presented against it rather
than treat a root it can reproduce as a root that commits to something.

### Leaf binding {#leaf-binding}

The leaf a proof carries is a convenience and is not evidence. A verifier MUST
compute the leaf from the object whose inclusion is being proved -- the
Signing Input Digest of the Partial Attestation for a Merkle Root under
{{aggregation}}, the Claim Hash for an Examined-Set Root under
{{sweep-statements}} -- and MUST use that computed value, and no value taken
from the proof, as the input to the sibling walk. Where the proof carries a
leaf, the verifier MUST refuse the proof if the computed value does not equal
it, and MUST perform that comparison before the sibling array is walked.

The requirement is stated over the object rather than over the carried field
because the field is not always present. {{aggregation}} permits per-register
inclusion proofs to be encoded as COSE Receipts {{RFC9942}}, whose inclusion
proof carries no leaf; a requirement written only as a comparison against a
carried leaf would be vacuous under that encoding, which is the encoding a
SCITT-aware verifier is most likely to use.

The ordering is the whole of the requirement. A proof whose leaf is lifted
unchanged from another object's valid proof folds to the correct root under a
sibling array that verifies, because it is a correct proof -- of the other
object. A verifier that walks the path first and takes the carried leaf on trust
accepts it, and concludes that the object it holds was committed when what was
committed was something else. Nothing in the walk depends on the object, so the
walk cannot detect this; only the recomputation can. It is the more dangerous
half of its pair: a malformed proof fails loudly on every path a verifier
tries, while a valid proof bound to the wrong leaf passes every check except
this one.

### Verification outcomes {#verification-outcomes}

The preceding rules tell a verifier to refuse. They do not give it any way to
record which refusal it made, and four conditions that arrive at "refuse"
through this section are evidence about four different things. A deployment that
reports them alike reports something that did not happen, and the report will be
believed, because the check that produced it worked exactly as specified.

A verifier that refuses a proof or an artefact under this document MUST record a
Verification Outcome, drawn from the registry of {{iana}}, and MUST NOT report
one as another. The initial values are:

`proof-against-empty-root`:
: A proof was presented against the empty-tree root of {{merkle-construction}}.
  Evidence of neither equivocation nor re-encoding: the empty root commits to
  nothing and no proof against it can be valid.

`leaf-object-mismatch`:
: The leaf recomputed from the object differs from the leaf the proof carries.
  Evidence of equivocation by the serving party, and the case this section
  exists to catch.

`root-mismatch`:
: The sibling walk completed and produced a root other than the one named.
  Evidence of equivocation by the serving party.

`same-act-distinct-encodings`:
: The artefact the verifier holds and the artefact the proof or digest commits
  to have equal Signing Input Digests and unequal enveloped bytes. **Evidence of
  a re-encoding and not of equivocation.** A verifier MUST test for this
  condition before reporting `leaf-object-mismatch` or `root-mismatch`, and
  where it holds, MUST report this outcome instead.

The last is the one that changes what a reader concludes. Two artefacts with one
Signing Input Digest are one signing act under two encodings, which
{{signature-malleability}} shows a third party holding no key can produce from
the honest signer's own bytes -- and which, for ECDSA, is produced by any
implementation that normalises `s` on ingest while believing it is hardening.
Reporting that as detected tampering accuses a party of equivocating on the
strength of an operation an intermediary performed correctly. The constructions
of {{signature-malleability}} make the digests stable; this makes the report
that survives them accurate.

## Aggregation {#aggregation}

The aggregation subsystem operates in Hash-Linkage Aggregation. Each
Partial Attestation is committed to a Merkle tree as {{merkle-construction}}
defines it, under the leaf value that is its Signing Input Digest, and the
resulting Merkle Root is carried in the Reconciliation Output. The leaf is the
Signing Input Digest and not a digest of the attestation as received, so that
the leaf a verifier computes under {{leaf-binding}} does not depend on which of
several byte-strings carrying one register signature it happens to hold. Its
per-register inclusion proofs MAY be encoded as COSE Receipts {{RFC9942}},
enabling any SCITT-aware verifier to check inclusion without a bespoke proof
format. Each leaf commits one register's attestation individually, so an
inclusion proof discloses no other register's payload.

## Registers That Do Not Answer {#no-answer}

A register may fail to produce a usable Partial Attestation. Every such state
has a defined outcome, because dropping the register silently would produce
exactly the addressed-register-cherry-picking pattern the Adversarial
Pre-Transmission Test exists to detect.

The Per-Register Result Set MUST carry an entry for every addressed register.
Where no usable attestation was received, the entry carries no Attested Verdict
and carries instead, in its own field, a Non-Answer Reason drawn from:

- `projection-ambiguous` and `projection-unsupported`, where the projection
  itself failed and no projection was transmitted
- `agreement-drift-suspended`, where reconciliation against that register was
  suspended for Bilateral-Register-Agreement drift
- `attestation-stale`, where the Freshness Timestamp fell outside the declared
  window and the attestation was rejected
- `attestation-signature-invalid`, where the signature did not verify
- `attestation-echo-mismatch`, where a value the register echoed did not match
  the one sent, or a value carried in the protected header did not equal the
  corresponding payload field
- `attestation-binding-mismatch`, where the Query Binding the server recomputed
  did not match the one the attestation carries, which is an attestation
  elicited for a different question
- `attestation-source-version-invalid`, where a Source-Data Version Identifier
  was not drawn from the publisher's own state sequence
- `attestation-scope-exceeded`, where the register attested a Divergence Axis the
  registry of {{iana}} records as server-recorded
- `register-unresponsive`, where no attestation was received within the window
  declared in the Bilateral Register Agreement
- `register-refused`, where the register declined to answer, whether under its
  own statutory access regime or under the Agent-IFF policy
- `query-budget-exhausted`, where the reconciliation would exceed the
  per-principal per-subject query budget declared under {{containment}}
- `subject-ceiling-exhausted`, where the reconciliation would exceed a per-subject
  ceiling declared under {{containment}}
- `audience-constraint-exceeded`, where the requested Audience Set exceeds the
  audience constraint that register declares under {{audience}}
- `non-answer-unattested`, where the register asserted a register-attested reason
  without a verifying Non-Answer Statement

Each Non-Answer Reason is either register-attested or server-observed, and the
registry of {{iana}} MUST record which for every registration.
`register-refused` is register-attested. `attestation-stale` and the five
`attestation-` reasons above are server-observed but arise from an attestation
the server holds. The remainder are server-observed with no register artefact
behind them.

Earlier revisions carried a single `attestation-unverifiable` covering all five
of those conditions, and normative text in four other sections directed
implementations to it for causes its own definition did not name. They are not
variants of one condition and an auditor cannot be asked to treat them as one.
A failed signature is a broken or impersonated register. An echo mismatch is an
attestation about a different policy state. A binding mismatch is the
reconciliation server presenting an attestation elicited for a different subject
or predicate, which is a server-side attack and not a register fault at all. A
source-version invalidity is a register attempting a covert channel. A scope
excess is a register claiming competence the registry says it does not have.
Recording all five as one value tells the Register Operator reading its own
entry under {{read-operations}} that something was wrong with its attestation,
and does not tell it whether the fault was its own. This document made exactly
this argument for `non-answer-unattested` two paragraphs below and did not
apply it here. An implementation MUST NOT record any of the five under a
value that does not name its cause.

Where a Non-Answer Reason is register-attested, the Per-Register Result Set entry
MUST carry a Non-Answer Statement in the field {{reconciliation-output}} defines
for it. The Statement is a COSE_Sign1 by that register, under the primitive its
Bilateral Register Agreement declares and under a key resolvable as in
{{sealing-key-discovery}}, whose payload is the CBOR array

    ["arp-non-answer-v1", Reconciliation Identifier, Projected Predicate,
     Subject Reference, Reconciliation Nonce, Non-Answer Reason]

encoded under Section 4.2.1 of {{RFC8949}}. The Reconciliation Identifier is
inside the payload for the reason the Query Binding of {{partial-attestation}}
carries it: without it a refusal elicited in one reconciliation is admissible as
a refusal in another over the same subject and predicate.

Where a register-attested reason is recorded without a Statement, or with one
that does not verify, the reason MUST be replaced by `non-answer-unattested`.
That is a distinct reason and not any of the `attestation-` reasons, which denote a
Partial Attestation the server holds and could not verify; collapsing the two
would put the missing-refusal case back into a server-observed bucket and undo
the distinction this rule exists to draw.

Without that rule a `register-refused` is an unattested assertion by the party
that transmitted the projection, and a server can suppress a `match` by claiming
the register declined. The server can still downgrade a reconciliation to
`indeterminate` by asserting a server-observed reason -- `register-unresponsive`
is indistinguishable from a network failure by construction, and this document
does not pretend otherwise -- but it cannot dress suppression as an act of the
register. Suppressing a sanctions hit is the harm this domain cares about, and
the difference between "the register would not say" and "I did not ask" is the
difference the record must preserve.

A Non-Answer Reason is not a verdict, occupies its own field of the Per-Register
Result Set per {{reconciliation-output}}, and MUST NOT be combined by the
Verdict Arithmetic. Its effect is given in {{verdict-arithmetic}}: a reconciliation with
any non-answering register cannot reach a decisive Combined Verdict.

Where the reason is `attestation-stale`, `freshness-stale` MUST also be added to
the Server-Recorded Divergence-Axis Set against that Register Identifier.

A reconciliation server MUST reject a Partial Attestation that attests a
Divergence Axis the registry of {{iana}} records as server-recorded, with the
reason `attestation-scope-exceeded`. A register cannot attest a relation between
itself and another register, which is what those axes are.

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

  Threshold-sensitivity is a property of a Register Data-Format Profile, which
  declares which of its predicates are threshold-sensitive, and the test above
  names the Canonical Claim Predicate, which is not expressed in any profile.
  The test is therefore evaluated as follows, and is defined over a register set
  whose members declare different profiles. The Canonical Claim Predicate is
  threshold-sensitive where the Per-Register Claim Projection transmitted to ANY
  addressed register was a predicate that register's declared profile marks
  threshold-sensitive. Taking the disjunction rather than requiring agreement is
  deliberate: a mixed-profile register set in which one profile marks the
  predicate threshold-sensitive and another is silent is precisely the set in
  which the thresholds may differ unnoticed, and requiring every profile to mark
  it would disable the test in the case it exists for.

- A `match` attested against a Projected Predicate that is a proper ancestor of
  the Canonical Claim Predicate is re-typed to `partial-match` under an operator
  that admits that value and to `indeterminate` under one that does not, under
  the ground `projection-broadened`. The projection function of {{projection}}
  resolves by taxonomic prefix match upward, producing the nearest permitted
  ancestor, so a register answering a Projected Predicate that narrowing did not
  reach is answering a **broader** question than the claim asked. A subject
  designated on some US sanctions list is not thereby designated on the OFAC SDN
  list, and a decisive `match` assembled from the ancestor states a conclusion
  the input does not support.

  A contribution other than `match` is not re-typed on this ground: a `no-match`
  over an ancestor entails `no-match` over every descendant of it, so the
  broadening is harmless in that direction and re-typing it would discard sound
  evidence.

  Earlier revisions covered the converse only. The opening sentence of this
  section says a register answers a Projected Predicate "which may be a
  narrowing of the Canonical Claim Predicate", and the projection function
  produces an ancestor, which is the opposite relation. The Output records the
  broadening in the Narrowed-From field of the Projection Record, so a relying
  party inspecting it could see what happened; nothing obliged it to look, and
  the Combined Verdict was decisive either way. Recording a divergence while
  permitting a decisive verdict built on it is the failure ground 3 above is
  written against, and it applied here and was not applied.

  The Divergence Axis `claim-projection-narrowed-beyond-attestation-scope`
  names this condition and is register-attestable, optional in the attestation,
  and connected to no normative rule anywhere in this document; it appears in
  its own enumeration and nowhere else. An axis a register need never emit, and
  which changes no verdict when emitted, is not a control. This ground is.

Re-typing operates on a register's contribution. It does not override the
Verdict Arithmetic resolved under {{verdict-arithmetic}}, which is applied
afterwards to the re-typed set and is otherwise unaffected. An implementation
MUST NOT re-type on any ground not enumerated here.

## Verdict Arithmetic {#verdict-arithmetic}

The Verdict Arithmetic combines the Reconciliation-Verdict Fields of the
Per-Register Result Set, after any re-typing under {{verdict-retyping}}, into
the Combined Verdict. The requester names the applicable regimes in its
Canonical Claim; it does not choose the operator. The operator and every
parameter it takes are resolved by the reconciliation server from the
policy-epoch store of {{sealing}}, keyed on the predicate and the named regimes,
and are committed to the Policy-Version Hash. They are carried into the
Reconciliation Output so that a relying party can reproduce the combination.

A requester able to choose both the operator and its threshold could choose the
verdict: disjunction over five registers and threshold-count with a threshold of
five differ only in which answer they return over the same contributions, and
selecting between them after seeing which registers were addressed is verdict
shopping that no downstream check would detect. Naming a regime is a claim about
which law applies, which the requester is competent to make and accountable for;
selecting an operator is a determination about how evidence combines, which the
deployment's policy makes.

Naming regimes is not thereby unconstrained. The reconciliation server MUST
verify that every regime the Applicable-Regimes Set names is one the policy-epoch
store admits for that predicate, and MUST refuse a claim naming a regime that is
not, returning a Remediation Advisory identifying it. Without that check a
requester enumerates admissible regime sets, reads out of the Outputs it receives
which operator, threshold and reliance interval each resolves to, and selects the
combination that returns the answer it wants -- taking the longest reliance
interval with it. That is verdict shopping at one remove. There is nothing to probe for: {{read-signing}}
requires the server to publish the resolved operator, its parameters and the
reliance interval per predicate and regime set, so the mapping is available
without probing and the admitted-regime check is what constrains the choice.

Three rules apply to every operator and take precedence over the operator's own
table:

- The Addressed-Registers Identifier Set MUST NOT be empty, and a Combined
  Verdict MUST NOT be computed over an empty contribution set. Every operator
  below is defined by a condition universally quantified over the contributions,
  so every one of them is vacuously satisfied where there are none: conjunction
  yields `match`, disjunction and threshold-count yield `no-match`, and the two
  rules that follow -- both of which begin "where any" -- do not fire, because
  there is no contribution to be indecisive. A decisive verdict from no evidence
  at all is the failure mode the rest of this section is built to prevent, and
  it is reached not by an operator behaving badly but by every guard being true
  of nothing. A relying party MUST reject an Output whose Addressed-Registers
  Identifier Set is empty, and MUST NOT treat its Combined Verdict as a verdict.
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

Operators are drawn from the registry of {{iana}}. Subject to those rules, the
initial four are:

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
  threshold resolved for the named regimes. `no-match` where the count
  of `match` contributions cannot reach the threshold and no contribution is
  `indeterminate`. `indeterminate` otherwise, which includes every case in which
  an `indeterminate` contribution is present and the threshold is not met.
  `partial-match` contributions do not count toward the threshold.

source-class-quorum:
: threshold-count evaluated per source class, over the partition and the
  per-class threshold resolved for the named regimes, then combined across
  classes by conjunction. A source class containing no addressed register
  contributes `indeterminate` and MUST NOT contribute `no-match`. Without that
  rule the class is threshold-count over nothing: the count of `match`
  contributions cannot reach a threshold of one or more, no contribution is
  `indeterminate` because there is no contribution, and the class yields a
  decisive negative built on an empty class -- which conjunction then propagates
  to the Combined Verdict. The `indeterminate`-substitution rule above does not
  reach it, because that rule governs evidence that is present and inconclusive
  and this is evidence that is absent. Suppressing a hit by partitioning it into
  a class with no members in it is a decisive negative assembled out of the
  partition, and the partition is resolved from the policy-epoch store rather
  than from the registers actually addressed.

Every operator admits `partial-match` except threshold-count and
source-class-quorum, which do not. Where {{verdict-retyping}} would re-type a
contribution to `partial-match` under an operator that does not admit it, the
contribution is re-typed to `indeterminate` instead.

## Reconciliation Output {#reconciliation-output}

A Reconciliation Output comprises:

- Reconciliation Event Identifier
- Reconciliation Identifier
- Claim Hash
- Reconciliation Timestamp
- Reliance Horizon of {{entitlement}}
- Audience Set of {{entitlement}}
- Combined Verdict
- Verdict Arithmetic as resolved under {{verdict-arithmetic}}, together with
  every parameter that operator takes -- the threshold for threshold-count, and
  both the source-class partition and the per-class threshold for
  source-class-quorum
- Addressed-Registers Identifier Set, each member an Authority Origin, sorted in
  bytewise lexicographic order of its UTF-8 encoding
- Bilateral-Register-Agreement Hash Set, sorted in bytewise lexicographic order
  of the digests themselves, in the order of the Addressed-Registers Identifier
  Set having no meaning once a register may be absent from a set
- Policy-Version Hash
- Pattern-Library Version Identifier
- Requester-Binding Class
- Per-Register Result Set, one entry per addressed register, ordered by Register
  Identifier in bytewise lexicographic order of its UTF-8 encoding
- Aggregation-Method Descriptor, drawn from the registry of {{iana}}
- Merkle Root, constructed as in {{merkle-construction}}
- Server-Recorded Divergence-Axis Set, possibly empty
- OPTIONAL Override Record, present exactly where an Adversarial
  Pre-Transmission Test failure was overridden
- Sealing-Key Identifier
- Sealing Signature, a COSE_Sign1 by the reconciliation-server sealing key whose
  payload is the CBOR array of this Output with the Sealing Signature position
  alone encoded as CBOR null, so that it covers every other field including the
  Sealing-Key Identifier

The Reconciliation Event Identifier is a 16-octet value drawn from a
cryptographically secure random source at the start of a reconciliation, unique
to that reconciliation across the life of the deployment.

The Reconciliation Identifier is the Claim Hash concatenated with the
Policy-Version Hash concatenated with the Reconciliation Event Identifier.

Earlier revisions omitted the third component, and the first two are both
reproducible functions of enumerated inputs. Two reconciliations over one claim
under one policy state therefore shared an identifier, and the protocol keys
three mechanisms on it that each assume it names one event:

- A register's own read under {{read-operations}} is keyed on the Reconciliation
  Identifier, and exists so that a server cannot discard a register's signed
  `match` and record `register-unresponsive` while the only party holding the
  contradicting artefact has no operation with which to produce it. Where two
  reconciliations shared the identifier, a server could record the register's
  `match` in the first and suppress it in the second, and serve the first to the
  register's audit read. The register sees its answer faithfully recorded and
  the suppression is invisible.
- The Query Binding of {{partial-attestation}} carries the Reconciliation
  Identifier so that an attestation is admissible only into the reconciliation
  that elicited it. Every element of that preimage was identical across the two,
  so an attestation elicited in the first verified unchanged inside the second.
- The Non-Answer Statement carries it so that a refusal elicited in one
  reconciliation is not admissible as a refusal in another over the same subject
  and predicate — which, under unchanged policy, is precisely when the
  identifier repeated.

The three protections were each written against the same assumption and the
assumption was not established anywhere. A retroactive supersession under a
Source-Data Version trigger leaves the policy state unchanged by definition, so
the identifier repeated on the path the document itself constructs, not only on
one a requester might contrive. The Event Identifier is what the three
mechanisms were already relying on.

It is carried in the Output as its own field, so it is inside the Reconciliation
Hash preimage: two reconciliations that address no register and are sealed in
the same second would otherwise produce one Reconciliation Hash, which is the
ledger index and the retrieval key, and no field distinguishing them.

The Event Identifier is not a secret and carries no requester-supplied content.
It is random rather than a counter so that it discloses nothing about
reconciliation volume to a register or to a relying party, and 16 octets rather
than 32 because it needs only uniqueness within a deployment.

The Claim Hash binds the Output to the question it answers. Without it a relying
party receives a Combined Verdict with nothing to attribute it to, and the
Retroactive Evaluation Subsystem has no key to select on.

The Verdict Arithmetic and its parameters are carried because a relying party
cannot otherwise reproduce the combination from the Per-Register Result Set, and
because {{verdict-retyping}} turns on which values the operator admits. The
Applicable-Regimes Set is a Canonical Claim field and is not itself carried in
the Output, so naming the operator without its parameters would leave
threshold-count and source-class-quorum irreproducible. `source-class-quorum` is
threshold-count evaluated per class and therefore takes a threshold as well as a
partition; carrying the partition alone would leave it as irreproducible as
carrying neither, which an earlier revision did.

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
  Claim Projection where a projection was transmitted, the Applied-Parameter
  Set the register reported where the Answer State is `answered`, and the
  Subject Mapping Record of {{subject-mapping}}; required
  wherever a projection was transmitted and either the projection narrowed or
  the Profile Parameter Set was non-empty
- Query Binding Record, present exactly where the Answer State is `answered`,
  comprising the Projected Predicate, the Subject Reference and the
  Reconciliation Nonce the server transmitted, and the register's signed Partial
  Attestation
- Non-Answer Statement, present exactly where the Answer State is `not-answered`
  and the Non-Answer Reason is register-attested under {{no-answer}}, comprising
  the Projected Predicate, the Subject Reference and the Reconciliation Nonce the
  server transmitted, and the register's signature over them together with the
  reason and the Reconciliation Identifier, as {{no-answer}} constructs it. The
  three projection values are carried here as well as in the Query Binding Record
  because the two are never both present and a verifier of either needs the
  preimage in the artefact it holds.

Each member of the Server-Recorded Divergence-Axis Set is a two-element array of
a Divergence Axis and the Register Identifier it concerns, the second element
being CBOR null where the axis concerns the reconciliation as a whole. Members
are sorted in bytewise lexicographic order of that encoding. A uniform two-element
member with an explicit null, rather than a member that is sometimes a pair and
sometimes a scalar, is what makes the Set's contribution to the Reconciliation
Hash determinate. Of the axes recorded by the server,
`freshness-stale` and `declared-not-determined` are per-register and MUST carry
a Register Identifier. `source-version-skew` is a relation between two or more
registers, and one member MUST be added for each register involved, so that the
set is a determinate function of the inputs rather than a choice between them; `register-threshold-divergence`
concerns the reconciliation and MUST NOT. `agent-action-scope-divergence` is
likewise a relation, between two capsules rather than between two registers, and
one member MUST be added for each Register Identifier whose contribution the
divergence concerns, or a single member carrying null where it concerns no
register's contribution; the rule is stated for all five axes and not four
because the Set is inside the Reconciliation Hash preimage, so an axis whose
member form is left open gives one reconciliation two ledger indices.
Recording a bare axis over five
addressed registers would state that something was stale without stating what,
which is not reproducible.

The Set is a set rather than a single value: a reconciliation may be qualified
on more than one axis, and an encoding admitting only one would force an
implementation to choose between them silently.

A Reconciliation Output is encoded as a CBOR array in the field order of this
section, an absent OPTIONAL or conditionally absent field encoded as CBOR null so
that position is preserved and the array's length is fixed. The Per-Register
Result Set is an array of arrays, each in the field order enumerated above, under
the same rule. The order is normative because the Reconciliation Hash is taken
over it, and because a CBOR map would be re-sorted into bytewise lexicographic
key order under Section 4.2.1 of {{RFC8949}}, which would override it.

The Reconciliation Hash is the SHA-256 digest over that same CBOR array with the
Sealing-Key Identifier and Sealing Signature positions encoded as CBOR null. The
array's length is unchanged: "excluding" means null-substitution at fixed
positions and MUST NOT be implemented as truncation, because a shorter array
carries a different CBOR array header and therefore a different digest, and two
implementations reading "excluding" the two ways would never agree on a ledger
index. It is the value recorded in the Settlement-Layer Ledger, the value a
Post-Seal Evaluation Record references, and the retrieval key of
{{ledger-read}}.

Determinism under Section 4.2.1 of {{RFC8949}} fixes how a given value is
encoded. It does not fix which CBOR type a field takes, nor the order of
elements within a field that is a set. The Reconciliation Hash is the ledger
index of {{settlement-ledger}}, the retrieval key of {{ledger-read}}, and a
value {{request-binding}} has the requester compute over an Output it has just
been handed, so two parties compute it independently and MUST obtain the same
value. The types are therefore fixed here, as {{bra-hash}} fixes them for the
Agreement Hash and {{iana}} fixes them for a Ledger entry.

| Field | CBOR encoding |
|---|---|
| Reconciliation Event Identifier | byte string of 16 octets |
| Reconciliation Identifier | byte string of 80 octets, the Claim Hash followed by the Policy-Version Hash followed by the Reconciliation Event Identifier |
| Claim Hash, Policy-Version Hash, Merkle Root | byte string of 32 octets |
| Reconciliation Timestamp, Reliance Horizon | text string, in the form fixed below |
| Combined Verdict | text string, one of the four values of {{terminology}} |
| Verdict Arithmetic and its parameters | two-element array: the operator identifier as a text string, and its parameters as an array, empty for conjunction and disjunction, a one-element array of the threshold as an unsigned integer for threshold-count, and a two-element array of the source-class partition and the per-class threshold for source-class-quorum |
| source-class partition | array of two-element arrays of the class identifier as a text string and the sorted array of Register Identifiers in that class, the outer array sorted by class identifier |
| Addressed-Registers Identifier Set | array of Authority Origins as text strings, sorted as {{reconciliation-output}} states |
| Bilateral-Register-Agreement Hash Set | array of 32-octet byte strings, deduplicated, sorted |
| Pattern-Library Version Identifier | text string |
| Requester-Binding Class | text string |
| Aggregation-Method Descriptor | text string |
| Audience Set, Per-Register Result Set, Server-Recorded Divergence-Axis Set | array of arrays, each member in the field order its own section enumerates |
| Override Record | array in the field order of {{adversarial-test}}, or null |
| Sealing-Key Identifier | two-element array of the Authority Origin as a text string and the JWK thumbprint as a text string |
| Sealing Signature | byte string, the serialised COSE_Sign1, or null in a preimage |
| Register Identifier | text string |
| Answer State, Attested Verdict, Effective Verdict, Non-Answer Reason, Re-Typing Ground, Subject Mapping Descriptor | text string |
| Divergence-Axis Field | array of two-element arrays of the axis identifier as a text string and its Register Identifier or null, sorted by the deterministic encoding of the member |
| Query Binding Record, Non-Answer Statement, Projection Record | array in the field order its own section enumerates, or null |

The Bilateral-Register-Agreement Hash Set is deduplicated because two addressed
registers may be governed by one Agreement, and an implementation that carried
the digest twice and one that carried it once would compute two Policy-Version
Hashes and two Reconciliation Hashes from identical inputs.

Every timestamp this document places inside a digest preimage or a signature
payload MUST be expressed in the form `YYYY-MM-DDTHH:MM:SSZ`: {{RFC3339}} with the
`Z` designator rather than a numeric offset, and with no fractional seconds.
{{RFC3339}} admits several renderings of one instant, and a preimage that admits
several renderings admits several digests.

CBOR rather than {{RFC8785}}: the mandatory-to-implement encoding for a
Reconciliation Output is CBOR, and several of its fields are byte strings, for
which JSON has no type. Digesting a JSON rendering of it would require a
CBOR-to-JSON mapping this document does not define, and two implementations
would produce different ledger indices. The Canonical Claim is serialised under
{{RFC8785}} and that serialisation is carried as one element of the CBOR array
the Claim Hash is taken over; the Reconciliation Output is CBOR throughout.

A Reconciliation Output is immutable once sealed. Conditions arising after
sealing are recorded under {{post-seal}} and MUST NOT be represented as fields
of the Reconciliation Output.

## Output Entitlement and Delivery {#entitlement}

The Reconciliation Output is the confidential artefact of this protocol and the
Settlement-Layer Ledger is its public one. An Output carries subject references,
register-signed Partial Attestations and principal identifiers; a Ledger entry carries digests, register origins and structural
metadata, and no claim, register-record or principal content. Every rule in this
document about who may see what rests on that division, and they are not
interchangeable. A party admitted to a Ledger read learns nothing of the subject
or the answer. A party holding an Output already holds the content of
one reconciliation, and admitting it to reads about that same reconciliation
discloses nothing it does not have.

Earlier revisions had no answer to who may hold an Output. It was a bearer
artefact: possession was the whole of the entitlement, it never expired, and
every read predicate this document attempted was expressed in terms of a
Requester-Binding that the reader could not present and the Ledger could not
evaluate. This section supplies the missing term.

### Audience {#audience}

A Reconciliation Output carries an Audience Set of zero or more Audience Members,
encoded as a CBOR array which is empty only in the case described below.
Each Audience Member comprises:

- an Audience Member Identifier: a URI, in the same identifier space a
  Requester-Binding uses for an accountable principal, encoded as a CBOR text
  string. Two Audience Member Identifiers are equal where they do not differ
  after normalisation under Sections 6.2.2 and 6.2.3 of {{RFC3986}}; comparison
  is over the normalised form and is otherwise bytewise, and an implementation
  MUST encode the normalised form rather than normalise on receipt, for the
  reason {{terminology}} gives for an Authority Origin. It is a sort key inside
  the Audience Set and so inside the Reconciliation Hash preimage, the first
  element of every Witness Entry and so inside the Agreement Hash, and the
  equality target of the quorum rule of {{quorum-rule}}; the same treatment is
  given to an Operating-Party Identifier and was not given here
- a Verification Method Reference: the JWK thumbprint, computed as in
  {{RFC7638}}, of the public key under which that member signs a read request
  under {{ledger-read}}. It MUST be a durable key and MUST NOT be a session
  credential or a one-time request signature, because the member has to present
  it long after the reconciliation is over

Audience Members are sorted in bytewise lexicographic order of the deterministic
CBOR encoding of the Audience Member Identifier, and each member is encoded as a
two-element array in the field order above. Ordering is stated because the
Audience Set is inside the Reconciliation Hash preimage, and an unordered set
would give one Output as many hashes as it has permutations.

The server MUST NOT require proof of possession from a named member at
reconciliation time -- the member is typically not present -- and naming one is
therefore an assertion by the Requesting Principal, not a fact about the member.
Two consequences follow and are stated so that neither surprises. Naming a party
places a row in that party's `GET /arp/outputs` enumeration and in the server's
access log that the party did not ask for, so a deployment SHOULD constrain who
may be named through the audience constraint below and through the enrolment
requirement of {{request-binding}}. And a member that loses or
rotates the key its thumbprint names loses entitlement to every Output that names
it, permanently, because the Audience Set cannot be amended after sealing; a
member that expects to rely on Outputs over time SHOULD be named by a thumbprint
of a key held for that purpose.

The Requesting Principal is an Audience Member of every Output performed on its
behalf where it can be identified: by its accountable-principal identifier where
the Requester-Binding carries one, and otherwise as below. Where it does not -- classes `agent-unverified`
and `agent-key-verified` -- the Set carries a member whose Identifier is the URI
form of the verified signing key's thumbprint. Every requester signs, by
{{read-signing}}, so there is always a key to name and an Audience Set is never
empty.

Further members are named in the reconciliation request, are enumerated inputs
for the purposes of {{architecture}}, and are sealed with the rest of the
Output. The Audience Set MUST NOT be enlarged after sealing; naming a
further member requires a new reconciliation, which is a new question and gets a
new answer.

A Bilateral Register Agreement MAY declare an audience constraint: a maximum
cardinality, a permitted class of member, or both. Where the Audience Set exceeds
the constraint an addressed register declares, the reconciliation server MUST NOT
transmit a projection to that register and MUST record
`audience-constraint-exceeded` as its Non-Answer Reason. It MUST NOT refuse the
reconciliation, and MUST NOT quietly drop the register: the first leaves no
artefact stating why, and the second is the addressed-register-cherry-picking
{{no-answer}} exists to prevent. The reconciliation is sealed and, by
{{verdict-arithmetic}}, cannot reach a decisive Combined Verdict.

The requester is not a party to any Bilateral Register Agreement and cannot read
the constraint, so it learns the cap from the reason recorded against that
register rather than by inspection. A register that attests about a subject is
entitled to bound how widely that attestation travels, and a constraint enforced
after transmission would be enforced too late. The constraint is enforced by the
reconciliation server on the register's behalf and the register cannot verify
that enforcement from any artefact this document defines; a register that requires
assurance of it should negotiate an audit right in its agreement.

A party MUST NOT be treated as entitled to a Reconciliation Output by possession
alone. A relying party that has been handed an Output and is not an Audience
Member of it MAY verify its Sealing Signature and read its Combined Verdict --
nothing prevents this, and the signature is what makes the Output worth handing
on -- but it obtains no read under {{ledger-read}}, learns nothing of
supersession or post-seal evaluation, and MUST NOT treat the verdict as current.
Reliance without entitlement is reliance on a snapshot of unknown age.

### Reliance Horizon {#reliance-horizon}

A Reconciliation Output carries a Reliance Horizon: a time in the form of
{{reconciliation-output}}, being the Reconciliation Timestamp advanced by the
reliance interval the reconciliation server resolves from the policy-epoch store
of {{sealing}}, keyed on the predicate and the regimes the claim names, exactly
as it resolves the Verdict Arithmetic under {{verdict-arithmetic}}. A requester
able to set its own reliance interval could set its own staleness window, which
is the same defect as choosing its own Verdict Arithmetic. After that time an Audience
Member MUST NOT treat the Combined Verdict as current without having read the
Continuation entries for its Reconciliation Hash under {{ledger-read}} and found
no supersession.

The Horizon does not invalidate the Output and does not weaken the Sealing
Signature: what was sealed remains true of the moment it was sealed. It bounds
reliance, not validity. A sanctions `no-match` is a statement about consolidated
lists as they stood, and those lists change on a daily cadence
({{profile-sanctions}}); an artefact that asserted such a verdict indefinitely
and carried no marker of its own staleness would be relied upon indefinitely,
which is the failure {{retroactive}} exists to prevent and could not, having no
way to reach the party that had relied.

The Reliance Horizon is derived from the Reconciliation Timestamp and is
therefore outside the reproducibility requirement of {{architecture}} on the same
ground.

### Delivery {#delivery}

The reconciliation server MUST return the sealed Reconciliation Output to the
Requesting Principal in the response to the request that commissioned it, in the
form {{request-binding}} states. Where the Adversarial Pre-Transmission Test emitted
a Remediation Advisory, the server returns that Advisory and no Output. {{request-binding}} enumerates the
responses to a commissioning request. A refusal under {{containment}} or an
audience constraint under {{audience}} is not among them: those refuse a register
and not the reconciliation, so an Output is produced and delivered, carrying the
reason against the register it concerns.

That the server returns the Output is stated because nothing in earlier revisions
did. The document specified in detail what an Output contains, how it is sealed,
digested, ledgered and notarised, and never that any party receives one. Every
discovery path in this document begins with a party holding a Reconciliation
Hash, and it holds one because of this paragraph.

An Audience Member other than the Requesting Principal is not delivered to. It
retrieves under {{ledger-read}}: the server has no channel to a party it has
never spoken to, and pushing a confidential artefact to an address named by
somebody else is not a mechanism this protocol should define.

The Reconciliation Hash is the retrieval key and is not reproducible across runs
({{architecture}}), so a party that has discarded it cannot recompute it, and the
Reconciliation Identifier is no help because the Claim Hash within it is blinded
under {{sealing}} and cannot be computed outside the deployment. The server MUST
therefore also answer the enumeration of {{ledger-read}}, returning to an
authenticated principal the Reconciliation Hashes of the Outputs whose Audience
Set names it. Without it, an Audience Member that has lost a 32-byte value has
lost every entitlement this section grants it, permanently and silently.

The server MUST retain each sealed Output, and MUST answer reads of it and of its
Continuation entries, for the retention period, which is the LONGEST period any
Bilateral Register Agreement addressed by that reconciliation declares, and in no
case ending before the Reliance Horizon advanced by one further reliance
interval. Where two agreements declare different periods the longest governs. That
direction is specific to a retention period, which is a floor: the shortest
declaration would let one register's agreement extinguish another's.

Wherever else this document takes a value from a plural set of agreements, the
direction is the one that makes the obligation stricter, and it is stated at each
site. For every interval that bounds a deadline -- the ledger-head notarisation
interval of {{settlement-ledger}}, and the Evaluation Sweep and supersession
deadlines measured against it -- the SHORTEST declaration governs. Taking the
longest there would let one permissive agreement postpone every deadline for
every other register, which inverts the obligation instead of strengthening it.
For the read rate limit of {{read-errors}}, the most permissive declaration
governs, a rate limit being a ceiling on the server's refusals rather than on its
duties.

The extra interval matters. {{reliance-horizon}} requires an Audience Member to
read before relying past the Horizon, and entitlement is evaluated against the
Audience Set of the retained Output; a retention floor that ended exactly at the
Horizon would permit the server to discard the basis of that evaluation at the
moment the obligation begins, and the member would receive the `404` of
{{read-errors}} -- indistinguishable, by design, from never having been
entitled.

## Policy-Version-Hash Sealing {#sealing}

The Policy-Version Hash MUST commit to:

1. Reconciliation rules
2. Threshold parameters
3. Pattern-Library Version Identifier
4. Applicable-Regimes precedence
5. Verdict-Arithmetic selection, together with every parameter that operator
   takes
6. The reliance interval from which the Reliance Horizon of
   {{reliance-horizon}} is computed
7. Agent-IFF policy identifier and the Requester-Binding
8. Bilateral-Register-Agreement Hashes of the addressed registers

The Policy-Version Hash is the SHA-256 digest over the deterministically encoded
CBOR array

    ["arp-policy-version-v1", Deployment Blinding Value,
     reconciliation rules identifier, threshold parameters,
     Pattern-Library Version Identifier, applicable-regimes precedence,
     [Verdict Arithmetic, its parameters], reliance interval,
     Agent-IFF policy identifier, Requester-Binding,
     Bilateral-Register-Agreement Hash Set]

in that order, the Hash Set sorted in bytewise lexicographic order of the digests
and every other composite element a CBOR array in the order this section states
it. It MUST be reconstructible under audit from that array, held in the
policy-epoch store. A value every addressed register echoes and every auditor
recomputes cannot be left to "a canonical policy state", which earlier revisions
were content with and which is not a preimage.

The Claim Hash and the Policy-Version Hash MUST each be computed over a preimage
that includes the Deployment Blinding Value: a secret of at least 128 bits drawn
once from a cryptographically secure random source, persisted in the
policy-epoch store, constant for the life of the deployment, and disclosed
outside the policy-epoch store only as {{audit-path}} provides. {{audit-path}}
discharges an auditor's need as far as it can without disclosing the constant
that blinds every digest in the deployment, and states what that leaves
unverified.

It is constant rather than per-claim, and that is what makes it compatible with
the rest of this document. The Claim Hash remains a deterministic function of
the canonical claim fields within a deployment, so it remains usable as the
Settlement-Layer Ledger index and as the retroactive-evaluation key, and the
reproducibility requirement of {{architecture}} continues to hold: the same
deployment given the same enumerated inputs produces the same digests. What
changes is that the preimage is no longer guessable from outside the deployment.
A per-claim random value would defeat all three properties.

Both digests are otherwise taken over low-entropy preimages: a subject
identifier is typically a company number of ten or so digits, a predicate is
drawn from a published taxonomy, and the accountable principal, agent-IFF policy
identifier and verdict arithmetic are each drawn from small enumerable sets
within one deployment. Both digests then appear where adversaries can reach
them -- the Policy-Version Hash in the protected header of every notarised
Signed Statement and in every reconciliation entry of the Ledger, the Claim Hash
in the Output and in every Ledger entry of either kind. Without blinding, anyone holding either can recover by exhaustive search
the subject that was investigated and the principal that commissioned the
reconciliation, which is the disclosure this protocol exists to prevent.
Blinding does not weaken reconstructibility under audit, since the Blinding
Value is persisted with the state it blinds.

A register receives the same Policy-Version Hash as every other addressed
register, by {{projection}}. The Blinding Value prevents two colluding registers
from recovering the Addressed-Registers Identifier Set from it by search; that
they can observe they were addressed together is inherent and is discussed in
{{side-channel}}.

Equality is a different matter from inversion. The Requester-Binding is an
element of the preimage and every other element is fixed by policy and by the
addressed register set, so one requester asking repeatedly about different
subjects presents every addressed register with the same Policy-Version Hash. A
register cannot recover who that requester is, and can group every reconciliation
that requester commissioned against it. Two registers addressed together can join
their traffic on the same value, as can any reader of the notarised Signed
Statements, in which the hash appears in the protected header. That is a stable
requester pseudonym, disclosed to parties {{containment}} otherwise limits to the
Requester-Binding Class, and reasoning about the preimage's resistance to search
says nothing about it: a correlation handle does not need to be inverted to work.

A deployment for which that is unacceptable MUST substitute, in the seventh
element, a digest over the Requester-Binding and the Reconciliation Identifier.
The Policy-Epoch Store holds both, so an auditor can still reconstruct the
preimage, and the element then varies per reconciliation and carries no
cross-reconciliation handle. It is stated as a deployment choice rather than a
requirement because the constant form is what lets a register recognise a
returning counterparty under a bilateral agreement, which some deployments need
and others must not have. Discussed further in
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
- a Post-Seal Evaluation Timestamp, in the form of {{reconciliation-output}}
- an Attribution Account, present exactly where the Qualifier is
  `attribution-indeterminate`: a text string stating which of the two candidate
  causes were examined and why neither could be excluded. A bare qualifier would
  be a discretionary escape signed by the party that benefits from it
- a Sealing-Key Identifier
- a signature by the reconciliation-server sealing key, a COSE_Sign1 whose
  payload is the CBOR array of this record with the signature position encoded as
  CBOR null

A Post-Seal Evaluation Record is encoded as a CBOR array in the field order
above, an absent conditionally-absent field encoded as CBOR null so that position
is preserved. The Post-Seal Evaluation Record Hash of {{settlement-ledger}} is the Signing
Input Digest of that record's signature. Earlier revisions took it over the
array in its entirety with the signature included, on the ground that the digest
should be over the artefact as served under {{ledger-read}}. That ground does
not hold: under a signature primitive whose encoding is not byte-unique the
artefact as served is not one byte-string, and a digest over it names whichever
copy the reader was handed. {{signature-malleability}} states the measurement.

A Post-Seal Evaluation Record MUST be retained by the reconciliation server for
the period of {{delivery}}, and a Continuation entry of type
`continuation-post-seal-record` MUST be appended to the Settlement-Layer Ledger
carrying the record's hash. The hash is not written into the entry that recorded
the reconciliation: that entry is already signed and the Ledger exposes no
UPDATE. An Audience Member of the Output discovers the record by reading the
Continuation entries for its Reconciliation Hash under {{ledger-read}} and
retrieves it by its hash under the same binding. The record travels as the
`result` element of the signed read response of {{read-responses}}; the media
type registered for the record labels it wherever it is carried outside that
envelope, and the Post-Seal Evaluation Record Hash is taken over the record
itself and not over the response that carried it. A record emitted but not appended would be undiscoverable, which would
make the attribution safety valve of {{source-versioning}} unreachable in exactly
the case it exists for.

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

The Ledger carries two kinds of entry. A reconciliation entry records a sealed
Reconciliation Output. A Continuation entry records a fact that arose after that
Output was sealed and therefore could not be a field of it. Every entry carries
an Entry Type drawn from the registry of {{iana}}, and the Entry Type determines
which further fields the entry carries. An entry whose Entry Type is not
`reconciliation` is a Continuation entry. Without a discriminator a verifier
reading an entry cannot tell which field list to apply, and an entry legitimately
lacking a field would be indistinguishable from one that is malformed.

Every entry, of either kind, comprises these fields and in this order:

- Entry Sequence Number, a strictly increasing integer with no gaps: the first
  entry of a chain is 1 and each subsequent entry is its predecessor's plus one.
  Contiguity is required because the consistency read of {{read-operations}}
  cannot otherwise distinguish a sequence number the operator never allocated
  from one it is refusing to answer for, the two being the same `404` by
  {{read-errors}}
- Entry Type, from the ARP Ledger Entry Types registry of {{iana}}
- Claim Hash, the index of {{architecture}}
- Reconciliation Hash of the Reconciliation Output the entry concerns
- Entry Timestamp ({{RFC3339}} UTC), the time at which the entry was appended
- Prior-Entry Hash, being the Signing Input Digest of the immediately preceding
  entry's Entry Signature; in the first entry of a chain, which has no preceding
  entry, thirty-two zero octets. It is taken over that entry's signing input and
  not over the entry as served, so that a reader handed any byte-string carrying
  that entry's signature computes one value. It still commits to every field of
  the preceding entry, including that entry's Self-Entry Hash, and to the
  Sealing-Key Identifier and the algorithm identifier in the protected header,
  because the `Sig_structure` covers all of them

followed by the type-specific fields enumerated below, followed by:

- Self-Entry Hash, being the SHA-256 digest over the CBOR array of this same
  entry with the Self-Entry Hash and Entry Signature positions encoded as CBOR
  null, encoded under the Core Deterministic Encoding Requirements of Section
  4.2.1 of {{RFC8949}}, so that the array's length is the length fixed by the
  Entry Type and is the same array a verifier already holds. The encoding
  requirement is stated here and not left to be inferred from
  {{cbor-cose}}: without it a definite-length and an indefinite-length encoding
  of one entry yield two Self-Entry Hashes, and the head comparison of this
  section treats that as a fork, which obliges every reader of the second
  encoding to act under {{ledger-replication}} against an operator that
  equivocated about nothing
- Entry Signature, a COSE_Sign1 by the reconciliation-server sealing key whose
  payload is the CBOR array of this same entry with the Entry Signature position
  alone encoded as CBOR null -- so it covers every other field including the
  Self-Entry Hash -- and whose protected header carries the Sealing-Key
  Identifier that resolves it

An entry is encoded as a CBOR array in the field order of this section, an absent
field -- whether marked OPTIONAL or conditionally absent under a stated condition
-- encoded as CBOR null, so that position is preserved and the array's length is
fixed by the Entry Type. Absence MUST be encoded and MUST NOT be expressed by a
shorter array: two encodings of one entry would otherwise yield two Self-Entry
Hashes, which the head comparison of this section treats as a fork. The
order is normative because the Self-Entry Hash is taken over it; an encoding as a
CBOR map would be re-sorted by key under the Core Deterministic Encoding Requirements of Section 4.2.1 of {{RFC8949}} and would override it. A field whose value is itself a choice --
the second field of a `continuation-notarisation` entry -- is encoded as a
two-element array of a discriminant and a value, the discriminant being the CBOR
text string `entry-id` or `refused`.

The Self-Entry Hash is enumerated after the type-specific fields so that it
covers them. Placing it before them would leave a Continuation entry's payload
outside it. The Prior-Entry Hash is taken over the preceding entry's signing input rather
than over that entry's Self-Entry Hash, so that the Sealing-Key Identifier and
the algorithm identifier under which that entry was signed are inside the chain.
Were the chain to link Self-Entry Hash to Self-Entry Hash, neither would be
covered by anything, and an operator could re-sign every historical entry under
a revoked or unresolvable key while every hash in the chain, and every head
already published and notarised, continued to verify.

The signature bytes themselves are deliberately outside the chain, and this is
a change from earlier revisions, which took the Prior-Entry Hash over the whole
preceding entry so that Entry Signatures were inside it. That is not
recoverable: {{signature-malleability}} measures a primitive under which one
signing act has many verifying encodings, so a chain keyed on those bytes breaks
for a reader handed a different one. What the chain binds is the identity of the
signing act rather than the bytes of one encoding of it.

**Two things earlier revisions detected are no longer detectable and are stated
here rather than left to be discovered.** Stripping a historical Entry Signature
while leaving its protected header and payload intact moves no Prior-Entry Hash.
So does re-signing an entry under the same key and header. The Sealing-Key
Identifier and the algorithm remain covered, so a re-signature under a
*different* key or algorithm still moves the chain, which is the case the
paragraph above is about; a re-signature under the same key does not.

An entry is signed exactly once. A second signature over the same fields is a
different entry, MUST NOT be appended at the same Entry Sequence Number, and MUST
NOT replace the first.

Under the Prior-Entry Hash of this section that rule has no verifier-side test,
and saying so is better than implying one. A Signing Input Digest is a value per
signing input, not per signature, so two signings of one entry share it and
yield one chain and one head rather than the two divergent chains an earlier
revision relied on to make the violation visible. The rule is therefore an
operator obligation an Audit Identity under {{audit-path}} can examine and a
reader cannot, which is the price of the digest being stable under
{{signature-malleability}}, and is paid deliberately: a rule that is unenforceable
against an honest reader is better than a chain that breaks for one.

The Entry Timestamp is distinct from the Reconciliation Timestamp. A
Continuation entry may be appended weeks after the reconciliation it concerns,
and an entry carrying only a Reconciliation Timestamp would state that the
notarisation, the post-seal evaluation or the supersession occurred at the
moment of the reconciliation, which is false in every case the mechanism exists
for.

An entry whose Entry Type is `reconciliation` additionally comprises:

- Policy-Version Hash
- Addressed-Registers Identifier Set, each member an Authority Origin, sorted in
  bytewise lexicographic order of its UTF-8 encoding
- Aggregation-Method Descriptor
- Merkle Root
- Requester-Binding-Class Descriptor, one of the four classes enumerated in
  the Requester Identity Binding and Agent Friend-or-Foe Gate section
- Reconciliation Timestamp, as sealed in the Reconciliation Output
- OPTIONAL Source-Reconciliation-Output Identifier, being the Reconciliation
  Hash of the Output this reconciliation supersedes, present exactly where it
  supersedes one
- Override Indicator, true exactly where the Reconciliation Output carries an
  Override Record under the Adversarial Pre-Transmission Test

An entry whose Entry Type is `continuation-notarisation` additionally comprises:

- Transparency Service Identifier, being the Authority Origin of that service
- exactly one of the EntryID that service returned, or the HTTP status code by
  which that service terminally refused registration

Only the status code is recorded, never a response body. A body is authored by
the Transparency Service, is unbounded, and routinely echoes submitted content;
writing one into an append-only log with no DELETE would put text this document
does not control inside a record that forbids claim and principal content in the
clear.

A `continuation-notarisation` entry MUST be appended where notarisation
completes, and where the Transparency Service returns a status the implementation
resolves as a terminal refusal under {{async-registration}}. Where a
status cannot be so resolved -- the 404 of {{async-registration}} carries
two meanings and a service is not obliged to distinguish them -- it is not a
terminal refusal, and the reconciliation is treated as one whose polling bound
was exhausted. In that case no `continuation-notarisation` entry is appended and
the outcome is recorded under {{post-seal}} as `notarisation-incomplete`.
Requiring an entry only on failure would leave the successful case -- the case
the join exists for -- unrecorded.

Where an implementation subsequently learns the EntryID of a registration it had
recorded as incomplete, it MUST append the `continuation-notarisation` entry
then. This document defines no means by which it would learn that:
{{I-D.ietf-scitt-scrapi}} retrieves by EntryID and the EntryID is precisely what
was not received, polling is bounded, and no callback is specified. A
`notarisation-incomplete` record will therefore usually stand permanently, and it
is evidence that registration did not complete within the polling bound and not
that it failed. That is open.

An entry whose Entry Type is `continuation-post-seal-record` additionally
comprises:

- Post-Seal Evaluation Record Hash

An entry whose Entry Type is `continuation-supersession` additionally comprises:

- Material-Change Indicator, stating whether the Combined Verdict changed
  materially within the meaning of {{retroactive}}
- Superseding-Reconciliation Hash, being the Reconciliation Hash of the
  Reconciliation Output that supersedes the one this entry concerns, present
  exactly where a superseding Output was produced and absent where the
  supersession is the revocation of a Verified Principal Credential under
  {{retroactive}}, which supersedes an Output without producing another
- Superseding-Entry Sequence Number, being the Entry Sequence Number of the
  reconciliation entry that records the superseding Output, present under the
  same condition

No Continuation entry carries a retrieval URI. Every artefact a Continuation
entry points at is retrieved under {{ledger-read}}, by hash for a Post-Seal
Evaluation Record and by Reconciliation Hash for a superseding Output, from the
same authority origin that served the entry. Carrying a URI instead would oblige
every reader to dereference an operator-chosen address before it could check
anything -- a forced fetch, a de-blinding oracle correlating a reader's network
identity with one Reconciliation Hash, and a covert channel that no constraint on
the URI's content can close, since host selection and path structure carry the
signal without stating anything. It would also put a non-digest field in a Ledger
whose whole disclosure argument is that it holds digests.

A Reconciliation Output produced by Retroactive Evaluation to supersede an
earlier Output MUST carry the Audience Set and the Requester-Binding Class of the
Output it supersedes. Without that rule the party entitled to learn that its
verdict had changed would be entitled to the entry saying so and not to the
Output that says what it changed to, and the traversal would end one step short.
Such an Output has no commissioning request and is not delivered under
{{delivery}}; it is retrieved.

Where the superseding reconciliation addresses a register whose audience
constraint the inherited Audience Set exceeds -- which can happen, since the
superseding reconciliation may address registers the superseded one did not --
that register is recorded `audience-constraint-exceeded` under {{no-answer}} like
any other. The Audience Set is not truncated to fit: truncating it would strand
the party the supersession exists to notify, and the constraint is satisfied by
not obtaining that register's answer rather than by silencing the reader.

A party retrieving a Post-Seal Evaluation Record MUST reconstruct the
`Sig_structure` of that record's signature from the protected header and the
payload of the retrieved COSE_Sign1, MUST verify that its Signing Input Digest
equals the Post-Seal Evaluation Record Hash carried in the entry, MUST verify
that signature under the Sealing-Key Identifier the record carries, and MUST
discard the record where either check fails. The hash does not cover the
signature bytes, so the signature check is not redundant and a record served
with a substituted, absent or garbage signature satisfies the digest check
alone. Without both checks the hash is decorative and an operator can serve a
different record to each audience, reopening at the record the equivocation the
Ledger closes at the entry.

A Continuation entry carries no Policy-Version Hash, no Addressed-Registers
Identifier Set, no Aggregation-Method Descriptor, no Merkle Root and no
Requester-Binding-Class Descriptor. Those describe the reconciliation, which the
reconciliation entry already records and the Reconciliation Hash already binds;
carrying them a second time would create a second place for them to disagree. A
Continuation entry MUST carry the same Claim Hash and Reconciliation Hash as the
reconciliation entry it continues, and the storage interface layer MUST reject a
Continuation entry whose Reconciliation Hash matches no earlier reconciliation
entry, returning a rejection the appending subsystem can distinguish from a
transport failure. Because Entry Sequence Numbers are allocated in one sequence
and secondary stores replicate rather than originate, every store holds the
reconciliation entry against which the check is made.

Prior-Entry and Self-Entry Hashes establish that no entry has been removed from
a chain; they do not establish that only one chain exists. Signing each entry
makes a second chain attributable rather than merely possible.

A Reconciliation Output is sealed before it is notarised and so cannot itself
carry the EntryID, and the Ledger exposes no UPDATE, so the join cannot be made
by amending the original entry. It is made by appending. Without it a successful
notarisation would be unlinkable to the reconciliation from every side, since
retrieval is by EntryID and {{I-D.ietf-scitt-scrapi}} offers no query surface.

A `continuation-supersession` entry MUST be appended against the superseded
Output on every supersession, whether or not the change is material. Where the
supersession produced a superseding Output, the superseding reconciliation entry
MUST also carry the Source-Reconciliation-Output Identifier naming what it
replaced, and the two records are inverse pointers over one relation. Where it
did not -- the revocation of a Verified Principal Credential -- there is no
superseding entry and no second record, and the Continuation entry stands alone.
The Material-Change Indicator distinguishes a material supersession from an
immaterial one in either case. {{retroactive}} imposes
the further obligation of a Sovereign Re-Notification where the change is
material; it does not condition the ledger record, which is written either way,
since a party relying on a superseded Output needs to know it was superseded
before it can be told the change was immaterial.

Where both records exist they are inverse pointers over one relation and neither
substitutes for the other. A party holding the superseded Output cannot follow a pointer that
exists only on an entry it has not been returned, and a regulator whose scope
under {{regulator-portal}} covers the superseded reconciliation is not thereby
returned the superseding one, whose addressed registers and therefore whose
agreements may differ. The constraint is on what a reader is returned, not on
what a store holds.

The Ledger MUST NOT store Canonical-Claim content, register records,
Partial-Attestation payloads, or any principal identifier in the clear; the
requester's accountable principal is committed only through the Policy-Version
Hash. The append-only constraint MUST be enforced at the storage interface layer. The
Ledger interface MUST expose APPEND and READ operations only, with no UPDATE and
no DELETE operation exposed or implemented. Retroactive Evaluation and the
derivation-chain invariant check are subsystems of the reconciliation server and
read the Ledger without scope restriction. Every read by a party outside the
reconciliation server is served under {{ledger-read}}, which states the
operations, the entitlement each requires, the response form, and the error
semantics. Three entitlements reach the Ledger: a regulator's, governed by
{{regulator-portal}}; an Audience Member's under {{entitlement}}; and an Audit
Identity's under {{audit-path}}. A Register
Operator holds the narrower entitlement of the consistency check below.

An Audience Member is entitled to the Continuation entries carrying the
Reconciliation Hash of an Output that names it, and to the reconciliation entry
carrying that same Reconciliation Hash. It is entitled to no other entry. This is
the predicate earlier revisions could not express. It is evaluable, because the
Audience Set is a sealed field of the Output and the server retains the Output
under {{delivery}}; the Ledger is not asked to evaluate it, and could not, since
it stores no principal identifier in the clear. It admits the right party,
because entitlement follows the Output rather than the request, so a member the
Requesting Principal named at reconciliation time is admitted and a party that
merely came into possession of the artefact is not. And it survives the events
that broke its predecessors: an Audience Member's verification method is required
by {{audience}} to be presentable after the fact, and revocation of the
Requesting Principal's Verified Principal Credential does not remove the other
members of the Audience Set, so the supersession entry recording that revocation
has a reader.

Where an Output's Audience Set is reduced to members that can no longer
authenticate -- a single-member Set whose sole member's credential has been
revoked -- its Continuation entries are reachable only through the Regulator
Portal. The reconciliation MUST still have been performed with a
Requester-Binding class recorded under {{agent-iff-integrity}}, so the condition
is visible to the regulator that scope serves.

An Audience Member's read discloses only facts about a reconciliation whose full
content it already holds: that a supersession or a post-seal evaluation exists,
what it points to, and the ledger position of each. The one exception is worth
naming, because it is not obvious: a Post-Seal Evaluation Record carries the
Policy-Version Hash and Pattern-Library Version Identifier in force at the time
of the evaluation rather than at sealing, and those are values the member did not
previously hold and, being stable within a deployment, are durable correlators.
That is a deliberate disclosure to a party already entitled to the reconciliation
they qualify, and it is bounded by {{audience}}'s rule that a register may cap
how wide an Audience Set addressing it may be.

Where the Ledger is replicated per {{ledger-replication}}, each secondary store
MUST be able to demonstrate that its chain and every other secondary store's
chain share a common prefix.

A common-prefix demonstration between stores under one operator is that operator
attesting to itself. The reconciliation server MUST therefore publish a signed Ledger Head Statement
at `/.well-known/arp-ledger-head` on its Authority Origin. It is republished once
per notarisation interval and not on every append: the resource is unauthenticated
and carries a contiguous sequence number, so a continuously updated head would
hand any observer the deployment's exact entry count, its write rate and the
timing and size of every retroactive supersession burst -- the aggregate
disclosure {{read-errors}} rate-limits the authenticated surface to prevent. A
Statement comprises:

- the Entry Sequence Number of the current head
- the Self-Entry Hash of that entry
- the Entry Timestamp of that entry
- a Statement Timestamp, being the time the Statement was produced, in the form
  of {{reconciliation-output}}. Without it two Statements published across a
  quiet period differ only in their notarisation pointer and neither is dateable,
  so the interval a register negotiated is unverifiable from the artefact
- a two-element array of the Transparency Service Identifier and the EntryID of
  the most recent completed notarisation of a Ledger Head Statement, encoded as
  CBOR null until the first such notarisation completes
- a signature by the reconciliation-server sealing key over the foregoing,
  carrying the Sealing-Key Identifier that resolves it

A Ledger Head Statement is encoded as a COSE_Sign1 over the deterministically
encoded CBOR array of the first five items above, in that order, under the media
type registered in {{iana}}, with the fifth item encoded as CBOR null until the
first notarisation completes.
The server MUST notarise the Ledger Head Statement current at each interval into
a SCITT Transparency Service. The interval is the shortest declared by any
Bilateral Register Agreement, per the direction rule of {{delivery}}. The
Transparency Service MUST be one every Bilateral Register Agreement the
deployment holds declares,
and MUST NOT be operated by or under the control of the reconciliation server or
any party controlling it. A notary the operator owns is the operator attesting to
itself, which is the condition this mechanism exists to escape; the same
requirement governs the notarisation of Evaluation Sweep Statements under
{{sweep-statements}}.
It is not registered under the binding of {{scrapi-binding}}, which is scoped to
sealed Reconciliation Outputs and whose protected header requires a
Policy-Version Hash and a Bilateral-Register-Agreement Hash that a head statement
does not have; it is registered as a Signed Statement under its own media type.
Statements published between intervals are not notarised.

Entry Sequence Numbers are allocated in a single sequence for the logical Ledger.
A secondary store under {{ledger-replication}} replicates that sequence and MUST
NOT allocate independently, or two conforming stores would present the same
sequence number over different entries and be indistinguishable from a fork.

The Entry Sequence Number is what makes two heads comparable. A bare hash cannot
distinguish a fork from ordinary progress: two parties who have each seen a
different head learn only that the values differ, which is the expected case
whenever they observed at different times. Two Head Statements bearing the same
Entry Sequence Number and different Self-Entry Hashes are therefore a fork on
their face, and both are signed, so both are attributable.

Two Head Statements bearing different sequence numbers are reconciled by the
consistency read of {{read-operations}}. A party entitled to that read -- a
Register Operator or a regulator -- presents the lower of the two sequence
numbers and receives the Self-Entry Hash of the entry at that position in a
signed response bound to the request it answers. The two views agree only where
that value equals the one the lower Head Statement carried, and where they
disagree the party holds two signed statements by one key that cannot both be
true of one chain. That is why the response is signed and bound to its request:
an unsigned answer would let an operator serve each questioner from that
questioner's own branch and leave the questioner with nothing it could show a
third party.

The rate limit of {{read-errors}} is load-bearing on that operation and not
merely hygiene. The consistency read ranges over every sequence number up to the
head; swept without limit it yields the deployment's exact entry count by binary
search, its write rate by polling, and the timing and size of a retroactive
supersession burst by watching for a step change -- none of which any single
answer discloses.

A party that holds two irreconcilable signed statements MUST cease to rely on any
Reconciliation Output sealed by that server after the lower of the two sequence
numbers, MUST report the pair to every regulator whose Bilateral Register
Agreements it can identify from the Outputs it holds, and MUST NOT treat the
server's subsequent statements as evidence of anything until the discrepancy is
resolved. A Register Operator that holds such a pair MUST additionally
refuse further Per-Register Claim Projections from that server, on which the
server records `agreement-drift-suspended` against that register under
{{no-answer}} as it would for any other suspension. Detection without a
required response leaves the mechanism ending in a held contradiction and no
consequence.

Two limits remain and are stated rather than claimed away. An operator that
publishes to two audiences at disjoint sequence numbers never emits a colliding
pair, so detection by collision is opportunistic even though reconciliation by
consistency read is not. And a party holding neither a Reconciliation Output nor
a Bilateral Register Agreement has no register set against which to anchor the
signing key under {{sealing-key-discovery}}: it can check that a Head Statement
is signed and not that the signer was entitled to publish it. Both bear on a
party outside the entitled set; a Register Operator, which is the party with
standing to care whether its attestations sit on one chain, has the agreement
that anchors the key and the entitlement that completes the check.

### Replication {#ledger-replication}

The Ledger MAY be distributed across a plurality of per-jurisdiction
secondary stores under synchronous replication, each operated under the
data-residency constraints of its host jurisdiction. The append-only
derivation-chain invariant -- that every entry's Prior-Entry Hash equals the
Signing Input Digest, as {{settlement-ledger}} defines it, of the immediately
preceding entry's Entry Signature -- MUST be preserved across all secondary
stores. A secondary
store replicates the single sequence of {{settlement-ledger}} and originates no
entry of its own.

## Regulator Portal {#regulator-portal}

The Regulator Portal Subsystem authenticates a sovereign regulator's
jurisdictional credentials against a regulator-identity-provider trust
anchor that MUST be declared in every Bilateral Register Agreement addressed by
the reconciliation being read. It restricts returned fields to those within the
regulator's statutory scope as declared in the statutory-regulator-access scope
of those agreements. Each Bilateral Register Agreement declares, per regulator jurisdiction, a
permitted-read-field set: the names of the Reconciliation Output and Ledger entry
fields a regulator of that jurisdiction may be returned, and the predicates over
which it may be returned them. The scope restriction is the INTERSECTION of the
per-agreement permitted-read-field sets scoped to the regulator's jurisdiction,
taken only over reconciliations whose Canonical Claim Predicate is in the
intersection of the corresponding permitted-read-predicate sets, and further
intersected with the regulator's requested field set. Fields and predicates are
different domains and are intersected separately; intersecting one with the other
would yield the empty set, which earlier text did. Each
access MUST be recorded in an append-only audit trail. Each record MUST carry a
contiguous sequence number and the digest of the preceding record, computed as
{{settlement-ledger}} computes a Prior-Entry Hash, and the reconciliation server
MUST publish a signed head of that trail -- its current last sequence number and
digest, under its sealing key -- once per ledger-head notarisation interval, and
MUST notarise that head into the Transparency Service of {{settlement-ledger}}.

Earlier revisions called the trail subpoena-grade and specified none of that.
The trail is held by the party whose reads it records, and the accountability of
the Audit Identity entitlement rests on it -- an unaudited audit right is a
standing unaccountable read. Without a chain and an externally anchored head, a
record can be removed or rewritten by the party the trail exists to hold
accountable, and it is then evidence only against a party that has not tampered
with it. This document applies exactly this construction to the Settlement-Layer
Ledger a few sections above and applied none of it here, which is the whole of
the defect: not a technique the document lacks, a technique it did not carry to
the second place that needed it.

The Portal is a subsystem of the reconciliation server and reads the Ledger
without scope restriction. The scope governs what it RETURNS, not what it may
read. Stating it the other way round would make the Portal unable to compute the
authority under which it answers, since that computation requires reading the
entry first.

Where the entry read is a Continuation entry, the Portal computes the trust
anchor and the scope from the agreements addressed by the reconciliation entry
carrying the same Reconciliation Hash. A Continuation entry names no registers of
its own, and an intersection taken over an empty set of agreements would either
deny every regulator or restrict none, which are the two failures the rest of
this section exists to avoid.

The fields a Continuation entry carries are structural: an entry type, a sequence
number, a timestamp, chain hashes, and a pointer to an artefact. None is a
register record, a claim value or a verdict. A regulator in scope for a
reconciliation entry is therefore in scope for every field of every Continuation
entry carrying that entry's Reconciliation Hash, without any agreement having to
enumerate those fields. The alternative -- intersecting a set of field names no
agreement mentions -- yields the empty set, and would make a Sovereign
Re-Notification arrive at a regulator that is then returned nothing when it
follows the pointer. Agreements negotiated before this revision name none of
these fields, and {{retroactive}} forbids retroactive evaluation from requiring
any agreement to be renegotiated.

Both intersections are load-bearing. Taking the union across agreements would
let one register operator's permissive agreement widen what a regulator may read
about a reconciliation that also addressed a restrictive register, inverting the
data-residency property this protocol exists to preserve; and requiring the
trust anchor in only one agreement would let a single register operator
unilaterally introduce a regulator identity that authenticates against
multi-register events. Intersecting with the requester's own requested set is
not itself a restriction, since the requester chooses it.

### Sovereign Re-Notification {#re-notification}

A Sovereign Re-Notification is a COSE_Sign1 by the reconciliation-server sealing
key, under the media type registered in {{iana}}, whose payload is the CBOR array
of:

- the Claim Hash and the Reconciliation Hash of the superseded Output
- the Entry Sequence Number of the `continuation-supersession` entry recording
  the supersession
- the Material-Change Indicator
- the verdict values before and after
- the Attribution, one of `policy-state`, `source-data-version` or
  `attribution-indeterminate`, and where it is the last, the Post-Seal Evaluation
  Record Hash of the record {{post-seal}} requires
- a Notification Timestamp, in the form of {{reconciliation-output}}

encoded as a CBOR array in that order, an absent conditionally-absent element as
CBOR null so that the array's length is fixed, the first element a two-element
array of the two hashes and the fourth a two-element array of the verdict before
and after; and signed under the Sealing-Key Identifier its protected header
carries. The signature is not a payload element.

The server MUST deliver it to the notification endpoint each affected regulator's
Bilateral Register Agreements declare, MUST retry until acknowledged or until the
retention period of {{delivery}} elapses, and MUST make every Re-Notification
retrievable by a regulator under {{read-operations}}. A regulator that is
unreachable when a verdict changes is exactly the case the mechanism exists for,
so delivery cannot be a single attempt, and an obligation with no artefact and no
endpoint -- which is what earlier revisions specified -- is an obligation no
party can discharge or audit.

## Audit Path {#audit-path}

Several requirements in this document are justified by what an auditor can
reproduce: the re-typing decision of {{verdict-retyping}} "without the server's
assurance", the Query Binding of {{partial-attestation}}, the Policy-Version Hash
"under audit" of {{sealing}}, and the Deployment Blinding Value of
{{sealing}}. No earlier revision
defined that path, so every one of those justifications rested on a party the
document did not admit.

Each Bilateral Register Agreement MUST declare at least one Audit Identity: an
identifier and a key thumbprint, in the form {{audience}} uses for an Audience
Member. A party authenticating as an Audit Identity under {{read-signing}} is
entitled to:

- every operation of {{read-operations}}, unredacted, over any reconciliation
  addressing the register whose agreement declares that identity
- the Reconciliation Outputs of those reconciliations, irrespective of their
  Audience Sets, by `GET /arp/outputs/{reconciliation-hash}`
- for a named reconciliation, every element of the Policy-Version Hash preimage
  of {{sealing}} EXCEPT the Deployment Blinding Value, together with a
  Reconstruction Proof: a keyed digest, computed as HMAC-SHA-256 under the
  Deployment Blinding Value over the deterministically encoded CBOR array
  `["arp-reconstruction-v1", P]`, where `P` is the Policy-Version Hash preimage
  array of {{sealing}} with its Deployment Blinding Value position encoded as
  CBOR null so that the array's length is preserved. It is served as the
  two-element array of the disclosed elements and the proof, as the `result` of
  `GET /arp/outputs/{reconciliation-hash}` where the requester authenticated as
  an Audit Identity. An auditor given the Value recomputes it; one not given the
  Value can only compare it against another proof the same server produced.

  The preimage is pinned here because it was not pinned anywhere. The sweep
  recorded in the Document History put every digest preimage and signature
  payload in this document into a CBOR array with a normative field order and
  null-substitution for absent fields, and enumerated the artefacts it had
  reached; this construction was not among them. It had no array, no
  domain-separation string, no field order, no rule for the excised element and
  no encoding requirement, and it also had no wire representation, since
  {{read-operations}} defines that operation as returning the sealed Output and
  {{read-responses}} defines no slot for a value served beside one

An Audit Identity is NOT given the Deployment Blinding Value, and is not given
the preimage in full, because the preimage contains it. The Value is one
deployment-wide constant and its holder can invert every Claim Hash and
Policy-Version Hash on the published Ledger by the exhaustive search {{sealing}}
describes, including those of reconciliations the auditor's own register had no
part in; every agreement declares an Audit Identity, so disclosing the Value to
one would disclose the deployment to all of them.

An Audit Identity that does not hold the Deployment Blinding Value compares one
value the server produced against another value the server produced, under a key
only the server holds, over material that neither the Sealing Signature nor any
Ledger entry commits to. Equality establishes that the server was self-consistent
across the two reads and establishes nothing further. It does not establish that
the disclosed policy elements are the ones sealed into the Policy-Version Hash,
because a server that sealed under one policy state and later disclosed a
different one computes a consistent pair with no more effort than an honest one
does. And it does not establish that the resulting hash is correct. Only an
Audit Identity given the Value can establish either.

An earlier revision stated the first half as established and only the second as
open, which was one step too generous: it granted the mechanism the property
that a proof minted by the audited party, under the audited party's secret,
over material nothing else commits to, tells a third party something about the
world. A deployment that requires the stronger property MUST
appoint an Audit Identity jointly with every register whose agreement it holds,
and MAY disclose the Value to that joint identity alone. This document states the
limit rather than resolving it, because a construction that let one register's
appointee verify a deployment-wide digest without holding the deployment-wide
secret is a different mechanism than the one specified here.

An Audit Identity is declared in an agreement rather than named by a requester,
because the party being audited must not choose its auditor after the facts are
known, and because the register whose records are at issue is the party with
standing to insist on one. Its entitlement is scoped to reconciliations
addressing that register: an auditor appointed under one agreement reads nothing
about a reconciliation that agreement had no part in.

Every access under an Audit Identity MUST be recorded in the append-only audit
trail of {{regulator-portal}}. An unaudited audit right is a standing
unaccountable read of every Output a deployment holds.

## Retroactive Evaluation {#retroactive}

Upon publication of an updated Pattern Library, an updated Policy Version, or a
new Source-Data Version for any list a register consulted under
{{source-versioning}}, the Retroactive Evaluation Subsystem MUST execute a
deterministic re-application of the updated state to the retained metadata of
historical Reconciliation Outputs -- the Per-Register Result Set, the resolved
arithmetic and its parameters, and the Source-Data Version Identifiers, being the
inputs from which a Combined Verdict is recomputed. Under a Pattern-Library or
Policy-Version trigger the set to be examined is every retained Output whose
Policy-Version Hash preimage, as the Policy-Epoch Store of {{sealing}} holds it,
carries a value the transition changed. A Policy-Version Hash is not superseded
as a value: its seventh element is that reconciliation's Requester-Binding, so
it is per-reconciliation and there is no current hash against which to compare
one. What a transition supersedes is a preimage element, and the store holds
every preimage. Earlier revisions selected on "a superseded Policy-Version
Hash", which named no determinate set and left the operator to choose which
Outputs its own policy change had reached. Under a Source-Data Version trigger the policy
state is unchanged and that set would be empty; the set is instead those Outputs
whose Per-Register Result Set carries a Source-Data Version Identifier from the
list that was republished. Under a credential-revocation trigger it is those
whose Requester-Binding rested on the revoked credential. Under a
register-record-correction trigger, being a statement by a Register Operator
under item 32 of {{bra-items}} that a record it attested has been corrected, the
set is those Outputs carrying a Partial Attestation from that register over the
corrected record.

The fifth trigger is new in this revision and the gap it closes is the one a
subject would care about most. A `source-data-version` trigger reaches a
corpus-level republication whose state identifier the list publisher assigns and
which must be identical across every attestation over that list; it does not
reach a register correcting one record about one person. So a beneficial-ownership
register carrying an erroneous ownership percentage could produce a `match` on a
sanctions-linkage predicate, correct the record the following week, and no
trigger would fire, no sweep would run and no supersession would be appended. An
Audience Member reading Continuations before relying past the Reliance Horizon
would correctly find nothing, and the verdict built on the error would stand.
{{privacy-erasure}} states that a rectified verdict is expressed by supersession
rather than by deletion, and until this revision no trigger produced one. Where permissible under the applicable Bilateral
Register Agreements, partial attestations MAY be re-invoked.

The retroactive evaluation MUST be executable without re-negotiation of any
Bilateral Register Agreement. A material change in a historical Combined Verdict -- defined as any change of
verdict value into, out of, or between the decisive values, the decisive values
being `match` and `no-match` -- MUST trigger a Sovereign Re-Notification through the Regulator Portal, and MUST
additionally be recorded as a Continuation entry of type
`continuation-supersession` against the superseded Output, under the field rules
of {{settlement-ledger}}, so that a party which acted on the superseded Output
can discover that it was superseded. Notifying only the regulator would leave the party that acted
on a verdict the last to learn it had changed. A transition from `no-match` to `match` is material: it is
the case the protocol's motivating domain cares most about, and a definition
that excluded transitions within the decisive class would omit it. Revocation of a
Verified Principal Credential relied upon in a historical reconciliation is
itself a material change: the Retroactive Evaluation Subsystem MUST re-derive
the affected Requester-Binding class and, where a decisive reconciliation was
performed for what is now an unverifiable requester, emit a Sovereign
Re-Notification.

### Evaluation Sweep Statements {#sweep-statements}

Every trigger of retroactive evaluation is observed by the reconciliation server,
every decision to run is taken by it, and until this revision nothing recorded
that a sweep had run. "We evaluated and found no change" and "we never evaluated"
were the same observation from every position outside the server, which made the
central obligation of this section unfalsifiable.

The Retroactive Evaluation Subsystem MUST emit exactly one Evaluation Sweep
Statement for each trigger, within the ledger-head notarisation interval of
{{settlement-ledger}} measured from the trigger event. One Statement per trigger,
on a deadline tied to an event outside the server, is what makes a missing
Statement provable; "one per sweep" would let an operator batch a quarter's
triggers into a single Statement and remain conformant while evaluating nothing
in time. A Statement comprises:

- the trigger, drawn from the registry of {{iana}} and initially one of
  `pattern-library`, `policy-version`, `source-data-version`,
  `credential-revocation` or `register-record-correction`, and the identifier
  of the artefact that triggered it
- the Policy-Version Hash and Pattern-Library Version Identifier applied
- the Entry Sequence Number of the Ledger head when the sweep began and when it
  completed
- the Examined-Range Set: the set of Entry Sequence Number ranges the sweep
  covered, each a two-element array of a first and a last Entry Sequence Number
  inclusive, the ranges pairwise disjoint and in ascending order, and together
  covering every entry between the two head sequence numbers above whose Entry
  Type is `reconciliation`
- the count of Reconciliation Outputs examined, and the count found materially
  changed
- the Examined-Set Root: the root of a Merkle tree, constructed as
  {{merkle-construction}} defines it, over the Claim Hashes of the Reconciliation
  Outputs examined, sorted in bytewise lexicographic order, so that a party
  entitled to one of those reconciliations can be shown an inclusion proof that
  its own reconciliation was in the set. The Root commits to the distinct Claim
  Hashes examined and to nothing else. By {{merkle-construction}} the leaf count
  and the examined count are not derivable from one another, because two Outputs
  over one claim share a Claim Hash and the leaves are deduplicated; and no
  construction in this document commits the count found materially changed to
  anything beyond this Statement's own signature. Both counts are therefore
  assertions of the signing server, which the signature, the Timestamp and the
  notarisation make attributable and dated, and do not make verifiable. An
  earlier revision said the counts "are not bare assertions", which the
  deduplication rule two sections above already contradicted. The Examined-Range
  Set and the identity below are what make them checkable, by measuring them
  against the Ledger rather than against the Root
- an Evaluation Sweep Timestamp, in the form of {{reconciliation-output}}
- the Transparency Service Identifier and EntryID of the notarisation of the
  previous Evaluation Sweep Statement, encoded as CBOR null in the first
  Statement of a series
- a Sealing-Key Identifier
- a signature by the reconciliation-server sealing key, a COSE_Sign1 whose
  payload is the CBOR array of the fields above in the order listed, with the
  signature position encoded as CBOR null, an absent field likewise, encoded
  under Section 4.2.1 of {{RFC8949}}. The first, second, third, fourth and seventh
  items are each a two-element array, so that a field carrying two values
  occupies one position

Statements are retrievable under {{read-operations}} and MUST each be notarised
into the Transparency Service of {{settlement-ledger}} under their own media
type, within the same interval that bounds their emission. The previous-
notarisation pointer above makes the published series a chain, so that a
withdrawn Statement is detectable rather than merely absent;
{{I-D.ietf-scitt-scrapi}} retrieves by EntryID and offers no query surface, so a
party not told an EntryID could not find that notarisation by search. A Statement
is retained for the retention period of {{delivery}}.

On request under {{read-operations}}, a server MUST return an inclusion proof of a
given Claim Hash in the Examined-Set Root of a given Statement, to a party
entitled to a reconciliation carrying that Claim Hash.

**The sweep identity.** For every Evaluation Sweep Statement, a party able to
read the Ledger over the Statement's Examined-Range Set MUST be able to verify
all three of the following, and a Statement failing any of them is
non-conforming:

1. The Examined-Range Set is contiguous over the interval it claims: the ranges
   are disjoint, ascending, and their union contains every Entry Sequence Number
   between the two head sequence numbers whose entry is of Entry Type
   `reconciliation`. A gap is a claim to have examined an interval with a hole
   in it, and it is visible because the Ledger is contiguous by construction.
2. The count of Reconciliation Outputs examined equals the number of
   `reconciliation` entries in that union.
3. The count found materially changed equals the number of
   `continuation-supersession` entries appended in the interval between the two
   head sequence numbers whose superseded Reconciliation Hash is one of a
   `reconciliation` entry in that union.

The three together are an accounting identity rather than a signature, and that
is the point of them. A signature makes an assertion attributable; an identity
makes it checkable against something the asserting party does not solely
control. The Ledger is append-only, contiguous, head-notarised into a
Transparency Service outside the operator's control, and read under
{{read-operations}} by regulators, Audience Members, Register Operators and
Audit Identities. Requiring the counts to balance against it converts two
numbers the operator could previously choose into two numbers the operator must
now make true, and a sweep that examined less than it claims fails the identity
at whichever of the three it falsified.

The Examined-Set Root and the Examined-Range Set answer different questions and
both are needed. The Root proves **membership**: an Audience Member can be shown
that its own reconciliation was in the examined set. The Range Set proves
**coverage**: any Ledger reader can see that no interval was skipped. A Merkle
root over a set of Claim Hashes cannot prove coverage, because Claim Hashes are
sparse in the digest space and a set commitment has no notion of the elements
that are missing. Entry Sequence Numbers are dense and contiguous, so absence in
that space is visible in a way absence in the digest space is not. Committing to
the same sweep in both spaces is what lets one artefact answer both questions.

A Statement does not prove a sweep was performed honestly, and this document does
not claim it does. What it changes is that a sweep not performed is now a
statement the operator has to make, sign and date, rather than a silence. A
Source-Data Version publication is a public event with a public timestamp; an
operator with no Statement within the deadline has not evaluated in time, which
is checkable. The other three triggers are not public events, so the
Policy Parameters Document of {{read-signing}} carries the identifier and
effective time of every Pattern-Library and Policy-Version transition the server
applies, which makes those two triggers observable. A credential-revocation
trigger is observable to the credential's issuer and to the affected principal
and to nobody else, and this document does not make it more so.

The fifth trigger, `register-record-correction`, is a statement by a Register
Operator under item 32 of {{bra-items}}, so the event that starts its clock is
outside the reconciliation server in the same way a list publication is, and the
argument reaches it.

The falsifiability argument therefore holds for four triggers in five, and it
holds for the second and third of them **only through the anchoring
{{read-signing}} places on the Policy Parameters Document itself**, which is
stated here because an earlier revision of this section claimed three in four
while the Document carrying two of them was published by the reconciliation
server, under its own key, with no publication time and no notarisation. On
that footing the count was one in four and the sentence claiming otherwise was
the one place this document rounded up. A transition simply omitted from the
array started no clock, and no party could date the Document well enough to show
that it had been. The Publication Timestamp, the notarisation, and the
obligation to republish on the interval whether or not anything changed are
what make the second and third arguments true, and a deployment whose Policy
Parameters Document is not anchored as {{read-signing}} requires has two
falsifiable triggers and not four.

Both counts in this paragraph were stale within two hours of the fifth trigger
being added, in opposite directions: the enumeration above still named four
triggers while the registry of {{iana}} named five, and this sentence still said
three in four. Neither needed a reader to catch. A count in a specification is
an assertion about the specification, and the conformance class of
{{coverage-probes}} now carries a runner that checks every such count against
the text that makes it. An operator that signs a Statement it did not earn is making a
false attributable claim, which is a different thing from an invisible omission,
and the Examined-Set Root means an Audience Member can require it to prove that
its own reconciliation was in the set it claims to have examined.

Where a Sovereign Re-Notification cannot state whether a material change arose
from policy state or from Source-Data Version, the `attribution-indeterminate`
Post-Seal Evaluation Record it references MUST state which of the two candidate
causes were examined and why neither could be excluded. A bare qualifier is a
discretionary escape signed by the party that benefits from it.

### Revocation and the reliance window {#revocation-reliance}

Revocation of a Verified Principal Credential cannot be detected at the moment of
reliance by a party that is not checking, and this protocol does not put a
revocation check in the hot path of every relying party. What it does instead is
bound the window. An Audience Member MUST read the Continuation entries for a
Reconciliation Hash under {{ledger-read}} before relying on that Output past its
Reliance Horizon ({{reliance-horizon}}), and the supersession that records a
revocation is among the entries that read returns. Reliance inside the horizon on
a credential revoked during it is possible and is not prevented; reliance years
later on an Output whose principal was disowned the following week is prevented,
which is the case that matters and the case earlier revisions left open. The
horizon is declared per predicate, so a deployment needing a shorter window for a
sanctions predicate than for a corporate-registry one sets one.

### Coverage Probes {#coverage-probes}

Every mechanism in this section makes a sweep that was not performed into a
statement an operator has to sign and date. None of them establishes how much of
what should have been examined actually was. The sweep identity of
{{sweep-statements}} closes the gap between the counts and the Ledger; it does
not close the gap between the Ledger and the world, because an operator that
never wrote an entry has nothing to be caught balancing.

That is the omission problem, and it does not have a proof. It has an estimator.

**The construction.** A **Coverage Probe** is an ordinary reconciliation,
commissioned by an Audit Identity under {{audit-path}}, that is indistinguishable
at the reconciliation server from any other reconciliation over the same
predicate and register set. Before commissioning a set of probes, the Audit
Identity publishes a **Probe Commitment**: a COSE_Sign1 under its own key whose
payload is the Merkle Root, constructed as {{merkle-construction}} defines it,
over the Claim Hashes of the probes it intends to commission, together with
their count and a Commitment Timestamp. The commitment is published before the
first probe is commissioned and MUST be notarised into the Transparency Service
of {{settlement-ledger}}.

After a sweep that should have covered them, the Audit Identity requests an
inclusion proof for each probe's Claim Hash under the Examined-Set Root of the
Statement covering the interval its probe fell in, which {{sweep-statements}}
already obliges the server to return. The **recovery fraction** is the number of
probes for which a valid inclusion proof was returned, over the number
committed.

**What it estimates.** The recovery fraction is an unbiased estimator of the
proportion of eligible Outputs the sweep actually examined, provided the server
cannot distinguish a probe from an ordinary reconciliation. Applied to the
examined count the Statement asserts, it yields an estimate of the population
that should have been examined and was not: where a sweep asserts `E` examined
and recovers `m` of `k` probes, the eligible population is estimated at
`E · k / m`, and the shortfall at `E · (k - m) / m`.

This is not a proof about any individual Output and this document does not claim
it is. It is a bound on an aggregate, with a confidence interval that narrows as
`k` grows, and it is the only thing in this document that speaks to the size of
what was never written down. An operator suppressing a class of reconciliations
suppresses probes at the same rate, because it cannot tell them apart, and the
suppression appears in the recovery fraction rather than in any artefact the
operator controls.

**Indistinguishability is the whole of the mechanism, and it is what makes it
expensive.** A probe MUST address real registers over a real predicate and MUST
be charged against a real query budget, and its subject MUST be drawn from the
same distribution as ordinary subjects for that predicate. A server that can
identify probes by their subject, their register set, their timing, their
requester or their budget treatment can examine those and suppress the rest, and
the estimator then reports the operator's discrimination rather than its
coverage. A deployment MUST NOT exempt a probe from any charge, limit or path
that applies to an ordinary reconciliation, and MUST NOT mark one as a probe in
any artefact before the sweep it tests has been notarised.

**Why the commitment precedes the probes.** Without it, an auditor could
commission many probes, observe which were examined, and publish only those it
liked, in either direction: an auditor hostile to an operator publishes only the
misses, and an auditor captured by one publishes only the hits. The commitment
fixes the denominator before the numerator is knowable to anybody, which is what
makes the fraction evidence rather than a selection.

**What it costs and what it cannot do.** Probes consume register capacity, and a
register bears that cost without receiving the benefit, so the number of probes
is a term for a Bilateral Register Agreement rather than a constant this
document sets; item 33 of {{bra-items}} carries it. The technique establishes
nothing about a deployment whose registers are themselves suppressing, since a
probe's answer is only as good as the register's. And it cannot reach a
reconciliation that was never commissioned by anyone, which is the requester's
vantage and not the auditor's.

The estimator is standard practice in fields that must characterise a survey
they cannot repeat: sources of known brightness are injected into an
astronomical image and the fraction recovered gives the survey's completeness
function; marked individuals are released into a population and the fraction
recaptured bounds the population that was never seen. In both cases the quantity
of interest is what the instrument missed, which cannot be observed directly and
can be estimated from a known signal passed through the same instrument. A
retroactive evaluation sweep is an instrument of that kind.

## Cryptographic-Primitive-Upgrade Path {#crypto-upgrade}

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
hashes of canonicalised content rather than to cryptographic identities. The
Entry Signature and the Sealing-Key Identifier it carries are the exception, and
a verifier MUST resolve the Sealing-Key Identifier carried by each entry rather
than assume one key across the chain. An entry signed under a superseded
primitive remains verifiable under the key that identifier resolves. The chain
is unbroken across a rotation, but not because it is independent of the
primitive: the Prior-Entry Hash of {{settlement-ledger}} is the Signing Input
Digest of the preceding entry's Entry Signature, so it depends on the algorithm
identifier in that signature's protected header, which the `Sig_structure`
covers. It does not depend on the signature bytes, and that is deliberate.
Earlier revisions took the Prior-Entry Hash over the whole preceding entry
including its Entry Signature and argued the chain was unbroken because those
bytes "are fixed at the moment the entry is appended and are never rewritten".
Fixed for the operator, and not unique: {{signature-malleability}} measures a
primitive under which one signing act has many verifying encodings, so the bytes
a reader is handed are not the bytes the operator appended and a chain keyed on
them breaks for that reader alone. A verifier recomputing a Prior-Entry Hash
across a rotation boundary takes the protected header and the payload byte
strings from the preceding entry's COSE_Sign1 verbatim and constructs the
`Sig_structure` around them. It MUST NOT re-encode the protected header: those
bytes are the signer's and are what the signature covers, and a verifier that
re-encoded them would compute a different digest wherever its encoding differed
from the signer's, and could not encode a rotated primitive's header parameters
at all without implementing that primitive. The verifier therefore parses a
COSE_Sign1 but needs no knowledge of the primitive under which it was signed,
and in particular need not verify it. That is more than earlier revisions asked,
which was to copy the preceding entry's bytes and hash them; the additional
requirement is COSE parsing, and it is the price of a digest that does not move
when the signature encoding does.

## The Bilateral Register Agreement {#bra}

A register is addressable under this document only through a Bilateral Register
Agreement. Nothing in this document can be executed against a register that has
none: the projection has no permitted-predicate set to test against, the channel
has no construction, the encryption has no key, and the Per-Register Claim
Projection has no Bilateral-Register-Agreement Hash to carry. This section is
where the obligations that other sections place on an Agreement are gathered,
and it is the definition of the Agreement Hash.

### Declared items {#bra-items}

Each Bilateral Register Agreement MUST declare each of the following, save where
an item is marked OPTIONAL or the text of the item admits its absence;
{{bra-hash}} lists which those are. The numbering is normative: it is the order
in which the Agreement Hash of {{bra-hash}} is computed, and it is the only
order this document specifies.

1. The permitted-predicate set of {{projection}}.
2. The supported cryptographic primitives, including any post-quantum primitives
   selected under {{post-quantum}}. Every primitive appearing in an equivalence
   list of item 3 MUST appear here.
3. The Cryptographic-Primitive-Upgrade Path of {{crypto-upgrade}}.
4. The transport, endpoint, framing and encryption construction of the bilateral
   channel of {{projection}}.
5. The regulator-identity-provider trust anchor of {{regulator-portal}}.
6. The notification endpoint of {{re-notification}}.
7. The statutory-regulator-access scope of {{regulator-portal}}, together with
   the per-jurisdiction permitted-read-field and permitted-read-predicate sets
   it is computed from.
8. The Subject Reference form of {{projection}}.
9. The Freshness Window of {{projection}}.
10. The register's data-format profile under {{format-profiles}}, together with
    every value that profile obliges a declaring Agreement to supply or to name,
    in the order the profile enumerates them. A vocabulary release a profile
    requires the Agreement to name is such a value and is not a parameter in the
    sense of {{format-profiles}}, so naming only the parameters would leave it
    outside the Agreement Hash.
11. The register's public key material, as a COSE Key Set carrying at least one
    claim-encryption key and at least one partial-attestation-signature key,
    each with its `arp-key-status` and `arp-key-validity`.
12. The response window after which a register is recorded unresponsive.
13. The per-principal per-subject query budget of {{containment}} and the
    interval over which it is measured.
14. Any per-subject ceiling under {{containment}}.
15. The ledger-head notarisation interval of {{settlement-ledger}}.
16. The Transparency Service of {{settlement-ledger}}.
17. The artefact retention period of {{delivery}}.
18. The read rate limit of {{read-errors}}.
19. The notarisation polling bound of {{async-registration}}.
20. The authority origin of the reconciliation server the Agreement authorises.
21. At least one Audit Identity under {{audit-path}}.
22. The Register Operator's own read key.
23. Whether the Per-Register Claim Projection must carry the Requester-Binding
    Class.
24. The audit right over the query-budget counter of {{budget-suppression}}.
25. The reserved proportion of any per-subject ceiling and its per-principal
    sub-budget.
26. The response freshness tolerance of {{read-responses}}, which MUST NOT
    exceed the effective ledger-head notarisation interval of
    {{settlement-ledger}}, being the shortest item 15 any Bilateral Register
    Agreement the deployment holds declares. Bounding it against this
    Agreement's own item 15 would admit a tolerance longer than the interval the
    deployment notarises at, and so a response naming a head the reader could
    already know to be superseded.
27. The Witness Set of {{bra-witness}}, which MAY be empty.
28. The Witness Quorum of {{bra-witness}}.
29. OPTIONALLY, an audience constraint under {{audience}}.
30. The regulator read keys of {{read-signing}}, or the means by which they are
    resolved from the trust anchor of item 5, together with the means by which
    key material for items 21, 22, 27 and 30 is retrieved. A Witness Entry
    carries a key thumbprint, and a thumbprint is not key material, so without
    this a relying party holding a Head Consistency Statement has no defined way
    to obtain the key that verifies it.
31. Whether partial attestations may be re-invoked under {{retroactive}}.
32. Whether the Register Operator notifies corrections to records it has
    attested, and the endpoint at which it does so, which is what makes the
    `register-record-correction` trigger of {{retroactive}} reachable.
33. The Coverage Probe allowance of {{coverage-probes}}: the number of probes an
    Audit Identity may commission against that register per interval, and the
    interval, as a two-element array of unsigned integers.

Items 26, 27, 28, 30, 31, 32 and 33 are new in this revision; item 29 is carried from
-03 in a new position. Two of the five were already required elsewhere in this
document while sitting outside the Agreement Hash.
{{read-responses}} obliges a deployment to declare a response freshness
tolerance in its Bilateral Register Agreements; that is item 26.
{{read-signing}} obliges an Agreement to declare the keys under which a
regulator reads, and item 5's regulator-identity-provider trust anchor is not a
key; that is item 30. In both cases two deployments could agree on every item
the Agreement Hash committed to, differ on the term, and compute the same
Agreement Hash -- an Agreement Hash that does not cover a term the Agreement is
required to carry. {{retroactive}} makes re-invocation of partial attestations
conditional on what the applicable Agreements permit without making that
permission a declared item; that is item 31. Items 27 and 28 specify the witness
quorum {{read-responses}} names and earlier revisions declined to fix.

**An Agreement computed under an earlier revision does not compute the same
Agreement Hash under this one.** The Agreement Hash covers five items it did not
cover before -- 26, 27, 28, 30 and 31 -- and {{bra-hash}} now fixes the CBOR type of every item and the
ordering within every set-valued one, so the value changes for every Agreement
even where no negotiated term has changed. Agreements MUST be recomputed, and a deployment
holding a Bilateral-Register-Agreement Hash recorded before this revision MUST
treat it as naming an Agreement under the earlier item list rather than
as a value comparable with one computed under this section. Comparing the two
is the Bilateral-Register-Agreement drift of {{agreement-drift}}, and a
deployment that does not recompute will observe drift where none exists.

### Witness Set and Witness Quorum {#bra-witness}

{{read-responses}} establishes that an empty result is falsifiable to the extent
that its reader holds head-consistency evidence for the served chain from an
observer independent of the responding service, and that head evidence obtained
only from that service bounds nothing. It states the preference -- a witness
countersignature over the head, or, failing that, an independently anchored head
digest -- without saying how many countersignatures, from whom, or what makes
two of them two rather than one. This section says.

#### Witness Entries {#witness-entries}

A **Witness Set** is a set of zero or more Witness Entries. Each Witness Entry
is a CBOR array of exactly three elements, in this order and not nested:

1. the Audience Member Identifier, as {{audience}} defines it;
2. the Verification Method Reference, as {{audience}} defines it; and
3. an **Operating-Party Identifier**: an Authority Origin naming the party that controls the
   witness.

{{audience}} encodes those first two as a two-element array. Here they are the
first and second elements of a three-element array and are not wrapped in one,
because a Witness Entry is carried both in the Agreement Hash of {{bra-hash}}
and in the Policy Parameters Document of {{read-signing}}, and two readings of
one shape would let those two artefacts disagree about a set they are both
supposed to describe.

Two Operating-Party Identifiers are **distinct** where they differ after
normalisation under Sections 6.2.2 and 6.2.3 of {{RFC3986}}. Comparison is over
the normalised form and is otherwise bytewise. Without a stated normalisation
`https://acme.example` and `https://ACME.example/` are distinct to one
implementation and identical to another, and whether a quorum is met turns on
which.

A Witness Entry's Operating-Party Identifier MUST NOT be that of the
reconciliation server, of the Transparency Service of {{settlement-ledger}}, of
any party controlling either, of any party controlled by either, or of any party
under common control with either, and no two Witness Entries counted toward one
quorum may be under common control with each other. The first exclusion runs in
every direction because
running it upward alone excludes nothing that matters: a reconciliation server
that incorporates three subsidiaries, declares three distinct Operating-Party
Identifiers and satisfies a quorum of three controls every observation the
quorum is composed of, and the fork {{read-responses}} is concerned with stays
invisible while the quorum reports it as checked. The second exclusion is there
because the rationale of this section is observer diversity and not identifier
diversity: three witnesses that are three subsidiaries of one unrelated parent
declare three distinct Operating-Party Identifiers, pass the distinctness test
as a verifier computes it, and are one observation reported three times. The
Register Operator of the addressed register, and any operator of a secondary
store under {{ledger-replication}}, are excluded on the same ground.

#### Head Consistency Statements {#head-consistency}

A **Head Consistency Statement** is a COSE_Sign1 by a witness, under the media
type registered in {{iana-media}}, carrying the `arp-witness-identifier` header
parameter registered in {{iana}} in its protected header, whose payload is
the deterministically encoded CBOR array, under {{cbor-cose}}, of:

1. the text string `arp-head-consistency-v1`;
2. the Entry Sequence Number of the head covered;
3. the Self-Entry Hash of that entry;
4. the Statement Timestamp of the Ledger Head Statement the witness observed, in
   the form of {{reconciliation-output}}; and
5. the **Witness Observation Time**, being the time the witness produced this
   Statement, in the same form.

Item 5 exists because a COSE_Sign1 is not dateable from its own bytes, so a
freshness rule over a Statement carrying no time is a rule no verifier can
apply. {{settlement-ledger}} adds a Statement Timestamp to the Ledger Head
Statement for the same reason.

#### The quorum rule {#quorum-rule}

The **Witness Quorum** is an integer `t` with `0 <= t <= n`, where `n` is the
cardinality of the Witness Set. A Witness Set MUST contain at least `t` entries
with pairwise distinct Operating-Party Identifiers; an Agreement whose Witness
Set does not is non-conforming, and a deployment MUST NOT address a register
under it. Without that constraint an Agreement declaring three entries under one
operating party and `t` of three is well formed, satisfiable by nobody, and
every empty result served under it is permanently unfalsifiable with no
conformance test firing.

A relying party holds sufficient head-consistency evidence for an empty result
under {{read-responses}} when it holds Head Consistency Statements from at least
`t` Witness Entries where:

- each verifies under the key material declared for that entry;
- the `t` entries have **pairwise distinct Operating-Party Identifiers**;
- the `t` entries have **pairwise distinct Verification Method References**, and
  a relying party MUST reject a set in which two entries resolve to the same
  key. Distinctness of the Operating-Party Identifier alone does not establish
  that two entries are two observations: two entries declaring one key under two
  Operating-Party Identifiers are satisfied by a single COSE_Sign1, and a
  relying party applying only the previous condition counts one signature twice
  and reports a quorum of two met by one signer. That failure is mechanical and
  locally checkable, which distinguishes it from the declared-independence limit
  {{bra-limits}} concedes and cannot close: a verifier cannot test whether two
  named parties are truly independent, and it can always test whether two
  entries name one key;
- each covers the head the response names, that is, item 2 of the Statement
  equals the response's `as-of-sequence-number` and item 3 equals the Self-Entry
  Hash that response names; or covers a head at a higher Entry Sequence Number
  **and** the relying party additionally holds the linkage triples between the
  two, read under {{read-operations}}, and has verified all three of: that the
  Self-Entry Hash of the triple at the Statement's Entry Sequence Number equals
  item 3 of that Statement; that the Self-Entry Hash of the triple at the named
  head equals the one the response names; and that the triple at each sequence
  number carries, as its Prior-Entry Hash, the Signing Input Digest that the
  linkage array of the entry below it reports. The linkage projection carries
  that digest as its fourth element precisely so this condition is computable by
  the party required to compute it: a Signing Input Digest is taken over the
  `Sig_structure`, so neither the protected header nor the payload of the entry
  below is recoverable from a triple of sequence number and two hashes, and the
  substitution a reader might reach for instead is the one the next sentence
  forbids. Those two values are digests over different
  preimages -- {{settlement-ledger}} takes a Self-Entry Hash over the entry
  array with two positions nulled and a Prior-Entry Hash over a `Sig_structure`
  -- so a verifier MUST NOT test them for equality against each other; and
- each carries a Witness Observation Time no earlier than the Statement
  Timestamp of item 4 and no later than twice the effective ledger-head
  notarisation interval after it, that interval being the shortest any Bilateral
  Register Agreement the deployment holds declares, per the direction rule of
  {{delivery}}.

A witness MUST publish its Head Consistency Statements at
`/.well-known/arp-head-consistency` on the Authority Origin of its
Operating-Party Identifier, most recent first, under the media type registered
in {{iana}}, and MUST serve them to any party without authentication. The
Operating-Party Identifier is for this reason an Authority Origin and not a bare
name: an identifier that names a party without locating it cannot be the route
by which the artefact is obtained.

**A relying party MUST obtain Head Consistency Statements from the witnesses'
own origins, and MUST NOT accept for quorum purposes a Statement obtained from
the responding service.** Until this revision the document specified the
artefact, the quorum arithmetic and the freshness window, and specified no
channel at all, which left the obvious implementation: the responding service
hands over the witness statements alongside its response. That implementation
satisfies every condition above. The witness signature stops the service
forging a Statement and does nothing to stop it choosing which ones to pass on,
and under exactly the fork this mechanism exists to detect, an operator serving
two branches hands each reader the statements of the witnesses it fed that
branch. Every check passes on both branches and the quorum is met on both.

This is the whole of the artefact's value and it was the one thing not stated.
A Head Consistency Statement obtained from the party it is evidence about is
not independent evidence; it is the responding service's own selection,
countersigned. Where a witness origin is unreachable, the relying party holds
fewer than `t` Statements and MUST act under {{read-responses}} accordingly,
rather than accepting a substitute from the service.

The chain requirement in the third condition is what makes the artefact worth
its name, and it is why the condition pins **both ends** of the chain and not
only its internal consistency. A witness signature over a head at a higher
sequence number is, on its own, evidence about whatever branch that witness was
served, which may not be the reader's: a fork at disjoint sequence numbers is
precisely a pair of heads neither of which contradicts the other. A chain that
is merely internally consistent proves only that the entries the responding
service just served are consistent with each other, which that service controls
entirely. Anchoring the top of the chain to the digest the witness signed, and
the bottom to the digest the response named, is what puts the two observations
on one chain. A Statement covering the named head exactly needs no linkage
because there is nothing to link.

The window in the fourth condition is measured from the Statement Timestamp of
the Ledger Head Statement and not from the Entry Timestamp of the head, and it
is two intervals and not one, because {{settlement-ledger}} republishes the
Ledger Head Statement once per notarisation interval and not on every append. An
entry appended just after a publication is not published until one interval
later; a window of one interval measured from that entry's own timestamp is
already closed when the witness first sees the head, and no conforming Statement
could exist for it.

The distinctness requirement is the substance of the rule. Countersignatures
from witnesses under one operating party are one observation reported `t` times,
and a quorum satisfied by them is a quorum in arithmetic only: the equivocation
{{read-responses}} is concerned with becomes observable when two independent
observers compare heads, and two instances of one observer are not two
observers.

#### Discovery {#witness-discovery}

A relying party is not a party to any Bilateral Register Agreement and holds
only the hashes of those Agreements, so a quorum declared only inside an
Agreement is a test the party required to run it cannot read. The Policy
Parameters Document of {{read-signing}} therefore carries the effective Witness
Set and the effective Witness Quorum, and a relying party evaluates the quorum
against that document.

Where a deployment holds more than one Bilateral Register Agreement, the
effective Witness Set is the intersection of the Witness Sets every such
Agreement declares and the effective Witness Quorum is the largest any of them
declares, per the direction rule of {{delivery}}. Two Witness Entries are
**equal for the purpose of that intersection when their Operating-Party
Identifiers are equal and their Verification Method References are equal**, and
the intersection carries, for each such pair, the entry as the Agreement with
the lexicographically least Agreement Hash declares it.

Stating the relation is not pedantry. Taken over whole entries, the intersection
empties on any difference in the first element -- an Audience Member Identifier
written two ways for one witness -- and this section then obliges a conforming
deployment to stop serving reads entirely. Taken over the Operating-Party
Identifier alone, two entries declaring different keys for one party merge, and
a relying party accepts a Head Consistency Statement under key material only one
of the two Agreements declared. Both readings are available from the bare word
"intersection", one produces an outage and the other produces an unauthorised
key, and a deployment cannot be conforming under both.

The effective Witness Set MUST contain at least the effective Witness Quorum
entries with pairwise distinct Operating-Party Identifiers. Where it does not,
the deployment is non-conforming and MUST NOT serve reads under
{{read-responses}}. The per-Agreement constraint of {{quorum-rule}} does not
reach this: two Agreements each declaring two entries and a quorum of two, with
no entry in common, are each conforming and together produce an empty effective
set under a quorum of two, which is the unsatisfiable quorum that constraint
exists to forbid.

#### Where the quorum is zero {#quorum-zero}

A Witness Quorum of `0`, which a Witness Set of zero entries requires, declares
that no witness evidence is available. A relying party acting on an empty result
served under an effective quorum of `0` SHOULD instead hold an independently
anchored head digest as {{read-responses}} provides, and MUST NOT treat the
absence of a witness requirement as evidence that the head is uncontradicted. A
deployment declaring `0` is making a statement about what its empty results can
be checked against, in a term a relying party can read, rather than leaving a
reader to infer it.

### The Agreement Hash {#bra-hash}

Each Bilateral Register Agreement carries an Agreement Hash: the SHA-256 digest
over the deterministically encoded CBOR array, under {{cbor-cose}}, of the items
of {{bra-items}} in the order given there. The array has **exactly thirty-three
elements**. The reconciliation server and the Register Operator compute it
independently and MUST obtain the same value.

Determinism under Section 4.2.1 of {{RFC8949}} fixes how a given value is
encoded. It does not fix which CBOR type an item takes, nor the order of
elements within an item that is a set, and two parties that differ on either
compute different digests from identical negotiated terms. Since
{{agreement-drift}} suspends reconciliation on a deviation, that is an outage
and not a warning. The types are therefore fixed here.

| Item | CBOR encoding |
|---|---|
| 1, 2, 21, 27, 30 | array, sorted in bytewise lexicographic order of the deterministic CBOR encoding of each element |
| 3 | three-element array, in the class order of {{crypto-upgrade}}, each element that class's equivalence list **in the declared preference order and not sorted** |
| 4 | four-element array: transport identifier, endpoint URI and framing identifier, each a text string, and the sorted array of COSE algorithm identifiers of the encryption construction |
| 5, 8, 16, 20 | text string |
| 6 | URI, as a text string |
| 7 | three-element array: the statutory-regulator-access scope as a text string, and the per-jurisdiction permitted-read-field and permitted-read-predicate sets, each a sorted array of two-element arrays of the jurisdiction identifier and the sorted set for it |
| 9, 12, 15, 17, 19, 26 | unsigned integer, seconds |
| 10 | two-element array: the profile identifier as a text string, and the array of profile-obliged values **in the order that profile enumerates them** |
| 11, 22 | COSE Key Set, its keys sorted in bytewise lexicographic order of the deterministic CBOR encoding of each key |
| 13 | two-element array: the budget as an unsigned integer count, and the interval in seconds as an unsigned integer |
| 14, 28 | unsigned integer |
| 18 | two-element array: the permitted request count as an unsigned integer, and the interval in seconds as an unsigned integer |
| 23, 24, 31 | boolean |
| 32 | two-element array: a boolean, and the endpoint URI as a text string or null |
| 33 | two-element array of unsigned integers: the probe allowance and the interval in seconds |
| 25 | two-element array: the reserved proportion as a CBOR decimal fraction, and the per-principal sub-budget as an unsigned integer |
| 29 | two-element array: the maximum cardinality as an unsigned integer or null, and the permitted member class as a text string or null |

Every item that is a set is encoded as a CBOR array sorted in bytewise
lexicographic order of the deterministic CBOR encoding of each element. This
document already requires that ordering of the Audience Set, of the algorithm
array of {{read-signing}} and of the origin array of {{sealing-key-discovery}},
and for the same reason: an unordered set gives one Agreement as many hashes as
it has permutations. Items 3 and 10 are the exceptions and are called out in the
table as such, because each is a **sequence** rather than a set: {{crypto-upgrade}}
declares an ordered equivalence list whose order is the preference, and item 10
takes its order from the profile that enumerates the values. Sorting either
would discard the meaning it carries, and a change of order in either would then
leave the Agreement Hash unmoved.

An item that is absent, inapplicable or empty is encoded as CBOR null, and the
element is present in the array regardless. **Items 14, 25, 27 and 29 are the
only items that may be absent**: 14 and 25 where the Agreement sets no
per-subject ceiling, 27 where the Witness Set is empty, and 29 because it is
OPTIONAL. Item 25 is null whenever item 14 is. An empty Witness Set is encoded
as CBOR null and not as an empty array. Every other item MUST be present and
MUST NOT be null. Encoding an absent per-subject ceiling as null, as zero, or by
omitting the element are three readings of one sentence, and all three produce
different Agreement Hashes.

The order is fixed by the numbering of {{bra-items}} and by nothing else. An
implementation MUST NOT derive it from the order in which terms appear in the
negotiated instrument, from any serialisation the parties exchange, or from an
alphabetisation of the item names. Earlier revisions of this document specified
the digest over "its canonicalised content", which named no order and so did not
make independent computation of one value possible.

A change to any item changes the Agreement Hash, and {{agreement-drift}}
suspends reconciliation against a register whose Agreement Hash deviates from
the one committed at the start of a reconciliation event. Items 11, 22, 27 and
30 carry key material and witness membership, which change under ordinary
operation -- a rotation under the upgrade path of item 3, the addition of a
witness -- so an Agreement Hash change is a renegotiation event and the parties
MUST agree the new Agreement Hash before the operation that causes it. A
deployment that rotates first and renegotiates afterwards has suspended its own
reconciliation, by its own drift rule, at the moment its upgrade path was
exercised.

### What a Bilateral Register Agreement does not establish {#bra-limits}

An Agreement is a declaration by two parties. It is not evidence that what it
declares is true.

The Operating-Party Identifiers of {{witness-entries}} are declared, not proven.
{{witness-entries}} excludes a witness under the control of the responding
service, under common control with it, or controlling it, and that exclusion is
normative; what this document supplies no mechanism for is **detecting a false
declaration**. Two witnesses under common control that each declare a distinct
Operating-Party Identifier satisfy the distinctness test as a verifier can
compute it, and a relying party comparing the two identifiers sees two parties.
The requirement is worth stating regardless, because a party that declares an
independence it does not have has made a false attributable claim rather than
benefited from an unexamined silence, and because an Audit Identity under
{{audit-path}} can be given the Witness Set to examine. But a relying party
MUST NOT treat a met quorum as proof of observer diversity. It is proof that
observer diversity was declared, by a named party, in a term that party can be
held to.

The same holds of item 20, the Authority Origin, which {{containment}} already
requires a register operator to corroborate by publishing an Authorised-Origin
Document, and which is the one declared item this document does provide a
mechanism to check.

# Agentic Principal Reconciliation {#agentic}

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
sealed against a Policy-Version Hash, written to the Settlement-Layer Ledger
without claim or register content, and re-evaluable if the underlying credential
is later revoked.

# Encoding {#encoding}

## CBOR-COSE Encoding {#cbor-cose}

The mandatory-to-implement encoding for ARP messages on the wire is CBOR with
COSE {{RFC9052}} {{RFC9053}} envelopes. COSE_Sign1 is used for both Partial
Attestations and the Sealing Signature. Every COSE_Sign1 this document defines MUST carry the algorithm identifier
(label 1) and the key identifier (label 4) in its protected header, and MUST NOT
carry either in an unprotected header. A Signing Input Digest under
{{terminology}} depends on the protected header and on nothing else in the
envelope, so an algorithm or key identifier placed outside it is a value that
digest does not bind -- and {{crypto-upgrade}} relies on the algorithm
identifier being bound.

The protected header of a Partial Attestation and of a sealed Reconciliation
Output MUST additionally include the Bilateral-Register-Agreement Hash and
Policy-Version Hash as COSE header parameters; the other COSE_Sign1 structures this document defines
carry the headers their own sections state registered per {{iana}}.
`arp-bilateral-agreement-hash` always carries an array, sorted in lexicographic
byte order: a Partial Attestation's array has exactly one member, and a Sealing
Signature's has one per addressed register. A single encoding for both avoids a
decoder having to infer the type from context. Pending registration,
implementations MAY use labels from the private-use range of the COSE Header
Parameters registry; such use is not interoperable.

## Reconciliation Request Binding {#request-binding}

A reconciliation is commissioned by `POST /arp/reconciliations` on the
reconciliation server's authority origin, with a request body carrying the
Canonical Claim, the Audience Set the requester asks for, and, where the
requester is an agent, its asserted principal. The body is CBOR under the media
type registered in {{iana}} for a reconciliation request, save for the Canonical
Claim, which is carried as a CBOR byte string holding the {{RFC8785}}
serialisation of the claim exactly as the Claim Hash is taken over it. Carrying
the claim as native CBOR would need the CBOR-to-JSON mapping
{{reconciliation-output}} declines to define, and two servers receiving identical
bytes would compute different Claim Hashes. The request MUST be signed under the
profile of {{read-signing}}, with `tag` set to `arp-reconcile`.

An Audience Member other than the Requesting Principal MUST have been enrolled at
the reconciliation server before it may be named: an enrolment binds an
accountable-principal identifier to a Verification Method Reference, is performed
by the party being enrolled, and is out of scope for this document. A server MUST
refuse to name an unenrolled member. Without enrolment a requester could name any
identifier it liked, and the named party -- a competitor, a journalist, a foreign
ministry -- would be handed a sealed, register-attested record that a named
subject had been investigated under a named predicate, without its consent and
without any register's. Naming is an assertion by the requester; enrolment is
what makes it an assertion about a party that has agreed to receive.

A refusal on that ground discloses that a named identifier is not enrolled,
which a requester able to repeat it turns into an enumeration of the enrolment
roster. A server MUST charge such a refusal against the requester's rate limit
under {{read-errors}} and MUST record it in the access log that section requires.
{{read-errors}} refuses to distinguish absence from inentitlement on the read
path, on the ground that answering differently would turn every endpoint into an
existence oracle; this endpoint is outside that section, so the principle is
carried here by rate and by record rather than by collapsing the two answers,
because a requester naming an audience member it believes enrolled needs to be
told when it is wrong. The residual is recorded in {{privacy}}.

The response is one of four things, the fourth being the `401` of
{{read-signing}} where the request's own signature was not accepted. A `200` whose body is the
signed read response of {{read-responses}}, whose `result` element is the sealed
Reconciliation Output and whose As-Of pair gives the Ledger head at the moment of
delivery. That is the delivery {{delivery}} requires, and it is what carries the
Reconciliation Hash: the requester computes it over the Output it has just been
handed, and the signed response fixes the head against which every later read of
that Output is compared. A `422` carrying a Remediation Advisory, where the Adversarial
Pre-Transmission Test did not emit a Pass and no override was authorised, or
where a named regime is not one the policy-epoch store admits for the predicate,
or where a named Audience Member is not enrolled. Or a `403` carrying a
Remediation Advisory whose sole content is the Agent-IFF ground, where the
Agent-IFF policy of the Requester Identity Binding and Agent Friend-or-Foe Gate
section refuses the requester outright for the predicate class. Both refusals are
signed as {{read-responses}} requires of a `4xx`, so a refused requester holds
evidence of what it asked and what it was told.

A refusal under {{containment}} or an audience constraint under {{audience}} is
not a fourth case: those refuse a register, and the reconciliation is sealed and
delivered with the reason recorded against that register.

## HTTP Message Signature Binding {#http-sig}

Where a reconciliation is requested over HTTP by an autonomous agent, the
request MUST be signed under HTTP Message Signatures {{RFC9421}}, with the
signature-agent key resolvable through a Web Bot Auth signature-agent card
{{I-D.meunier-webbotauth-registry}}, advertised via the Signature-Agent header
{{I-D.meunier-webbotauth-httpsig-protocol}} and resolved through the HTTP
Message Signatures directory it names
{{I-D.meunier-webbotauth-httpsig-directory}}. The reconciliation server
derives the Agent Friend-or-Foe Determination from
verification of that signature and,
where required by the Agent-IFF policy, a Verified Principal Credential
carried in the request body.

## Output and Ledger Read Binding {#ledger-read}

This section is the wire binding for every read this document requires of a party
outside the reconciliation server. Earlier revisions stated what a read returns
and never how one is requested, which left every discovery path ending at a value
its holder could not present to anything.

Requests are HTTP over TLS to the reconciliation server's authority origin, the
same origin whose Sealing-Key Identifier resolves under {{sealing-key-discovery}}.
Every hash appearing in a path segment is base64url-encoded without padding;
every Authority Origin appearing in one is percent-encoded as Section 2.1 of
{{RFC3986}} provides; and every timestamp in a path or query parameter is in the
form {{reconciliation-output}} pins. The `@target-uri` is inside the request-binding
digest of {{read-responses}}, so an encoding two implementations could choose
differently would make their bindings differ over the same read.
A non-Requesting Audience Member is not told that origin by this protocol; it
learns it from the party that named it, and this document defines no directory by
which a principal discovers the servers at which Outputs naming it may exist.

### Request signing profile {#read-signing}

{{RFC9421}} requires an application that uses it to state a profile. This is that
profile. It governs every request to an operation of {{read-operations}} and the
commissioning request of {{request-binding}}.

- Every request MUST carry exactly one signature, labelled `arp`.
- The covered components MUST be `@method`, `@target-uri`, and, where the request
  carries a body, `content-digest` as {{RFC9530}} defines it, together with the
  signature parameters `created`, `expires`, `nonce`, `keyid`, `alg` and `tag`. A
  request covering fewer MUST be refused. `tag` is `arp-read` for an operation of
  {{read-operations}} and `arp-reconcile` for the commissioning request of
  {{request-binding}}; those are the only two values, and a server MUST reject a
  request whose `tag` does not match the endpoint it was sent to.
- Covering `content-digest` is what binds the body. The commissioning request
  carries the Canonical Claim, the requested Audience Set and any asserted
  principal in its body; a signature that covered only the target would leave an
  intermediary free to substitute the subject or add Audience Members and have
  the result sealed, ledgered and notarised as the signed requester's.
- The `nonce` MUST be at least 128 bits drawn from a cryptographically secure
  random source, base64url-encoded.
- `expires` MUST be no more than 300 seconds after `created`. A server MUST
  reject a request whose `created` is more than 300 seconds in the past or more
  than 60 seconds in the future, and MUST reject a repeated `nonce` from the same
  `keyid` within that window. Without this a captured read request replays
  indefinitely, which {{replay-defence}} closes only for requests that initiate a
  reconciliation.
- The permitted signature algorithms are those the deployment declares for the
  partial-attestation-signature class in its Cryptographic-Primitive-Upgrade
  Path, so that read authentication rotates with everything else.
- `keyid` MUST be the JWK thumbprint of the requester's public key, computed as
  in {{RFC7638}}. For an Audience Member it MUST equal the Verification Method
  Reference the Output names. For a regulator, a Register Operator or an Audit
  Identity it MUST be a key the corresponding Bilateral Register Agreement
  declares. For a requester commissioning a reconciliation it is the key that
  becomes that requester's Verification Method Reference in the resulting
  Audience Set. Key material is retrieved as that agreement provides, or, for an
  agent, through the Web Bot Auth directory of {{http-sig}}.
- The reconciliation server MUST publish a Policy Parameters Document at
  `/.well-known/arp-policy-parameters` on its Authority Origin: a COSE_Sign1 by
  its sealing key, under the media type registered in {{iana}}, whose payload is
  the six-element CBOR array of: a Publication Timestamp, in the form
  {{reconciliation-output}} fixes; the array of permitted signature algorithm
  identifiers, sorted in bytewise lexicographic order of the deterministic CBOR
  encoding of each element; the array of per-predicate entries, each a four-element array of
  the predicate, the admitted regime set sorted in bytewise lexicographic order,
  the two-element array of the resolved Verdict Arithmetic and its parameters,
  and the reliance interval, the entries themselves sorted by predicate; and the
  array of two-element arrays of the identifier and effective time of every
  Pattern-Library and Policy-Version transition the server has applied, sorted by
  effective time, which {{sweep-statements}} relies on; and the two-element array
  of the effective Witness Set and the effective Witness Quorum of
  {{witness-discovery}}, the Witness Set sorted in bytewise lexicographic order
  of the deterministic CBOR encoding of each entry; and the two-element array of
  the response freshness tolerance of {{read-responses}} in seconds and the
  effective ledger-head notarisation interval that bounds it, each an unsigned
  integer.

  The sixth element is present for the same reason as the fifth.
  {{read-responses}} obliges **every** reader of a read response to check that
  the response time falls within a declared tolerance, and declares that
  tolerance in the Bilateral Register Agreements. A relying party is party to no
  Agreement and holds only their hashes, so the tolerance every reader must
  apply was readable only by the parties who did not have to apply it, which is
  precisely the defect the Witness Set element was added to fix.

  Without that fifth element a
  relying party, which holds only Agreement Hashes, could not evaluate the quorum
  the same section obliges it to evaluate.

  The Publication Timestamp is first because the rest of the array is evidence
  about the reconciliation server, published by the reconciliation server, under
  its own key, and a COSE_Sign1 is not dateable from its own bytes. Two
  Documents published a year apart, one of which has had a transition or a
  Witness Entry quietly dropped from it, are otherwise indistinguishable to
  every party the Document exists to inform. This document already reached that
  conclusion twice, for the Ledger Head Statement of {{settlement-ledger}} and
  for the Head Consistency Statement of {{head-consistency}}, and the same
  reasoning was not carried here.

  The reconciliation server MUST notarise each published Policy Parameters
  Document into the Transparency Service of {{settlement-ledger}}, under its own
  media type, within the ledger-head notarisation interval of that section
  measured from its Publication Timestamp, and MUST republish it on that
  interval whether or not its contents changed. A Document that changed without
  a new Publication Timestamp, or a published Document with no notarisation
  inside the interval, is non-conforming.

  The obligation to republish unchanged is what makes silence readable: without
  it, an operator that has removed a Witness Entry and an operator that has
  changed nothing publish the same thing, and the notarised series has no entry
  to be missing. A relying party MUST NOT treat a Policy Parameters Document as
  current where its Publication Timestamp is older than twice that interval, and
  MUST refuse to evaluate a quorum against one it cannot date. A requester is
  party to no Bilateral Register Agreement and could not otherwise determine how
  to sign, and publishing the resolved parameters removes the regime-shopping
  probe of {{verdict-arithmetic}} by making its result available without
  probing.
- A request that is unsigned, that fails signature verification, that is outside
  the freshness window, or that replays a nonce MUST be refused with `401`. A
  `401` is the one response of this section that is not signed under
  {{read-responses}}: its payload would have to bind a request carrying no nonce
  and no key identifier, and there is no requester key to bind it to. A `401`
  therefore carries no body, and a requester receiving one has learned only that
  its own signature was not accepted.

### Read operations {#read-operations}

Nine operations are defined, and no read of an Output or of the Settlement-Layer
Ledger by a party outside the reconciliation server is defined anywhere else in
this document. An Audit Identity under {{audit-path}} is entitled to every one of
them, unredacted, over reconciliations addressing the register whose agreement
declares it; the Entitlement clauses below state the other parties and do not
repeat that. The Ledger Head Statement of {{settlement-ledger}} is not a read of
the Ledger: it is a published statement about the Ledger, served without
authentication at a well-known URI, and is deliberately outside this section so
that a party holding no entitlement at all can still observe a head.

- `GET /arp/outputs/{reconciliation-hash}` returns the sealed Reconciliation
  Output. Entitlement: an Audience Member of that Output; an Audit Identity under
  {{audit-path}} for a reconciliation addressing its register; and a regulator in
  scope for that reconciliation under {{regulator-portal}}, whose response is
  field-restricted by that section.
- `GET /arp/reconciliations/{reconciliation-identifier}/registers/{register-identifier}`
  returns the Per-Register Result Set entry concerning that register alone,
  keyed on the Reconciliation Identifier the register received in its
  Per-Register Claim Projection, since a register never holds a Reconciliation
  Hash. Entitlement: the Register Operator of that register. It is what lets a register
  see what was recorded of its own answer. Without it a server could discard a
  register's signed `match` and record `register-unresponsive`, and the only
  party holding the contradicting artefact would have no operation with which to
  produce it.
- `GET /arp/outputs` returns, for the Outputs whose Audience Set names the
  authenticated principal, the Reconciliation Hash, the Reliance Horizon and the
  Entry Sequence Number of the reconciliation entry that records each. It is
  ordered by that Entry Sequence Number descending, which is a total order and
  needs no tie-break. A `since` parameter carrying an {{RFC3339}} UTC time is
  REQUIRED; a server MUST return at most 100 entries and MUST carry a `next`
  parameter value in the response where more exist, which the requester supplies
  on the following request. Entitlement: any authenticated principal, as to its
  own membership only; and an Audit Identity, as to the Outputs of
  reconciliations addressing the register whose agreement declares it, without
  which an auditor entitled to Outputs by hash would hold no operation that
  yields the hashes.
- `GET /arp/continuations/{reconciliation-hash}` returns the Continuation entries
  of {{settlement-ledger}} carrying that Reconciliation Hash, in Entry Sequence
  Number order, and no reconciliation entry. Entitlement: an Audience Member of
  the Output that Reconciliation Hash identifies, or a regulator in scope for
  that reconciliation under {{regulator-portal}}.
- `GET /arp/entries/{entry-sequence-number}` returns one Ledger entry.
  Entitlement: a regulator, subject to {{regulator-portal}}; an Audience Member,
  for an entry carrying a Reconciliation Hash it is entitled to; and a Register
  Operator or regulator requesting the Self-Entry Hash alone, for the consistency
  check of {{settlement-ledger}}, by the `fields=self-entry-hash` query
  parameter. Any requester whose signature verifies under {{read-signing}} is
  additionally entitled to the four-element array of the Entry Sequence Number,
  the Prior-Entry Hash, the Self-Entry Hash and the Signing Input Digest of that
  entry's Entry Signature, by the `fields=linkage` query
  parameter, for the head linkage of {{quorum-rule}}, **and only for an Entry
  Sequence Number at or below the head of the most recently published Ledger
  Head Statement**. A request under that parameter naming a higher sequence
  number MUST be refused with `404` whether or not the entry exists. Without
  that bound the projection is a live head oracle: the Ledger is contiguous, so
  a requester could binary-search the current head between publications and poll
  it for the write rate, which is the disclosure {{settlement-ledger}} publishes
  the head once per notarisation interval to prevent. Bounded, the projection
  carries no Reconciliation Hash and no structural metadata and discloses nothing
  beyond the chain shape below a head that is already published
  unauthenticated. It is rate-limited as {{read-errors}} provides.
- `GET /arp/post-seal-records/{post-seal-evaluation-record-hash}` returns the
  Post-Seal Evaluation Record of {{post-seal}}. Entitlement: as for the
  Continuation entry that carries the hash.
- `GET /arp/sweeps/{examined-set-root}/inclusion/{claim-hash}` returns an
  inclusion proof of that Claim Hash under that Examined-Set Root. Entitlement: a
  party entitled to a reconciliation carrying that Claim Hash. The Statement is
  keyed on its Examined-Set Root rather than on its timestamp, which is pinned to
  whole seconds and would collide where two triggers fall in one second.
- `GET /arp/re-notifications` returns the Sovereign Re-Notifications of
  {{re-notification}} whose Notification Timestamp falls in the interval named by
  REQUIRED `since` and `until` parameters, at most 100 per response under the same
  `next` rule. Entitlement: a regulator, as to notifications addressed to it.
- `GET /arp/sweeps` returns the Evaluation Sweep Statements of
  {{sweep-statements}} whose Evaluation Sweep Timestamp falls in the interval
  named by REQUIRED `since` and `until` parameters, at most 100 per response
  under the same `next` rule. Entitlement: a Register Operator, a regulator or an
  Audience Member. Its
  counts are deployment-wide aggregates and disclosing them to a party named in
  one Audience Set is a real cost, recorded in {{privacy}}; the Statement is a
  signature over a fixed array and cannot be served with fields removed without
  destroying the signature that makes it worth serving.

The enumeration is what makes the Entry Sequence Number of a party's own
reconciliation entry reachable. Without it an Audience Member entitled to that
entry under {{settlement-ledger}} would have no operation that maps its
Reconciliation Hash to a sequence number, and its only route to an entitlement
this document grants would be the sweep of `GET /arp/entries/{n}` that the rate
limit below exists to prevent.

### Responses {#read-responses}

Every response to an operation of {{read-operations}} or to the commissioning
request of {{request-binding}}, including every `4xx` other than the `401` of
{{read-signing}}, MUST be a COSE_Sign1 by the reconciliation-server sealing key, under the media
type registered in {{iana}}, whose payload is the CBOR array

    ["arp-read-v1", request-binding, status, response-time,
     as-of-sequence-number, as-of-self-entry-hash, result]

where:

- `request-binding` is the SHA-256 digest over the CBOR array of the request's
  `@method`, its `@target-uri` normalised as in Section 6.2.2 and 6.2.3 of
  {{RFC3986}}, the request's `nonce`, and its `keyid`. Digesting a normalised
  binding rather than echoing the target as sent leaves nothing to disagree about
  and binds the response to one requester and one request.
- `status` is the HTTP status code.
- `response-time` is the time the response was produced, in the timestamp form of
  {{reconciliation-output}}.
- `as-of-sequence-number` and `as-of-self-entry-hash` MUST be those of the Ledger
  head at the moment the read was served, and MUST NOT be those of any earlier
  entry. A response naming a head lower than the most recently published Ledger
  Head Statement is non-conforming, and a reader MUST reject one: a server free to
  answer against a head it chooses could suppress a supersession indefinitely by
  answering truthfully about a stale head, and its answer would never contradict
  anything.
- `result` is the operation's result, an empty array where the operation is
  set-valued and nothing matched. On a `404` it is an empty array. On the `422`
  or `403` of {{request-binding}} it is the Remediation Advisory, which is the
  artefact a refused requester needs; on a `429` it is an empty array.
- For a response to the commissioning request, `as-of-sequence-number` and
  `as-of-self-entry-hash` are those of the Ledger head at the moment the
  response was produced, and the `request-binding` digest is taken over a
  five-element array, the request's `content-digest` appended after its
  `keyid`.

Signing errors as well as successes is the load-bearing part. A server that
signed only its successes could suppress any continuation channel by answering
`404` or `429` forever, and the party it was suppressing would hold an unsigned
status line: no proof that it asked, no proof of what it was told, and no way to
distinguish suppression from a hash that names nothing. Binding the response to
the requester's nonce and key, and stamping it with a time, is what stops a
server serving one party's response to another or replaying a year-old empty
result; without those the same bytes verify forever and against everybody.

A reader MUST check that the `request-binding` matches the request it sent, that
the `response-time` is within a declared freshness tolerance, and that the
`as-of-sequence-number` is at least that of the most recent Ledger Head Statement
it has seen. A deployment MUST declare that tolerance in its Bilateral Register
Agreements and it MUST NOT exceed the effective ledger-head notarisation
interval of {{settlement-ledger}}, being the shortest any Bilateral Register
Agreement the deployment holds declares, per the direction rule of
{{delivery}}: a tolerance left to each reader is not a property two
implementations can be tested against, and one longer than the notarisation
interval would admit a response naming a head the reader could already know to
be superseded. Without those checks a server may serve a cached response for a
repeated request tuple indefinitely, and the properties below do not hold.

An empty result is therefore an assertion and not an absence: a signed statement
that as of a named head, at a named time, in answer to this requester's request,
there was nothing. A `continuation-supersession` entry later found at or below
that head contradicts it, in one operator's own signature.

That contradiction is conditional on the reader and the later observer having
been served one chain, and the condition is load-bearing. {{settlement-ledger}}
states that detection of a fork is opportunistic: an operator publishing to two
audiences at disjoint sequence numbers never emits a colliding pair. Under such
a fork the superseding entry lands on a branch the holder of the empty result
never reads, the at-or-below test never fires, and the assertion stands
uncontradicted for as long as the branches are kept apart. An empty result is
therefore an assertion about a named head on the chain its reader was served,
and it is falsifiable to the extent that the reader holds head-consistency
evidence for that chain from an observer independent of the responding service.

Head evidence obtained only from that service does not bound this. A fork at
disjoint sequence numbers is invisible from a single vantage by construction,
and the vantage is what is in question: equivocation is precisely the condition
that no single consistent chain explains two observations, so it becomes
observable when two independent observers compare heads and not before. A
relying party acting on an empty result SHOULD hold head-consistency evidence
for the served chain from at least one observer independent of the responding
service -- a witness countersignature over the head, or, where no Witness Set is
available, an independently anchored head digest, in decreasing order of
strength. {{bra-witness}} specifies the Witness Set and the Witness Quorum, so
that "at least one observer independent of the responding service" is a
condition a deployment declares a value for and an implementation can be tested
against, rather than a property each reader decides for itself. What that
quorum does and does not establish is stated in {{bra-limits}}: it is
independence declared, not independence proven, and this document still does not
claim to close the gap.

The contradiction is only as tight as the operator's freedom to defer. A
`continuation-supersession` entry MUST be appended within the ledger-head
notarisation interval of {{settlement-ledger}}, measured from the completion of
the Evaluation Sweep that produced the superseding Output -- an event the
Evaluation Sweep Statement of {{sweep-statements}} dates and signs, and which
therefore exists for an immaterial supersession as much as for a material one.
Where the supersession is the revocation of a Verified Principal Credential and
no superseding Output is produced, the deadline runs from the completion of the
sweep the revocation triggered, which {{sweep-statements}} likewise dates and
signs. Measuring from "the material change" would leave both that case and an
immaterial supersession with no start point and so no deadline. Without a deadline an operator defers
every supersession above the highest head it has ever named and no contradiction
ever arises.

### Error semantics {#read-errors}

A request that is well-formed and signed but that names a resource the requester
is not entitled to, and a request naming a resource that does not exist, MUST
both be refused with `404`. Only an entitled requester receives `200`. Answering
`403` for the first and `404` for the second would turn every endpoint into an
existence oracle: a party could sweep Reconciliation Hashes, or sequence numbers,
and learn what a deployment had done without being entitled to any of it.

The two cases MUST be equivalent under the normalised observation this section
defines, rather than byte-identical, which a conforming server cannot make them:
{{read-responses}} requires every response to bind the request and the serving
instant, so the `request-binding`, the `response-time`, the As-Of pair and the
resulting signature differ between any two requests whether or not the resource
exists. A requirement of byte equality would be unsatisfiable, and a test
written against it would fail every conforming implementation.

The normalised observation of a response is that response with exactly those
four values removed. Two responses are equivalent when their normalised
observations are equal. Across the two cases a server MUST therefore produce the
same status, the same media type, the same set of HTTP header field names, the
same set of protected COSE header parameters, the same empty-result
representation, the same cache directives and the same rate-limit effects, and
the signed payload MUST NOT carry any error discriminator whose value depends on
whether the resource exists. Every value removed by normalisation MUST still be
valid for its own request: normalisation is how two responses are compared, not
a licence to omit a required field or to carry an existence-dependent
discriminator inside one.

A response to either case MUST carry `Cache-Control: no-store`. A response bound
to a nonce and a serving instant is not reusable by another requester, and a
cache that retained one case and not the other would reintroduce through
intermediaries the distinction the rest of this section removes.

Two channels survive that rule and MUST be closed with it. A server MUST charge
the rate-limit counter before evaluating entitlement, so that an unentitled
request and a nonexistent one consume the same budget and a burst of each yields
the same sequence of statuses. And entitlement evaluation MUST NOT be
short-circuited: a server MUST perform the same work for a Reconciliation Hash it
does not hold as for one whose Audience Set does not name the requester, so that
the two do not differ in response time.

Response timing is a separate claim from the requirements above and MUST be
stated separately. Serving both cases from one processing path is evidence about
the design and is not evidence that the two latency distributions are
indistinguishable to an observer. An implementation that claims resistance to
timing-based existence inference MUST publish the measurement population, the
sample count, the network placement of the measurement, the decision rule and
the acceptance threshold under which the two response classes were compared. An
implementation that makes no such claim is not for that reason non-conforming:
the requirements above are met or not met independently of it, and conflating
the two would let a deterministic conformance failure be excused as a
measurement artefact, or a measurement result be read as protocol conformance.

The `fields=linkage` projection of {{read-operations}} answers `200` for an
entry whose full read the same requester would be refused, and is not an
existence oracle for two reasons that both have to hold. The Ledger carries a
contiguous Entry Sequence Number and {{settlement-ledger}} publishes the head
unauthenticated, so existence at or below that head is already public and the
projection discloses no fact about which entries exist. And the projection is
bounded at that published head, so it cannot answer the one existence question
that is not already public, which is where the head is now. A projection that
widened either -- serving a non-contiguous ledger, or serving above the
published head -- would be an oracle, and neither is permitted.

A server MUST rate-limit these operations, per authenticated principal, at the
most permissive rate any of its Bilateral Register Agreements declares, and MUST answer `429` when the limit
is reached. The declared rate MUST admit at least one read of each operation per
Reconciliation Hash per reliance interval, so that a limit cannot silently void
the obligation of {{reliance-horizon}}. `GET /arp/entries/{n}` in particular
ranges over the whole Ledger; unlimited, a party entitled to one consistency
check could sweep for the deployment's entry count, write rate, and the timing of
retroactive bursts, which is disclosure by aggregation of a surface every
individual answer to which is innocuous.

A read served under {{regulator-portal}} with any field redacted MUST NOT return
the Prior-Entry Hash or the Self-Entry Hash of that entry, and MUST NOT return
the Prior-Entry Hash of the entry that follows it, which is the Signing Input
Digest of the redacted entry's Entry Signature and so covers every field of that
entry including the fields being withheld. The Self-Entry Hash is a digest over the entry's
own fields and carries no blinding value; a reader holding the leading fields and
denied the type-specific block could otherwise recover the block by search over
register subsets, a small aggregation descriptor set, four binding classes and a
bounded timestamp, and would do so off the audit trail that section imposes. A
redacted field is returned as CBOR null in its position, so that the array's
length is still the length fixed by the Entry Type; a regulator receiving a
redacted entry therefore cannot verify its chain hashes, which is the price of
redaction and is why an unredacted read is the ordinary case.

Each read served under this section MUST be recorded in an append-only access
log, retained for the period of {{delivery}}, sequenced, chained, headed and
notarised as the audit trail of {{regulator-portal}} is and for the same reason. The log is not the Settlement-Layer
Ledger and MUST NOT be written to it: who asked a question is not a fact about
the reconciliation, and a Ledger that recorded reads would disclose the pattern
of interest in a subject to every party entitled to read it. The log is readable only by a regulator under
{{regulator-portal}} and by an Audit Identity under {{audit-path}}, to which it is
disclosed out of band as the policy-epoch material is; the reasoning that keeps
it off the Ledger applies equally to the log itself.

## SCITT Reference API Binding {#scrapi-binding}

A Reconciliation Output MAY be notarised into a SCITT Transparency Service as a
transparent statement. Where it is, an implementation MUST use the binding in
this section. {{composition-scitt}} states the architectural relationship; this
section states the wire behaviour, so that two implementations registering the
same Reconciliation Output against the same Transparency Service produce
interchangeable results.

### Registration {#registration}

The Reconciliation Output MUST be registered as a Signed Statement by
`POST /entries` as defined in {{I-D.ietf-scitt-scrapi}}, with the HTTP
`Content-Type` that document requires on that request. A Transparency Service
returns a `Location` header on both `201 Created` and `202 Accepted`; an
implementation MUST use it in both cases rather than constructing a polling URL
of its own.

Notarising an Output does not enlarge its Audience Set. Registration places the
sealed Output in a log whose retrieval is by EntryID, and a party that obtains it
that way holds it on the terms of {{entitlement}}: it may verify the Sealing
Signature and read the Combined Verdict, and it obtains no read under
{{ledger-read}} and no notice of supersession. A deployment for which that is
the wrong disclosure should not notarise; {{scrapi-binding}} is composed
permissively for that reason.

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
and every other check here would pass, and the Receipt would attribute the
statement to the Transparency Service and to nobody else. Fixing the nested payload closes a false-policy-version
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

### Asynchronous registration {#async-registration}

A Transparency Service may register synchronously or asynchronously, and an
implementation MUST support both. This is the most likely source of divergence
between two otherwise conforming implementations, and is therefore stated as a
requirement rather than left to the referenced document.

On `201 Created` the Receipt is available immediately. On `202 Accepted` the
response carries a `Location` header, and the implementation MUST poll that URL
verbatim rather than constructing a path of its own. A `204 No Content` means
registration is still in progress and MUST NOT be treated as failure or as a
negative result.

A `4xx` other than `404` returned synchronously by `POST /entries` is a terminal
refusal and MUST NOT be retried under the same Signed Statement; it is the
ordinary refusal case and is recorded as such under {{settlement-ledger}}.

A `404 Not Found` ends polling and MUST NOT be polled further. It carries two
meanings in {{I-D.ietf-scitt-scrapi}} -- that no Receipt was found for the
specified EntryID, and that an asynchronous registration has failed and no
Receipt will be produced -- and an implementation MUST distinguish them from the
response body where the service supplies one, because the second is a
registration failure and the first may follow from having polled a URL the
Transparency Service did not issue. Ending polling is not
the same as resolving the outcome: only the second meaning is a terminal refusal
for the purposes of {{settlement-ledger}}, and a `404` the implementation cannot
resolve to one meaning or the other is recorded as an incomplete notarisation,
not as a refusal.

An implementation MUST honour a `Retry-After` header where one is present, MUST
NOT poll more frequently than once per second in its absence, and MUST bound
total polling, to the shortest bound any Bilateral Register Agreement addressed
by the reconciliation declares; a bound of 300 seconds is RECOMMENDED where the
Bilateral
Register Agreement declares none. Exhaustion of the bound MUST be recorded in a Post-Seal Evaluation Record
carrying `notarisation-incomplete` per {{post-seal}}, rather than as either
success or refusal. A
Reconciliation Output whose notarisation is incomplete remains valid under its
Sealing Signature; notarisation is an additional property, not a precondition of
validity.

### Sealing-key discovery {#sealing-key-discovery}

A signed key set, wherever this document requires one, is a COSE_Sign1 whose
payload is the deterministically encoded CBOR serialisation of the COSE_KeySet,
under the media type registered in {{iana}}. Each key in the set carries the
`arp-key-status` and `arp-key-validity` COSE Key common parameters registered in
{{iana}}. An Authorised-Origin Document is a COSE_Sign1 whose payload is a CBOR
array of three-element arrays -- the server's authority origin, the identifier of
the key signing its sealing key set, and the identifier of the key signing its
operator key set -- sorted in bytewise lexicographic order of the origin.

A relying party is not a party to any Bilateral Register Agreement and holds
only the hashes of those agreements. It therefore cannot resolve the sealing key
from them, and a binding that assumed otherwise would oblige every conforming
relying party to refuse every Reconciliation Output.

A reconciliation server MUST publish its sealing keys as a COSE Key Set at
`/.well-known/arp-sealing-keys` on the reconciliation server's authority origin,
and
a single key by identifier at `/.well-known/arp-sealing-keys/{kid_value}`. The
Sealing-Key Identifier is the pair of that origin and the `kid`; where this
document requires a `kid` to equal the Sealing-Key Identifier, a key identifier in this document is in every case the JWK thumbprint of
{{RFC7638}}, base64url-encoded without padding. It is carried as a CBOR text
string in every payload field and in every `keyid` signature parameter, as the
UTF-8 encoding of that same text string in a COSE `kid` (label 4), which
{{RFC9052}} makes a byte string, and as that text string unaltered in a
`{kid_value}` path segment. Every equality test this document requires between a
`kid` and a Sealing-Key Identifier component is over the base64url text. Without
one pinned form the same key has three spellings and those equality tests
compare values of different CBOR types. With that fixed, it is the `kid`
component that is compared.

Resolving a key is not sufficient. Web PKI establishes that an origin is the
origin it claims to be; it does not establish that the origin is entitled to
seal Reconciliation Outputs naming a given register set. A relying party that
accepted any well-formed key set would accept an Output minted by any party able
to stand up a host, since the Bilateral-Register-Agreement Hashes can be copied
from a genuine Output and are one-way.

Each Bilateral Register Agreement MUST therefore declare the Authority Origin of
the reconciliation server it authorises, and each register operator MUST publish
an Authorised-Origin Document at `/.well-known/arp-authorised-origins` on its own
register origin. A Register Identifier is an origin, so the register origin is a
member of the Addressed-Registers Identifier Set and is known to the relying
party from the Output.

An Authorised-Origin Document is a COSE_Sign1 whose payload comprises, for each
reconciliation server the register operator has authorised, that server's
the three-element arrays {{sealing-key-discovery}} pins above. It MUST be signed under a key served in a COSE Key Set at
`/.well-known/arp-register-keys` on the same register origin -- a key set carrying the same `arp-key-status` and `arp-key-validity` parameters as
a sealing key set, so
that a compromised register key has an in-band revocation path, and the same key
set that resolves a register's signatures on Partial Attestations and Non-Answer
Statements -- which the relying
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

A key entry MUST carry the `arp-key-validity` and `arp-key-status` parameters of
`active`, `retired` or `revoked`, and an entry whose status is `revoked` MUST
carry a revocation time as the third element of `arp-key-validity`. A relying party MUST reject a Sealing Signature made under a
`revoked` key whose Reconciliation Timestamp falls at or after the revocation time that key
entry carries, MUST reject a Sealing Signature made under a `revoked` key
carrying no revocation time irrespective of when the Output claims to have been
sealed, MUST
accept one made under a `retired` key only where the Reconciliation Timestamp
falls within that key's validity interval, and MUST reject one whose
Reconciliation Timestamp falls outside the interval of the key it resolves to. A
key MUST NOT be removed from the set while any Reconciliation Output it sealed
may still be relied upon: retirement is by status, not by deletion, so that a
historical Output remains verifiable while a compromised key can still be
refused.

Revocation without a time is repudiation of an epoch. Earlier revisions scoped
`retired` by validity interval and left `revoked` unscoped, so one status change
in a document the reconciliation server publishes, on its own origin, under its
own key, invalidated every Reconciliation Output, Evaluation Sweep Statement,
signed read response and Entry Signature that key had ever made. The rule
closing removal -- a key MUST NOT be deleted while an Output it sealed may be
relied upon -- was defeated by status, which is the same act with a different
verb.

The reconciliation server MUST therefore publish and notarise its sealing key
set as {{read-signing}} requires of the Policy Parameters Document: with a
Publication Timestamp, notarised into the Transparency Service of
{{settlement-ledger}} on the ledger-head notarisation interval, and republished
on that interval whether or not its contents changed. A relying party MUST NOT
act on a status transition it cannot date. A COSE_Sign1 is not dateable from its
own bytes, and a status flip that no party can place in time disarms every party
it disarms without any of them being able to say when, or to show that it
happened after the Output they hold.

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

A Reconciliation Output MAY be additionally serialised as a JSON-LD document
conforming to the W3C Verifiable Credentials Data Model {{W3C-VC-DM-2.0}}, under
the media type `application/arp-reconciliation-output+json` registered in
{{iana}} -- `+json` rather than `+ld+json`, there being no such registered
structured syntax suffix -- with the Reconciliation Hash, Addressed-Registers
Identifier Set, Bilateral-Register-Agreement Hash Set,
Requester-Binding-Class, Policy-Version Hash, Claim Hash, Combined Verdict,
Audience Set and Reliance Horizon
included as credential subject fields. The COSE_Sign1 envelope is the normative
form; the Verifiable Credential serialisation is an interop convenience for
relying parties operating in W3C VC ecosystems.

The Audience Set and the Reliance Horizon are not optional in this
serialisation. A credential is the form of an Output most likely to reach a party
outside its Audience Set, and one carrying neither the membership list against
which such a party could determine that it is not entitled, nor the marker of its
own staleness, would be the bearer artefact {{entitlement}} exists to retire,
reintroduced through the interop form.

## Representation Invariance {#representation-invariance}

Every interoperability defect this document has repaired in its digest
constructions is one defect. A signature that has two byte encodings for one
signing act. A CBOR item whose major type the text did not fix. A set with no
ordering rule. An optional member that could be omitted or nulled. A URI that
could be normalised on receipt or before sending. A Unicode string in NFC or in
NFD. A binary value rendered into JSON as base64, base64url or hex. A digest
taken over transmitted bytes or over a re-encoding.

In each case two byte strings carry the same information and a digest over them
differs. The information content is invariant and the representation is not, and
the digest was defined over the representation. This section states the general
rule those repairs are instances of, so that the next instance is caught by the
rule rather than by the next reviewer.

**The rule.** For every digest, signature payload and comparison this document
defines, the value MUST depend only on the information its input carries and
MUST NOT depend on any choice of representation that carries no information. A
construction that fails this is not merely inconvenient: two conforming
implementations given the same facts compute different values, and every
mechanism built on the value inherits the divergence.

**The obligation that makes it testable.** A specification cannot discharge this
by asserting it. For every digest it defines, this document names the
**representation class** of each input: the set of byte strings that carry the
same information as that input. The classes this document recognises are:

- **Signature encoding.** For ECDSA, `(r, s)` and `(r, n - s)`. The class has
  more than two members over the wire, since a low-S rule removes one member of
  an unbounded set. Handled by {{signature-malleability}}.
- **CBOR type choice.** A value expressible as more than one major type: an
  identifier as `tstr` or `bstr`, a count as `uint` or text, a URI as `tstr` or
  tag 32, a timestamp as `tstr` or tag 0. Handled by the type tables of
  {{bra-hash}}, {{reconciliation-output}}, {{partial-attestation}} and {{iana}}.
- **Collection order.** The permutations of a set. Handled by the bytewise sort
  rules stated at each set.
- **Absence.** An optional member omitted, or present and null. Handled by the
  null-substitution rules, which also fix array length.
- **Text normalisation.** The Unicode normalisation forms of one string.
  Handled by the NFC requirement of {{ingestion}}.
- **Reference normalisation.** The equivalent forms of one URI or origin.
  Handled by {{terminology}} for an Authority Origin and by {{RFC3986}}
  normalisation for the identifiers that carry it.
- **Binary rendering in a text encoding.** Base64, base64url with or without
  padding, and hexadecimal renderings of one byte string. Handled by the
  key-identifier rule of {{sealing-key-discovery}} and by the digest rendering
  of {{ingestion}}.
- **Framing.** A concatenation against an array, and an array against a map.
  Handled by the domain-separated array requirement stated at each preimage.

**A specification that defines a new digest MUST state, for every element of its
preimage, which of these classes the element belongs to and which member of the
class the preimage takes.** A registration under {{iana}} that introduces a value
carried into any digest this document defines MUST do the same, and the
designated expert MUST refuse one that does not.

**The conformance obligation.** A conformance runner for any construction in
this document MUST exercise the construction against the representation class of
each of its inputs, and not against an enumeration of previously observed
defects. The distinction is the whole of the test's value. A runner that checks
a digest against the two ECDSA signature encodings it has heard of confirms
what its author already knew; a runner that enumerates the class and asserts the
digest is constant across it detects the member nobody had thought of. The same
holds for every class above. Where a class is unbounded, the runner MUST sample
it and MUST record in its run transcript that it sampled rather than enumerated,
so that a reader is not told a property was established over a class when it was
established over a sample of one.

**What this does not establish.** Invariance across a representation class is
not correctness. A digest can be perfectly invariant and taken over the wrong
elements, and this rule says nothing about that. It says only that two parties
holding the same facts reach the same value, which is the precondition for every
other property this document claims and is not itself any of them.

# Security Considerations

## Service-Operator Containment {#containment}

The reconciliation server operates under a service-operator entity
standing in bilateral contractual relationship with each Register
Operator. The service-operator entity MUST NOT be given access to any register record or any
Partial-Attestation payload beyond the verdict and divergence-axis fields, and a
deployment MUST enforce that by construction -- by encryption addressed to the
requester or by an equivalent measure that no internal operator action can
reverse -- rather than by policy. A conformance test for this requirement is
whether an operator holding every credential the deployment issues can obtain a
register record; if it can, the deployment does not conform.

Encryption addressed to the requester discharges this requirement for a register
record, and for any enumerated field the reconciliation server does not read. It
cannot discharge it for the Query Binding, the Freshness Timestamp, the echoed
Policy-Version Hash and Bilateral-Register-Agreement Hash, the Source-Data
Version Identifier Set or the Applied-Parameter Set, each of which
{{partial-attestation}}, {{source-versioning}}, {{projection}} and
{{replay-defence}} oblige the reconciliation server to read in the clear. For
those fields the equivalent measure MUST be an execution boundary whose
integrity is remotely attestable under {{RFC9334}} and whose plaintext state no
credential the deployment issues can read, and the conformance test above
extends to them: an operator holding every credential the deployment issues must
be unable to obtain any of them.

The distinction this rests on is the one the section opens with and did not
carry through. The prohibition binds **the service-operator entity**, a legal
person, and not the reconciliation server, a process, whose reading of those six
fields the sections named above require. The two named enforcement measures were
therefore not alternatives of equal reach: the first is unavailable for exactly
the fields where the prohibition bites, and the conformance test asked only
about a register record, so the payload half of the requirement had no test at
all.

That property is per-event and MUST NOT be read as a property of the system
under repeated querying. A verdict is a function of an attested value the
requester chooses, so a sequence of reconciliations varying that value recovers
the underlying record field by search, and several Divergence Axis values --
`ownership-threshold-mismatch`, `register-record-absent`, `temporal-mismatch` --
disclose record content on their own. Each event conforms while the sequence
does not.

A deployment MUST therefore declare in each Bilateral Register Agreement a query
budget and the interval over which it is measured, and the budget MUST be
measured per accountable principal per subject, not per subject alone. The
subject half of that key is the **Claim Hash of the Canonical Claim with its
Predicate, Applicable-Regimes Set and Claim Timestamp elided**, computed as
{{terminology}} computes a Claim Hash over the remainder. The principal half is
pinned in three tiers below and the subject half was pinned nowhere, which left
the counter keyed on a value the requester controls: a Subject Identifier is
NFC-normalised as a string and nothing more, so case, leading zeros,
jurisdiction prefixes and equivalent register-specific forms each open a fresh
counter. The bound on recovery-by-search this section exists to impose was
evadable by respelling, and the per-subject ceiling was a shared counter whose
key a party could collide with a victim's, forcing every third-party
reconciliation about that victim to `indeterminate`. Where the
budget is shared across requesters, any one requester exhausts it for all of
them -- including a requester whose Requester-Binding class is
`agent-unverified`, which is to say a party the deployment has declined to
identify -- and every subsequent reconciliation about that subject is forced to
`indeterminate` for the remainder of the interval. That is a denial of service
against every other requester, granted by the countermeasure. The recovery
property this budget bounds is a property of one requester's sequence, and
sequences run by colluding principals are the business of the repeated-narrowing
pattern below rather than of a shared counter.

The budget is keyed on the accountable principal identifier where the
Requester-Binding carries one. Where it does not -- classes `agent-unverified`
and `agent-key-verified` -- the budget MUST be keyed on the verified signing key
where one exists, and otherwise on a deployment-declared fallback key such as the
authenticated transport client identity. Every requester signs, by
{{read-signing}}, so every requester has a key and none falls outside the budget.
Admitting a requester to a shared counter is the denial of service this paragraph
exists to remove.

A deployment MAY additionally declare a per-subject ceiling across all
principals. A ceiling is a shared counter and reintroduces that denial of service
by construction, so where a deployment declares one it MUST partition it: a stated proportion
reserved for principals of class `human-operator` and `agent-verified`, and
within that proportion a per-principal sub-budget, so that no one principal can
consume the reserve. Classes carrying no corroborated principal --
`agent-key-verified` and `agent-unverified` -- are charged only against the
remainder. A reserve with no per-principal partition is exhausted by a subject
that incorporates enough entities to hold enough corroborated principals, which
is a purchase and not a barrier. A
subject able to mint identities cheaply can otherwise exhaust the ceiling on
itself and force every third-party reconciliation about it to `indeterminate`,
which is a self-service veto over the verdicts this protocol exists to produce.
Exhaustion of a ceiling is recorded as `subject-ceiling-exhausted` rather than
`query-budget-exhausted`, so that the two are distinguishable in the record and
an auditor can see which counter refused.

Where a reconciliation would exceed the budget, the reconciliation server MUST
NOT transmit a projection to the affected register and MUST record
`query-budget-exhausted` as that register's Non-Answer Reason. The reconciliation
proceeds and is sealed; it cannot reach a decisive Combined Verdict, by
{{verdict-arithmetic}}. It is the register that is refused, not the
reconciliation: refusing the reconciliation outright would leave no Output in
which to record the reason, which is the artefact the requester needs in order to
know why it was refused and the regulator needs in order to see that it was.

The Pattern Library MUST include a repeated-narrowing pattern so that the
Adversarial Pre-Transmission Test detects the sequence rather than only the
event.

A register cannot apply its own statutory access regime to a requester it cannot
see. Where a Bilateral Register Agreement requires it, the Per-Register Claim
Projection MUST carry the Requester-Binding Class, which discloses the class and
not the principal.

## Budget Exhaustion as a Suppression Channel {#budget-suppression}

{{architecture}} places a reconciliation driven to `query-budget-exhausted` or
`subject-ceiling-exhausted` outside the reproducibility requirement, because the budget is accumulated state
rather than an enumerated input. That carve-out is a suppression channel and is
recorded here as one.

Any non-answering register makes a decisive Combined Verdict unreachable
({{verdict-arithmetic}}). An operator that wishes to prevent a particular
reconciliation from reaching a decisive verdict can therefore record
`query-budget-exhausted` against one register, and an auditor replaying the
enumerated inputs is required not to treat the divergence as a determinism
failure. The reason is server-observed under {{no-answer}}, so no register
signature contradicts it.

Two mitigations are available and neither is adopted here. Publishing the budget
counter and interval boundaries beside the refusal would let an auditor
distinguish exhaustion from suppression -- and would tell every requester how
much third-party interest a subject has attracted, and exactly when to exhaust
the counter so that no other party obtains a decisive verdict, which is a worse
disclosure than the one it cures. Requiring a register-signed acknowledgement of
each charge against the budget would remove the server's discretion, at the cost
of a round trip to every addressed register on every refused reconciliation,
including the ones the budget exists to avoid making.

The per-subject ceiling of {{containment}} is the stronger of the two channels,
because it is a counter several principals share: an operator need not fabricate
anything, only decline to reserve enough of it. {{containment}} requires the
reserve to be partitioned per principal for that reason, and the residual is that
the size of the reserve is a deployment choice this document does not bound.

A deployment concerned with either channel should bound it contractually: the
budget, its interval and the audit right over the counter are all declared in the
Bilateral Register Agreements, and an Audit Identity under {{audit-path}} can be
given the counter state directly. That is an out-of-band remedy and it is stated
as one.

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
entry MUST record the requester-binding class the gate determined --
`agent-unverified` where no verifiable identity was presented, or
`agent-key-verified` where a key verified and the asserted principal was not
corroborated -- so that downstream reliance is aware no accountable principal was
established and can still tell the two apart.

## Bilateral-Register-Agreement Drift {#agreement-drift}

Each Bilateral Register Agreement carries an Agreement Hash. Each Partial
Attestation includes a reference to the Agreement Hash under which it was
issued. Agreement drift is detectable by comparison of agreement-hash
references across Partial-Attestation batches. Reconciliation MUST be
suspended for an addressed register whose Agreement Hash deviates from the
hash committed at the start of a reconciliation event. A suspension under this
section ends when the two parties have agreed a new Agreement Hash under
{{bra-hash}} and the reconciliation server holds it as the hash it commits at the
start of the next reconciliation event, from which event the register is
addressable again. A suspension arising instead from the irreconcilable head
statements of {{settlement-ledger}} ends only when the Register Operator that
refused further projections states, under the read key of item 22 of
{{bra-items}}, that the discrepancy is resolved. No other event ends either, and
a deployment MUST NOT treat the passage of time as ending one.

## Replay Defence {#replay-defence}

Each Partial Attestation MUST carry a Freshness Timestamp. The
reconciliation server MUST verify the Freshness Timestamp against a
freshness window declared in the Bilateral Register Agreement. The window is
measured backward from the instant the reconciliation server received the
Partial Attestation. An attestation is fresh where its Freshness Timestamp is no
earlier than that instant less the declared window and no later than 60 seconds
after it, and a Freshness Timestamp further in the future MUST be treated as
stale. A window with no stated reference instant and no stated direction is a
test two implementations apply differently to the same attestation, and the
register cannot tell which one it will be held to. This document states the
reference instant and direction for the witness observation window of
{{quorum-rule}} and did not state them here. Stale Partial Attestations MUST be rejected, and the rejection MUST be recorded
in the Reconciliation Output under {{no-answer}} with the Non-Answer Reason
`attestation-stale` and a `freshness-stale` divergence axis attributed to that
register. A signed agent request under {{RFC9421}} MUST additionally carry a
nonce and created/expires parameter set that {{read-signing}} requires, so that
a captured signed request
cannot be replayed to initiate a fresh reconciliation.

## Post-Quantum Migration {#post-quantum}

The Cryptographic-Primitive-Upgrade Path is the mechanism by which ARP
deployments migrate to post-quantum primitives. ML-KEM-1024 {{FIPS203}}
is RECOMMENDED for the claim-encryption primitive class. ML-DSA-65
{{FIPS204}} is RECOMMENDED for the partial-attestation-signature and
sealing-signature primitive classes. Implementations MUST declare their
chosen post-quantum primitives in the Bilateral Register Agreement.

## Side-Channel Considerations {#side-channel}

The disclosure model as a whole, and the residual risks this document accepts,
are set out in {{privacy}}.

Per-register projection narrowing is observable to the addressed register
through the Projected Predicate. Implementations MUST NOT use narrowing
patterns to fingerprint individual subjects. The Predicate Taxonomy SHOULD
be designed such that the set of permitted narrowings is small enough that
narrowing observation does not materially weaken subject privacy.

## Signature Malleability and Artefact Identity {#signature-malleability}

A digest taken over a signed artefact as served identifies that artefact only
where the signature has one valid encoding, and not every primitive this
document admits has that property.

For ECDSA, a signature `(r, s)` and the signature `(r, n - s)`, where `n` is the
order of the curve's base point, both verify against the same key over the same
message. No specification prohibits it: Section 4.1.4 of SEC1 v2.0 and Section
6.4.2 of FIPS 186-5 range-check `r` and `s` only, and Section 2.1 of
{{RFC9053}} constrains neither. The substitution follows from the verification
equation and falls outside every check any of the three imposes. No specification is violated and
nothing is forged: the signing authority is identical in both encodings, and a
party holding no key can produce the second from the first while it is in
transit. Measured over two hundred randomly generated P-256 keys and ES256
signatures, two hundred substitutions verified and two hundred changed the
enveloped bytes.

EdDSA is not exposed to this substitution. Section 8.4 of {{RFC8032}} puts the
check that the decoded `S` is less than `l` inside verification, so an attacker
holding an Ed25519 or Ed448 signature cannot derive a second byte-string that
verifies over the same message under the same key. That is a non-malleability
property and not a claim that only one byte-string can ever verify: Section
5.1.7 of {{RFC8032}} leaves cofactored and cofactorless verification optional,
so conforming implementations can differ at the margin. A deployment that declares only EdDSA signature primitives
under item 2 of {{bra-items}} is therefore not reachable by this. Nothing in
this document requires that, and a deployment declaring an ECDSA primitive is
conforming, so the constructions and not the primitive choice are where this is
addressed.

Every digest in this document that identifies or chains a signed artefact is
accordingly a Signing Input Digest, or has its embedded signatures replaced by
one. Those are the Prior-Entry Hash of {{settlement-ledger}}, the Post-Seal
Evaluation Record Hash of {{post-seal}}, the Merkle leaf of {{aggregation}}, the
authority-reference digest of {{composition}} in its tagged-transparency form,
the Reconciliation Hash of {{terminology}}, and -- reached through the
Reconciliation Hash rather than named beside it -- the authorising operator's
signature in the Override Record of {{adversarial-test}}.

The sixth was found after the first five had been repaired, and the way it was
missed is worth stating rather than quietly corrected. The first sweep looked
for digests taken over signed artefacts, found the Reconciliation Hash embedded
a register signature, and repaired that. The Override Record is a signature
made by a third party -- the authorising operator, deliberately not the server,
under {{adversarial-test}} -- travelling to the server over a channel the server
does not control, and sitting in a field the Reconciliation Hash preimage
carries. It failed no test that was applied to it; no test was applied to it.

An implementation MUST therefore apply the rule of {{terminology}} over the
class rather than over the list above: in any preimage this document defines,
every signature made by a party other than the party computing the digest is
replaced by its Signing Input Digest. A specification that enumerates the
carriers is correct until someone adds a field, and correctness that expires on
the next revision is not the property this section exists to establish. The `Sig_structure` excludes the
signature by construction, which is why this is total where a low-S
canonicalisation rule is partial -- low-S removes one encoding from a set with
more than one member, while the signing input has one value for one signing act
however many encodings of the signature exist.

The Reconciliation Hash is the one worth naming separately, because excluding
the Sealing Signature is what an earlier revision did and it is not sufficient.
A Reconciliation Output embeds a register signature in each Query Binding Record
and in each Non-Answer Statement of {{reconciliation-output}}, so its preimage
carried a signature after the sealing one was excluded. The Reconciliation Hash
is a field of every Settlement-Layer Ledger entry, and therefore inside the
Entry Signature payload and inside the Prior-Entry Hash, so leaving it exposed
would have reintroduced at one remove exactly what fixing the Prior-Entry Hash
removed. The Self-Entry Hash of {{settlement-ledger}} nulls the signature
position and was already outside it.

The consequence of getting this wrong is not a forgery and is easy to
misdiagnose as one. A reader served a substituted entry computes a Prior-Entry
Hash that does not match the following entry's, and concludes the chain is
broken when the operator equivocated about nothing. Under {{leaf-binding}} a
substituted Partial Attestation makes a verifier refuse a valid inclusion proof
for the same reason. Both are failures of verification rather than of
authenticity, and a deployment that reports them as detected tampering will be
reporting something that did not happen.

## Declared Trade-offs {#tradeoffs}

Several properties this document would like to hold cannot hold together. Where
that is so, the document chooses, and this section is the list of the choices in
one place, so that a reader can find what was given up without reading for it.

The discipline is worth stating on its own. A specification that wants two
incompatible properties has three options: claim both and be wrong somewhere a
reader has to find; weaken both until the conflict disappears and deliver
neither; or take the conflict as irreducible, choose, and say where the loss
went. The third is the only one that leaves a reader able to reason about a
deployment. What makes it work is that the loss is **located** rather than
distributed: a reader who knows exactly which property was surrendered, and
where, can compensate for it, and a reader told that everything holds cannot.

| Wanted | Also wanted | Given up | Stated in | What a reader can check instead |
|---|---|---|---|---|
| Reproducibility from enumerated inputs | Uniqueness per reconciliation | Field-for-field identity, for three fields | {{architecture}} | Every other field is identical; the three are carved out by name |
| Erasure of a subject's data | An append-only record | Permanence of Output content | {{privacy-erasure}} | No chain depends on content; a digest whose preimage is gone is still a valid chain element |
| A flag-day-free schema upgrade | Telling withheld from never-defined | The upgrade; absence is encoded, not omitted | {{settlement-ledger}} | Array length is fixed by Entry Type, so a short array is a defect and not a version |
| A chain stable under re-encoding | A verifier-side test that an entry was signed once | The test | {{signature-malleability}} | The obligation remains and is examinable by an auditor; a re-signature under a different key still moves the chain |
| Digests unguessable from outside | An auditor who can recompute them | Recomputation without the blinding value | {{audit-path}} | Self-consistency across two reads, and nothing more, which that section now says |
| A register recognising a returning counterparty | A requester unlinkable across reconciliations | Unlinkability, by default | {{sealing}} | The deployment may substitute a per-reconciliation element; the choice is declared |
| One interoperable register leg | Sovereign registers keeping their own interfaces | The common leg | {{format-profiles}} | Every leg is declared in an Agreement whose hash is committed to |
| A regulator reading a redacted entry | That regulator verifying the entry's chain | Chain verification under redaction | {{read-operations}} | Redacted fields are null in place, so the length is intact and an unredacted read is available |
| Errors that tell a requester what went wrong | Endpoints that are not existence oracles | Distinguishing errors, on the read path | {{read-errors}} | The commissioning path distinguishes them and pays for it in rate limit and access log |
| Coverage measured without cost | Probes indistinguishable from real work | Free measurement | {{coverage-probes}} | A probe consumes a real budget against a real register, which is what makes it uncountable by the operator |
| A quorum proving observer independence | A test a verifier can actually run | Proof of independence | {{bra-limits}} | Distinct declared parties and distinct keys, both mechanically checkable |

Two things follow from having written this table that were not obvious before
writing it.

The first is that most of the losses are **stated limits rather than open
defects**, and the difference is whether a reader can compensate. A limit a
reader knows about is an input to that reader's decision; a limit it does not
know about is a false belief. This document has repeatedly found that its own
worst errors were sentences claiming a property it did not have, rather than
missing properties honestly described, and the table is the form that makes the
distinction hard to lose.

The second is that a row can be **retired by invention**. Two rows that stood in
earlier revisions no longer do: the falsifiability of a sweep against its
operator, which was traded away and has been bought back by anchoring the Policy
Parameters Document; and the verifiability of the sweep counts, which was
conceded as an assertion and is now an accounting identity against the Ledger. A
trade-off is a statement about the mechanisms available at the time it was made,
not a law, and a list of them is also a list of what to attack next.

# Privacy Considerations {#privacy}

This protocol operates over beneficial-ownership registers, corporate registries,
consolidated sanctions lists and customs records. Its subject is almost always a
party that is neither the requester nor a recipient, and that is not told a
reconciliation about it occurred.

The disclosure model has two artefacts and one division. A Reconciliation Output
is confidential to its Audience Set and carries subject references,
register-signed attestations and principal identifiers; the Settlement-Layer
Ledger is broadly readable and carries digests, register origins and structural
metadata. {{entitlement}} states the division and the rules that rest on it.

What is protected. The Deployment Blinding Value of {{sealing}} keeps the Claim
Hash and the Policy-Version Hash from being inverted by exhaustive search over
their low-entropy preimages, which is what stops a Ledger reader recovering the
subject and the commissioning principal. Entitlement follows the Audience Set,
so possession of an Output is not authorisation to learn what happened to it
afterwards. Enrolment under {{request-binding}} means a requester cannot direct
an Output at a party that has not agreed to receive one. The per-principal query
budget of {{containment}} bounds recovery of a register record by repeated
querying. Read responses are rate-limited and logged, and the log is not on the
Ledger, because a Ledger that recorded reads would disclose the pattern of
interest in a subject to everyone entitled to read it.

What is not. A subject has no standing in this protocol: it is not notified, it
cannot object, and it cannot learn that it was reconciled. That is a deliberate
property of a sanctions-screening protocol and a real cost, and a deployment
operating where subject rights attach should provide for them outside this
document. An Audience Member learns the subject, the predicate and every
register's answer; the audience constraint of {{audience}} lets a register cap
how many such parties there may be, and the register cannot verify that the cap
was enforced. Notarising an Output under {{scrapi-binding}} places it in a log
whose retrieval is by EntryID, and a deployment for which that is the wrong
disclosure should not notarise. The Ledger Head Statement is unauthenticated and
carries a contiguous sequence number, so it discloses the deployment's size and
approximate rate at the notarisation interval. An Audit Identity under {{audit-path}} reads every Output of every reconciliation
addressing its register irrespective of Audience Set, and each register declares
one, so a deployment's disclosure surface grows with the number of registers it
addresses. An Override Record names an authorising operator in the clear inside
the Output. {{budget-suppression}} records a further residual risk, and
{{side-channel}} the projection-narrowing channel.

## Against the threat model of RFC 6973 {#privacy-6973}

Taking the threats of Section 5 of {{RFC6973}} in turn, and stating the residual
rather than the mitigation where there is one.

**Surveillance and correlation.** Every digest that could otherwise correlate a
subject across deployments is blinded: a Claim Hash cannot be recomputed outside
the deployment that produced it and equality of Claim Hashes across deployments
is not a comparison that can be made at all. Within a deployment, correlation is
by design -- the Ledger index is a stable function of the claim, which is what
makes retroactive re-evaluation possible -- so a Ledger reader entitled to
nothing else still learns that some subject was reconciled repeatedly, and how
often. That residual is inherent in an append-only index and is not closed here.

**Identification.** The Ledger carries no Subject Identifier and no Subject
Reference. Those travel to the addressed registers, which is unavoidable in a
protocol that asks a register about a subject, and into the Reconciliation
Output, which is confidential to its Audience Set.

**Secondary use and disclosure.** A reconciliation server MUST NOT write a
Subject Identifier, a Subject Reference, an Applied-Parameter Set or any
register-record field to the Settlement-Layer Ledger, and MUST NOT include one
in any artefact it notarises into a Transparency Service. Notarisation under
{{scrapi-binding}} places the sealed Output into an append-only log operated by a
third party, and a sealed Output carries Subject References inside its Query
Binding Records. Notarisation of an Output is a MAY and MUST NOT be performed
where the deployment's subjects have not been accounted for in that disclosure.
The Ledger Head Statement, the Evaluation Sweep Statements and the Policy
Parameters Document carry no subject data and are the artefacts this document
requires to be notarised.

**Exclusion.** The subject is not told, cannot object and cannot learn that it
was reconciled. This is stated above as a deliberate property and it is the
sharpest privacy cost the protocol imposes. It is restated here because
{{RFC6973}} names exclusion as a threat in its own right and a document that
lists its mitigations and passes over the one threat it does not mitigate is
reporting selectively.

## Erasure and rectification against an append-only record {#privacy-erasure}

A jurisdiction in which a subject may require erasure or rectification of
personal data is in direct tension with a Ledger this document requires to be
append-only and with a Transparency Service it requires to be outside the
operator's control. That tension cannot be resolved by a protocol mechanism, and
this document does not claim to resolve it. What it can do is bound what has to
be erased, and that is a design obligation rather than a remark:

- **No personal data is written to the Ledger**, per the rule above. What the
  Ledger carries about a reconciliation is digests, register Authority Origins,
  verdict values and structural metadata. An erasure obligation over the
  subject's data therefore falls on the Reconciliation Output and the register
  correspondence, both of which are held by the deployment and both of which
  have a retention period.
- **A retracted or rectified verdict is expressed by supersession and not by
  deletion.** {{retroactive}} appends a `continuation-supersession` entry and
  {{re-notification}} notifies the affected regulators. The superseded Output
  remains identified by its Reconciliation Hash and its content may be destroyed
  at the end of its retention period without breaking any chain, because no
  chain hashes the Output's content: the Ledger commits to the Reconciliation
  Hash, and a digest whose preimage no longer exists is still a valid chain
  element. **This is the property that makes erasure implementable at all, and
  an implementation MUST NOT introduce any construction that hashes Output
  content into the chain.**
- **A deployment that has notarised an Output cannot erase it**, because the
  Transparency Service is required not to be under the operator's control. That
  is the reason notarisation of an Output is optional and is now prohibited
  where the disclosure has not been accounted for.

A deployment operating under an erasure regime should treat the retention period
of {{delivery}} as the erasure horizon for Output content, and should not
notarise Outputs. This document states that as guidance and not as a
requirement, because the obligation arises outside it and its shape differs by
jurisdiction. What is normative is the constraint that makes any of it possible:
personal data does not enter the append-only record, and nothing in the chain
depends on the continued existence of the content that could be erased.

# IANA Considerations {#iana}

This document requests IANA to register the following:

- Four COSE header parameters in the COSE Header Parameters registry, values
  to be assigned by IANA:
  - `arp-bilateral-agreement-hash` (value TBD)
  - `arp-policy-version-hash` (value TBD)
  - `arp-source-data-version` (value TBD)
  - `arp-witness-identifier` (value TBD)

  `arp-witness-identifier` is a CBOR text string carrying the identifier of the
  Witness Entry whose key signed the Head Consistency Statement, and is used by
  {{head-consistency}};
  `arp-policy-version-hash` is a CBOR byte string;
  `arp-bilateral-agreement-hash` is a CBOR array of byte strings;
  `arp-source-data-version` is a CBOR array of two-element arrays, each of a list
  name and that publisher's state identifier, as {{source-versioning}}
  constructs it. Each MUST appear in a protected header and MUST NOT appear in an
  unprotected one: every one of them is a commitment a verifier
  relies on, and a commitment a signature does not cover is not a commitment.
  `arp-policy-version-hash` and `arp-bilateral-agreement-hash` are used by
  {{registration}}; `arp-source-data-version` is used by {{source-versioning}}.

- Two COSE Key common parameters in the COSE Key Common Parameters registry,
  values to be assigned by IANA: `arp-key-status` (value TBD), a CBOR text string
  of `active`, `retired` or `revoked`; and `arp-key-validity` (value TBD), a
  two-element CBOR array of the not-before and not-after times, or a
  three-element array whose third element is a revocation time where the entry's
  `arp-key-status` is `revoked`, each in the form of
  {{reconciliation-output}}. {{sealing-key-discovery}} requires both on every key
  it publishes, and a key parameter used normatively and never registered is a
  parameter no other implementation can read.

- A registry of ARP Divergence-Axis values, registration policy Specification
  Required, initially containing the descriptors enumerated in the Divergence
  Axis definition of {{terminology}}. Each entry MUST record whether the axis is
  register-attestable or server-recorded, a distinction eight normative sections
  depend on and which is otherwise carried only in prose. The designated expert
  MUST refuse a registration that does not state it.

- A registry of ARP Non-Answer Reasons, registration policy Specification
  Required, initially containing the values enumerated in {{no-answer}}. Each
  entry MUST record whether the reason is register-attested or server-observed,
  which determines whether a Non-Answer Statement signed by the register is
  required; the initial entries are recorded as {{no-answer}} states. A
  Non-Answer Reason is not a verdict; the designated expert MUST refuse a
  registration that could be combined by the Verdict Arithmetic, and MUST refuse
  a register-attested registration that does not state what the register signs
  over.

- A registry of ARP Subject Mapping Descriptors, registration policy
  Specification Required, initially containing `identity`, `profile-declared`
  and `agreement-declared`, defined in {{subject-mapping}}. A registration MUST
  specify a transformation that is a function of the Subject Identifier and of
  declared terms alone. The designated expert MUST refuse a registration whose
  transformation takes any input the reconciliation server chooses at
  reconciliation time, since a descriptor naming server discretion records that
  the discretion was exercised and not what it did.

- A registry of ARP Verification Outcomes, registration policy Specification
  Required, initially containing the values enumerated in
  {{verification-outcomes}}. A registration MUST name a condition a verifier can
  reach mechanically, and MUST state whether reaching it is evidence of
  equivocation by the serving party, evidence of a transport or encoding
  difference, or neither. The designated expert MUST refuse a registration that
  does not state which, because the distinction between an operator that
  equivocated and an artefact that was re-encoded in transit is the one this
  registry exists to carry.

- A registry of ARP Post-Seal Evaluation Qualifiers, registration policy
  Specification Required, initially containing `notarisation-incomplete` and
  `attribution-indeterminate`, defined in {{post-seal}}. A registration MUST
  identify a condition arising after a Reconciliation Output is sealed; the
  designated expert refuses a registration that qualifies a verdict, which
  belongs in the Divergence-Axis registry.

- A registry of ARP Register Data-Format Profile identifiers, registration policy
  Specification Required, initially containing `arp-profile-bods`,
  `arp-profile-corporate-org`, `arp-profile-customs-wco` and
  `arp-profile-sanctions-consolidated`, defined in {{format-profiles}}.
  Identifiers beginning `x-` are reserved for bilateral use and are not
  registered. A registration MUST state the dated vocabulary in which permitted
  predicates are expressed where it names one and state that it names none
  otherwise, the relation corresponding to taxonomic narrowing for
  each branch of its predicate space, and the parameters a Bilateral Register
  Agreement declaring it must supply. The designated expert refuses a
  registration that defines any means of transporting register records, that
  declares more than one parent relation applicable to a single predicate, that
  names a vocabulary without pinning its version, or that fixes in the profile a
  parameter varying between registers using the same format.

- A registry of ARP Aggregation-Method Descriptors, registration policy
  Specification Required, initially containing `hash-linkage-conjunction`,
  `hash-linkage-disjunction`, `hash-linkage-threshold-count` and
  `hash-linkage-source-class-quorum`: the aggregation mode of {{aggregation}}
  joined to the Verdict-Arithmetic operator it sequenced. A registration naming a
  new aggregation mode MUST specify that mode's construction; the descriptor is a
  signed Ledger field and a mode with no construction gives it no meaning.

- A registry of ARP Retroactive Evaluation Triggers, registration policy
  Specification Required, initially containing `pattern-library`,
  `policy-version`, `source-data-version`, `credential-revocation` and `register-record-correction`, defined in
  {{sweep-statements}}. A registration MUST name an event whose occurrence and
  time a party outside the reconciliation server can establish, or state plainly
  that it cannot, since the falsifiability of {{sweep-statements}} turns on it.

- A registry of ARP Override Grounds, registration policy Specification
  Required, initially containing `operational-continuity`,
  `pattern-false-positive` and `statutory-obligation`, defined for use in the
  Override Record of the Adversarial Pre-Transmission Test. A registration MUST
  state the circumstances in which the ground is available and MUST NOT admit a
  ground that could be asserted of every override, which would return the field
  to free text.

- A registry of ARP Re-Typing Grounds, registration policy Specification
  Required, initially containing `bounded-depth-not-closure`,
  `declared-not-determined`, `threshold-divergence` and `projection-broadened`,
  corresponding to the four grounds of {{verdict-retyping}}.

- A registry of ARP Verdict-Arithmetic operators, registration policy
  Specification Required, initially containing conjunction, disjunction,
  threshold-count and source-class-quorum, defined in {{verdict-arithmetic}}. A
  registration MUST state the operator's result as a total function of the
  multiset of contribution values and the operator's declared parameters, and
  MUST state whether it admits partial-match, on which {{verdict-retyping}}
  turns.

- A registry of ARP Ledger Entry Types, registration policy Specification
  Required, initially containing `reconciliation`,
  `continuation-notarisation`, `continuation-post-seal-record` and
  `continuation-supersession`, defined in {{settlement-ledger}}. Entry Type
  values are CBOR text strings. A registration MUST enumerate the fields an entry
  of that type carries in addition to the fields every entry carries, MUST state
  their order, since the Self-Entry Hash is taken over that order, and MUST state
  each field's value type and whether it is conditionally absent and on what
  condition. The designated expert MUST refuse a registration whose type
  restates a field already carried by the reconciliation entry it continues, and
  MUST refuse any type other than `reconciliation` that records a reconciliation
  rather than a fact arising after one was sealed.

  The initial registrations are those of {{settlement-ledger}}, with these value
  types. Every hash is a 32-octet CBOR byte string; every sequence number is a
  CBOR unsigned integer; every timestamp is a CBOR text string in the form of
  {{reconciliation-output}}; every Entry Type is a CBOR text string; the
  Addressed-Registers Identifier Set is a CBOR array of text strings, each an
  authority origin, sorted in bytewise lexicographic order of its UTF-8 encoding;
  the Aggregation-Method Descriptor and the Requester-Binding-Class Descriptor
  are CBOR text strings, the first drawn from the ARP
  Aggregation-Method Descriptors registry and the second from the four classes of
  the Requester Identity Binding and Agent Friend-or-Foe Gate section; the Override Indicator and the Material-Change Indicator are CBOR
  booleans; the Transparency Service Identifier is a CBOR text string carrying an
  authority origin; the EntryID is a CBOR text string as
  {{I-D.ietf-scitt-scrapi}} returns it; an HTTP status code is a CBOR unsigned
  integer; and every Entry Signature is a COSE_Sign1.

## Well-Known URIs {#iana-wellknown}

Seven entries are requested in the Well-Known URIs registry of {{RFC8615}}. For
each, the change controller is the IETF, the status is permanent, and the
specification document is this document.

| URI suffix | Defined in | Path syntax below the suffix |
|---|---|---|
| `arp-sealing-keys` | {{sealing-key-discovery}} | `/{kid}`, where `{kid}` is a JWK thumbprint, returns that single key |
| `arp-register-keys` | {{sealing-key-discovery}} | `/{kid}` as above |
| `arp-operator-keys` | the Adversarial Pre-Transmission Test | `/{kid}` as above |
| `arp-authorised-origins` | {{sealing-key-discovery}} | none |
| `arp-ledger-head` | {{settlement-ledger}} | none |
| `arp-policy-parameters` | {{read-signing}} | none |
| `arp-head-consistency` | {{head-consistency}} | none; served by a witness on the Authority Origin of its Operating-Party Identifier |

## Media types {#iana-media}

Twelve media types are requested, registered under the template of {{RFC6838}}.
For each: the type name is `application`; there are no required and no optional
parameters; the encoding considerations are binary, save for the `+json` type,
which is 8-bit UTF-8 text; the security and interoperability considerations are
those of this document; the published specification is this document; the
intended usage is COMMON; the change controller is the IETF; the applications
that use the type are ARP reconciliation servers, registers, regulators and
relying parties; there are no restrictions on usage; the author is the author of
this document and the contact address is the one on its front page; there are no
deprecated alias names, no magic numbers and no customary file extensions; and
fragment identifier considerations are those of the structured syntax suffix
where one applies -- Section 3.1 of {{RFC6839}} for `+json` -- and are otherwise
none, no fragment identifier syntax being defined for the `+cbor` and `+cose`
forms.

| Subtype | Carries | Defined in |
|---|---|---|
| `arp-reconciliation-request+cbor` | a request commissioning a reconciliation | {{request-binding}} |
| `arp-remediation-advisory+cbor` | a Remediation Advisory | the Adversarial Pre-Transmission Test |
| `arp-sovereign-re-notification+cose` | a Sovereign Re-Notification | {{re-notification}} |
| `arp-sealed-reconciliation-output+cose` | a Reconciliation Output under its Sealing Signature, whether delivered directly or nested in a SCITT Signed Statement | {{reconciliation-output}} |
| `arp-policy-parameters+cose` | a Policy Parameters Document | {{read-signing}} |
| `arp-post-seal-evaluation-record+cbor` | a Post-Seal Evaluation Record | {{post-seal}} |
| `arp-reconciliation-output+json` | the Verifiable Credentials JSON-LD form | {{vc-interop}} |
| `arp-ledger-head+cose` | a Ledger Head Statement | {{settlement-ledger}} |
| `arp-read-response+cose` | a signed read response | {{read-responses}} |
| `arp-evaluation-sweep+cose` | an Evaluation Sweep Statement | {{sweep-statements}} |
| `arp-key-set+cose` | a signed COSE Key Set or an Authorised-Origin Document | {{sealing-key-discovery}} |
| `arp-head-consistency+cose` | a Head Consistency Statement | {{head-consistency}} |
| `arp-probe-commitment+cose` | a Probe Commitment | {{coverage-probes}} |

# Acknowledgments

This document benefits from the SCITT Architecture {{RFC9943}}, the SCITT
Reference APIs {{I-D.ietf-scitt-scrapi}}, COSE Receipts
{{RFC9942}}, the RATS Architecture {{RFC9334}},
HTTP Message Signatures {{RFC9421}}, and the Web Bot Auth HTTP message
signature protocol {{I-D.meunier-webbotauth-httpsig-protocol}}.

Named findings, because a specification improved by review should say by whom.

Songbo Bu established that the indistinguishability requirement of
{{read-errors}} could not be satisfied as -02 stated it: the response profile of
{{read-responses}} binds each response to its request and its serving instant,
so two responses cannot be byte-equal, and a conformance rule demanding that
they be would fail every conforming implementation. The normalised observation
in {{read-errors}}, its enumeration of HTTP metadata and cache behaviour, and
the separation of the deterministic requirements from any statistical timing
claim are his design, contributed as an executable vector class.

Steven Mih established that the empty-result contradiction of {{read-responses}}
is conditional on the reader and any later observer having been served one
chain, and that under the fork {{settlement-ledger}} admits it may be
opportunistic to detect, an absence assertion can stand uncontradicted
indefinitely. The boundary now stated in {{read-responses}} is his finding.
He also confirmed, against three independent drafts, that the deterministic
encoding requirements relied on here are those of Section 4.2.1 of {{RFC8949}}
and not those of Section 9 of {{RFC9052}}.

Iman Schrock established, with Anton Sokolov, that a content digest cannot
serve as a correlation key across independently produced descriptions of one
act. He then established that the earlier repair was itself imprecise:
{{I-D.schrock-canonical-action-identifier}} declares required and optional
fields per action type and marks no field as a correlation key, so the
selection belongs to the profile. The requirements in
{{construction-distinctness}} to pin the action type and version, the selected
field and its normalisation and comparison rules, and to require that the
selected field be present in the Canonical Claim so that the Claim Hash commits
to it, are his, substantially as he drafted them.

Walter Hawkins established that the falsifiability condition of
{{read-responses}} is bounded by observer diversity rather than by any stronger
single-log property: head evidence obtained from the responding service cannot
bound a fork, because a fork at disjoint sequence numbers is invisible from a
single vantage by construction and the vantage is what is in question. Naming
the independent observer, and the ordering of witness countersignature over
independently anchored head digest, is his.

Tiago Pinto established that the obligation to answer with a signed response
carrying a log position belongs on the party making the claim rather than on
the party relying on it, and that an unsigned or position-less answer is to be
treated as the log not having answered. {{read-responses}} takes that shape at
his argument.

Tom Sato's leaf-construction work on Certificate Transparency logs informed
the inclusion-proof requirements of {{merkle-construction}}, and established
that a document defining a Merkle construction without stating its relationship
to Certificate Transparency leaves an implementer arriving from RFC 6962 unable
to tell whether the two agree.

Anton Sokolov established that a digest taken over a signed artefact as served
does not identify that artefact under a signature primitive whose encoding is
not byte-unique, and that ECDSA is such a primitive without violating SEC1,
FIPS 186-5 or {{RFC9053}}. {{signature-malleability}}, and the reconstruction of
the Prior-Entry Hash of {{settlement-ledger}}, the Post-Seal Evaluation Record
Hash of {{post-seal}} and the Merkle leaf of {{aggregation}} as Signing Input
Digests, follow from his measurement.

Henri Sirkkavaara established that a document may carry both the sound and the
unsound rule at once, each defensible on its own reading, and that the check is
therefore to sweep every identity rule in a tree rather than to correct the one
that was reported. Applied to this document it found that the Self-Entry Hash of
{{settlement-ledger}} already excluded the signature while the Prior-Entry Hash
two paragraphs below it did not.

Nenad Vasic established that an inclusion proof whose carried leaf is lifted
unchanged from another object's valid proof folds to the correct root under a
sibling array that verifies, so that a verifier walking the path before
recomputing the leaf accepts a proof bound to bytes it does not hold. The
requirement in {{leaf-binding}} that a verifier compute the leaf from the object
whose inclusion is being proved and use that value as the input to the sibling
walk is his, contributed as an executable vector against a
third-party corpus.

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

The Aggregation Subsystem operates in Hash-Linkage Aggregation. The Verdict
Arithmetic,
resolved from policy for the regimes the claim names, is disjunction. The
Combined Verdict is `no-match`.

The requester named itself and its compliance department's shared identity in the
Audience Set; no addressed register declared an audience constraint, so both are
admitted. The reliance interval that policy declares for `sanctions:` predicates
is seven days, so the Reliance Horizon is 2026-05-04T19:47:14Z. The Output is
sealed against the current Policy-Version Hash and returned to the requester in
the signed read response to the request that commissioned it, over which the
requester computes its Reconciliation Hash.

The Settlement-Layer Ledger entry comprises:

- Entry Sequence Number: 42
- Entry Type: `reconciliation`
- Claim Hash: <32 bytes>
- Reconciliation Hash: <32 bytes>
- Entry Timestamp: 2026-04-27T19:47:15Z
- Prior-Entry Hash: <32 bytes>
- Policy-Version Hash: <32 bytes>
- Addressed-Registers Identifier Set:
  `["https://register-a.example", "https://register-b.example",
  "https://register-c.example"]`
- Aggregation-Method Descriptor: `hash-linkage-disjunction`
- Merkle Root: <32 bytes>
- Requester-Binding-Class Descriptor: "human-operator"
- Reconciliation Timestamp: 2026-04-27T19:47:14Z
- Source-Reconciliation-Output Identifier: CBOR null -- this reconciliation
  supersedes none
- Override Indicator: false
- Self-Entry Hash: <32 bytes>
- Entry Signature: COSE_Sign1, Sealing-Key Identifier
  (`https://arp.example`, `example-sealing-2026-01`)

The one absent field occupies its position as CBOR null, so that the array's
length is fixed by the Entry Type and the Self-Entry Hash is taken over a
determinate encoding. When the sealed Output is registered with a
Transparency Service, the EntryID it returns is not written into entry 42, which
is already signed; it is appended as a later entry:

- Entry Sequence Number: 57
- Entry Type: `continuation-notarisation`
- Claim Hash: <the same 32 bytes as entry 42>
- Reconciliation Hash: <the same 32 bytes as entry 42>
- Entry Timestamp: 2026-04-27T19:52:03Z
- Prior-Entry Hash: <32 bytes>
- Transparency Service Identifier: `https://ts.example/`
- the notarisation outcome: `["entry-id", <the identifier that service returned>]`
- Self-Entry Hash: <32 bytes>
- Entry Signature: COSE_Sign1, Sealing-Key Identifier
  (`https://arp.example`, `example-sealing-2026-01`)

Entry 57 carries no Policy-Version Hash and no Addressed-Registers Identifier
Set; entry 42 records those and the shared Reconciliation Hash binds them. No
register record content is stored on the Ledger in either entry. Had the
registration neither completed nor been refused within the polling bound, entry
57 would not exist: the outcome would be a Post-Seal Evaluation Record qualified
`notarisation-incomplete`, pointed to by a `continuation-post-seal-record` entry,
and a later completion -- were the server able to learn of one, which
{{settlement-ledger}} records as an open question -- would be appended as a
`continuation-notarisation` entry later in the sequence. Had the service instead
refused registration terminally, the second field would read
`["refused", 400]`.

On 2026-05-06, two days past the Reliance Horizon, the compliance department
wishes to rely on the verdict again. Being an Audience Member it presents a
signed `GET /arp/continuations/{reconciliation-hash}`. The server answers `200`
with a signed response carrying the ledger head it was served against and, as its
result, entry 57 alone. That the result contains no `continuation-supersession`
entry is a signed statement by the server that as of that head there was none --
not merely the absence of one -- and the department retains it. Had it not been
an Audience Member the same request would have returned `404`, which is also what
it would have received had the Reconciliation Hash named nothing at all.

## Example: Retroactive Re-evaluation

Continuing the illustrative example above: six weeks after that
reconciliation, the list register-a.example consults adds the subject as part of a
new tranche. That register, on next invocation over the bilateral
channel its agreement declares, returns verdict `match`.

The Retroactive Evaluation Subsystem detects the new Source-Data Version the list
publisher issued, re-invokes Partial Attestations on the historical
reconciliations whose Per-Register Result Set carries a Source-Data Version
Identifier from the republished list, identifies the material verdict change, and emits a Sovereign
Re-Notification through the Regulator Portal to the regulators whose
statutory-regulator-access scope intersects the changed reconciliation.

It also emits an Evaluation Sweep Statement recording the trigger
`source-data-version`, the identifier of the list version that triggered it, the
policy state applied, the ledger head at the start and end of the sweep, the
Examined-Set Root over the Claim Hashes it examined, and the counts examined and
materially changed. The compliance department later presents that root and its
own Claim Hash to `GET /arp/sweeps/{examined-set-root}/inclusion/{claim-hash}`
and is shown that its reconciliation was in the set the server claims to have
examined. Had the server not run the sweep, there
would be no Statement covering a list republication whose date is public, and its
absence would itself be the finding.

The supersession is recorded from both ends. A new Reconciliation Output is
sealed against the current Policy-Version Hash and appended as a
`reconciliation` entry whose Source-Reconciliation-Output Identifier is the
Reconciliation Hash of the superseded Output. A `continuation-supersession`
entry is then appended against the superseded Output, carrying that Output's
Claim Hash and Reconciliation Hash, a Material-Change Indicator of true -- the
verdict moved from `no-match` to `match`, which is decisive-to-decisive and
therefore material -- the Superseding-Reconciliation Hash of the new Output, and
the Entry Sequence Number of the entry that records it.

The compliance department, an Audience Member of the original Output, presents
`GET /arp/continuations/{reconciliation-hash}` again. This time the signed
response carries the `continuation-supersession` entry. It reads the
Superseding-Reconciliation Hash, presents
`GET /arp/outputs/{superseding-reconciliation-hash}`, and is served the new
Output -- because a superseding Output inherits the Audience Set of the Output it
supersedes, so the party entitled to learn that its verdict changed is entitled
to see what it changed to. It verifies the new Sealing Signature, reads the
`match`, and acts.

Had the department retained the earlier signed empty response and the server now
denied that any supersession existed, the two signed statements by one key would
be irreconcilable, which is the point of signing them.

A party that is not an Audience Member -- one that was handed the Output by
someone who was -- reaches none of this. It may verify the Sealing Signature and
read the `no-match`, which is what makes an Output worth handing on, and it
obtains no read, learns of no supersession, and must not treat the verdict as
current. Entitlement follows the Audience Set, not the artefact.

## Example: Agentic Principal Reconciliation

An autonomous agent requests reconciliation of `sanctions:any-list-match`
over HTTP, signing the request under HTTP Message Signatures {{RFC9421}} with
a key published in a Web Bot Auth signature-agent card. The reconciliation
server verifies the signature (Agent Friend-or-Foe Determination: the agent
carries a verifiable identity). That establishes the class `agent-key-verified`
-- the key verified and the asserted principal is so far uncorroborated -- and
the Agent-IFF policy for the `sanctions:` class does not admit a decisive verdict
at that class.

The server therefore first performs an `agent:principal-binding-verifiable`
reconciliation with Subject Identifier set to the agent's key thumbprint and
Attested Value set to the asserted principal `org:ACME:operator:jdoe`,
addressing the ACME organisational directory register and the
credential-issuer status-list register. Both return `match`. The
Requester-Binding class is raised to `agent-verified` with accountable principal
`org:ACME:operator:jdoe`, committed to the Policy-Version Hash, and only then
is the sanctions reconciliation performed with a decisive verdict binding. Had
either identity register returned `no-match` with an attested
Divergence-Axis Field of `agent-impersonation-suspected`, the agent would have been classified ENEMY --
a contradicted binding is a stronger signal than an absent one -- and the
sanctions reconciliation refused or downgraded to advisory per policy.

The distinction is not bookkeeping. Under -02 both states were recorded as
`agent-verified`, so a relying party reading the Ledger entry for the first
reconciliation could not tell an agent whose principal had been corroborated
against two registers from one that had merely signed correctly.

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
diverge: the actual conduct exceeds the authorised scope. The Combined Verdict is `no-match`, and
`agent-action-scope-divergence` is recorded in the Server-Recorded
Divergence-Axis Set: it is a relation between two capsules and no single capsule
producer can attest it, on the same reasoning that makes `source-version-skew`
server-recorded.

Because the Agent-IFF policy for this action class requires a decisive `match`
before the action is treated as authorised, the divergent verdict is available
as a refusal at decision time -- the reconciliation surfaces the excess while
the action can still be refused, rather than after the consequence. The
Reconciliation Output is sealed against the Policy-Version Hash and written to
the Settlement-Layer Ledger without claim or register content, with
requester-binding class `agent-verified` -- the agent's asserted principal having
been corroborated as in the preceding example -- and no register or capsule
content disclosed.

# Composition with the SCITT Architecture {#composition-scitt}

The SCITT Architecture {{RFC9943}} provides notarisation of supply-chain
artefacts through a Transparency Service, which registers Signed Statements and
returns Receipts, yielding Transparent Statements. ARP composes with SCITT in
four ways:

1. SCITT receipts MAY be the input claim to ARP. A claim referencing a
   SCITT-anchored artefact (its hash and its registration receipt) is
   reconciled across registers without disclosing the underlying artefact.

2. ARP Reconciliation Outputs MAY be notarised into a SCITT Transparency
   Service as Transparent Statements, enabling SCITT-aware relying parties to
   verify the cross-sovereign reconciliation event in the same way they verify
   any other supply-chain claim. Registration and retrieval MAY use the SCITT
   Reference APIs {{I-D.ietf-scitt-scrapi}}. Notarisation does not enlarge the
   Audience Set of {{entitlement}}: what is registered is the sealed Output, and
   a party that retrieves it by EntryID holds it on the same terms as a party
   handed it directly.

3. The SCITT Architecture's Issuer role maps to the Bilateral Register Agreement
   structure: each Sovereign Register acts as a SCITT Issuer for a constrained
   predicate set. RFC 9943 defines no role for a party that combines statements
   from several Issuers, and this document does not claim one: the reconciliation
   server is an ARP role that acts as a SCITT Client toward the Transparency
   Service, registering its own Signed Statements.

4. ARP Hash-Linkage Aggregation MAY emit its Merkle commitment as COSE Receipts
   {{RFC9942}}, a compatible inclusion-proof encoding
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

{{I-D.mih-sato-agent-accountability-composition}} models accountable autonomous
action as four independently verifiable slots -- CAN, what the agent was
permitted to do; WHO, which human authorised it; WHAT the agent did; and AUDIT,
the runtime enforcement record -- each filled by a separately signed profile.
This document does not restate that model; the slot definitions, their semantics
and their composition rules are those of
{{I-D.mih-sato-agent-accountability-composition}}, and this appendix uses them as
defined there.

This appendix calls a filled slot a capsule. That is this document's term and not
that draft's, which speaks of slots and profiles; it is used here because ARP
admits each filled slot as a Partial-Attestation source and the word names the
signed unit rather than the position it occupies.

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

The agreement of this construction with a deployed {{RFC8785}} profile depends on
both parties having selected {{RFC8785}}, which the normative reference above
makes an obligation. {{I-D.mih-sato-agent-accountability-composition}} freezes a
conformance vector only once two independent implementations have recomputed it
and specifies no implementation, so no pinned corpus is cited here.

The capsules may disagree about the action -- that disagreement is the finding
ARP exists to surface -- but they do not disagree about which action is under
attestation, because they carry the same action serialisation. Each capsule's
own account travels in its payload, committed by its receipt-payload digest
below, not in `subject_digest`.

Two further profile-tagged digests, defined by this
document rather than by {{I-D.mih-sato-agent-accountability-composition}},
position each capsule for reconciliation: an authority-reference digest
committing to the authorising instrument (tagged transparency where it is the
Signing Input Digest of the COSE_Sign1 transparency receipt, an RFC 9942 receipt
being signed by the Transparency Service and so within
{{signature-malleability}}; or offline where it is the SHA-256 of the
{{RFC8785}} serialisation of an offline receipt payload, which carries no
signature), and a receipt-payload digest committing to the
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
produced at decision time and sealed to the Settlement-Layer Ledger without
claim or capsule content.

This composition is the agent-action specialisation of the mechanism ARP
applies to sovereign registers: reconcile heterogeneous authoritative outputs
over a shared subject into one deterministic verdict, disclose only verdict and
divergence, and seal against a Policy-Version Hash. It allows a relying party
to reconcile what an agent was permitted to do against what it did, at the
moment of action, across attestations no single party produced.

## The digest constructions are distinct {#construction-distinctness}

A third construction, the Signing Input Digest of {{terminology}}, identifies a
signed artefact by what was signed rather than by the envelope carrying it, and
is over deterministic CBOR rather than over a JSON serialisation. It is
distinct from both of the constructions below and from the Reconciliation Hash,
which is over a Reconciliation Output with each embedded register signature
replaced by its Signing Input Digest. Substituting any of these four for another
produces a value that verifies against nothing.

This document defines two digest constructions over a JSON serialisation, for two different
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
correlate two actions that a conforming implementation keeps apart. Neither case
needs measuring: both follow from the two constructions as this document defines
them, and either can be checked by computing the two digests over the four
inputs named above.

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
one act correlate. The action types, their required and optional members and
the reference issuer that minted the instances measured below are those of
{{I-D.schrock-canonical-action-identifier}}; the measurement is not
reproducible without it. Where an action type declares optional members, two
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
  permitted variation cannot enter it, or designate a typed field that the
  action type itself requires, and correlate on that. The second is the more
  robust of the two, because it does not require every producer to agree on a
  serialisation before they can agree that they are describing the same act.
  The selection is the profile's and not the registry's.
  {{I-D.schrock-canonical-action-identifier}} declares required and optional
  fields per action type; it does not mark any field as a correlation key, and
  a specification that says an action type "declares a material identifier"
  attributes to that registry a semantic it does not carry. A profile
  therefore MUST pin the action type and its version, the field it has
  selected for correlation, and that field's normalisation and comparison
  rules. The selected field MUST be present in the Canonical Claim, so that
  the Claim Hash commits to it and the join cannot be made on a value the
  reconciliation does not cover.

  Equality of the selected value identifies candidate descriptions only. It
  MUST NOT establish action equivalence, authorisation or execution.
  Exact-action agreement remains a separate comparison, under the
  subject-digest construction of {{composition}} or under the profile of
  {{I-D.schrock-canonical-action-identifier}}. Where the selected values match
  and the exact-action digests differ, that is a conflict to surface and not a
  failed join, and surfacing it is what reconciliation is for.

Three substitutions are forbidden, because each is available to an implementer
who has read only part of the foregoing and each fails silently.

* The designated join key MUST NOT be treated as the action's identity. The
  identity of an exact action is its content commitment; the join key is stable
  across the variation that commitment is required to detect, which is what
  makes it usable for correlation and useless for authorisation.
* A Claim Hash MUST NOT be treated as a cross-deployment identifier. It is a
  digest over a canonical serialisation preceded by the Deployment Blinding
  Value of {{sealing}}, so two deployments reconciling the same claim
  compute different Claim Hashes by construction, and equality of Claim Hashes
  across deployments is not a comparison that can be made at all.
* Equal join keys MUST NOT be taken to mean equal claims. Two reports sharing a
  designated join key have been asserted to describe one act; whether they
  agree about it is the question reconciliation exists to answer. Where their
  Claim Hashes differ, the difference is the finding, and a profile that
  collapsed them on the strength of the join key would report agreement it
  never established.

Stated positively, each object has one job: the designated field joins candidate
reports across permitted variation, the Claim Hash commits to the exact claim
under the deployment's blinding value, and the action type's own content
commitment remains what authorisation and execution bind to.

A specification that describes a content digest as a correlation key without
stating which of the two preceding cases it relies on invites an implementer to
assume a stability property the construction does not have. The resulting
failure is a correlation that silently does not occur.

# Document History

RFC Editor: please remove this section before publication.

## Since draft-hillier-scitt-arp-03

### Certificate Transparency, and the leaf a proof carries

{{merkle-construction}} now states its relationship to Certificate
Transparency, which -03 named only in its Acknowledgments while defining a
Merkle construction in its body. An implementer arriving from Certificate Transparency had
no way to tell from the text whether the two constructions agree. The finding is
Tom Sato's.

The relationship was established by executing both constructions rather than by
comparing their prose. The odd-node rule of {{merkle-construction}} and the
recursive split at the largest power of two below the leaf count of {{RFC9162}}
Section 2.1.1 produce identical roots for every leaf count from 1 to 4200, and
identical sibling arrays for all 131,328 leaf-count-and-index pairs up to 512
leaves. They diverge at one input in that whole range: the empty tree, where
this document gives thirty-two zero octets and Certificate Transparency gives
the hash of the empty string. That divergence is kept, and the section now says
why -- the Certificate Transparency value is a digest a verifier reproduces
successfully and may then treat as a root that commits to something, and
thirty-two zero octets is a value no commitment in this document produces.

The section also states what an implementation ported from a Certificate
Transparency log gets wrong if it is carried over unchanged: this document sorts
and deduplicates leaves where a log commits to submission order, and this
document's inclusion proof carries the leaf where the inclusion proof of
{{RFC9162}} Section 2.1.3 does not, carrying the index and the tree size as this
document does but assuming the verifier already holds the leaf. And it records
that the third convention in common use -- duplicating the last node at an odd
level -- agrees with this construction at **every leaf count that is a power of
two** and disagrees at every other, so a conformance vector taken at four or
eight leaves will not detect an implementation that ported it.

{{leaf-binding}} is new and is the security-relevant part. -03 defined the
inclusion proof as carrying the leaf and said nothing about where a verifier
should get the leaf it checks against. A proof whose carried leaf is lifted
unchanged from another object's valid proof folds to the correct root under a
sibling array that verifies, because it is a correct proof of the other object;
a verifier that walks the path first and trusts the carried leaf accepts it and
concludes that the object it holds was committed. Nothing in the walk depends on
the object, so no amount of path checking detects it. A verifier MUST now compute
the leaf from the object whose inclusion is being proved and use that value, and
no value taken from the proof, as the input to the walk. The requirement is
stated over the object rather than over the carried field because
{{aggregation}} permits COSE Receipts {{RFC9942}}, whose inclusion proof carries
no leaf, and a rule written only as a comparison against a carried leaf would be
vacuous under exactly the encoding a SCITT-aware verifier is most likely to use.
The finding is Nenad Vasic's, contributed as an executable vector against a
third-party corpus.

Two errors in the -03 text of {{merkle-construction}} are corrected. The
sibling-derivation rule said the verifier halves "the index and the level width"
as it ascends; the level width halves by **ceiling**, not by truncation, and an
implementation following the sentence literally computes the wrong width at
every leaf count that is not a power of two -- which is the entire range the
paragraph exists to pin down. And {{composition-scitt}} described COSE Receipts as
"the same inclusion-proof format", which they are not: an RFC 9942 inclusion
proof carries no leaf and is defined over the RFC 9162 tree whose empty root
this document rejects. {{aggregation}} also loses a stray duplicated clause.

### Every digest that identifies a signed artefact

{{signature-malleability}} is new, and five constructions changed with it. -03
took the Prior-Entry Hash of {{settlement-ledger}} over the whole preceding
entry including its Entry Signature, the Post-Seal Evaluation Record Hash of
{{post-seal}} over its record "in its entirety, signature included", the Merkle
leaf of {{aggregation}} over a canonical hash of a register-signed Partial
Attestation, and the tagged-transparency authority-reference digest of
{{composition}} over a COSE_Sign1 receipt. Those four are now Signing Input
Digests. The Reconciliation Hash of {{terminology}} is the fifth and took a
different repair, below.

The reason is a measurement. For ECDSA, `(r, s)` and `(r, n - s)` both verify
against the same key over the same message, and no specification prohibits it:
Section 4.1.4 of SEC1 v2.0 and Section 6.4.2 of FIPS 186-5 range-check `r` and
`s` only, and Section 2.1 of {{RFC9053}} constrains neither. Nothing is forged
and no authority is bypassed -- a party holding no key produces the second
encoding from the first, in transit. Over two hundred random P-256 keys, two
hundred substitutions verified and two hundred changed the entry bytes. The
finding is Anton Sokolov's.

**The Reconciliation Hash is where the repair nearly failed.** -03 defined it as
excluding the Sealing Signature, and an earlier draft of this section asserted
on that basis that it was already outside the signature and unchanged. It was
not. {{reconciliation-output}} embeds a register signature in each Query Binding
Record and in each Non-Answer Statement, so the preimage still carried a
signature after the sealing one was removed -- measured, stable in none of two
hundred trials. The Reconciliation Hash is a field of every Settlement-Layer
Ledger entry, hence inside the Entry Signature payload, hence inside the
Prior-Entry Hash: leaving it would have reintroduced at one remove exactly what
fixing the Prior-Entry Hash removed. It now replaces each embedded register
signature with that signature's Signing Input Digest.

That is the second instance in two days of this document carrying the sound rule
and the unsound one at once. The first was in a single bulleted list, where the
Self-Entry Hash nulled the signature position and the Prior-Entry Hash two
paragraphs below it did not. The instruction to sweep every identity rule in a
document rather than correct the one that was reported is Henri Sirkkavaara's,
from finding the same split in his own implementation on the same day, and the
Reconciliation Hash is what the second sweep found.

**Two things earlier revisions detected are no longer detectable**, and
{{settlement-ledger}} now says so rather than leaving it to be discovered.
Stripping a historical Entry Signature while leaving its protected header and
payload intact moves no Prior-Entry Hash, and neither does re-signing an entry
under the same key and header. A re-signature under a *different* key or
algorithm still moves the chain, because the `Sig_structure` covers the
protected header. The "signed exactly once" rule consequently has no
verifier-side test and is stated as an operator obligation an Audit Identity can
examine.

{{cbor-cose}} now requires every COSE_Sign1 this document defines to carry the
algorithm and key identifiers in its protected header and not in an unprotected
one. Nothing previously required it, while both {{terminology}}'s definition and
{{crypto-upgrade}}'s rotation argument assumed it -- and RFC 9052 permits `alg`
in the unprotected bucket, which a `Sig_structure` does not cover.
{{terminology}} also fixes the external additional authenticated data at the
zero-length byte string, because a Signing Input Digest a third party cannot
reproduce is not an identifier.

{{crypto-upgrade}} is rewritten where it rested on this. Its conclusion survives
and both its reason and its stated cost change. The chain holds because the
Prior-Entry Hash is over the signing input; and a verifier recomputing one takes
the protected header and payload byte strings verbatim and MUST NOT re-encode
them, which is *more* than -03 asked rather than less. -03 required copying
bytes and hashing them; -04 requires parsing a COSE_Sign1. That is the price of
a digest that does not move when the signature encoding does, and an earlier
draft of this section had the comparison backwards.

The consequence of the old constructions was a failure of verification rather
than of authenticity, which is the harder kind to diagnose. A reader served a
substituted entry concludes the chain is broken when the operator equivocated
about nothing; under {{leaf-binding}} it refuses a valid inclusion proof. A
deployment reporting either as detected tampering reports something that did not
happen.

{{RFC8032}} is added as an informative reference for Section 8.4 alone: EdDSA
puts the low-S check inside verification, so an attacker cannot derive a second
verifying byte-string, and a deployment declaring only EdDSA primitives under
item 2 of {{bra-items}} is not reachable by this. That is non-malleability and
not a claim that one byte-string alone can ever verify, since Section 5.1.7 of
{{RFC8032}} leaves cofactored verification optional. Nothing in this document
requires EdDSA, which is why the constructions and not the primitive choice are
where this is addressed.

### The Bilateral Register Agreement

{{bra}} is new. The Bilateral Register Agreement is what makes a register
addressable, and -03 defined it in a definition-list entry in
{{terminology}}: one paragraph enumerating twenty-six declared items and the
Agreement Hash construction over them. That is normative content with MUST-level
force, sited where a reader looks for a definition and not for a requirement,
and unreadable at the length it had reached. It is now a section, the
enumeration is numbered, and the numbering is what fixes the Agreement Hash
order.

Gathering it surfaced two obligations this document places on an Agreement
elsewhere and never enumerated here, so that neither was covered by the
Agreement Hash. {{read-responses}} obliges a deployment to declare a response
freshness tolerance; that is now item 26. {{read-signing}} obliges an Agreement
to declare the keys under which a regulator reads, and the
regulator-identity-provider trust anchor of item 5 is not a key; that is now
item 30. In both cases two deployments could agree on every item the Agreement
Hash committed to, differ on the term, and compute the same Agreement Hash --
an Agreement Hash that does not cover a term the Agreement is required to carry,
which is the class of defect this document exists to prevent. Item 31 makes the
re-invocation permission {{retroactive}} already conditions on a declared term
for the same reason.

{{bra-hash}} now fixes the CBOR type of every item and requires every set-valued
item to be sorted in bytewise lexicographic order of the deterministic CBOR
encoding of each element. Determinism under Section 4.2.1 of {{RFC8949}} fixes
how a given value is encoded and does not fix which type an item takes or how a
set is ordered, so -03's construction was not one two parties could
independently compute even with the item order settled. It also states that the
array has exactly thirty-three elements and that an absent, inapplicable or empty
item is encoded as CBOR null with the element still present, naming the four
items that may be absent -- -03 said only that an absent *optional* item was
null, while more than the one OPTIONAL item admits absence. Since {{agreement-drift}} suspends reconciliation on a deviating
Agreement Hash, each of these was an outage rather than a warning.

### The witness quorum

{{bra-witness}} specifies the witness quorum. -03 stated, in
{{read-responses}}, that a relying party acting on an empty result SHOULD hold
head-consistency evidence from at least one observer independent of the
responding service, and said in terms that it specified no quorum. The condition
was therefore normative while the thing that satisfies it was not. The finding
that this is bounded by observer diversity rather than by any stronger single-log
property is Walter Hawkins's, carried from -03.

An Agreement now declares a Witness Set and a Witness Quorum, both of which
enter the Agreement Hash. {{witness-entries}} gives a Witness Entry a form and
an Operating-Party Identifier with a stated normalisation, so that "distinct"
is a test a verifier computes rather than one it decides. The exclusion runs in
every direction -- a witness may not be operated by the responding service, by a
party controlling it, by a party it controls, or by a party under common control
-- because an exclusion running upward alone excludes nothing that matters: a
server that incorporates three subsidiaries satisfies a quorum of three while
controlling every observation in it.

{{head-consistency}} gives the Statement a payload, a media type and a
registered protected-header parameter, and carries a Witness Observation Time,
because a COSE_Sign1 is not dateable from its own bytes and a freshness rule
over an undateable artefact is a rule no verifier can apply.

{{quorum-rule}} requires that a Statement covering a **higher** head be
accompanied by the entries linking that head back to the one the response names,
verified by Prior-Entry Hash. A witness signature over a higher head is
otherwise evidence about whichever branch that witness was served, and a fork at
disjoint sequence numbers is precisely a pair of heads neither of which
contradicts the other; only the linkage puts the two observations on one chain.
It also measures the freshness window from the Statement Timestamp of the Ledger
Head Statement rather than from the head's own Entry Timestamp, and sets it at
two notarisation intervals, because {{settlement-ledger}} republishes once per
interval and a one-interval window measured from an entry's own timestamp closes
before any witness can see that entry.

{{witness-discovery}} puts the effective Witness Set and Quorum in the Policy
Parameters Document of {{read-signing}}. A relying party is party to no
Agreement and holds only Agreement Hashes, so a quorum declared solely inside an
Agreement is a test the party obliged to run it cannot read.

{{bra-limits}} states what none of this establishes. Operating-Party Identifiers
are declared and not proven; the exclusion is normative and the detection of a
false declaration is not provided for. A met quorum is proof that observer
diversity was declared, by a named party, in a term that party can be held to.

### The head-linkage projection

{{read-operations}} gains a `fields=linkage` projection returning the Entry
Sequence Number, Prior-Entry Hash, Self-Entry Hash and the Signing Input Digest
of the Entry Signature of one entry, entitled to
any requester whose signature verifies, because {{quorum-rule}} obliges a
relying party to link two heads and a relying party is entitled to no other read
that would let it. The fourth element was added after the projection was
specified with three: the chain condition of {{quorum-rule}} compares a
Prior-Entry Hash against the Signing Input Digest of the entry below, that
digest is taken over a `Sig_structure`, and neither the protected header nor the
payload of the entry below is recoverable from a triple of one sequence number
and two hashes. The condition was uncomputable by the only party required to
compute it, and the substitution a reader might have reached for instead is the
one the same section forbids. The projection is bounded at the head of the most recently
published Ledger Head Statement. Unbounded it would be a live head oracle --
the Ledger is contiguous, so a requester could binary-search the current head
between publications and poll it for the write rate, which is the disclosure
{{settlement-ledger}} publishes the head only once per notarisation interval to
prevent. {{read-errors}} states why a projection answering `200` where the full
read answers `404` is not an existence oracle, and what would make it one.

No timing claim is added by this revision and none is tested. {{read-errors}}
continues to state that response timing is a separate claim which an
implementation must either make with its measurement conditions published or not
make at all, and that making none is not non-conformance.

### Six adversarial passes, and what they found

The changes above were made in response to review. The changes below were made
in response to a sweep run against this document with the specific intent of
breaking it, from six directions at once, before anyone else did. They are
grouped by what they say about the document rather than by section, because the
grouping is the finding.

**Three sentences claiming rigour were the least rigorous sentences in the
document.**

{{sweep-statements}} said the falsifiability argument holds for three triggers
in four, "stated rather than rounded up". It held for one. Two of the three
rested on a transition array published by the reconciliation server, under its
own key, in a Policy Parameters Document with no publication time, no
notarisation and no chain, so a transition omitted from the array started no
clock and no party could date the Document well enough to show that it had been.
{{read-signing}} now gives that Document a Publication Timestamp, requires it to
be notarised on the ledger-head interval, and requires republication on that
interval whether or not its contents changed. The claim is now three in four and
is stated as conditional on that anchoring.

{{signature-malleability}} said "every digest in this document that identifies
or chains a signed artefact" and enumerated five. There were seven. The Override
Record of {{adversarial-test}} carries a COSE_Sign1 by the authorising operator
inside the Reconciliation Hash preimage, and the Evidentiary Provenance Manifest
of {{ingestion}} could carry one inside the Claim Hash preimage. The rule is now
stated over the class -- in any preimage this document defines, every signature
made by a party other than the one computing the digest is replaced by its
Signing Input Digest -- because an enumeration of carriers is correct only until
someone adds a field. The Manifest could not be repaired that way, its preimage
being {{RFC8785}} JSON with no byte-string type and its octets being the
requester's, so signed artefacts are now prohibited inside it and carried beside
it by digest.

{{bra-witness}} said two instances of one observer are not two observers and
tested distinctness on the Operating-Party Identifier alone. Two entries
declaring one key under two identifiers satisfied a quorum of two with a single
signature. {{quorum-rule}} now requires pairwise distinct Verification Method
References, which is a mechanical test, and states why that is different from
the declared-independence limit {{bra-limits}} concedes and cannot close.

**Two paths reached a decisive verdict out of nothing.** An empty
Addressed-Registers Identifier Set yielded `match` under conjunction: every
operator in {{verdict-arithmetic}} is a condition universally quantified over
the contributions, and both precedence rules began "where any", so at zero
contributions every guard was vacuously satisfied. A source class containing no
addressed register yielded a decisive `no-match`, which conjunction propagated.
Neither required an operator to misbehave. Both are now closed by explicit rules.

**Nothing bound the subject.** The transformation from the Canonical Claim's
Subject Identifier to the Subject Reference each register was asked about was
unrecorded, unconstrained and invisible to every party outside the
reconciliation server. Every signature could verify, every binding recompute,
the chain hold and the notarisation pass, while every register answered honestly
about a different person. {{subject-mapping}} adds a Subject Mapping Record
carrying the Subject Reference and a registered descriptor naming a
transformation that must be a function of the Subject Identifier and declared
terms alone.

**Evidence about a party was obtainable only from that party.** Head Consistency
Statements had an artefact, a quorum rule, a linkage chain and a freshness
window, and no channel. The obvious implementation has the responding service
supply them, which satisfies every stated condition and defeats the mechanism
entirely under exactly the fork it exists to detect. Witnesses now publish on
their own origins and a relying party MUST NOT accept one from the responding
service.

**Vocabulary that did not reach the output.** A verifier told to refuse a proof
had no way to record which of four refusals it made; {{verification-outcomes}}
adds them, and requires `same-act-distinct-encodings` to be tested before any
outcome that accuses a party of equivocation. One Non-Answer Reason carried five
distinct causes because four other sections directed implementations to it for
conditions its own definition never named; it is now five reasons.

**Claims a mechanism could not support.** The Reconstruction Proof of
{{audit-path}} had no pinned preimage, no wire representation, and compares one
value the audited server produced against another value the same server
produced under a key only it holds. The preimage and the wire form are now
fixed, and the stated limit is corrected: equality establishes self-consistency
across two reads and nothing else. The Examined-Set Root's counts were said not
to be bare assertions, which {{merkle-construction}} already contradicted; they
are assertions, made attributable and dated by the signature and the
notarisation and not made verifiable. The Regulator Portal audit trail was
called subpoena-grade with no sequence, chain, head or notarisation behind it,
and is now given all four.

**Things two implementers would encode differently.** A CBOR type table for the
Reconciliation Output; deterministic encoding stated for the Self-Entry Hash
preimage; `authority origin` defined as an Authority Origin against {{RFC6454}};
element types for the Query Binding preimage; a form for the Audience Member
Identifier; one canonical form for a key identifier and its two conversions; an
ordering rule, a form discriminator and an equality rule for the Source-Data
Version Identifier Set; an equality relation for the Witness Set intersection; a
member form for the fifth Divergence Axis; a subject key for the query budget; a
reference instant and direction for the freshness window; and the edges of the
Predicate Taxonomy the projection function walks.

**Things no implementer could satisfy.** The reproducibility requirement of
{{architecture}} was stated as identity in every field save an enumerated
carve-out, and three fields that are necessarily fresh were not in it. The
`fields=linkage` projection returned three values where the chain condition it
exists to serve needs four. The response freshness tolerance every reader must
apply was readable only by the parties who do not have to apply it. Suspension
under {{agreement-drift}} had no defined exit.

**Privacy.** {{privacy-6973}} takes the threats of {{RFC6973}} in turn and
states the residual rather than the mitigation where there is one, including
exclusion, which this protocol does not mitigate. {{privacy-erasure}} states the
one property that makes erasure implementable against an append-only record --
no personal data enters the Ledger, and no chain depends on the continued
existence of content that could be erased -- and prohibits notarising an Output
where that disclosure has not been accounted for.

**What was looked for and not found.** Several candidates did not survive
verification and no change was made for them: the Claim Hash's unverifiability
outside the deployment is already stated in two places; `notarisation-incomplete`
already distinguishes pending, refused and never-attempted; the register key
discovery root already has an encoding, a media type and a trust anchor; and the
containment requirement of {{containment}} is satisfiable, though its named
enforcement measure could not reach six fields the reconciliation server is
obliged to read, which is now stated.

### Five mechanisms taken from outside this field

The repairs above answer review. These four sections answer questions the
document could not previously answer at all, and each is a technique this field
has not used and another has.

**{{representation-invariance}} — every encoding defect is one defect.** A
signature with two byte forms, a CBOR item whose type is unfixed, a set with no
order, an optional member omitted or nulled, a URI normalised or not, NFC or
NFD, base64 or hex, transmitted bytes or a re-encoding. In each the information
is the same and the representation differs, and the digest was defined over the
representation. Physics has a name for a quantity that must not depend on a
choice carrying no information, and the discipline that goes with it is to
identify the freedom and quotient it out rather than to patch each place it
shows. The section names the eight representation classes this document
recognises, requires every new digest to state which class each preimage element
belongs to, and requires a conformance runner to exercise the **class** rather
than an enumeration of previously observed defects. A runner testing the two
ECDSA encodings it has heard of confirms what its author knew; a runner
enumerating the class finds the member nobody thought of.

**{{coverage-probes}} — an estimator where there is no proof.** The sweep
identity below closes the gap between the counts and the Ledger. Nothing closes
the gap between the Ledger and the world, because an operator that never wrote
an entry has nothing to be caught balancing, and that is the omission problem in
its general form. It has no proof and it has an estimator. An Audit Identity
publishes a commitment to a set of Claim Hashes it intends to commission, then
commissions them as ordinary reconciliations the server cannot distinguish, then
requests the inclusion proofs {{sweep-statements}} already obliges the server to
return. The recovery fraction estimates the proportion of eligible Outputs the
sweep actually examined, and the shortfall estimates the population that was
never written down. Astronomy injects sources of known brightness into an image
to measure what its pipeline missed; ecology releases marked individuals to
bound a population it cannot count. Both are estimating the same thing: what an
instrument failed to record, from a known signal passed through the same
instrument. A retroactive sweep is an instrument of that kind. The commitment
precedes the probes so that the denominator is fixed before the numerator is
knowable, which is what makes the fraction evidence rather than a selection.

**The sweep identity in {{sweep-statements}} — accounting rather than
signature.** The examined count and the materially-changed count were assertions
of the signing server. They are now required to balance against the Ledger: the
Examined-Range Set must be contiguous over the interval it claims, the examined
count must equal the number of `reconciliation` entries in it, and the
materially-changed count must equal the number of `continuation-supersession`
entries appended over the same interval. A signature makes an assertion
attributable; an identity makes it checkable against something the asserting
party does not solely control, which is what double-entry bookkeeping has done
for six centuries and what a conservation law does in physics.

**The Examined-Range Set — coverage needs a dense space.** A Merkle root over
Claim Hashes proves membership and cannot prove coverage, because Claim Hashes
are sparse in the digest space and a set commitment has no notion of what is
missing from it. Entry Sequence Numbers are dense and contiguous, so a gap in
them is visible. Committing to the same sweep in both spaces lets one artefact
answer both questions, and the choice of space is the whole of the trick.

**{{tradeoffs}} — locating the loss.** Several properties this document wants
cannot hold together, and a specification facing that can claim both and be
wrong somewhere a reader must find, weaken both and deliver neither, or choose
and say where the loss went. The section is the third, in one table. What makes
it useful is that the loss is located rather than distributed: a reader who
knows which property was surrendered and where can compensate, and a reader told
that everything holds cannot. Two rows that stood in earlier revisions have
already been retired by the mechanisms above, which is the other thing the table
turns out to be — a list of what to attack next.

### Mechanical

Anchors were added to sections that had none -- {{crypto-upgrade}},
{{cbor-cose}}, {{agreement-drift}} and {{post-quantum}} -- so that {{bra}} can
cite them. No heading text changed. Item 2 of {{bra-items}} cites
{{post-quantum}} for the post-quantum primitives a deployment has selected. {{RFC9162}} and {{RFC6962}} are added as
informative references: RFC 9162 obsoletes RFC 6962 and is the current
specification, and RFC 6962 is cited deliberately alongside it because it is the
version deployed Certificate Transparency logs implement, so naming only the
replacement would leave the reader who is actually at risk without the reference
they hold. Neither is normative -- the construction is fully specified here --
so no downref is introduced.

## Since draft-hillier-scitt-arp-02

This revision answers a review of -02 on the SCITT list. Of its five asks, three
are adopted as put, one is adopted in its goal and not in its mechanism, and one
is declined for now with a reason.

{{read-responses}} now names the evidence that bounds the empty-result
falsifiability condition. -02, and this revision as circulated for comment,
said that an empty result is falsifiable to the extent that the reader
"independently holds head-consistency evidence" for the served chain, without
saying independent of whom. Head evidence obtained from the responding service
bounds nothing, because a fork at disjoint sequence numbers is invisible from a
single vantage by construction and the vantage is what is in question. The
condition now names an observer independent of the responding service and
carries a `SHOULD` on the relying party, with witness countersignature over the
head preferred to an independently anchored head digest. The gap is not closed
and is not claimed to be; it is bounded by evidence an implementation can be
said to hold or not hold. The finding is Walter Hawkins's.

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
Verdict Arithmetic resolved under {{verdict-arithmetic}} is never displaced. A
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
identifiers and for Post-Seal Evaluation Qualifiers. -03 adds registries for
Ledger Entry Types, Override Grounds, Retroactive Evaluation Triggers and
Aggregation-Method Descriptors.
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

{{no-answer}} is new. A register may fail to answer in eleven distinct ways and no
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
was already declared its key. The Settlement-Layer Ledger gains the Claim Hash
and now exposes READ as well as APPEND -- the Regulator Portal, retroactive
evaluation and the chain-invariant check all require reads that "only APPEND"
forbade. Ledger entries are now signed, because prior-entry hashes prove that
nothing was removed from a chain and not that only one chain exists.

The Ledger now carries two kinds of entry under an Entry Type discriminator, and
each type's fields are enumerated. Facts arising after an Output is sealed --
the outcome of notarisation, a Post-Seal Evaluation Record, a supersession --
are recorded as Continuation entries appended against the Reconciliation Hash
they concern. An earlier revision of this text described Continuation entries
without giving them a form: they carried fields the entry list did not admit,
supplied none of the fields it made mandatory, and nothing distinguished one
kind from another. {{post-seal}} correspondingly no longer requires a Post-Seal
Evaluation Record Hash to be appended to an already-signed entry, which the
Ledger's absent UPDATE made impossible. Supersession is now recorded from both
ends, the superseding entry naming what it replaced and a Continuation entry
naming what replaced it, because neither pointer is reachable from the other's
starting point. A retriever of a Post-Seal Evaluation Record must now check the
retrieved bytes against the hash carried beside them, and that hash's
construction is defined. A supersession entry carries the superseding entry's
sequence number rather than a retrieval URI: obliging every reader to dereference
an operator-chosen URI before it could check anything would have been a forced
fetch, a de-blinding oracle and a covert channel no constraint on the URI's
content could close.

The Self-Entry Hash is defined, and is taken after the type-specific fields so
that it covers them. The Prior-Entry Hash is now taken over the whole preceding
entry including its Entry Signature. Chaining Self-Entry Hash to Self-Entry Hash
would have left every signature outside the structure that detects tampering,
which is a poor place for the field this document relies on to make a second
chain attributable. Entry encoding and field order are stated, because the
Self-Entry Hash is taken over them and a CBOR map would have been re-sorted by
key.

### Five things the protocol assumed and never stated

Working through the Ledger changes made it clear that a class of gap ran under
all of them. Every discovery path in -02 ended at a value its holder could not
present to anything, and each attempt to fix one by adding a pointer moved the
dead end without removing it. Five substrate layers were missing. They are now
written, and adding them closed more open items than any mechanism in this
revision.

**{{delivery}} states what the pipeline returns.** No earlier revision said that
a Reconciliation Output is delivered to anybody. The document specified in
detail how an Output is composed, sealed, digested, ledgered and notarised, and
never that any party receives one. Every discovery path begins with a party
holding a Reconciliation Hash; until now nothing said how it came to hold one.

**{{entitlement}} states who may hold an Output.** -02 made it a bearer
artefact: possession was the whole of the entitlement, it never expired, and
every read predicate the document attempted was expressed in terms of a
Requester-Binding the reader could not present and the Ledger could not
evaluate. An Output now carries a sealed Audience Set and a Reliance Horizon.
Entitlement follows the Audience Set rather than possession, which admits the
party the Requesting Principal named and excludes the party that merely came
into possession; a register may cap how wide an Audience Set addressing it may
be, because a register that attests about a subject is entitled to bound how far
that attestation travels. The Horizon bounds reliance without touching validity:
a sanctions `no-match` is a statement about lists that change daily, and an
artefact asserting one indefinitely was relied upon indefinitely.

**{{ledger-read}} states how a read is requested.** -02 and every draft of this
revision before it stated what a read returns and never the endpoint, the
request form, the response form, the media type, or the error semantics -- and
the two errors that matter most, "nothing exists" and "you may not ask", are the
two a reader most needs distinguished, because a server suppressing a
supersession returns what a server with nothing to report returns. There are
nine operations. Every response, success or error, is signed and carries the
ledger head it was served
against, so an empty result is an assertion rather than an absence, and a
supersession later found at an earlier sequence number is evidence against the
operator who signed the denial. Not-entitled and not-found are both `404` with
no distinguishing body, so no endpoint is an existence oracle. Reads are
rate-limited, because a surface whose every individual answer is innocuous
discloses entry count, write rate and retroactive-burst timing when swept.

With those in place, the Continuation entries of this revision are reachable by
the parties they were written for, a superseded Output's replacement is
retrievable because a superseding Output inherits the Audience Set of what it
supersedes, and the fork check reconciles two heads at different sequence
numbers through a signed consistency read rather than through an unsigned answer
from the party under suspicion. Retrieval URIs, which an earlier draft of this
revision put in Continuation entries, are gone: every artefact is now fetched by
hash from the origin that served the entry, so the Ledger holds no retrieval
address, no reader is obliged to dereference an operator-chosen URL before it can
check anything, and the covert channel that host selection and path structure
carried is closed.

The published ledger head is a signed statement carrying a sequence number, and
Entry Sequence Numbers are allocated in one sequence so that two conforming
stores cannot present the same number over different entries. Two limits are
stated rather than claimed away: an operator publishing to two audiences at
disjoint sequence numbers never emits a colliding pair, and a party holding
neither an Output nor an agreement cannot anchor the signing key.

The Reconciliation Hash is no longer among the values required to be reproducible
across runs. Its preimage includes the Reconciliation Timestamp, so the
requirement was unsatisfiable; the Reconciliation Identifier is the reproducible
index and always was.

**{{request-binding}} states how a reconciliation is commissioned.** The document
imposed obligations on "the response to the request that commissioned it" without
defining that request anywhere. **{{audit-path}} states who an auditor is.** Four
requirements were justified by what an auditor could reproduce, and the auditor
was not a party this document admitted; an Audit Identity is now declared in a
Bilateral Register Agreement, so that the audited party cannot choose its auditor
after the facts are known.

Several corrections follow from checking this document's claims about other
specifications against those specifications. The deterministic CBOR encoding
every digest here depends on is that of Section 4.2.1 of {{RFC8949}}, which is
now a normative reference; RFC 9052 narrows those requirements to COSE's own
signing structures and states no map-key ordering rule, so the previous citation
did not support what was built on it. {{RFC3339}}, {{RFC7638}}, {{RFC3986}} and
{{RFC6838}} are referenced rather than named in prose. {{composition-scitt}} no
longer attributes an Identity Manager or an Aggregator role to {{RFC9943}}, which
defines neither. {{composition}} no longer presents "capsule" as that draft's
term. An unsourced claim about agreement on twenty-two pinned conformance vectors
is removed, that draft having frozen none. The EU consolidated financial
sanctions list and the OFAC SDN list are retargeted at the resources that
actually publish them.

Three further sections follow from those. {{merkle-construction}} pins the tree
both Merkle roots in this document use, with domain separation and an inclusion-
proof encoding, so that a proof produced by one implementation verifies under
another. {{re-notification}} gives the Sovereign Re-Notification an artefact, a
payload, a media type, a delivery endpoint and a retry obligation; it was a MUST
with none of those in -02. {{privacy}} states the disclosure model and the
residual risks this revision accepts rather than leaving them to be inferred --
the subject has no standing in this protocol, an Audit Identity reads broadly,
and the published ledger head discloses a deployment's size at the notarisation
interval.

Every digest preimage and signature payload in the document is now pinned to a
CBOR array with a normative field order and null-substitution for absent fields:
the Reconciliation Output and its Sealing Signature, the Partial Attestation, the
Per-Register Claim Projection, the ledger entry, the Post-Seal Evaluation Record,
the Non-Answer Statement, the Ledger Head Statement, the Evaluation Sweep
Statement and the read response. -02 left several of them as "the canonical
serialisation of the foregoing", which is not a preimage two implementations can
agree on.

Homomorphic Aggregation Mode is removed and Hash-Linkage is the only mode. The
mode named no primitive, had no class in the Cryptographic-Primitive-Upgrade
Path for one to be declared in, and defined no encrypted-contribution structure;
and the reconciliation server must read every per-register verdict in the clear
in any case, to verify the register's signature, recompute the Query Binding,
check the echoed Policy-Version Hash and apply re-typing. The privacy property
the mode advertised was therefore not available under it, and ARP's actual
minimum-disclosure property -- controlled projection, and a Partial Attestation
payload that discloses of the subject only a verdict, a divergence axis, the
applied parameters and a digest -- is unaffected by its removal. Four
`homomorphic-*` Aggregation-Method Descriptors go with it.

The interface between the reconciliation server and a sovereign register is now
stated to be out of scope, and the claim that enumerating the Per-Register Claim
Projection lets two register operators build interoperable endpoints is
withdrawn. Enumerating a structure is not specifying a binding. That leg -- an
endpoint, a media type, and a COSE_Encrypt construction pinning the AEAD and its
authenticated additional data -- is the principal item this revision leaves for
the next.

### Ways the protocol could be gamed, closed

{{containment}}'s query budget is now measured per accountable principal per
subject. A budget shared across requesters is exhausted for everyone by any one
of them -- including an unidentified agent -- which forced every reconciliation
about that subject to `indeterminate` for the interval. The countermeasure was a
denial of service. Exhaustion now refuses the register and not the
reconciliation, which resolves a contradiction in -02: the old text refused the
reconciliation and then recorded a Non-Answer Reason in an Output that
consequently did not exist.

A register-attested Non-Answer Reason now requires a Non-Answer Statement signed
by that register over the projection values and the reason, and
{{no-answer}} records which reasons are register-attested and which are
server-observed. Without it a `register-refused` was an unattested assertion by
the party that transmitted the projection, and a server could suppress a `match`
by claiming the register had declined. A server can still downgrade a
reconciliation by asserting a server-observed reason and the document says so;
what it can no longer do is dress suppression as an act of the register.

{{sweep-statements}} is new. Every trigger of retroactive evaluation was
server-observed, every decision to run was the server's, and nothing recorded
that a sweep had happened -- so "we evaluated and found no change" and "we never
evaluated" were the same observation from outside. A signed Evaluation Sweep
Statement per sweep, notarised on the head interval, makes the absence of one an
assertion the operator has to make. A Source-Data Version publication is a public
event with a public timestamp; an operator with no Statement covering one has
not evaluated, which is now checkable.

The Verdict Arithmetic is resolved by the reconciliation server from policy,
keyed on the predicate and the regimes the requester names. -02 read as though
the requester declared the operator and its threshold in its own claim, which
would let it choose the verdict: disjunction over five registers and
threshold-count with a threshold of five differ only in which answer they return
over the same contributions. Naming a regime is a claim about which law applies
and the requester is accountable for it; selecting an operator is a determination
about how evidence combines, and the deployment makes it. `source-class-quorum`
now carries its per-class threshold into the Output as well as its partition,
without which it was as irreproducible as carrying neither.

The Requester-Binding gains a fourth class, `agent-key-verified`, for an agent
whose signing key verified but whose asserted principal was not corroborated.
-02 recorded key possession and principal binding as one fact. An agent that
signs correctly has shown it is the same agent as last time and not that any
accountable party stands behind it; recording that as `agent-verified`
overclaimed to every downstream reader and recording it as `agent-unverified`
discarded something real.

{{revocation-reliance}} states what revocation of a Verified Principal Credential
does and does not reach. It is not detected in the hot path and this document
does not pretend to put it there; what it does is bound the window, by requiring
an Audience Member to read continuations before relying past the Reliance
Horizon. Reliance years later on an Output whose principal was disowned the
following week is the case that matters, and -02 left it open.

The Override Record is enumerated, carries an Override Ground from a new
registry, and is signed by the authorising operator rather than by the server. A
record the server signs attests only that the server says an operator authorised
a bypass. It names that operator in the clear, which is consistent with
{{entitlement}}: blinding protects the published Ledger, and the Output is
confidential to its Audience Set.

Retroactive Evaluation now triggers on a new Source-Data Version. It previously
triggered only on a Pattern Library or Policy Version change, so a sanctions
list republication -- the case {{source-versioning}} was written for -- fired
nothing. A material change now includes a transition between decisive values: a
no-match becoming a match is the case the motivating domain cares most about,
and the earlier definition omitted it.

Homomorphic Aggregation Mode was restricted in -02 and is removed in -03; see
the -03 entry above.
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
  Agreement with a deployed profile depended on both parties having
  independently selected {{RFC8785}}. It is now an obligation rather than a
  coincidence.
- The Canonical Claim in {{terminology}} now pins its member-sort code unit to
  UTF-16, per Section 3.2.3 of {{RFC8785}}. -01 said "lexicographic sorting of
  object keys", which does not determine the ordering of member names outside
  the Basic Multilingual Plane.
- Number rendering now cites Section 3.2.2.3 of {{RFC8785}}. -01 cited
  "canonical JSON RFC 8259 number rendering"; RFC 8259 defines no
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
  the Claim Hash, Reconciliation Hash and Policy-Version Hash; -03 removes the
  Reconciliation Hash from that set, as the -03 entry above records. -01 required
  bit-for-bit identical Settlement-Layer Ledger entries, which the entry's own
  sequence number, timestamp and prior-entry hash make unsatisfiable.
- The Claim Hash is pinned to SHA-256 in Canonical Claim Ingestion. -01 named the
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
- Two independent implementations of an {{RFC8785}}-based digest construction,
  one in Go and one in Python and sharing no source, were measured as agreeing
  byte-for-byte on 24 generated inputs selected to exercise absent-field
  normalisation, arrays, string escaping, UTF-16 member sorting and both integer
  bounds. Two implementations derived from one source would have demonstrated
  code identity rather than agreement, which is why the pair is named. That is the
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
