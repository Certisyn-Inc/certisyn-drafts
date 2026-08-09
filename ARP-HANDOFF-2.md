# ARP handoff, second edition

Supersedes `ARP-HANDOFF.md` for everything after "where things stand". Written
2026-08-09. Everything below is verified against the repository, the build, or a
review pass, not recalled.

Read section 4 first if you read nothing else. It is the only thing in here that
the previous handoff could not have told you.

---

## 1. State

| | |
|---|---|
| **Filed** | `draft-hillier-scitt-arp-02`, 2026-08-08, idnits clean |
| **Filed branch** | `feat/revision-02-canonicalization` @ `ae54748` |
| **-03 work** | `wip/revision-03` @ `625ee31`, **unchanged by this session** |
| **This session's output** | `draft-hillier-scitt-arp.wip.md` and friends, untracked, alongside the originals |
| **Emails** | Three Outlook drafts, unsent, all correctly referencing **-02**. Do not touch. |

Nothing was committed. `draft-hillier-scitt-arp.md` on disk is byte-identical to
`625ee31`. The session's work is in the `.wip.` files. To adopt it:

```
git checkout wip/revision-03
mv draft-hillier-scitt-arp.wip.md  draft-hillier-scitt-arp.md
mv draft-hillier-scitt-arp.wip.xml draft-hillier-scitt-arp.xml
mv draft-hillier-scitt-arp.wip.txt draft-hillier-scitt-arp.txt
```

The delta is 17 hunks, +519 / -74 lines of source. The built text goes from 3,752
to 4,368 lines. **It is not fileable.** Section 5 says why.

---

## 2. The build now works in two places

`build-draft.ps1` on Windows is unchanged and still correct. `cloudbuild.sh` is
its POSIX equivalent and was verified to reproduce the Windows-built
`draft-hillier-scitt-arp.txt` **byte for byte** from the unmodified `625ee31`
source — 3,752 lines, zero diff after CRLF normalisation.

Five things about the cloud build that will each cost an hour if rediscovered:

1. **rubygems.org is not reachable** from an Anthropic cloud container (403 at
   the proxy). `gem install kramdown-rfc2629` cannot work there. github.com is
   reachable, so 1.7.39 is run straight from a clone of `cabo/kramdown-rfc`.
2. **apt's `ruby-kramdown-rfc2629` is 1.6.22 and does NOT match.** It drops the
   `<?line?>` markers, the `type="1"` list attributes and the combined
   `<references>` wrapper — 445 diff lines against the real output. Do not fall
   back to it. Its dependencies are still useful: `ruby-kramdown` 2.4.0,
   `ruby-kramdown-parser-gfm`, `ruby-unicode-blocks`, `ruby-net-http-persistent`.
3. **Run it under `/usr/bin/ruby3.2`**, not the rbenv ruby, which cannot see the
   apt-installed gems.
4. **Both `bib.ietf.org` and `datatracker.ietf.org` are blocked** in that
   container, so the refcache can be neither seeded nor renewed. Copy `.refcache`
   from the Windows repo and set `KRAMDOWN_REFCACHETTL` absurdly high, or
   kramdown-rfc will try to renew a "stale" entry and die on the 403.
5. **A failed `xml2rfc` run leaves the previous `.txt` in place.** Existence
   proves nothing. `cloudbuild.sh` deletes it first and greps the log for
   `Error:`. It also treats kramdown-rfc's "no end tag for X" as fatal — that
   warning means an angle-bracketed literal in an example was parsed as an HTML
   tag and silently swallowed, which is how `<COSE_Sign1, ...>` in a worked
   example produced a malformed document this session.

`idnits` is not installable in the container (not on PyPI, not in apt). Lint on
Windows or at author-tools.ietf.org.

---

## 3. What this session did

Fixed the Continuation-entry defect cluster, which the previous handoff named as
the thing four open items collapse into. Then reviewed it, repaired it, reviewed
it again, and corrected it again. Three review rounds, eleven independent
adversarial passes in total.

**Round A — the schema.** Entry Type discriminator, per-type field lists,
Self-Entry Hash constructed, `{{post-seal}}` stopped requiring an in-place ledger
write, terminology and determinism carve-outs brought into line, IANA registry,
worked examples, change log. Also invented two new read scopes and a Ledger Head
Statement to close the two remaining items — relying-party discoverability and
fork detection.

**Round B — review.** Three passes (normative rigour, role/lifecycle, adversarial
security), run blind to each other. 48 raw findings, 19 after dedup. Six defects
closed, roughly fifteen opened. Almost all the new damage came from the two
invented read surfaces.

**Round C — repair.** Retracted head-consistency scope entirely. Bounded
continuation scope to the Requesting Principal, evaluated by the server against
the policy-epoch store rather than by the Ledger, which cannot. Redefined
Prior-Entry Hash over whole entries so Entry Signatures are inside the chain.
Fixed encoding, ordering, conditionality, the IANA self-refusal, the Portal join.
Withdrew every overclaim about fork detection.

**Round D — review.** Three more passes. 18 closed, 6 partial, 1 acknowledged, 1
open — and 13 newly introduced by the repair.

**Round E — correction.** Twenty-two targeted fixes for the unambiguous
oversights in round C, plus retraction of the two round-C additions that had
themselves generated attacks (supersession retrieval URIs, mandatory
query-budget disclosure). Verified by a fourth pass, which found 11 confirmed, 5
incomplete with named stale dependants; those were then fixed too.

`ARP-03-CONTINUATION-REVIEW.md` has the full round-B inventory with line numbers.

---

## 4. Why the rounds do not converge

The previous handoff recorded the symptom — "each round closed roughly fifteen
defects and opened a comparable number" — and correctly concluded that was the
reason to stop. It could not say *why*. Four more rounds and eleven more passes
make the cause legible, and it is not defect density.

**The document adds normative machinery faster than it defines the substrate the
machinery stands on.** Every round adds a mechanism. Every review finds that the
mechanism requires something the document has never defined. The next round adds
another mechanism to patch the gap, which requires another undefined thing.

Three substrate layers are missing, and between them they account for the large
majority of every finding in this session and most of the open list in the
previous handoff.

### 4.1 There is no read binding

The document defines, in detail, *what* a Ledger read returns. It has never
defined how one is requested. No endpoint. No request encoding. No response
encoding. No media type for a ledger entry or a scope response. No error
semantics — and the two errors that matter most, "no continuations exist" and
"you are not entitled to ask", are the two a reader most needs distinguished,
because an operator suppressing a supersession returns the same thing for both.
No completeness statement, no as-of-sequence binding, no freshness bound, no
signature on a response, and no inclusion proof from a returned entry to the
published head.

The consequence is that every discovery path the document has ever specified
dead-ends at the same place, and every round that tries to fix a dead end by
adding a pointer — a hash, a URI, a sequence number — moves the dead end one step
without removing it. `{{post-seal}}`'s record, the superseding Output, the
Regulator Portal's own read of a reconciliation entry to compute the scope under
which it may read a Continuation entry: all of them.

Compare `{{sealing-key-discovery}}`, which is the one retrieval path in the
document that *is* fully specified — well-known URI, key set, origin
authorisation, a stated reason each step exists — and which is correspondingly
the one that has never generated a finding of this kind.

### 4.2 There is no authorisation model for artefacts

Round A authorised continuation scope by the Requester-Binding; the Ledger
cannot evaluate that, because it stores no principal identifier. Round C moved
the evaluation to the server and the policy-epoch store, which works — and
immediately produced the next finding, that the Requesting Principal is not the
party the scope was written for, and that a hostile Requesting Principal gets a
permanent budget-free feed about a subject that never consented.

Underneath both is that the document has no model of who may hold what. It knows
the Output is a bearer artefact and says so. It has never said who is entitled
to hold one, how a holder demonstrates entitlement, what a register's or a
regulator's or a downstream party's entitlement is, or how any of them is
checked. Every authorisation predicate written so far has been invented at the
point of need, and each has failed on a different one of those questions.

### 4.3 There is no delivery model

The document never states that a Reconciliation Output is delivered to the
Requesting Principal. The only artefact the pipeline is stated to return to a
requester is the Remediation Advisory on an adversarial-test failure. This was
found by the lifecycle pass and it is the sharpest single observation of the
session, because it explains the shape of everything above: the discovery paths
keep dead-ending partly because the document has never described the ordinary,
non-exceptional case of a party receiving the thing it asked for.

Continuation scope is keyed on the Reconciliation Hash. That value is, by this
session's own correction, not reproducible across runs. So a principal's only
discovery path depends on retaining byte-for-byte an artefact the document never
promises it, indexed by a value it cannot recompute.

---

## 5. What to do next

**Do not open another mechanism round.** On the evidence of ten rounds it will
close roughly fifteen defects and open roughly fifteen, and the fifteen it opens
will be in whatever substrate the new mechanism happens to stand on.

Write the substrate first, as one revision, adding no new capability:

1. **A read binding.** One section, modelled on `{{sealing-key-discovery}}`,
   which already demonstrates the pattern. Endpoint, request form, response form,
   media types, error semantics, and — the parts that are load-bearing and easy
   to omit — a completeness statement, an as-of-sequence binding, and a signature
   over the response. Roughly a dozen open items collapse into this.
2. **An entitlement model.** Who may hold an Output, who may read what about it,
   how entitlement is demonstrated and checked, and what the subject's standing
   is. State plainly where a party has none. Most of the security findings and
   all of the authorisation findings are downstream of this.
3. **A delivery statement.** One paragraph saying what the pipeline returns, to
   whom, and indexed by what. It is the cheapest of the three and probably the
   highest yield.

Only then reconsider the mechanism list. Expect much of it to have already
resolved.

### If you file -03 before that

You would be filing a document whose Continuation entries are well defined and
whose read paths are not. That is defensible for a `-03` — it is visibly better
than `-02` on the schema, and every gap it leaves is now stated in the text
rather than implied. It is not defensible as a claim to be implementable. The
`.wip.` draft is honest about this in five places; if you file it, do not
retreat from any of them under review pressure. Each was earned by a finding.

---

## 6. The method, refined

Four independent adversarial dimensions, run blind to each other, remains right.
Two refinements from this session:

- **Run the security pass before committing to a new externally-reachable
  surface, not after.** Round A's head-consistency scope generated three of the
  four worst findings in round B, and all three followed directly from an
  argument the document already makes about low-entropy preimages, applied to a
  digest round A had introduced. Half an hour of dimension 4 at design time would
  have saved the round.
- **Add a fifth pass: dependants.** Rounds A and C both edited a section
  correctly and left its dependants stale — round C's determinism fix never
  struck the term from the sentence it carved out of, and its example still
  described a retrieval URI it had removed. A pass that does nothing but check
  "what else in this document mentions the thing I just changed" caught five such
  in round E and is cheap.

The lifecycle walkthrough remains the highest-yield dimension by a wide margin,
and it is the one that produced section 4.

### Mistakes not to repeat, carried forward

- Do not patch a normative MUST by appending a paragraph that contradicts it.
- A Python edit script that asserts across several replacements and writes once
  at the end loses every earlier edit when one assertion fails. Save per edit.
  `fix.py`-style scripts in this session write after each successful replacement
  and print `SKIP` rather than raising, which is why a failed match cost nothing.
- Bisect to the end before naming a cause.
- Judge a build on its artifact, never on an exit code — and never on an artifact
  that a failed run may have left behind from the previous one.

---

## 7. Files

| File | What it is |
|---|---|
| `draft-hillier-scitt-arp.md` | Unchanged, `625ee31`. |
| `draft-hillier-scitt-arp.wip.md` | This session's work. Not fileable. |
| `draft-hillier-scitt-arp.wip.xml` / `.txt` | Built from it, 4,368 lines. |
| `cloudbuild.sh` | POSIX build, verified byte-identical to the Windows build. |
| `ARP-03-CONTINUATION-REVIEW.md` | Round-B inventory, 19 findings with line numbers. |
| `ARP-HANDOFF-2.md` | This file. Supersedes `ARP-HANDOFF.md` from section 3 on. |
| `ARP-HANDOFF.md` | Still correct on -02, the emails, and the Windows toolchain. |
| `ARP-03-BLOCKERS.md` | Superseded twice over. |

One repository note: viewing this repo through a Linux mount makes 42 files show
as modified purely from CRLF. The draft itself has a genuinely empty diff. Do not
run `git add` from that side.
