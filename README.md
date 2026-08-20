# Certisyn Internet-Draft sources

xml2rfc and markdown sources for Internet-Drafts authored by Joel David Hillier, Certisyn, Inc.

| Draft | Directory | Datatracker |
|---|---|---|
| Attestation Reconciliation Protocol | this directory | https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/ |
| The Coverage Attestation Profile (CAP-1) | `cap-1/` | https://datatracker.ietf.org/doc/draft-hillier-coverage-attestation/ |

## CAP-1, the Coverage Attestation Profile

A tool-agnostic vocabulary for stating what an examination examined, what it did not, and why. Eight normative rules, eight closed dispositions, and a denominator that has to state its own basis.

`cap-1/` holds the draft source and the complete runnable conformance class in `cap-1/src`: three independent verifier implementations, fifteen vectors, the mutation harness and the run records. Specification text is CC BY 4.0, code is Apache-2.0. See `cap-1/README.md`.

---

# Attestation Reconciliation Protocol (ARP)

`draft-hillier-scitt-arp` — IETF Internet-Draft, individual submission
to the SCITT Working Group.

| Field        | Value                                                                          |
|--------------|--------------------------------------------------------------------------------|
| Draft name   | `draft-hillier-scitt-arp`                                                      |
| Revision     | `00`                                                                           |
| Author       | Joel David Hillier <jhillier@certisyn.com>                                     |
| Affiliation  | Certisyn, Inc. (Delaware, USA)                                                 |
| Submitted    | 2026-05-01                                                                     |
| Workgroup    | SCITT (Supply Chain Integrity, Transparency, and Trust)                        |
| Category     | Standards Track                                                                |
| Datatracker  | https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/                      |
| HTMLized     | https://datatracker.ietf.org/doc/html/draft-hillier-scitt-arp                  |
| Plain text   | https://www.ietf.org/archive/id/draft-hillier-scitt-arp-00.txt                 |
| HTML         | https://www.ietf.org/archive/id/draft-hillier-scitt-arp-00.html                |

## What ARP is

A deterministic, bilateral, zero-knowledge-capable protocol for
reconciling verification claims against a plurality of sovereign
authoritative registers (FinCEN BOSS, UK PSC, EU AML, OFAC SDN, EU
Consolidated, FOCI, maritime and aviation, multilateral biometric)
without raw register records leaving their data-residency jurisdiction.

ARP extends the SCITT architecture to cross-sovereign claim
reconciliation. Outputs are sealed against a policy-version hash and
notarised on an append-only cross-jurisdictional settlement-layer
ledger that records only hashes — no content from any underlying
register.

## Three deficiencies addressed in combination

1. **Raw-record disclosure.** Existing approaches require the raw
   register record to leave its data-residency jurisdiction or be
   re-disclosed in plaintext to a relying party. ARP transmits only
   register-specific ciphertexts and receives only verdict-plus-
   divergence-axis partial attestations.

2. **Non-reconcilable register outputs.** Each sovereign register
   exposes a different schema, signing chain, verdict semantic, and
   statutory access regime. ARP canonicalises the claim once and
   projects it through register-specific controlled-projection
   functions producing the greatest-lower-bound predicate per register.

3. **Non-auditable settlement.** Cross-sovereign reliance, where it
   occurs, occurs without a settlement-layer audit trail consumable by
   sovereign regulators. ARP seals every reconciliation output against
   a policy-version hash and notarises on an append-only ledger
   recording only hashes.

## Intellectual property

These Internet-Drafts are Certisyn's standards-track contributions.
Contributions to the IETF are governed by BCP 78 and BCP 79, and any
applicable IPR disclosures are filed with the IETF alongside the
submission. Rights not granted under those provisions are reserved by
Certisyn, Inc.

## Composition

ARP composes with the SCITT architecture
(`draft-ietf-scitt-architecture`, `draft-ietf-scitt-receipts`) and
the RATS architecture (RFC 9334). SCITT receipts may be input claims
to ARP; ARP outputs may be notarised as SCITT transparent statements;
the reconciliation server may run inside a RATS-attested confidential-
computing boundary. A separate forthcoming draft will specialise ARP
to compute-attestation reconciliation across heterogeneous TEE/CC
providers.

## Status

- 2026-05-01 — `-00` posted to IETF Datatracker (individual submission)
- TODO — request review on `scitt@ietf.org` mailing list
- TODO — incorporate WG feedback into `-01`
- TODO — request WG-document adoption

## Source

The draft source is `kramdown-rfc` Markdown at
`draft-hillier-scitt-arp.md` in this repository. Build instructions
are in `BUILD-AND-SUBMIT.md`.

## Filing trail

| Date       | Event                                                          |
|------------|----------------------------------------------------------------|
| 2026-04-27 | Draft prepared in `kramdown-rfc` Markdown form                 |
| 2026-04-29 | Idnits validation pass; -00 generated to xml/text/html/pdf     |
| 2026-05-01 | Submitted to IETF Datatracker as submission #162795             |
| 2026-05-01 | Posted by IETF Secretariat after author confirmation            |

## Contributing

Review and pull requests welcome. The intended audience is the SCITT
working group and operators of sovereign authoritative registers in
the AML, FOCI, sanctions, export-control, beneficial-ownership, and
multilateral identity domains.

For substantive technical feedback, please post to `scitt@ietf.org`
with reference to this draft so the WG record captures the discussion.
For editorial corrections, file a PR against
`draft-hillier-scitt-arp.md` in this repository.

## Licence

The Internet-Draft itself is governed by the IETF Trust Provisions
(BCP 78). The repository contents (build scripts, README, supporting
material) are MIT-licensed. The `cap-1/` directory carries its own
licences: specification text under CC BY 4.0 and code under Apache-2.0,
see `cap-1/LICENSE` and `cap-1/LICENSE-SPEC`. Other rights are reserved by Certisyn,
Inc.

## Maintainer

Joel David Hillier · Certisyn, Inc. · jhillier@certisyn.com


