I read the document selectively across all its normative sections. Findings below; every attack is conformant (no MUST violated) unless I say otherwise.

# ARP adversarial and privacy review — draft-hillier-scitt-arp

The document is unusually well defended in several places, and I say where. It is not defended in the places that decide outcomes about people.

---

## 1. THE CONFORMANT OPERATOR

### 1.1 The subject-mapping step is unrecorded and unverifiable by anyone but the operator — BLOCKING

The Canonical Claim carries a `Subject Identifier` (line 668). Each Per-Register Claim Projection carries a different value, `Subject Reference, in the form the addressed register's Bilateral Register Agreement declares` (line 861). **Nothing in the document records, binds or constrains the mapping between them.**

The Reconciliation Output (lines 1610–1650) carries the Claim Hash but *not* the Canonical Claim and *not* the Subject Identifier. The Query Binding Record (line 1682) carries the Subject Reference. The Claim Hash is blinded (line 1957ff) and is not invertible by any party outside the deployment. The Audit Identity is given "every element of the Policy-Version Hash preimage … EXCEPT the Deployment Blinding Value" — and the Policy-Version Hash preimage does not contain the claim (lines 1936–1944).

Sequence: the operator receives a claim about Subject Identifier `person:UK:AliceX`. It transmits projections carrying Subject Reference `person:UK:AliceY` — a different natural person, or a deliberately misspelled transliteration, or a dissolved shell with the same name. All three registers answer honestly about Y. Every register signature verifies. Every Query Binding recomputes. The Merkle root verifies. The Sealing Signature verifies. The ledger entry chains. The notarised Signed Statement passes every check in `{{registration}}`.

Wrong conclusion: an Audience Member, a regulator under `{{regulator-portal}}`, an Audit Identity, and a court all conclude that Alice X was screened and cleared. Only the requester holds the claim, and the requester is the party who may have wanted this.

The document's own justification — "The Claim Hash binds the Output to the question it answers" (line 1652) — is false as against every reader except the requester. This is the single most valuable defect in the document: the entire signature chain is anchored on an unrecorded, unattested projection step performed by the party the rest of the document declines to trust.

Fix shape: carry the Subject Identifier, or a per-register binding digest over `(Subject Identifier, Subject Reference, Register Identifier)`, inside the Projection Record.

### 1.2 `conjunction` returns a decisive `no-match` on a single dissent — BLOCKING

Lines 1579–1583:

> `match` where every contribution is `match`. **`no-match` where any contribution is `no-match`.**

Compare the safety rule immediately above it (lines 1568–1572): "Where any contribution is `indeterminate`, the Combined Verdict MUST be `indeterminate` wherever the operator's table would otherwise yield `no-match`. An `indeterminate` contribution is an absence of evidence and a decisive negative may not be built on one."

So `{no-match, indeterminate}` is **not** decisive, but `{match, no-match}` **is** decisive `no-match`. A flat contradiction between two sovereign registers is treated as more conclusive than one register's absence of evidence. There is no `conflicting` outcome and no rule sending disagreement to `indeterminate`.

Concrete attack. The operator (a) writes the policy-epoch store, which is "internal to the reconciliation server; this document constrains what it must be able to answer and not how it is built" (line 296), and resolves `conjunction` for `sanctions:` predicates; (b) chooses the Addressed-Registers Identifier Set, which the document never constrains — it is not a Canonical Claim field, is not carried in the commissioning request (line 3222), and is not resolved from policy. It addresses OFAC (returns `match`) plus a small national register that holds no record and returns `no-match` with divergence axis `register-record-absent`.

Combined Verdict: decisive **`no-match`**. Sealed, ledgered, notarised, delivered. A designated person is cleared, and the Output carries a register-signed `match` inside it that the arithmetic overrode.

The register that has never heard of the subject out-votes the register that designated them.

### 1.3 The Addressed-Registers Identifier Set is chosen by the operator and constrained by nothing but the operator's own secret corpus — BLOCKING (composite with 1.2)

`addressed-register-cherry-picking` is a Pattern Library pattern (line 758). But the Pattern Library is "the reconciliation server's internal adversarial-test corpus and is **not published to registers**" (lines 1188–1190), its version identifier is committed to the Policy-Version Hash which is blinded, and the gate is executed by the party it is supposed to constrain. `{{no-answer}}` forbids *dropping* an addressed register; nothing forbids *never addressing* it. The ledger entry discloses which registers were addressed (line 2167) but no artefact anywhere states which registers *should* have been.

### 1.4 Marking a sealing key `revoked` retroactively repudiates every verdict it ever sealed — BLOCKING

Lines 3848–3852:

> A relying party MUST reject a Sealing Signature made under a `revoked` key **irrespective of when the Output claims to have been sealed**

The key set is published by the operator at its own `/.well-known/arp-sealing-keys`, signed under a key the operator also controls. `arp-key-status` is a single text string. The document carefully forbids *deletion* — "retirement is by status, not by deletion, so that a historical Output remains verifiable" (line 3855) — and then hands the operator a status value that achieves more than deletion would.

Sequence: an operator faces litigation over a historical Output. It sets `arp-key-status: revoked` on the sealing key of that epoch. Every relying party is now required by a MUST to reject that Output — and every other Output of that epoch, and every Ledger Entry Signature made under it, and every Ledger Head Statement, Evaluation Sweep Statement, Post-Seal Evaluation Record and signed read response of that epoch. No ledger entry records the revocation. No party need be notified. No ground need be stated. There is no `continuation-` entry type for a key-status change and no registry entry for one.

This is "make a past verdict unattributable" as a single-field, unilateral, conformant, deployment-wide operation. The retroactive-evaluation, supersession and re-notification machinery — all of it — is bypassed.

### 1.5 The retroactive sweep set is undefined, which makes selective evaluation conformant — BLOCKING

Line 2624: "Under a Pattern-Library or Policy-Version trigger the set to be examined is those Outputs **sealed against a superseded Policy-Version Hash**."

But the Policy-Version Hash commits to the **Requester-Binding** (line 1937, item 7) and to the **Bilateral-Register-Agreement Hashes of the addressed registers** (item 8). It is therefore *per reconciliation*, not per policy epoch: two reconciliations by different requesters, or against different register sets, under identical policy have different Policy-Version Hashes.

There is consequently no such thing as "the superseded Policy-Version Hash". An operator reading the sentence literally — the set of Outputs sealed under the one specific 32-byte value that has now changed — examines the reconciliations of one requester against one register set and none other. It emits exactly one Evaluation Sweep Statement per trigger as `{{sweep-statements}}` requires, with honest counts, an honest Examined-Set Root, and an honest notarisation. Every conformance test passes. Every other historical Output goes permanently un-re-evaluated, and no artefact anywhere says so.

The Examined-Set Root defence (line 2686) does not reach this: an Audience Member can demand proof its claim *was* in the examined set, and gets nothing when it was not — indistinguishable from a claim outside the trigger's scope.

### 1.6 Timing, freshness and the determinism carve-outs

Lines 645–652 place `attestation-stale`, `register-unresponsive`, `query-budget-exhausted` and `subject-ceiling-exhausted` outside the reproducibility requirement. `{{budget-suppression}}` (lines 4002–4038) documents **two** of these four as suppression channels, honestly and well. It does not document the other two.

`register-unresponsive` is the stronger channel and it is free: the operator delays transmission until the declared response window has closed, or simply never transmits. Any non-answering register forces `indeterminate` (line 1564). No register signature contradicts it. `{{budget-suppression}}` says an operator "can therefore record `query-budget-exhausted`" — it can equally record `register-unresponsive`, with no counter to audit under item 24 of `{{bra-items}}` and no per-principal accounting at all.

The mitigation the document offers — `GET /arp/reconciliations/{rid}/registers/{rid}`, "what lets a register see what was recorded of its own answer" (line 3382) — is **void for this attack**. The operation is keyed on "the Reconciliation Identifier the register received in its Per-Register Claim Projection". A register that was never sent a projection never learns a Reconciliation Identifier, and there is no enumeration operation for a Register Operator. The check catches the operator who asked and discarded; it cannot catch the operator who never asked, which is strictly easier.

### 1.7 Retention expiry destroys the evidence and keeps the correlator — LATENT

`{{delivery}}` sets a retention **floor** (line 1900). After it, the operator may discard the Output; reads return the signed `404`, "indistinguishable, by design, from never having been entitled" (line 1924). The Settlement-Layer Ledger has **no retention limit anywhere in the document** and exposes no DELETE.

Net effect after the floor: the blinded, correlatable, permanent record of a reconciliation about a natural person survives forever; the artefact that would let anyone establish what it said, who was named, or whether it was superseded is gone. An operator who wants a verdict to become unprovable need only negotiate short retention periods and wait. A holder of a copy cannot prove it was not superseded, because `{{entitlement}}` (line 1834) forbids treating a possessed Output as current.

### 1.8 The policy-epoch store is the operator's, unbounded — LATENT

`{{verdict-arithmetic}}` argues at length (lines 1541–1560) that a *requester* choosing the operator would be "verdict shopping that no downstream check would detect". Correct. But the operator chooses the operator, its threshold, the source-class partition and the reliance interval, per predicate and regime set, with no constraint of any kind, and publishes the mapping in a Policy Parameters Document it signs itself (line 3348). "Naming a regime is a claim about which law applies … selecting an operator is a determination about how evidence combines, which the deployment's policy makes" — the document never says anything about what makes that determination correct, or who may review it. Combined with 1.2 and 1.3 this is the whole verdict.

---

## 2. THE CONFORMANT REGISTER

### 2.1 Any single register holds a silent, deniable, per-subject veto over every reconciliation it is addressed in — BLOCKING

Line 1564: any non-answering register forces `indeterminate`. `register-unresponsive` (line 1416) requires **no artefact from the register** — it is server-observed and, by the document's own words, "indistinguishable from a network failure by construction".

A register that does not wish a particular subject reconciled simply drops that query. It signs nothing, so `{{no-answer}}`'s Non-Answer Statement requirement — which is a genuinely good defence against the *server* dressing suppression as refusal — never engages. The reconciliation is sealed with a non-decisive verdict, forever.

The document names the server-side channel in `{{budget-suppression}}` and does not name this one. It is strictly easier to exercise and available to every register in the set. Any state that controls one addressable register controls the decisiveness of every screening that addresses it.

### 2.2 The register chooses the applied depth, and thereby chooses the verdict — BLOCKING

Line 988: "**A register MAY answer at a shallower depth than the declared maximum**; the declared maximum is therefore not a substitute for the applied value, and re-typing under `{{verdict-retyping}}` turns on the applied value."

`{{verdict-retyping}}` (line 1491): any non-`match` at bounded depth against a closure claim is re-typed to `indeterminate`, which by line 1568 forces the Combined Verdict to `indeterminate` wherever it would be `no-match`.

So a beneficial-ownership register that wishes to prevent a decisive verdict about a particular subject answers at depth 1 for that subject and at its declared maximum for everyone else. It is conformant on every query, its Applied-Parameter Set is honest, and the per-subject variation is invisible because no artefact compares a register's applied depth across subjects. Silent, deniable, per-subject, and it does not even require a lie.

### 2.3 Register-supplied fields that vary per subject are unconstrained channels — BLOCKING

`{{source-versioning}}` is a genuinely excellent piece of work: it identifies the register-chosen opaque string as "an arbitrary-bandwidth channel from register to relying party, carried under signature into a sealed and ledgered artefact" (lines 1113–1117), pins the identifier to the *publisher's* state sequence, and requires the identifier to be constant across every attestation over that list. That reasoning is exactly right, and it is applied to exactly one field.

The same reasoning is not applied to:

- **Applied-Parameter Set** (line 1216, carried into the Output at line 1679) — register-chosen, per-query, subject-varying, several bits.
- **Freshness Timestamp** (line 1222) — register-chosen, second granularity, and additionally a *control*: a register can push a timestamp just outside the declared window to force `attestation-stale` → `freshness-stale` → `indeterminate` for a chosen subject.
- **Divergence-Axis Field** (line 1214) — OPTIONAL, register's choice whether to fill. `{{containment}}` itself observes that `ownership-threshold-mismatch`, `register-record-absent` and `temporal-mismatch` "disclose record content on their own" (lines 3943–3946), and then leaves the register free to attach them at will.

All three are covered by the register's signature, carried into a sealed Output, delivered to the whole Audience Set, and — where the deployment notarises — placed in an external transparency log permanently.

### 2.4 A register can unilaterally suspend the deployment against itself — LATENT

`{{agreement-drift}}` (line 4071): reconciliation MUST be suspended for a register whose Agreement Hash deviates from the one committed at the start of the event. `{{bra-hash}}` (line 3125): items 11, 22, 27 and 30 "carry key material and witness membership, which change under ordinary operation". A register rotates a key mid-flight; the Agreement Hash moves; every in-flight reconciliation addressing it records `agreement-drift-suspended`; none reaches a decisive verdict. Blunt, but conformant and unilateral.

---

## 3. THE OBSERVER / NETWORK ADVERSARY

### 3.1 The side-channel section does not cover what other sections say it covers — BLOCKING (documentation defect with substantive consequence)

`{{side-channel}}` is eight lines (4095–4104). It covers exactly one thing: projection narrowing observable to the addressed register. It then defers everything else to `{{privacy}}`.

Line 1991, in `{{sealing}}`, states: "that they can observe they were addressed together is inherent and **is discussed in `{{side-channel}}`**." It is not discussed in `{{side-channel}}`. It is not discussed in `{{privacy}}` either. The document makes a forward reference to a treatment of register co-addressing that does not exist, in the one paragraph where it acknowledges the problem.

Also absent from both sections: message length, response length, timing, fan-out, retry behaviour, and any padding requirement whatsoever.

### 3.2 Partial Attestation length is a verdict-and-record oracle on the register leg — BLOCKING

`{{per-register-encryption}}` (lines 1161–1200) specifies confidentiality and authenticated additional data. It specifies **no length hiding and no padding**. The Partial Attestation payload (lines 1207–1230) null-pads *positions* — good, that fixes array length — but not *values*. An attestation carrying a `Source-Data Version Identifier Set` over three lists, an `Applied-Parameter Set`, and a `Divergence-Axis Field` is materially longer than one carrying three CBOR nulls.

An observer on the register leg who cannot decrypt anything therefore distinguishes, per query: whether the register answered at all; roughly how many sanctions lists it consulted; whether it attached a divergence axis; and whether it reported applied parameters. Since `register-record-absent` is precisely the axis attached when the register has no record of the subject, **the length of an undecryptable response distinguishes "this subject exists in this register" from "this subject does not"**. That is the oracle the question asks about, and it is available to a passive observer.

Similarly, the count and simultaneity of outbound ciphertexts from one server origin discloses the register fan-out and links the legs of one reconciliation in time — the thing line 1991 promises is discussed and is not.

### 3.3 What the read surface gets right

`{{read-errors}}` (lines 3562–3660) is the strongest section in the document and I could not break it on its own terms. It:

- collapses unentitled and nonexistent to `404` and explains why `403`/`404` would be an oracle;
- defines a **normalised observation** rather than demanding unsatisfiable byte equality — this is a genuinely good piece of specification;
- requires the rate-limit counter to be charged **before** entitlement evaluation;
- forbids short-circuiting entitlement evaluation so the two paths cost the same;
- requires `Cache-Control: no-store` so intermediaries do not reintroduce the distinction;
- and — unusually and correctly — refuses to *claim* timing indistinguishability, requiring any implementation that claims it to publish its measurement population, sample count, network placement, decision rule and threshold.

That last paragraph is better practice than most security-considerations text in published RFCs. Note what it does not reach: it governs the read surface only. The commissioning endpoint (§5.2 below) has explicit discriminating errors, and the register leg (§3.2) has none of these protections.

---

## 4. THE INSIDER AND THE COMPELLED OPERATOR

### 4.1 The `fields=linkage` projection reopens the redaction-recovery channel the same document closes — BLOCKING

`{{read-errors}}` closes a real attack at lines 3637–3648: a regulator given a field-redacted entry must not receive that entry's Prior-Entry Hash or Self-Entry Hash, because "The Self-Entry Hash is a digest over the entry's own fields and **carries no blinding value**; a reader holding the leading fields and denied the type-specific block could otherwise **recover the block by search** over register subsets, a small aggregation descriptor set, four binding classes and a bounded timestamp, and would do so **off the audit trail**".

`{{read-operations}}`, lines 3413–3420, then grants:

> **Any requester whose signature verifies** under `{{read-signing}}` is additionally entitled to the three-element array of the Entry Sequence Number, the **Prior-Entry Hash** and the **Self-Entry Hash**, by the `fields=linkage` query parameter … for an Entry Sequence Number at or below the head of the most recently published Ledger Head Statement.

Sequence: a regulator (or an insider, or anyone holding an entry's leading fields) is served a redacted entry at sequence `n` under `{{regulator-portal}}`, correctly withheld its chain hashes. It then issues `GET /arp/entries/n?fields=linkage` under any verifying signature — including a bare `agent-unverified` key with no principal — and receives the Self-Entry Hash the redaction withheld. It brute-forces the withheld type-specific block exactly as line 3643 describes, off the audit trail, and reads the Addressed-Registers Identifier Set, Aggregation-Method Descriptor, Requester-Binding class and Override Indicator it was denied.

The two sections were plainly written against different threat models and the later one silently voids the earlier one. `{{read-errors}}`'s own defence of `fields=linkage` (lines 3616–3627) argues only that it is not an *existence* oracle. It never notices that it is a *recovery* oracle, in the exact terms the section states ten lines later.

### 4.2 The "subpoena-grade audit trail" is a self-attestation — BLOCKING

`{{regulator-portal}}` (line 2492): "Each access MUST be recorded in an append-only subpoena-grade audit trail." `{{audit-path}}` (line 2609): "Every access under an Audit Identity MUST be recorded in the append-only audit trail of `{{regulator-portal}}`." `{{read-errors}}` (line 3652): "Each read served under this section MUST be recorded in an append-only access log … readable only by a regulator … and by an Audit Identity … **disclosed out of band**."

Compare what the document requires of every *other* accountability artefact: the Ledger is hash-chained, signed per entry, head-published at a well-known URI, and notarised into a Transparency Service that "MUST NOT be operated by or under the control of the reconciliation server" (line 2434). Evaluation Sweep Statements are signed, chained through a previous-notarisation pointer, and notarised. Read responses are signed and request-bound.

The access log is **none of these**. It is not signed, not chained, not head-published, not notarised, not readable by an Audience Member or a subject, and it is held by the party whose conduct it records. A compelled operator served with a gag order writes whatever the order permits, and no external party holds anything against which the log can be checked. A regulator auditing a portal access is auditing a file the audited party maintains about itself.

Keeping reads off the Ledger is the right call for the reason the document gives (line 3654). The consequence — that portal and audit access are then unattestable to anyone but the operator — is not confronted.

### 4.3 A single-register reconciliation collapses the trust-anchor defence — LATENT

`{{regulator-portal}}` (line 2480) requires the regulator-identity-provider trust anchor to "be declared in **every** Bilateral Register Agreement addressed by the reconciliation being read", and defends this well: "requiring the trust anchor in only one agreement would let a single register operator unilaterally introduce a regulator identity that authenticates against multi-register events" (lines 2521–2524).

Nothing in the document requires a reconciliation to address more than one register. For a single-register reconciliation, "every agreement" is one agreement, and the register operator *does* unilaterally determine which regulator identities authenticate against it. A state that controls one addressable register and can induce single-register reconciliations obtains portal authentication for those events.

### 4.4 The Audit Identity is a standing bulk read — LATENT, and the document says so

`{{audit-path}}` grants an Audit Identity "the Reconciliation Outputs of those reconciliations, **irrespective of their Audience Sets**" for every reconciliation addressing its register, plus `GET /arp/outputs` over them. Every agreement must declare at least one (item 21). `{{privacy}}` records this honestly at line 4203: "a deployment's disclosure surface grows with the number of registers it addresses." Correct, and correctly disclosed. Worth noting that the Audit Identity is appointed by the register, not by the subject, and reads Outputs containing subject references in the clear.

### 4.5 Where the operator-key separation is only a declaration — LATENT

The Override Record must be signed by an *operator* key, not the sealing key, and the Authorised-Origin Document "MUST name a key identifier for the operator key set distinct from the one anchoring the sealing key set" (lines 812–818). The reasoning is right. But both identifiers are supplied by the reconciliation server to the register at negotiation time and merely republished by the register; no party verifies that the two anchoring keys are held by different humans. `{{bra-limits}}` applies exactly this scepticism to Witness Operating-Party Identifiers — "It is proof that observer diversity was declared" (line 3153) — and does not apply it here.

---

## 5. RESOURCE AND DENIAL OF SERVICE

### 5.1 The direction rules of `{{delivery}}` are a weapon a single counterparty can fire — BLOCKING

Lines 1900–1918 establish, for values taken from a plural set of agreements:

- retention: **longest** governs;
- every deadline-bounding interval: **shortest** governs — "the ledger-head notarisation interval of `{{settlement-ledger}}`, and the Evaluation Sweep and supersession deadlines measured against it";
- read rate limit: **most permissive** governs.

No floors and no ceilings are stated for any of them.

**(a) Forced non-conformance by a short interval.** One register declares item 15 as `1` (second). It is well-formed: item 15 is "unsigned integer, seconds" (`{{bra-hash}}` table) with no minimum. The deployment must now notarise its Ledger Head Statement into an external Transparency Service every second; emit an Evaluation Sweep Statement within one second of every trigger (line 2657); append every `continuation-supersession` within one second of a sweep completing (line 3538); and — item 26 — cap its response freshness tolerance at one second, so that essentially **every read response is rejected as stale by every conforming reader** (line 3506). One counterparty, one integer, and the deployment is in breach of four MUSTs and its read surface is dead for every Audience Member of every reconciliation.

**(b) Unlocking ledger enumeration by a permissive rate.** One register declares item 18 as an enormous permitted count. That rate now governs deployment-wide. `{{settlement-ledger}}` states the rate limit is "load-bearing on that operation and not merely hygiene" because unlimited consistency reads yield "the deployment's exact entry count by binary search, its write rate by polling, and the timing and size of a retroactive supersession burst" (lines 2452–2456). A single agreement disables it for everyone.

**(c) Forced data retention.** One register declares item 17 as a century. Every sealed Output — containing subject references and principal identifiers in the clear — must be retained that long by the operator, regardless of the wishes of every other register, of the operator, or of the subject.

The document justifies each direction locally ("the direction is the one that makes the obligation stricter") and never considers that "stricter" is exactly what an adversarial counterparty wants to impose.

### 5.2 The Witness Set intersection is a read kill-switch — BLOCKING

`{{witness-discovery}}` (lines 3035–3046): "the effective Witness Set is the **intersection** of the Witness Sets every such Agreement declares and the effective Witness Quorum is the **largest** any of them declares… Where it does not [contain at least quorum entries with pairwise distinct Operating-Party Identifiers], **the deployment is non-conforming and MUST NOT serve reads under `{{read-responses}}`**."

Item 27 is a required declared item and any Witness Set is permitted. A register that declares a Witness Set sharing no entry with the others drives the intersection to empty. If any agreement declares a quorum above zero, the deployment is now non-conforming and must stop serving all reads — to Audience Members, regulators, Register Operators and Audit Identities alike. Every party under a `{{reliance-horizon}}` obligation to read before relying is thereby put in breach of a MUST by a third party's contract term.

The section anticipates the *unsatisfiable* case ("two Agreements each declaring two entries and a quorum of two, with no entry in common") and treats it as a conformance error to be detected — it does not notice it is also a lever, and that the remedy it prescribes is total read shutdown.

### 5.3 Audience-Set flooding exhausts a victim's read budget and forces it into breach — BLOCKING

`{{audience}}` acknowledges the naming problem at lines 1798–1804: "Naming a party places a row in that party's `GET /arp/outputs` enumeration and in the server's access log that the party did not ask for, so a deployment SHOULD constrain who may be named". Enrolment (line 3232) is the gate, and enrolment "is performed by the party being enrolled" — so any party that enrols to receive legitimate Outputs is exposed.

Attack: attacker commissions N reconciliations naming victim V in each Audience Set. Each is enrolled-and-valid, so each succeeds. V now has N rows in its enumeration (paged at 100). `{{reliance-horizon}}` puts V under a **MUST**: it "MUST NOT treat the Combined Verdict as current without having read the Continuation entries for its Reconciliation Hash". The rate limit (line 3630) guarantees only "at least one read of each operation per Reconciliation Hash per reliance interval" — but the *declared* rate is a fixed count per interval, and V's obligations scale with N while its budget does not. At sufficient N, V cannot discharge its reading obligation within the rate limit, receives `429`, and is in breach of a MUST it cannot satisfy.

A third party has exhausted a resource on someone else's behalf and forced them into non-conformance, using nothing but the protocol's ordinary commissioning path. The document analyses shared-counter DoS carefully for the *subject* budget (lines 3958–3990, and `{{budget-suppression}}`) and not at all for the *reader* budget.

### 5.4 The per-subject query budget has no defined subject key — LATENT

`{{containment}}` requires the budget to be "measured per accountable principal **per subject**" (line 3960) and this is the sole bound on record recovery by repeated querying (line 4188). But "subject" is never defined for counting purposes. The requester chooses the Subject Identifier; the server chooses the Subject Reference (§1.1). A requester varying identifier form — company number vs LEI vs name-plus-jurisdiction, or transliteration variants for a natural person — plausibly resets the counter under a conforming implementation, and two conforming implementations will differ. The countermeasure the whole containment argument rests on is not specified tightly enough to be one.

### 5.5 Where budget DoS *is* handled well

`{{containment}}` lines 3970–3990 are good: it identifies that a shared counter is a DoS granted by the countermeasure, keys the budget on the signing key where no principal exists so that no requester falls into a shared bucket, requires a declared per-subject ceiling to be partitioned with a reserve for corroborated principals **and** a per-principal sub-budget within the reserve, and states plainly why an unpartitioned reserve "is exhausted by a subject that incorporates enough entities to hold enough corroborated principals, which is a purchase and not a barrier." That is real adversarial thinking. `{{budget-suppression}}` then declines both available mitigations and explains why each is worse — also good practice.

---

## 6. THE PRIVACY REGULATOR

I assess this as a regulator would, against RFC 6973 and against the data-protection regimes the Introduction itself invokes at line 210.

### 6.1 There is no RFC 6973 analysis and the document does not cite it — BLOCKING

The string "6973" does not appear in the document. Nor do "erasure", "rectification", "data subject", "natural person", "lawful basis", "purpose limitation", "controller", "processor" or "GDPR". The Privacy Considerations section runs from line 4167 to line 4209 — roughly 40 lines for a protocol whose subjects are, in its own words, "beneficial-ownership registers, corporate registries, consolidated sanctions lists and customs records" and "multilateral biometric registers" (line 195).

RFC 6973's threat taxonomy is not worked through. Of its categories:

- **Surveillance** — not addressed; the protocol is a screening oracle (§6.5).
- **Correlation** — addressed only as "colluding registers cannot recover the register set", and wrongly (§7.1).
- **Identification** — the blinding analysis at lines 1975–1988 is good as far as it goes and covers only two digests.
- **Secondary use** — not addressed; Audit Identity and notarisation are both secondary-use surfaces.
- **Disclosure** — partially addressed.
- **Exclusion** — named and then disclaimed (§6.2).

The section's honest "What is protected / What is not" structure is genuinely better than boilerplate, and I want to credit it: lines 4188–4208 list six residual disclosures accurately, including the ones that embarrass the design (the unauthenticated head statement, the Audit Identity's bulk read, the Override Record naming an operator in the clear). But an honest list of residuals is not a privacy analysis, and this document is asking to be an RFC.

### 6.2 Exclusion is named and dodged — BLOCKING

Lines 4195–4199:

> A subject has no standing in this protocol: it is not notified, it cannot object, and it cannot learn that it was reconciled. That is a deliberate property of a sanctions-screening protocol and a real cost, and **a deployment operating where subject rights attach should provide for them outside this document.**

Two problems with the deferral.

First, it is not true that the rights can be provided for outside the document, because the document's own design forecloses them. The Ledger is append-only with **no DELETE exposed or implemented** (line 2384) and has no stated retention limit at all. Ledger Head Statements are notarised into an external Transparency Service that "MUST NOT be operated by or under the control of the reconciliation server" (line 2434) — that is, into a log the controller cannot reach. Where the deployment notarises Outputs (§6.3), subject references leave the controller's reach entirely. A deployer told to "provide for erasure outside this document" cannot.

Second, the deferral is inconsistent with the Introduction, which motivates the entire protocol on the ground that "Sovereign registers under data-protection regimes are jurisdictionally constrained against such re-disclosure" (lines 209–211). A document that claims data-protection constraint as its reason for existing cannot decline to analyse data-protection consequence.

The blinded Claim Hash is **pseudonymous, not anonymous**: the Deployment Blinding Value is held by the controller and is "persisted in the policy-epoch store" (line 1960), so the controller can re-identify at will. Under every regime I am aware of that is still personal data, and an append-only, unbounded-retention, externally-notarised store of it is exactly the structure that erasure regimes are aimed at.

### 6.3 Notarisation exports subject identifiers and principal identifiers into an external append-only log — BLOCKING

`{{registration}}` (line 3688): "The payload of the Signed Statement **MUST be the sealed COSE_Sign1** — the Reconciliation Output under its Sealing Signature".

The sealed Output contains, in the clear:

- every register's **Subject Reference**, inside each Query Binding Record (line 1682) and inside each Non-Answer Statement (line 1690);
- the **Audience Set**, each member an accountable-principal URI (line 1780);
- the Combined Verdict, every per-register verdict, every Divergence Axis, every Applied-Parameter Set;
- where present, the **Override Record naming an authorising operator in the clear** (line 807).

`{{entitlement}}`'s entire disclosure argument is the division between the confidential Output and the digest-only Ledger (lines 1752–1766), and it is a sound argument about the Ledger. Notarisation walks the confidential half of that division into a third-party transparency log with no deletion path and retrieval by EntryID.

The document's treatment is a one-sentence permission: "A deployment for which that is the wrong disclosure should not notarise; `{{scrapi-binding}}` is composed permissively for that reason" (line 3684), plus one line in `{{privacy}}`. There is no MUST NOT for personal-data subjects, no redaction profile for the notarised form, no requirement to notarise only the Reconciliation Hash, and — pointedly — no acknowledgement that the *whole* Output goes, subject references included. A reader skimming `{{composition-scitt}}` item 2 would reasonably believe the notarised object was hash-only, as the Ledger is.

### 6.4 A corrected register record is not a retroactive-evaluation trigger — BLOCKING

The trigger registry (line 4302, and `{{retroactive}}` line 2618) is exactly four values: `pattern-library`, `policy-version`, `source-data-version`, `credential-revocation`.

A register correcting its own record about a person is none of these. `source-data-version` covers "a published corpus, external to both the Bilateral Register Agreement and the Policy Version" — a consolidated sanctions list — and does not cover a beneficial-ownership register fixing a wrong ultimate-beneficial-owner entry, a corporate registry correcting a directorship, or a customs authority reversing a determination.

Consequence: the retroactive machinery — sweeps, supersession entries, Sovereign Re-Notification, the whole of §`{{retroactive}}` and `{{sweep-statements}}` — will revisit a verdict when *the operator changes its own policy* and will **never** revisit it when *the authoritative register corrects the fact*. A person wrongly recorded as a beneficial owner of a sanctioned entity, who successfully gets the register corrected, has no mechanism in this protocol by which the false `match` sealed against them is ever re-evaluated, superseded, or notified to the parties that relied on it. Every Audience Member's `GET /arp/continuations` continues to return a signed statement that there was no supersession — and that statement will be true.

This is the one trigger a data subject would care about, and it is the one that is missing. It is also a straightforward correctness defect, not only a privacy one.

### 6.5 The protocol is an open screening oracle by default — BLOCKING

`POST /arp/reconciliations` (line 3222) requires a verifying signature and nothing else. `agent-unverified` — "a bare key that resolves to no signature-agent card, carries no Verified Principal Credential, and asserts no principal" (line 723) — is an admitted class, not a refusal. Whether it may reach a decisive verdict is a per-deployment Agent-IFF policy choice, but the reconciliation *runs* either way, the register is queried either way, and the Ledger entry is written either way.

There is no requirement anywhere of: a lawful basis, a purpose declaration, a relationship between requester and subject, a limitation on which subjects may be screened, or any notion of proportionality. Any party with a keypair can commission a register-attested reconciliation about any named natural person, subject only to the query budget. `{{containment}}`'s query budget exists to bound *record recovery*, not to bound *screening*, and per line 3960 it resets each interval.

For a protocol whose worked examples are sanctions screening of named parties, "any pseudonymous key may screen anyone, repeatedly, forever" is the design, and it is not stated as such anywhere.

### 6.6 Data minimisation: the narrowest predicate is narrow; the surrounding metadata is not

The projection function is genuinely minimising and I want to credit it. `{{projection}}` (line 838) computes the nearest permitted ancestor and **fails rather than choose** where two are equidistant. The register receives one enumerated structure and "does not receive the Canonical Claim, the Addressed-Registers Identifier Set, or any other register's projection" (line 903). The Partial-Attestation payload "SHALL NOT contain any register-record field, any pre-image of the register record, or any field beyond those enumerated" (line 1249). `{{format-profiles}}` forbids a profile from introducing "a means of transporting register records" and the IANA text tells the designated expert to refuse such a registration. That is real minimisation and it is enforced structurally.

What defeats it is everything around the predicate:

- The register receives the **Reconciliation Identifier** (§7.1) and the **Policy-Version Hash** (§7.2), both of which are joins.
- `{{containment}}` itself concedes the per-event property "MUST NOT be read as a property of the system under repeated querying" — "a sequence of reconciliations varying that value recovers the underlying record field by search" (lines 3936–3946) — bounded only by the budget whose subject key is undefined (§5.4).
- The Divergence Axes the register may attach disclose record content by the document's own admission.
- The Output, which is where all of this lands, carries subject references in the clear to every Audience Member and to the transparency log.

The narrowest predicate is narrow. The question is fully reconstructible from what travels beside it.

### 6.7 Can a subject learn it was screened, or contest a verdict?

No, and no. Line 4195 says so for the first. For the second: there is no subject-initiated path of any kind. The only correction mechanisms are the operator's Override Record (an *authorising* act, not a contesting one), retroactive evaluation (which excludes register correction, §6.4), and supersession (operator-initiated). The Remediation Advisory goes to the requester. The Sovereign Re-Notification goes to the regulator. The `continuation-supersession` entry is readable by the Audience Set. The subject is in none of those sets and cannot become a member of any of them, because the Audience Set "MUST NOT be enlarged after sealing" (line 1817).

---

## 7. CORRELATION

### 7.1 The Reconciliation Identifier is an exact cross-register join key handed to every register in the clear — BLOCKING

The Per-Register Claim Projection's **first field** is the Reconciliation Identifier (line 858), and it is the same value for every register in one reconciliation. It is defined as `Claim Hash || Policy-Version Hash` (line 1648).

`{{terminology}}` takes considerable care that the *nonce* differs per register, "so an attestation elicited from one register cannot be presented as an answer from another" (line 452). Correct, and it solves attestation transferability. It does not solve correlation, because the Reconciliation Identifier is deliberately shared.

Attack: registers A (a US beneficial-ownership register, Subject Reference = an EIN) and B (an EU register, Subject Reference = a national identity number) collude, or are compelled by their respective states, or simply share logs under a mutual legal assistance arrangement. They compare Reconciliation Identifiers. Every match is a **confirmed identity equation between their two national identifier spaces for the same natural person**, attested by the fact that one reconciliation server treated them as the same subject.

This is precisely the cross-jurisdiction linkage that data-residency regimes exist to prevent, and the protocol supplies it as a mandatory field. The document's only correlation analysis (lines 1990–1993) considers whether colluding registers can recover the *register set* from the Policy-Version Hash by search, concludes blinding prevents it, and never notices that the join key is transmitted to both of them in plaintext.

Fix shape: per-register Reconciliation Identifiers, derived as the nonce is, with the shared identifier retained only server-side.

### 7.2 The Policy-Version Hash is a stable requester pseudonym disclosed to every register — BLOCKING

`{{sealing}}` item 7 commits the **Requester-Binding** to the Policy-Version Hash. `{{projection}}` requires the server to "send the same Policy-Version Hash to every addressed register in one reconciliation" (line 902), and the register echoes it under signature.

So the Policy-Version Hash is a stable, deterministic function of (policy state, requester identity, register set). Two reconciliations by the same requester under the same policy against the same registers carry an **identical** Policy-Version Hash. Every addressed register therefore holds a durable pseudonym under which it can bucket every reconciliation ever commissioned by one principal — its volume, its cadence, and every subject in it. If the register ever learns one principal's identity by any means, the whole bucket deanonymises retroactively.

The blinding value prevents *inverting* the hash. It does nothing about *linkage by equality*, which is the whole of the attack and requires no computation.

The Policy-Version Hash also appears in the Ledger reconciliation entry (line 2166) — which regulators, Audience Members and Audit Identities read — and in the protected header of every notarised Signed Statement, where it is public. So the same requester-bucketing is available to anyone who obtains two notarised Outputs.

### 7.3 What an Audience Member of one reconciliation learns about others

`{{settlement-ledger}}` handles most of this well: an Audience Member's read "discloses only facts about a reconciliation whose full content it already holds" (line 2358), and it explicitly names the one exception — a Post-Seal Evaluation Record carries the Policy-Version Hash and Pattern-Library Version Identifier in force at evaluation time, "values the member did not previously hold and, being stable within a deployment, are **durable correlators**" (lines 2363–2366). That is an unusually candid piece of analysis.

The wider leak is `GET /arp/sweeps`, entitled to "a Register Operator, a regulator **or an Audience Member**" (line 3440), returning Evaluation Sweep Statements whose counts are deployment-wide aggregates. The document records this as a cost (line 3442) and explains that the Statement is a signature over a fixed array and cannot be field-redacted. Both true. The consequence stands: being named in one Audience Set — which, per `{{audience}}`, is an assertion by a *requester* that the named party never consented to — buys deployment-wide volume telemetry, per trigger, over time.

### 7.4 Tree positions, sequence numbers, inclusion proofs

Clean. `{{merkle-construction}}` sorts and deduplicates leaves, so tree position carries no submission-order information — a deliberate divergence from CT that the document explains (line 1332). `{{aggregation}}` commits each register's attestation as its own leaf so "an inclusion proof discloses no other register's payload" (line 1395). Examined-Set Roots commit blinded Claim Hashes. The contiguous Entry Sequence Number is a size-and-rate disclosure, and the document says so in `{{privacy}}` and rate-limits the sweep. This part is well done.

---

## 8. THE LEGAL AND EVIDENTIARY ATTACK

What a defence lawyer says, in order of how much damage each does.

### 8.1 "The exhibit does not say who it is about." — BLOCKING

Per §1.1. The sealed Output contains a blinded Claim Hash and a set of register-specific Subject References. No party other than the requester and the server can establish that those references denote the defendant. The prosecution's own expert cannot recompute the Claim Hash without the Deployment Blinding Value, which the document forbids disclosing even to an Audit Identity (lines 2588–2594). The chain of signatures is impeccable and is anchored to an unattested step performed by an interested party.

### 8.2 "A register said the opposite and the arithmetic threw it away." — BLOCKING

Per §1.2. Under `conjunction`, `{match, no-match}` yields decisive `no-match`. The Output on its face carries a register-signed `match` and a Combined Verdict of `no-match`. The expert must explain to the tribunal why a designation by the listing authority was outweighed by a register that had never heard of the subject. There is no `conflicting` verdict value in which to express what actually happened.

### 8.3 "The operator could have withdrawn this exhibit at any time and still can." — BLOCKING

Per §1.4. `arp-key-status: revoked` makes every relying party's MUST reject this document. The evidentiary value of an artefact whose issuer can unilaterally and retroactively require its rejection, without stating a ground and without any record, is not high.

### 8.4 "Nobody ever checked whether the registers were asked." — BLOCKING

Per §1.6 and §2.1. `register-unresponsive` requires no artefact from anyone. The Output's assertion that a register did not answer is the unsupported word of the server. The document says so itself, at line 1466: "`register-unresponsive` is indistinguishable from a network failure by construction, **and this document does not pretend otherwise**." That sentence will be read aloud in court.

### 8.5 "The sweep that would have caught this was never defined." — BLOCKING

Per §1.5. "Sealed against a superseded Policy-Version Hash" names no set, because the Policy-Version Hash is per reconciliation. An operator can be fully conformant, sign and notarise every Statement, and have examined almost nothing.

### 8.6 What the document claims that it does not establish

The document is better than most at stating limits, and I want to be precise about which claims survive.

**Survives.** The register's own signature over its own verdict, its Query Binding, its agreement hash and its policy-version echo — this is genuinely independently checkable by a holder of the Output, via `{{sealing-key-discovery}}`, without the server's assurance. That is a real evidentiary property and it is well constructed. So is the Non-Answer Statement requirement: the distinction between "the register would not say" and "I did not ask" is preserved for the *register-attested* case, and `non-answer-unattested` correctly refuses to let a missing refusal fall back into a server-observed bucket (lines 1450–1462).

**Does not survive.** "Deterministic combined verdict" (line 216) — the combination rule is chosen by the operator and, per §1.2, is not sound over disagreeing witnesses. "The Claim Hash binds the Output to the question it answers" (line 1652) — only for the requester. "Without the server's assurance" as used for re-typing (line 1487) — an auditor can check the *arithmetic* of re-typing but not the *applied depth* it turns on, which the register chose per query (§2.2). "Subpoena-grade audit trail" (line 2492) — see §4.2.

**Correctly disclaimed already, and worth crediting.** `{{bra-limits}}` — "a relying party MUST NOT treat a met quorum as proof of observer diversity. It is proof that observer diversity was **declared**" (lines 3150–3154). `{{subject-digest-scope}}`. `{{post-quantum}}`. The `notarisation-incomplete` open question (line 2209: "That is open."). The falsifiability count in `{{sweep-statements}}`: "The falsifiability argument therefore holds for three triggers in four, **which is stated rather than rounded up**" (line 2718). The empty-result analysis in `{{read-responses}}` (lines 3510–3530), which walks itself from "an empty result is an assertion and not an absence" all the way to "and it is falsifiable only to the extent that the reader holds independent head evidence" — that is a specification arguing honestly against its own strongest claim, and it is rare.

---

## Where the document already defends well

Recording this because the review is worthless without it.

| Section | What it covers | What it misses |
|---|---|---|
| `{{merkle-construction}}` (1265–1382) | CT divergence at the empty tree; sorted+deduplicated leaves; the odd-node carry-up rule vs the duplicate-last convention, with the observation that a 4- or 8-leaf conformance vector will not detect the difference; ceiling-vs-truncation in width halving; no direction bit; rejection of proofs against the empty root | Nothing. Best section in the document. |
| `{{leaf-binding}}` (1354–1382) | Verifier MUST compute the leaf from the object and compare **before** walking; written over the object rather than the carried field so it is not vacuous under COSE Receipts | Nothing. |
| `{{signature-malleability}}` (4106–4166) | ECDSA `(r, s)` / `(r, n−s)`, with a measurement (200 keys, 200 substitutions); EdDSA's non-exposure and the cofactor caveat; conversion of every chaining digest to a Signing Input Digest; the correct observation that this is a verification failure, not a forgery, and that reporting it as tampering reports something that did not happen | Nothing. |
| `{{read-errors}}` (3562–3659) | 404-equivalence; the normalised-observation construction; rate-limit charged before entitlement; no short-circuit; `no-store`; refusal to claim timing indistinguishability without published measurement methodology | §4.1: `fields=linkage` reopens the redaction-recovery channel the same section closes |
| `{{source-versioning}}` (1105–1160) | Publisher-assigned state identifiers only; tuple form against collision; constancy across attestations so the identifier cannot vary per subject; skew ≠ disagreement; attribution of change to policy vs corpus | Applies its own reasoning to one field only (§2.3) |
| `{{containment}}` + `{{budget-suppression}}` (3925–4038) | Per-event vs per-sequence disclosure; budget keyed per principal per subject; shared counters as DoS; ceiling partitioning with a per-principal sub-budget; both mitigations considered and declined with reasons | Undefined subject key (§5.4); documents 2 of 4 determinism carve-outs (§1.6) |
| `{{no-answer}}` (1397–1479) | Every non-answer has a defined outcome; register-attested vs server-observed; signed Non-Answer Statements with the Reconciliation Identifier inside the payload; `non-answer-unattested` as a distinct reason | The register-side silent veto (§2.1) |
| `{{entitlement}}` (1750–1925) | Retires the bearer artefact; entitlement follows the Audience Set, not possession; durable verification methods; the retention floor extended by one reliance interval so the 404 does not arrive at the moment the obligation begins | Naming as a DoS vector (§5.3) |
| `{{bra-hash}}` (3059–3131) | Fixes the CBOR type of every item, the ordering within every set-valued one, and which four items may be null; distinguishes sequences from sets; states that Agreements MUST be recomputed and that comparing across revisions produces false drift | The direction rules are weaponisable (§5.1) |
| `{{witness-entries}}` / `{{bra-limits}}` | Common-control exclusion running in every direction, with the subsidiary-stacking attack named explicitly; URI normalisation for distinctness; and then the honest concession that independence is declared, not proven | Intersection as a kill-switch (§5.2) |

---

## Summary table — most severe first

| # | Direction | Finding | Where | Severity |
|---|---|---|---|---|
| 1 | 1, 8 | Subject Identifier → Subject Reference mapping is unrecorded; no verifier outside the server can check the Output is about the claimed subject | 668, 861, 1610ff, 1682 | **BLOCKING** |
| 2 | 1, 8 | `conjunction` yields a decisive `no-match` on any single dissent; a register with no record out-votes a designating authority | 1579–1583 vs 1568–1572 | **BLOCKING** |
| 3 | 1, 8 | `arp-key-status: revoked` is a unilateral, unrecorded, retroactive repudiation of every Output, entry and statement of an epoch | 3848–3852 | **BLOCKING** |
| 4 | 7, 6 | Reconciliation Identifier is a plaintext exact join key across sovereign registers; links national identifier spaces for one person | 858, 1648, 1990–1993 | **BLOCKING** |
| 5 | 1, 5 | Retroactive sweep set is undefined — Policy-Version Hash is per reconciliation, so "superseded Policy-Version Hash" names no set; selective evaluation is conformant | 2624, 1936–1937 | **BLOCKING** |
| 6 | 6 | A corrected register record is not a retroactive-evaluation trigger; a false verdict about a person is never revisited | 2618, 4302 | **BLOCKING** |
| 7 | 4 | `fields=linkage` returns to any signer the Self-Entry Hash that redacted regulator reads withhold, reopening the search-recovery channel off the audit trail | 3413–3420 vs 3637–3648 | **BLOCKING** |
| 8 | 2 | Any register holds a silent, deniable, per-subject veto via non-response; no artefact, no attribution | 1416, 1564 | **BLOCKING** |
| 9 | 5 | Direction rules weaponisable: one register's item 15 = 1s forces four MUST breaches and kills reads; item 18 unlocks ledger enumeration; item 17 forces indefinite retention | 1900–1918 | **BLOCKING** |
| 10 | 5 | Witness Set intersection: one register's disjoint set makes the deployment non-conforming and stops all reads for everyone | 3035–3046 | **BLOCKING** |
| 11 | 5, 6 | Audience-Set flooding exhausts a victim's read rate limit and forces breach of the `{{reliance-horizon}}` MUST | 1798–1804, 3628–3634 | **BLOCKING** |
| 12 | 6 | Notarisation exports Subject References, Audience-Member identifiers and Override operator names into an external append-only log with no deletion path | 3688, 1682, 3684 | **BLOCKING** |
| 13 | 6 | No RFC 6973 analysis; no erasure, rectification, lawful-basis, controller/processor or retention-limit treatment; exclusion named and deferred to a "outside this document" that the design forecloses | 4167–4209 | **BLOCKING** |
| 14 | 3 | Partial-Attestation length is unpadded: a passive observer distinguishes subject-exists from subject-absent on the register leg | 1161–1200, 1207–1230 | **BLOCKING** |
| 15 | 2 | Register chooses applied depth per query; re-typing turns on it; a register selects the Combined Verdict silently and per subject | 988, 1491 | **BLOCKING** |
| 16 | 1, 3 | Remediation Advisory returns matched Pattern-Library identifiers to any requester — the secret anti-evasion corpus is enumerable by probing; `audience-member-not-enrolled` is a free enrolment-roster oracle at an endpoint where `{{read-errors}}` forbids exactly this | 766–772, 3232 | **BLOCKING** |
| 17 | 4 | Portal and Audit access log is unsigned, unchained, unnotarised and held by the audited party — "subpoena-grade" is self-attestation | 2492, 3652 | **BLOCKING** |
| 18 | 6 | Open screening oracle: any keypair, including `agent-unverified`, may screen any named person, with no lawful-basis, purpose or relationship requirement | 3222, 723 | **BLOCKING** |
| 19 | 7 | Policy-Version Hash is a stable requester pseudonym disclosed to every register and public in every notarised header; linkage by equality, no inversion needed | 1937, 902, 2166 | **BLOCKING** |
| 20 | 3 | `{{side-channel}}` is 8 lines and does not cover register co-addressing, which `{{sealing}}` line 1991 explicitly says it discusses; no length, timing, fan-out or padding treatment anywhere | 1991, 4095–4104 | **BLOCKING** |
| 21 | 1, 8 | Retention expiry destroys the evidentiary artefact while the Ledger retains the correlatable one indefinitely; operator controls the floor | 1900, 1924, 2384 | LATENT |
| 22 | 1 | Addressed-Registers Identifier Set is unconstrained; the anti-cherry-picking gate is the operator's own unpublished corpus, run by the operator on itself | 620, 758, 1188 | LATENT |
| 23 | 1 | Policy-epoch store is the operator's; the predicate→operator/threshold/reliance mapping is bounded by nothing | 296, 1533–1560 | LATENT |
| 24 | 5, 6 | Query budget's subject key is undefined; requester controls the Subject Identifier, so the sole bound on record recovery is evadable and non-interoperable | 3960 | LATENT |
| 25 | 4 | Single-register reconciliation collapses the "every agreement" regulator trust-anchor defence to one register operator's unilateral choice | 2480, 2521 | LATENT |
| 26 | 2, 3 | Register-supplied Freshness Timestamp is both a per-subject channel and a control (force `attestation-stale` → `indeterminate`) | 1222, 4074 | LATENT |
| 27 | 1 | Registers under bilateral `x-` profiles need declare no Source-Data Version Identifier; their Outputs fall permanently outside every `source-data-version` sweep | 1107, 2626, 941 | LATENT |
| 28 | 5 | Witness Quorum of 0 is conformant deployment-wide; every empty result — including "no supersession" — is then permanently unfalsifiable, bounded only by a SHOULD | 3048–3058 | LATENT |
| 29 | 4 | Operator-key/sealing-key separation is a declaration republished by the register; nobody verifies distinct custody | 812–818, 3153 | LATENT |
| 30 | 7 | `GET /arp/sweeps` gives deployment-wide volume telemetry to any Audience Member — membership assigned by a requester, not consented to | 3438–3444 | LATENT |

---

## The two changes that buy the most

If only two things change: **carry the Subject Identifier binding into the Projection Record** (kills #1, and with it most of #8's evidentiary attack), and **derive per-register Reconciliation Identifiers as the nonce is already derived** (kills #4, and blunts #19). Both are small, local edits to sections that already have the right instincts everywhere else.agentId: ac853d1678bb2951b (use SendMessage with to: 'ac853d1678bb2951b', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 172965
tool_uses: 23
duration_ms: 690180</usage>