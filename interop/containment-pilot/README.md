# Certisyn containment pilot pack

Prepared for the SCITT interoperability pilot with b7n0de. Synthetic data. Apache-2.0 for the verifier and vectors.

## Contents

- `KEY.json`: the pilot public key, agreed before anything is verified
- `FORMAT.md`: record and seal format, canonical form, verification procedure, limits
- `verify.mjs`: offline verifier, Node 20 or later, no dependencies
- `run-all.mjs`: runs every vector against `expected.json`
- `vectors/`: 2 sealed records that must be accepted (P01, P02) and 10 that must be refused (N01 to N10)
- `inputs/`: the synthetic input series behind P01 and P02
- `canonical/`: the canonical bytes of each input and each record body, for implementers in other languages
- `expected.json`: the expected outcome of every vector

## Run

    node run-all.mjs
    node verify.mjs vectors/P01.record.json vectors/P01.seal.json inputs/P01.input.json

## What each refusal vector tests

- N01 to N03: content changed after sealing
- N04 and N05: wrong signer, damaged signature
- N06 and N07: wrong domain, another record's seal
- N08 to N10: duplicate member names (identical value, escaped spelling, conflicting value), the same family as probes S11 to S15 in PR #11

## Key

`KEY.json` carries a pilot-only Ed25519 key. It signs no production seal. Agree it first, then verify.
