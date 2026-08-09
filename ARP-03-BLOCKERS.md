# ARP-03: not fileable, and why

Two red-team passes. The first found 15 defects in the new -03 material. Those
were fixed. The second pass, run against the fixes, found **12 new defects
introduced by the fixes themselves** — including that the fix to the single most
important one is prose-only and still unverifiable.

That pattern is the finding. When a round of repairs generates a fresh
generation of defects, the work has not converged, and a third patch round would
produce a third generation. -03 is not close.

**-02 is filed, sound and idnits-clean. It stands as today's filing.**

---

## Root cause: -03 adds fields to a structure that was never enumerated

This is pre-existing, not introduced by -03, and it is why every fix spawns a
new defect. Confirmed against the current file:

| Term | Status |
|---|---|
| `Reconciliation Output` | Used throughout. **No field enumeration anywhere.** Partial Attestation has one; the Ledger entry has one; this does not. |
| `Reconciliation Hash` | Used 5 times, including in the bit-for-bit determinism requirement. **Never defined.** |
| `Combined Verdict` | Carries 5 new MUSTs in -03. **Never defined in terminology.** |

-03 adds roughly eight new normative requirements about what the Reconciliation
Output carries — answered depth per register, per-register Source-Data Version
Identifiers, three new divergence axes, an attribution statement. None is
testable, because there is no enumeration to test against and no definition of
the hash that covers it.

**This must be fixed first.** Enumerate the Reconciliation Output, define
`Reconciliation Hash` and `Combined Verdict`, and decide whether the divergence
axis is a single value or a set. Every open item below then becomes tractable;
without it they stay unfixable.

## The three that need design decisions, not edits

**1. The Signed Statement is not bound to the Sealing Signature.**
-03's centrepiece argument is that carrying the policy-version hash in a
protected header beats a query pattern, because the receipt covers it. The fix
added: *"The Signed Statement MUST be signed by the entity that applied the
Sealing Signature... and the `arp-policy-version-hash` in its protected header
MUST equal the Policy-Version Hash committed to by that Sealing Signature."*

A relying party cannot check either. The payload is the bare Reconciliation
Output; the sealed COSE_Sign1 is not nested inside it, and no trust anchor for
the sealing key is defined anywhere in the document. The requirement is real and
unverifiable — which is the exact defect class -02's red team was run to catch.

*Decision needed:* nest the sealed COSE_Sign1 as the registered payload, or
define a sealing-key trust anchor. The first is simpler and probably right.

**2. Profile identifiers are shared, but profiles must declare per-register
facts.** `arp-profile-bods` is one registered identifier, yet a BODS profile
must declare an interest threshold and a maximum chain depth — both of which
vary by register and jurisdiction. Two BODS registers with different thresholds
cannot both use the identifier, which defeats the registry that was just added.
It also contradicts `#source-versioning`, which locates the same kind of
declaration in the Bilateral Register Agreement.

*Decision needed:* profile identifiers name a vocabulary and parent relation
only; per-register parameters move to the Bilateral Register Agreement.

**3. Divergence Axis is now carrying things that are not divergences.**
`notarisation-incomplete` qualifies a notarisation attempt that happens *after*
sealing; `attribution-indeterminate` is produced by Retroactive Evaluation
against an already-sealed Output. Neither can travel in a Partial Attestation
(the register never sees the Transparency Service) nor in the Reconciliation
Output (both arise after it is sealed). They have no carrier.

*Decision needed:* a separate post-seal Evaluation Qualifier structure, or drop
both values.

## Mechanical, once the above is settled

- `arp-bilateral-agreement-hash` now means a single hash in `#encoding` and a
  sorted array in `#registration`, under one IANA registration with no stated type.
- Source-Data Version Identifier is singular in the Partial Attestation but
  `#profile-sanctions` contemplates several lists per register.
- `arp-source-data-version` is requested from IANA and never used on the wire.
- The Divergence-Axis registry says "the descriptors enumerated in terminology",
  but terminology says "a controlled set **including**" — an open set. IANA
  cannot populate from it.
- BODS forced `indeterminate` silently overrides declared Verdict Arithmetic and
  discards a true `match` found at depth 1.
- "record it where it affects the Combined Verdict" — no rule relates a
  divergence axis to verdict computation, so the condition is untestable.
- Freshness Timestamp is listed *after* the signature line in the Partial
  Attestation enumeration, i.e. unsigned — pre-existing, but the new
  freshness/skew distinction now rests on it.

## What is worth keeping

The substance is good and the review that prompted it was right. Specifically:

- **Source-data version binding is a genuine contribution.** A sanctions verdict
  without a list version is not reproducible, and -02 could record that a
  historical verdict changed without being able to attribute the change. That
  insight survives all of the above.
- **Declining the SCRAPI query-pattern ask was correct.** SCRAPI genuinely has
  no query surface — verified against -11. The refusal is right; only the
  substitute mechanism needs work.
- **The factual corrections are verified and should carry forward:** UN/CEFACT
  and WCO express authority determinations as well as declarations (LPCO,
  Declaration Response, eCERT); consolidated sanctions lists are event-driven,
  not on a cadence, and only OFAC publishes deltas; `org:FormalOrganization`
  does carry legal recognition.

## Recommendation

File nothing further today. -02 is filed and clean. Take -03 through one
working session that starts with the Reconciliation Output enumeration and the
two missing definitions, then re-runs both red teams. The email drafts should
continue to reference -02, which is what is actually published.
