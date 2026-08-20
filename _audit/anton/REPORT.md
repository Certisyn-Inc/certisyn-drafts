# Anton Sokolov's two 395-byte files, run against ARP

Received 2026-08-20 05:47 UTC, direct rather than to the list. Run the same
day. Files verified against the digests he published before opening them:

    87044ba351d8ce4aff9b3bd6c4b1a254a67b88cb43360acf2f42e66ae42b6d89  receipt.cose
    d374e5d49a5d68364cc2b1d0611e537c9477c29efcf3839e592c642e2cb81f09  receipt-twin.cose

Both match. The public key is the P-256 key from the device's attestation
certificate, not from any file that travelled, which is the right control.

## Everything he claimed holds

Both 395 bytes. Protected header, unprotected header and payload are
byte-identical; only the 64-octet signature differs. `r` is equal in both,
and `s2` is exactly `n - s1`. Both verify against the attestation-certificate
key. The `Sig_structure` is byte-identical, so the Signing Input Digest is
one value:

    e104e763c87f8bda5a731be370db00cd703274f43d806f14528925a34b1c14ce

The protected header decodes to `{1: -7, 4: "piv-9c/37587575"}`. PIV slot 9c
is the digital-signature slot, which corroborates his account of a
non-extractable on-die key with a touch policy.

## One thing he did not say, and it makes the case worse

**The original is high-S and the twin is low-S.** The twin is not an exotic
adversarial artefact. It is the canonical low-S normalisation of the
original, which is what any implementation following the common hardening
advice would produce on receipt.

So the second identifier does not need an attacker. A well-behaved
middlebox that normalises `s` on ingest manufactures it, from the honest
signer's own bytes, while believing it is improving matters. "Mandate low-S"
does not just fail to close the gap. Applied to an artefact already in
flight, it is one of the ways the gap gets opened.

## ARP's constructions, both revisions

    -03 Prior-Entry Hash    DIFFER
    -04 Prior-Entry Hash    SAME

    Merkle leaf, -03 (over the served envelope)  distinct   -> two entries, one act
    Merkle leaf, -04 (over the Sig_structure)    identical  -> one entry, one act

The `-04` repair does what it was written to do, on bytes a secure element
produced rather than on synthetic ones.

## The wrong answer, reported as promised

Take a holder of the original who is shown an inclusion proof issued over the
twin. Under `-03`, Section 4.9.1 requires the verifier to recompute the leaf
from the object and refuse the proof when it does not match the carried leaf.
It refuses. That is correct behaviour and it is the right outcome.

**What the document does not give it is any way to say why.** Section 4.9.1
says "MUST refuse" and stops. ARP has reason codes for a stale attestation,
an unverifiable attestation, an unresponsive register, an exhausted budget,
an incomplete notarisation, and nothing at all for *the object I hold and the
object this proof commits to are the same signing act under two encodings*.

That distinction is the whole of Section 4.9.1's own argument. It calls a
valid proof bound to the wrong leaf "the more dangerous half of its pair"
precisely because it is the case that passes every check but one. A refusal
caused by an `s` normalisation in transit and a refusal caused by an attacker
splicing another object's proof are, in ARP's error surface, the same event.

That is Sirkkavaara's false-split from this morning, arriving in ARP's
vocabulary rather than in its digests: a deployment reporting this as
detected tampering is reporting something that did not happen, and it will be
believed, because the check that produced it worked exactly as specified.

## The residual, and it is not in ARP's own digests

`-04` converts every ARP construction that was over signature-bearing bytes.
The place the twin still bites is the one identity rule ARP does not own.

Evaluation Sweep Statements chain by carrying the Transparency Service
Identifier and EntryID of the *previous* Statement's notarisation. If a
Transparency Service keys EntryID on the enveloped bytes, one Sweep Statement
has two EntryIDs available to it, and a party walking the chain backwards
from a pointer to one of them holds a pointer that the other copy's chain
does not reach. `draft-ietf-scitt-scrapi` retrieves by EntryID and offers no
query surface, so that party cannot search for the other.

The published series is ARP's evidence that a sweep it was obliged to perform
was performed. A chain that can be made to look broken by a third party who
holds no key, from bytes the honest signer produced, is a weaker instrument
than the section claims.

This is downstream of SCRAPI-11 Section 2.3.1 requiring "the same Location
URL for the same registered Signed Statement" without defining "the same"
byte-wise, which is the point already raised on the list. ARP makes a
normative reference to that document. It is not ARP's defect and ARP cannot
repair it alone, but ARP can state what it assumes, and currently does not.

## Actions

1. Reason code for the same-act-two-encodings case, so a refusal under
   Section 4.9.1 can be characterised rather than merely issued. `-04`.
2. Section 4.20.1 to state what it assumes of EntryID stability, and what
   follows for the sweep chain if a Transparency Service keys on enveloped
   bytes. `-04`.
3. Carry the low-S observation into Section 7.9: normalising `s` on ingest
   produces the twin rather than preventing it.
