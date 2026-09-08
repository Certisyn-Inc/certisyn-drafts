# IPR Reconciliation: draft-hillier-scitt-arp-04

**Document:** CS-IPR-RECONCILIATION-ARP-04
**Entity:** Certisyn, Inc. - Salt Lake City, Utah
**Prepared by:** Joel Hillier, Founder and CEO
**Date:** 7 September 2026
**Version:** 1.0
**Classification:** CONFIDENTIAL - Not for Distribution
**Subject:** Reconciliation of the 7 IETF IPR disclosures on file against revision 04, prepared before posting -04 to the Datatracker.

---

## 1. Executive summary

| Item | Position |
|---|---|
| Disclosures on file for draft-hillier-scitt-arp | 7 (IDs 7585-7591), all filed 1 September 2026 |
| Revision range each disclosure names | 00-03. None names 04. |
| Licensing declaration on all 7 | No License Required |
| Disclosed sections still present in -04 | 12 of 12, plus Appendix C. None deleted or restructured. |
| Section numbers cited in all 7 | Stale against -04 by a uniform shift of 1 at the top level |
| Sections new in -04 with no counterpart in -03 | Approximately 20, including the entire witness apparatus |
| Estate status, from the Office XML export of 2 September 2026 | 101 applications. Nothing abandoned. Nothing missing. |
| Formality outstanding on F39 | Notice to File Missing Parts, due 12 October 2026 |

**Bottom line.** Every disclosure's substance survives into -04 and nothing disclosed was removed. 2 items require action: the revision range and section numbers in all 7 disclosures are now wrong for -04 and should be updated, and a determination is required on whether the material that is new in -04, principally the witness quorum apparatus, is supported by any application on file.

---

## 2. The disclosures as filed

Retrieved from the IETF Datatracker on 7 September 2026. F-numbers resolved against the estate roster.

| Disclosure | Application | F | Filed | Scope as written |
|---|---|---|---|---|
| 7585 | US 64/041,845 | F27 | 17 Apr 2026 | Section 4.8 Partial Attestation Reception, Section 4.9 Merkle Construction, Section 4.10 Aggregation |
| 7586 | US 64/041,847 | F28 | 17 Apr 2026 | Section 4.16 Policy-Version-Hash Sealing, Section 4.17 Post-Seal Evaluation Records |
| 7587 | US 64/048,589 | F46 | 24 Apr 2026 | Section 4.19 Regulator Portal, Section 4.20 Audit Path |
| 7588 | US 64/049,282 | F62 | 4 May 2026 | Appendix C, composition with the RATS architecture; and Section 4.16 |
| 7589 | US 64/058,190 | F71 | 5 May 2026 | Section 4.3 Adversarial Pre-Transmission Test, Section 7.3 Pattern-Library Integrity |
| 7590 | US 64/058,242 | F81 | 6 May 2026 | Section 4.21 Retroactive Evaluation, including 4.21.1 and 4.21.2 |
| 7591 | US 64/048,165 | F39 | 24 Apr 2026 | The reconciliation protocol the document specifies, throughout. Also covers 2 further drafts. |

All 7 are United States provisional applications under 35 U.S.C. 111(b), filed by Certisyn, Inc. All 7 declare **No License Required**, which is the most permissive position available under RFC 8179 and forecloses licence revenue from the disclosed claims for implementations of the specification.

6 of the 7 are scoped to named sections. Disclosure 7591, against F39, is scoped to the document as a whole.

---

## 3. Section mapping, -03 to -04

Revision 04 inserts a new top-level Section 3, Relationship to Other Work. Every section below it shifts by 1. Verified by title match against the filed -03 text and the built -04 text.

| Disclosed section, -03 numbering | Title | -04 numbering |
|---|---|---|
| 4.3 | Adversarial Pre-Transmission Test | 5.3 |
| 4.8 | Partial Attestation Reception | 5.8 |
| 4.9 | Merkle Construction | 5.9 |
| 4.10 | Aggregation | 5.10 |
| 4.16 | Policy-Version-Hash Sealing | 5.16 |
| 4.17 | Post-Seal Evaluation Records | 5.17 |
| 4.19 | Regulator Portal | 5.19 |
| 4.20 | Audit Path | 5.20 |
| 4.21 | Retroactive Evaluation | 5.21 |
| 4.21.1 | Evaluation Sweep Statements | 5.21.1 |
| 4.21.2 | Revocation and the reliance window | 5.21.2 |
| 7.3 | Pattern-Library Integrity | 8.3 |
| Appendix C | Composition with the RATS Architecture | Appendix C, unchanged |

No disclosed section was deleted, merged or restructured. The substance of all 7 disclosures is intact in -04.

---

## 4. What is new in revision 04

Approximately 20 sections in -04 have no counterpart in -03. The material one for this reconciliation is the witness apparatus, which is absent from -03 entirely. Term counts, filed -03 text against built -04 text:

| Term | -03 | -04 |
|---|---|---|
| Witness Set | 0 | 29 |
| Head Consistency Statement | 0 | 14 |
| Witness Quorum | 0 | 11 |
| quorum rule | 0 | 4 |
| Witness Linkage Segment | 0 | 8 |
| fields=linkage | 0 | 4 |
| Attestation Floor | 0 | 6 |

Also new since -03: the Bilateral Register Agreement and the Agreement Hash, Coverage Probes, Representation Invariance, Signature Malleability and Artefact Identity, Declared Trade-offs, Subject Mapping Record, Aggregate Statements, and Relationship to Other Work.

None of this material falls inside any of the 6 section-scoped disclosures. Disclosure 7591 is scoped to the protocol throughout and on its face follows the document into new material.

**The distinction that governs.** A disclosure's scope statement records what the disclosure relates to. It does not establish that the underlying application describes the mechanism. F39 was filed 24 April 2026. The witness apparatus did not exist in the specification until revision 04. Whether F39 as filed supports claims to that apparatus is determined by what F39 discloses, and is a question for patent counsel reading F39 against the -04 text.

**The consequence of publication.** Posting -04 places the witness apparatus in the public domain on the posting date. Where an application already describes the mechanism, publication is immaterial. Where none does, publication forecloses foreign patent rights immediately and starts the 12-month United States grace period.

---

## 5. Estate position

Source order of authority, per the estate remediation record of 3 September 2026: the USPTO file wrapper, then the notices, then ESTATE-ROSTER.md, then DOCKET.md, then everything else. The spreadsheet trackers have been wrong 7 times and are not authority.

From the Office XML export taken 2 September 2026: **101 applications, 98 provisionals and 3 non-provisionals, F1 through F97 all present. Nothing abandoned. Nothing missing.**

**F39, application 64/048,165, is the Attestation Reconciliation Protocol filing.** It carries disclosure 7591, the only document-wide disclosure on the draft. 2 matters stand against it:

1. A Notice to File Missing Parts, requiring a signed cover sheet, micro entity certification and the surcharge, **due 12 October 2026**.
2. The file wrapper carries 11 documents and no DRW code. Figures were never deposited.

Provisional terms run 12 months from filing:

| F | Application | Lapses |
|---|---|---|
| F27 | 64/041,845 | 17 April 2027 |
| F28 | 64/041,847 | 17 April 2027 |
| F39 | 64/048,165 | 24 April 2027 |
| F46 | 64/048,589 | 24 April 2027 |
| F62 | 64/049,282 | 4 May 2027 |
| F71 | 64/058,190 | 5 May 2027 |
| F81 | 64/058,242 | 6 May 2027 |

---

## 6. Actions arising

1. **Update all 7 disclosures.** The Datatracker exposes Update this IPR disclosure against each record, so each is an update against the existing ID and not a refiling. Change the revision range from 00-03 to 00-04 and restate the section numbers per the mapping in Section 3.
2. **Determine coverage of the new material.** Patent counsel to read F39 against the -04 witness apparatus and advise whether it is supported, and whether a further application or a further disclosure is required.
3. **Cure the F39 formality by 12 October 2026.** F39 carries the only document-wide disclosure on this draft.
4. **Confirm the licensing position.** No License Required is declared on all 7 and is difficult to reverse once implementers have relied on it.

---

## 7. Sources

- IETF Datatracker, IPR disclosures 7585 through 7591, retrieved 7 September 2026.
- draft-hillier-scitt-arp-03.FILED.txt, repository scitt-arp-f39.
- draft-hillier-scitt-arp-04, built 7 September 2026 from draft-hillier-scitt-arp.md.
- USPTO Applications by Customer XML export, 2 September 2026, archived under USPTO Correspondence 2026.
- CS-SEED-PATENT-REMEDIATION-AND-FILING-2026-09-03.md, Sections 1 and 3.
- DOCKET.md, USPTO Correspondence 2026.
