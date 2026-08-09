# ARP handoff — read this first

Context for a fresh session picking up `draft-hillier-scitt-arp`. Written
2026-08-09 at the end of a long session. Everything below is verified against
the repository and the datatracker, not recalled.

---

## 1. Where things stand in one screen

| | |
|---|---|
| **Filed** | `draft-hillier-scitt-arp-02`, 2026-08-08, idnits **clean** — no errors, flaws or nits |
| **Filed branch** | `feat/revision-02-canonicalization` @ `ae54748` — reproduces the filed bytes |
| **-03 work** | `wip/revision-03` @ `30587c0` — pushed, builds clean (3,752 lines), **NOT FILEABLE** |
| **Repo** | `C:\Users\joelh\certisyn-app\scitt-arp-f39`, origin `github.com/Certisyn-Inc/scitt-arp-f39` |
| **Emails** | Three Outlook drafts, unsent, all correctly referencing **-02** |

Do not file -03. Do not commit -03 work onto the filed branch.

---

## 2. Toolchain — five things that will each cost an hour if rediscovered

1. **`make` does not work.** The repo Makefile is POSIX. `build-draft.ps1` is
   the Windows equivalent and does the same three steps.
2. **`bib.ietf.org` is broken, not blocked.** Its root returns 200 and a missing
   directory returns 404, but every file under `/public/rfc/bibxml/` accepts the
   request and never responds. kramdown-rfc fetches *every* reference from
   there, so an unseeded build hangs forever. This is IETF-side, not the local
   network — verified by curl over IPv4 with the host pinned. **No firewall or
   DNS change is warranted.**
3. **`seed-refcache.ps1` is the workaround** and `build-draft.ps1` calls it. It
   writes 13 RFC entries from rfc-editor metadata and pulls 6 I-D entries from
   `datatracker.ietf.org/doc/bibxml3/`, which does work. `.refcache\` is
   gitignored. **Adding a new RFC reference to the draft means adding it to the
   seeder too**, or the build hangs on that one reference.
4. **xml2rfc**: Store-installed Python puts `xml2rfc.exe` off PATH, and
   `python -m xml2rfc` fails (no `__main__`). `build-draft.ps1` resolves the exe.
5. **Judge build success on the artifact, not the exit code.** `Start-Process`
   with redirected streams returns an empty `ExitCode`, and `$null -ne 0` reads
   as failure. `build-draft.ps1` checks for `</rfc>` instead.

`arp-ops.ps1 status|build|filed|wip|verify` wraps the common operations.

**Watch for conflict markers.** A `git stash pop` once left `<<<<<<<` in the
source and produced a malformed XML build that took a while to diagnose. Both
scripts now check.

---

## 3. What -03 is for

A review of -02 on the SCITT list made four asks. The response, and its status:

| Ask | Response |
|---|---|
| Post-quantum guidance | **Already normative in -02** — a MUST for one PQ primitive per class, ML-KEM-1024 and ML-DSA-65 named, FIPS 203/204 cited. No action. |
| SBOM / DevOps translation layers | **Category error.** ARP reconciles sanctions lists and beneficial-ownership registers, not software artifacts. Countered with four named regulatory formats instead. |
| SCRAPI mapping | **Valid.** -02 composed permissively (MAY notarise, MAY use the APIs) — a permission, not a binding. -03 adds a normative wire binding. |
| Practical guidance | Half right. Examples and conformance vectors exist; a reference implementation does not. |

Two positions worth holding, both verified:

- **SCRAPI has no query surface.** Verified against `draft-ietf-scitt-scrapi-11`:
  the entire API is `POST /entries`, `GET /entries/{EntryID}`, and two
  `/.well-known/scitt-keys` paths. The reviewer asked for a retrieval path keyed
  on the policy-version hash; specifying one would specify an endpoint that does
  not exist. -03 instead carries the policy-version hash in the protected header
  so the receipt covers it — established by verification rather than lookup.
- **No forward-looking promise about a reference implementation.** Publish it,
  then cite it by repo and commit. A draft should not claim an artefact a reader
  cannot check.

Three factual corrections were made and verified against primary sources, and
should not be re-litigated: UN/CEFACT and WCO express authority determinations
as well as declarations (LPCO, Declaration Response, eCERT); consolidated
sanctions lists are event-driven rather than periodic and only OFAC publishes
deltas; `org:FormalOrganization` does carry legal recognition.

---

## 4. Why -03 is not fileable

Six rounds of fix-then-red-team. **Each round closed roughly fifteen defects and
opened a comparable number.** The final round's two critical findings were bugs
introduced by the previous round's own fixes. That is not convergence, and it is
the reason to stop rather than any single unresolved item.

The underlying cause, and it predates -03: **-03 added requirements to
structures that were never enumerated.** The Reconciliation Output had no field
list, `Reconciliation Hash` and `Combined Verdict` were used normatively —
the former inside the bit-for-bit determinism requirement — and never defined.
Those are now fixed, but every round of building on them surfaced another layer.

### What the rounds actually bought

Real defects, most **pre-existing in -02**, now closed on the WIP branch:

- **A Partial Attestation was not bound to the question it answered.** No
  subject, no predicate, no nonce in the signed payload. An attestation
  harvested about a clean shell company could be placed into a reconciliation
  about a sanctioned one and pass every other check; a register could answer two
  ways and deny it. Closed by a signed Query Binding. *This is the single most
  valuable finding of the session.*
- **The Per-Register Claim Projection — a register's only input — had no field
  list.** The register role was unimplementable.
- **Verdict Arithmetic was named but never defined.** No truth table, no
  behaviour for `indeterminate`.
- **A relying party was told to verify a sealing key it could not obtain.**
- **Claim and Policy-Version hashes were unsalted digests over low-entropy
  preimages**, published in ledger entries and notarised statements — subject
  and commissioning principal recoverable by dictionary attack.
- **No outcome was defined for a register that did not answer** — five reachable
  dead ends, and silently dropping a register is the cherry-picking pattern the
  protocol claims to detect.

None of these came from the SCRAPI reviewer. They came from running dimensions
nobody had run.

---

## 5. The method that found them — use it again

Four independent review dimensions, run as separate adversarial passes. Each
found a class the others missed:

1. **Normative rigour** — untestable MUSTs, contradictions, terms used but
   undefined, requirements two implementers would read differently.
2. **External fact verification** — every claim about another specification
   checked against the primary source. Caught the UN/CEFACT and sanctions-cadence
   errors, and confirmed the SCRAPI no-query-surface claim was right.
3. **Role and lifecycle walkthrough** — for each actor and each phase, does this
   party hold the inputs the requirement names? Can it verify what it is told to
   verify? Found ~40 gaps, most pre-existing. **Highest yield of the four.**
4. **Adversarial security** — a malicious participant at each position. Found
   the two criticals.

Run 1 and 3 at minimum on any future round. Run 2 whenever a claim about another
document is added. Run 4 before any filing.

### Mistakes not to repeat

- I twice declared a cause before running the test that would falsify it — first
  blaming RFC 9942/9943 for the build failure, then asserting a second cause
  that did not exist. Bisect to the end before concluding.
- A Python edit script that asserts on several replacements and writes only at
  the end will lose every earlier edit when one assertion fails. Save per edit.
- Do not patch a normative MUST by appending a paragraph that contradicts it.
  One round "fixed" the pattern-library AAD by adding a rebuttal while leaving
  the original MUST in place; the next review caught it unchanged.

---

## 6. Open defects on `wip/revision-03`

Seventeen from the last verification, plus security items not yet addressed.
Grouped by what they block.

### Blocking — a party cannot do what is required

- **Continuation entries have no defined form.** The ledger entry list says
  "comprises only" fourteen fields; Continuation entries carry fields not in it,
  supply none of the mandatory ones, and there is no type discriminator.
  Two unreconciled supersession mechanisms now exist (Continuation entry vs
  `Source-Reconciliation-Output Identifier`), and the worked example uses the
  other one.
- **`post-seal` still requires an in-place ledger write** the ledger does not
  expose. The Continuation mechanism was added in one section and the dependent
  section was not rewritten.
- **Post-Seal Evaluation Records remain undiscoverable by relying parties.**
  Ledger READ is scoped to regulator credentials; a relying party has no access
  and no index from Reconciliation Hash to entry.
- **Fork detection does not work as specified.** A published head is a bare hash
  with no sequence number and no consistency proof, so two heads are
  indistinguishable from ordinary progress; the SCITT anchor's EntryID is
  published nowhere and SCRAPI has no query surface.

### Security — reachable attacks

- **The per-subject query budget is requester-independent.** Any requester,
  including an ENEMY agent, can exhaust it and force every reconciliation about
  that subject to `indeterminate` for the interval. Scope it per principal.
- **Non-Answer Reasons carry no register-signed evidence.** A server can suppress
  a real `match` by asserting `register-unresponsive`. It can only downgrade to
  `indeterminate`, not fabricate — but suppressing a sanctions hit is the harm
  the domain cares about.
- **Retroactive evaluation is unfalsifiable.** All triggers are server-controlled,
  nothing records that an evaluation ran, so "found no change" and "never ran"
  are identical from outside. `attribution-indeterminate` is a self-signed
  discretionary escape.
- **The requester chooses the Verdict Arithmetic**, so it can pick an operator
  and threshold that reach the verdict it wants. No adversarial pattern covers it.
- **The IFF gate conflates key possession with principal binding** —
  `agent-verified` overclaims, and there is no third value for
  key-verified-but-principal-uncorroborated.
- **VPC revocation is unreachable in the hot path** by definition, and the
  compensating notification goes to the regulator, never to the relying party
  that acted.
- **The Output is a bearer artefact** — no audience, no expiry, no holder binding.

### Consistency and hygiene

- The `terminology` definition of the Settlement-Layer Ledger is stale — no
  Claim Hash, no Entry Signature, no Continuation type.
- The determinism exemption list was not updated for Entry Signature, Override
  Record, or accumulated query-budget state.
- `source-class-quorum`'s threshold is not carried in the Output, so it is
  irreproducible despite the rationale for carrying the operator.
- The Override Record has no field list, no registry, no operator signature, is
  absent from the ledger, and publishes an operator identity in cleartext in an
  artefact whose policy hash is blinded to protect exactly that.
- Threshold-sensitivity is a profile property but the re-typing test names the
  Canonical Claim predicate; undefined over a mixed-profile register set.
- `containment` contradicts itself: refuse the reconciliation, *and* record a
  Non-Answer Reason in an Output that then does not exist.
- **Examples and Document History do not describe rounds 5 and 6** — Query
  Binding, Deployment Blinding Value, Authorised-Origin Document, Continuation
  entries, ledger head, query budget, Override Record, Answer State, and the new
  IANA registrations are all missing from the change log the working group reads.

---

## 7. Suggested order for the next session

1. `.\arp-ops.ps1 status`, then `wip`, then `build`. Confirm 3,752 lines.
2. Fix the **Continuation entry schema** first — four open items collapse into it.
3. Fix **Document History and the worked examples**. They are the reviewer's
   entry point and currently describe a document two rounds out of date.
4. Re-scope the **query budget** per principal.
5. Re-run dimensions 1 and 3. Expect new findings; that is the point.
6. Only then consider filing, and only if a round closes defects without
   opening comparable ones.

Realistically this is a dedicated cycle, not an evening.

---

## 8. Files

On `wip/revision-03` unless noted.

| File | What it is |
|---|---|
| `draft-hillier-scitt-arp.md` | The source. `-03` on wip, `-02` on the filed branch. |
| `draft-hillier-scitt-arp.xml` | **Commit this.** The only durable proof of which bytes were filed — the lesson of the lost `-01`. |
| `build-draft.ps1` | The Makefile's Windows equivalent. |
| `seed-refcache.ps1` | Populates `.refcache\`. Add new RFC references here too. |
| `arp-ops.ps1` | status / build / filed / wip / verify. |
| `ARP-03-BLOCKERS.md` | Earlier blocker analysis; section 6 above supersedes it. |
| `ARP-03-adoption-plan.md` | The response to the SCRAPI reviewer. |
| `REBUTTAL-arp02-review.md` | The point-by-point reply to the -02 review. |
| `BUILD-AND-SUBMIT.md`, `RECOVERY.md` | Pre-existing. Note the Makefile caveat above. |

---

## 9. Emails

Three unsent Outlook drafts, all correct as they stand:

- **Typed-reference vectors to Steven, Songbo, Tom, Iman** — cites `ae54748`.
- **SCITT list reply to Walter and Tiago** — includes the bib.ietf.org note.
- **Contributor credit to Steven and Songbo** — the "-02 is not filed" claim in
  it was corrected once -02 went live; do not reintroduce it.

**They reference -02, which is what is published. Do not update them to claim
-03.** Making a claim about an unpublished revision is the exact error the
credit email spends three paragraphs asking Steven to correct.
