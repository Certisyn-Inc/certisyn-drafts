# draft-hillier-scitt-arp-03 — what review changed, and what ships with it

Joel David Hillier, Certisyn, Inc. — 10 August 2026

Companion to `ARP-03-FOR-COMMENT.md` of 9 August. That document described what
I proposed to file. This one records what the review changed, who established
each change, what now ships alongside the text, and two corrections to claims I
made in the first document.

Filing remains **Thursday 13 August**. Comments remain open until end of
**Wednesday 12 August**.

---

## 0. The pin Songbo asked for

His 9 August message asked two things: apply the one-line correction, and
**publish a replacement exact pin or archive hash**. Until that existed he
described the record as six of seven documented output hashes matching, with
the seventh reproduced byte-identically but its README hash stale. Both are
now done, so the caveat comes off.

```
correction   61c6916 and 6034be6 on feat/revision-02-canonicalization,
             follow-up commits on top of ae54748, not folded into it

cpb_run.json at that branch, from the committed blob:
             c39d204c9685c78d39c66b46f89dcf406116ecde9f3c416b5f98fcf4878e6b9d

exact pin    git tree object for conformance/
             090f6ac91e6b6cbaaed0529e4dec1344dd7d62b8   (-02 branch)
             c42330dccc7d74d3373963b7c90e62a2360718bb   (wip/revision-03)
```

The git tree object is the durable pin and an archive hash is not: a zip moves
on timestamps and compression settings even when every content byte is
identical. His patch and the applied change are the same one line; his arrived
first.

---

## 1. Three findings, three changes

**Songbo Bu — the indistinguishability requirement was unsatisfiable.**
§6.4.4 required the not-entitled and not-found responses to be indistinguishable
in every comparable field, while §6.4.3 requires every response to bind its
request and its serving instant. The two cannot both hold: the
`request-binding`, `response-time`, As-Of pair and signature differ between any
two requests, so byte equality is unreachable and a conformance test written
against it fails every conforming server.

§6.4.4 now defines a **normalised observation** — the response with exactly
those four values removed — and requires equivalence under it. It enumerates
what must match across the two cases: status, media type, HTTP header field-name
set, protected COSE header parameters, empty-result representation, cache
directives and rate-limit effects. It forbids an existence-dependent error
discriminator in the signed payload. It requires `Cache-Control: no-store` on
both arms, so intermediaries cannot reintroduce the distinction. And it requires
that every value removed by normalisation still be valid for its own request,
so normalisation cannot become a way to hide a discriminator.

Timing is now stated as a **separate claim**. Serving both cases from one
processing path is evidence about the design and not evidence that two latency
distributions are indistinguishable. An implementation claiming timing
resistance must publish its measurement population, sample count, network
placement, decision rule and threshold. An implementation making no such claim
is not thereby non-conforming. Conflating the two would let a deterministic
failure be excused as measurement noise, or a measurement be read as protocol
conformance.

**Steven Mih — the absence assertion is fork-conditional.** §6.4.3's
contradiction machinery presumes the reader and any later observer were served
one chain. §4.18 concedes that fork detection is opportunistic: an operator
publishing to two audiences at disjoint sequence numbers never emits a colliding
pair. Under such a fork the superseding entry lands on a branch the holder of
the empty result never reads, the at-or-below test never fires, and the
assertion stands uncontradicted for as long as the branches are kept apart.

§6.4.3 now states that boundary: an empty result is an assertion about a named
head **on the chain its reader was served**, falsifiable to the extent that the
reader independently holds head-consistency evidence for that chain. The gap is
not closed and the document does not claim to close it.

A second change came out of the same reading. §6.4.3 required the
`response-time` to be within "its own freshness tolerance" — a per-reader value,
which is not a property two implementations can be tested against. A deployment
must now declare the tolerance in its Bilateral Register Agreements, and it must
not exceed the notarisation interval.

**Iman Schrock — "a material identifier" is not a designation.** CAID defines no
generic material identifier; it defines typed material fields, and
`payment.release.1` requires `payment_instruction_id`. A profile must now
**designate a typed field the action type itself requires**, by name, for each
action type it admits, and three substitutions are forbidden outright: the join
key is not the action's identity, a Claim Hash is not a cross-deployment
identifier, and equal join keys do not mean equal claims. Stated positively —
the designated field joins candidate reports across permitted variation, the
Claim Hash commits to the exact claim under the deployment's blinding value, and
the action type's own content commitment remains what authorisation binds to.

**Iman Schrock, in full.** His 9 August message — which I under-read on the
first pass — carried both the citation and a replacement paragraph, and both
are now in. -03 cites `draft-schrock-canonical-action-identifier-02`, *The
Canonical Action Identifier (CAID)*, resolved from the datatracker, at the
designation rule, at the measurement in Appendix D, and in the references. The
measurement paragraph now states that the action types, their members and the
reference issuer that minted the five instances are all his, and that the
measurement is not reproducible without that document.

The substantive correction is that my first repair still attributed a semantic
to CAID that CAID does not carry. Its type schema declares required and
optional fields and marks **none** of them as a correlation key, so the
selection belongs to the profile. A profile MUST therefore pin the action type
and its version, the field selected for correlation, and that field's
normalisation and comparison rules; and — the requirement I did not have — the
**selected field MUST be present in the Canonical Claim so that the Claim Hash
commits to it**, closing a join made on a value the reconciliation does not
cover. Equality of the selected value identifies candidates only. Where the
selected values match and the exact-action digests differ, that is a conflict
to surface and not a failed join.

His second reading, after Steven's and Songbo's, endorsed both other boundaries
and closed his own point.

**Anticipating Tom Sato.** The Merkle section now pins three things an
inclusion-proof implementer otherwise gets wrong: the sibling array carries one
entry per level at which the node **has** a sibling and none for a level where
it was carried up, so its length is not the base-two logarithm of the leaf count;
no direction bit is carried, and the verifier derives left-or-right from the
index and leaf count; and the empty tree's root of thirty-two zero octets admits
no inclusion proof.

**Songbo Bu, again, on how a result is described.** His contributor wording to
Steven — reproduction established for *the exercised paths and recorded
outputs*, and not general conformance, unexercised requirements, or
independence beyond the specifically identified implementations and source
boundaries — is the discipline now written into the existence-oracle run
record's own `establishes` and `does_not_establish` fields, in his formulation
rather than a paraphrase of it.

The Acknowledgments section now names these findings and who established them.

---

## 2. What ships alongside the text

Songbo's review recorded his vector class as `not-run`, because the material
identified proposed text and an archive but no runnable endpoint with server
state, two authenticated principals, signing keys and an entitlement fixture.
Those coordinates now exist.

```
conformance/reference/arp_read_ref.py            reference read endpoint
conformance/reference/fixture-eo-v0.1.json       pinned state, published keys
conformance/vectors/arp-existence-oracle-v0.1.json   the class
conformance/runners/run_existence_oracle_vectors.py  the runner
conformance/runs/existence_oracle_run.json       deterministic record
conformance/runs/existence_oracle_timing.json    timing, separately
```

To run it, from `conformance/runners`:

```
python3 run_existence_oracle_vectors.py
```

No arguments, no network, no installation beyond `cryptography`. The runner
starts the endpoint itself, on loopback, in each configuration it needs.

The endpoint implements deterministic CBOR to RFC 8949 §4.2.1 — written out
rather than imported, so the encoder under test is the one the specification
names — COSE_Sign1 over Ed25519 for every response including every `4xx`, an
RFC 9421-shaped request signature over the same four components the
`request-binding` digest covers, the rate-limit counter charged before
entitlement is evaluated, one code path for both refused arms, and
`Cache-Control: no-store`.

**Result: deterministic PASS**, on Linux under Python 3.11 and on Windows under
Python 3.13. Seven negative controls each refuse the endpoint when one existence
channel is deliberately reintroduced: a status oracle, a signed-body
discriminator, an HTTP header present on one arm, differing cache directives,
entitlement evaluated before the counter is charged, responses sealed with an
unpublished key, and an always-404 server. Signature validity is verified
against the sealing public key the fixture publishes; the always-404 control
proves the positive vector can fail, and the bad-signature control proves the
signature check can refuse.

---

## 3. What the run establishes, and what it does not

Stated plainly, because the distinction is the whole value of the exercise.

**It establishes** that §6.4.4 as I read it is implementable, that the class
executes end to end, and that every check in it fires against an injected defect
rather than being a no-op.

Iman's position before the endpoint existed was that these vectors should
remain explicitly not-run until the required server-state fixture existed. That
was right, and it is the same discipline as recording the run honestly now that
the fixture does exist. The disposition moves from `not-run` to measured **for
that endpoint**, and no further — which is the next paragraph.

**It does not establish anything about the specification.** The endpoint was
written by the specification's author from his own reading of his own text,
which makes it the one configuration that cannot surface a specification defect:
author and implementer share the same misreadings. Specification adequacy is
untested until someone working only from the text passes this class. That is an
invitation, and the fixture exists to make accepting it cheap.

**The negative side is fault injection, not two-sidedness.** The defects, the
detector and the endpoint are all mine, and each control confirms the detector
is wired to its own switch. That is the weakest useful form of negative
evidence. The class becomes two-sided the first time it refuses an endpoint I
did not write.

**Five coverage gaps are declared in the run record**, not left to be found:

- `NV-ARP-EO-05`, the same-work requirement, is **structural and not decidable
  by response comparison**. The defective endpoint is byte-equivalent under the
  normalised observation — which is itself the finding. Closing it needs source
  or trace inspection, or a timing population with a stated network placement
  and threshold.
- `NV-ARP-EO-04` refuses, but by the fallback branch: the designed discriminator
  never executes, because the defective endpoint answers `404` before charging
  and so never reaches `429`. Refused for the wrong reason; the budget-ordering
  channel remains untested.
- `NV-ARP-EO-06`, the statistical timing row, is reported and not adjudicated.
- Encoder independence: `request-binding` and the CBOR encoder are imported from
  the implementation under test, so an encoder defect — including an RFC 8949
  §4.2.1 map-ordering violation — is invisible to this class. Closing it needs a
  second encoder written from the RFC.
- Timing resistance: no claim is made and none is tested. Loopback latency is
  not evidence about a deployed path.

The normalised-observation rule these rows test is **not** in -03 as circulated
on 9 August; it was written in response to the class. The run record says so and
carries the digest of the text it actually tested.

---

## 4. Two corrections to my own summary of 9 August

**"Twenty independent adversarial passes, 0 open findings."** Accurate to the
schema it summarised and misleading in a message to four external reviewers.
Those were my own passes, run blind to each other, on one toolchain — not
independent reviewers. The underlying tally was 33 closed, 15 **partially**
closed, 2 acknowledged, 0 open, and "0 open" is partly an artefact of a schema
in which "partially closed" is not "open". Two of you landed findings the
following morning, which is the fair measure of what self-review reaches.

**"Built twice on unrelated toolchains."** Both builds are kramdown-rfc plus
xml2rfc; only the operating system differs. Byte-identical output across two
platforms rules out an environment-dependent build, which is worth having and is
what I should have said. It is not an independent-toolchain check, because there
is no second toolchain.

---

## 5. Deploying against this

For anyone building to §6.4 rather than reviewing it.

**Start from the fixture, not the prose.** `fixture-eo-v0.1.json` pins a server
state, two principals with published keys, an entitled resource and an absent
identifier. Point your own endpoint at the same state and run the class against
it; every disagreement is either a defect in your endpoint or an ambiguity in
the text, and both are worth more to me than agreement.

**The four load-bearing behaviours, in the order they bite.** Charge the rate
limit before you evaluate entitlement. Serve both refused arms from one code
path. Sign your errors, not only your successes. Bind every response to the
request and to the head it was served against.

**What to expect to get wrong first.** Cache directives and header presence —
they sit outside the handler most people write, and both are existence channels.
The class has a control for each.

**Sequencing for a deployment.** The read binding is implementable now against
the fixture. The register leg is explicitly out of scope in -03 and is the
obvious -04; a deployment needs a Bilateral Register Agreement to cover that
channel until it is specified. Absence assertions are usable within one chain
today; a deployment relying on them across audiences needs its own
head-consistency evidence, per §6.4.3, and should plan for that rather than
assume the protocol supplies it.

---

## 6. State of the artefact

| | |
|---|---|
| Source | `draft-hillier-scitt-arp.md`, 4,835 lines |
| Source SHA-256 | `9a086e8832489f456ae5066848c208ceccbab9e00adadd29bc003c3a142c86c9` |
| Text | `draft-hillier-scitt-arp-03.txt`, 7,056 lines, 336,811 bytes |
| Text SHA-256 | `8fab5b82a67f56e0735a859ecfa0a7bb78ccb44fb85a9d87a6efea3342f07c27` |
| Build | kramdown-rfc 1.7.39 + xml2rfc, byte-identical on Linux and Windows |
| idnits | 3.1.0 — 1 error, 11 warnings |
| Manifest | `MANIFEST: PASS`, 18 of 18 in §6, 9 of 9 in §5 |
| Existence class | deterministic PASS, 7 controls refuse, 5 gaps declared |

The single idnits error is the RFC 8785 downref, deliberate and documented in
the Note to the RFC Editor: RFC 8785 is Informational, is normatively referenced
because the Canonical Claim is a digest over an RFC 8785 serialisation, and is
not in the downref registry, so it needs calling out at IETF Last Call under
§2 of RFC 8067.

The digests in `ARP-03-FOR-COMMENT.md` refer to the 9 August text and no longer
match the working copy. Use the table above.
