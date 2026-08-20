# Adversarial Digest-Reproducibility Audit
**File:** `/home/claude/arp/draft-hillier-scitt-arp.md`
**Test applied:** for every item in every preimage — (a) CBOR major type fixed? (b) set/collection order fixed? (c) absent-OPTIONAL rule fixed? (d) digest over transmitted bytes or re-encoding fixed?

A structural note that governs most of what follows. The document fixes CBOR value types in exactly two places: the Ledger Entry Types registration (`4331`–`4343`, "Every hash is a 32-octet CBOR byte string; … every Entry Type is a CBOR text string…") and the Agreement Hash table (`3074`–`3091`). **Neither reaches the Reconciliation Output, the Post-Seal Evaluation Record, the Policy-Version Hash preimage, or the Non-Answer Statement.** The IANA text is scoped by its own opening sentence — "The initial registrations are those of {{settlement-ledger}}, with these value types" (`4330`) — so it cannot be borrowed. The Agreement Hash table is introduced by prose that states the principle correctly and then applies it only to `{{bra-items}}`:

> `3068`: "Determinism under Section 4.2.1 of {{RFC8949}} fixes how a given value is encoded. It does not fix which CBOR type an item takes, nor the order of elements within an item that is a set… **The types are therefore fixed here.**"

That paragraph is the document's own statement of the test. It is discharged for one of the six constructions audited.

---

## 1. Reconciliation Hash — `{{reconciliation-output}}` (1608–1745), definition at 403–412

Not clean. 13 findings.

**1.1 — BLOCKING — array length is a function of the operator, contradicting the section's own fixed-length claim.**
Item: Verdict Arithmetic and its parameters. Lines `1618`–`1621`:

> "- Verdict Arithmetic as resolved under {{verdict-arithmetic}}, together with every parameter that operator takes -- the threshold for threshold-count, and both the source-class partition and the per-class threshold for source-class-quorum"

One bullet, carrying between one and three values. The encoding rule at `1714`–`1717` says "A Reconciliation Output is encoded as a CBOR array in the field order of this section… so that position is preserved and **the array's length is fixed**." The length is not fixed: conjunction takes no parameters, threshold-count takes one, source-class-quorum takes two. Nothing says whether the parameters occupy their own positions, are nested in a sub-array, or are null-padded. Contrast `{{sealing}}` (`1948`), which writes the same content as a nested pair `[Verdict Arithmetic, its parameters]`, and `{{bra-hash}}` (`3063`), which states "The array has **exactly thirty-one elements**." The Output section states no element count anywhere.
Divergence: reconciliation under `disjunction`. Implementer A encodes 19 elements with the operator at position 7 and no parameter position. Implementer B encodes 20, position 8 being CBOR null. Implementer C encodes 19 with position 7 being `["disjunction", null]`. All three read the same sentence; three different array headers, three Reconciliation Hashes, three ledger indices.

**1.2 — BLOCKING — the source-class partition is an unordered collection of unordered collections, with no ordering rule anywhere.**
Item: the source-class partition, `1620`–`1621`; defined at `552`–`555`: "Source Class: A partition of the Addressed-Registers Identifier Set resolved for the named regimes under {{verdict-arithmetic}}". The Output fixes ordering for four other sets (`1622`, `1624`, `1631`, `1697`, and the Audience Set at `1780`) and for this one fixes nothing — neither the order of classes within the partition nor the order of register identifiers within a class, nor whether a class is named or anonymous.
Divergence: partition {A,B},{C}. Implementer A encodes `[["reg-a","reg-b"],["reg-c"]]`; implementer B encodes `[["reg-c"],["reg-b","reg-a"]]`. Both conform; digests differ. Same defect recurs inside the Policy-Version Hash (finding 2.4).

**1.3 — BLOCKING — "the register signature … replaced by the Signing Input Digest" does not say what is replaced.**
Item: the substitution that was just added. Lines `406`–`408`:

> "and with **the register signature** carried in each Query Binding Record and in each Non-Answer Statement replaced by the Signing Input Digest of that signature"

Reinforced ambiguously at `4137`: "or has its embedded signatures replaced by one", and at `5075`–`5076`: "It now replaces each embedded register signature with that signature's Signing Input Digest." A COSE_Sign1 is `[protected, unprotected, payload, signature]`. "The register signature" reads either as the whole COSE_Sign1 (the artefact) or as its fourth element (the signature bstr). The Query Binding Record's field is described at `1685` as "the register's signed Partial Attestation" — an envelope, not a bstr.
Divergence: implementer A substitutes a 32-byte bstr for the entire COSE_Sign1, giving a 4-element Query Binding Record whose fourth element is `h'…32 bytes'`. Implementer B leaves the envelope and replaces only element 4, giving a 4-element record whose fourth element is a 4-element array. Different bytes, different Reconciliation Hash.
Second-order consequence, which makes this the most severe finding in the construction: under reading B the preimage still contains the COSE_Sign1's **unprotected header bucket**. `{{cbor-cose}}` (`3200`–`3203`) forbids only `alg` and `kid` there; it does not forbid the bucket, and `5100` states the point explicitly — "in the unprotected bucket, which a `Sig_structure` does not cover". An in-transit party can add an unprotected parameter and move the Reconciliation Hash. Reading B therefore fails to achieve the repair's stated purpose while conforming to its text.

**1.4 — BLOCKING — `agent-action-scope-divergence` is a server-recorded axis the Divergence-Axis Set rule never disposes of.**
Item: Server-Recorded Divergence-Axis Set members. `{{terminology}}` (`466`–`471`) lists five server-recorded axes: "which initially are freshness-stale, source-version-skew, register-threshold-divergence, declared-not-determined **and agent-action-scope-divergence**". The Output rule at `1701`–`1706` disposes of four:

> "Of the axes recorded by the server, `freshness-stale` and `declared-not-determined` are per-register and MUST carry a Register Identifier. `source-version-skew` is a relation between two or more registers, and one member MUST be added for each register involved… `register-threshold-divergence` concerns the reconciliation and MUST NOT."

`agent-action-scope-divergence` is absent from the enumeration.
Divergence: an agentic reconciliation under `{{agentic}}` records the axis. Implementer A emits `["agent-action-scope-divergence", "https://register-a.example"]`; implementer B emits `["agent-action-scope-divergence", null]`. The set is sorted over the member encodings, so the whole set's encoding differs. Both conform; digests differ.

**1.5 — BLOCKING — the Reconciliation Identifier's encoding is undefined, and it is claimed to be the reproducible index.**
Item: Reconciliation Identifier, `1612`; construction at `1643`–`1644`:

> "The Reconciliation Identifier is the Claim Hash concatenated with the Policy-Version Hash. It is therefore reproducible from enumerated inputs and satisfies the determinism requirement of {{architecture}}"

No type, no representation. "Concatenated" fixes neither the container (a 64-octet bstr? a two-element array? a 128-character hex tstr?) nor, if textual, the case or the separator. The claim of reproducibility is exactly the claim the ambiguity defeats.
Divergence: implementer A encodes a 64-octet byte string; implementer B, following the URI-safe habit that `{{ledger-read}}` retrieval paths encourage (`GET /arp/outputs/{reconciliation-hash}`, `4606`), encodes a 128-character lowercase-hex text string; implementer C uses uppercase. Three Reconciliation Identifiers, three Reconciliation Hashes, and — because the identifier is also inside the Query Binding preimage (`1213`) and the Non-Answer Statement preimage (`1442`) — three Query Bindings and three register signatures for one question.

**1.6 — BLOCKING — controlled-vocabulary values have no fixed CBOR type in the Output.**
Items: Combined Verdict (`1617`), Answer State (`1665`), Attested Verdict (`1666`), Effective Verdict (`1671`), Non-Answer Reason (`1668`), Re-Typing Ground (`1673`), Aggregation-Method Descriptor (`1633`), Requester-Binding Class (`1630`), each Divergence Axis (`1693`). Every one is drawn from an IANA registry created in `{{iana}}`. Of the eight registries created there, **only** the Ledger Entry Types registry states a CBOR type — "Entry Type values are CBOR text strings" (`4320`–`4321`). The Divergence-Axis registry (`4245`–`4250`), Non-Answer Reasons (`4250`+), Override Grounds (`4296`–`4302`), Re-Typing Grounds (`4304`–`4308`), Verdict-Arithmetic operators (`4310`–`4317`) and Post-Seal Evaluation Qualifiers state registration policy and required documentation and no value type. The IANA text that does fix types (`4331`–`4343`) fixes them for *ledger entry fields* and covers only two of these nine (Aggregation-Method and Requester-Binding-Class Descriptors, "are CBOR text strings").
Divergence: implementer A encodes the Combined Verdict as the text string `"no-match"`; implementer B, reading a registry of four enumerable values as an integer code-point registry — the ordinary CBOR practice — encodes `1`. Both conform. Digests differ. This propagates into the Policy-Version Hash (the operator name), the Non-Answer Statement payload (the reason), and the Post-Seal Record (the qualifier).

**1.7 — BLOCKING — the Projection Record's presence condition admits two states and its members have no order.**
Item: Projection Record, `1677`–`1681`:

> "- Projection Record, comprising the Narrowed-From field of the Per-Register Claim Projection where a projection was transmitted, and the Applied-Parameter Set the register reported where the Answer State is `answered`; **required wherever** a projection was transmitted and either the projection narrowed or the Profile Parameter Set was non-empty"

Three defects in one bullet. (i) "Required wherever X" states when it must be present and not when it must be absent; where a projection was transmitted, did not narrow, and the Profile Parameter Set was empty, implementer A writes CBOR null and implementer B writes a present record with two nulls inside. (ii) The record is a compound with no stated encoding: the array rule at `1714`–`1719` covers the Output array and the Per-Register Result Set ("an array of arrays, each in the field order enumerated above") and stops there — nothing makes the Projection Record a two-element array rather than two adjacent positions. (iii) The Applied-Parameter Set is a set with **no ordering rule**, here or in `{{partial-attestation}}` (`1210`–`1212`), and its members' types are delegated to profiles that never state any (see 6.5).
Divergence: BODS register answering at depth 2 with no narrowing — A emits `null`, B emits `[null, [["max-depth", 2]]]`, C emits `[null, [2]]`. Three digests.

**1.8 — BLOCKING — the Source-Data Version Identifier Set has no ordering rule in any construction that carries it.**
Item: `1676`, "- OPTIONAL Source-Data Version Identifier Set, as attested by that register". `{{source-versioning}}` (`1107`–`1122`) defines each member as "a tuple of the list name … and the state identifier the LIST PUBLISHER assigns" and never orders the set. The IANA header-parameter text (`4226`–`4228`) says only "`arp-source-data-version` is a CBOR array of two-element arrays, each of a list name and that publisher's state identifier" — again no order.
Divergence: a register consulting OFAC-SDN and EU-CFSP. Implementer A orders by consultation order, B by list name, C by whatever its map iterator yields. Three encodings, three Partial-Attestation signatures, three Reconciliation Hashes. This is a set the section knows is set-valued and orders nowhere, while ordering five other sets in the same section.

**1.9 — BLOCKING — the Query Binding Record and the Non-Answer Statement are compounds with no stated encoding.**
Items: `1682`–`1686` and `1686`–`1693`. Each is described with "comprising" and a list of four values, and neither is made a CBOR array anywhere. The Output's array rule (`1714`) reaches two levels only. Implementer A gives the Query Binding Record one Output position holding a four-element array; implementer B gives it four adjacent positions. Different array length, different digest — and the divergence is not detectable by a decoder, because both are well-formed CBOR arrays of nulls and values.

**1.10 — BLOCKING — the Override Record is a nested signed structure the substitution rule does not reach.**
Item: `1635`–`1636` ("OPTIONAL Override Record"); defined at `790`–`804`. It is a six-field structure whose sixth field is a COSE_Sign1 by the authorising operator. The Reconciliation Hash substitution at `406`–`408` names "each Query Binding Record and … each Non-Answer Statement" and **not** the Override Record. So an operator's raw ECDSA signature bytes remain in the Reconciliation Hash preimage — precisely the condition `{{signature-malleability}}` (`4113`–`4123`) measures as "two hundred substitutions verified and two hundred changed the enveloped bytes", and precisely what `5066`–`5076` describes the repair as having swept for. Separately, the Output never says whether it carries the six-element array or a COSE_Sign1 wrapping it.
Divergence: a third party re-encodes `s` to `n - s` on the operator signature in transit. Two readers of one Output compute two Reconciliation Hashes, both believing the ledger index is wrong. Two implementers also differ on the container.

**1.11 — LATENT — the timestamp form is fixed; the CBOR representation is not.**
Items: Reconciliation Timestamp (`1614`), Reliance Horizon (`1615`). Rule at `1731`–`1735`:

> "Every timestamp this document places inside a digest preimage or a signature payload MUST be expressed in the form `YYYY-MM-DDTHH:MM:SSZ`… {{RFC3339}} admits several renderings of one instant, and a preimage that admits several renderings admits several digests."

The paragraph fixes the rendering and not the major type. RFC 8949 tag 0 is defined as exactly a text string in this form, and 4.2.1 does not forbid tags. The IANA ledger text fixes it ("every timestamp is a CBOR text string in the form of {{reconciliation-output}}", `4332`) for ledger entries only.
Divergence: implementer A encodes `0x74 "2026-04-27T19:47:14Z"`; implementer B encodes `0xc0 0x74 "…"`. Both are "expressed in the form". Two-byte-different preimages. Latent rather than blocking only because tag-0 use is uncommon in COSE payloads; nothing in the text excludes it.

**1.12 — LATENT — digests, identifiers and thumbprints in the Output have no fixed type.**
Items: Claim Hash (`1613`), Policy-Version Hash (`1628`, `1674`), Bilateral-Register-Agreement Hash Set members (`1622`), Merkle Root (`1634`), Pattern-Library Version Identifier (`1629`), Register Identifier (`1664`), Reconciliation Nonce (inside `1684`), Audience Member Identifier and Verification Method Reference (`1771`–`1778`). The Pattern-Library Version Identifier has no type and no form anywhere in the document (all 11 occurrences checked). The Verification Method Reference is "the JWK thumbprint, computed as in {{RFC7638}}" (`1774`) — RFC 7638 yields octets and defines a base64url string form, so bstr and tstr are both "computed as in RFC 7638". Audience Member Identifier is "a URI" (`1772`) with no statement that it is a text string, where `{{bra-hash}}` item 6 was careful to say "URI, as a text string" (`3081`).
Divergence: implementer A encodes the thumbprint as `h'…32 bytes'`, implementer B as a 43-character base64url text string. Since the Audience Set is sorted "in bytewise lexicographic order of the deterministic CBOR encoding of the Audience Member Identifier" (`1780`), and the identifier under tag 32 sorts differently from a bare tstr, the *order* diverges as well as the bytes.

**1.13 — LATENT — "OPTIONAL Divergence-Axis Field" is singular in name and set-shaped in practice.**
Item: `1675`. The server's own set is deliberately uniformised — "A uniform two-element member with an explicit null, rather than a member that is sometimes a pair and sometimes a scalar, is what makes the Set's contribution to the Reconciliation Hash determinate" (`1698`–`1700`) — and the register-attested field two lines above it receives no such treatment. Implementer A encodes a scalar axis, B a one-element array. The rationale sentence at `1698` states exactly why that matters and is not applied.

**Clean in this construction, and stated as such:** the Addressed-Registers Identifier Set ordering (`1622`–`1623`, "sorted in bytewise lexicographic order of its UTF-8 encoding"); the Bilateral-Register-Agreement Hash Set ordering (`1624`–`1626`, "sorted in bytewise lexicographic order of the digests themselves"); the Per-Register Result Set ordering (`1631`–`1632`); the Audience Set ordering (`1780`–`1781`); the Server-Recorded Divergence-Axis Set member shape and ordering (`1695`–`1700`); the null-substitution rule for absent fields at the top two levels (`1714`–`1719`); the anti-truncation rule (`1723`–`1728`, "'excluding' means null-substitution at fixed positions and MUST NOT be implemented as truncation"); and the map prohibition (`1719`–`1721`). Those six are correct and each closes a real divergence.

---

## 2. Policy-Version Hash — `{{sealing}}` (1926–1994) and `{{policy-version-determination}}` (3875–3901)

Not clean. 6 findings.

**2.1 — BLOCKING — "threshold parameters" has no structure, no type and no ordering.**
Item: element 4 of the array at `1942`–`1950`. The closing rule is `1951`–`1953`:

> "in that order, the Hash Set sorted in bytewise lexicographic order of the digests and **every other composite element a CBOR array in the order this section states it**."

The section states no order for threshold parameters. `{{verdict-arithmetic}}` (`1537`–`1540`) establishes that thresholds are resolved "keyed on the predicate and the named regimes" — so the element is plausibly a table keyed on (predicate, regime-set) pairs, plausibly the single resolved value, plausibly a list. Nothing says which, nor how the keys are ordered.
Divergence: implementer A commits the resolved integer `3`; implementer B commits the whole policy table as an array of pairs sorted by predicate; implementer C the same table sorted by regime set. Three Policy-Version Hashes for one policy epoch — and every addressed register echoes the value (`900`–`906`), so a deployment running two implementations rejects every attestation with `attestation-unverifiable`.

**2.2 — BLOCKING — "applicable-regimes precedence" and "reconciliation rules identifier" have no defined structure or type.**
Items: elements 3 and 6, `1944`–`1947`. A precedence is an ordering relation; whether it is committed as a sorted array of regime identifiers, an array of ordered pairs, or a map of ranks is unstated, as is the type of a regime identifier (tstr or registry integer).
Divergence: precedence {EU > UK}. Implementer A encodes `["eu","uk"]`; implementer B encodes `[["eu","uk"]]`; implementer C encodes `{"eu":1,"uk":2}` which 4.2.1 then re-sorts. Three digests.

**2.3 — BLOCKING — the Requester-Binding is a three-field composite with a conditional field and no null rule.**
Item: element 10, `1949`. Defined at `699`–`701`: "The Requester-Binding comprises a requester-binding class, the identifier of the accountable principal **where known**, and a reference to the verification method used." Every other array construction in this document states its absent-field rule explicitly — `{{reconciliation-output}}` at `1714`, `{{settlement-ledger}}` at `2105`, `{{projection}}` at `877`, `{{partial-attestation}}` at `1221`, `{{post-seal}}` at `2025`, `{{bra-hash}}` at `3104`. The Policy-Version Hash array is the one construction with a composite element and no such rule.
Divergence: class `agent-unverified`, no principal identifier. Implementer A encodes `["agent-unverified", null, "<ref>"]`; implementer B encodes the two-element `["agent-unverified", "<ref>"]`. Both conform; digests differ; and B's encoding is indistinguishable from a malformed A.

**2.4 — BLOCKING — `[Verdict Arithmetic, its parameters]` inherits 1.1 and 1.2.**
Item: element 7, `1948`. For conjunction and disjunction there are no parameters: is the second element null, an empty array, or is the pair a one-element array? For source-class-quorum the parameters include the partition, which has no ordering rule (finding 1.2). The operator name's own type is unfixed (finding 1.6).

**2.5 — BLOCKING — "reliance interval" has no unit and no type.**
Item: element 8, `1948`. `{{bra-hash}}` was careful to pin every interval it carries — "| 9, 12, 15, 17, 19, 26 | unsigned integer, seconds |" (`3083`) — and this interval is not a `{{bra-items}}` item, so that row does not reach it. `{{reliance-horizon}}` (`1843`–`1849`) and the example (`4498`, "seven days") give no encoding.
Divergence: seven days. Implementer A encodes `604800`; implementer B encodes `7` (days, the unit policy is stated in); implementer C encodes `"P7D"`. Three digests.

**2.6 — LATENT — the array commits to a *reconciliation rules identifier* while the section requires commitment to *reconciliation rules*, defeating the reconstructibility the section asserts.**
Item `1` of the MUST-commit list (`1930`) is "Reconciliation rules"; element 3 of the array (`1944`) is "reconciliation rules identifier". The section then asserts "It MUST be reconstructible under audit from that array" (`1953`–`1954`) and disparages the alternative — "cannot be left to 'a canonical policy state', which earlier revisions were content with and which is **not a preimage**" (`1955`–`1957`). An identifier is not a preimage either. Two deployments that change their reconciliation rules without changing the identifier compute an unchanged Policy-Version Hash, and `{{audit-path}}`'s Reconstruction Proof (`2581`–`2588`) reconstructs the identifier rather than the rules.

**`{{policy-version-determination}}` (3875–3901): CLEAN.** It defines no digest. It pins the source of the value — "MUST determine the Policy Version … from the `arp-policy-version-hash` parameter in the verified protected header of the Signed Statement, and MUST NOT determine it from any retrieval path, query parameter or Transparency Service index entry" (`3877`–`3880`) — and that parameter's type *is* fixed: "`arp-policy-version-hash` is a CBOR byte string" (`4224`). The nesting-and-equality chain it relies on is stated normatively at `3720`–`3727`. No divergence found. Note only that this fixes the type of the header parameter, not of the Policy-Version Hash field inside the Output array (finding 1.12).

---

## 3. Post-Seal Evaluation Record Hash — `{{post-seal}}` (1995–2060)

Not clean. 4 findings.

**3.1 — BLOCKING — one bullet carries two fields, so the record is seven or eight elements.**
Item: `2012`–`2014`:

> "- **the Policy-Version Hash and Pattern-Library Version Identifier** in force at the time of the evaluation, which may differ from those the Output was sealed under"

The encoding rule at `2025`–`2027` — "A Post-Seal Evaluation Record is encoded as a CBOR array in the field order above" — takes "the field order above" from the bullets. One bullet, two named values.
Divergence: implementer A produces a seven-element array with `[pvh, plvi]` nested at position 3; implementer B an eight-element array with them at positions 3 and 4. Both are signed; both verify under their own signature; a receiving implementation decoding positionally reads B's Pattern-Library Version Identifier as A's timestamp. Since the Hash is the Signing Input Digest over the payload, the two records also carry different hashes for identical facts, and the `continuation-post-seal-record` ledger entries that carry them (`2216`–`2218`) are not comparable.

**3.2 — BLOCKING — the record and its signature duplicate the same six fields with no equality rule.**
Items: the record's fields (`2010`–`2023`) and the retrieval check (`2257`–`2266`). The record's last field is "a signature by the reconciliation-server sealing key, a COSE_Sign1 whose payload is the CBOR array of this record with the signature position encoded as CBOR null" (`2021`–`2023`). The retrieval rule then says:

> "A party retrieving a Post-Seal Evaluation Record MUST reconstruct the `Sig_structure` of that record's signature from the protected header and the payload of the retrieved COSE_Sign1, MUST verify that its Signing Input Digest equals the Post-Seal Evaluation Record Hash carried in the entry, MUST verify that signature under the Sealing-Key Identifier the record carries, and MUST discard the record where either check fails."

Both checks run against the COSE_Sign1's own payload. Neither compares the record's outer fields against that payload. `{{partial-attestation}}` states exactly this rule for its own duplicated values — "MUST equal the corresponding payload fields, and an implementation MUST reject an attestation where they differ: a value carried twice with no equality rule is a value an implementation may read either way" (`1243`–`1246`) — and `{{post-seal}}` does not.
Divergence: an operator serves a record whose visible Qualifier is `notarisation-incomplete` and whose signed payload says `attribution-indeterminate`. Both mandated checks pass. Two readers reading the same artefact at different levels reach opposite conclusions. Independently: implementer A reads "the record" as the outer array (media type `arp-post-seal-evaluation-record+cbor`, `4381`) and implementer B as the COSE_Sign1 (`2258`, "the retrieved COSE_Sign1"), so the two do not even agree on what bytes the media type labels.

**3.3 — BLOCKING — the Post-Seal Evaluation Qualifier and the Sealing-Key Identifier have no fixed type.**
Items: `2011` (Qualifier, from the `{{iana}}` registry — see finding 1.6) and `2020` (Sealing-Key Identifier). The Sealing-Key Identifier is defined at `3805`–`3808` as "the pair of that origin and the `kid`" — a pair whose container is unstated and whose `kid` type is unstated (COSE `kid` is a bstr; an origin is a tstr).
Divergence: implementer A encodes position 6 as `["https://arp.example", h'6578…']`; implementer B as `["https://arp.example", "example-sealing-2026-01"]`; implementer C as the tstr `"https://arp.example#example-sealing-2026-01"`. Three payloads, three Signing Input Digests, three ledger entries.

**3.4 — LATENT — timestamp representation, per finding 1.11.**
Item: `2015`, "a Post-Seal Evaluation Timestamp, in the form of {{reconciliation-output}}". Inherits the tag-0 ambiguity.

**Clean in this construction, and stated as such:** the choice to make the Hash a Signing Input Digest rather than a digest over the artefact as served — "Earlier revisions took it over the array in its entirety with the signature included… under a signature primitive whose encoding is not byte-unique the artefact as served is not one byte-string, and a digest over it names whichever copy the reader was handed" (`2028`–`2034`). This correctly resolves property (d): the `Sig_structure`'s protected and payload elements are byte strings taken as transmitted (`{{terminology}}` `421`–`424`, "The protected header is taken as the byte string transmitted and MUST NOT be re-encoded"), and the external AAD is pinned at the zero-length byte string (`422`–`425`). Two verifiers holding the same bytes always agree. The Attribution Account's type is also fixed — "a text string stating which of the two candidate causes were examined" (`2016`–`2018`) — and its presence condition is exact ("present exactly where the Qualifier is `attribution-indeterminate`") with the null rule stated at `2025`–`2027`. Those are the only fully-pinned fields in the record.

---

## 4. Superseding-Reconciliation Hash — `{{settlement-ledger}}` (2221–2226)

**CLEAN at its own level.** All four properties are fixed, by two provisions read together.

Type — `{{iana}}` `4331`: "Every hash is a 32-octet CBOR byte string"; the field is defined as a Reconciliation Hash (`2221`–`2222`, "being the Reconciliation Hash of the Reconciliation Output that supersedes the one this entry concerns"), and the companion Superseding-Entry Sequence Number by `4331`, "every sequence number is a CBOR unsigned integer".

Order — the field's position is fixed by the type-specific enumeration at `2219`–`2226` and by the registration requirement at `4322`–`4324`: "A registration MUST enumerate the fields an entry of that type carries… MUST state their order, since the Self-Entry Hash is taken over that order".

Absence — the condition is exact and the encoding stated: "present exactly where a superseding Output was produced and absent where the supersession is the revocation of a Verified Principal Credential under {{retroactive}}, which supersedes an Output without producing another" (`2222`–`2225`), with `2105`–`2110`: "an absent field -- whether marked OPTIONAL or conditionally absent under a stated condition -- encoded as CBOR null, so that position is preserved and the array's length is fixed by the Entry Type. Absence MUST be encoded and MUST NOT be expressed by a shorter array".

Transmitted-vs-re-encoded — not applicable; the field is a digest value, not a digest construction.

**Caveat, not a finding against this section:** the value it carries is a Reconciliation Hash, so every defect in construction 1 reaches it. A superseding Output whose Reconciliation Hash two implementers compute differently produces a `continuation-supersession` entry that points at nothing, and `2233`–`2236` makes the pointer the sole retrieval path ("No Continuation entry carries a retrieval URI… by Reconciliation Hash for a superseding Output").

---

## 5. Verdict-Arithmetic inputs that are hashed — `{{verdict-arithmetic}}` (1529), `{{verdict-retyping}}` (1480), `{{no-answer}}` (1397)

Not clean. 4 findings. (The two hashed surfaces are the Non-Answer Statement payload and the Output fields these sections populate; the operator tables at `1580`–`1604` are computation rules and enter no preimage.)

**5.1 — BLOCKING — the Non-Answer Statement payload carries three items with no fixed CBOR type.**
Item: `1440`–`1445`:

> "whose payload is the CBOR array
>     `["arp-non-answer-v1", Reconciliation Identifier, Projected Predicate, Subject Reference, Reconciliation Nonce, Non-Answer Reason]`
> encoded under Section 4.2.1 of {{RFC8949}}."

Element count is fixed at six — good. But: the Reconciliation Identifier is unencodable (finding 1.5); the Non-Answer Reason is a registry value with no type (finding 1.6); the Projected Predicate is a Predicate Taxonomy value with no type or lexical form anywhere in the document (`{{terminology}}` `353`–`358` defines the taxonomy and gives examples such as `agent:principal-binding-verifiable`, without stating that a predicate is a text string or whether it is a full path or a leaf token); and the Reconciliation Nonce is "a value of at least 128 bits drawn from a cryptographically secure random source" (`556`–`558`) with no CBOR type and no fixed length.
Divergence: the register signs `["arp-non-answer-v1", h'…64', "sanctions:any-list-match", …, "register-refused"]` while the reconciliation server, verifying, reconstructs `["arp-non-answer-v1", "…hex…", 17, …, 5]`. The signature does not verify, the reason is replaced by `non-answer-unattested` under `1447`–`1449`, and by `1569`–`1573` the Combined Verdict collapses to `indeterminate`. A type disagreement presents as a register refusing to answer.

**5.2 — BLOCKING — the Subject Reference's CBOR type is delegated to the Agreement, and the Agreement declares only its *form*, as a text string.**
Item: Subject Reference, `1442`. `{{projection}}` `861`–`862`: "Subject Reference, in the form the addressed register's Bilateral Register Agreement declares". `{{bra-items}}` item 8 is "The Subject Reference form of {{projection}}" and `{{bra-hash}}` types it "| 5, 8, 16, 20 | text string |" (`3080`) — that types the *declaration of the form*, not a Subject Reference value.
Divergence: an Agreement declaring the form "LEI". Implementer A encodes the value as tstr `"5493001KJTIIGC8Y1R12"`; implementer B as a 20-octet bstr. Both are the declared form. Two Query Bindings (`1211`–`1216`), two Non-Answer Statement payloads, and — because `{{partial-attestation}}` (`1237`–`1240`) requires the server to "recompute the Query Binding from the projection it transmitted and MUST reject an attestation whose Query Binding does not match" — a rejection with `attestation-unverifiable`. This is not closed by the parties being bilateral: `1250`–`1255` says the Query Binding Record exists "so that a relying party or auditor can recompute the binding", and a relying party is not a party to the Agreement.

**5.3 — BLOCKING — the re-typed values, grounds and answer states that `{{verdict-retyping}}` writes into the Output have no type.**
Items: `{{verdict-retyping}}` requires the server to "record the attested value, the re-typed value and the ground on which it re-typed in the Per-Register Result Set" (`1485`–`1487`), landing in Output fields `1666`, `1671`, `1673`. The Re-Typing Grounds registry (`4304`–`4308`) states initial values and no CBOR type. Per finding 1.6.

**5.4 — LATENT — `non-answer-unattested`'s attestation class is never registered, so the Non-Answer Statement's presence condition is undecidable for it.**
Item: `1447`–`1449`, "Where a register-attested reason is recorded without a Statement, or with one that does not verify, the reason MUST be replaced by `non-answer-unattested`." The Output field is "present exactly where the Answer State is `not-answered` and the Non-Answer Reason is register-attested" (`1686`–`1687`), and `1428`–`1435` classifies the reasons in prose — "`register-refused` is register-attested. `attestation-stale` and `attestation-unverifiable` are server-observed… The remainder are server-observed" — where `non-answer-unattested` falls in "the remainder" only by inference from a list it was appended to. Implementer A treats it as server-observed and nulls the field; implementer B retains the non-verifying Statement it holds. Different arrays.

**Clean in these sections, and stated as such:** the Per-Register Result Set completeness rule — "The Per-Register Result Set MUST carry an entry for every addressed register" (`1404`) — which fixes the entry count; the domain-separation string and fixed element count of the Non-Answer Statement payload (`1440`–`1443`); the exclusion of the Non-Answer Reason from the arithmetic (`1462`–`1466`); and the deterministic derivation rules for `freshness-stale` (`1470`–`1471`), `source-version-skew` (`1702`–`1704`, "one member MUST be added for each register involved, so that the set is a determinate function of the inputs rather than a choice between them") and `declared-not-determined` (`1063`–`1067`). The `partial-match`-not-admitted collapse at `1606`–`1608` is total and leaves no undefined case.

---

## 6. The Agreement Hash — `{{bra-hash}}` (3059–3131) and `{{bra-items}}` (2796–2887)

**The best of the six by a wide margin.** It is the only construction that states the test and works through it: element count fixed ("The array has **exactly thirty-one elements**", `3063`); a per-item type table (`3074`–`3091`); a global set-ordering rule with its two exceptions named and justified (`3092`–`3103`); an absence rule with the closed list of items to which it applies (`3104`–`3111`, "**Items 14, 25, 27 and 29 are the only items that may be absent**… Encoding an absent per-subject ceiling as null, as zero, or by omitting the element are three readings of one sentence, and all three produce different Agreement Hashes"); and an explicit prohibition on deriving the order from anything else (`3113`–`3118`). Items 4, 5, 6, 8, 9, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 26, 28, 29 and 31 are fully pinned and I can construct no divergence for them.

The residue is that the table pins the *container* of several items and not the *elements inside them*. 6 findings.

**6.1 — BLOCKING — item 30 has no structure at all.**
Item: `2860`–`2865`:

> "30. The regulator read keys of {{read-signing}}, **or** the means by which they are resolved from the trust anchor of item 5, **together with** the means by which key material for items 21, 22, 27 and 30 is retrieved."

The table gives it "| 1, 2, 21, 27, 30 | array, sorted in bytewise lexicographic order of the deterministic CBOR encoding of each element |" (`3077`). One item, a disjunction of two incommensurable things plus a conjoined third, encoded as a flat sorted array. Nothing says whether it is one array of keys, a two-element array of (keys-or-means, retrieval-means), or a discriminated union; nothing types "a means"; and sorting a heterogeneous array by CBOR encoding interleaves keys with means.
Divergence: an Agreement resolving regulator keys from the trust anchor and retrieving item-21/22/27/30 material over a well-known URI. The reconciliation server encodes `["https://…/regulator-keys", "https://…/keys"]`; the Register Operator encodes `[["resolve-from-anchor"], ["https://…/keys"]]`. Different Agreement Hashes from identical negotiated terms — which, by `3125`–`3127` and `{{agreement-drift}}`, suspends reconciliation against the register. The section names this outcome itself at `3071`–`3073`: "Since {{agreement-drift}} suspends reconciliation on a deviation, that is an outage and not a warning."

**6.2 — BLOCKING — the cryptographic-primitive identifier type is fixed for item 4 and not for items 2 and 3.**
Items: `2802`–`2806`. Item 4's row says "the sorted array of **COSE algorithm identifiers** of the encryption construction" (`3079`). Item 2's row says only "array, sorted…" (`3077`), and item 3's says "three-element array, in the class order of {{crypto-upgrade}}, each element that class's equivalence list" (`3078`). `{{crypto-upgrade}}` (`2745`–`2752`) names primitives as `ML-KEM {{FIPS203}}` and `ML-DSA {{FIPS204}}` — prose names, not code points.
Divergence: implementer A encodes item 2 as `[-7, -8, -35]` (COSE algorithm identifiers, by analogy with item 4); implementer B as `["ES256", "EdDSA", "ML-DSA-65"]`. Both conform. And note the sort inverts between them: COSE algorithm identifiers are negative integers, whose deterministic encodings sort ascending as the values descend, so A and B do not even agree on member order. Item 3 is doubly exposed, since it is exempt from sorting and its preference order is the semantics ("Sorting either would discard the meaning it carries", `3101`).

**6.3 — BLOCKING — item 10's inner values are typeless, and item 10 is explicitly exempt from the set-sorting rule while containing sets.**
Item: `2815`–`2820`, and `3086`: "| 10 | two-element array: the profile identifier as a text string, and the array of profile-obliged values **in the order that profile enumerates them** |", with `3099`–`3102`: "Items 3 and 10 are the exceptions… because each is a **sequence** rather than a set". The profiles in `{{format-profiles}}` state which values an Agreement must supply and never their types or their enumeration order:
- `arp-profile-bods` (`1071`, `1097`–`1099`): "MUST supply the maximum chain depth" and "MUST supply the threshold its permitted predicates assume" — stated four paragraphs apart, with no numbering. A threshold is a percentage: integer 25, decimal fraction 0.25, or text "25%"?
- `arp-profile-customs-wco` (`1058`–`1074`): "MUST supply, **for each permitted predicate**, whether it ranges over a declared fact or over a determined one" — a per-predicate mapping, i.e. a set, sitting inside an item the document has just exempted from sorting; plus a named CCL release and "the declaration types the register answers over", another unordered set.
- `arp-profile-sanctions-consolidated` (`1093`–`1097`): "MUST supply **the set of lists** the register consults and, for each, the identifier by which the register expresses that list's state" — a set of pairs, again inside the sorting-exempt item.

Divergence: a customs Agreement over four permitted predicates. Implementer A orders the declared/determined mapping by predicate; implementer B in the order the predicates appear in item 1 (which *is* sorted, by a different key). Different Agreement Hashes. This is precisely the failure `3096`–`3098` articulates — "an unordered set gives one Agreement as many hashes as it has permutations" — occurring inside the two items exempted from the rule that closes it.

**6.4 — BLOCKING — item 25's decimal fraction has multiple deterministic encodings of one value.**
Item: `3089`: "| 25 | two-element array: the reserved proportion as a **CBOR decimal fraction**, and the per-principal sub-budget as an unsigned integer |". RFC 8949 §3.4.4 defines tag 4 as `[exponent, mantissa]`, and §4.2.1 canonicalises the encoding of each integer inside it but does not canonicalise the pair: `4([-1, 1])` and `4([-2, 10])` both denote 0.1 and both are valid deterministic encodings. The table does not require a normalised (minimal-exponent, or fixed-exponent) form.
Divergence: reserved proportion 10%. Implementer A encodes `4([-1, 1])` (five bytes); implementer B `4([-2, 10])`. Both conform to 4.2.1 and to the table. Different Agreement Hashes. This is the cleanest instance in the document of "4.2.1 fixes how a value encodes" being false for a tagged composite.

**6.5 — BLOCKING — item 27's Witness Entry elements and item 21's Audit Identity elements have no fixed types.**
Items: `2857` (27) and `2851` (21). `{{witness-entries}}` fixes the shape well — "Each Witness Entry is a CBOR array of exactly three elements, in this order and not nested" (`2900`–`2901`), with the non-nesting rationale at `2907`–`2912` — but element 1 is "the Audience Member Identifier, as {{audience}} defines it", element 2 "the Verification Method Reference, as {{audience}} defines it", element 3 "an **Operating-Party Identifier**: a URI naming the party that controls the witness" (`2902`–`2905`). Per finding 1.12: `{{audience}}` types neither the identifier (a URI: tstr or tag 32?) nor the thumbprint (RFC 7638 octets or base64url string?). Item 21's Audit Identity is "an identifier and a key thumbprint, in the form {{audience}} uses for an Audience Member" (`2570`–`2572`) — the two-element array shape is thereby fixed, and the element types are not.
Divergence: implementer A encodes a Witness Entry as `["https://w.example", h'…32', "https://op.example"]`; implementer B as `[32("https://w.example"), "NzbLs…", 32("https://op.example")]`. Different Agreement Hashes, and — because item 27 is sorted by the deterministic CBOR encoding of each entry and tag 32 changes the leading byte — different member order. This also cross-cuts `{{witness-discovery}}` (`3027`–`3037`), which requires the Policy Parameters Document to carry "the effective Witness Set" for relying-party evaluation: a relying party comparing the document's entries against a quorum computes distinctness over whichever encoding it was served.

**6.6 — LATENT — item 1's element type; and the empty-sub-element contradiction.**
Item 1 is "The permitted-predicate set of {{projection}}" (`2801`), sorted but untyped; predicates have no fixed CBOR type (finding 5.1). Separately, `3104`–`3110` reads "An item that is absent, inapplicable or empty is encoded as CBOR null… Every other item MUST be present and MUST NOT be null" — applied to a *sub-element*, an empty equivalence list inside item 3 is both "empty" (→ null) and part of an item that "MUST NOT be null". Item 7's nested "sorted set for it" per jurisdiction has the same question. Implementer A writes `[]`, implementer B writes `null`.

---

## Findings table, most severe first

| # | Sev | Construction | Item | § / line | Divergence |
|---|---|---|---|---|---|
| 1.3 | BLOCKING | Reconciliation Hash | "the register signature … replaced by the Signing Input Digest" | `{{terminology}}` 406–408 | A replaces the whole COSE_Sign1 with a 32-byte digest; B replaces only the signature bstr, leaving the uncovered unprotected header in the preimage and defeating the repair |
| 1.1 | BLOCKING | Reconciliation Hash | Verdict Arithmetic + parameters | `{{reconciliation-output}}` 1618–1621 | Array is 19, 20 or 21 elements depending on operator and reading, contradicting "the array's length is fixed" at 1716 |
| 6.1 | BLOCKING | Agreement Hash | Item 30, regulator read keys / means | `{{bra-items}}` 2860–2865; table 3077 | Disjunction-plus-conjunction encoded as one flat sorted array with no stated structure; server and Register Operator compute different hashes from identical terms → drift suspension |
| 1.5 | BLOCKING | Reconciliation Hash (+ Query Binding, Non-Answer Statement) | Reconciliation Identifier | 1643–1644 | "Concatenated" fixes neither container nor representation: 64-octet bstr vs 128-char hex tstr vs 2-array; the value claimed to be "the reproducible index" |
| 1.6 | BLOCKING | all four hashed structures | every controlled-vocabulary value | 1617, 1665–1673, 1630, 1633; registries 4245–4317 | Seven of eight IANA registries state no CBOR type; A encodes `"no-match"`, B encodes an integer code point |
| 3.1 | BLOCKING | Post-Seal Record Hash | Policy-Version Hash + Pattern-Library Version Identifier in one bullet | `{{post-seal}}` 2012–2014 | Seven-element vs eight-element record; positional decoders misread each other's fields |
| 3.2 | BLOCKING | Post-Seal Record Hash | record fields vs signed payload | 2010–2023, 2257–2266 | Same six fields carried twice with no equality rule (cf. 1243–1246 for Partial Attestations); an operator serves a record whose visible Qualifier differs from the signed one and both mandated checks pass |
| 6.3 | BLOCKING | Agreement Hash | Item 10, profile-obliged values | 2815–2820; 3086, 3099–3102 | Item exempt from set-sorting yet contains per-predicate and per-list sets; profiles state no order and no types (threshold as int / decimal / "25%") |
| 6.4 | BLOCKING | Agreement Hash | Item 25, reserved proportion | 3089 | `4([-1,1])` and `4([-2,10])` both denote 0.1 and both satisfy 4.2.1; the table requires no normalised form |
| 1.4 | BLOCKING | Reconciliation Hash | `agent-action-scope-divergence` | 466–471 vs 1701–1706 | Five server-recorded axes defined, four disposed of; A pairs it with a Register Identifier, B with null |
| 1.2 / 2.4 | BLOCKING | Reconciliation Hash, Policy-Version Hash | source-class partition | 1620–1621, 552–555, 1948 | Unordered collection of unordered collections; no ordering rule anywhere, while five sibling sets are ordered |
| 2.1 | BLOCKING | Policy-Version Hash | "threshold parameters" | 1945, 1951–1953 | Resolved scalar vs whole policy table vs table sorted three ways; every register echoes the resulting hash |
| 1.8 | BLOCKING | Reconciliation Hash | Source-Data Version Identifier Set | 1676, 1107–1122, 4226–4228 | Set of (list, state) tuples with no ordering rule in the Output, in `{{source-versioning}}`, or in the COSE header parameter |
| 5.2 | BLOCKING | Non-Answer Statement, Query Binding | Subject Reference | 861–862; item 8 at 2814, 3080 | Agreement declares the *form* as a text string, not the value's CBOR type; A tstr, B bstr → Query Binding mismatch → `attestation-unverifiable` |
| 1.7 | BLOCKING | Reconciliation Hash | Projection Record | 1677–1681 | "Required wherever" states no absence rule; compound has no stated array encoding; Applied-Parameter Set has no ordering |
| 1.9 | BLOCKING | Reconciliation Hash | Query Binding Record, Non-Answer Statement | 1682–1693 vs 1714–1719 | Four-value compounds never made arrays; A nests, B flattens; array length differs |
| 1.10 | BLOCKING | Reconciliation Hash | Override Record | 1635–1636, 790–804, vs 406–408 | Substitution rule names only the Query Binding Record and Non-Answer Statement, leaving a raw operator ECDSA signature in the preimage; container unstated |
| 6.2 | BLOCKING | Agreement Hash | Items 2 and 3, primitive identifiers | 2802–2806; 3077–3078 | Item 4 says "COSE algorithm identifiers", items 2 and 3 say nothing; A `[-7,-8]`, B `["ES256","EdDSA"]`, with inverted sort order |
| 6.5 | BLOCKING | Agreement Hash | Items 21 and 27, Audit Identity / Witness Entry elements | 2851, 2857, 2570–2572, 2900–2905, 1772–1778 | URI as tstr vs tag 32; RFC 7638 thumbprint as octets vs base64url; changes both bytes and sorted member order |
| 2.2 | BLOCKING | Policy-Version Hash | applicable-regimes precedence, reconciliation rules identifier | 1944–1947, 1951–1953 | "The order this section states it" — the section states none; array vs pair-array vs map |
| 2.3 | BLOCKING | Policy-Version Hash | Requester-Binding composite | 1949, 699–701 | Conditional "where known" field with no null rule — the one array construction in the document lacking one |
| 2.5 | BLOCKING | Policy-Version Hash | reliance interval | 1948 | No unit, no type: `604800` vs `7` vs `"P7D"`; the `{{bra-hash}}` seconds rule does not reach it |
| 3.3 | BLOCKING | Post-Seal Record Hash | Qualifier, Sealing-Key Identifier | 2011, 2020, 3805–3808 | "The pair of that origin and the `kid`" — container and `kid` type unstated (COSE `kid` is a bstr) |
| 5.1 | BLOCKING | Non-Answer Statement | Projected Predicate, Nonce, Reason, Identifier | 1440–1445 | Element count fixed, four of six element types not; a type disagreement presents as a register refusal and collapses the verdict to `indeterminate` |
| 5.3 | BLOCKING | Reconciliation Hash | attested / effective verdict, Re-Typing Ground | 1485–1487, 1666–1673, 4304–4308 | Per 1.6 |
| 1.11 / 3.4 | LATENT | Reconciliation Hash, Post-Seal Record | every timestamp | 1731–1735, 2015 | Rendering fixed, major type not: bare tstr vs RFC 8949 tag 0 |
| 1.12 | LATENT | Reconciliation Hash | digests, identifiers, thumbprints, Pattern-Library Version Identifier | 1613–1634, 1771–1778 | No type fixed for the Output (only for ledger entries at 4331); Pattern-Library Version Identifier untyped in all 11 occurrences |
| 5.4 | LATENT | Reconciliation Hash | `non-answer-unattested` attestation class | 1428–1435, 1447–1449, 1686–1687 | Class assigned only by inference; A nulls the Statement field, B retains the non-verifying Statement |
| 1.13 | LATENT | Reconciliation Hash | register-attested Divergence-Axis Field | 1675 vs 1698–1700 | Scalar vs one-element array; the uniformity rationale two lines below is not applied to it |
| 2.6 | LATENT | Policy-Version Hash | rules *identifier* vs rules | 1930 vs 1944, 1953–1957 | Section requires reconstructibility from the array and commits to an identifier, not a preimage |
| 6.6 | LATENT | Agreement Hash | Item 1 element type; empty sub-elements | 2801; 3104–3110 | Predicates untyped; an empty equivalence list is both "empty" (→ null) and inside an item that "MUST NOT be null" |

**Clean results, for the record:** `{{policy-version-determination}}` (3875–3901) — no divergence found; the Superseding-Reconciliation Hash field itself (2221–2226) — all four properties fixed by 2222–2225, 2105–2110 and 4331; and within construction 1, the six ordering/null/anti-truncation rules listed at the end of that section, each of which closes a real divergence. `{{bra-hash}}` discharges the test for 20 of its 31 items and is the model the other five constructions do not follow.agentId: a51de7b469213c065 (use SendMessage with to: 'a51de7b469213c065', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 151599
tool_uses: 33
duration_ms: 616695</usage>