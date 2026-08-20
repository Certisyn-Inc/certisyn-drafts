I have completed a full pass. Findings follow.

---

# AD / Gen-ART / SecDir Pre-Publication Review
**Document:** `draft-hillier-scitt-arp-04` (`/home/claude/arp/draft-hillier-scitt-arp.md`, 5801 lines)
**Intended status:** Standards Track (`category: std`), IETF stream, individual submission
**Reviewer posture:** would ballot **DISCUSS** with the points in §1–§5 below.

This is a technically serious document — far above the median individual submission. Almost every defect below is a *process/placement/reference-hygiene* defect rather than a protocol-design defect. But there are enough of them, and several are of a kind (unsatisfiable MUST, missing normative crypto references, normative dependence on individual I-Ds) that will hold publication.

---

## 1. RFC 2119 / RFC 8174 KEYWORDS

### 1.1 Boilerplate — CORRECT
L253–257 reproduces the RFC 8174 §2 boilerplate verbatim and correctly, including the "when, and only when, they appear in all capitals" clause and both BCP 14 citations. **No defect.** Abstract and Introduction contain zero keywords — correct.

### 1.2 DISCUSS — Two MUSTs that cannot both be satisfied (containment vs. the rest of the protocol)

L3929–3931 (`{{containment}}`, Security Considerations):
> "The service-operator entity **MUST NOT** be given access to any register record or any Partial-Attestation payload **beyond the verdict and divergence-axis fields**, and a deployment **MUST** enforce that by construction -- by encryption addressed to the requester or by an equivalent measure that no internal operator action can reverse -- rather than by policy."

This is contradicted by at least six normative requirements that oblige the reconciliation server to read *other* Partial-Attestation payload fields:

| Line | Requirement | Field it forces the server to read |
|---|---|---|
| 987 | "MUST be carried into the Projection Record" | Applied-Parameter Set |
| 1000–1001 | "MUST recompute the Query Binding ... MUST reject an attestation whose Query Binding does not match" | Query Binding |
| 903–905 | "MUST verify on reception that each Partial Attestation echoes it" | Policy-Version Hash |
| 1250–1252 | protected-header params "MUST equal the corresponding payload fields, and an implementation MUST reject an attestation where they differ" | BRA Hash, Policy-Version Hash |
| 1120–1128 | source-version comparison across registers | Source-Data Version Identifier Set |
| 1390–1392 | Merkle leaf = Signing Input Digest of the attestation | whole `Sig_structure` |

The stated enforcement mechanism ("encryption addressed to the requester") is **never specified anywhere in the document** — `{{per-register-encryption}}` (L1161–1195) specifies only the *outbound* projection encryption and is explicit that it covers "Each Per-Register Claim Projection". There is no return-path confidentiality construction. The MUST is therefore both contradicted and unimplementable. Additionally the actor, **"service-operator entity" (L3927, L3929), is used exactly twice in the document and is never defined** in `{{terminology}}`, so the subject of the prohibition is undefined.

### 1.3 DISCUSS — Three mutually inconsistent closed field lists for the Partial Attestation payload

Three normative statements each purport to close the set:

- L377–384 (`{{terminology}}`): "The Partial Attestation payload **SHALL** disclose, of the subject, **only** a Reconciliation-Verdict field, an OPTIONAL Divergence-Axis field, the applied parameters of {{format-profiles}} and the Query Binding". It then excuses only *two* further fields ("the Freshness Timestamp, and the Source-Data Version Identifier").
- L1257–1258 (`{{partial-attestation}}`): "The Partial Attestation payload **SHALL NOT** contain ... any field beyond those enumerated" — where the enumeration at L1200–1218 carries **eight** fields, including **Register Identifier, Bilateral-Register-Agreement Hash and Policy-Version Hash**, which appear in *neither* the terminology "only" list nor its two-item excuse clause.
- L3929 (`{{containment}}`): "beyond the verdict and divergence-axis fields" — narrower than both.

Three closed sets, three different cardinalities. An implementer cannot determine which SHALL governs.

### 1.4 DISCUSS — Two contradictory MUSTs inside one paragraph (`{{bra-hash}}`, L3104–3112)

> L3104: "An item that is **absent, inapplicable or empty** is encoded as CBOR null, and the element is present in the array regardless."
> L3109–3110: "Every other item **MUST** be present and **MUST NOT** be null."

Items 1, 2, 21, 27, 30 are set-valued (L3076: "array, sorted in bytewise lexicographic order"). Item 7 (L3082) carries "per-jurisdiction permitted-read-field and permitted-read-predicate sets", which may legitimately be empty for a deployment with no regulator jurisdictions declared. Item 21 requires "At least one Audit Identity" so is non-empty; but item 30's "means by which key material ... is retrieved" and item 7's per-jurisdiction sets can be empty. The first sentence says empty → null; the last says MUST NOT be null. The two cannot both hold, and by the document's own reasoning at L3111–3112 the disagreement produces different Agreement Hashes — which `{{agreement-drift}}` (L4070–4072) converts into a **suspension of reconciliation**, i.e. an outage.

### 1.5 DISCUSS — Requirements whose subject is a contract, not a protocol party

`{{bra-items}}` L2798 and the 31 numbered items impose "Each Bilateral Register Agreement **MUST** declare ..." — 31 normative requirements on a negotiated commercial instrument. Similar constructions occur at L923–925, L972–973, L997–998, L1067–1068, L1091–1093, L2745, L3816, L4092–4093. Roughly a quarter of this document's normative weight falls on out-of-band contracts rather than on implementations or on the wire, and none of it is testable by any interoperability criterion. This is the single largest structural objection an AD will raise about Standards Track suitability (see also §6.3 below).

### 1.6 COMMENT — MUSTs with no actor (passive / pronominal subject)

| Line | Text | Problem |
|---|---|---|
| 1953 | "It **MUST** be reconstructible under audit from that array" | reconstructible *by whom*; obligation *on whom* |
| 1857 | "Absence **MUST** be encoded and **MUST NOT** be expressed by a shorter array" | no actor |
| 1146 | "Both **MUST** trigger" | subject is a condition, not a party |
| 1127 | "It **MUST** be carried into the Per-Register Result Set" | no actor |
| 632–634 | "**the system MUST** produce Reconciliation Outputs identical in every field" | "the system" is not a protocol role defined anywhere |
| 943 | "Identifiers beginning `x-` are reserved for bilateral use and **MUST NOT** be registered" | addressed to IANA/future registrants inside the protocol body; and see §4.6 |
| 4228 | "Each **MUST** appear in a protected header and **MUST NOT** appear in an unprotected one" | normative requirement located in IANA Considerations |
| 3826 | "It **MUST** be signed under a key served as a COSE Key Set at ..." | referent of "It" is two sentences away |

### 1.7 COMMENT — lowercase keywords where a keyword was plainly intended

| Line | Text | Should be |
|---|---|---|
| 286 | "Statements a relying party **must** hold before the evidence condition of {{read-responses}} is satisfied" | The referenced condition at L3535 is a **SHOULD** ("A relying party acting on an empty result SHOULD hold head-consistency evidence"). The definition is *stronger* than the requirement it points at. Genuine inconsistency, not just case. |
| 722–723 | "A relying party that requires an attributable principal **should** treat `agent-key-verified` as it treats `agent-unverified`" | SHOULD, or explicitly disclaim (the next sentence does disclaim — but then the "should" is misleading) |
| 2606 | "the party being audited **must not** choose its auditor after the facts are known" | MUST NOT |
| 2076 | "Contiguity **is required** because ..." | MUST |
| 2339 | "an Audience Member's verification method **is required**" | MUST |
| 2030 | "**should** be over the artefact as served under {{ledger-read}}" | SHOULD |
| 3683, 4201 | "a deployment for which that is the wrong disclosure **should not** notarise" | SHOULD NOT |
| 4033 | "A deployment concerned with either channel **should** bound it contractually" | SHOULD (in Security Considerations — see §2) |
| 4195 | "a deployment operating where subject rights attach **should** provide for them outside this document" | SHOULD |

### 1.8 COMMENT — "may not" (ambiguous between prohibition and possibility)

- L1572: "a decisive negative **may not** be built on one" — in `{{verdict-arithmetic}}`, a normative section. Reads as prohibition; should be MUST NOT.
- L3106: "**Items 14, 25, 27 and 29 are the only items that may be absent**" — bold, not a keyword.
- L5180: "a witness **may not** be operated by the responding service" (Document History).

### 1.9 NIT — RFC 2119 keywords used as data-model annotations rather than requirements

`OPTIONAL` is used ~20 times as a field-presence marker in enumerations (L1206, L1209, L1629, L1674–1676, L903, L2183, L2809). In the *same* enumerations, presence is also expressed as "present exactly where ..." (L1629, L1664–1670) and once as lowercase "required" (L1679: "required wherever a projection was transmitted"). Three notations for one concept in one bulleted list. Likewise `REQUIRED` is used to mean "this query parameter is mandatory" (L3396, L3441, L3446) rather than as a requirement on an implementer.

### 1.10 NIT — All-caps non-keywords adjacent to keyword text

`INTERSECTION` (L2486), `RETURNS` (L2496), `EXCEPT` (L2580), `LONGEST` (L1900), `SHORTEST` (L1911), `ANY` (L1516), `SAME` (L4862, L4902), `CONTENT` (L4849), `COLLISION` (L4860), `TYPED` (L4886), `AND` (L708), `NOT` (103 occurrences, many not part of MUST NOT / SHALL NOT / NOT RECOMMENDED — e.g. L4838 "they are **NOT** interchangeable", L4763 "it is **NOT** a correlation key"). RFC 8174 makes all-caps the *signal* for normativity; using all-caps for ordinary emphasis directly next to keywords invites misreading. `FRIENDLY`/`ENEMY` are defined terms in all caps and are less objectionable but should be flagged for the RFC Editor.

### 1.11 NIT — normative weight carried by markdown bold, which is lost in the .txt rendering

L3063–3064 "**exactly thirty-one elements**"; L3078 "**in the declared preference order and not sorted**"; L3105–3106 "**Items 14, 25, 27 and 29 are the only items that may be absent**"; L2135 "**Two things earlier revisions detected are no longer detectable**"; L2877 "**An Agreement computed under an earlier revision does not compute the same Agreement Hash under this one.**"; L3418–3419 "**and only for an Entry Sequence Number at or below the head...**". In the canonical .txt output the emphasis disappears and these read as ordinary prose.

---

## 2. NORMATIVE LANGUAGE IN THE WRONG SECTION

This is the reported defect and it is confirmed and worse than reported: normative text is anchored in **Security Considerations, IANA Considerations, the Terminology section, and four appendices** simultaneously.

### 2.1 DISCUSS — Section 7 (Security Considerations) carries 31 normative keyword instances

Security Considerations is conventionally non-normative. Complete inventory:

| Line | Subsection | Requirement |
|---|---|---|
| 3929 | `{{containment}}` | "service-operator entity **MUST NOT** be given access to any register record or any Partial-Attestation payload" |
| 3930 | `{{containment}}` | "a deployment **MUST** enforce that by construction" |
| 3939 | `{{containment}}` | "That property is per-event and **MUST NOT** be read as a property of the system under repeated querying" |
| 3949–3951 | `{{containment}}` | "A deployment **MUST** therefore declare in each Bilateral Register Agreement a query budget ... and the budget **MUST** be measured per accountable principal per subject" |
| 3966–3967 | `{{containment}}` | "the budget **MUST** be keyed on the verified signing key where one exists" |
| 3973–3975 | `{{containment}}` | "**MAY** additionally declare a per-subject ceiling ... where a deployment declares one it **MUST** partition it" |
| 3989–3991 | `{{containment}}` | "the reconciliation server **MUST NOT** transmit a projection ... and **MUST** record `query-budget-exhausted`" |
| 3998–4000 | `{{containment}}` | "The Pattern Library **MUST** include a repeated-narrowing pattern" |
| 4004 | `{{containment}}` | "the Per-Register Claim Projection **MUST** carry the Requester-Binding Class" |
| 4041–4045 | Pattern-Library Integrity | "**MUST** be bound to a Pattern-Library Commitment Hash"; "**MUST** produce a new Pattern-Library Version Identifier"; "**MUST** be re-executed" |
| 4050–4055 | `{{agent-iff-integrity}}` | "determination **MUST** default to ENEMY"; "**MUST** all yield an ENEMY classification"; "The server **MUST NOT** infer friendliness from network origin, User-Agent string, or any self-asserted identifier" |
| 4057–4060 | `{{agent-iff-integrity}}` | "the resulting Reconciliation Output **MUST NOT** carry a decisive verdict binding, and the Settlement-Layer Ledger entry **MUST** record the requester-binding class" |
| 4071–4072 | `{{agreement-drift}}` | "Reconciliation **MUST** be suspended for an addressed register whose Agreement Hash deviates" |
| 4076–4084 | `{{replay-defence}}` | five MUSTs: "**MUST** carry a Freshness Timestamp"; "**MUST** verify the Freshness Timestamp"; "**MUST** be rejected"; "the rejection **MUST** be recorded"; "**MUST** additionally carry a nonce and created/expires parameter set" |
| 4089–4093 | `{{post-quantum}}` | "ML-KEM-1024 is **RECOMMENDED**"; "ML-DSA-65 is **RECOMMENDED**"; "Implementations **MUST** declare their chosen post-quantum primitives" |
| 4100–4103 | `{{side-channel}}` | "Implementations **MUST NOT** use narrowing patterns to fingerprint individual subjects"; "The Predicate Taxonomy **SHOULD** be designed such that ..." |

Several of these are load-bearing and referenced normatively from the body: `{{containment}}` is cited from L903 (`{{projection}}` OPTIONAL field condition), L1419–1423 (`{{no-answer}}` reason definitions), L2839 (BRA item 23), L2828–2830 (BRA items 13/14), L2853 (item 25). `{{agent-iff-integrity}}` is cited from the **Introduction** (L228: "the normative rules are in {{terminology}} and {{agent-iff-integrity}}"). `{{replay-defence}}` is cited from L1420. A reader following the Introduction's own pointer is sent to Security Considerations to find "the normative rules".

**Remedy the AD will ask for:** move the query-budget, IFF-default-ENEMY, pattern-library-integrity, agreement-drift, replay-defence and post-quantum requirements into numbered protocol sections, and leave §7 with the threat analysis and the (excellent) `{{budget-suppression}}` and `{{signature-malleability}}` narratives, which are correctly non-normative.

### 2.2 DISCUSS — Section 9 (IANA Considerations) carries 20 normative keyword instances

L4227–4229 is a protocol requirement, not a registration instruction:
> "Each **MUST** appear in a protected header and **MUST NOT** appear in an unprotected one: every one of them is a commitment a verifier relies on"

This duplicates and partially conflicts with `{{cbor-cose}}` L3202–3204, which imposes the protected-header rule only on `alg` (label 1) and `kid` (label 4). L4240–4241 ("{{sealing-key-discovery}} requires both on every key it publishes") likewise restates a body requirement. The remaining ~16 MUSTs (L4245, L4249, L4253–4257, L4262, L4270–4278, L4287, L4293, L4297–4299, L4308–4310, L4315–4321) are **designated-expert instructions**, which *are* correctly located in IANA Considerations per RFC 8126 §4.6 — no defect for those.

### 2.3 DISCUSS — Section 3 (Conventions and Definitions) carries 24 normative keyword instances

A definitions section should define terms, not impose requirements. Present:

- L274–276: "{{bra}} enumerates the items an Agreement **MUST** declare" (restatement — acceptable)
- L342: "A member whose value is absent **is omitted**" — the five-step canonicalisation at L336–346 is fully normative and is the single most implementation-critical algorithm in the document, sitting in a definition list.
- L356–357: "The two **MUST NOT** be substituted for one another; see {{construction-distinctness}}" — a MUST NOT in the terminology section whose *definition* lives in an **appendix** (see §2.4).
- L370–371: "Where the taxonomy admits more than one such ancestor, the projection **MUST** fail rather than choose" — duplicated at L849–851 in `{{projection}}`.
- L377–380: the Partial Attestation **SHALL / SHALL NOT** discussed in §1.3.
- L432–433: "an implementation **MUST NOT** supply another value"; L435: "**MUST NOT** be re-encoded" (Signing Input Digest definition — normative construction in a glossary)
- L536: "A profile registered under {{format-profiles}} **MUST** state which of its predicates are threshold-sensitive"
- L563: "an implementation **MUST NOT** treat it as one" (Source-Version Skew)
- L586–587: "An Audience Member **MUST NOT** treat a Combined Verdict as current without ..." (Reliance Horizon)

### 2.4 DISCUSS — Normative requirements in appendices that the normative body depends on

`--- back` is at L4475. Everything from L4477 is an appendix. The following appendices carry MUST/MUST NOT:

| Line | Appendix | Requirement |
|---|---|---|
| 4762–4763 | `{{composition}}` | "All capsules composed under this appendix **MUST** be computed over that same serialised action object" |
| 4765–4766 | `{{composition}}` | "it is **NOT** a correlation key ... and **MUST NOT** be used as one" |
| 4769–4771 | `{{composition}}` | "An attester that re-serialises its own account of the action **MUST NOT** compute `subject_digest` over that account; it **MUST** carry the serialisation it received" |
| 4873–4874 | `{{construction-distinctness}}` | "An implementation **MUST NOT** use the Claim Hash construction where `subject_digest` is specified, or the reverse" |
| 4875–4884 | `{{construction-distinctness}}` | "the producer **MUST** identify the construction used, by an identifier that commits to the declared canonicalisation parameters ... Such an identifier **MUST NOT** commit to facts about a specification that do not affect the serialised bytes" |
| 4886–4894 | `{{construction-distinctness}}` | "the producer **MUST** validate the object against a pinned definition of that type before emitting a correlation identifier ... and **MUST NOT** emit one where validation fails" |
| 4896–4980 | `{{subject-digest-scope}}` | 3 MUST, 5 MUST NOT, 1 MAY, 1 OPTIONAL |
| 4855 | `{{construction-distinctness}}` | "An implementation that substitutes one for the other **MUST** be assumed to produce incorrect correlations" — a MUST addressed to a reader's epistemic state, which is not a protocol behaviour at all |

`{{terminology}}` L356–357 sends the reader to `{{construction-distinctness}}` for a normative rule. `{{signature-malleability}}` L4159 cites "the authority-reference digest of {{composition}}" as one of the digests the *body's* Signing Input Digest rule governs. So the appendix is inside the normative dependency graph.

Worse: **L4875–4881 imposes a MUST to emit "an identifier that commits to the declared canonicalisation parameters" but defines no identifier syntax, no value space, and requests no IANA registry for it.** That requirement is unimplementable as written.

### 2.5 COMMENT — Document History appendix (L4981–5801) carries normative keywords

820 lines — 14% of the document — of change log containing 4 MUST, 2 MUST NOT, 2 MAY, 2 SHOULD, 2 OPTIONAL (L5041–5042, L5098–5109, L5149, L5166–5180, L5245–5303, L5420–5482, L5639–5732). There is **no "RFC Editor: remove this section" instruction on it** — only §1 (L156–158) carries one.

### 2.6 NIT — Examples appendix is clean
L4477–4681 contains no all-caps keywords (verified). L4479–4481 correctly self-labels: "This example is illustrative and non-normative". Good practice; the only blemish is lowercase "must not" at L4619 and the "-02" reference at L4646.

---

## 3. REFERENCES

### 3.1 DISCUSS — Normative MUSTs expressed in terms of **informative individual Internet-Drafts**

`{{http-sig}}` L3268–3276:
> "the request **MUST** be signed under HTTP Message Signatures {{RFC9421}}, with the signature-agent key resolvable through a Web Bot Auth signature-agent card **{{I-D.meunier-webbotauth-registry}}**, advertised via the Signature-Agent header **{{I-D.meunier-webbotauth-httpsig-protocol}}** and resolved through the HTTP Message Signatures directory it names **{{I-D.meunier-webbotauth-httpsig-directory}}**."

Same construction at L737–745 (`MUST` classify FRIENDLY / `MUST` classify ENEMY) and in the `Requesting Agent` definition at L308–312. The Agent Friend-or-Foe Determination — the fourth of the four problems the Introduction says this protocol exists to solve (L219–228) — **cannot be implemented without all three of these documents.** They are declared **informative** (L96–98).

Three consequences:
1. They must be reclassified normative, at which point the document acquires a normative reference to three **individual (non-WG) Internet-Drafts**, producing an indefinite MISSREF hold. There is no Note to the RFC Editor covering them (the note at L172–183 covers only `I-D.ietf-scitt-scrapi`).
2. Alternatively the FRIENDLY/ENEMY MUSTs must be rewritten abstractly (e.g. "a verifiable agent identity as defined by an applicable profile") with Web Bot Auth as one named example.
3. `I-D.meunier-webbotauth-registry` is also cited from the definition of `agent-unverified` (L714–717: "signed under a bare key that resolves to no signature-agent card"), which is one of the four values of a **signed Settlement-Layer Ledger field** (L2179–2180). The Ledger's semantics thus depend on an informative individual draft.

### 3.2 DISCUSS — `RECOMMENDED` (a BCP 14 keyword) applied to informative references

L4089–4091 (`{{post-quantum}}`):
> "ML-KEM-1024 **{{FIPS203}}** is **RECOMMENDED** for the claim-encryption primitive class. ML-DSA-65 **{{FIPS204}}** is **RECOMMENDED** for the partial-attestation-signature and sealing-signature primitive classes."

and L2748–2751 (`{{crypto-upgrade}}`, normative body):
> "The equivalence list **MUST** include at least one post-quantum primitive for each class, **drawn from a set including ML-KEM {{FIPS203}} ... and ML-DSA {{FIPS204}}**"

`FIPS203` and `FIPS204` are declared **informative** (L106–117). A RECOMMENDED algorithm and a MUST-include set are not implementable without the specifications. Both must move to normative. (Neither is an IETF-stream document so RFC 8067 downref procedure does not apply, but the IESG reviews non-IETF normative references and both will need stable, dated citations — which they have.)

### 3.3 DISCUSS — Missing references entirely (documents cited by section number, or algorithms mandated, with no reference entry)

| Line(s) | Cited / mandated | Reference entry |
|---|---|---|
| 4114–4115, 5059 | "Section 4.1.4 of **SEC1 v2.0**"; "Section 6.4.2 of **FIPS 186-5**"; and L4453 "without violating SEC1, FIPS 186-5" | **none** — cited by section number in Security Considerations and Acknowledgments |
| 21 occurrences (L347, L419, L426, L1276–1277, L1479, L1935, L2093, L2581, L4842, L4848, …) | **SHA-256** — the mandatory-to-implement hash for every digest in the protocol | **none** — no FIPS 180-4, no RFC 6234 |
| L2581 | "**HMAC-SHA-256** under the Deployment Blinding Value" | **none** — no RFC 2104, no FIPS 198-1 |
| L3289, L3319 | "**base64url**-encoded without padding"; "base64url-encoded" (padding unstated the second time) | **none** — no RFC 4648 §5 |
| L3287 | "Requests are HTTP over **TLS**" | **none** — no RFC 8446, no version floor, and the sentence is declarative rather than normative |
| throughout `{{ledger-read}}` | HTTP methods, `200`/`401`/`403`/`404`/`422`/`429`, `Cache-Control: no-store` (L3592) | **none** — no RFC 9110, no RFC 9111 |
| L5660 | "canonical JSON **RFC 8259** number rendering" | **none** (Document History only — lower severity) |

A Standards Track document that mandates SHA-256, HMAC-SHA-256, base64url, TLS and HTTP without citing any of them will not clear the RFC Editor, let alone IESG evaluation.

### 3.4 DISCUSS — The register data-format vocabularies are misclassified

L935–938 invents a reference category that does not exist:
> "The vocabulary documents a profile names are **informative to this document and normative to an implementation of that profile**: an implementation cannot evaluate a projection expressed in a vocabulary without it."

But **this document defines the four profiles itself** (L943–948, and §§4.6.1–4.6.4). Its own normative text is written in those vocabularies:

- L1008–1009: "A profile in this class **MUST** declare **{{W3C-ORG}}** for any branch of its predicate space over which taxonomic narrowing is defined."
- L1009–1013: "**{{RFC6350}}** expresses organisational hierarchy only within one organisation's own `ORG` structured value ... so a vCard-only profile ... **MUST NOT** declare a narrowing branch."
- L1026–1028: "`org:subOrganizationOf` is the parent relation for the organisational-structure branch, and `org:hasSite` for the branch of predicates ranging over establishment or place of business."
- L959–961, L972–986: MUSTs over **{{BODS}}** relationship records; "This profile is written against **BODS 0.4**."
- L1066–1069: "The vocabulary is pinned to **Version 4** of the **{{WCO-DM}}** and to the **{{UNCEFACT}}** Core Component Library release the Bilateral Register Agreement names".

`BODS`, `W3C-ORG`, `RFC6350`, `WCO-DM`, `UNCEFACT` are all declared **informative** (L60, L64–95). Each is required to implement a normative MUST in this document. RFC 3967/8067 recognise no "normative to an implementation of that profile" category.

Compounding: the reference entries **do not carry the versions the body pins**. Front matter `BODS` has `date: 2024` and no version, while L961 pins "BODS 0.4". `WCO-DM` has `date: 2024` and no version, while L1066 pins "Version 4". `UNCEFACT` is unversioned and the body defers versioning to a bilateral contract (L1067–1069) — a normative reference whose version is set by a private agreement is not a reference at all. `W3C-ORG` is pinned in prose to "its 2014 Recommendation" (L1039) and the entry's `date: 2014` matches — acceptable.

### 3.5 COMMENT — Note to the RFC Editor is incomplete and partly unverifiable

L156–183. Positives: it is present, it correctly identifies RFC 8785 as the downref needing Last Call announcement, and it correctly justifies why RFC 8785 cannot be demoted. Defects:

1. **Enumeration is wrong once §3.1–3.4 are fixed.** "makes **four** normative references to Informational documents: RFC 6839, RFC 8785, RFC 9053 and RFC 9334" (L160–161). It omits `UAX15` (a non-IETF normative reference, L51–58) and does not address `RFC9943` / `RFC9942` at all.
2. **Downref-registry claims must be verified.** L162–163: "RFC 6839, RFC 9053 and RFC 9334 are already recorded in the downref registry, so no Last Call action is required for them". RFC 9053 and RFC 9334 are commonly downreffed and plausibly registered; **RFC 6839's presence in the downref registry should be independently confirmed** before Last Call, because if it is not registered the announcement omits it.
3. **RFC 9943 / RFC 9942 status is unverified in this review.** The front matter asserts (L49–50) that these are the published SCITT Architecture (ex `I-D.ietf-scitt-architecture`) and COSE Receipts (ex `I-D.ietf-cose-merkle-tree-proofs`). **If RFC 9943 (SCITT Architecture) published as Informational — as RATS' architecture document RFC 9334 did — it is a fifth undisclosed downref**, and the Note is materially incomplete. This must be checked against the RFC index before the document leaves the AD's queue. `RFC9943` is cited normatively 5× (L204, L4394, L4704, and in `{{composition-scitt}}`); `RFC9942` 8×.
4. **The SCRAPI note under-instructs the RFC Editor.** L172–183 says only "the reference should be updated to the resulting RFC number". But L177–179 concedes that "{{scrapi-binding}} imposes requirements expressed in terms of **that document's endpoints, status codes and media types**". §12 of this document hardcodes `/.well-known/scitt-keys` and `/.well-known/scitt-keys/{kid_value}` (L3871–3872), a `Content-Type` requirement (L3673) and status-code handling (L3745–3785). If SCRAPI's endpoint names changed in AUTH48 — and the endpoint name in the SCITT reference API has been in flux — this document is silently wrong. The Note should instruct the RFC Editor (or the authors at AUTH48) to **verify each endpoint, status code and media type against the published SCRAPI RFC**, not merely to swap the reference number.

### 3.6 COMMENT — `RFC 9530` normative but cited once, `RFC 8615` cited once

`RFC9530` (Digest Fields) is cited only at L3304 for `content-digest` — correctly normative. `RFC8615` is cited only at L4347. Both fine; noted only because idnits will report the low citation counts.

### 3.7 GOOD — Obsoleted-RFC handling is exemplary

L63 flags `RFC6962` as "obsoleted by RFC 9162 and cited deliberately: it is what deployed CT logs implement", and the body says so explicitly at L1286–1291. Both are informative and RFC 9162 is named as "the current specification". **No defect.** This is the correct way to cite an obsoleted RFC and should be left alone.

### 3.8 GOOD — Reference completeness

Every one of the 39 declared references is cited at least once; every `{{...}}` citation resolves either to a declared reference or to a defined anchor. **No dangling or orphan references.** (Verified programmatically.)

### 3.9 NIT — Bare RFC numbers used where citation syntax was intended

L4448 ("an implementer arriving from RFC 6962"), L4704 ("RFC 9943 defines no role"), L4798 ("an RFC 9942 receipt"), L5041–5042, L5099, L5238–5239, L5498. These will not hyperlink in the HTML rendering.

### 3.10 NIT — `UAX15` reference floats

L51–58 targets `https://www.unicode.org/reports/tr15/` with `date: 2025`. The tr15 URL always redirects to the current version. A normative reference to Unicode normalisation should pin a specific UAX #15 revision *and* a Unicode version (the body at L336 says only "Unicode Normalization Form C {{UAX15}}"). NFC is stability-guaranteed by Unicode policy, so this is a nit rather than a correctness problem, but the RFC Editor will ask.

---

## 4. IANA CONSIDERATIONS

The IANA section (L4210–4391) is unusually thoughtful about *designated-expert instructions* and unusually weak about *registration mechanics*. IANA will bounce it in its current form.

### 4.1 DISCUSS — Ten new registries requested with no registry tables, no column definitions, no reference column, and no registry group

L4243–4341 requests ten new registries in **prose bullets**:

1. ARP Divergence-Axis values
2. ARP Non-Answer Reasons
3. ARP Post-Seal Evaluation Qualifiers
4. ARP Register Data-Format Profile identifiers
5. ARP Aggregation-Method Descriptors
6. ARP Retroactive Evaluation Triggers
7. ARP Override Grounds
8. ARP Re-Typing Grounds
9. ARP Verdict-Arithmetic operators
10. ARP Ledger Entry Types

For each, RFC 8126 requires and this document omits:
- **The registry group / protocol registry page** it belongs to (no "Attestation Reconciliation Protocol (ARP)" group is requested; IANA cannot create ten free-floating registries).
- **A table of the registry's columns.** Registries 1, 2 and 10 are described as having extra columns ("Each entry **MUST** record whether the axis is register-attestable or server-recorded", L4245–4246; "whether the reason is register-attested or server-observed", L4252–4253) but the columns are never named or ordered.
- **A table of initial contents.** All ten say "initially containing the values enumerated in {{X}}" and leave IANA to extract them from running prose. For the Divergence-Axis registry the initial set is buried in a **17-item comma-separated sentence inside a definition list at L495–521**, interleaved with parenthetical explanations. IANA will not do that extraction.
- **A Reference column** giving the defining section for each initial value.
- **A Change Controller / contact** for the registries.

Registries 3, 4, 8 additionally have **no designated-expert instruction at all** or use non-normative phrasing where the others use MUST: L4266 "the designated expert **refuses** a registration that qualifies a verdict"; L4276 "The designated expert **refuses** a registration that defines any means of transporting register records" (lowercase, indicative) versus L4247 "The designated expert **MUST** refuse a registration that does not state it". Registry 8 (Re-Typing Grounds, L4302–4306) has no expert guidance whatsoever.

### 4.2 DISCUSS — COSE registrations are incomplete against the registries' own column sets

L4212–4231 requests four **COSE Header Parameters**. That registry's columns are **Name, Label, Value Type, Value Registry, Description, Reference**. The document supplies Name and (informally) Value Type; it does not supply Label-range guidance, Value Registry (may be empty, but must be stated), or a per-parameter Reference section. It also does not say **whether the labels are to be integers or text strings** — COSE permits both, and "values to be assigned by IANA" (L4213) is ambiguous. `arp-bilateral-agreement-hash` is described as "a CBOR array of byte strings" and `arp-source-data-version` as "a CBOR array of two-element arrays" (L4222–4225), which are structures, not registry Value Types.

L4233–4241 requests two **COSE Key Common Parameters**. That registry's columns are **Name, Label, CBOR Type, Value Registry, Description, Reference**, and — importantly — the *Common* registry is for parameters applicable to **all** key types. `arp-key-status` and `arp-key-validity` are ARP-application-specific key lifecycle metadata. The COSE designated experts will very likely object that these belong in an application-specific header/parameter space rather than the common key parameters registry. At minimum the document must justify the choice.

### 4.3 DISCUSS — Controlled value sets used in signed fields but never registered (body → IANA direction)

Cross-checking the body against §9 in the body→IANA direction turns up **five** closed vocabularies that are not registered:

| Value set | Defined at | Used in | Registry? |
|---|---|---|---|
| **Requester-Binding Class**: `human-operator`, `agent-verified`, `agent-key-verified`, `agent-unverified` | L701–718 | Reconciliation Output field (L1628), **signed Ledger reconciliation-entry field** (L2179–2180), `{{vc-interop}}` credential subject field (L3910), Security Considerations (L4058–4060) | **NO.** L4339–4340 even refers to it as "the four classes of the Requester Identity Binding and Agent Friend-or-Foe Gate section" — i.e. IANA is told a Ledger field's value space lives in prose. |
| **Refusal Ground**: `pattern-matched`, `regime-not-admitted`, `audience-member-not-enrolled`, `agent-iff-refused` | L765–772 | Remediation Advisory, which is itself a **registered media type** (`arp-remediation-advisory+cbor`) returned on `422`/`403` | **NO** |
| **Attribution**: `policy-state`, `source-data-version`, `attribution-indeterminate` | L2543–2546 | Sovereign Re-Notification signed payload | **NO.** And `attribution-indeterminate` simultaneously appears in the *Post-Seal Evaluation Qualifiers* registry (L4262–4263) — one token, two vocabularies, one of them unregistered. |
| **Pattern Library pattern identifiers**: `projection-narrowing-evasion`, `predicate-substitution-evasion`, `attested-value-bracketing-evasion`, `addressed-register-cherry-picking`, `agreement-staleness-injection`, `pattern-library-version-pinning`, `agent-principal-spoofing`, plus `repeated-narrowing` (L3998) | L757–761 | **Override Record** signed by an operator (L792), and the Remediation Advisory | **NO.** L4295–4296 says the Override *Ground* is registered "so that grounds are enumerable and comparable across deployments rather than free text that no reviewer can aggregate" — the identical argument applies to pattern identifiers, which are also carried in the Override Record. |
| **Combined Verdict values**: `match`, `no-match`, `partial-match`, `indeterminate` | L385–388, L1201 | everywhere | **NO** — and the Verdict-Arithmetic *operator* registry is extensible (Specification Required, L4307) with a requirement only that a registration "state the operator's result as a total function of the multiset of contribution values" (L4310–4311), which does not bound the codomain. A registered operator could yield a fifth verdict value with no registry to record it. |

### 4.4 DISCUSS — RFC 8820 (BCP 190): the document fixes URI paths on origins it does not own

`{{ledger-read}}` and `{{request-binding}}` hardcode nine read paths plus one write path directly under the authority root of every deployment:

`POST /arp/reconciliations` (L3222); `GET /arp/outputs/{reconciliation-hash}` (L3376); `GET /arp/reconciliations/{reconciliation-identifier}/registers/{register-identifier}` (L3382); `GET /arp/outputs` (L3391); `GET /arp/continuations/{reconciliation-hash}` (L3403); `GET /arp/entries/{entry-sequence-number}` (L3409); `GET /arp/post-seal-records/{...}` (L3424); `GET /arp/sweeps/{examined-set-root}/inclusion/{claim-hash}` (L3428); `GET /arp/re-notifications` (L3434); `GET /arp/sweeps` (L3439).

RFC 8820 (BCP 190) §2.1: specifications "MUST NOT specify the structure of the path component" of URIs on origins they do not control; they should use a well-known URI or a discovery document instead. This document **registers six well-known URIs** (§9.1) and therefore clearly knows the mechanism — but uses it only for key/head/parameter discovery, and puts the entire read API under a fixed `/arp/` prefix. **RFC 8820 is not referenced anywhere in the document.** This is a straightforward ART-area DISCUSS.

### 4.5 COMMENT — Well-Known URI registrations: template incomplete, and a non-registry column is presented as one

L4345–4358. RFC 8615 §3.1 template fields: **URI suffix; Change controller; Specification document(s); Related information; Status.** The document supplies four of five (L4347–4348) and omits **Related information** (which may be "none", but must be stated).

The table's third column, "Path syntax below the suffix", **is not a field of the Well-Known URIs registry**. It should be presented as explanatory text outside the registration template, or IANA will not know what to do with it.

Minor internal inconsistency: the table says `arp-sealing-keys` takes `/{kid}` (L4353) while the body writes `/.well-known/arp-sealing-keys/{kid_value}` (L3805). Pick one.

Substantive: **six new well-known URIs from a single specification** is a lot, and four of them (`arp-sealing-keys`, `arp-register-keys`, `arp-operator-keys`, `arp-authorised-origins`) are key-discovery variants that a single signed discovery document could carry. RFC 8615 §1.1 explicitly discourages proliferation. Expect pushback from the designated experts.

### 4.6 COMMENT — `x-` prefix rule stated normatively in the body and non-normatively in IANA

L943–944: "Identifiers beginning `x-` are reserved for bilateral use and **MUST NOT** be registered."
L4274–4275: "Identifiers beginning `x-` are reserved for bilateral use and **are not registered**."

Two different strengths for one rule; and the RFC 6648 position is that `x-` prefixes are deprecated as a convention. The reservation belongs in the IANA section as a registry note, once, and should acknowledge RFC 6648.

### 4.7 COMMENT — Media types: template largely present, several gaps

L4360–4390. The collective template at L4362–4377 covers: type name, subtype names, required/optional parameters, encoding considerations, security considerations, interoperability considerations, published specification, intended usage, change controller, applications, restrictions on usage, deprecated alias names, magic numbers, file extensions, fragment identifier considerations, and (obliquely) person & email. Gaps:

1. **"Macintosh file type code(s)"** — required by the RFC 6838 §5.6 template's "Additional information" block, omitted.
2. **Person & email address is given by reference**: "the author is the author of this document and the contact address is the one on its front page" (L4373–4374). IANA registrations must carry a literal name and address; the RFC Editor will require expansion.
3. **`+cose` and `+cbor` structured syntax suffixes are not sourced.** L4374–4377 cites "Section 3.1 of {{RFC6839}} for `+json`" and says fragment identifier considerations "are otherwise none, no fragment identifier syntax being defined for the `+cbor` and `+cose` forms". RFC 6839 registers neither `+cbor` nor `+cose`; those were registered elsewhere (RFC 8949 and the COSE work respectively). RFC 6838 §4.2.8 requires that a suffix used be a registered one, and the registration should cite where each suffix is defined.
4. **Ten of the twelve media types are never named at their point of use.** Only `application/arp-sealed-reconciliation-output+cose` (L3696) and `application/arp-reconciliation-output+json` (L3906) appear literally in the body. Everywhere else the body says "under the media type registered in {{iana}}" (L774, L2532, L3339, L3790, L3461) and leaves the reader to reverse-map through the IANA table's "Carries" column. An implementer of `{{head-consistency}}` or `{{sweep-statements}}` cannot determine the `Content-Type` to emit without solving a puzzle. Name each type at its definition site.
5. **`{{vc-interop}}`'s justification for `+json` should be re-checked.** L3907–3908: "`+json` rather than `+ld+json`, **there being no such registered structured syntax suffix**". A `+ld+json` structured syntax suffix registration does exist in the IANA Structured Syntax Suffix registry (W3C change controller). **Verify before Last Call**; if it is registered, the stated rationale is false and the suffix choice must be reconsidered, because a JSON-LD document served as `+json` loses JSON-LD processing semantics for generic consumers.

### 4.8 COMMENT — Pre-publication transitional text inside a normative section

L3216–3218 (`{{cbor-cose}}`):
> "**Pending registration**, implementations **MAY** use labels from the private-use range of the COSE Header Parameters registry; such use is not interoperable."

Once published there is no "pending registration". This sentence must be removed (or moved into the Note to the RFC Editor). As written, a Standards Track document contains a MAY that explicitly authorises non-interoperable behaviour with no sunset.

### 4.9 NIT — "(value TBD)" ×6

L4216–4219, L4235–4236. These are legitimate IANA placeholders (IANA assigns), unlike a genuine editorial TODO. **No other TBD/TODO/XXX/FIXME/editor's-note markers exist anywhere in the document** — verified by exhaustive grep. Good.

### 4.10 GOOD — IANA→body direction cross-check is clean

Every registry the document requests has its initial values genuinely defined in the body, and all six registered well-known suffixes are used in the body. All eleven Non-Answer Reasons enumerated at L1407–1430 (including `subject-ceiling-exhausted`, which is *motivated* in Security Considerations at L3982) are present in the section the registry points at. **No defect in this direction.**

---

## 5. SECURITY AND PRIVACY CONSIDERATIONS (SecDir lens)

### 5.1 GOOD — a Privacy Considerations section exists and is honest
L4167–4208. It exists (many drafts in this space have none), it names what is protected and what is not, and it explicitly concedes the hardest point: "**A subject has no standing in this protocol: it is not notified, it cannot object, and it cannot learn that it was reconciled**" (L4192–4194). It enumerates six residual disclosure surfaces. This is better than most SecDir reviews ever see.

### 5.2 DISCUSS — Key compromise destroys all history, with no recovery path

L3847–3855:
> "A relying party **MUST** reject a Sealing Signature made under a `revoked` key **irrespective of when the Output claims to have been sealed** ... A key **MUST NOT** be removed from the set while any Reconciliation Output it sealed may still be relied upon"

Combined with:
- L2098–2101: every Settlement-Layer Ledger **Entry Signature** is "a COSE_Sign1 by the reconciliation-server sealing key";
- L2085–2091: the **Prior-Entry Hash** is the Signing Input Digest of the preceding entry's Entry Signature, and therefore covers the Sealing-Key Identifier;
- L3459–3460: every **read response** is "a COSE_Sign1 by the reconciliation-server sealing key".

A single sealing-key compromise therefore: invalidates every Reconciliation Output ever sealed under it; invalidates every Ledger entry signed under it; and, because the hash chain commits to the key identifier, leaves the chain structurally intact but every link's signature rejected. There is **no counter-signature, re-sealing, timestamping-authority, or "valid-at-time-of-signing under an independent time attestation" mechanism** anywhere in the document. `{{crypto-upgrade}}` (L2743–2785) handles *primitive* rotation, explicitly not compromise. The notarisation into a SCITT Transparency Service (`{{scrapi-binding}}`) is **optional** ("A Reconciliation Output **MAY** be notarised", L3662) and so cannot be relied on as the recovery path.

This needs either a recovery mechanism or an explicit, reasoned statement in §7 that compromise is catastrophic and why that is acceptable.

### 5.3 DISCUSS — The Deployment Blinding Value is a single, unrotatable, deployment-lifetime secret whose compromise deanonymises the entire published ledger

L1959–1963:
> "a secret of at least 128 bits drawn once from a cryptographically secure random source, persisted in the policy-epoch store, **constant for the life of the deployment**"

L1976–1986 states the consequence precisely and correctly: without it "anyone holding either can recover by exhaustive search the subject that was investigated and the principal that commissioned the reconciliation, which is the disclosure this protocol exists to prevent." What is missing:

1. **No rotation procedure.** L1969 asserts constancy is required for Ledger indexing and retroactive evaluation. So the value can never be changed, and there is no forward secrecy: a compromise at year 10 retroactively deanonymises years 1–10 of a *published, broadly readable* ledger (L4176–4177).
2. **No storage/HSM requirement** beyond "persisted in the policy-epoch store".
3. **No compromise-response guidance at all** — the word does not appear in connection with it.
4. **Key reuse across two primitives.** The same secret is used (a) as a value inside SHA-256 digest preimages (L1943–1944, L347) and (b) as an **HMAC-SHA-256 key** for the Reconstruction Proof (L2581–2585). One secret, two constructions, no domain separation. This is a standard SecDir objection even where no concrete attack is known.
5. **It is disclosable.** L2600–2601: "A deployment that requires the stronger property **MUST** appoint an Audit Identity jointly with every register ... and **MAY** disclose the Value to that joint identity alone." Disclosing the deployment's master de-anonymisation key to a jointly-appointed auditor is a very large security event described in one sentence with no controls on it.

### 5.4 DISCUSS — Output verification requires reachability of every addressed register, including ones that failed to answer

L3838–3841:
> "A relying party **MUST** verify that the origin component of the Sealing-Key Identifier appears in the Authorised-Origin Document published by **every register in the Addressed-Registers Identifier Set**, and **MUST** reject the Output where it does not **or where any such document cannot be verified**."

But the Addressed-Registers Identifier Set includes registers recorded as `register-unresponsive` (L1418–1419), `register-refused`, `agreement-drift-suspended`, `query-budget-exhausted`, etc. — `{{no-answer}}` L1404 is emphatic that "The Per-Register Result Set **MUST** carry an entry for **every** addressed register". So:

- An Output produced when register C was down is **permanently unverifiable** if register C's origin is still unreachable at verification time.
- More seriously, this is a **third-party denial-of-service on verification**: any register operator can render every Output that ever addressed it unverifiable by withdrawing `/.well-known/arp-authorised-origins`, retroactively and for all relying parties. The document's own `{{bra-limits}}` and `{{budget-suppression}}` show it is alert to suppression channels; this one is not discussed.
- It is also a **fetch-amplification vector**: every verification of every Output triggers one Authorised-Origin fetch plus one register-key-set fetch per addressed register, unbounded, with no caching guidance and no rate discussion.

### 5.5 COMMENT — Unbounded retry obligation to a third-party endpoint

L2551–2554 (`{{re-notification}}`): "The server **MUST** deliver it to the notification endpoint ... **MUST retry until acknowledged** or until the retention period of {{delivery}} elapses". The retention period is "the LONGEST period any Bilateral Register Agreement ... declares" (L1899–1901) and in no case shorter than the Reliance Horizon plus one reliance interval. There is **no backoff requirement, no maximum rate, and no cap on concurrent retries.** A regulator endpoint that goes offline receives an unbounded retry storm for potentially years. Needs an exponential-backoff MUST and a rate ceiling.

### 5.6 COMMENT — Amplification: one request, N register queries

The reconciliation server issues one Per-Register Claim Projection per addressed register (L838–905). There is a per-principal per-subject **query budget** on the *register* side (L3949–3951) but no bound on the number of registers a single request may address, no cost/proof-of-work, and no discussion of the server as a reflector against registers. `{{containment}}`'s budget is about record recovery, not about load. Should be addressed in §7.

### 5.7 COMMENT — Timing / traffic analysis is asserted, not bounded

`{{read-errors}}` L3596–3618 is genuinely strong on the 403/404 oracle and correctly separates deterministic conformance from statistical timing claims. But it stops at requiring that an implementation *claiming* timing resistance publish its methodology (L3606–3610). No implementation is required to *have* the property. Given that the whole `{{read-errors}}` construction exists to prevent an existence oracle, an attacker who wins on timing defeats every deterministic requirement in the section. State the residual explicitly in `{{privacy}}` or §7.

### 5.8 COMMENT — Privacy Considerations does not follow or cite RFC 6973

RFC 6973 is not referenced anywhere. §8 covers, informally, several RFC 6973 threats (surveillance, correlation, secondary use, disclosure) but never does the structured analysis, and omits **identifiability of the *requester*** and **exclusion** (the subject's inability to know or correct data about itself) — which is precisely the GDPR-adjacent point given the domain is beneficial ownership and sanctions. L4192–4196 gestures at it ("a deployment operating where subject rights attach **should** provide for them outside this document") in lowercase, non-normatively, in one sentence. For a protocol whose stated inputs are FinCEN BOSS, UK PSC and EU AMLD beneficial-ownership registers, the IESG will want more than one sentence, and will want RFC 6973 cited.

### 5.9 COMMENT — Data-residency claim is stronger in the Abstract than in the body

Abstract L127–129: "without raw register records leaving their data-residency jurisdiction". The body concedes the residual inference channels honestly (L3939–3947: "a sequence of reconciliations varying that value recovers the underlying record field by search, and several Divergence Axis values ... disclose record content on their own"). The Abstract's unqualified claim is not supported by §7. Soften the Abstract.

### 5.10 GOOD — coverage that is genuinely present
Key rotation ✓ (`{{crypto-upgrade}}`, `arp-key-status`/`arp-key-validity`, retired-not-deleted). Revocation ✓ (in-band, L3830–3833). Replay ✓ (`{{replay-defence}}`, nonce uniqueness L1000–1005, `{{per-register-encryption}}` L1191–1195). DoS ✓ partially (rate limits L3631–3640, budget exhaustion L4002–4038 — and `{{budget-suppression}}` is a model of how to document a countermeasure that is itself an attack). Side channels ✓ (`{{side-channel}}`). Malleability ✓ (`{{signature-malleability}}` is the best section in the document).

---

## 6. STRUCTURAL / EDITORIAL DEFECTS THAT DELAY PUBLICATION

### 6.1 DISCUSS — Pervasive Internet-Draft revision commentary in the normative body and the Abstract

An RFC has no revisions. There are **20+ occurrences in the normative body**, plus one in the Abstract:

- **Abstract, L147–153**: "**This revision adds** a normative binding to the SCITT Reference APIs, register data-format profiles ..., and a source-data version binding". An RFC abstract cannot say this.
- L2862–2864: "Items 26, 27, 28, 30 and 31 are **new in this revision**; item 29 is carried from **-03** in a new position."
- L2877–2885 — the worst instance, because it is normative:
  > "**An Agreement computed under an earlier revision does not compute the same Agreement Hash under this one.** ... Agreements **MUST** be recomputed, and a deployment holding a Bilateral-Register-Agreement Hash recorded **before this revision MUST** treat it as naming an Agreement under the earlier item list"

  Two MUSTs whose antecedent is a pre-publication draft revision. Meaningless in an RFC.
- L2516–2517: "Agreements negotiated **before this revision** name none of these fields" — with a normative consequence following.
- L895–896: "is the principal item of work **this revision leaves for the next**."
- Also L717, L1660, L1762, L1879, L1955, L2028, L2128, L2135, L2332, L2557, L2566, L2653, L2739, L2766, L2781, L2875, L3117, L3283, L4148, L4403, L4646.

All of this must move to the (removable) Document History appendix or be rewritten as timeless design rationale.

### 6.2 DISCUSS — Normative construction defined only in an appendix, with an unimplementable requirement

Covered at §2.4. Restating the sharpest instance: `{{terminology}}` L356–357 makes a MUST NOT whose subject (`subject_digest`) is defined at L4753–4758 — in Appendix D — and whose distinctness rules are at L4873–4894, also Appendix D. And L4875–4881's requirement to emit "an identifier that commits to the declared canonicalisation parameters -- member-sort code unit, normalisation, number rendering, absent-member handling and hash algorithm" specifies no identifier format and requests no registry. It cannot be implemented interoperably.

### 6.3 DISCUSS — The register-facing transport is deliberately left unspecified

L893–897:
> "That is a deliberate scoping decision and it is a real limitation ... two reconciliation servers addressing the same register do so over channels the register defined, so **ARP is interoperable in its artefacts and not yet in that leg's transport**. Specifying it -- an endpoint, a media type, and a COSE_Encrypt construction pinning the AEAD and the ordering of its authenticated additional data -- is the principal item of work this revision leaves for the next."

RFC 2026 §4.1.1 requires a Proposed Standard to be "well-understood" and to have "no known technical omissions". The document is admirably candid, but the omission is the **primary protocol leg** — the reconciliation server ↔ sovereign register channel, which is the whole point of the specification. `{{per-register-encryption}}` (L1163–1165) explicitly says it states "properties the channel **MUST** provide and **not a wire construction this document pins**". BRA item 4 (L2807–2808) delegates "The transport, endpoint, framing and encryption construction" to a private contract.

Two implementations of this specification cannot talk to the same register without a bilateral agreement neither the IETF nor a third implementer can read. That is not Proposed Standard material as it stands. Options the AD will offer: (a) pin the construction; (b) retarget to Experimental or Informational; (c) split, publishing the artefact formats as Standards Track and the register leg separately.

### 6.4 COMMENT — Contradiction / dangling forward reference in `{{audience}}`

L1770–1771: "A Reconciliation Output carries an Audience Set of **zero or more** Audience Members, encoded as a CBOR array which is **empty only in the case described below**."
L1804–1806: "Every requester signs, by {{read-signing}}, so there is always a key to name and **an Audience Set is never empty**."

The "case described below" does not exist. Either the first sentence's forward reference is stale, or the second is wrong. Resolve, and fix "zero or more" → "one or more".

### 6.5 COMMENT — Undefined terms used normatively

| Term | First use | Status |
|---|---|---|
| **"service-operator entity"** | L3927, L3929 | Used twice, both in the MUST NOT of `{{containment}}`. **Never defined.** `{{terminology}}` defines *Register Operator* but not this. The subject of a DISCUSS-level prohibition is undefined. |
| **"the system"** | L632 | Subject of the determinism MUST; not a defined protocol role |
| **"Operating-Party Identifier"** | L285 (Witness Quorum definition) | Defined later, at `{{witness-entries}}` (L2898+); the definition that uses it carries no forward reference |
| **"Audit Identity"** | L2152 | Used 20 times; defined operationally at L2570–2572 but has no `{{terminology}}` entry despite being a first-class protocol role with read entitlements |
| **"Policy Parameters Document"** | L2711 | Defined at L3337–3355; no terminology entry, but has a registered media type |
| **"Authorised-Origin Document"** | L804 | First used in the Adversarial Pre-Transmission Test section; defined at L3792–3795, i.e. ~3000 lines later |
| **"Reconstruction Proof"** | L2581 | Defined inline only; no terminology entry |

### 6.6 COMMENT — Five section headings have no anchor, and three are cross-referenced by prose name

Headings without `{#anchor}` that are referred to elsewhere: **"Canonical Claim Ingestion"** (L664, referred to at L692), **"Requester Identity Binding and Agent Friend-or-Foe Gate"** (L695, referred to at L3255–3256 and **L4339–4340 in IANA Considerations**), **"Adversarial Pre-Transmission Test"** (L751, referred to at **L4300 in IANA Considerations**, **L4355 in the well-known URI table**, and **L4380 in the media-types table**), **"Pattern-Library Integrity"** (L4039), **"Receipt validation"** (L3868).

The consequence is concrete: three **IANA registration entries** identify their defining section by an English phrase rather than a section number. IANA and the RFC Editor will both ask for section references. Add anchors and use `{{...}}`.

### 6.7 COMMENT — Self-referential cross-reference and a broken sentence in `{{sealing-key-discovery}}`

L3824–3826:
> "An Authorised-Origin Document is a COSE_Sign1 whose payload comprises, for each reconciliation server the register operator has authorised, **that server's the three-element arrays {{sealing-key-discovery}} pins above**. It MUST be signed under a key served as a COSE Key Set at ..."

Two defects in one sentence: (a) "that server's the three-element arrays" is ungrammatical; (b) `{{sealing-key-discovery}}` is the anchor of the section this sentence is in — a section citing itself. Also, the Authorised-Origin Document is defined twice in the same section (L3792–3795 and L3824–3826) with two different phrasings.

### 6.8 COMMENT — Abstract

247 words, 6 sentences, ~2000 characters. **No citations** ✓ (correct). But:
- One sentence runs from L125 to L146 — roughly 190 words with seven subordinate clauses. It will be unreadable in the 72-column text rendering.
- L147–153 refers to "This revision" (§6.1).
- The length is at the upper bound of what the RFC Editor accepts; ~200 words is the norm. It does stand alone.

### 6.9 COMMENT — No Implementation Status section (RFC 7942), and the document contains implementation evidence that would populate one

Absent. The document contains multiple concrete implementation and measurement claims that RFC 7942 exists to house:
- L4119–4121: "Measured over two hundred randomly generated P-256 keys and ES256 signatures, two hundred substitutions verified and two hundred changed the enveloped bytes."
- L4409–4410: "his design, **contributed as an executable vector class**"
- L4478–4479 (Acknowledgments): "contributed as an executable vector against a **third-party corpus**"
- L1295–1300 discusses conformance-vector coverage at four and eight leaves.

There is also a `conformance/` directory and a `merkle_equiv.py` alongside the source. RFC 7942 is optional, but where a document already asserts measurement results in its Security Considerations, the AD will ask that they be relocated into a properly-marked, removable Implementation Status section — measurement results in Security Considerations are not stable statements for an archival RFC.

### 6.10 COMMENT — Tables will render poorly in the .txt output

The `{{bra-hash}}` CBOR-type table (L3075–3092) has a 2-column layout in which the second column reaches **262 characters** (L3081, item 7) and exceeds 100 characters in eight rows. At a 72-column text width with a `| Item | CBOR encoding |` split, item 7's cell wraps to roughly 20 lines against a 2-character first column. The media-types table (L4378–4390) has one 190-character row (L4382) and three over 100. Both should be converted to definition lists.

### 6.11 NIT — One artwork line exceeds the 72-character limit

L1442: `    ["arp-non-answer-v1", Reconciliation Identifier, Projected Predicate,` — 73 characters. idnits will report it. All other literal blocks (L1941–1947, L3463–3465, L4756–4758) are within bounds.

### 6.12 NIT — Grammatical / typographic errors

- L2485: "the predicates over which it may **be returned them**"
- L3824–3825: "that server's the three-element arrays" (§6.7)
- L3847: "A key entry MUST carry the `arp-key-validity` and `arp-key-status` parameters **of `active`, `retired` or `revoked`**" — the enumeration binds to the wrong parameter
- L1272–1273: "A leaf node is `SHA-256(0x00 || leaf)`" appears mid-paragraph rather than as artwork
- L4400: "Named findings, because a specification improved by review should say by whom." — sentence fragment / editorialising in the Acknowledgments
- Consistent British spelling ("canonicalise", "notarise", "serialisation", "recognised", "Licence") throughout; the RFC Editor will not object but will normalise, and the document mixes it with US forms in places (e.g. "authorized" does not appear, but "Authorised-Origin Document" is registered as a term while `arp-authorised-origins` is a wire identifier — the wire identifier is now permanently British and cannot be normalised, which is worth flagging to the authors *before* AUTH48).

### 6.13 NIT — Author/affiliation block is thin

L24–31: `ins`, `name`, `organization`, `email`, `country` only. No street, city, region or postal code; no phone; no URI. The RFC Editor typically wants at least city + country. `country: United States of America` is the correct current RFC style. Single author, no `contributor:` block — see §7.2.

### 6.14 NIT — Front matter miscellany

- `date: 2026-08-13` on a document reviewed 2026-08-20 — fine, but should be bumped or removed (kramdown-rfc will use the submission date if omitted).
- No `consensus:` key. For `submissiontype: IETF` + `category: std` xml2rfc defaults it correctly, but stating it removes ambiguity.
- `area: Security` with no `workgroup:` — correct for an individual submission.
- Section 1 is "Note to the RFC Editor", to be removed. Removing it renumbers every section, so every "Section N" reference in any external document (and in the Document History) shifts. Conventionally these notes are unnumbered or placed after the Introduction. Minor, but worth doing before Last Call so reviewers cite stable numbers.
- L2867–2868 says "Two of the five were already required elsewhere in this document" then enumerates **three** (items 26, 30, 31) at L2868–2874. Off-by-one in the prose.

### 6.15 GOOD — things that are right and should not be touched
- `--- back` placement is correct: middle sections → references → appendices.
- All example domains use `.example` (`arp.example`, `register-a.example`, `ts.example`) per RFC 2606 ✓.
- Example arithmetic is internally consistent: disjunction over three `no-match` → `no-match` (L1587–1591 vs L4491–4494); Reliance Horizon 2026-04-27T19:47:14Z + 7 days = 2026-05-04T19:47:14Z ✓ (L4497–4499); "two days past" 2026-05-06 ✓ (L4560).
- The Ledger entry field order in the example (L4505–4526) matches the normative field order in `{{settlement-ledger}}` (L2072–2101, L2172–2186) exactly, including the CBOR-null placeholder ✓.
- "seventeen subsystems" (L598) — 17 items enumerated ✓. "Nine operations" (L3367) — 9 enumerated ✓. "exactly thirty-one elements" (L3063) — items 1–31 ✓. "Twelve media types" (L4362) — 12 rows ✓. "Six entries ... in the Well-Known URIs registry" (L4347) — 6 rows, and exactly those six appear in the body ✓.

---

## 7. IPR AND PROCESS

### 7.1 GOOD — `ipr` setting is correct
L11: `ipr: trust200902`. Correct for an IETF-stream Standards Track individual submission. No statement anywhere in the document conflicts with BCP 78 or BCP 79 — verified by exhaustive search for patent/licence/royalty/proprietary/trademark/copyright language. The only hits are the author's affiliation (L29–30) and unrelated uses of "confidential" (describing artefact handling) and "Licence" inside the WCO Data Model package name (L1053).

### 7.2 COMMENT — Nine individuals are credited with drafting normative text but are not Contributors

L4402–4480 credits nine named people, several in terms that describe **text contribution**, not review:

- L4416–4425 (Iman Schrock, with Anton Sokolov): "The requirements in {{construction-distinctness}} to pin the action type and version, the selected field and its normalisation and comparison rules ... **are his, substantially as he drafted them**."
- L4409–4410 (Songbo Bu): "The normalised observation in {{read-errors}}, its enumeration of HTTP metadata and cache behaviour, and the separation of the deterministic requirements from any statistical timing claim **are his design**"
- L4431–4433 (Walter Hawkins): "**Naming the independent observer, and the ordering of witness countersignature over independently anchored head digest, is his.**"
- L4437–4438 (Tiago Pinto): "{{read-responses}} takes that shape at his argument."
- L4472–4477 (Nenad Vasic): "The requirement in {{leaf-binding}} ... **is his**"

RFC 7322 §4.11 distinguishes Acknowledgements from a **Contributors** section, which is where people who supplied text belong and which carries full name/affiliation/contact. More importantly, BCP 78 §5.6 places the obligation on the *submitter* to have the rights to grant in **all** the text, including text drafted by others. An AD will ask:

1. Move these to a **Contributors** section with full contact blocks (they are, on this description, Contributors within the meaning of BCP 78 §1.d).
2. Confirm that each has been informed the text is being submitted under BCP 78 and has no objection.
3. Confirm whether any should be a co-author.

### 7.3 COMMENT — BCP 79 disclosure question

The author's affiliation is Certisyn, Inc. (L29), and the document is a substantial, novel protocol with commercial application to sanctions and beneficial-ownership screening. No IPR disclosure is referenced. Under BCP 79 §5.1.1 the obligation is personal to the contributor. The AD should ask on the record whether the author or Certisyn holds or has applied for any IPR reading on this specification, and, if so, that a disclosure be filed before Last Call. This is a routine question, not an accusation — but this document is exactly the profile where it gets asked.

### 7.4 COMMENT — Individual submission of a large protocol overlapping active WG work

`{{scrapi-binding}}` imposes MUSTs on SCITT WG endpoints; the document layers on the SCITT architecture and COSE Receipts; the Web Bot Auth drafts are active individual work in HTTPBIS/WEBTRANS space. An AD will ask whether this belongs in the SCITT WG (or a new WG) rather than as an AD-sponsored individual submission, and will want the SCITT chairs' view on record. That question is orthogonal to the technical content but will affect the timeline more than any finding above.

---

# SUMMARY TABLE

## DISCUSS-level (would block publication)

| # | Area | Finding | Location |
|---|---|---|---|
| D1 | §1.2 | `{{containment}}`'s "MUST NOT be given access to any ... Partial-Attestation payload beyond the verdict and divergence-axis fields" is contradicted by six MUSTs requiring the server to read other payload fields; the stated enforcement mechanism is never specified; the actor ("service-operator entity") is undefined | L3929–3931 vs L987, L1000–1001, L903–905, L1250–1252, L1120–1128, L1390–1392 |
| D2 | §1.3 | Three mutually inconsistent closed field lists for the Partial Attestation payload — SHALL vs SHALL NOT vs MUST NOT, three cardinalities | L377–384, L1200–1218/L1257–1258, L3929 |
| D3 | §1.4 | Two contradictory MUSTs in one paragraph on CBOR-null encoding of BRA items; the disagreement causes a reconciliation outage via `{{agreement-drift}}` | L3104–3110 |
| D4 | §3.1 | Normative MUSTs (the Agent Friend-or-Foe gate — one of the document's four stated purposes) expressed wholly in terms of **three informative individual I-Ds**; no RFC Editor note covers them | L3268–3276, L737–745, L308–312 vs L96–98 |
| D5 | §3.2 | `RECOMMENDED` (BCP 14) and a MUST-include set applied to **informative** FIPS 203 / FIPS 204 | L4089–4093, L2748–2751 vs L106–117 |
| D6 | §3.3 | **No reference at all** for SHA-256, HMAC, base64url, TLS, or HTTP, all of which are mandated; SEC1 v2.0 and FIPS 186-5 cited by section number with no reference entry | 21×, L2581, L3289/L3319, L3287, throughout §12; L4114–4115 |
| D7 | §3.4 | Register-profile vocabularies (BODS 0.4, W3C-ORG, RFC 6350, WCO-DM v4, UN/CEFACT) declared informative while this document's own MUSTs are written in them; invents a non-existent reference category; reference entries do not carry the versions the body pins | L935–938, L1008–1013, L1026–1028, L959–986, L1066–1069 |
| D8 | §2.1 | 31 normative keyword instances in **Security Considerations**, several of them load-bearing and referenced from the Introduction as "the normative rules" | L3925–4104 (table in §2.1) |
| D9 | §2.4 | Normative MUST/MUST NOT in four **appendices**, on which `{{terminology}}` and `{{signature-malleability}}` normatively depend; one appendix MUST (emit a canonicalisation-parameter identifier) defines no identifier and requests no registry | L4762–4980, esp. L4875–4881; L356–357 |
| D10 | §4.1, §4.2, §4.3 | IANA: ten registries requested in prose with no tables, columns, reference column or registry group; COSE registrations missing required columns and label-type; **five controlled value sets used in signed fields are never registered** (Requester-Binding Class, Refusal Ground, Attribution, Pattern identifiers, Verdict values) | L4210–4341; L701–718, L765–772, L2543–2546, L757–761 |
| D11 | §4.4 | RFC 8820 (BCP 190) violation: ten fixed `/arp/...` URI paths on origins the specification does not own; RFC 8820 not referenced | L3222, L3376–3441 |
| D12 | §6.3 | The primary protocol leg (server↔register transport, framing, endpoint, AEAD construction) is deliberately unspecified and delegated to private contracts — two implementations cannot interoperate | L893–897, L1163–1165, L2807–2808 |
| D13 | §5.4 | Output verification requires an Authorised-Origin Document from **every** addressed register including non-answering ones, and MUST reject on failure — a third-party retroactive DoS on verification and a fetch-amplification vector | L3838–3841 vs L1404, L1418–1419 |
| D14 | §5.2 | Sealing-key compromise permanently invalidates every historical Output, every Ledger Entry Signature and every read response, with no recovery, counter-signature or independent-time mechanism; notarisation is only MAY | L3847–3855, L2098–2101, L3459–3460, L3662 |
| D15 | §5.3 | Deployment Blinding Value is a single unrotatable deployment-lifetime secret whose compromise retroactively deanonymises the entire published Ledger; no rotation, no forward secrecy, no compromise response, reused as both a digest input and an HMAC key, and disclosable to a joint auditor | L1959–1963, L1976–1986, L2581–2585, L2600–2601 |
| D16 | §6.1 | Internet-Draft revision commentary throughout the normative body **and the Abstract**, including two MUSTs whose antecedent is draft `-03` | L147–153, L2877–2885, L2862–2864, +20 more |
| D17 | §1.5 | Roughly a quarter of the normative content imposes MUSTs on a private commercial contract rather than on an implementation or the wire; not testable against any interoperability criterion | L2798 + items 1–31, L923–925, L3816, L4092–4093 |

## COMMENT (would be raised)

| # | Area | Finding | Location |
|---|---|---|---|
| C1 | §3.5 | Note to the RFC Editor enumerates four downrefs but omits UAX15 and does not address RFC 9943/9942 status (**verify RFC 9943 is not Informational — if it is, a fifth undisclosed downref**); RFC 6839's downref-registry entry unverified; SCRAPI note instructs only a number swap, not verification of endpoints/status codes/media types | L156–183 |
| C2 | §2.2 | 20 normative keyword instances in **IANA Considerations**; L4227–4229 is a protocol requirement duplicating and partly conflicting with `{{cbor-cose}}` | L4210–4341 vs L3202–3204 |
| C3 | §2.3 | 24 normative keyword instances in the **Conventions and Definitions** section, including the entire five-step canonicalisation algorithm | L252–594 |
| C4 | §2.5 | Document History appendix (820 lines, 14% of the document) carries normative keywords and has **no "RFC Editor: remove" instruction** | L4981–5801 |
| C5 | §1.7 | Nine lowercase keywords where uppercase was intended; L286's lowercase "must" is **stronger** than the SHOULD at L3535 it refers to | L286, L722, L2606, L2076, L2339, L2030, L3683, L4033, L4195 |
| C6 | §4.5 | Well-Known URI template omits "Related information"; a non-registry column is presented as a registry field; `/{kid}` vs `/{kid_value}` inconsistency; six new well-known URIs invites RFC 8615 §1.1 pushback | L4345–4358 vs L3805 |
| C7 | §4.7 | Media types: Macintosh file type code omitted; contact given by reference not literally; `+cose`/`+cbor` suffix sources not cited; **ten of twelve types never named at point of use**; the `+ld+json` rationale at L3907–3908 should be verified against the Structured Syntax Suffix registry | L4360–4390, L3907–3908 |
| C8 | §4.8 | "Pending registration, implementations MAY use labels from the private-use range" — pre-publication transitional text authorising non-interoperable behaviour, with no sunset | L3216–3218 |
| C9 | §4.6 | `x-` prefix rule stated as MUST NOT in the body and non-normatively in IANA; RFC 6648 not acknowledged | L943–944 vs L4274–4275 |
| C10 | §5.5 | Unbounded retry obligation to third-party regulator endpoints for the retention period, with no backoff or rate ceiling | L2551–2554 |
| C11 | §5.6 | One request → N register queries; no bound on addressed-register count; server-as-reflector not discussed | L838–905 |
| C12 | §5.7 | Timing-based existence inference is required to be *documented* if claimed, never required to be *resisted*; residual not recorded in `{{privacy}}` | L3596–3618 |
| C13 | §5.8 | Privacy Considerations does not cite or follow RFC 6973; subject rights addressed in one lowercase sentence despite the beneficial-ownership/sanctions domain | L4167–4208, esp. L4192–4196 |
| C14 | §5.9 | Abstract's unqualified data-residency claim is not supported by `{{containment}}`'s own concession about repeated querying | L127–129 vs L3939–3947 |
| C15 | §6.4 | `{{audience}}`: "empty only in the case described below" — the case does not exist; contradicted by "an Audience Set is never empty" | L1770–1771 vs L1804–1806 |
| C16 | §6.5 | Seven terms used normatively and never defined in `{{terminology}}`, including "service-operator entity" (subject of a DISCUSS-level MUST NOT) and "the system" (subject of the determinism MUST) | L3927, L632, L2152, L2711, L804, L2581 |
| C17 | §6.6 | Five headings lack anchors; **three IANA entries cite their defining section by English phrase rather than section number** | L664, L695, L751, L4039, L3868; L4300, L4340, L4355, L4380 |
| C18 | §6.7 | `{{sealing-key-discovery}}` cites its own anchor; the sentence containing it is ungrammatical; Authorised-Origin Document defined twice | L3824–3826, L3792–3795 |
| C19 | §6.8 | Abstract: 247 words, one 190-word sentence, and a "This revision" clause | L125–153 |
| C20 | §6.9 | No RFC 7942 Implementation Status section, while measurement results sit inside Security Considerations | absent; L4119–4121 |
| C21 | §6.10 | Tables will render badly at 72 columns — one 262-character cell, one 190-character cell | L3075–3092, L4378–4390 |
| C22 | §1.6 | Eight MUSTs with passive or pronominal subjects | L1953, L1857, L1146, L1127, L632, L943, L4228, L3826 |
| C23 | §1.9 | Three notations for field presence in one enumeration: `OPTIONAL`, "present exactly where", lowercase "required" | L1206–1209, L1629–1679 |
| C24 | §7.2 | Nine individuals credited with having drafted normative text appear in Acknowledgements, not Contributors; RFC 7322 §4.11 and BCP 78 §5.6 rights question | L4402–4480 |
| C25 | §7.3 | No BCP 79 disclosure referenced; commercially-affiliated author, novel protocol in a commercial domain — AD should ask on the record | L29 |
| C26 | §7.4 | Individual submission overlapping active SCITT WG work; chairs' view should be on record | — |

## NIT

| # | Area | Finding | Location |
|---|---|---|---|
| N1 | §1.8 | "may not" used three times where prohibition is meant | L1572, L3106, L5180 |
| N2 | §1.10 | Thirteen all-caps non-keywords adjacent to keyword text | L2486, L2496, L2580, L1900, L1911, L1516, L4862, L4849, L4860, L4886, L708, L4838 |
| N3 | §1.11 | Six normative statements carried by markdown bold, lost in .txt | L3063, L3078, L3105, L2135, L2877, L3418 |
| N4 | §6.11 | One artwork line at 73 characters (limit 72) | L1442 |
| N5 | §6.12 | Grammatical errors: "may be returned them"; "that server's the three-element arrays"; parameter enumeration binds to the wrong parameter | L2485, L3824, L3847 |
| N6 | §6.12 | British spellings baked into permanent wire identifiers (`arp-authorised-origins`) — flag before AUTH48 normalisation | L4356, L3819 |
| N7 | §6.13 | Author block has no city/region/postal; single author, no `contributor:` block | L24–31 |
| N8 | §6.14 | No `consensus:` key; §1 is a numbered removable section (renumbers everything on removal); L2867 says "two of the five" then lists three | L1–22, L156, L2867–2874 |
| N9 | §3.9 | Seven bare "RFC NNNN" mentions that will not hyperlink | L4448, L4704, L4798, L5041, L5099, L5238, L5498 |
| N10 | §3.10 | `UAX15` targets the floating tr15 URL with no Unicode version pinned | L51–58 |
| N11 | §4.9 | Six "(value TBD)" IANA placeholders — legitimate, listed only for completeness; **no other TBD/TODO/XXX/FIXME/editor's note exists in the document** | L4216–4236 |

---

## Note on what is *right*

So the review is not read as uniformly negative: the reference graph is complete in both directions (no orphan or dangling references), the RFC 8174 boilerplate is exact, the Introduction and Abstract are keyword-free, the Examples appendix is correctly self-labelled non-normative and its arithmetic checks out against the normative sections, RFC 2606 domains are used throughout, every enumerated count in the document is accurate, the obsoleted-RFC citation of RFC 6962 is handled better than in most published RFCs, a Privacy Considerations section exists and is unusually candid, and `{{signature-malleability}}`, `{{budget-suppression}}` and `{{merkle-construction}}` are genuinely good specification writing — the last of these does something most Merkle-tree specifications fail to do, which is state its exact relationship to CT and name the leaf counts at which a plausible wrong implementation passes a test suite.

The blocking issues are, with the two exceptions of D12 (unspecified register transport) and D1/D2/D3 (the contradictory MUSTs), **placement and reference hygiene rather than design**. D12 is the one that determines whether this can be Standards Track at all.agentId: ab7ab93f77a4cae97 (use SendMessage with to: 'ab7ab93f77a4cae97', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 206263
tool_uses: 53
duration_ms: 1132985</usage>