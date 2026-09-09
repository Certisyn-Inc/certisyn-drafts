"""
draft-hillier-scitt-arp-04, the head-linkage condition of the quorum rule.

A relying party holds a Head Consistency Statement obtained from a witness's
own origin covering the ledger head at entry 4, and a response from the
reconciliation service naming its head at entry 2. Because the Statement covers
a head at a higher Entry Sequence Number, the party additionally reads the
`fields=linkage` arrays for entries 2 to 4 and bridges the two. That bridge is
the third condition of the quorum rule and it is what the projection exists to
serve.

  A   the deployment as the draft specifies it, sealed under SHA-256, served
      honestly.
  B   the same records with the digest moved whole to SHA3-256, service and
      witness together. Not an attack and not conformant; it is here to show
      what the projection can express.
  B'  the same move with the witness Statement from before it.
  C   one Reconciliation Hash changed at entry 2, the chain re-linked and
      re-sealed, the service serving its own rewritten arrays.
  D   the same rewrite, with the service serving the Self-Entry Hash the
      witness signed at the Statement's sequence number and its own values in
      every other position of every array.
  E   the honest ledger, with the service naming a head its own arrays do not
      carry.

C, D and E are what an operator can produce over its own history. None needs a
collision. Each needs the sealing key, which the operator holds. D needs one
further value, the Self-Entry Hash inside the Statement the witness serves to
any party without authentication.

The business records are identical in A, B, B' and E. C and D differ from them
at entry 2, which is the whole of what those two rows are about.

Not modelled, because nothing here turns on it: the type-specific fields of an
entry, the Witness Observation Time window of the fourth condition, and the
t-of-n arithmetic across several witnesses. One witness is enough to show what
a witness signature pins.

One thing is not modelled that a reader will ask about. The linkage projection
is bounded at or below the most recently published Ledger Head Statement, so in
rows D, D2 and D3 the service must have published a head at entry 4 while its
response names as-of entry 2, and the array it serves at entry 4 reports a
Self-Entry Hash its own chain does not carry. The Ledger Head Statement is
signed by the same sealing key the service holds, so it publishes whichever
pair it likes and the bound is met. The bound narrows who can do this to the
operator, which is who these rows are about.
"""
import hashlib
import os
import sys

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import arpledger as arp

SEED = b"arp-head-linkage-2026-09-07"
WITNESS_SEED = b"arp-witness-2026-09-07"

CONTENT = [
    (b"claim-0001", b"recon-0001", "2026-09-01T00:00:00Z"),
    (b"claim-0002", b"recon-0002", "2026-09-02T00:00:00Z"),
    (b"claim-0003", b"recon-0003", "2026-09-03T00:00:00Z"),
    (b"claim-0004", b"recon-0004", "2026-09-04T00:00:00Z"),
]

STATEMENT_AT = 4      # the head the witness observed
RESPONSE_AT = 2       # the head the service names
NAMES = ["Entry Sequence Number", "Prior-Entry Hash", "Self-Entry Hash",
         "Signing Input Digest"]


def h32(tag):
    return hashlib.sha256(tag).digest()


def build(dname, content):
    led = arp.Ledger(SEED, dname)
    for claim, recon, ts in content:
        led.append(h32(claim), h32(recon), ts)
    return led


def arrays(led):
    return [led.linkage(i) for i in range(RESPONSE_AT, STATEMENT_AT + 1)]


def outcome(ok):
    return "accept" if ok else "refuse"


def versions():
    try:
        from importlib.metadata import version
        return version("cbor2"), version("cryptography")
    except Exception:
        return "unavailable", "unavailable"


def main(w):
    witness_sk = Ed25519PrivateKey.from_private_bytes(
        hashlib.sha256(WITNESS_SEED).digest())
    witness_pub = witness_sk.public_key()

    rewritten = list(CONTENT)
    rewritten[1] = (CONTENT[1][0], b"recon-0002-altered", CONTENT[1][2])

    A = build("sha256", CONTENT)
    B = build("sha3_256", CONTENT)
    C = build("sha256", rewritten)

    def stmt(led, pinned=False, ends=False, at=STATEMENT_AT):
        return arp.head_consistency_statement(
            led, at, witness_sk, with_signing_input_digest=pinned,
            with_prior_entry_hash=ends)

    def resp(led, seq=RESPONSE_AT):
        e = led.entries[seq - 1]
        r = led.response(seq)
        r["sid"] = arp.signing_input_digest(e["protected"], e["payload"],
                                            led.dname)
        return r

    def attested(led, lo=RESPONSE_AT, hi=STATEMENT_AT):
        return {i: led.linkage(i) for i in range(lo, hi + 1)}

    def spliced():
        """D: the witness-signed Self-Entry Hash at the top, C everywhere else."""
        out = [list(a) for a in arrays(C)]
        out[-1][2] = A.entries[STATEMENT_AT - 1]["self_hash"]
        return out

    def spliced_deep():
        """D2: the same, with the top array's Signing Input Digest taken from A
        as well. Costs the service one further published octet string."""
        out = spliced()
        out[-1][3] = A.linkage(STATEMENT_AT)[3]
        return out

    def spliced_ends():
        """D3: the whole top array taken from A, and the bottom array's Signing
        Input Digest taken from C's own chain, with the two interior positions
        the chain does not constrain filled from C."""
        out = [list(a) for a in arrays(C)]
        out[-1] = list(A.linkage(STATEMENT_AT))
        out[-2][3] = out[-1][1]
        return out

    wrong_head = dict(seq=RESPONSE_AT, self_hash=h32(b"a head nobody served"),
                      sid=h32(b"nor this"))

    cases = [
        ("A   served honestly", A, arrays(A), A, resp(A)),
        ("B   digest moved whole", B, arrays(B), B, resp(B)),
        ("B'  digest moved, witness before", B, arrays(B), A, resp(B)),
        ("C   rewritten, served plainly", C, arrays(C), A, resp(C)),
        ("D   rewritten, witness value spliced", C, spliced(), A, resp(C)),
        ("D2  the same, top fourth value too", C, spliced_deep(), A, resp(C)),
        ("D3  the same, whole top array", C, spliced_ends(), A, resp(C)),
        ("E   response names another head", A, arrays(A), A, wrong_head),
    ]

    cb, cr = versions()
    w("draft-hillier-scitt-arp-04, head linkage under the quorum rule")
    w("what the linkage arrays pin, and what they do not")
    w()
    w("environment")
    w("  python        %s" % sys.version.split()[0])
    w("  cbor2         %s" % cb)
    w("  cryptography  %s" % cr)
    w()
    w("construction, from the section text and nothing else")
    w("  Prior-Entry Hash   the Signing Input Digest of the preceding entry's")
    w("                     Entry Signature; thirty-two zero octets in entry 1")
    w("  Self-Entry Hash    the digest over the entry array with the Self-Entry")
    w("                     Hash and Entry Signature positions encoded as CBOR")
    w("                     null, under RFC 8949 Section 4.2.1")
    w("  Entry Signature    over the array with the Entry Signature position")
    w("                     alone null, so it covers the Self-Entry Hash")
    w("  protected header   the algorithm identifier (label 1) and the key")
    w("                     identifier (label 4), which the draft requires")
    w("                     there and forbids in an unprotected header. No")
    w("                     digest identifier is carried in either header here,")
    w("                     or anywhere in the draft, whose upgrade path")
    w("                     declares three primitive classes and no digest one.")
    w("  fields=linkage     Entry Sequence Number, Prior-Entry Hash, Self-Entry")
    w("                     Hash, Signing Input Digest. The three hashes cannot")
    w("                     be recomputed by a holder of the array: it carries")
    w("                     neither the payload nor the protected header.")
    w()
    w("scenario")
    w("  witness Statement  covers entry %d, obtained from the witness's own"
      % STATEMENT_AT)
    w("                     origin, as the draft requires and as every row")
    w("                     below observes")
    w("  response names     the service's head at entry %d" % RESPONSE_AT)
    w("  reader holds       linkage arrays for entries %d to %d, read from the"
      % (RESPONSE_AT, STATEMENT_AT))
    w("                     service, which is where the draft has them read")
    w("  keys               one sealing key and one witness key throughout")
    w()

    w("1. THE CONDITION AS THE DRAFT STATES IT")
    w()
    w("   Three parts, verified together. That the Self-Entry Hash of the array")
    w("   at the Statement's sequence number equals item 3 of that Statement.")
    w("   That the Self-Entry Hash of the array at the named head equals the one")
    w("   the response names. That the array at each sequence number carries, as")
    w("   its Prior-Entry Hash, the Signing Input Digest the array below it")
    w("   reports. The draft forbids testing a Self-Entry Hash against a")
    w("   Prior-Entry Hash, which are digests over different preimages, and no")
    w("   such test is made.")
    w()
    w("   %-40s%s" % ("case", "quorum"))
    w("   " + "-" * 56)
    rows = []
    for label, led, arr, wled, resp in cases:
        q = arp.verify_quorum_linkage(arr, stmt(wled), witness_pub, resp)
        rows.append((label, q))
        w("   %-40s%s" % (label, outcome(q[0])))
    w()
    w("   reasons given on refusal")
    for label, q in rows:
        if not q[0]:
            w("     %s" % label)
            w("       %s" % q[1])
    w()
    w("   E is the control for the second part, which every other row satisfies.")
    w()

    w("2. THE RESULT")
    w()
    w("   An entry's Signing Input Digest is bound to that entry's Self-Entry")
    w("   Hash. The Entry Signature nulls its own position alone, so its payload")
    w("   carries the Self-Entry Hash, and the Signing Input Digest is taken")
    w("   over the Sig_structure around that payload. The binding is real and it")
    w("   is in the entry.")
    w()
    w("   A holder of a linkage array cannot check it. Verifying it needs the")
    w("   payload and the protected header, and the projection carries neither.")
    w("   The three hashes arrive in one array, bound to one another, and are")
    w("   checked apart.")
    w()
    w("   The condition anchors two values to something outside the service: the")
    w("   Self-Entry Hash at the top of the span, which a witness signed, and")
    w("   the Self-Entry Hash at the bottom, which the response names. The chain")
    w("   it then walks runs on the Prior-Entry Hash and the Signing Input")
    w("   Digest. Those are different positions. Neither anchored value is in a")
    w("   position the chain reads, and no value the chain reads is anchored.")
    w()
    w("   Row D is what follows. The service holds a rewritten history, serves")
    w("   the Self-Entry Hash the witness published at the top of the span, and")
    w("   serves its own values everywhere else. Every part of the condition")
    w("   holds. The Statement is untouched and is obtained from the witness's")
    w("   own origin, as the draft requires; the service supplies only the")
    w("   arrays and the response, which is what the draft has it supply.")
    w()
    w("   Entry %d as the projection delivers it, honestly in A, rewritten in C,"
      % STATEMENT_AT)
    w("   and as the service serves it in D:")
    w()
    la, lc, ld = A.linkage(STATEMENT_AT), C.linkage(STATEMENT_AT), spliced()[-1]
    for i, n in enumerate(NAMES):
        for tag, v in (("A", la[i]), ("C", lc[i]), ("D", ld[i])):
            val = v.hex() if isinstance(v, bytes) else str(v)
            w("     %-22s %s  %s" % (n if tag == "A" else "", tag, val))
    w()
    w("   D takes its third value from A and the rest from C. The witness")
    w("   signature is satisfied and pins one octet string that nothing the")
    w("   reader walks connects to. The chain the reader walks ends at the top")
    w("   array's Prior-Entry Hash, which the service chose, and the head the")
    w("   response names is an entry of C.")
    w()
    w("   D2 and D3 are the same construction with more of A copied in, and they")
    w("   are here because they are what the obvious repairs run into. Section 4")
    w("   takes them.")
    w()

    w("3. WHICH POSITIONS THE CONDITION BINDS")
    w()
    w("   Each of the nine hash positions in the span, replaced in turn with a")
    w("   value the service chose, against the honest ledger and the honest")
    w("   Statement and response of row A.")
    w()
    w("   %-14s%-24s%s" % ("entry", "position", "verdict"))
    w("   " + "-" * 56)
    base = arrays(A)
    st_a, rs_a = stmt(A), A.response(RESPONSE_AT)
    free = []
    for idx, seq in enumerate(range(RESPONSE_AT, STATEMENT_AT + 1)):
        for pos in (1, 2, 3):
            mutated = [list(a) for a in base]
            mutated[idx][pos] = h32(b"substituted %d %d" % (seq, pos))
            ok, _ = arp.verify_quorum_linkage(mutated, st_a, witness_pub, rs_a)
            if ok:
                free.append((seq, NAMES[pos]))
            w("   %-14d%-24s%s" % (seq, NAMES[pos], outcome(ok)))
    w()
    w("   Three positions are free:")
    for seq, name in free:
        w("     entry %d %s" % (seq, name))
    w()
    w("   Two of the three are ends: the bottom array's Prior-Entry Hash reaches")
    w("   below the span and the top array's Signing Input Digest reaches above")
    w("   it, and the condition spans neither. The third is not an end. Every")
    w("   interior Self-Entry Hash is free, and a relying party that goes on to")
    w("   use one, to check a receipt against a particular entry, is using a")
    w("   value this condition never constrained. The text does not say so.")
    w()
    w("   The reader also recomputes no digest over ledger content. Arbitrary")
    w("   octets, digests of nothing in any ledger, chain as readily as an")
    w("   honest span:")
    w()
    opaque = [hashlib.sha256(b"chosen-by-the-service-%d" % i).digest()
              for i in range(7)]
    arb, prev = [], None
    for k, seq in enumerate(range(RESPONSE_AT, STATEMENT_AT + 1)):
        sid = opaque[2 * k + 1]
        arb.append([seq, prev if prev else opaque[0], opaque[2 * k + 2], sid])
        prev = sid
    arb_body = arp.det([arp.HCS_V1, STATEMENT_AT, arb[-1][2],
                        "2026-09-05T00:00:00Z", "2026-09-05T00:04:00Z"])
    arb_st = arp.cose_sign1(witness_sk, arp.det({1: -8, 4: b"witness-1"}),
                            arb_body)
    arb_st.update(seq=STATEMENT_AT, self_hash=arb[-1][2], carries_sid=False)
    ok, why = arp.verify_quorum_linkage(
        arb, arb_st, witness_pub,
        dict(seq=RESPONSE_AT, self_hash=arb[0][2]))
    w("     arbitrary octets, a witness signing the top of them")
    w("       %s | %s" % (outcome(ok), why))
    w()
    w("   Row B follows from that and is not a separate finding. A deployment")
    w("   that moved its digest whole satisfies the condition because the")
    w("   condition compares octets and never asks what produced them. The")
    w("   draft fixes SHA-256, so such a deployment is non-conformant rather")
    w("   than adversarial, and a reader holding whole entries refuses it. That")
    w("   reader, run over each ledger under SHA-256:")
    w()
    for nm, led in (("A", A), ("B", B), ("C", C)):
        ok, why = arp.verify_entries(led.entries, led.verify_key(), "sha256")
        w("     %-4s %-7s %s" % (nm, outcome(ok), why))
    w()
    w("   It accepts C, which is the rewritten history, because a rewrite the")
    w("   operator re-sealed is internally perfect. Nothing a reader recomputes")
    w("   from the entries alone separates it. What row B measures is the")
    w("   projection's expressiveness: no")
    w("   value in it names the digest, so nothing carried in a protected")
    w("   header, where a digest identifier would naturally go, reaches this")
    w("   reader at all.")
    w()

    w("4. WHAT CLOSES IT")
    w()
    w("   pinned    the Statement carries a sixth item, the Signing Input Digest")
    w("             of the entry it covers, and the reader checks the top")
    w("             array's fourth value against it.")
    w("   ends      the Statement carries a seventh item, the Prior-Entry Hash")
    w("             of that entry, and the response names the Signing Input")
    w("             Digest at the head it names, so that both ends of the span")
    w("             are anchored in positions the chain does read.")
    w("   attested  the witness publishes the linkage arrays for the span it")
    w("             observed, signed and served from its own origin, and the")
    w("             reader requires the served arrays to be those arrays.")
    w()
    w("   %-38s%-9s%-9s%-8s%s" % ("case", "rule", "pinned", "ends", "attested"))
    w("   " + "-" * 72)
    for label, led, arr, wled, resp_ in cases:
        st_p = stmt(wled, pinned=True)
        st_e = stmt(wled, ends=True)
        q = arp.verify_quorum_linkage(arr, stmt(wled), witness_pub, resp_)
        p1 = arp.verify_quorum_pinned(arr, st_p, witness_pub, resp_)
        p2 = arp.verify_quorum_ends(arr, st_e, witness_pub, resp_)
        p3 = arp.verify_quorum_attested(arr, stmt(wled), witness_pub, resp_,
                                        attested(wled))
        w("   %-38s%-9s%-9s%-8s%s" % (label, outcome(q[0]), outcome(p1[0]),
                                      outcome(p2[0]), outcome(p3[0])))
    w()
    w("   Pinning closes D and D2 defeats it, at the cost to the service of one")
    w("   further octet string the witness already published. Anchoring both")
    w("   ends closes D2 and D3 defeats it, because the array between the two")
    w("   ends is the service's and it can be made to join an anchored top to an")
    w("   unanchored bottom. Lengthening the span makes that easier and never")
    w("   harder: every interior array is two more values the condition")
    w("   constrains only against each other.")
    w()
    w("   That is the shape of the thing. Anchoring endpoints cannot work, at")
    w("   any span, because the chain is a sequence of equalities among values")
    w("   the reader cannot recompute, and an equality between two values the")
    w("   same party supplies is not evidence. Soundness has to come from a copy")
    w("   of the chain the service did not write.")
    w()
    w("   The witness holds the entries it observed, so it can publish the")
    w("   arrays. It already publishes a signed artefact at its own origin and")
    w("   the draft already forbids taking that artefact from the responding")
    w("   service, so the channel, the origin rule and the trust boundary all")
    w("   exist. What is added is the arrays themselves. That is the attested")
    w("   column, and it refuses every row where the service departed from what")
    w("   a witness saw.")
    w()
    w("   The alternative that needs nothing new is the first branch of the same")
    w("   condition, where a Statement covers the head the response names")
    w("   exactly. It carries no span, so it has no interior, and the draft")
    w("   already says of it that there is nothing to link.")
    w()
    w("   One editorial point, from reading the condition closely. The quorum")
    w("   rule calls the object a linkage triple in four places; the read")
    w("   operation defines a four-element array. The two are the same object")
    w("   and the third part of the condition sources its fourth value from it,")
    w("   so the arithmetic is right and the noun is one revision behind.")
    w()

    w("5. AN ENCODING NOTE, MEASURED IN PASSING")
    w()
    w("   The Self-Entry Hash is taken over an encoding the draft requires to")
    w("   satisfy Section 4.2.1 of RFC 8949. An implementer of that requirement")
    w("   who reaches for cbor2's canonical=True gets Section 4.2.3 map key")
    w("   ordering instead: length-first, ties broken bytewise.")
    w()
    m = {100000: 1, "z": 2}
    w("     map                        {100000: 1, 'z': 2}")
    w("     cbor2 canonical=True       %s" % cbor2.dumps(m, canonical=True).hex())
    w("     RFC 8949 Section 4.2.1     %s" % arp.det(m).hex())
    w("     SHA-256 of the first       %s"
      % hashlib.sha256(cbor2.dumps(m, canonical=True)).hexdigest())
    w("     SHA-256 of the second      %s"
      % hashlib.sha256(arp.det(m)).hexdigest())
    w()
    w("   The call is right in every other respect, and one of those respects")
    w("   matters more than the ordering. Preferred serialization requires the")
    w("   shortest floating-point form that preserves the value, and")
    w("   canonical=True gives it: 1.5 encodes as %s. This harness"
      % cbor2.dumps(1.5, canonical=True).hex())
    w("   delegates every leaf to that call for exactly that reason and takes")
    w("   back the map ordering alone. An implementer who replaces the call")
    w("   outright rather than wrapping it trades one departure for another.")
    w()
    w("   Two maps sit on the digest path here: each protected header, inside")
    w("   every Signing Input Digest. Their keys are COSE labels 1 and 4, both")
    w("   one byte, so the two orderings agree and nothing above turns on the")
    w("   difference. A protected header mixing integer and text-string labels")
    w("   would not agree, and neither would a type-specific field that is a map")
    w("   with keys of differing encoded length. Where that holds, two")
    w("   implementations compute two Self-Entry Hashes over one entry, and the")
    w("   head comparison treats it as a fork. A sentence naming the section and")
    w("   naming the ordering it is not would close it.")


if __name__ == "__main__":
    import io
    buf = io.StringIO()
    main(lambda s="": buf.write(s + "\n"))
    text = buf.getvalue()
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "run-output.txt"), "w") as f:
        f.write(text)
    sys.stdout.write(text)
