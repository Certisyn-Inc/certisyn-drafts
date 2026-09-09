# Reproducing the head-linkage measurement

Artefact under measurement: **draft-hillier-scitt-arp-03**, the head-linkage
condition of its quorum rule, and the `fields=linkage` projection of the read
operations that condition is served by.

The repair this package measures as holding is the one **draft-hillier-scitt-arp-04
specifies**, as the Witness Linkage Segment of Section 5.23.2.3 and the quorum rule
of Section 5.23.2.4. This package is the evidence for that change, not a measurement
of -04.

## What this package is

An independent construction of the Settlement-Layer Ledger chain and of the two
readers the document gives a relying party, written from the section text
alone. Nothing is imported from any ARP implementation and no implementation
was consulted. The construction is stated at the top of `arpledger.py` beside
the definitions it is taken from.

The result is in section 2 of the run output. The condition anchors two values
outside the responding service and then walks a chain over two other positions,
and no anchored value is in a position the chain reads. So a service holding a
rewritten history is accepted when it serves the Self-Entry Hash a witness
signed at the top of the span and its own values everywhere else. Section 3
gives the same result positionally, over every hash position in the span.
Section 4 measures three candidate repairs against successively cheaper forms
of the same substitution: the two that anchor endpoints are defeated, and the
one that gives the reader a copy of the chain the service did not write holds.
That third reader is what -04 adopts.

Prior art. Witness cosigning of transparency-log checkpoints is established
practice and nothing here claims it. See Haber and Stornetta, J. Cryptology 3(2),
1991; Maniatis and Baker, USENIX Security 2002; Crosby and Wallach, USENIX
Security 2009; Syta et al., IEEE S&P 2016; and the C2SP tlog-witness and
tlog-cosignature specifications with the Sigsum project. In a Merkle log the
answer to head consistency is a consistency proof under RFC 6962 or RFC 9162 and
it works. What this package measures is the case those do not reach: a hash-chained
ledger with no succinct consistency proof, whose entries are withheld from the
verifier, where two heads at different sequence numbers must be shown to lie on
one chain.

## Digests of these bytes

SHA-256, per file, so nothing depends on a concatenation convention.

    arpledger.py
      2e0e86e21b36d189acdb5ae37365d6541db3e406f81f860c6da458a2fac6b2eb
    run.py
      a6a1078843ea55f4cfe3f9c002d4008b735131fcd52595005b42a6e980e341ed
    run-output.txt
      a803a79972692bd542290100d0824566ccd2de74cc75a4cc055e06526c13b552

`run-output.txt` is reproduced by running `run.py`, so its digest is the one
that matters. The other two identify the source that produced it.

## Requirements

    python 3.11.15
    cbor2 6.1.4
    cryptography 46.0.7

## Run

    python3 run.py

The run is deterministic. Both signing keys are derived from fixed seeds, RFC
8032 signing is deterministic, and every value the run calls arbitrary is drawn
from a fixed sequence. The output reproduces byte for byte on any machine with
the same library versions. `run.py` writes `run-output.txt` beside itself and
also to standard output.

## What is in the package

    arpledger.py    the ledger construction, the witness Statement, the two
                    readers the document gives, and the three candidate
                    repairs, each beside the text it is taken from
    run.py          builds the six cases, runs the readers, writes the output
    run-output.txt  the run as produced

## Method

The entry construction, the two digests, the Entry Signature payload, the
Sig_structure, the protected header contents, the projection's four values and
the five items of the Head Consistency Statement are transcribed from the
section text with nothing added and nothing removed. The digest is a
constructor argument rather than a constant so that one case can be run under a
successor; under `sha256` the construction is the document.

Deterministic encoding is implemented rather than delegated. Section 4.2.1 of
RFC 8949 orders map keys bytewise over their deterministic encodings; cbor2's
`canonical=True` orders them length-first, which is Section 4.2.3. Leaves are
delegated to `canonical=True` because it supplies preferred serialization,
including the shortest floating-point form; arrays, maps and the key ordering
are built here. Section 5 of the run output shows the difference and where it
does and does not reach this document.

Three things are deliberately not modelled, and none of them bears on the
result: the type-specific fields an Entry Type adds between the Prior-Entry
Hash and the Self-Entry Hash, which both digests and the signature cover; the
Witness Observation Time window of the fourth condition of the quorum rule; and
the t-of-n arithmetic across a Witness Set. One witness is enough to measure
what a witness signature pins.

Every row observes the document's own trust boundary. The Head Consistency
Statement is obtained from the witness's own origin and is never touched; the
linkage arrays and the response are read from the reconciliation service, which
is where the document has them read.
