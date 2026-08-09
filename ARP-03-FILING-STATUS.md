# -03 filing status

Written 2026-08-09. Everything here is verified against the source or against a
review pass, not recalled.

---

## 1. Where -03 stands

`draft-hillier-scitt-arp.wip.md`, 4,685 source lines, builds clean to a
6,832-line text. 83 hunks against `625ee31`. `docname` is already `-03`.

Five review rounds, twenty independent adversarial passes, across five
dimensions: normative rigour, external fact verification, role and lifecycle
walkthrough, adversarial security, and a dependants sweep. The last full pass
returned **33 closed, 15 partially closed, 2 acknowledged, 0 open**, and the
consistency sweep that followed the final structural edits returned 37 items,
all corrected.

**It is not filed and I have not filed it.** Two decisions in section 4 are
yours. Everything else is done.

---

## 2. What changed, in one screen

**Three substrate layers that did not exist.** `{#delivery}` states what the
pipeline returns and to whom — no earlier revision said a Reconciliation Output
is delivered to anybody. `{#entitlement}` gives an Output a sealed Audience Set
and a Reliance Horizon, so entitlement follows membership rather than possession;
that closes the bearer-artefact defect and supplies the read predicate every
earlier attempt failed to express. `{#ledger-read}` is a wire binding: nine
operations, an RFC 9421 signing profile, signed responses that cover errors as
well as successes and carry the ledger head they were served against, and a
`404` for both not-entitled and not-found so no endpoint is an existence oracle.

**Two more that the last round found.** `{#request-binding}` states how a
reconciliation is commissioned; the document previously imposed obligations on
"the response to the request that commissioned it" without defining that request.
`{#audit-path}` states who an auditor is; four requirements were justified by
what an auditor could reproduce, and the auditor was not a party the document
admitted.

**Every digest preimage and signature payload is now pinned** to a CBOR array
with a normative field order and null-substitution for absent fields: the Claim
Hash, the Policy-Version Hash, the Agreement Hash, the Reconciliation Output and
its Sealing Signature, the Partial Attestation, the Per-Register Claim
Projection, the ledger entry chain, the Post-Seal Evaluation Record, the
Non-Answer Statement, the Ledger Head Statement, the Evaluation Sweep Statement,
the Sovereign Re-Notification, the Policy Parameters Document, the Override
Record, the read response, and both Merkle trees with their inclusion-proof
encoding. -02 left several as "the canonical serialisation of the foregoing",
which is not a preimage two implementations can agree on. The Policy-Version Hash
and the Agreement Hash had no construction at all.

**Eight ways the protocol could be gamed, closed.** Per-principal query budget
(the shared counter was a denial of service granted by the countermeasure);
register-signed Non-Answer Statements (a `register-refused` was an unattested
assertion by the party that transmitted the projection); Evaluation Sweep
Statements (a sweep never run and a sweep that found nothing were the same
observation); policy-resolved Verdict Arithmetic (the requester could otherwise
choose the operator, and therefore the verdict); a fourth Requester-Binding class
`agent-key-verified`; a bounded revocation window; an operator-signed Override
Record with a ledger-visible Override Indicator; and Continuation entries with a
type discriminator, which is where this session started.

**Corrections from checking claims against sources.** The deterministic CBOR
encoding every digest depends on is Section 4.2.1 of RFC 8949, now a normative
reference — RFC 9052 narrows those requirements to COSE's own signing structures
and states no map-key ordering rule, so the previous citation did not support
what was built on it. RFC 9943 defines no Identity Manager and no Aggregator
role. The referenced agent-accountability draft never uses the word "capsule" and
freezes no conformance vectors, so an unsourced claim about twenty-two pinned
vectors is gone. `+ld+json` is not a registered structured syntax suffix. The EU
consolidated financial sanctions list and the OFAC SDN list now point at the
resources that publish them. RFC 3339, 3986, 6838, 6839, 7638, 8949 and 9530 are
referenced rather than named in prose.

**Two removals, on your instruction and on the evidence.** Homomorphic
Aggregation Mode is gone: it named no primitive, had no class in the upgrade path
for one to be declared in, defined no encrypted-contribution structure, and the
server must read every per-register verdict in the clear anyway to verify the
register's signature, recompute the Query Binding, check the echoed
Policy-Version Hash and apply re-typing. The privacy property it advertised was
not available under it. The server-to-register wire binding is now explicitly out
of scope, and the claim that enumerating the Per-Register Claim Projection lets
two register operators build interoperable endpoints is withdrawn — the document
now specifies what that channel must achieve and leaves the transport to the
Bilateral Register Agreement.

**A Privacy Considerations section**, which a document about beneficial
ownership, sanctions and customs records did not have.

---

## 3. What is acknowledged rather than fixed

Each of these is stated plainly in the text. A reviewer may still push, and
should.

- **The subject has no standing.** It is not notified, cannot object, and cannot
  learn it was reconciled. Deliberate in a screening protocol, and a real cost.
- **The Audit Identity is broad.** Every agreement declares one, and each reads
  every Output of every reconciliation addressing its register irrespective of
  Audience Set. It is not given the Deployment Blinding Value, so it can
  establish that the disclosed policy elements are the ones the server used and
  not that the resulting hash is correct. The stronger property needs a jointly
  appointed identity, which the text says and does not build.
- **Budget exhaustion is a suppression channel** (`{#budget-suppression}`). Any
  non-answering register makes a decisive verdict unreachable, the reason is
  server-observed, and the determinism carve-out tells the auditor to disregard
  the divergence. Both available mitigations cost more than they buy; the text
  says so rather than pretending otherwise.
- **Fork detection is opportunistic.** An operator publishing to two audiences at
  disjoint sequence numbers never emits a colliding pair. What the mechanism
  establishes is that where two heads at one sequence number are observed
  together, neither can be disowned.
- **The ledger head discloses deployment size and rate** at the notarisation
  interval. It is republished per interval rather than per append to bound that.
- **`register-unresponsive` is indistinguishable from a network failure** by
  construction, so a server can still downgrade a reconciliation by asserting a
  server-observed reason. What it can no longer do is dress suppression as an act
  of the register.
- **Sweep falsifiability holds for three triggers in four.** A
  credential-revocation trigger is observable to the credential's issuer and the
  affected principal and to nobody else.

---

## 4. The two decisions left

**4.1 File -03 as it stands, or hold for the register binding.**

Filing now files a document that is internally consistent, whose every artefact
is constructible, and which is explicit that one leg of the protocol is bilateral
rather than specified. That is a defensible individual submission and the gap is
disclosed rather than discovered. Holding means writing the register binding — an
endpoint, a media type, and a COSE_Encrypt construction pinning the AEAD and the
ordering of its authenticated additional data — which is perhaps a day of
drafting and its own review round, and would make ARP implementable end to end.

My reading: file. The substrate work is what -03 is for, the register binding is
a clean, separable piece of work, and a -04 with one well-scoped addition is a
better story on the list than a -03 that slips.

**4.2 idnits.**

I could not install idnits in this environment — it is not on PyPI and not in
apt. Run `.\build-draft.ps1 -Lint` on Windows, or upload the txt to
author-tools.ietf.org and press Validate, before submitting. `-02` was clean and
nothing in this revision touches the boilerplate, but it is the one check I could
not perform.

---

## 5. Before you submit

1. `.\arp-ops.ps1 wip`, then promote the `.wip.` files over the tracked ones.
2. `.\build-draft.ps1` on Windows and confirm the txt matches
   `draft-hillier-scitt-arp.wip.txt`. The Windows and cloud toolchains were
   verified byte-identical at the start of this work; `.refcache` now needs six
   further entries (RFC 3339, 3986, 6838, 6839, 7638, 8949, 9530) which
   `seed-refcache.ps1` does not yet write. Add them there or the Windows build
   will hang on them.
3. idnits.
4. Commit the `.xml`. It is the only durable proof of which bytes were filed.
5. The three Outlook drafts reference **-02**, which is what is published. Leave
   them. If -03 goes up, they can be updated afterwards; do not update them in
   anticipation, which is the exact error the credit email asks Steven to
   correct.

---

## 6. Method note

Five dimensions, run blind to each other, remains right. Two refinements earned
this session:

- **Run the security pass before committing to a new externally-reachable
  surface, not after.** A read scope invented in one round generated three of the
  four worst findings in the next, and all three followed from an argument the
  document already made about low-entropy preimages.
- **The dependants sweep is the highest-value-per-token pass.** Twice a section
  was edited correctly and its dependants left stale; a pass that does nothing
  but ask "what else mentions the thing I just changed" caught 37 items in the
  final round and would have caught most of the churn in earlier ones.

The lifecycle walkthrough remains the highest-yield dimension. The external fact
check earned its place this session by finding the RFC 9052 error, which no
amount of internal review would have surfaced.
