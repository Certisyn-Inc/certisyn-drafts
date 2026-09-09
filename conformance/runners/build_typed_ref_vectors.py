#!/usr/bin/env python3
"""Generate the typed-reference vector set for CPB-01.

    draft-mih-sokolov-scitt-payload-binding-01

Steven Mih asked for typed-reference vectors built against -01 and offered to
fold them into the CPB suite. This builds them. The existing CPB set has one
PASS and four MUST-FAIL cases against §7; these five are additional.

WHAT EACH VECTOR ESTABLISHES

  01  PASS control. A negatives-only set detects a verifier that is too loose
      and structurally cannot detect one that is too strict, so nothing here
      ships without one.

  02  §7.1 requires the verifier to confirm that digest_alg identifies a hash
      algorithm consistent with the registered context, and §13.1 registers
      jcs-n with SHA-256. The reference library binds digest_alg into TypedRef
      and never reads it: SHA-512, MD5, an unregistered name and the empty
      string are all accepted against a jcs-n entry, with the correct SHA-256
      digest carried, so the comparison succeeds and nothing catches it.

  03  §13.2's registration template asks an entry to declare a representation.
      §4.1 lists a raw 32-octet sequence as one of three, and permits a
      deterministic conversion only where the specification or the applicable
      payload profile expressly defines one. §7 types `digest` as a JSON
      string. A registrant reading §13.2 alone meets none of that. Carried as
      a MUST-FAIL so it is checkable rather than only arguable.

  04  §6.1: the log leaf is computed over the raw bytes of the derived
      identifier, never over its hex-string encoding. The rule is unchanged
      since -00 and no vector in the suite exercises it. The reference library
      implements no leaf construction, so this is offered as coverage.

  05  Fails on ARP's side. Appendix D of draft-hillier-scitt-arp-01 defines
      subject_digest = SHA-256(JCS(action)) and keys reconciliation on it. A
      content digest must be injective over content; a key must be stable
      under permitted variation. Five conforming instances of one registered
      action type, differing only in content that type declares optional,
      produce five distinct identifiers.

FINDING CLASS. Every vector declares one, and the runner checks it:

    conformance_baseline    correct behaviour, recorded as a control
    revision_uplift_gap     -01 requires it; the library targets -00, which
                            did not. Conformant to its own declared target.
    specification_question  two parts of -01 that do not compose. Not a defect
                            in any implementation.
    suite_coverage_gap      the rule is stated and no vector reaches it
    contributor_side_defect the failure is ARP's

The distinctions carry weight. Calling a specification gap an implementation
defect accuses an author of a bug they do not have; calling a -00-conformant
library defective against -01 invites a one-line rebuttal.

EVERY ACTION OBJECT IN VECTOR 05 IS MINTED by the CAID reference issuer at its
pinned commit before it is written out, and the build stops if any is refused.
The guard is exercised on every run against a known-bad input.

NOTHING HERE IS HAND-EDITED. Every digest, pre-image and byte string is
computed by this script from the CPB reference library and the ARP harness at
their pinned commits. Regenerate and diff rather than trusting the output.

Usage:
    python3 build_typed_ref_vectors.py --cpb-repo /path/to/scitt-payload-binding
"""

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--cpb-repo", required=True,
                 help="checkout of github.com/action-state-group/scitt-payload-binding "
                      "at the pinned commit")
_ap.add_argument("--caid-repo", required=True,
                 help="checkout of github.com/emiliaprotocol/emilia-protocol at "
                      "the pinned commit. Required, not optional: vector 05 "
                      "carries payment.release.1 action objects and every one "
                      "of them is validated against the reference issuer here "
                      "rather than by inspection.")
_ap.add_argument("--out", default=os.path.join(
    HERE, "..", "vectors", "arp-typed-ref-cpb01-v0.1.json"))
ARGS = _ap.parse_args()

sys.path.insert(0, os.path.join(HERE, "..", "harness"))
sys.path.insert(0, os.path.join(ARGS.cpb_repo, "lib"))
sys.path.insert(0, os.path.join(ARGS.caid_repo, "caid", "impl", "python"))

import arp_reconcile as arp                                   # noqa: E402
import caid as C                                              # noqa: E402
from cpb.canonicalize import canonical_digest, jcs, normalize  # noqa: E402

DRAFT = "draft-mih-sokolov-scitt-payload-binding-01"

_REGISTRY_PATH = os.path.join(
    ARGS.caid_repo, "caid", "registry", "action-types.json")
_REGISTRY = json.load(open(_REGISTRY_PATH))
CAID_DEFS = _REGISTRY["types"]
CAID_OPT = {"suite": "jcs-sha256", "definitions": CAID_DEFS}


def issue_or_die(action, label):
    """Mint a CAID, or stop the build. Never write out an action object that
    this repository's own reference issuer refuses."""
    out = C.compute_caid(action, CAID_OPT)
    if "caid" not in out:
        raise SystemExit(
            f"CAID issuer refused the {label!r} action object: "
            f"{out.get('refusals')}. Not writing the vector file. This is the "
            "check ARP-OUTCOME-VECTORS v0.1 did not have.")
    assert C.verify_caid(action, out["caid"], {"definitions": CAID_DEFS})["valid"]
    return out["caid"]


def _prove_the_guard_is_live():
    """A guard that has never refused anything is not known to be a guard.

    Puts a known-bad action object -- a plaintext `beneficiary_account`, where
    the registry types the field as a digest -- through issue_or_die ITSELF,
    and fails the build unless that call raises. Exercising the guard rather
    than the validator behind it is the point: a guard that is present but
    inert would otherwise be indistinguishable from a working one.
    """
    bad = {
        "action_type": "payment.release.1",
        "amount": "1250.00",
        "currency": "USD",
        "beneficiary_account": "AU-4471-0092",     # plaintext, not sha256:<hex>
        "payment_instruction_id": "pi-2026-0731-0007",
    }
    refusals = C.compute_caid(bad, CAID_OPT).get("refusals")
    if not refusals or "mistyped_field:beneficiary_account" not in refusals:
        raise SystemExit(
            "the CAID issuer accepted a plaintext beneficiary_account. Either "
            "the registry moved or the issuer is not doing anything, and "
            "either way this builder must not run until that is understood.")
    try:
        issue_or_die(bad, "guard-proof")
    except SystemExit:
        return str(refusals)
    raise SystemExit(
        "issue_or_die returned for an action object the CAID issuer refuses. "
        "The guard is present and not working, which is worse than absent "
        "because the vector file asserts it ran. Not writing anything.")


GUARD_PROOF = _prove_the_guard_is_live()


def cd(payload, exclusion=()):
    return canonical_digest(payload, frozenset(exclusion))


def preimage(payload, exclusion=()):
    p = {k: v for k, v in payload.items() if k not in set(exclusion)}
    return jcs(normalize(p)).decode("utf-8")


def arp_sd(action):
    """ARP Appendix D: subject_digest = SHA-256(JCS(action)). No exclusion set,
    no absent-field normalisation. That is the whole of the difference."""
    return hashlib.sha256(arp.jcs_bytes(action)).hexdigest()


# The artefact every vector cites. Deliberately the payload the existing suite
# already uses, so a reader can line these up against typed-ref-pass-01 without
# re-deriving anything.
AUTH_DOC = {
    "doc_id": None,
    "subject": "WS-42",
    "scope": "temperature-write",
    "issued_at": "2026-07-24T00:00:00Z",
}
AUTH_EXCL = ["doc_id"]
AUTH_D = cd(AUTH_DOC, AUTH_EXCL)

AUTH_ENTRY = {
    "name": "authorization-doc",
    "digest_context": "jcs-n; exclusion set {doc_id}; 64-char lowercase hex",
    "algorithm": "jcs-n",
    "exclusion_set": AUTH_EXCL,
    "representation": "bare_hex",
}


def v01_pass():
    return {
        "id": "typed-ref-cpb01-01",
        "description": (
            "PASS: conformance baseline for CPB-01 §7. The registry entry, the "
            "carried digest_alg, the carried representation and the recomputed "
            "digest are all mutually consistent. A verifier MUST report this "
            "reference as verified. Present so the set is two-sided: four "
            "MUST-FAIL vectors can detect a verifier that is too loose and "
            "structurally cannot detect one that is too strict."),
        "spec_ref": f"{DRAFT} §7, §7.1",
        "finding_class": "conformance_baseline",
        "must_fail": False,
        "artifact_type_registry_entry": dict(AUTH_ENTRY),
        "cited_artifact": {
            "payload": AUTH_DOC,
            "pre_image": preimage(AUTH_DOC, AUTH_EXCL),
            "derived_id": AUTH_D,
        },
        "typed_reference": {
            "type": "authorization-doc",
            "digest_alg": "SHA-256",
            "digest": AUTH_D,
        },
        "expected": {"verified": True, "recomputed_digest": AUTH_D},
    }


def v02_digest_alg():
    return {
        "id": "typed-ref-cpb01-02",
        "description": (
            "MUST-FAIL: digest_alg is inconsistent with the digest context "
            "registered for the artifact type. §13.1 registers jcs-n with "
            "SHA-256. The reference carries digest_alg 'SHA-512' while "
            "carrying the correct SHA-256 derived identifier, so the digest "
            "comparison at step 4 succeeds and the reference still MUST NOT be "
            "reported as verified. The check that fails is the one that has no "
            "effect on the bytes, which is why nothing catches it by "
            "accident."),
        "spec_ref": (
            f"{DRAFT} §7.1 ('It MUST confirm that digest_alg identifies a hash "
            "algorithm consistent with that context.'), §13.1 (jcs-n: 'RFC "
            "8785 JCS over a normalized JSON object (null, empty-array, and "
            "empty-object members removed bottom-up); SHA-256; lowercase "
            "hex'), and §7 (the digest_alg row: 'The canonicalization "
            "context of the "
            "cited artifact is resolved from its artifact type's registry "
            "entry (Section 13.2), not from this field.')"),
        "finding_class": "revision_uplift_gap",
        "revision_note": (
            "The reference library declares its target in lib/cpb/typed_ref.py "
            "line 4: 'Reference: draft-mih-sokolov-scitt-payload-binding-00 "
            "§6' -00 §7.1 requires the verifier to confirm that the carried "
            "IDENTIFIER is consistent with the established context; it says "
            "nothing about digest_alg. The digest_alg sentence is new in -01. "
            "So the library is conformant to the revision it targets and this "
            "is not a defect in it. It is what a -01 uplift has to add."),
        "must_fail": True,
        "failure_reason": "digest_alg_inconsistent_with_registered_context",
        "artifact_type_registry_entry": dict(
            AUTH_ENTRY, hash_algorithm_registered_by_algorithm_entry="SHA-256"),
        "cited_artifact": {
            "payload": AUTH_DOC,
            "pre_image": preimage(AUTH_DOC, AUTH_EXCL),
            "derived_id": AUTH_D,
        },
        "typed_reference": {
            "type": "authorization-doc",
            "digest_alg": "SHA-512",
            "digest": AUTH_D,
        },
        "expected": {
            "verified": False,
            "reason": "digest_alg_inconsistent_with_registered_context",
        },
        "note_second_form": (
            "The same missing check admits an unregistered algorithm name "
            "entirely. Measured on the same code path: 'SHA-512', "
            "'not-a-hash-algorithm', 'MD5' and the empty string are all "
            "accepted. Recorded here rather than as four more vectors because "
            "it is one missing check, not four."),
    }


def v03_representation():
    return {
        "id": "typed-ref-cpb01-03",
        "description": (
            "SPECIFICATION QUESTION, carried as a MUST-FAIL so it is checkable "
            "rather than only arguable. §4.1 lists three representations, one "
            "of which is a raw 32-byte octet sequence, and §13.2's "
            "registration template requires an entry to declare 'the "
            "representation of the output'. So an artifact type may be "
            "registered with representation 'raw'. But §7's field table types "
            "`digest` as a JSON string, and 32 arbitrary octets have no form "
            "as a JSON string. The draft is not inconsistent about this: §4.1 "
            "permits a deterministic conversion ONLY WHERE the specification "
            "or the applicable payload profile expressly defines both the "
            "conversion and the resulting comparison representation. Note the "
            "modal -- §4.1 conditions a permission and obliges nobody. The "
            "consequence of defining no conversion falls on the VERIFIER, at "
            "§7.1: it MUST NOT report the reference as verified. So a "
            "registrant who registers 'raw' and defines nothing has violated "
            "nothing; their references simply never verify. The question is "
            "narrow and is about where that is discoverable. §13.2's template "
            "asks for a representation and mentions neither §4.1's condition "
            "nor §7's string typing, so a registrant reading §13.2 alone "
            "learns nothing about either."),
        "spec_ref": (
            f"{DRAFT} §4.1 (three representations, 'distinct and are not "
            "implicitly interchangeable'; 'A verifier MUST NOT silently coerce "
            "among representations'; 'A deterministic conversion MAY be "
            "applied only where this specification or the applicable payload "
            "profile expressly defines both the conversion and the resulting "
            "comparison representation.'), §7 (field table: digest, type string), "
            "§7.1 ('if a required deterministic conversion to a common "
            "comparison representation is not expressly defined, the verifier "
            "MUST NOT report the typed reference as verified'), §13.2 "
            "(registration template)"),
        "finding_class": "specification_question",
        "not_a_defect_note": (
            "This is not reported against the reference library. Its "
            "verify_typed_ref takes `digest: str`, so raw octets cannot be "
            "handed to it at all, and its _check_representation applying the "
            "bare-hex test to the 'raw' branch is a consequence of that API "
            "shape rather than a misreading of the draft. The observation "
            "below records what the library does only so the question is "
            "grounded in something runnable."),
        "must_fail": True,
        "failure_reason": "registrable_representation_has_no_form_in_the_digest_field",
        "artifact_type_registry_entry": {
            "name": "authorization-doc-raw",
            "digest_context": "jcs-n; exclusion set {doc_id}; 32 raw octets",
            "algorithm": "jcs-n",
            "exclusion_set": AUTH_EXCL,
            "representation": "raw",
        },
        "cited_artifact": {
            "payload": AUTH_DOC,
            "pre_image": preimage(AUTH_DOC, AUTH_EXCL),
            "derived_id_bare_hex": AUTH_D,
        },
        "typed_reference": {
            "type": "authorization-doc-raw",
            "digest_alg": "SHA-256",
            "digest": AUTH_D,
            "note": (
                "This carries bare hex because there is nothing else it could "
                "carry. That is the question, not a workaround for it."),
        },
        "expected": {
            "verified": False,
            "reason": "registrable_representation_has_no_form_in_the_digest_field",
        },
        "two_ways_to_close_it": [
            {
                "change": (
                    "§13.2's registration template gains a line: an entry "
                    "declaring a representation not expressible as a JSON "
                    "string MUST also cite the section defining its "
                    "conversion under §4.1."),
                "cost": (
                    "This is new normative behaviour on registrants, not a "
                    "clarification. It moves the failure from verification "
                    "time to registration time and makes an entry that is "
                    "well-formed today non-conforming. That is the point of "
                    "it, but it should be stated rather than sold as free."),
            },
            {
                "change": (
                    "§7.1 or §13.2 expressly defines the lowercase-hex "
                    "transcription of the raw form as the common comparison "
                    "representation, discharging §4.1 centrally rather than "
                    "per profile."),
                "cost": (
                    "It makes 'raw' and 'bare_hex' operationally identical in "
                    "the digest field, which arguably empties 'raw' of "
                    "meaning as a distinct registrable representation for "
                    "typed references. It also takes back a delegation §4.1 "
                    "appears to have made deliberately."),
            },
        ],
        "preference": (
            "The first, on the reasoning that §4.1's delegation to the "
            "payload profile looks deliberate and the second option reverses "
            "it. A preference, not a finding, and the cost above is real."),
        "an_answer_this_vector_does_not_have": (
            "§4.1 and §7 both locate the representation declaration in the "
            "PAYLOAD CLASS, while §13.2's Digest Context separately lists "
            "'the representation of the output'. This vector treats those as "
            "one declaration. If they are not -- if §7's digest field carries "
            "the payload class's representation and not the registry entry's "
            "-- the question above is answered and the vector should be "
            "withdrawn. That reading is the author's to give."),
    }


def v04_leaf_construction():
    """§6.1. Unchanged since -00; the suite does not reach it."""
    d = AUTH_D
    raw = bytes.fromhex(d)
    ascii_bytes = d.encode("utf-8")

    return {
        "id": "typed-ref-cpb01-04",
        "description": (
            "MUST-FAIL: leaf constructed over the hex-string encoding of the "
            "derived identifier instead of over its raw bytes. §6.1 states the "
            "rule in both directions and writes the wrong form out explicitly. "
            "No vector in the suite exercises it. The failure it describes is "
            "silent: a wrong leaf hashes cleanly and produces a well-formed "
            "inclusion proof that no correct log will accept."),
        "spec_ref": (
            f"{DRAFT} §6.1 ('the log leaf MUST be computed over the raw bytes "
            "of the derived identifier, not over its hex-string encoding')"),
        "finding_class": "suite_coverage_gap",
        "revision_note": (
            "§6.1 is NOT new in -01. It appears verbatim in -00 at the same "
            "section number, with the same MUST and the same two code lines, "
            "and -00 Appendix C.1.2 carries the same rule for the GAR session "
            "block."),
        "must_fail": True,
        "failure_reason": "leaf_input_is_hex_encoding_not_raw_bytes",
        "reachable_by_reference_library": False,
        "reachability_note": (
            "lib/cpb implements no leaf construction, so there is nothing in "
            "the reference library for this vector to accept or refuse. It is "
            "offered as coverage for implementations that key a log on the "
            "derived identifier, and it is checked here only against its own "
            "recorded bytes. A runner reporting it as a library pass or a "
            "library failure would be inventing a result."),
        "derived_identifier": d,
        "correct_leaf_input": {
            "rule": "leaf_input = bytes.fromhex(D)",
            "length_bytes": len(raw),
            "bytes_hex": raw.hex(),
        },
        "incorrect_leaf_input": {
            "rule": "leaf_input = D.encode(\"utf-8\")",
            "length_bytes": len(ascii_bytes),
            "bytes_hex": ascii_bytes.hex(),
        },
        "vds_note": (
            "§6 states this profile is VDS-agnostic and imposes no VDS "
            "requirement, so CPB-01 does not say how leaf_input is hashed. "
            "§6.1 constrains the INPUT only. The derivations below are "
            "recorded so the vector is byte-checkable by an implementer who "
            "has already chosen a VDS; they are illustrative and are NOT "
            "CPB-01 requirements. An implementation on a different VDS checks "
            "§6.1 by comparing leaf_input, not these."),
        "illustrative_derivations": {
            "sha256_of_correct_leaf_input": hashlib.sha256(raw).hexdigest(),
            "sha256_of_incorrect_leaf_input": hashlib.sha256(ascii_bytes).hexdigest(),
            "rfc6962_leaf_hash_correct": hashlib.sha256(b"\x00" + raw).hexdigest(),
            "rfc6962_leaf_hash_incorrect": hashlib.sha256(b"\x00" + ascii_bytes).hexdigest(),
            "rfc6962_note": (
                "RFC 6962 §2.1 prefixes a leaf with 0x00 before hashing "
                "(0x01 is the interior-node prefix). Shown for one concrete "
                "VDS because 'raw bytes' and 'hash of raw bytes' are "
                "themselves easy to conflate, which is the same class of error "
                "§6.1 is about."),
        },
        "expected": {
            "verified": False,
            "reason": "leaf_input_is_hex_encoding_not_raw_bytes",
            "check": (
                "A verifier constructing the leaf per §6.1 produces "
                "correct_leaf_input. Any implementation producing "
                "incorrect_leaf_input fails this vector. The two are "
                "distinguishable by length alone, 32 against 64, which is the "
                "cheapest possible guard and worth writing down."),
        },
        "prior_evidence": (
            "GAR CT leaf 166 (Tom Sato, gar-core.ts fe18f24) already "
            "constructs the leaf as SHA-256 over bytes.fromhex(id) rather than "
            "over id.encode('utf-8'), and the vectors README files it under "
            "historical evidence, explicitly not a suite member. This vector "
            "turns that evidence into a test. The evidence remains Tom's and "
            "under his own digest context; nothing here relabels it."),
    }


def v05_arp_fails_first():
    """The vector that fails on ARP's side.

    Every action object is minted by the CAID reference issuer before it is
    written out; the build stops if any is refused.
    """
    ref_plain = {
        "type": "authorization-doc",
        "digest_alg": "SHA-256",
        "digest": AUTH_D,
    }
    ref_annotated = dict(ref_plain, note="purchase order 4471")

    # beneficiary_account is typed `digest` in the registry:
    # sha256:<lowercase hex> of the normalized account identifier.
    account = "acct:AU-4471-0092"
    base = {
        "action_type": "payment.release.1",
        "amount": "1250.00",
        "currency": "USD",
        "beneficiary_account":
            "sha256:" + hashlib.sha256(account.encode("utf-8")).hexdigest(),
        "payment_instruction_id": "pi-2026-0731-0007",
    }

    variants = [
        ("base",
         base,
         "the four required material fields of payment.release.1 and nothing "
         "else. Cites no artifact"),
        ("registered_optional_field_memo",
         dict(base, memo="purchase order 4471"),
         "adds `memo`, which the CAID registry declares an OPTIONAL FIELD of "
         "this exact action type. Cites no artifact -- which is the point: "
         "the identifier moves here, before any typed reference appears"),
        ("registered_optional_field_memo_empty_string",
         dict(base, memo=""),
         "the same registered optional field carrying the empty string, which "
         "the issuer accepts and which changes the bytes. Cites no artifact"),
        ("typed_digest_reference_added",
         dict(base, authorization=ref_plain),
         "adds a CPB typed digest reference to the authorising document. The "
         "issuer accepts it; it is not a registered field of the type"),
        ("optional_member_inside_the_typed_reference",
         dict(base, authorization=ref_annotated),
         "the same typed reference carrying an additional member, which CPB "
         "§7 permits and requires a verifier that does not understand it to "
         "ignore. This is the only record that exercises §7's ignore rule"),
    ]

    records = []
    for name, action, why in variants:
        records.append({
            "variant": name,
            "what_it_changes": why,
            "cites_an_artifact": "authorization" in action,
            "action": action,
            "caid": issue_or_die(action, name),
            "arp_subject_digest": arp_sd(action),
        })
    assert all(r["caid"] for r in records)
    sds = [r["arp_subject_digest"] for r in records]
    assert len(set(sds)) == len(records), "each variant must produce its own digest"

    # Both readings of a declared-field-set identifier, measured rather
    # than argued. `required` is read from the registry, not hardcoded.
    entry_ = [t for t in CAID_DEFS if t["action_type"] == "payment.release.1"][0]
    req = [f["name"] for f in entry_["required_fields"]]
    opt = [f["name"] for f in entry_.get("optional_fields", [])]

    def over(action, fields):
        keep = ["action_type"] + fields
        return hashlib.sha256(arp.jcs_bytes(
            {k: v for k, v in action.items() if k in keep})).hexdigest()

    read_a = [over(a, req + opt) for _n, a, _w in variants]
    read_b = [over(a, req) for _n, a, _w in variants]

    # Reading B's safety counterexample: one payment, two different
    # authorising documents, and no authorising document at all.
    auth_a = dict(base, authorization=dict(ref_plain, digest="aa" * 32))
    auth_b = dict(base, authorization=dict(ref_plain, digest="bb" * 32))
    collide = [over(x, req) for x in (auth_a, auth_b, base)]

    return {
        "id": "typed-ref-cpb01-05",
        "description": (
            "FAILS ON THE CONTRIBUTOR'S SIDE, and is in this set for that "
            "reason. Five action records are all conforming instances of the "
            "registered CAID type payment.release.1, each one minted by the "
            "reference issuer rather than accepted by inspection. TWO of the "
            "five carry a CPB typed digest reference; the other three cite "
            "nothing at all, and that asymmetry is the finding. ARP's "
            "Appendix D subject_digest is SHA-256(JCS(action)) over "
            "the whole action, so it produces five identifiers -- and it "
            "already produces the second one at `memo`, a field the registry "
            "declares optional, in a record that cites nothing. Whatever is "
            "happening here, it is not about typed references. A contributed "
            "vector set that only finds defects in the recipient's code has "
            "not been run against the contributor."),
        "spec_ref": (
            "draft-hillier-scitt-arp-01 Appendix D (subject_digest = "
            "SHA-256(JCS(action))), against the CAID action-type registry "
            f"entry for payment.release.1, which declares `memo` optional. "
            f"{DRAFT} §7 ('Additional fields MAY be present and MUST be "
            "ignored by verifiers that do not understand them.') is cited "
            "only for the fifth record, which is the one that exercises it."),
        "finding_class": "contributor_side_defect",
        "gap_owner": "draft-hillier-scitt-arp",
        "must_fail": True,
        "failure_reason": "arp_appendix_d_does_not_say_what_kind_of_identifier_it_defines",
        "artifact_type_registry_entry": dict(AUTH_ENTRY),
        "cited_artifact": {
            "note": ("cited by two of the five records only; see "
                     "records[].cites_an_artifact"),
            "payload": AUTH_DOC,
            "pre_image": preimage(AUTH_DOC, AUTH_EXCL),
            "derived_id": AUTH_D,
        },
        "caid_conformance": {
            "registry": f"{_REGISTRY['meta']['registry']} "
                        f"v{_REGISTRY['meta']['registry_version']}, "
                        f"updated {_REGISTRY['meta']['updated']}",
            "registry_owner": (
                "EMILIA Protocol, not ARP. Third-party input to this tree, "
                "read from the reader's own checkout at the pinned commit and "
                "listed as such in REPRODUCE.md §6."),
            "action_type": "payment.release.1",
            "required_fields": req,
            "optional_fields": opt,
            "every_action_object_here_was_minted_by_the_reference_issuer": True,
            "note": (
                "beneficiary_account is typed `digest` in the registry: "
                "sha256:<lowercase hex> of the normalized account identifier. "
                "The builder mints every object here through the reference "
                "issuer and stops if any is refused."),
        },
        "the_observation": (
            "draft-hillier-scitt-arp-01 Appendix D defines subject_digest = "
            "SHA-256(JCS(action)). That IS a statement of what the digest is: "
            "a content digest over the canonical JSON of the action. ""What it does not do is reconcile that construction with "
            "the role it simultaneously assigns it -- 'the capsules are bound "
            "to a common action through a shared subject digest', and 'each "
            "capsule is admitted to ARP as a Partial-Attestation source KEYED "
            "ON the shared subject digest'. A content digest must be injective "
            "over content: two actions differing in any byte must differ, or a "
            "receipt bound to one does not bind the other. A key must be "
            "stable under permitted variation: two producers reporting the "
            "same act, one of whom sends an optional field the other omits, "
            "must land on the same value. Those are contradictory and no "
            "single digest holds both. Note that the word 'correlation' does "
            "not appear in -01; the draft's term is subject_digest. -02 has "
            "to say which role the digest serves, and build the other."),
        "is_this_property_stated_by_arp_01": False,
        "records": records,
        "what_this_vector_does_not_claim": {
            "not_a_cpb_defect": (
                "CPB verifies the typed reference in both records that carry "
                "one and is right to; the differing members are outside the "
                "cited artifact's digest context. §7's ignore rule is "
                "exercised by exactly one of the five records, and it works."),
            "not_a_caid_defect": (
                "Five distinct CAIDs from five distinct action objects is "
                "correct and required. CAID is a content identifier and a "
                "collision across a memo change would mean a receipt bound to "
                "a CAID did not bind the memo."),
            "and_the_caid_count_is_not_a_second_measurement": (
                "MEASURED: caid.canonicalize(action) is byte-identical to "
                "arp.jcs_bytes(action), and the CAID digest field equals "
                "'sha256:' + the ARP subject digest, for every record here. "
                "The two counts are one digest in two encodings, and must "
                "not be reported side by side as corroboration: agreement "
                "between two views of one construction is code identity, not "
                "independent measurement."),
        },
        "why_arp_does_not_simply_adopt_an_exclusion_set": (
            "ARP implements no exclusion set deliberately: a correlation "
            "digest that omitted fields could correlate two materially "
            "different actions. The reading-B counterexample above is that "
            "failure, produced on purpose."),
        "who_does_not_move": (
            "CPB. Narrowing §7's MUST-ignore so it did not extend to a typed "
            "reference in a digest-bearing position would have §8 against it: "
            "a payload profile MUST NOT impose requirements on the internal "
            "structure or field values of another payload profile."),
        "one_open_question_for_the_arp_side": (
            "REVISION-PLAN-02 A4 says a CAID or signed reference travels as a "
            "separate field and is never conflated with the digest. Two of "
            "the five records here nest a typed digest reference inside the "
            "action, so it enters subject_digest. Whether A4 already forbids "
            "that placement, or speaks only to CAIDs and signed references "
            "and not to citations, is not settled -- and the three records "
            "that nest nothing carry the observation regardless."),
    }


def main():
    vectors = [
        v01_pass(),
        v02_digest_alg(),
        v03_representation(),
        v04_leaf_construction(),
        v05_arp_fails_first(),
    ]

    doc = {
        "suite": "ARP contribution to the CPB typed-reference conformance vectors",
        "target": DRAFT,
        "version": "v0.1",
        "generated_by": "conformance/runners/build_typed_ref_vectors.py",
        "generated_from": {
            "cpb_reference_library": (
                "cpb.canonicalize (canonical_digest, jcs, normalize). The "
                "builder does not import cpb.typed_ref; that is used by the "
                "runner."),
            "cpb_lib_sha256": {
                rel: hashlib.sha256(open(os.path.join(
                    ARGS.cpb_repo, "lib", "cpb", rel), "rb").read()).hexdigest()
                for rel in sorted(
                    f for f in os.listdir(os.path.join(ARGS.cpb_repo, "lib", "cpb"))
                    if f.endswith(".py"))
            },
            "caid_reference_issuer_sha256": hashlib.sha256(
                open(os.path.join(ARGS.caid_repo, "caid", "impl", "python",
                                  "caid.py"), "rb").read()).hexdigest(),
            "caid_registry_sha256": hashlib.sha256(
                open(_REGISTRY_PATH, "rb").read()).hexdigest(),
            "arp_harness": "conformance/harness/arp_reconcile.py",
            "arp_harness_sha256": hashlib.sha256(
                open(os.path.join(HERE, "..", "harness", "arp_reconcile.py"),
                     "rb").read()).hexdigest(),
            "note": (
                "Every side is pinned by content hash, not just ARP's, so the "
                "whole provenance is checkable."),
        },
        "standing_rules": [
            "Two-sided. One PASS control; four MUST-FAIL. A negatives-only set "
            "detects a verifier that is too loose and structurally cannot "
            "detect one that is too strict. Stated precisely, because the bare "
            "count flatters the coverage: against the CPB reference library "
            "the set is one PASS and TWO exercised MUST-FAILs (02, 03). 04 is "
            "structurally unreachable by that library and says so, and 05's "
            "requirement is ARP's own, not CPB-01's.",
            "Every vector declares its finding_class, and a specification "
            "question, a revision-uplift gap and an implementation defect are "
            "three different things reported three different ways.",
            "Preconditions are stated in the vector, not assumed by the "
            "runner. Every registry entry a runner needs is a field of the "
            "vector that needs it, so a third party can check it without "
            "reading the runner.",
            "One vector fails on the author's own side. A contributed set that "
            "only finds defects in the recipient's code has not been run "
            "against the contributor.",
            "Every finding is classed before it is reported, so a "
            "specification question, a revision-uplift gap and an "
            "implementation defect are never conflated.",
        ],
        "vectors": vectors,
    }

    out = os.path.abspath(ARGS.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(doc, f, indent=2, sort_keys=False)
        f.write("\n")

    blob = open(out, "rb").read()
    print(f"wrote vectors/{os.path.basename(out)}")
    print(f"  {len(vectors)} vectors, "
          f"{sum(1 for v in vectors if v.get('must_fail'))} MUST-FAIL, "
          f"{sum(1 for v in vectors if not v.get('must_fail'))} PASS")
    for v in vectors:
        print(f"  {v['id']}  {v['finding_class']:<24} "
              f"{'MUST-FAIL' if v.get('must_fail') else 'PASS'}")
    print(f"  sha256 {hashlib.sha256(blob).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
