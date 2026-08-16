# ARP-04

**Read this file first. Everything else in this folder is derived from it or superseded by it.**

Working document for `draft-hillier-scitt-arp-04`. Owner: Joel Hillier.
Opened 2026-08-14, the day `-03` posted. Last updated 2026-08-16. Supersedes
every `-03`-era note in `archive/arp-03/`.

**Sections 10 to 12 are the live edge.** Two commitments to other authors closed
on 16 August and are verified from the remote; two remain open with dates.

---

## 1. Where `-03` landed

`draft-hillier-scitt-arp-03` posted **2026-08-14 at 04:24:24 UTC**, submitted as
xml2rfc v2 XML built by kramdown-rfc 1.7.39, logged in as `jhillier`. Standards
Track, Individual Submission, 127 pages, expires 14 February 2027.

Submission status page:
`https://datatracker.ietf.org/submit/status/167720/e055c01d780f5fb3720db4783868aa12/`

| artefact | sha256 | size |
|---|---|---|
| `draft-hillier-scitt-arp.md` | `e8cb3b93dcea2f0b1e0a35da03f95d04ce425bb6717e15e8eafad9ecf85641d1` | 291,282 B |
| `draft-hillier-scitt-arp-03.txt` | `fe7ba656ef07842c365ce93938610cd874668c29f0fa06031d37d0e4e72b395d` | 7,112 lines, 339,537 B |
| `conformance-tree.zip` | `ea1c326522913b7cb8e3959837b4d17876e15904f0b160dc3968c4411314f64d` | 265,566 B |
| `runners/run_existence_oracle_vectors.py` | `1b2ff11dcb46f42bdab4e2eba34a996d91f7bbe174e768ec9d55c8e04cc888f6` | |
| `runs/existence_oracle_run.json` | `74df0c9aae6a6d230c1ecc1a9fc92be2ace571be411c50666e7cf8bfb5199869` | |

**The archive copy was fetched back and hashed.**
`https://www.ietf.org/archive/id/draft-hillier-scitt-arp-03.txt` is `fe7ba656...`,
339,537 bytes, byte-identical to the local build. Do this on every filing. It is
the only check that establishes the datatracker served what was built.

Source and evidence are on `wip/revision-03` at commit `2e1993a`, pushed and
verified by fetching the three files back out of the GitHub API rather than
trusting the working copy. All three match the digests above.

idnits on the filed bytes, networked: **1 error, 11 warnings**. The error is the
RFC 8785 downref, deliberate and disclosed in the Note to the RFC Editor per
Section 2 of RFC 8067.

---

## 2. What `-04` has to carry

Seven items. Each states who found it, what the evidence is, and what closing it
looks like. Nothing here is a claim `-03` makes.

### 2.1 Section 4.9 has to state its relationship to RFC 6962

**Found by Tom Sato, 2026-08-14, on the CPB-01 thread.** He read the empty-tree
rule as a defect and was right to.

Section 4.9 defines a Merkle construction and never mentions RFC 6962 anywhere in
the document. Any implementer arriving from Certificate Transparency will assume
RFC 6962 and will get the empty tree wrong.

Measured, by executing both constructions rather than comparing prose:

- ARP's odd-node rule, where the last node at a level is carried up unchanged
  rather than duplicated, and RFC 6962's recursive split at k equal to the
  largest power of two below n, produce **identical roots for every leaf count
  from 1 to 128**.
- **Identical inclusion-proof sibling arrays for all 2,080 (leaf count, index)
  pairs up to 64 leaves.**
- They diverge at exactly one point in that whole range: the empty tree. ARP
  gives thirty-two zero octets. RFC 6962 gives MTH of the empty set equal to
  SHA-256 of the empty string, `e3b0c442...`.

The divergence is deliberate and worth keeping. `e3b0c442...` is a well formed
digest that a verifier reproduces successfully and may then treat as a root that
commits to something. Thirty-two zero octets is a value no commitment produces,
so it cannot be mistaken for one. Section 4.9 already requires a verifier to
reject any proof presented against the empty root, and that rule does the work
under either convention.

**Close it by:** stating in Section 4.9 that the construction is RFC 6962
Section 2.1's Merkle Tree Hash for every non-empty tree and departs from it only
at the empty tree, with the reason. Add RFC 6962 as an informative reference.
This is text, not mechanism. It is the cheapest item on this list and the one
most likely to prevent a wrong implementation.

**No vector regeneration is required.** `typed-ref-cpb01-04` does not pin a digest
as its expected result. Its `expected` block is `verified: false`, checked by
comparing `leaf_input`, 32 raw bytes against the 64-byte hex encoding,
distinguishable by length alone. Its `vds_note` records that CPB-01 Section 6 is
VDS-agnostic and Section 6.1 constrains the input only. The digests it carries
sit in an `illustrative_derivations` block marked non-normative and are already
the 0x00-prefixed RFC 6962 forms, `47558aa8...` correct and `35258dc3...`
incorrect. All four digests in that block were recomputed on 2026-08-14 and
verify. GAR-04's move to RFC 6962 Section 2.1 brought GAR onto the values the
vector already recorded.
### 2.2 The witness quorum Section 6.4.3 names but does not specify

**Found by Walter Hawkins, adopted into `-03`.** Section 6.4.3 now says an empty
result is falsifiable to the extent the reader holds head-consistency evidence
for the served chain from an observer independent of the responding service, and
carries a SHOULD on the relying party with witness countersignature over the head
preferred to an independently anchored head digest.

`-03` names the evidence that bounds the gap. It does not specify a quorum, and
says so.

**Close it by:** specifying the witness set and the quorum rule in the register
binding. This is easier than it was before `-03`, because the condition it has to
satisfy is already written down and already normative.

### 2.3 Two conformance channels that have never been exercised

The aggregate reads `PASS_WITH_DECLARED_GAPS`, six of eight controls exercised.
The two that are not:

- **`NV-ARP-EO-05`.** The same-work requirement of Section 6.4.4 is structural and
  is not decidable by response comparison. Recorded with
  `designed_discriminator: null`, which is the finding rather than a missing one.
- **`NV-ARP-EO-04`.** Refuses, but through a fallback branch. The defective
  endpoint answers 404 before charging the rate-limit counter, so it never
  reaches 429, so the designed discriminator, an equal 404 and 429 transition
  index, never executes. The budget-ordering channel is untested. **Found by
  Songbo Bu, by reading the aggregate rather than the verdicts.**

**Close them by:** giving `NV-ARP-EO-05` a wire-observable discriminator or
retiring it and saying why; and rebuilding the `NV-ARP-EO-04` fixture so the
endpoint reaches its budget before answering.

### 2.4 The class is one-sided

Every negative control is fault injection into an endpoint written by the
specification's author from his own reading of his own text. That is the one
configuration that cannot surface a specification defect.

**Close it by:** getting the class to refuse an endpoint written by somebody else
working only from the text. Until then, specification adequacy is untested and
the run record says so in `does_not_establish`.

### 2.5 Encoder independence

Request-binding and deterministic CBOR are computed with functions imported from
the implementation under test. An encoder defect, including an RFC 8949 Section
4.2.1 map-ordering violation, is invisible to this class.

This matters beyond the document. A widely used CBOR library, in its canonical
mode, applies a different map-ordering rule than RFC 8949 Section 4.2.1, so an
implementation importing it ships non-conforming bytes with no error.

**Close it by:** computing the expected bytes with an independent encoder, or by
adding a vector whose expected bytes are fixed in the file rather than derived at
run time.

### 2.6 Timing

`NV-ARP-EO-06`, the statistical timing row of the class as designed, is not
carried as a conformance row. It is reported as `timing_observation` and is not
adjudicated. No timing-resistance claim is made and none is tested. The loopback
observation is not evidence about a deployed path.

**Close it by:** leaving it alone unless a timing claim is added. If a claim is
added, it needs a test on a deployed path, not on loopback.

### 2.7 The register binding

Already the `-04` headline before any of the above. Section 2.2's quorum belongs
inside it.

---

## 3. Family coherence

The three drafts share one Verification Reconciliation Object, one issuing-partner
framework, and one cryptographic-continuity model. A change to any of these five
rows in one draft is a change to the family.

| element | ARP | E8V | AIGV |
|---|---|---|---|
| VRO content model | Reconciliation Output | Section 6 | Section 6 |
| Issuing-partner framework | Bilateral Register Agreement | Section 7 | Section 7 |
| Anchor and continuity | Sections 3.8, 3.12 | Section 8 | Section 8 |
| Maturity or verdict scale | match, no-match, partial, indeterminate | One, Two, Three | Documented, Operational, Adversarial-ready |
| Registry | Settlement-Layer Ledger | public attestation registry | public attestation registry |

Open family items, none of them blocking:

- **Cross-references are pinned one revision behind.** Each `-02` cites the other
  at `-01`. Repoint both at `-03` when the family is next co-filed.
- **`essential-eight` has no postal address.** The datatracker author record reads
  "unknown country" where `ai-governance` reads "United States". Add the same
  street, region, code and country block.
- **`essential-eight` Section 9 has no reciprocal SCITT composition paragraph** to
  match `ai-governance` Section 9. The family should read symmetrically.
- **Author name** renders "Hillier, J." in reference blocks and "J. D. Hillier" on
  the title page. Cosmetic. Fix in the datatracker author record.
- **`chorale-protocol-03` is unfiled.** Two things to settle before it goes: it
  carries no `date:`, so a build stamps it with whatever day it ran, and the
  author email is `joel@certisyn.com` where the other three use
  `jhillier@certisyn.com`. There is no `joel@certisyn.com`.
---

## 4. How to reproduce anything in section 1

From the conformance tree, whether cloned or unpacked:

```
unzip conformance-tree.zip
cd conformance
python3 runners/run_existence_oracle_vectors.py     # no arguments
python3 runners/verify_manifest.py
```

Expected: `DETERMINISTIC RESULT: PASS_WITH_DECLARED_GAPS`, exit 0, run digest
`74df0c9a...`, and `MANIFEST: PASS`.

Ordering constraint. `runs/existence_oracle_run.json` records
`spec_source_sha256` over `../draft-hillier-scitt-arp.md`, so it is evidence about
one revision of the draft and its digest changes whenever the draft does. Freeze
the draft source first, then run the existence-oracle runner, then run the
manifest check. A run generated before the last edit to the draft fails the
manifest, which is intended behaviour and not a defect in the runner.

Full command list, nine items, is in `conformance/REPRODUCE.md`.

To check the filing record itself against the IETF rather than against itself:

```
python3 verify-filings.py --dir .
```

in `drafts/ietf/` or in the OneDrive folder at
`02 - Strategy and IP/Current/Standards/IETF-Drafts/`. It asks the datatracker
submission API which revisions are actually posted and fails on any the register
omits, then fetches each `.FILED.txt` from the archive and fails unless the local
copy is byte-identical. Exit 2, not 0, if either service is unreachable.

Build the document with kramdown-rfc 1.7.39 and xml2rfc 3.34.0. Run idnits on a
networked machine only. An offline idnits run reported 18 errors on `-03` where
the networked run reported 1. Do not treat an offline idnits run as a result.

---

## 5. Standing rules in the conformance tree

Rules 1 through 8 are in `conformance/README.md`. The two added during `-03`:

**Rule 9.** A negative control declares the discriminator it is designed to trip,
and is credited only when that discriminator is what fired. A control that refuses
through some other check is recorded `control_exercised: false` and is excluded
from any complete-pass claim. *Attributed to Songbo Bu.*

**Rule 10.** A package is an artefact only if it runs unpacked. Prove it by
unpacking into a clean directory with no repository present and running with no
arguments. *Attributed to Walter Hawkins and Songbo Bu.*

The class of defect both rules address is one gate reporting success over inputs
it never examined. Fix that class at three levels every time: the instance, the
class, and the enforcement, with a negative control proving the fix.

---

## 6. Who found what

Named findings are carried in the Acknowledgments, because a specification
improved by review should say by whom.

| person | finding carried in `-03` |
|---|---|
| Songbo Bu | The indistinguishability requirement of Section 6.4.4 could not be satisfied as `-02` stated it. The normalised observation, its enumeration of HTTP metadata and cache behaviour, and the separation of deterministic requirements from any statistical timing claim are his design, contributed as an executable vector class. Also rule 9. |
| Steven Mih | The empty-result contradiction is conditional on reader and later observer having been served one chain. The boundary now stated in Section 6.4.3 is his finding. Also confirmed the deterministic encoding requirements are RFC 8949 Section 4.2.1 and not RFC 9052 Section 9. |
| Iman Schrock | With Anton Sokolov, that a content digest cannot serve as a correlation key across independently produced descriptions of one act. The requirements in Section 3 on pinning action type and version, the selected field, and its normalisation and comparison rules are his, substantially as drafted. |
| Walter Hawkins | The falsifiability condition of Section 6.4.3 is bounded by observer diversity rather than by any stronger single-log property. Naming the independent observer and the ordering of witness countersignature over independently anchored head digest is his. Also rule 10. |
| Tiago Pinto | The obligation to answer with a signed response carrying a log position belongs on the party making the claim rather than the party relying on it. Section 6.4.3 takes that shape at his argument. |
| Tom Sato | Leaf-construction work on Certificate Transparency logs informed the inclusion-proof requirements. Section 2.1 above is his, and lands in `-04`. |

Addresses for all six are in the private copy of this file, not here.

Cited alongside: `draft-sato-soos-gar-04` and `draft-hawkins-scitt-attested-agent-payment`.
Walter cites `draft-hillier-scitt-arp` unpinned with section references to 6.4.3
and 6.4.4. Those section numbers are unchanged in `-03`, so the citation is stable.

Confirmation of the `-03` filing went to all six on 2026-08-14 at 17:21 to 17:22
UTC, each carrying the digests in section 1, with `conformance-tree.zip` and
`existence_oracle_run.json` attached.
---

## 7. Working method

Written down because it is the reason the reviews above produced what they did.

- **Ground every claim in bytes.** State digests, line counts and sizes. Fetch the
  published copy back and hash it rather than assume the upload was faithful.
- **Reproduce on a second machine before claiming reproducibility.** The `-03` text
  and its run record both reproduce on Linux with CPython 3.11 from the same
  source, byte for byte, as well as on Windows with CPython 3.13.
- **Declare gaps in the record, not in a covering message.** A summary stronger
  than the record it summarises is the defect, not the record.
- **Distinguish what a run establishes from what it does not.** Reproduction of
  fixed bytes under a published runner is not independent verification.
- **Credit findings by name.**
- **Never diff against a local copy of the archive. Diff against the archive.**
  Truncated `.FILED.txt` reference copies were the root cause of the `-01`
  reconstruction losses, and they survived in the source-of-record folder until
  2026-08-14. They are now renamed `.TRUNCATED-DO-NOT-USE.txt` with a warning file
  beside each.

---

## 8. Where things live

| what | where |
|---|---|
| this file | `scitt-arp-f39/ARP-04.md`, mirrored to the OneDrive `IETF-Drafts` folder |
| draft source | `scitt-arp-f39/draft-hillier-scitt-arp.md` |
| conformance tree | `scitt-arp-f39/conformance/` |
| reproduction runbook | `scitt-arp-f39/conformance/REPRODUCE.md` |
| standing rules | `scitt-arp-f39/conformance/README.md` |
| filing register | `certisyn-app/drafts/ietf/STANDARDS-REGISTER.md`, mirrored to OneDrive |
| register self-check | `drafts/ietf/verify-filings.py` |
| immutable filed text, every revision | OneDrive `IETF-Drafts/*.FILED.txt`, with `PROVENANCE.md` |
| superseded `-03` working notes | `scitt-arp-f39/archive/arp-03/` |

Repositories. `scitt-arp-f39` is its own repository at
`github.com/Certisyn-Inc/scitt-arp-f39` and is PUBLIC, currently on
`wip/revision-03` at `2e1993a`. The IETF drafts other than ARP live in
`certisyn-app` under `drafts/ietf/`. `certisyn-app` is private and stays private.

---

## 9. Open elsewhere, not `-04`

Standards-adjacent, carried so a new session does not have to rediscover them:

- W3C CCG prior-art post.
- Consider replying to `draft-maintainer-1f916-agent-record-00` on the SCITT list.
- Consider supporting the RATS adoption call for `draft-poirier-rats-eat-da-10`.

Programme, legal and repository-hygiene items are held in the private copy of this
file in the OneDrive `IETF-Drafts` folder, not here, because this repository is
public.

---

## 10. Open commitments to others, with dates

### 10.1 CPB out-of-scope wording. CLOSED 2026-08-16

The out-of-scope reasons in `cpb_run.json` described ARP in language ARP does
not use. "Correlation digest" appears nowhere in `-01`, "by design" asserted an
intent the draft does not state, and the typed-refs reason made a normative
claim about another document's obligations that ARP is not entitled to make.
Replacement wording was agreed with Steven Mih on 9 August. It reached the
runner and the record on 16 August, before his
`draft-mih-agent-accountability-conformance-01` filed.

The strings are emitted by `run_cpb_vectors.py` rather than stored, so the fix
went into the runner and the record was regenerated from it. Editing the record
directly would have produced a run record no run produced.

    branch feat/revision-02-canonicalization   commit ec354e5
    branch wip/revision-03                     commit 5930f5c

| artefact | was | now |
|---|---|---|
| `runs/cpb_run.json` | `c39d204c...` 10,470 B | `ddf063bb23ade16a729bc6ba8baada5c30a4f4ef3ec0f5b52a103f45fbe0208e` 11,972 B |
| `runs/cpb_run.txt` | `0ae0ea71...` 4,550 B | `186cc728e8661505f16f1449f865bdad143b96ae199e229b991665481a705e41` 4,886 B |
| `runners/run_cpb_vectors.py` | `4170baf3...` | `ecaee0cc29127d61abb27ebbf190a07226abff48c2b910d55c8bf1ec3655d774` |

Regenerated against the pinned CPB corpus,
`github.com/action-state-group/scitt-payload-binding` at
`bc08d78a210f8e77d4abfd8c04c10ea9b57d4390`. That repository was not on the
machine and was cloned fresh from the pin in REPRODUCE.md section 2.

**Controls run before committing anything.** The unmodified runner was executed
first and confirmed to reproduce `c39d204c...` and `0ae0ea71...` exactly, so the
delta is attributable. A structural comparison of old against new shows eight
changed leaves, every one a `reason` string under `out_of_scope`. Every row,
digest, verdict and count is identical: ten positive vectors, three agreeing,
seven diverging with five absent-field-normalization and two exclusion-set, one
must-fail refused by both, zero unattributed, SELF-CHECK PASS. REPRODUCE.md
sections 5 and 6 re-pinned, MANIFEST PASS on both branches. The pushed bytes
were fetched back out of GitHub and hashed, and the withdrawn strings return
zero occurrences on the remote.

### 10.2 Stale record at the commit Steven cited. CLOSED 2026-08-16

Steven's draft pointed at `ae54748`, where REPRODUCE.md section 5 recorded
`cpb_run.json` as `cc94f74e...`, contradicting both the file and the digest his
own draft states. A reader following the citation would have found a flat
contradiction with no way to tell which side was wrong.

Superseded by `ec354e5`, where the record and the file agree and the manifest
passes. Three lines had differed between `ae54748` and `6034be6` and nothing
else. One of them, `runs/arp_adapter_run.json`, had been carrying
`typed_ref_cpb01_run.json`'s digest: a transposition between adjacent rows,
which is the failure a checker reading only one layout cannot see. All eight
outputs named in section 5 were fetched at both commits and every one matched
the `6034be6` record, so the artefacts had never changed. Only the record was
wrong.

### 10.3 Two wording problems in Steven's draft text. OPEN, with him

Both checked against `cpb_run.json` rather than against any summary of it.

**The three-conjunct sentence misreads.** It attributes every divergence to
three declared canonicalization steps including the digest-bearing guard. No
positive row carries that cause; it appears on kat-10 alone. The seven positive
divergences are explained by two steps. Split so the seven attach to the
exclusion set and the absent-field-normalization rule and the must-fail row
attaches to the digest-bearing guard.

**"Exactly as an unattributed divergence did" should read "would have".** The
`unattributed` array is empty, so the past tense claims an event that did not
happen.

Sent 16 August. He files Wednesday 19 August.

### 10.4 Iman Schrock's Gap 6 reproduction receipt. CLOSED

Run it and send back the generated `reproduction-receipt.json`.

    https://github.com/emiliaprotocol/emilia-protocol
    commit 14eee68e64a4f8b0b5950e2ddfab753c48d202a9
    node conformance/composition/gap6-execution-evidence-v0.1/run.mjs

Run from the repository root. It writes `report.json` and
`reproduction-receipt.json`. Committed 14-case reference digest is
`sha256:d79e68656441dcf231a4802c1b5c973fa798ca7d48d7e6acacd2c5683148b239`.

`run.mjs` was read before recommending it: 41,882 bytes, no network calls, one
`execFileSync` running `git rev-parse HEAD` to stamp the receipt. The runner's
header states the boundary correctly, that running it externally is a
reproduction of pinned checks and not an independent implementation result.
Keep that framing when reporting.

**CLOSED 2026-08-16.** Reproduced on win32-arm64, Node v24.14.1.
`results_digest` sha256:d79e68656441dcf231a4802c1b5c973fa798ca7d48d7e6acacd2c5683148b239
matches the committed reference, `matches_committed_reference: true`, runner
exit 0, fourteen of fourteen cases at their stated verdict.
`reproduction-receipt.json` is
`3e6e5aee1c37e2926f323e77638bd8452082495d28da680390dd2ddb72f8d9be`, 535 B, and
is staged at `_send/gap6-reproduction-receipt.json`.

Finding returned to Iman: the published instruction does not run on a clean
clone. `@emilia-protocol/require-receipt` is a `file:` dependency resolved
through the lockfile and the root `package.json` declares no `workspaces`, so
`node run.mjs` terminates in ERR_MODULE_NOT_FOUND until `npm ci --ignore-scripts`
runs first. Standing rule 10 applied to somebody else's tree.

### 10.5 Anton Sokolov. No action

His 16 August message to Tora, with ARP copied, asks nothing. One idea worth
taking: a multi-implementation gap register should say which implementation each
row was measured against and on what commit, because the common failure is a fix
landing in the reference implementation while the others keep accepting the
input and the register records the row as closed. That is rule 9 seen from the
register side rather than the control side.

---

## 11. New tree finding, closed the same day

**A run record that pins its own digest must pin its own line endings.**

`run_cpb_vectors.py` wrote with the platform default newline. The record was LF
as committed and CRLF when regenerated on Windows: identical content, different
digest, and nothing in the record to tell a reader whether they were looking at
a line-ending artefact or a tampered artefact. Measured: 197 lines, 10,470 bytes
as committed against 10,667 regenerated, and LF-normalising the fresh output
reproduced the committed digest exactly.

This is the same class as the environment block that used to sit inside
`existence_oracle_run.json`, and it is the general form of standing rule four:
a reproduction manifest is a claim about bytes, and the checkout and the writer
are both part of the measurement. The writer now pins LF.

Worth applying to every other writer in the tree that emits a pinned record.
That check has not been done yet.

---

## 12. Update log

| date | what changed |
|---|---|
| 2026-08-14 | Opened, the day `-03` posted. Sections 1 to 9. |
| 2026-08-16 | Added sections 10 to 12. Closed the 9 August CPB wording commitment in the runner and the record, and the stale-record citation, both verified from the remote. Recorded the line-ending finding. Sections 10.3 and 10.4 remain open. |