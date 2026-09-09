"""
ARP Settlement-Layer Ledger, the parts that carry the chain, and the readers
the document gives a relying party.

Written from draft-hillier-scitt-arp-04 section text alone. Nothing is imported
from any ARP implementation. The construction is the one the draft states:

  Prior-Entry Hash  the Signing Input Digest of the immediately preceding
                    entry's Entry Signature; thirty-two zero octets in the
                    first entry of a chain.
  Self-Entry Hash   the digest over the CBOR array of the entry with the
                    Self-Entry Hash and Entry Signature positions encoded as
                    CBOR null, under the Core Deterministic Encoding
                    Requirements of Section 4.2.1 of RFC 8949.
  Entry Signature   a COSE_Sign1 by the sealing key whose payload is the CBOR
                    array of the entry with the Entry Signature position ALONE
                    encoded as CBOR null, so that it covers every other field
                    including the Self-Entry Hash.
  Signing Input     the digest over the Sig_structure of Section 4.4 of RFC
  Digest            9052: the context string "Signature1", the protected
                    header as transmitted, the zero-length external additional
                    authenticated data, and the payload.

Note what follows from the last two together: a Signing Input Digest covers the
payload, the payload covers the Self-Entry Hash, and so an entry's Signing Input
Digest is bound to that entry's Self-Entry Hash. The binding is in the entry. It
is not in the projection, and that distinction is what this harness measures.

The draft fixes every one of these digests at SHA-256. The digest is a
constructor argument here so the same construction can be run under another.
Under "sha256" this is the draft.

The type-specific fields an Entry Type adds between the Prior-Entry Hash and
the Self-Entry Hash are not modelled. They are covered by both digests and by
the signature, and nothing below turns on their content.
"""
import hashlib

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ZERO32 = b"\x00" * 32


def digest(name, b):
    return hashlib.new(name, b).digest()


# ---- RFC 8949 Section 4.2.1 ---------------------------------------------

def _head(major, n):
    if n < 24:
        return bytes([major << 5 | n])
    if n < 0x100:
        return bytes([major << 5 | 24, n])
    if n < 0x10000:
        return bytes([major << 5 | 25]) + n.to_bytes(2, "big")
    if n < 0x100000000:
        return bytes([major << 5 | 26]) + n.to_bytes(4, "big")
    return bytes([major << 5 | 27]) + n.to_bytes(8, "big")


def det(obj):
    """Core Deterministic Encoding Requirements, RFC 8949 Section 4.2.1:
    definite lengths, preferred serialization, and map keys in the bytewise
    lexicographic order of their deterministic encodings.

    Arrays and maps are built here and leaves are delegated to cbor2 with
    canonical=True, which supplies preferred serialization: shortest-form
    integers, and the shortest floating-point form that preserves the value.
    Map ordering is not delegated, because cbor2's canonical=True sorts keys
    length-first, ties broken bytewise, which is the Length-First Map Key
    Ordering of Section 4.2.3 and not the ordering Section 4.2.1 states. The
    two agree wherever every key in a map encodes to the same length.
    """
    if isinstance(obj, dict):
        items = sorted(((det(k), det(v)) for k, v in obj.items()),
                       key=lambda kv: kv[0])
        return _head(5, len(items)) + b"".join(k + v for k, v in items)
    if isinstance(obj, (list, tuple)):
        return _head(4, len(obj)) + b"".join(det(v) for v in obj)
    return cbor2.dumps(obj, canonical=True)


def sig_structure(protected_bstr, payload):
    """Sig_structure for a COSE_Sign1, RFC 9052 Section 4.4, no external AAD.
    The protected header is passed as the byte string transmitted and is not
    re-encoded, which is what the draft requires of a verifier."""
    return det(["Signature1", protected_bstr, b"", payload])


def signing_input_digest(protected_bstr, payload, dname):
    return digest(dname, sig_structure(protected_bstr, payload))


def cose_sign1(sk, protected_bstr, payload):
    return dict(protected=protected_bstr, payload=payload,
                sig=sk.sign(sig_structure(protected_bstr, payload)))


def cose_verify(pub, s):
    try:
        pub.verify(s["sig"], sig_structure(s["protected"], s["payload"]))
        return True
    except Exception:
        return False


# ---- the ledger ----------------------------------------------------------

class Ledger:
    def __init__(self, seed, dname, alg_label=-8):
        self.sk = Ed25519PrivateKey.from_private_bytes(
            hashlib.sha256(seed).digest())
        self.dname = dname
        self.alg = alg_label            # COSE alg, -8 = EdDSA
        self.kid = b"sealing-1"         # the Sealing-Key Identifier
        self.entries = []

    def protected(self):
        """The algorithm identifier (label 1) and the key identifier (label 4),
        which the draft requires in the protected header and forbids in an
        unprotected one. No digest identifier is among them."""
        return det({1: self.alg, 4: self.kid})

    def append(self, claim_hash, recon_hash, ts, entry_type="reconciliation"):
        seq = len(self.entries) + 1
        if seq == 1:
            prior = ZERO32
        else:
            p = self.entries[-1]
            prior = signing_input_digest(p["protected"], p["payload"], self.dname)

        common = [seq, entry_type, claim_hash, recon_hash, ts, prior]
        # Self-Entry Hash preimage: both trailing positions null
        self_hash = digest(self.dname, det(common + [None, None]))
        # Entry Signature payload: the signature position alone null, so the
        # signature covers the Self-Entry Hash
        payload = det(common + [self_hash, None])
        protected = self.protected()
        self.entries.append(dict(
            seq=seq, type=entry_type, claim=claim_hash, recon=recon_hash,
            ts=ts, prior=prior, self_hash=self_hash, protected=protected,
            payload=payload,
            sig=self.sk.sign(sig_structure(protected, payload))))
        return self.entries[-1]

    def linkage(self, seq):
        """The `fields=linkage` projection: the four-element array of the Entry
        Sequence Number, the Prior-Entry Hash, the Self-Entry Hash and the
        Signing Input Digest of that entry's Entry Signature. It carries no
        Reconciliation Hash and no structural metadata, and neither the payload
        nor the protected header, so a holder of one array can recompute none
        of its three hashes."""
        e = self.entries[seq - 1]
        return [e["seq"], e["prior"], e["self_hash"],
                signing_input_digest(e["protected"], e["payload"], self.dname)]

    def response(self, seq):
        """What the reconciliation service names as its head: the
        as-of-sequence-number and the Self-Entry Hash at it."""
        e = self.entries[seq - 1]
        return dict(seq=e["seq"], self_hash=e["self_hash"])

    def verify_key(self):
        return self.sk.public_key()


# ---- the witness ---------------------------------------------------------

HCS_V1 = "arp-head-consistency-v1"


def head_consistency_statement(led, seq, witness_sk, witness_id=b"witness-1",
                               head_statement_ts="2026-09-05T00:00:00Z",
                               observed_at="2026-09-05T00:04:00Z",
                               with_signing_input_digest=False,
                               with_prior_entry_hash=False):
    """A Head Consistency Statement: a COSE_Sign1 by a witness whose payload is
    the deterministically encoded CBOR array of the text string
    arp-head-consistency-v1, the Entry Sequence Number of the head covered, the
    Self-Entry Hash of that entry, the Statement Timestamp of the Ledger Head
    Statement the witness observed, and the Witness Observation Time.

    Its protected header carries the algorithm and key identifiers and, like
    the sealing key's, names no digest.

    with_signing_input_digest appends a sixth item, the Signing Input Digest of
    the covered entry's Entry Signature. The draft has no such item. It is the
    repair this harness measures.
    """
    e = led.entries[seq - 1]
    sid = signing_input_digest(e["protected"], e["payload"], led.dname)
    body = [HCS_V1, seq, e["self_hash"], head_statement_ts, observed_at]
    if with_signing_input_digest or with_prior_entry_hash:
        body.append(sid)
    if with_prior_entry_hash:
        body.append(e["prior"])
    s = cose_sign1(witness_sk, det({1: -8, 4: witness_id}), det(body))
    s.update(seq=seq, self_hash=e["self_hash"], sid=sid,
             carries_sid=with_signing_input_digest)
    return s


# ---- readers -------------------------------------------------------------

def statement_items(statement):
    """The signed payload of a Head Consistency Statement, decoded. A reader
    that compares against anything else is comparing against something the
    witness did not sign."""
    items = cbor2.loads(statement["payload"])
    if not isinstance(items, list) or len(items) < 5 or items[0] != HCS_V1:
        return None
    return items


def verify_quorum_linkage(links, statement, witness_pub, response):
    """The head-linkage condition of the quorum rule, as the draft states it.

    Where a Statement covers a head at a higher Entry Sequence Number than the
    one the response names, the relying party additionally holds the linkage
    arrays between the two and verifies all three of: that the Self-Entry Hash
    of the array at the Statement's Entry Sequence Number equals item 3 of that
    Statement; that the Self-Entry Hash of the array at the named head equals
    the one the response names; and that the array at each sequence number
    carries, as its Prior-Entry Hash, the Signing Input Digest the array below
    it reports.

    The draft forbids testing a Self-Entry Hash against a Prior-Entry Hash for
    equality, the two being digests over different preimages. No such test is
    made here.
    """
    if not cose_verify(witness_pub, statement):
        return False, "the witness signature over the Statement does not verify"
    items = statement_items(statement)
    if items is None:
        return False, "the Statement payload is not a Head Consistency Statement"
    st_seq, st_self = items[1], items[2]
    if st_seq < response["seq"]:
        return False, ("the Statement covers entry %d, below the head the "
                       "response names" % st_seq)

    by_seq = {a[0]: a for a in links}
    span = list(range(response["seq"], st_seq + 1))
    missing = [s for s in span if s not in by_seq]
    if missing:
        return False, "the reader holds no array for entry %d" % missing[0]

    if by_seq[st_seq][2] != st_self:
        return False, ("Self-Entry Hash at entry %d does not equal item 3 of "
                       "the Statement" % st_seq)
    if by_seq[response["seq"]][2] != response["self_hash"]:
        return False, ("Self-Entry Hash at entry %d is not the one the response "
                       "names" % response["seq"])
    for a, b in zip(span, span[1:]):
        if by_seq[b][1] != by_seq[a][3]:
            return False, ("entry %d Prior-Entry Hash does not equal entry %d "
                           "Signing Input Digest" % (b, a))
    return True, "%d links chained" % (len(span) - 1)


def verify_quorum_pinned(links, statement, witness_pub, response):
    """Repair 1. The Statement carries a sixth item, the Signing Input Digest
    of the entry it covers, and the reader checks the array's fourth value
    against it."""
    ok, why = verify_quorum_linkage(links, statement, witness_pub, response)
    if not ok:
        return False, why
    items = statement_items(statement)
    if len(items) < 6:
        return False, "the Statement carries no Signing Input Digest to pin against"
    by_seq = {a[0]: a for a in links}
    if by_seq[items[1]][3] != items[5]:
        return False, ("Signing Input Digest at entry %d does not equal the one "
                       "the witness signed" % items[1])
    return True, "the top array's fourth value is one the witness signed"


def verify_quorum_ends(links, statement, witness_pub, response):
    """Repair 2. Both ends anchored in positions the chain reads: the Statement
    carries a seventh item, the Prior-Entry Hash of the entry it covers, and the
    response names the Signing Input Digest at the head it names."""
    ok, why = verify_quorum_linkage(links, statement, witness_pub, response)
    if not ok:
        return False, why
    items = statement_items(statement)
    if len(items) < 7 or "sid" not in response:
        return False, "one end carries no chain value to anchor against"
    by_seq = {a[0]: a for a in links}
    if by_seq[items[1]][1] != items[6]:
        return False, ("Prior-Entry Hash at entry %d does not equal the one the "
                       "witness signed" % items[1])
    if by_seq[response["seq"]][3] != response["sid"]:
        return False, ("Signing Input Digest at entry %d is not the one the "
                       "response names" % response["seq"])
    return True, "both ends anchored in positions the chain reads"


def verify_quorum_attested(links, statement, witness_pub, response,
                           witness_arrays):
    """Repair 3. The witness publishes, and signs, the linkage arrays for the
    span it observed, and the reader takes them from the witness's own origin.
    witness_arrays is that published set, keyed by Entry Sequence Number."""
    ok, why = verify_quorum_linkage(links, statement, witness_pub, response)
    if not ok:
        return False, why
    if not witness_arrays:
        return False, "the witness published no arrays to compare against"
    by_seq = {a[0]: a for a in links}
    for seq, served in sorted(by_seq.items()):
        attested = witness_arrays.get(seq)
        if attested is None:
            return False, "the witness attested no array at entry %d" % seq
        if list(served) != list(attested):
            return False, ("the array served at entry %d is not the one the "
                           "witness attested" % seq)
    return True, "every array in the span matches one the witness attested"


def verify_entries(entries, pubkey, dname="sha256"):
    """A reader holding whole entries, verifying under the digest the draft
    fixes: recomputing each Self-Entry Hash, recomputing each Prior-Entry Hash
    as the Signing Input Digest of the preceding entry, and verifying each
    Entry Signature."""
    for i, e in enumerate(entries):
        common = [e["seq"], e["type"], e["claim"], e["recon"], e["ts"], e["prior"]]
        if digest(dname, det(common + [None, None])) != e["self_hash"]:
            return False, ("entry %d Self-Entry Hash does not recompute under "
                           "%s" % (e["seq"], dname))
        expect = ZERO32 if i == 0 else signing_input_digest(
            entries[i - 1]["protected"], entries[i - 1]["payload"], dname)
        if e["prior"] != expect:
            return False, ("entry %d Prior-Entry Hash does not recompute under "
                           "%s" % (e["seq"], dname))
        if not cose_verify(pubkey, e):
            return False, "entry %d Entry Signature does not verify" % e["seq"]
    return True, "%d entries recompute and verify under %s" % (len(entries), dname)
