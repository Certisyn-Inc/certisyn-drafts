#!/usr/bin/env python3
"""Existence-oracle vector class for ARP Section 6.4.4: positive vectors and
negative controls by fault injection.

Vector class designed by Songbo Bu, review of 2026-08-10 (attachment
arp-03-existence-oracle-two-sided-review-2026-08-10.md, message-id
<CAK08nYYoPp4t8L_vAoH9jZMvYDL7_AMFWgU=OFL=CFJ+-4rHoQ@mail.gmail.com>). This
runner executes it against the reference endpoint in conformance/reference/, so
the class reports a measured result for that endpoint rather than not-run.

What the two sides are, stated precisely, because the weaker one is easy to
oversell:

  Positive   an entitled read of an existing resource MUST return 200, so an
             implementation cannot pass by refusing everything.
  Controls   each NV row re-runs the class against the reference endpoint with
             exactly one existence channel deliberately reintroduced by the
             author of both. This is fault injection into the implementation
             the suite was written alongside. It demonstrates that each check
             fires rather than being a no-op, and that is the weakest useful
             form of negative evidence. It does NOT show that the suite
             detects a channel not already enumerated here.

This class is therefore NOT two-sided in the sense the conformance-method work
uses that term. It becomes two-sided the first time it refuses an endpoint the
author did not write. Until then the negative side is a self-test and is
labelled as one.

The comparison is the normalised observation of Section 6.4.4: the response
with the request-binding, the response-time, the As-Of pair and the signature
removed, compared alongside the HTTP metadata the section enumerates. Every
removed value is independently checked to be valid for its own request, so
normalisation cannot become a way to ignore a discriminator.

Usage:
    python3 run_existence_oracle_vectors.py
    python3 run_existence_oracle_vectors.py --timing-samples 400
    python3 run_existence_oracle_vectors.py --spec-source ../draft-hillier-scitt-arp.md

The runner needs the draft source, because the run record binds its result to
one revision of the draft by recording spec_source_sha256 over it. The default
path assumes this tree sits inside the draft repository. Unpacked on its own it
does not, so --spec-source exists and the absence is reported as an instruction
rather than a traceback.
"""

import argparse
import base64
import hashlib
import http.client
import io
import json
import os
import statistics
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REF = os.path.join(ROOT, "reference")
sys.path.insert(0, REF)

# NOTE ON INDEPENDENCE: cbor, normalise_target and request_binding are imported
# from the module under test, so the request-binding and deterministic-encoding
# checks below compare an implementation against itself. An encoder defect --
# for example a map-key ordering that violates RFC 8949 Section 4.2.1 -- would
# be invisible to this class. That is a declared coverage gap, not an oversight;
# closing it requires a second encoder written from the RFC.
from arp_read_ref import (cbor, cose_sign1, normalise_target,  # noqa: E402
                          request_binding, serve, sig_base)
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey, Ed25519PublicKey)

FIXTURE = os.path.join(REF, "fixture-eo-v0.1.json")
PORT = 8471
SEAL_PK = None   # set in main() from the fixture's published sealing key


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------ decoding
def dec(b, i=0):
    """Minimal CBOR decoder, enough for the response payload."""
    ib = b[i]; mt, ai = ib >> 5, ib & 0x1F; i += 1
    if ai < 24:
        arg = ai
    elif ai == 24:
        arg = b[i]; i += 1
    elif ai == 25:
        arg = int.from_bytes(b[i:i + 2], "big"); i += 2
    elif ai == 26:
        arg = int.from_bytes(b[i:i + 4], "big"); i += 4
    elif ai == 27:
        arg = int.from_bytes(b[i:i + 8], "big"); i += 8
    else:
        raise ValueError("indefinite length is not deterministic CBOR")
    if mt == 0: return arg, i
    if mt == 1: return -arg - 1, i
    if mt == 2: return b[i:i + arg], i + arg
    if mt == 3: return b[i:i + arg].decode("utf-8"), i + arg
    if mt == 4:
        out = []
        for _ in range(arg):
            v, i = dec(b, i); out.append(v)
        return out, i
    if mt == 5:
        out = {}
        for _ in range(arg):
            k, i = dec(b, i); v, i = dec(b, i); out[k] = v
        return out, i
    if mt == 7:
        if ai == 20: return False, i
        if ai == 21: return True, i
        if ai == 22: return None, i
    if mt == 6:
        return dec(b, i)
    raise ValueError("unsupported major type %d" % mt)


def unwrap_sign1(body):
    v, _ = dec(body)
    protected, unprotected, payload, sig = v
    params, _ = dec(protected)
    return params, unprotected, dec(payload)[0], sig


# ------------------------------------------------------------------- client
class Client(object):
    def __init__(self, fx, keyid, port=PORT):
        p = next(x for x in fx["principals"] if x["keyid"] == keyid)
        self.sk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(p["seed"]))
        self.keyid = keyid
        self.port = port
        self.n = 0

    def get(self, rid):
        self.n += 1
        nonce = "%s-%d-%d" % (self.keyid, id(self), self.n)
        path = "/arp/outputs/" + rid
        target = "http://127.0.0.1:%d%s" % (self.port, path)
        sig = base64.b64encode(self.sk.sign(
            sig_base("GET", normalise_target(target), nonce, self.keyid))).decode()
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        t0 = time.perf_counter()
        c.request("GET", path, headers={
            "Host": "127.0.0.1:%d" % self.port,
            "Keyid": self.keyid, "Nonce": nonce, "Signature": sig})
        r = c.getresponse()
        body = r.read()
        dt = time.perf_counter() - t0
        obs = {
            "status": r.status,
            "headers": {k.lower(): v for k, v in r.getheaders()},
            "body": body,
            "elapsed": dt,
            "sent": {"method": "GET", "target": target,
                     "nonce": nonce, "keyid": self.keyid},
        }
        c.close()
        return obs


# --------------------------------------------------- normalised observation
REMOVED = ("request-binding", "response-time", "as-of-sequence-number",
           "as-of-self-entry-hash", "signature")


def normalise(obs, expect_head_seq):
    """Section 6.4.4: the response with exactly the four bound values removed.

    Returns (normalised, removed, problems). Every removed value is validated
    against its own request here, so that normalisation cannot hide an
    existence-dependent discriminator.

    Each problem is (code, text). The code names the check that fired, so a
    caller can tell which discriminator produced a refusal rather than only
    that some discriminator did. A row refused by a check other than the one
    it was designed to exercise is not evidence about the designed channel.
    """
    problems = []
    params, unprot, payload, sig = unwrap_sign1(obs["body"])
    tag, rb, status, rtime, seq, selfhash, result = payload

    s = obs["sent"]
    expect_rb = request_binding(s["method"], s["target"], s["nonce"], s["keyid"])
    if rb != expect_rb:
        problems.append(("request-binding-mismatch",
                         "request-binding does not match the request as sent"))
    if status != obs["status"]:
        problems.append(("signed-status-mismatch",
                         "signed status %r differs from HTTP status %r"
                         % (status, obs["status"])))
    try:
        time.strptime(rtime, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        problems.append(("response-time-invalid",
                         "response-time is not a valid timestamp"))
    if seq < expect_head_seq:
        problems.append(("as-of-below-head",
                         "as-of-sequence-number %r is below the published "
                         "head %r" % (seq, expect_head_seq)))
    if not isinstance(selfhash, bytes) or len(selfhash) != 32:
        problems.append(("as-of-hash-invalid",
                         "as-of-self-entry-hash is not a 32-octet digest"))
    if len(sig) != 64:
        problems.append(("signature-length",
                         "signature is not 64 octets"))
    elif SEAL_PK is None:
        problems.append(("no-sealing-key",
                         "no sealing public key available to verify against"))
    else:
        try:
            SEAL_PK.verify(sig, cbor(["Signature1", cbor({1: -8}), b"",
                                      cbor(payload)]))
        except Exception:
            problems.append(("signature-unverifiable",
                             "COSE_Sign1 signature does not verify under the "
                             "published sealing key"))

    h = obs["headers"]
    normalised = {
        "http_status": obs["status"],
        "media_type": h.get("content-type"),
        "header_names": sorted(k for k in h if k not in ("date", "server")),
        "cache_control": h.get("cache-control"),
        "length_class": "empty" if len(obs["body"]) == 0 else "cose",
        "protected_params": sorted(params.keys()),
        "unprotected_params": sorted(unprot.keys()),
        "payload_tag": tag,
        "payload_status": status,
        "result": result,
    }
    removed = {"request-binding": rb.hex(), "response-time": rtime,
               "as-of": [seq, selfhash.hex()], "signature": sig.hex()}
    return normalised, removed, problems


# ------------------------------------------------------------------ harness
class Server(object):
    def __init__(self, defect=None, port=PORT):
        self.httpd = serve(FIXTURE, port, defect)
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.t.start(); time.sleep(0.15); return self

    def __exit__(self, *a):
        self.httpd.shutdown(); self.httpd.server_close(); self.t.join(timeout=5)


def evaluate(fx, defect, timing_samples=0):
    """Run the deterministic class against one endpoint configuration.

    Returns (verdict, findings, codes). verdict is ACCEPT or REFUSE; REFUSE
    means the suite detected an existence channel or a trivially-refusing
    server. codes is the sorted set of checks that fired.

    The codes exist because REFUSE alone does not say which check produced the
    refusal. A negative control that refuses through a check other than the one
    it injects has not exercised the channel it is named for, and counting it
    as a passing control would be the suite claiming coverage it does not have.
    """
    head = int(fx["head"]["sequence_number"])
    findings = []
    codes = set()
    with Server(defect) as _:
        ent = Client(fx, "p-entitled")
        oth = Client(fx, "p-other")

        # PV-ARP-EO-01 -- an entitled read of an existing resource must succeed.
        a = ent.get("R_present")
        if a["status"] != 200:
            findings.append("PV-01 entitled read of an existing resource "
                            "returned %d, not 200" % a["status"])
            codes.add("entitled-read-refused")

        # PV-ARP-EO-02 / 03 -- the two refused arms.
        b = oth.get("R_present")
        c = oth.get("R_absent")
        for name, o in (("PV-02", b), ("PV-03", c)):
            if o["status"] != 404:
                findings.append("%s expected 404, got %d" % (name, o["status"]))
                codes.add("refused-arm-status")
        if b["status"] == 404 and c["status"] == 404:
            nb, rb_, pb = normalise(b, head)
            nc, rc_, pc = normalise(c, head)
            for tag_, probs in (("PV-02", pb), ("PV-03", pc)):
                for code, text in probs:
                    findings.append("%s %s" % (tag_, text))
                    codes.add(code)
            if nb != nc:
                diff = sorted(k for k in set(nb) | set(nc)
                              if nb.get(k) != nc.get(k))
                findings.append("normalised observations differ in %s "
                                "-- existence is observable" % ", ".join(diff))
                codes.add("normalised-observation-differs")
            if rb_["request-binding"] == rc_["request-binding"]:
                findings.append("two distinct requests share one "
                                "request-binding")
                codes.add("request-binding-collision")

        # PV-ARP-EO-04 -- charge-before-entitlement, interleaved bursts.
        seq_present, seq_absent = [], []
        for i in range(int(fx["rate_limit_per_window"]) + 3):
            seq_present.append(oth.get("R_present")["status"])
            seq_absent.append(oth.get("R_absent")["status"])
        # The predicate S6.4.4 states is that a burst of each arm yields THE
        # SAME SEQUENCE OF STATUSES. That is what is tested here. An earlier
        # form of this check tested only the 404/429 transition index, and only
        # where both arms reached 429 -- a strict subset of the predicate,
        # which meant the strongest possible budget oracle (one arm rate-limited
        # and the other never) was classed as "refused for the wrong reason"
        # rather than as the channel firing. Standing rule 11: index the check
        # by the predicate violated, not by the branch that catches it.
        # Compare WHERE the limit bites, not the raw statuses. A status
        # oracle makes the raw sequences differ too, and attributing that to
        # the budget would be a misclassed finding -- standing rule 7. The
        # 429 mask isolates the budget channel from every other channel.
        mask_present = [x == 429 for x in seq_present]
        mask_absent = [x == 429 for x in seq_absent]
        if mask_present != mask_absent:
            findings.append("PV-04 the two arms reach the rate limit at "
                            "different points under equal bursts -- the "
                            "budget is an oracle. present=%s absent=%s"
                            % (_seq_str(seq_present), _seq_str(seq_absent)))
            codes.add("budget-ordering")
        elif 429 not in seq_present:
            # Not a finding. The sequences are equal, which is what S6.4.4
            # requires. But the burst never reached the limit, so this run is
            # not evidence that they stay equal under it, and saying so is the
            # difference between a result and a claim.
            codes.add("budget-limit-not-reached")

    verdict = "REFUSE" if findings else "ACCEPT"
    return verdict, findings, sorted(codes)


def _seq_str(seq):
    """Compact run-length rendering of a status sequence, for the findings."""
    out, prev, n = [], None, 0
    for v in seq:
        if v == prev:
            n += 1
        else:
            if prev is not None:
                out.append("%dx%d" % (n, prev))
            prev, n = v, 1
    out.append("%dx%d" % (n, prev))
    return ",".join(out)


def timing_probe(fx, samples):
    """Statistical, and reported separately from conformance.

    Section 6.4.4 requires the measurement population, sample count, network
    placement, decision rule and threshold to be published with any
    timing-resistance claim. This is loopback with a tiny sample; it is
    published as such and is not a conformance verdict.
    """
    head = int(fx["head"]["sequence_number"])
    with Server(None) as _:
        oth = Client(fx, "p-other")
        pres, abst = [], []
        for i in range(samples):
            oth.n = i * 7
            pres.append(oth.get("R_present")["elapsed"])
            abst.append(oth.get("R_absent")["elapsed"])
    mp, ma = statistics.median(pres), statistics.median(abst)
    pooled = statistics.pstdev(pres + abst) or 1e-12
    effect = abs(mp - ma) / pooled
    return {
        "population": "loopback, single host, no network placement",
        "samples_per_arm": samples,
        "median_present_s": round(mp, 6),
        "median_absent_s": round(ma, 6),
        "standardised_median_difference": round(effect, 4),
        "decision_rule": "reported, not adjudicated",
        "claim": "none made",
        "note": "Loopback timing is not evidence about a deployed network "
                "path. A timing-resistance claim requires the population and "
                "threshold this run does not have.",
    }


# Each entry names the check the row is designed to trip. A row that refuses
# without firing its own discriminator is recorded with control_exercised
# false: the endpoint was rejected, but not by the channel the row injects, so
# the row is not evidence that that channel is detectable.
DEFECTS = [
    ("NV-ARP-EO-01", "status-oracle",
     "403 for unentitled, 404 for absent -- a direct status oracle",
     "refused-arm-status"),
    ("NV-ARP-EO-02", "body-oracle",
     "an error discriminator inside the signed payload",
     "normalised-observation-differs"),
    ("NV-ARP-EO-03", "header-oracle",
     "an extra HTTP header on the unentitled arm only",
     "normalised-observation-differs"),
    ("NV-ARP-EO-03b", "cache-oracle",
     "cache directives differ between the two arms",
     "normalised-observation-differs"),
    ("NV-ARP-EO-04", "ratelimit-oracle",
     "entitlement evaluated before the counter is charged",
     "budget-ordering"),
    ("NV-ARP-EO-08", "bad-signature",
     "responses sealed with a key the fixture does not publish",
     "signature-unverifiable"),
    ("NV-ARP-EO-07", "always-404",
     "every read refused, including the entitled one",
     "entitled-read-refused"),
]


# Gaps that are properties of the METHOD rather than of any row, so no run of
# this class can close them and no row records them. While any one stands, the
# aggregate cannot reach PASS: a class whose own record says what it does not
# establish should not report a headline that says otherwise.
STANDING_EVIDENCE_GAPS = {
    "one-sided-negative-class":
        "every NV row is fault injection into an endpoint written by the "
        "specification's author from his own reading of his own text. No "
        "independently written implementation has been refused, so the class "
        "is not two-sided in the conformance-method sense and cannot surface "
        "a specification defect. Closing evidence: this class refusing an "
        "endpoint written by somebody else working only from the text.",
}


DEFAULT_SPEC = os.path.abspath(os.path.join(ROOT, "..",
                                            "draft-hillier-scitt-arp.md"))

SPEC_MISSING = """\
  The draft source is not where this runner expects it:

      %s

  The run record binds its result to one revision of the draft by recording
  spec_source_sha256 over that file, so the run cannot be produced without it.
  It is NOT recorded as absent: a record that pins a source it never read would
  pass this runner and then fail the manifest, which moves the failure without
  removing it.

  This is what happens when the conformance tree is unpacked on its own -- the
  tree is a subdirectory of the draft repository and the draft sits one level
  above it. Two ways out:

      python3 runners/run_existence_oracle_vectors.py --spec-source /path/to/draft-hillier-scitt-arp.md

  or fetch the draft source alongside the tree, from the branch and commit
  named in REPRODUCE.md section 2. Reported by Walter Hawkins and by Songbo Bu
  on 2026-08-12, both of whom hit it on the packaged tree."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timing-samples", type=int, default=120)
    ap.add_argument("--spec-source", default=DEFAULT_SPEC,
                    help="path to draft-hillier-scitt-arp.md. The run records "
                         "its sha256, so the result is evidence about that "
                         "revision and no other.")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs",
                                                  "existence_oracle_run.json"))
    a = ap.parse_args()

    spec_path = os.path.abspath(a.spec_source)
    if not os.path.isfile(spec_path):
        sys.stderr.write("\nARP existence-oracle class: cannot run.\n\n")
        sys.stderr.write(SPEC_MISSING % spec_path)
        sys.stderr.write("\n\n")
        return 2

    fx = json.load(io.open(FIXTURE, encoding="utf-8"))
    global SEAL_PK
    SEAL_PK = Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(fx["sealing_public_key"]))
    invocation = "python3 " + " ".join(
        [os.path.basename(__file__)] + sys.argv[1:])

    rows = []
    failed = False           # a row did not reach its expected verdict
    unexercised = []         # a row refused, but not through its own channel

    verdict, findings, codes = evaluate(fx, None)
    rows.append({"vector": "PV-ARP-EO-01..04", "endpoint": "conforming",
                 "expected": "ACCEPT", "verdict": verdict,
                 "findings": findings,
                 "discriminators_fired": codes,
                 "requirement_source": "draft-hillier-scitt-arp-03 S6.4.4"})
    if verdict != "ACCEPT":
        failed = True

    # NV-ARP-EO-05 is a structural requirement, not a wire-observable one. A
    # server that short-circuits the absent arm emits a byte-equivalent
    # response; only source inspection, or a timing population this loopback
    # harness cannot supply, decides it. Running it and reporting ACCEPT would
    # be the suite claiming coverage it does not have, so it is carried as a
    # declared gap with the evidence that would close it named.
    method_limits = []
    v, f, c = evaluate(fx, "path-oracle")
    rows.append({
        "vector": "NV-ARP-EO-05", "endpoint": "defect:path-oracle",
        "channel": "the absent arm short-circuits the "
                   "entitlement-equivalent work",
        "expected": "REFUSE-BY-INSPECTION",
        "verdict": "NOT-DECIDABLE-FROM-WIRE",
        "findings": ["the defective endpoint is byte-equivalent under the "
                     "normalised observation, which is the finding: Section "
                     "6.4.4's same-work requirement is structural and no "
                     "response-comparison suite can decide it",
                     "closing evidence: source or trace inspection of the "
                     "entitlement path, or a timing population with a stated "
                     "network placement and threshold -- neither is available "
                     "on loopback"],
        "wire_comparison_verdict": v,
        "discriminators_fired": c,
        "designed_discriminator": None,
        "control_exercised": None,
        "row_class": "method-limit",
        "requirement_source": "draft-hillier-scitt-arp-03 S6.4.4"})
    # Not appended to `unexercised`. A negative control is credited when its
    # designed discriminator fires; a row that by construction HAS no
    # discriminator is not a control and counting it as an unexercised one
    # states the wrong thing about the suite. The requirement it names is real
    # and normative, so the row stays visible and is carried as a declared
    # limit of the method with its closing evidence named. Standing rules 9
    # and 11. Reclassified 2026-08-18.
    method_limits.append("NV-ARP-EO-05")

    for vid, defect, why, designed in DEFECTS:
        v, f, c = evaluate(fx, defect)
        exercised = (v == "REFUSE" and designed in c)
        rows.append({"vector": vid, "endpoint": "defect:" + defect,
                     "channel": why, "expected": "REFUSE", "verdict": v,
                     "findings": f,
                     "discriminators_fired": c,
                     "designed_discriminator": designed,
                     "control_exercised": exercised,
                     "requirement_source": "draft-hillier-scitt-arp-03 S6.4.4"})
        if v != "REFUSE":
            failed = True
        elif not exercised:
            unexercised.append(vid)

    timing = timing_probe(fx, a.timing_samples)

    exercised_ids = [r["vector"] for r in rows
                     if r.get("control_exercised") is True]
    # PASS is reserved for a run with no failed row, every control exercised,
    # AND no declared method limit or evidence gap standing. Letting the
    # aggregate reach PASS while `does_not_establish` still names open gaps
    # would be a summary stronger than the record it summarises.
    if failed:
        aggregate = "FAIL"
    elif unexercised or method_limits or STANDING_EVIDENCE_GAPS:
        aggregate = "PASS_WITH_DECLARED_GAPS"
    else:
        aggregate = "PASS"

    vectors_path = os.path.join(ROOT, "vectors",
                                "arp-existence-oracle-v0.1.json")
    out = {
        "class": "arp-existence-oracle",
        "version": "v0.1",
        "designed_by": "Songbo Bu, review of 2026-08-10, message-id "
                       "<CAK08nYYoPp4t8L_vAoH9jZMvYDL7_AMFWgU=OFL="
                       "CFJ+-4rHoQ@mail.gmail.com>",
        "author_added_rows": ["NV-ARP-EO-03b (cache-directive control) was "
                              "added by J. Hillier and is not part of the "
                              "class as designed"],
        "spec": "draft-hillier-scitt-arp Section 6.4.4, working copy",
        "spec_note": "The normalised-observation rule this class tests is NOT "
                     "present in -03 as circulated on 2026-08-09 (text sha256 "
                     "715513d49b10d0e8ad1379db28a073b24cccb295153a210b3b8abe1f"
                     "9fe6ac28). It was written into the working draft in "
                     "response to this class. These rows test the post-review "
                     "text.",
        "spec_source_sha256": sha256_file(spec_path),
        "fixture_sha256": sha256_file(FIXTURE),
        "reference_sha256": sha256_file(os.path.join(REF, "arp_read_ref.py")),
        "runner_sha256": sha256_file(os.path.abspath(__file__)),
        "vectors_sha256": sha256_file(vectors_path),
        "invocation_note": "the invocation, interpreter and platform are "
                           "recorded in runs/existence_oracle_timing.json; "
                           "they are excluded here so that this record is "
                           "byte-identical across platforms and interpreters "
                           "and can be pinned in REPRODUCE.md",
        "result_subject": "conformance/reference/arp_read_ref.py at "
                          "reference_sha256, under this class only",
        "controls_exercised": exercised_ids,
        "controls_not_exercised": unexercised,
        "establishes": "that Section 6.4.4 as its author reads it is "
                       "implementable, and that each control listed in "
                       "controls_exercised fires against the defect it "
                       "injects. It establishes nothing about the channels "
                       "listed in controls_not_exercised: those rows either "
                       "are not decidable from the wire or were refused "
                       "through a check other than the one they inject.",
        "does_not_establish": "anything about the specification. The endpoint "
                              "was written by the specification's author from "
                              "his own reading of his own text, so it is the "
                              "one configuration that cannot surface a "
                              "specification defect. Specification adequacy is "
                              "untested until an implementer working only from "
                              "the text passes this class.",
        "evidence_status": "measured for the deterministic rows; declared gaps "
                           "listed below",
        "deterministic_result": aggregate,
        "deterministic_result_note": "PASS requires every row to reach its "
                                     "expected verdict, every negative "
                                     "control to have fired its own designed "
                                     "discriminator, AND no declared method "
                                     "limit or standing evidence gap to "
                                     "remain. "
                                     "PASS_WITH_DECLARED_GAPS means no row "
                                     "failed but at least one channel in "
                                     "controls_not_exercised was never "
                                     "exercised. FAIL means a row did not "
                                     "reach its expected verdict. The process "
                                     "exit status is 0 for PASS and for "
                                     "PASS_WITH_DECLARED_GAPS, and 1 for "
                                     "FAIL: a disclosed gap is not a failure, "
                                     "and the distinction is carried here and "
                                     "in the printed result rather than in "
                                     "the exit code.",
        "method_limits": method_limits,
        "method_limits_note": "NV-ARP-EO-05 names a real and normative "
                              "requirement -- the same-work requirement of "
                              "S6.4.4 -- that no response-comparison suite can "
                              "decide, because a short-circuit that produces "
                              "byte-equivalent responses is invisible to one "
                              "by construction. It is carried as a limit of "
                              "the method and NOT as an unexercised control: a "
                              "negative control is credited when its designed "
                              "discriminator fires, and a row that by "
                              "construction has no discriminator is not a "
                              "control. Counting it as one stated the wrong "
                              "thing about the suite. Reclassified 2026-08-18. "
                              "Closing evidence: source or trace inspection of "
                              "the entitlement path, or a timing population "
                              "with a stated network placement and acceptance "
                              "threshold.",
        "standing_evidence_gaps": STANDING_EVIDENCE_GAPS,
        "covered_elsewhere": {
            "encoder-independence":
                "CLOSED 2026-08-18 by the arp-deterministic-encoding class, "
                "runs/deterministic_encoding_run.json. This class still "
                "computes request-binding and deterministic CBOR with "
                "functions imported from the implementation under test, and "
                "that has not changed: an encoder defect is still invisible "
                "HERE. What changed is that the imported encoder is now "
                "pinned to byte strings fixed in a vector file and derived by "
                "nothing at run time, and three named encoder defects -- "
                "length-first map ordering, non-shortest arguments and "
                "indefinite-length containers -- are each refused by the row "
                "designed to trip them. A silent encoder defect would "
                "therefore be caught in this tree even though it remains "
                "undetectable in this class. Stated as coverage moved rather "
                "than as coverage gained.",
        },
        "declared_coverage_gaps": [
            "NV-ARP-EO-04: CLOSED 2026-08-18. The defect implementation was "
            "rebuilt. It previously skipped the charge on BOTH refused arms, "
            "which is a budget bug and not an oracle, so the two arms stayed "
            "indistinguishable and the channel the row is named for was never "
            "opened. It now performs the resource lookup before charging, so "
            "an absent read costs nothing and a present one costs a unit, and "
            "the two arms reach the limit at different points. The "
            "discriminator was also widened from the 404/429 transition index "
            "to the 429 mask, because the transition index is a strict subset "
            "of the predicate S6.4.4 states and classed the strongest form of "
            "the oracle -- one arm limited, the other never -- as a refusal "
            "for the wrong reason. Standing rule 11. Found by Songbo Bu.",
            "NV-ARP-EO-06: the statistical timing row of the class as designed "
            "is not carried as a conformance row. It is reported separately "
            "as timing_observation and is not adjudicated.",
            "Timing resistance: no claim is made and none is tested; the "
            "loopback observation below is not evidence about a deployed path."
        ],
        "rows": rows,
        "timing_observation": "recorded separately in "
                              "runs/existence_oracle_timing.json; excluded "
                              "here so that this record is byte-stable across "
                              "runs and can be pinned in REPRODUCE.md",
        "boundary": "Deterministic protocol conformance only. The timing "
                    "observation is reported and is not part of the verdict. "
                    "Absence assertions served by this endpoint are "
                    "fork-conditional in the sense of Section 6.4.3.",
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(
        json.dumps(out, indent=2, sort_keys=True) + "\n")
    timing_out = dict(timing)
    timing_out["invocation"] = invocation
    timing_out["environment"] = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    timing_out["environment_note"] = (
        "This record is environment-dependent by design and is NOT pinned in "
        "REPRODUCE.md. The deterministic record is.")
    timing_out["run_of"] = os.path.basename(a.out)
    io.open(os.path.join(os.path.dirname(a.out),
                         "existence_oracle_timing.json"), "w",
            encoding="utf-8", newline="\n").write(
        json.dumps(timing_out, indent=2, sort_keys=True) + "\n")

    w = sys.stdout.write
    w("ARP existence-oracle class v0.1 -- %s\n" % out["evidence_status"])
    w("fixture   %s\n" % out["fixture_sha256"])
    w("reference %s\n\n" % out["reference_sha256"])
    for r in rows:
        if r["verdict"] == "NOT-DECIDABLE-FROM-WIRE":
            mark = "gap "
        elif r["verdict"] != r["expected"]:
            mark = "FAIL"
        elif r.get("control_exercised") is False:
            mark = "gap "
        else:
            mark = "ok  "
        w("  %s %-18s %-24s expected %-7s got %s\n"
          % (mark, r["vector"], r["endpoint"], r["expected"], r["verdict"]))
        if r.get("control_exercised") is False:
            if r.get("designed_discriminator") is None:
                w("        ! no wire-observable discriminator exists for this "
                  "row; carried as a declared gap\n")
            else:
                w("        ! designed discriminator %s did not fire; "
                  "fired instead: %s\n"
                  % (r["designed_discriminator"],
                     ", ".join(r["discriminators_fired"]) or "none"))
        for f in r["findings"]:
            w("        - %s\n" % f)
    w("\ntiming (reported, not adjudicated): median present %.6fs, "
      "absent %.6fs, standardised difference %.4f over %d samples/arm\n"
      % (timing["median_present_s"], timing["median_absent_s"],
         timing["standardised_median_difference"], timing["samples_per_arm"]))
    w("\ncontrols exercised     %d of %d  (%s)\n"
      % (len(exercised_ids), len(exercised_ids) + len(unexercised),
         ", ".join(exercised_ids) or "none"))
    if unexercised:
        w("controls NOT exercised %d        (%s)\n"
          % (len(unexercised), ", ".join(unexercised)))
    if method_limits:
        w("method limits          %d        (%s -- no discriminator exists; "
          "not counted as controls)\n"
          % (len(method_limits), ", ".join(method_limits)))
    if STANDING_EVIDENCE_GAPS:
        w("standing evidence gaps %d        (%s)\n"
          % (len(STANDING_EVIDENCE_GAPS),
             ", ".join(sorted(STANDING_EVIDENCE_GAPS))))
    w("\nDETERMINISTIC RESULT: %s\n" % out["deterministic_result"])
    if not failed and not unexercised and (method_limits
                                           or STANDING_EVIDENCE_GAPS):
        w("  No row failed and every negative control fired its own designed\n"
          "  discriminator. The result is not PASS because the method limits\n"
          "  and standing evidence gaps above still stand, and they are\n"
          "  properties of the method that no run of this class can close.\n"
          "  Exit status is 0; a disclosed gap is not a failure.\n")
    if unexercised and not failed:
        w("  No row failed. The channels above were never exercised, so this "
          "run is not\n  a complete pass and does not claim to be. Exit "
          "status is 0; the gaps are in\n  controls_not_exercised and in "
          "declared_coverage_gaps.\n")
    w("written %s\n" % a.out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
