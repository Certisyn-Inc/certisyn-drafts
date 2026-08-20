# CAP-1, the Coverage Attestation Profile

A tool-agnostic vocabulary for stating what an examination examined, what it did
not, and why. Eight normative rules, eight closed dispositions, stratified
populations, and a denominator that has to state its own basis.

Author: Dr Joel David Hillier, Certisyn, Inc. (Delaware, United States).
First published: see the commit history of this repository.

## The problem it addresses

A report can be complete and still silent about its own scope. "This message is
not present" is a claim about the universe; what was actually established is a
claim about a bounded artefact set examined to a stated depth. Nothing in
digital forensics currently makes anyone state the bound.

Turner put it at DFRWS in 2006: "no method has existed that captured the
criteria or method used by the examiner in deciding what to acquire." Nobody
closed it.

## What is not new here, stated first

Seven of the eight dispositions have a direct counterpart in XCCDF 1.2's
`resultEnumType` (NISTIR 7275r4, 2012). The PCI Approved Scanning Vendor
programme has required a coverage attestation with a declared denominator, an
enumerated out-of-scope set, and a rule that an incomplete run fails as
inconclusive rather than reporting clean, since 2006.

The literature search was run before publication, not after. Coverage
accounting is settled practice in configuration assessment and vulnerability
scanning. What is absent is the construct in this field. CAP-1 is a port with a
runnable conformance class, not an invention.

## Running it

    unzip cap-1.zip && cd cap-1 && ./all.sh

Node built-ins and Python standard library only. No dependencies, no network.
`verify.html` is a single file that can be opened directly in a browser and
issues no network request of any kind, established by recording every request
the page attempts under a browser engine with request interception enabled.

## What the conformance class actually establishes

- 5 positive vectors and 10 negative controls. Each control is the positive
  base with exactly one mutation, and each is refused by the rule it targets
  rather than by some other rule.
- Mutation testing on the verifier itself: silence any one of the eight rules
  and the class fails. Eight rules, eight mutants, eight kills.
- Three implementations agreeing on all fifteen vectors, **and all three are
  mine.** The class is implementation-independent, not author-independent, and
  the self-attestation caps its own verdict on exactly that ground. An
  independent implementation is the single most useful contribution anyone
  could make to this repository.
- Applied to a real Certisyn verdict document, CAP-1 refused its author's own
  engine: 227 catalogued check identifiers, 6 examined, 221 unaccounted, R1
  no-silent-remainder. The engine was changed rather than the specification.
  Both fixtures ship.

## Digests

    cap-1.zip     645dcc47a0082e48da2b6ffb654ec94e58f304d941e14bf2aaa6f6e378e0cac0
    verify.html   62ede737312cefc4e74dbf9e7ad19f65505e47386479d84e8c84b74a68afbf2c

Google refuses any message carrying a `.mjs` file, including inside a `.zip`,
so a mail-safe repack with those files renamed to `.mjs.txt` is provided for
recipients on Google Workspace or Gmail. Restoring the extensions yields files
byte-identical to the canonical package.

## Licence

The specification text is released under CC BY 4.0. The code is released under
Apache-2.0. Attribution is the only condition on the specification, and it is
the condition that matters: implement it, extend it, ship it in a product, but
cite it.

## Contributing

The most valuable contributions, in order:

1. A vector that satisfies all eight rules and still misleads a reader.
2. An independent implementation, written from the prose rather than ported.
3. A binding into an existing ontology (CASE/UCO, OSCAL) with the delta
   measured rather than asserted.

## What CAP-1 does not do

It accounts for coverage, not for actions. There is no action record here and
no transformation sealing. Those are separate problems and this repository does
not pretend to address them.
