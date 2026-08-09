# Response to the review of draft-hillier-scitt-arp-02

Checked against the filed text, `draft-hillier-scitt-arp-02`, 8 August 2026.

The review makes three specific asks and one general one. One ask is correct and
I am adopting it. One is factually wrong about this draft. One rests on a
misreading of what the draft is for. The general criticism is half right, and I
will say which half.

---

## 1. Post-quantum: already there, normatively

> "clear pathways for adopting post-quantum cryptography"

This is the ask I can answer by citation rather than argument. -02 does not
gesture at post-quantum migration; it requires it.

- **§ Cryptographic-Primitive-Upgrade Path** carries a MUST: a conforming
  primitive set "MUST include at least one post-quantum primitive for each
  class," drawn from a set including ML-KEM (FIPS 203) for key encapsulation
  and ML-DSA (FIPS 204) for signatures.
- **§ Post-Quantum Migration**, in Security Considerations, names the
  parameters: ML-KEM-1024 RECOMMENDED for the claim-encryption primitive class,
  ML-DSA-65 RECOMMENDED for the partial-attestation-signature and
  reconciliation-output-signature classes.
- Chosen primitives are pinned in the Bilateral Register Agreement, so the
  upgrade is a negotiated parameter of the agreement rather than a flag day.
- FIPS 203 and FIPS 204 are cited references, not prose mentions.

A review that reached the Security Considerations could not have written this
sentence. I would rather have that said plainly than have it stand as an open
item against the draft.

## 2. SBOM formats and DevOps tooling: a category error

> "native translation layers for common supply chain formats" /
> "better integration with existing DevOps tools"

ARP is layered on SCITT, and I think that adjacency is doing the work here — the
assumption being that anything SCITT-adjacent is a software-supply-chain
profile. ARP is not one.

The registers ARP reconciles are **sovereign authoritative registers**:
beneficial-ownership registers, consolidated sanctions lists, export-control and
FOCI registers, corporate registries, land title, customs declarations,
flag-state and aviation registration, multilateral biometric registers. The
relying parties are export-control compliance officers, AML review functions,
foreign-investment screening bodies and sanctions-screening operators.

There is no SPDX document in that pipeline, no CycloneDX BOM, no CI job. A
"native translation layer for CycloneDX" would be a translation layer to
nothing. The mechanism ARP needs in that slot is the controlled projection
function — mapping a claim to the nearest permitted ancestor predicate each
register can actually answer — and that is specified.

What -02 *does* define for interoperability, which is the legitimate version of
this ask:

- CBOR-COSE encoding
- HTTP Message Signature binding (RFC 9421)
- Verifiable Credentials JSON-LD interop
- registered media types in IANA Considerations

If the reviewer means a specific non-software format — a sanctions list schema,
a beneficial-ownership exchange format — that is a concrete and welcome
suggestion, and I would take it. Named formats beat "common supply chain
formats."

## 3. SCRAPI: the ask lands, and I am adopting it

> "direct mapping to the evolving SCITT Reference APIs (SCRAPI)"

This one is right, and the distinction matters.

-02 cites SCRAPI in four places and composes with it at the **architectural**
level — § Composition with the SCITT Architecture states that Reconciliation
Outputs MAY be notarised into SCITT registries as transparent statements, and
that registration and retrieval MAY use the SCITT Reference APIs.

That is a permission, not a binding. There is no operation-by-operation mapping:
which SCRAPI endpoint registers a Reconciliation Output, what the payload looks
like on the wire, what a receipt for one is, how retrieval by policy-version
hash works. Two implementers reading -02 could both conform and fail to
interoperate against the same Transparency Service. That is a real gap and the
review is right to name it.

The reason it is not in -02: `draft-ietf-scitt-scrapi` is at -11 and in the RFC
Editor queue. Binding wire-level detail to a document still moving would have
produced a mapping that needed reissuing. That was a judgement call about
sequencing, and it is defensible — but it is not a reason the mapping should
never exist, and stating it as future work is weaker than doing it.

**For -03:** a normative SCRAPI binding section — endpoints, payload shapes,
receipt semantics for a Reconciliation Output, and retrieval keyed on the
policy-version hash. If SCRAPI publishes as an RFC first, the binding cites the
RFC.

## 4. "Lacks practical, easy-to-implement guidelines"

Half right, and worth separating.

Against it: -02 carries four worked examples — a three-register sanctions
reconciliation, retroactive re-evaluation under an updated pattern library, an
agentic principal reconciliation, and a divergent agent-action reconciliation —
each with concrete values rather than prose. There is also a public conformance
harness: published vectors, committed run transcripts, and a documented
reproduction path, including two-sided vectors that fail in both directions so a
check that stops testing anything is caught.

Conceded: there is no reference implementation, and examples are not one. A
reader who wants to know whether their projection function is correct has worked
examples and vectors, but no code to diff against. That is the honest version of
this criticism and it is the one I would act on.

---

## Summary

| Ask | Status |
|---|---|
| Post-quantum pathway | Already normative in -02; MUST plus named parameters |
| SBOM / DevOps translation layers | Out of scope by subject matter, not by omission |
| SCRAPI mapping | **Valid.** Architectural only; wire-level binding scheduled for -03 |
| Practical guidance | Examples and conformance vectors exist; reference implementation does not |

One request in return. Two of these four are answerable from the draft's own
table of contents, and a review that engages the Security Considerations and the
composition appendices will be more useful to me than one that does not — I would
rather be told something I cannot already check.
