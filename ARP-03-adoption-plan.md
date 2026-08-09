# ARP -03: adoption plan

Response to the review's specific details. Three of the four I am taking as
written. One I am taking on its goal but not its mechanism, because the
mechanism specifies an endpoint SCRAPI does not define — and writing it into a
normative binding section would produce exactly the interoperability failure the
section exists to prevent.

Checked against `draft-ietf-scitt-scrapi-11`, currently in the RFC Editor queue.

---

## 1. Registry formats — accepted, and better than my own framing

I said "named formats beat 'common supply chain formats'." These are named, and
they are the right ones. Adopted for -03:

- **BODS** — the flattening case is the interesting one and the review has put
  its finger on the hard part. A beneficial-ownership tree is exactly where the
  controlled projection function earns its keep: the relying party asks a
  question about ultimate beneficial ownership, the register can answer a
  shallower predicate, and the projection is the mapping between them. BODS
  gives a concrete statement structure to write that against rather than prose.
- **vCard / W3C Org Ontology** — corporate registry and legal entity
  representation.
- **UN/CEFACT XML and the WCO Data Model** — customs declarations and transport
  registers.
- **OFAC and EU Consolidated Sanctions** — and the review is right that the
  delta-update and syndication-feed question is the substantive one, not the
  parse. A consolidated list that updates by delta means the *list version* is
  part of what a verdict is relative to. That interacts directly with
  policy-version-hash sealing and with retroactive re-evaluation, and it is
  currently unstated.

That last point is the most valuable thing in this list. A sanctions verdict
without a list version is not reproducible, and ARP already has the machinery to
carry one.

## 2. SCRAPI binding — accepted, with one correction

Endpoints, verified against SCRAPI -11:

| Purpose | Method and path |
|---|---|
| Register a Signed Statement | `POST /entries` |
| Poll for / retrieve a Receipt | `GET /entries/{EntryID}` |
| Transparency Service keys | `GET /.well-known/scitt-keys` |
| Single key by identifier | `GET /.well-known/scitt-keys/{kid_value}` |

**`POST /entries` is correct.** Items 1–3 of the review's list are adopted as
written.

Two additions the list omits, both interop-critical:

- **`POST /entries` takes a COSE Signed Statement, not free JSON.** So "the
  exact JSON/CBOR schema for encapsulating a Reconciliation Output" is more
  precisely a COSE_Sign1 whose payload is the Reconciliation Output and whose
  protected header carries the content type. ARP already registers media types
  in its IANA Considerations; the binding should use those rather than mint new
  ones.
- **Registration may be asynchronous.** SCRAPI returns `201 Created` when
  registration completes immediately, or `202 Accepted` with a `Location` header
  when it does not, and `GET /entries/{EntryID}` then answers `204 No Content`
  until the receipt exists. An ARP implementer who codes only the 201 path will
  interoperate with some Transparency Services and not others. That is a
  divergence between two conforming implementations, which is the exact failure
  the binding section is for, and it needs to be normative.

### The correction: item 4 cannot be written as a SCRAPI binding

> "Standardize the retrieval path using a strict HTTP GET query pattern keyed
> explicitly on the policy-version hash"

**SCRAPI defines no query surface.** Retrieval is by `EntryID` alone —
`GET /entries/{EntryID}`, where the EntryID comes back in the `Location` header
at registration. There is no endpoint that accepts a search key, and no
extension point in -11 for adding one. If -03 specifies a GET query pattern
keyed on the policy-version hash and calls it a SCRAPI binding, it specifies an
endpoint that does not exist, and every implementer either ignores the section
or builds something non-interoperable against a Transparency Service that will
reject it.

The **goal is right and I am keeping it.** Preventing policy equivocation over
time is precisely what policy-version-hash sealing is for. But the mechanism
should be stronger than a lookup convention:

**Carry the policy-version hash in the protected header of the Signed
Statement.** Then the SCITT receipt cryptographically covers it. A relying party
does not look up which policy version applied — it *verifies* which one applied,
from the receipt, without trusting the Transparency Service's index or the
retrieval path it used.

A query pattern makes the binding discoverable. A covered protected header makes
it non-repudiable. For a mechanism whose stated purpose is preventing
equivocation, the second is the one that does the work: an index can be wrong or
be made to lie, and a signed header cannot.

Correlation by policy-version hash across many entries is then a client-side or
Transparency-Service-specific concern, and -03 should say so plainly rather than
imply a standard retrieval path exists. If a query surface is genuinely wanted,
that is an extension request against SCRAPI, not something ARP can define on
SCRAPI's behalf — and I would rather raise it there than assert it here.

## 3. Reference implementation — the goal yes, the wording no

I agree a reference implementation is the real gap, and I will not put this
sentence in the draft:

> "a minimal open-source Reference Implementation ... **is being developed in
> parallel**"

An Internet-Draft should not announce an artefact that does not yet exist. This
session's other correspondence is a long argument about not making claims about
unpublished things, and I would be doing the same thing in my own document. If
the implementation slips, the draft carries a promise the reader cannot check —
which is worse than the draft saying nothing, because a broken commitment is
evidence about the author rather than about the protocol.

The order I would rather work in:

1. Publish the reference implementation — projection function and
   reconciliation, CLI, one of Python or Go.
2. **Then** cite it from -03, by repository and commit, alongside the
   conformance vectors it is checked against.

If it is not ready when -03 is, -03 cites what does exist — the vectors, the run
transcripts and the reproduction path — and says nothing about what does not.
The citation lands in -04. That costs one revision of adopter friction and
avoids writing a cheque the document cannot cash.

---

## Revised matrix

| Item | Action for -03 |
|---|---|
| Post-quantum | No action. Retain. |
| Registry formats | Adopt all four. Sanctions delta-updates and list versioning are the substantive item — they bind to policy-version sealing and retroactive re-evaluation. |
| SCRAPI binding | Adopt items 1–3. Add COSE Signed Statement framing and the 202/204 asynchronous path as normative. |
| Policy-version retrieval | **Mechanism changed.** SCRAPI has no query surface. Carry the policy-version hash in the protected header so the receipt covers it; raise any query surface with SCRAPI directly. |
| Reference implementation | Publish first, cite second. No forward-looking promise in the draft text. |
