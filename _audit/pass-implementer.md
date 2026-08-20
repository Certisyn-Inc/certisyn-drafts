# Independent-Implementer Review: draft-hillier-scitt-arp

**Posture:** I have only this file. Every point below is a place where I stopped, could not proceed from the text, and would have had to invent something. Where two inventions produce different bytes or different behaviour, I say which.

**Overall:** the document is unusually strong in the places it has been attacked before — the Merkle construction, the Signing Input Digest, the `404`/normalised-observation rule, the Agreement Hash type table, the ledger chaining, the SCITT polling binding. It is weakest in exactly the places no reviewer has yet forced it to be concrete: **the shape of the Canonical Claim, the shape of the Reconciliation Output, the predicate taxonomy, and the selection of registers.** Those four gaps mean I cannot compute the Claim Hash, the Reconciliation Hash, the projection or the register set — i.e. I cannot produce any artefact this protocol names.

---

## 1. Terms I cannot resolve

### T-1 "authority origin" — BLOCKING
Used at L1622, L2167, L2182, L2836, L3287, L3290, L3793, L4335 ("Addressed-Registers Identifier Set, each member an authority origin, sorted in bytewise lexicographic order of its UTF-8 encoding").
I must guess between: RFC 3986 §3.2 *authority* (`register-a.example:443`), RFC 6454 serialised origin (`https://register-a.example`), or an origin-with-path (`https://register-a.example/`). The document's own example uses `"https://register-a.example"` (L4514) with no trailing slash and `https://ts.example/` (L4539) **with one**, in two fields of the same entry family.
Divergence: this string is (a) a bytewise sort key for a signed set, (b) percent-encoded into a path segment (L3290), (c) compared for equality against the origin component of a Sealing-Key Identifier (L3836-3839). Implementer A rejects every Output implementer B seals, and their ledger entries hash differently over identical facts.

### T-2 "Policy-Version Identifier" — BLOCKING
L622: "an identical Pattern-Library Version Identifier, and an identical Policy-Version Identifier, the system MUST produce…". The string appears **exactly once in the document**. It is not a field of any structure, not an element of the Policy-Version Hash preimage (which instead carries a "reconciliation rules identifier", L1945), and not defined in {{terminology}}.
Guess A: it is the Policy-Version Hash — but then the determinism clause is circular, because the Hash commits to the Requester-Binding and the agreement hashes which are separately enumerated. Guess B: it is an opaque epoch label in the policy-epoch store — then it is an input no artefact carries and no conformance test can hold fixed. I cannot write the determinism test either way.

### T-3 "Predicate Taxonomy" — BLOCKING
Defined at L330 as "a controlled hierarchical classification of predicates" and then relied on by the whole projection function: "walking the Predicate Taxonomy upward" (L849), "more than one such Predicate at the same taxonomic distance" (L851), "reaches the taxonomy root" (L852).
Nothing states: the syntax of a predicate string; the parent relation in the general case; what "taxonomic distance" is; where the taxonomy is published (the IANA section at L4210-4344 requests eleven registries and **no predicate registry**); or how a taxonomy can present two parents at equal distance (a hierarchy cannot, so this is either a DAG or dead text).
Divergence: given `sanctions:eu:consolidated:designation` and a permitted set `{sanctions:designation}`, implementer A (colon-segment truncation) projects; implementer B (no defined parent, so no ancestor) fails `projection-unsupported`. Different Non-Answer Reason, different Combined Verdict, different sealed artefact.

### T-4 "predicate class" — BLOCKING
L741 "The Agent-IFF policy in force declares, per predicate class…"; L3258 "refuses the requester outright for the predicate class". Undefined. The non-normative example (L4640) says "the Agent-IFF policy for the `sanctions:` class", implying the first colon-segment, but that is in an appendix marked illustrative.
Divergence: whether a given ENEMY request is refused with `403` or admitted as advisory turns on a term with no definition.

### T-5 "Pattern-Library Commitment Hash" — LATENT
L4042: "The Pattern Library MUST be bound to a Pattern-Library Commitment Hash." One occurrence in the document. No construction, no preimage, no carrier field, no stated relationship to the Pattern-Library Version Identifier that is actually committed to the Policy-Version Hash. It is a MUST I can satisfy by computing any digest over anything and never emitting it.

### T-6 "Pattern-Library Version Identifier" — BLOCKING
Nine occurrences, never given a type or format, yet it is element 5 of the Policy-Version Hash array (L1946), a field of the Reconciliation Output (L1629), a field of the Post-Seal Evaluation Record (L2020) and a field of the Sweep Statement (L2669). Text string? Digest? Integer? Two implementations that agree on the policy state compute different Policy-Version Hashes.

### T-7 "reconciliation rules identifier", "threshold parameters", "applicable-regimes precedence" — BLOCKING
Elements 3, 4 and 6 of the Policy-Version Hash preimage (L1944-1950). "applicable-regimes precedence" occurs **once in the document**. None has a type, a structure or a content rule. {{bra-hash}} gives a full CBOR type table for the Agreement Hash precisely because "Determinism under Section 4.2.1 of RFC 8949 … does not fix which CBOR type an item takes" (L3064-3068) — that reasoning applies verbatim here and was not applied.

### T-8 "Requester-Binding" as a hash element — BLOCKING
L1948 puts "Requester-Binding" in the Policy-Version Hash array. L704-707 says it "comprises a requester-binding class, the identifier of the accountable principal where known, and a reference to the verification method used". No encoding, no order, no null rule, no statement of what "a reference to the verification method" is (a thumbprint? a URI? a text label?). The Output carries only the *class* (L1630), so the other two members exist only inside this digest — the one place where nobody can check my guess and everybody must match it.

### T-9 "reliance interval" — BLOCKING
Element 7 of the Policy-Version Hash (L1947), a field of the Policy Parameters Document (L3341), and the addend that produces the Reliance Horizon (L1845). Unit and type never stated. Seconds as an unsigned integer (as items 9/12/15/17/19/26 of the Agreement are, L3110)? An ISO 8601 duration string? The example says "seven days" (L4497). Two implementations sign two different Policy Parameters Documents and compute two different Policy-Version Hashes over the same policy.

### T-10 "Source Class" / "source-class partition" — BLOCKING
L479 defines a Source Class as "a partition of the Addressed-Registers Identifier Set resolved for the named regimes". The partition is a carried Output field (L1616-1619, "both the source-class partition and the per-class threshold") with no structure and no type. Array of arrays of register origins? Map from class name to member set? It is inside the Reconciliation Hash preimage.

### T-11 "deployment" — LATENT
The Deployment Blinding Value is "constant for the life of the deployment" (L1966). A deployment is never defined: one authority origin? one operator? one policy-epoch store? Two servers under one operator sharing a Value produce comparable Claim Hashes; not sharing it, they do not. Nothing says which is conforming, and {{construction-distinctness}} L4930 relies on cross-deployment incomparability being guaranteed.

### T-12 "authenticated human or institutional operator" — BLOCKING
L703. This is the discriminator for class `human-operator`, which is written into every ledger entry (L2172) and into the Policy-Version Hash. Every requester signs under {{read-signing}} with a JWK thumbprint `keyid` (L3329). Nothing states how a server maps an incoming signed request to `human-operator` rather than `agent-key-verified`. Guess A: enrolled principals are human-operator. Guess B: absence of a `Signature-Agent` header is human-operator. The two produce different ledger records and different budget partitions (L3968-3974).

### T-13 "genuinely verified declared bot" — LATENT
L312 and L733, as one of three ways to be FRIENDLY. No definition, no reference, no verification procedure. It is one third of a determination the document calls "deterministic" (L323).

### T-14 "a Verified Principal Credential whose status was checked" — BLOCKING
L705 requires a status check for class `agent-verified`; L316-318 defines a VPC as "verifiable without contacting the credential issuer in the reconciliation hot path". No status mechanism is named (no status list, no CRL, no expiry rule), yet revocation of a VPC is a retroactive-evaluation trigger (L2629, L2645) and a supersession cause. I cannot implement the check or the trigger.

### T-15 "the narrowing or substitution each concerns" — LATENT
L768, inside the Remediation Advisory field list. No type. See V-8.

### T-16 "subpoena-grade audit trail" — LATENT
L2492. Not a property with an implementable meaning; the audit trail's format, retention and read interface are otherwise undefined except for a retention pointer at L3620.

### T-17 "Register Identifier" vs origin — LATENT
"Register Identifier" is the sort key of the Per-Register Result Set (L1631), a path segment (L3378) and the second element of every Server-Recorded Divergence-Axis member (L1690). Only at L3820 ("A Register Identifier is an origin") is it tied to the Addressed-Registers members. Combined with T-1, I cannot tell whether the two strings are byte-identical.

**Complete as written:** "material change" (L2632-2637), "Signing Input Digest" (L400-415), Operating-Party Identifier distinctness including normalisation (L2921-2926), Source-Version Skew (L500-506).

---

## 2. Values I cannot construct

### V-1 The Canonical Claim has no schema — BLOCKING (worst finding in the document)
L668-682 lists six fields and then: "Claim Hash: the SHA-256 digest over the deterministically encoded CBOR array `["arp-claim-v1", Deployment Blinding Value, canonical serialisation]`, where the canonical serialisation is the RFC 8785 form of the preceding fields as {{terminology}} constructs it".
RFC 8785 serialises a **JSON value**. The document never states the JSON object: no member names, no nesting, no types. {{terminology}} L332-352 specifies with great care the *order of operations* over member names (NFC before sort, UTF-16 code units) and never names a single member.
Divergence: `{"subject":"corp:EX:1","predicate":"sanctions:any-list-match",...}` vs `{"subjectIdentifier":…,"pred":…}` — different JCS bytes, different Claim Hash, different Reconciliation Identifier, different ledger index, different retroactive-evaluation key. Nothing else in the protocol survives this.

### V-2 The Evidentiary Provenance Manifest cannot be in a JCS preimage — BLOCKING
It is one of "the preceding fields" of V-1, but L686-690 says it "MAY be carried in any COSE-enveloped evidence structure; the container form is an interop convenience and does not alter the Claim Hash". JCS has no byte-string type. So either (a) the manifest is JSON and the COSE sentence is wrong, or (b) it is COSE and must be base64'd into JSON under an unstated encoding, or (c) it is excluded from the preimage — which contradicts "the preceding fields". Three readings, three different Claim Hashes.

### V-3 The Reconciliation Output has no CBOR type table — BLOCKING
L1610-1640 enumerates the fields and L1712 fixes the field **order**; nothing fixes the **types**. {{bra-hash}} L3064-3068 explains exactly why that is fatal and supplies a table for the Agreement; {{iana}} L4325-4344 supplies one for ledger entries; the Output — whose digest is the ledger index, the retrieval key and the thing every relying party recomputes — gets neither.
Unfixed, at minimum: Combined Verdict (text string `"match"` or an integer enum?); Answer State; Non-Answer Reason; Divergence Axis; Re-Typing Ground; Aggregation-Method Descriptor; Requester-Binding Class; Reliance Horizon (pinned text form or epoch seconds?); the Sealing-Key Identifier pair; the Verdict Arithmetic **and whether it plus its parameters is one array element or two** (L1615-1619 reads as one bullet; the Policy-Version Hash writes the same pair as `[Verdict Arithmetic, its parameters]`, L1946).
Divergence: every one of these changes the Reconciliation Hash. Two conforming implementations index the same reconciliation at two different ledger keys.

### V-4 Query Binding element types — BLOCKING
L1213: `["arp-query-binding-v1", Reconciliation Identifier, Projected Predicate, Subject Reference, Reconciliation Nonce]`. This digest is computed **independently by the register and re-computed by the server** (L1246-1249), and a mismatch is `attestation-unverifiable`. Yet: the Reconciliation Identifier's type is undefined (see V-5); the Subject Reference's form is "as the Bilateral Register Agreement declares" (L861) with no requirement that the Agreement pin a CBOR type (item 8 is fixed as a *text string* at L3106 — but that fixes the *form descriptor*, not the value); the Nonce is bytes or base64url text, unstated.
Divergence: register encodes the nonce as a byte string, server as text; every attestation is rejected as unverifiable. This is the single most likely field-level interop failure in the document.

### V-5 "Reconciliation Identifier is the Claim Hash concatenated with the Policy-Version Hash" — BLOCKING
L1643. Concatenated as raw octets into a 64-byte byte string, or as two base64url texts, or as a delimiter-joined string? The document elsewhere refuses exactly this looseness: "Framing the blinding value as an array element rather than concatenating it is what stops two deployments differing on order, separator or length prefix" (L681-683) — and then concatenates.
It is also a path segment: L3378 `GET /arp/reconciliations/{reconciliation-identifier}/…` while L3288 says only "every **hash** appearing in a path segment is base64url-encoded without padding". A concatenation of two hashes may or may not be "a hash".

### V-6 Narrowed-From has no structure — BLOCKING
L854 "The narrowing operation MUST be recorded in the Narrowed-From field"; L864 lists it as a projection field; L1677 carries it into the Projection Record inside the Reconciliation Hash preimage; L1062 requires the server to **derive** the `declared-not-determined` Divergence Axis *from* it.
Is it the original predicate (text)? A pair of `[from, to]`? A depth integer? A narrowing-kind descriptor? I cannot encode the projection the register decrypts, cannot encode the Output, and cannot implement the derivation rule.

### V-7 Profile Parameter Set / Applied-Parameter Set have no structure — BLOCKING
L870-872 and L1209-1211. Both are inside signed payloads (the projection and the Partial Attestation) and one is inside the Reconciliation Hash preimage. Map or array of pairs? Ordered how? A CBOR map would be re-sorted under §4.2.1 and override any intended order — the same hazard the document flags for the Output (L1714-1716) and does not flag here. `{{profile-bods}}` L992-994 requires "the depth at which the register answered" to be "reported in the Applied-Parameter Set", with no key name.

### V-8 Remediation Advisory arity — BLOCKING
L763-775: three bullets, of which bullet 2 carries *two* things ("the identifiers … and the narrowing or substitution each concerns") and bullet 3 carries a value that is one of three different kinds "respectively". "It is encoded as a CBOR array in that field order … absent fields as CBOR null."
Is the array 3, 4, 5 or 6 elements? And L3256 says the `403` carries "a Remediation Advisory **whose sole content is** the Agent-IFF ground", which cannot be the same fixed-length array. The Advisory is the only artefact a refused requester receives and it travels in a signed payload; two implementations produce mutually unparseable refusals.

### V-9 Sealing-Key Identifier / `kid` encoding — BLOCKING
L3805-3807: "The Sealing-Key Identifier is the pair of that origin and the `kid`; where this document requires a `kid` to equal the Sealing-Key Identifier, it is the `kid` component that is compared." COSE `kid` (label 4) is a byte string; a JWK thumbprint (L4353) is base64url text. Is the `kid` the raw 32 SHA-256 octets, the ASCII of the base64url form, or something else? The same value is also a URL path segment `/.well-known/arp-sealing-keys/{kid_value}` (L3804). And the *pair* has no encoding as an Output field or Post-Seal Record field.
Divergence: signature verification fails between implementations that agree on everything else.

### V-10 "URI form of the verified signing key's thumbprint" — BLOCKING
L1804-1805. No scheme is named. `urn:ietf:params:oauth:jwk-thumbprint:sha-256:…`? `did:key:…`? A bare base64url string is not a URI. This value is an Audience Member Identifier, so it is inside the Audience Set, which is inside the Reconciliation Hash preimage and is the **sort key** for the Set (L1783). Every reconciliation by an unverified agent hashes differently between implementations.

### V-11 Audience Member Identifier comparison — BLOCKING
L1774: "a URI, in the same identifier space a Requester-Binding uses for an accountable principal." No normalisation, no comparison rule — while {{witness-entries}} L2921 pins RFC 3986 §6.2.2/6.2.3 for Operating-Party Identifiers "Without a stated normalisation `https://acme.example` and `https://ACME.example/` are distinct to one implementation and identical to another". The identical hazard governs *entitlement* here: whether a member is admitted to `GET /arp/outputs/{hash}` or gets the `404` of L3564. The example uses `org:ACME:operator:jdoe` (L4636), which is not a URI under any registered scheme.

### V-12 Reconstruction Proof — BLOCKING, and circular
L2581-2586: "a keyed digest, computed as HMAC-SHA-256 under the Deployment Blinding Value over the disclosed elements, which the auditor recomputes only if it is also given the Value, and otherwise compares against the Reconstruction Proof the server returns beside the Output".
No encoding or ordering for "the disclosed elements" (so no two implementations compute one value), and the fallback is self-defeating: the auditor compares the server's value against the server's value. The entire audit path — cited eight times as the justification for other requirements — reduces to a value the auditor cannot recompute and a comparison that establishes nothing. There is also **no read operation** that returns the disclosed preimage elements: the nine operations at L3365-3454 do not include one, and L2584 smuggles it into `GET /arp/outputs/{reconciliation-hash}` as a differently-shaped response for one requester class, which {{read-responses}} does not admit.

### V-13 Policy Parameters Document contradicts the resolution rule — BLOCKING
L3338-3348: "the array of per-predicate entries, each a four-element array of the predicate, the admitted regime set …, the two-element array of the resolved Verdict Arithmetic and its parameters, and the reliance interval, **the entries themselves sorted by predicate**."
{{verdict-arithmetic}} L1535-1537 resolves the operator "keyed on **the predicate and the named regimes**". A document with one entry per predicate cannot express two regime sets resolving to two operators for one predicate. If I instead emit one entry per (predicate, regime-set) pair, "sorted by predicate" gives no tie-break and my signed document is non-deterministic.
Also unfixed here: the type of a "transition identifier and effective time" pair; tie-breaking for transitions sharing an effective time (L3345 "sorted by effective time"); and the reliance-interval unit (T-9).

### V-14 Merkle leaf set membership — BLOCKING
L1385: "Each Partial Attestation is committed to a Merkle tree … under the leaf value that is its Signing Input Digest." Not stated: whether a **Non-Answer Statement** (also a register-signed COSE_Sign1, L1436-1445) is a leaf; whether a re-typed contribution is committed under its attested or effective value (it is a digest of the register's signature, so attested — but say so); and what the root is when no register answered. Under L1276-1278 the empty tree is 32 zero octets, so a reconciliation in which every register refused has a well-formed root that "no commitment in this document produces" — the document's own words for a value that must never appear.
Divergence: including or excluding Non-Answer Statements changes the Merkle Root, hence the Reconciliation Hash, hence the ledger index.

### V-15 Freshness Window has no reference point or direction — BLOCKING
L4076-4079: "The reconciliation server MUST verify the Freshness Timestamp against a freshness window declared in the Bilateral Register Agreement." Item 9 fixes the window as "unsigned integer, seconds" (L3110) but nothing says seconds *before what instant*: the server's receipt time, the Reconciliation Timestamp, or the projection's transmission time. Nor whether the window is one-sided: is a Freshness Timestamp 30 seconds in the *future* stale? {{read-signing}} L3352-3355 shows the author knows how to write this ("more than 300 seconds in the past or more than 60 seconds in the future") and did not write it here.
Divergence: `attestation-stale` fires for A and not for B over the same attestation → different Non-Answer Reason, different Divergence-Axis Set, different verdict.

### V-16 Reconciliation Timestamp instant undefined — BLOCKING (latent until key rotation)
The value is never said to be the moment of sealing, of request receipt, or of the last attestation. It determines the Reliance Horizon (L1844) and, decisively, whether a `retired` sealing key validates: "MUST accept one made under a `retired` key only where the Reconciliation Timestamp falls within that key's validity interval" (L3846-3849). A server that stamps at request receipt and a verifier that assumes seal time disagree across every rotation boundary.

### V-17 Source-Data Version Identifier — BLOCKING, contains an unexecutable MUST
L1121-1133: the state identifier is "a published version token, or **a digest of the published corpus where the publisher assigns none**" — no algorithm, no canonicalisation of "a corpus", no encoding. And: "The reconciliation server MUST reject an identifier that is not drawn from the publisher's own state sequence, under {{no-answer}} with the reason `attestation-unverifiable`." The server holds no copy of the publisher's sequence, no interface to it and no requirement to fetch one. I can only implement this as a no-op, in which case the anti-covert-channel argument at L1126-1130 does not hold in my implementation.

### V-18 The sealed Output has two possible representations — BLOCKING
L1633-1637 makes "Sealing Signature" a **field** of the Output whose payload is "the CBOR array of this Output with the Sealing Signature position alone encoded as CBOR null". The media type (L4381) is "a Reconciliation Output under its Sealing Signature". So the artefact on the wire is either (a) the COSE_Sign1 alone, whose payload array has null in the last position and in which the Sealing Signature field is therefore never populated in any encoding, or (b) the full array with element N = that COSE_Sign1, carrying the array twice.
Divergence: the `result` element of the `200` (L3244) is different bytes in the two readings; a verifier written for (a) cannot parse (b). The same ambiguity recurs for Ledger entries (L2098), Post-Seal Records (L2029), Sweep Statements (L2686) and the Override Record (L800).

### V-19 `next` has nowhere to live — BLOCKING
L3396: "MUST carry a `next` parameter value in the response where more exist, which the requester supplies on the following request." The signed response payload is a **fixed seven-element array** (L3463-3465) with no pagination field, and {{read-errors}} forbids response-shape variation only for the 404 pair but never adds a field. An HTTP header carrying it would be outside the signature. Three operations (`/arp/outputs`, `/arp/re-notifications`, `/arp/sweeps`) are unusable past 100 results.

### V-20 Result shapes for four operations — BLOCKING
`GET /arp/outputs` returns "the Reconciliation Hash, the Reliance Horizon and the Entry Sequence Number" (L3391) — array of 3-element arrays, presumably, unstated. `fields=self-entry-hash` (L3418) — bare byte string or wrapped? `GET /arp/sweeps/{root}/inclusion/{claim-hash}` returns "an inclusion proof" — the CBOR array of L1336 ✓ (this one is specified). `GET /arp/reconciliations/{rid}/registers/{rid}` returns "the Per-Register Result Set entry concerning that register alone" ✓ (specified by reference).

### V-21 Verifiable Credentials serialisation — BLOCKING for that form
L3902-3916 names the media type and nine fields to include "as credential subject fields" and stops. No `@context` URI, no `type` value, no property names, no mapping from CBOR byte strings to JSON, no proof format. Two implementations produce documents that share no key names.

### V-22 Deployment Blinding Value encoding — LATENT
"at least 128 bits" (L1962) — variable length, no CBOR type. Only matters when an auditor is given it (L2588) or when a deployment migrates stores, but then it matters absolutely.

### V-23 Rate-limit "most permissive" — LATENT
L3628 and L1914: the limit is a `(count, interval)` pair (L3116). Is (100, 60s) more permissive than (10, 1s)? By ratio they are equal; by count the first wins; by burst the second. Undefined comparison over a two-dimensional quantity.

### V-24 Witness Set intersection — LATENT/BLOCKING
L3043: "the effective Witness Set is the intersection of the Witness Sets every such Agreement declares." A Witness Entry is a three-element array including a key thumbprint (L2905). Intersection by full triple equality means one register's Agreement that has not yet been updated for a witness key rotation empties the effective set, and L3053 then makes the deployment non-conforming and forbids it to serve any read. Intersection by Operating-Party Identifier alone gives a different answer. No rule.

**Complete as written:** the Merkle construction and inclusion-proof shape (L1272-1352), the timestamp form (L1729-1734), the null-substitution-not-truncation rule (L1720-1725), the Agreement Hash type table (L3097-3118), the ledger-entry value types (L4325-4344), the Signing Input Digest (L400-415).

---

## 3. Decisions I cannot make

### D-1 Which registers are addressed — BLOCKING
The Addressed-Registers Identifier Set is an *enumerated input* to determinism (L620), a field of the Output (L1622) and of the ledger entry (L2167), the domain of the source-class partition (L479), and the thing `addressed-register-cherry-picking` (L757) exists to police. **No section says how it is derived.** The commissioning request body carries "the Canonical Claim, the Audience Set the requester asks for, and, where the requester is an agent, its asserted principal" (L3223-3225) — not a register set. Policy? Requester? Every agreement whose permitted-predicate set admits a projection?
Divergence: implementer A addresses all registers whose predicate set matches; implementer B addresses a requester-named subset. Different verdicts from the same request, and the anti-cherry-picking property is unenforceable because there is no baseline to compare against.

### D-2 Re-typing case 1 and case 2 triggers — BLOCKING
L1490-1493: re-type where the contribution was "attested against a bounded-depth predicate **where the Canonical Claim ranged over a transitive closure**". L1499-1501: re-type where the claim "ranged over a determined fact".
The document itself identifies this exact problem for the *third* ground and solves it (L1508-1523: "the test above names the Canonical Claim Predicate, which is not expressed in any profile. The test is therefore evaluated as follows…"). The same defect in grounds 1 and 2 is left standing. Nothing tells me whether `bo:ultimate-beneficial-owner` "ranges over a transitive closure" — that is a property of a taxonomy I do not have (T-3).
Divergence: A re-types a `no-match` to `indeterminate`; B does not; the Combined Verdict differs decisively, which is the whole output of the protocol.

### D-3 "advisory reconciliation" has no representation — BLOCKING
L742-744 lets policy permit an ENEMY requester "only for non-decisive advisory reconciliation", and L4056 requires that "the resulting Reconciliation Output MUST NOT carry a decisive verdict binding". There is no advisory flag in the Output, and the only verdict-valued field is the Combined Verdict. Do I force it to `indeterminate` (discarding real register answers), or emit `match` and rely on the reader to notice the Requester-Binding Class? Two implementations produce different Combined Verdicts for identical register answers.

### D-4 `register-threshold-divergence` across profiles — LATENT
L997-1001 requires the axis "wherever the Reconciliation Output combines registers whose declared thresholds differ". Only `arp-profile-bods` declares a threshold. Does a BODS register at 25% "differ" from a sanctions register that declares none? Yes → the axis fires on every mixed reconciliation; no → it never fires on a mixed set, which is the case it exists for.

### D-5 A register with two divergence reasons — LATENT
L1207 gives the Partial Attestation a singular "OPTIONAL Divergence-Axis Field" while the server gets a Set (L1626). A register whose answer is both `temporal-mismatch` and `identity-mismatch` must silently choose. The document makes exactly this argument for the server's Set ("an encoding admitting only one would force an implementation to choose between them silently", L1708-1710) and not for the register's field.

### D-6 Whether to notarise, and therefore whether continuations exist — LATENT
L3661 "MAY be notarised". Downstream, `continuation-notarisation` entries, the `notarisation-incomplete` qualifier and the polling bound all hang off a decision with no stated input. A relying party cannot tell a non-notarising deployment from a suppressed notarisation.

### D-7 "Where permissible … partial attestations MAY be re-invoked" — BLOCKING
L2630 plus Agreement item 31 (L2871). If re-invocation is *not* permitted, a `source-data-version` trigger recomputes a Combined Verdict from *retained* per-register verdicts — which cannot have changed, because the register's verdict is exactly what the new corpus state would alter. The entire source-data-version limb of {{retroactive}} is inert in that configuration, and nothing says so. The illustrative example (L4578-4582) assumes re-invocation without saying it is conditional.

### D-8 Which registers a superseding reconciliation addresses — LATENT
L2246-2248 acknowledges "the superseding reconciliation may address registers the superseded one did not" and gives no rule for choosing. Combined with D-1, a supersession's register set is entirely at the operator's discretion, which is the discretion {{budget-suppression}} is written to bound elsewhere.

### D-9 Resolving a SCITT `404` — BLOCKING
L3771-3775: "an implementation MUST distinguish them **from the response body where the service supplies one**". No body schema, no field, no example, no fallback rule beyond "cannot be resolved → incomplete". Whether a `continuation-notarisation` entry is appended (a signed, permanent ledger fact) turns on unspecified string matching against another specification's unspecified body.

### D-10 Who is "an authorised operator" — LATENT
L782 and L797. Any key in `/.well-known/arp-operator-keys` authorises any override of any pattern; no scoping, no per-ground authorisation, no separation between operators.

---

## 4. States and transitions

### S-1 The reconciliation request has no asynchronous state — BLOCKING
{{request-binding}} defines exactly four responses (L3241-3260): `200` with the Output, `422`, `403`, `401`. There is no `202`, no job identifier, no polling operation. But the server must first transmit projections to n registers and wait out "the response window after which a register is recorded unresponsive" (Agreement item 12, L2828), which is an unbounded contractual value. Every reconciliation therefore holds an HTTP request open for the longest register window. There is no state for "in progress", no way for a client that timed out to recover the Output (it has no Reconciliation Hash and cannot compute one — L1896-1899 concedes the hash "is not reproducible across runs"), and `GET /arp/outputs` requires a `since` window that may not yet contain the entry.
This is the largest structural omission in the wire model.

### S-2 Retry and duplicate delivery — BLOCKING
No idempotency key. A client that times out and retries with a fresh nonce (it must: L3355 rejects a repeated nonce) commissions a **second** reconciliation: second budget charge (L3990), second ledger entry, second Output — with the **same Reconciliation Identifier** as the first (V-25/C-2). Nothing forbids it and nothing lets a client detect it.

### S-3 Late attestation — LATENT
A register recorded `register-unresponsive` may answer at window+1s. The server holds a valid signed attestation for a sealed Output. No rule: discard? The register has consumed its one-per-nonce right (L1192) and its own read (L3378) will show a contradiction it cannot resolve.

### S-4 `agreement-drift-suspended` is a state with no exit — BLOCKING
L4070: "Reconciliation MUST be suspended for an addressed register whose Agreement Hash deviates from the hash committed at the start of a reconciliation event." No resumption condition, no notification to the Register Operator, no renegotiation protocol. L3122-3130 says "the parties MUST agree the new Agreement Hash before the operation that causes it" and defines no mechanism by which they do. A key rotation therefore suspends a register indefinitely with no specified way back.

### S-5 Two parties in different states, with no remedy — BLOCKING
The server records `register-unresponsive`; the register holds its signed `match`. L3378-3385 gives the register the read that exposes this and then stops: no dispute state, no obligation on the server, no artefact the register can produce that binds the server (its own read response is signed, so it *is* evidence — but nothing says what follows). The document is explicit that `register-unresponsive` "is indistinguishable from a network failure by construction" (L1462) and leaves the consequence undefined.

### S-6 Fork response is unexecutable — BLOCKING
L2436-2440: a party holding two irreconcilable head statements "MUST report the pair to every regulator whose Bilateral Register Agreements it can identify from the Outputs it holds". An Output carries register origins, agreement **hashes** and no regulator identity, no jurisdiction and no endpoint (L1610-1640). A relying party is not a party to any Agreement (L3025-3027). There is no discovery path from an Output to a regulator. The MUST cannot be discharged by any conforming implementation.

### S-7 Empty ledger / first read — BLOCKING
Every read response MUST carry `as-of-sequence-number` and `as-of-self-entry-hash` of "the Ledger head at the moment the read was served" (L3477). Before the first append there is no head. The Ledger Head Statement (L2378-2390) likewise requires "the Entry Sequence Number of the current head" and "the Self-Entry Hash of that entry". Nothing defines the empty case — contrast the care taken over the empty Merkle tree (L1276). And for the *first* commissioning request the ordering is undefined: is the reconciliation entry appended before the response is produced (so as-of ≥ 1) or after (so as-of has no value)?

### S-8 Retention expiry — LATENT
L1901-1907 fixes a retention floor and never says what happens after. The Output is discarded; `GET /arp/outputs/{hash}` returns `404`, which by L3564 is "indistinguishable, by design, from never having been entitled" — the document flags this hazard for the pre-horizon case (L1920-1925) and creates it permanently at expiry. Ledger entries meanwhile have **no** retention rule at all and no DELETE, so the ledger grows forever while its referents vanish.

### S-9 Key expiry — LATENT
L3849-3852: "A key MUST NOT be removed from the set while any Reconciliation Output it sealed **may still be relied upon**." Reliance is bounded by the Reliance Horizon (L1842) but *verification* is not; L1861 says the Horizon "does not invalidate the Output". So the removal condition is either "never" or "Horizon + retention", and an operator choosing the second breaks verification of every archived Output.

### S-10 A register that permanently disappears — BLOCKING
L3836-3839: a relying party "MUST verify that the origin component of the Sealing-Key Identifier appears in the Authorised-Origin Document published by **every** register in the Addressed-Registers Identifier Set, and MUST reject the Output where it does not **or where any such document cannot be verified**." When a register origin goes dark — decommissioned, jurisdictionally withdrawn, renamed — every historical Output that addressed it becomes permanently unverifiable. No caching rule, no pinning, no archival anchor, no grace. For a protocol whose artefacts are evidence for regulators years later, this is a designed-in expiry of the entire corpus.

### S-11 Agreement termination — BLOCKING (absent)
Agreement items (L2802-2872) include no validity period, no termination, no successor pointer. There is no state for "this register is no longer addressable", no way to retire a permitted-predicate set, and no rule for in-flight reconciliations at termination.

### S-12 Sovereign Re-Notification delivery state — BLOCKING
L2546-2549: "MUST deliver it to the notification endpoint … MUST retry until acknowledged or until the retention period of {{delivery}} elapses". No definition of acknowledgement (HTTP 2xx? a signed receipt?), no method, no media type on the wire, no backoff, no deduplication, and no terminal state if the endpoint is permanently gone. Retention periods here are years.

**Complete as written:** the ledger-entry lifecycle (append-only, sign-once, chain, no UPDATE/DELETE, L2070-2160) including the honest admission that the sign-once rule has no verifier-side test (L2131-2139); `notarisation-incomplete` as a permanent state, explicitly flagged as open (L2196-2205); the zero-witness case (L3048-3057).

---

## 5. The wire

### W-1 The register leg is undefined — BLOCKING (self-declared)
L883-898 states it: transport, endpoint, framing and encryption construction are per-Agreement, and "ARP is interoperable in its artefacts and not yet in that leg's transport". Honest, and still the reason no two deployments can address one register. I record it because a reader of the abstract would not expect the protocol's central data flow to be undefined.

### W-2 The commissioning request body has no schema — BLOCKING
L3220-3232: a CBOR body under a registered media type carrying three things, with no array/map structure, no field order, no key names, no rule for the absent asserted-principal case. Every implementer invents it. (The Canonical Claim's inner encoding is pinned as a JCS byte string ✓ — good — but that is one of the three.)

### W-3 Status-code coverage is incomplete — BLOCKING
Defined: `200`, `401` (L3357), `403`, `422` (L3251-3257), `404` (L3564), `429` (L3629). Undefined: malformed body; unsupported media type; missing REQUIRED `since`/`until` (L3395, L3437, L3444); a `tag` mismatch (L3313 says "MUST reject" without a code); a `fields=` value the server does not know; and **any 5xx**. L3457-3459 requires signing "every `4xx` other than the `401`" and is silent on 5xx, so a client cannot tell whether an unsigned 500 is conforming or an attack. A client cannot implement error handling.

### W-4 Well-known resources are underspecified — BLOCKING
Six URIs (L4351-4358) with no method (GET presumed), no status codes, no `Accept`/`Content-Type` statement, no caching guidance, and — critically — **no anchor for `/.well-known/arp-register-keys`**. L3826-3832 says the Authorised-Origin Document "MUST be signed under a key served as a COSE Key Set at `/.well-known/arp-register-keys` … which the relying party fetches over its ordinary web PKI", while L3788-3790 says "A signed key set, wherever this document requires one, is a COSE_Sign1". Is the register key set itself a bare `COSE_KeySet`, a self-signed COSE_Sign1, or TLS-only? Three answers, three incompatible parsers, and the chain at L3840-3845 is rooted on this.

### W-5 Head Consistency Statements have no distribution and no key path — BLOCKING
{{head-consistency}} defines the artefact and a media type; **no operation returns one**, no URI is defined, and no discovery mechanism exists. {{quorum-rule}} L2975 requires "each verifies under the key material declared for that entry" — declared in the Bilateral Register Agreement, which the relying party does not hold (L3025-3027). {{witness-discovery}} moves the *Set* and the *quorum* into the Policy Parameters Document but not the key material, and item 30 (L2866-2870) puts the retrieval means inside the Agreement, having just observed that "a thumbprint is not key material". The relying party is required to evaluate a quorum whose signatures it cannot obtain or verify.

### W-6 The `fields=linkage` chain check is uncomputable — BLOCKING
L2977-2989 requires the verifier to establish "that the triple at each sequence number carries, as its Prior-Entry Hash, the Signing Input Digest of the Entry Signature of the entry below it". The projection returns only `[sequence number, Prior-Entry Hash, Self-Entry Hash]` (L3423-3425). Computing the Signing Input Digest of entry *n−1* requires that entry's protected header and payload, which the projection does not return and which the requester is typically not entitled to (that is the whole point of the projection existing).
Reading A: uncomputable, so the linkage limb of the quorum rule cannot be satisfied by any relying party. Reading B: the statement is definitionally true of any well-formed entry and checks nothing. Under either reading, a chain of linkage triples is **not** verifiable: triple[n].prior does not equal triple[n−1].self (the document itself warns against that comparison at L2986-2989), and no other relation between consecutive triples is checkable. An implementer who tries anyway will compare self-to-prior and reject every honest chain.
Also unstated: how many triples ("the linkage triples between the two" — all of them? one per sequence number over a gap that may be millions, each a separate rate-limited signed request?).

### W-7 Regulator authentication is undefined — BLOCKING
L2476-2481: the Portal "authenticates a sovereign regulator's jurisdictional credentials against a regulator-identity-provider trust anchor". No credential format, no protocol, no binding to the `keyid` of {{read-signing}} (L3331 says only that the key must be "a key the corresponding Bilateral Register Agreement declares"), and **no mapping from an authenticated regulator to a jurisdiction identifier** — which is the key on which the permitted-read-field intersection (L2485-2491) is computed. I cannot implement field restriction.

### W-8 Read/response mechanics gaps — LATENT
No `Retry-After` on `429`; no guidance on request/response `Content-Type` for GETs; `Cache-Control: no-store` required only for the 404 pair (L3600) though the argument covers everything; no rule for a client retry after timeout double-charging the rate limit (L3608 charges before entitlement, so it charges before existence too).

**Complete as written:** the {{read-signing}} profile (L3303-3363) — components, parameters, nonce length, freshness bounds, algorithm source, `keyid` semantics, the unsigned-`401` carve-out and its justification; {{read-errors}}'s normalised-observation rule (L3562-3600); the SCITT registration and async-polling binding (L3669-3785) — statuses, `Location`, `Retry-After`, minimum poll interval, bounded polling, terminal-refusal classification. These are the parts of the wire I could implement from the text alone.

---

## 6. Concurrency and ordering

### C-1 The determinism requirement is unsatisfiable as written — BLOCKING
L618-624 requires that identical enumerated inputs produce "Reconciliation Outputs identical in every field save those enumerated below", and L636-665 enumerates the exceptions: Reconciliation Timestamp, Reliance Horizon, Sealing Signature, Override Record, register signatures, Sealing-Key Identifier, `attestation-stale`/`register-unresponsive`, budget-driven reasons, Freshness Timestamps, Source-Data Version Identifiers.
**The Reconciliation Nonce is not among them.** It is per-projection, random and never reused (L466-472). It is carried in the Query Binding Record (L1685-1688), inside the Query Binding digest (L1213), inside every register's signed payload, and therefore inside every Merkle leaf and the Merkle Root (L1385) — all of which are fields of the Output that the clause requires to be identical.
Two runs with identical enumerated inputs cannot produce identical Outputs. A conformance test written from this clause fails every implementation, including the author's.

### C-2 The Reconciliation Identifier is not unique — BLOCKING
It is `Claim Hash || Policy-Version Hash` (L1643), both of which are deterministic functions of enumerated inputs. Two reconciliations of the same claim under the same policy — a retry (S-2), a second requester, or a `source-data-version` supersession (where policy is unchanged by construction, L2624-2627) — share one Reconciliation Identifier.
Consequences: `GET /arp/reconciliations/{reconciliation-identifier}/registers/{register-identifier}` (L3376-3379) has no defined answer, and it is the *only* operation a Register Operator has; a register receiving two projections with one Reconciliation Identifier and different nonces cannot tell whether the second is a replay; and the Non-Answer Statement's anti-replay argument ("without it a refusal elicited in one reconciliation is admissible as a refusal in another", L1447-1449) fails exactly between two reconciliations of one claim.

### C-3 Nothing pins the policy epoch to the reconciliation — BLOCKING
The server "MUST send the same Policy-Version Hash to every addressed register in one reconciliation" (L901-903) but no text fixes *when* the policy is resolved, and a policy transition is an ordinary event with an effective time (L3344). A transition between the projection to register A and the projection to register B produces two policy versions in one reconciliation, detected only as `attestation-unverifiable` on the echo check (L905-907) — i.e. an honest policy change is reported as a register failure.

### C-4 Rotation during a reconciliation — BLOCKING
{{agreement-drift}} compares against "the hash committed at the start of a reconciliation event" (L4071) and no text defines that instant, records it, or carries it. Agreement items 11, 22, 27 and 30 "change under ordinary operation" (L3122-3125). A rotation between projection and attestation yields an echoed hash that differs from the committed one → `agreement-drift-suspended` → S-4's no-exit state, for a conforming, coordinated rotation.

### C-5 Overlapping sweeps — LATENT
{{sweep-statements}} requires "exactly one Evaluation Sweep Statement for each trigger" within the notarisation interval (L2657-2660), and a Statement carries one applied policy state and a head-at-start/head-at-end pair (L2669-2673). Two triggers inside one interval, or a policy transition mid-sweep, are not addressed: whether sweeps may overlap, whether a second sweep may supersede an Output the first is currently superseding, and which Statement's Examined-Set Root a given Output appears under. Two superseding Outputs for one superseded Output produce two `continuation-supersession` entries and two inverse pointers, which the "inverse pointers over one relation" claim (L2258) assumes cannot happen.

### C-6 Three clocks, one tolerance the reader cannot read — BLOCKING
Skew is bounded only for HTTP signatures (±300/60s, L3352-3355) and for the Witness Observation Time (two intervals, L2991-2995). It is unbounded for: the register's Freshness Timestamp against the server's window (V-15); the reader's check that `response-time` is "within a declared freshness tolerance" (L3503) — where the tolerance is Agreement item 26 (L2844), declared in an instrument the reader is not party to and **not carried in the Policy Parameters Document** (L3338-3348), so the reader cannot obtain the value it MUST check against; and the Entry Timestamp against anything.
This is the same defect {{witness-discovery}} was written to fix for the quorum (L3025-3031), left unfixed one section away for the tolerance.

### C-7 Replication versus the As-Of rule — LATENT
L2464-2474 permits per-jurisdiction secondary stores under "synchronous replication" with a single sequence. L3477-3482 requires every response to name the head "at the moment the read was served" and forbids naming one lower than the last published Head Statement. A momentarily lagging secondary must therefore refuse to answer, and no text says it may, what status it returns, or how a reader distinguishes lag from equivocation (which is precisely the condition the section is about).

### C-8 Budget counters under concurrency — LATENT
The per-principal/per-subject budget (L3944) and the shared ceiling with a reserved partition (L3966-3974) are read-modify-write counters consulted per register per reconciliation, with no atomicity requirement, no interval anchoring (calendar-aligned or sliding? item 13 gives only seconds, L2825), and no rollback when a reconciliation is refused after partial charging. Two concurrent requests can both pass a budget check that only one should pass — and `query-budget-exhausted` is already the document's acknowledged suppression channel (L4002-4037).

---

## 7. The first and the last

**Specified and correct:** the first ledger entry (sequence 1, Prior-Entry Hash of 32 zero octets, L2075-2088); the first Ledger Head Statement's null notarisation pointer (L2386-2388); the first Evaluation Sweep Statement's null previous-notarisation pointer (L2679-2681); the empty Merkle tree (L1276-1310, with the CT divergence stated and justified); the zero-witness deployment (L3048-3057). This is the strongest cluster in the document.

**Not specified:**

### F-1 Empty ledger — BLOCKING. See S-7. There is no head before the first append, and every read response and Head Statement requires one.

### F-2 The empty Audience Set contradicts itself — BLOCKING
L1770: "an Audience Set of zero or more Audience Members, encoded as a CBOR array **which is empty only in the case described below**." The case below (L1804-1806) concludes "there is always a key to name and an Audience Set is **never** empty." The forward reference points at nothing. I cannot tell whether to admit, reject or produce an empty Set — and an empty CBOR array versus a one-element array is a different Reconciliation Hash.

### F-3 Zero addressed registers — BLOCKING
No minimum cardinality is stated anywhere. Under conjunction, "match where every contribution is match" (L1578) is vacuously true over an empty set: an implementation returns a decisive `match` having asked nobody. Under disjunction the same construction returns `no-match`. The two operators return opposite decisive verdicts over the same (empty) evidence. The Merkle Root is 32 zero octets (V-14). Nothing forbids this reconciliation and it is sealed, ledgered and notarised like any other.

### F-4 The first Bilateral Register Agreement / chain root — BLOCKING. See W-4: the Authorised-Origin chain terminates at a key set with no defined anchor and no defined encoding.

### F-5 First reconciliation for a subject — LATENT. Budget interval anchoring undefined (C-8).

### F-6 Termination: retention expiry (S-8), key removal (S-9), register disappearance (S-10), agreement termination (S-11), regulator endpoint death (S-12), deployment closure (no final head, no closing statement, no rule for a ledger whose operator ceases). None is specified; three of the six make previously valid evidence permanently unverifiable.

---

## Summary table

Severity: **B** = BLOCKING (cannot build, or would build something non-interoperable). **L** = LATENT.

| # | Sev | Area | Line(s) | Finding |
|---|---|---|---|---|
| V-1 | B | values | 675-682 | Canonical Claim has no JSON schema; the JCS preimage of the Claim Hash — the ledger index — is unconstructible |
| V-3 | B | values | 1610-1725 | Reconciliation Output has no CBOR type table; the Reconciliation Hash is irreproducible across implementations |
| D-1 | B | decisions | 620, 3223 | Nothing states how the Addressed-Registers Identifier Set is derived |
| T-3 | B | terms | 330, 849-853 | Predicate Taxonomy undefined and unpublished; projection cannot be computed |
| C-1 | B | concurrency | 618-665 | Determinism clause omits the Reconciliation Nonce; it is unsatisfiable by any implementation |
| C-2 | B | concurrency | 1643 | Reconciliation Identifier is not unique across runs; the register's only read operation is ambiguous |
| V-4 | B | values | 1213 | Query Binding element CBOR types unfixed on a digest two parties must compute independently |
| S-1 | B | states | 3241-3260 | No asynchronous path for a reconciliation; a client that times out cannot recover the Output |
| W-6 | B | wire | 2977-2989, 3423 | The `fields=linkage` chain check is uncomputable from the data the projection returns |
| W-5 | B | wire | 2888-3046 | Head Consistency Statements have no distribution endpoint and no key-retrieval path for the party required to verify them |
| C-6 | B | concurrency | 3503, 2844 | The response freshness tolerance a reader MUST apply is declared only in Agreements the reader cannot read |
| V-18 | B | values | 1633-1637 | The sealed Output has two incompatible wire representations |
| T-1 | B | terms | 1622, 4514/4539 | "authority origin" undefined; the document's own example is internally inconsistent |
| V-13 | B | values | 3338-3348 vs 1535 | Policy Parameters Document is keyed per predicate; resolution is specified per (predicate, regime set) |
| W-4 | B | wire | 3826-3832, 3788 | `/.well-known/arp-register-keys` has no defined anchor or encoding; the whole key chain is rooted on it |
| S-10 | B | states | 3836-3839 | A register origin that disappears makes every historical Output it touched permanently unverifiable |
| D-2 | B | decisions | 1490-1501 | Re-typing grounds 1 and 2 have no rule for classifying the Canonical Claim Predicate (ground 3's fix not applied) |
| V-6 | B | values | 854, 1062 | Narrowed-From has no structure, yet a divergence axis MUST be derived from it |
| V-15 | B | values | 4076-4079 | Freshness Window has no reference instant and no direction |
| V-14 | B | values | 1385 | Merkle leaf set membership undefined for Non-Answer Statements and for the all-refused case |
| V-8 | B | values | 763-775, 3256 | Remediation Advisory array arity is ambiguous and the `403` shape contradicts it |
| V-9 | B | values | 3805-3807 | `kid` / Sealing-Key Identifier encoding unpinned across COSE bstr, thumbprint text and URL segment |
| V-10/11 | B | values | 1774, 1804 | Audience Member Identifier has no URI scheme, no normalisation and no comparison rule |
| W-3 | B | wire | 3457, 3564 | Status-code coverage incomplete; 5xx and malformed-request behaviour undefined |
| W-7 | B | wire | 2476-2491 | Regulator authentication and the authenticated-regulator→jurisdiction mapping undefined |
| V-12 | B | values | 2581-2586 | Reconstruction Proof has no preimage encoding and its fallback comparison is circular |
| V-2 | B | values | 686-690 | Evidentiary Provenance Manifest cannot be both COSE-enveloped and inside a JCS preimage |
| V-19 | B | values | 3396, 3463 | `next` has no field in the signed response payload; three operations unusable past 100 results |
| S-6 | B | states | 2436-2440 | Fork-reporting MUST cannot be discharged: no path from an Output to a regulator |
| S-7/F-1 | B | first | 2378, 3477 | Empty-ledger head undefined; the first read and the first Head Statement have no value |
| F-3 | B | first | 1578-1584 | Zero addressed registers yields a vacuous decisive verdict, opposite under conjunction and disjunction |
| F-2 | B | first | 1770 vs 1806 | "empty only in the case described below" — the case is absent and the text says never empty |
| S-4/C-4 | B | states | 4070, 3122 | `agreement-drift-suspended` has no exit and rotation has no handshake |
| T-2 | B | terms | 622 | "Policy-Version Identifier" used once, defined nowhere, carried by nothing |
| T-6/7/8/9 | B | terms | 1944-1950 | Four Policy-Version-Hash elements have no type, structure or unit |
| V-17 | B | values | 1121-1133 | Source-Data Version state identifier has no digest rule; the "not from the publisher's sequence" MUST is unexecutable |
| D-3 | B | decisions | 742, 4056 | "Advisory, non-decisive" reconciliation has no representation in the Output |
| D-7 | B | decisions | 2630, 2871 | Where re-invocation is not permitted, the source-data-version limb of retroactive evaluation is inert |
| D-9 | B | decisions | 3771-3775 | SCITT `404` disambiguation rests on an unspecified response body |
| T-12 | B | terms | 703 | No rule maps a signed request to the `human-operator` class |
| T-14 | B | terms | 705 vs 316 | VPC "status was checked" has no mechanism and contradicts the no-issuer-contact definition |
| V-7 | B | values | 870, 1209 | Profile/Applied Parameter Set structure undefined inside signed payloads |
| V-5 | B | values | 1643, 3288 | "Concatenated" Reconciliation Identifier has no encoding and no path-encoding rule |
| S-2 | B | states | 3241 | No idempotency: a retry silently commissions a second reconciliation and a second budget charge |
| S-11 | B | states | 2802-2872 | No agreement validity period, termination or successor state |
| S-12 | B | states | 2546-2549 | Re-Notification delivery has no method, media type, acknowledgement or terminal state |
| V-21 | B | values | 3902-3916 | VC serialisation has no `@context`, `type` or property names |
| C-3 | B | concurrency | 901 | Nothing fixes when the policy epoch is resolved for a reconciliation |
| T-4 | B | terms | 741, 3258 | "predicate class" governs the Agent-IFF gate and is undefined |
| W-1 | B | wire | 883-898 | The register leg is entirely per-Agreement (self-declared) |
| W-2 | B | wire | 3220-3232 | Commissioning request body has no schema |
| V-20 | B | values | 3391, 3418 | Result shapes for the enumeration and the `fields=self-entry-hash` projection undefined |
| T-10 | B | terms | 479, 1616 | Source-class partition is a carried Output field with no structure |
| V-16 | B | values | 1841, 3846 | Reconciliation Timestamp instant undefined; retired-key validation turns on it |
| S-9 | L | states | 3849 | "may still be relied upon" leaves key-removal either never or verification-breaking |
| S-8 | L | states | 1901 | Post-retention `404` is indistinguishable from never-entitled; ledger entries have no retention rule |
| C-5 | L | concurrency | 2657-2673 | Overlapping sweeps and mid-sweep policy transitions unaddressed; double supersession possible |
| C-7 | L | concurrency | 2464, 3477 | A lagging secondary store cannot satisfy the As-Of rule and has no defined refusal |
| C-8 | L | concurrency | 3944, 2825 | Budget counters have no atomicity, interval anchoring or rollback |
| V-24 | L | values | 3043 | Witness Set intersection over full triples empties the set on any key rotation, making the deployment non-conforming |
| V-23 | L | values | 3628 | "Most permissive rate" is an undefined comparison over a (count, interval) pair |
| D-4 | L | decisions | 997 | Threshold divergence across profiles that declare no threshold is undefined |
| D-5 | L | decisions | 1207 | A register with two divergence reasons must choose silently |
| D-6 | L | decisions | 3661 | Notarisation is a "MAY" with no input; a non-notarising deployment is indistinguishable from a suppressing one |
| D-8 | L | decisions | 2246 | The register set of a superseding reconciliation is unconstrained |
| D-10 | L | decisions | 782, 797 | "Authorised operator" is any key in the operator key set; no scoping |
| S-3 | L | states | 1412 | Late attestation after `register-unresponsive` has no rule |
| S-5 | L | states | 3378 | Register-versus-server contradiction is observable and has no remedy |
| T-5 | L | terms | 4042 | "Pattern-Library Commitment Hash" appears once, with no construction and no carrier |
| T-11 | L | terms | 1966 | "deployment" undefined; the blinding scope is unbounded |
| T-13 | L | terms | 312, 733 | "genuinely verified declared bot" is one third of a "deterministic" classification and has no definition |
| T-16/17 | L | terms | 2492, 3820 | "subpoena-grade"; Register Identifier/origin identity asserted only in passing |
| V-22 | L | values | 1962 | Deployment Blinding Value has no fixed length or CBOR type |
| W-8 | L | wire | 3600, 3629 | No `Retry-After` on 429; `no-store` scoped only to the 404 pair; retry double-charges the rate limit |

### Sections I could implement from the text alone
{{merkle-construction}} and {{leaf-binding}} (L1265-1382); the Signing Input Digest and {{signature-malleability}} (L400-415, L4106-4165); {{read-errors}}'s normalised observation (L3562-3600); {{read-signing}}'s RFC 9421 profile (L3299-3363); {{registration}} and {{async-registration}} (L3669-3785); {{bra-items}} + {{bra-hash}} (L2796-3130); the ledger entry field order, chaining and null rules (L2070-2160) and their IANA value types (L4325-4344); {{quorum-rule}}'s distinctness and window arithmetic (L2960-3023, modulo W-6); the timestamp form (L1729-1734). These are the parts where the document does what the rest of it needs to do everywhere.agentId: ad91396e8b707154f (use SendMessage with to: 'ad91396e8b707154f', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 196538
tool_uses: 30
duration_ms: 892947</usage>