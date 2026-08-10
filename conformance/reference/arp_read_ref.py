#!/usr/bin/env python3
"""Reference implementation of the ARP Output and Ledger Read Binding.

Scope: draft-hillier-scitt-arp-03 Section 6.4, enough of it to make the
existence-oracle property executable rather than asserted. It is a conformance
fixture, not a product: one process, in-memory state, no persistence, no TLS.

Why it exists. Songbo Bu's review of 2026-08-10 recorded the existence-oracle
vector class as not-run, because the review material identified proposed
protocol text and a conformance archive but no runnable endpoint with server
state, two authenticated principals, signing keys and an entitlement fixture.
That is the correct disposition for a vector that has not been executed, and it
is a coordinate problem rather than a design one, so the coordinates are here.

What is implemented, and why each is load-bearing:

  * Deterministic CBOR to the Core Deterministic Encoding Requirements of
    RFC 8949 Section 4.2.1 -- the requirement ARP-03 cites for every digest and
    every signed payload. Written out rather than imported so that the encoder
    under test is the one the specification names.
  * COSE_Sign1 over Ed25519 for every response, including every 4xx. A server
    that signed only successes could suppress a channel by answering 404
    forever and the suppressed party would hold an unsigned status line.
  * RFC 9421-shaped request signatures over @method, @target-uri, nonce and
    keyid, which is the tuple the response's request-binding digest covers.
  * The rate-limit counter charged BEFORE entitlement is evaluated, so an
    unentitled request and a nonexistent one consume the same budget.
  * One code path for both 404 arms, so the work done does not depend on
    whether the resource exists.
  * Cache-Control: no-store on both arms.

Deliberate defects, selected with --defect, exist so the vector class can be
shown to refuse something. A suite that has never rejected an implementation
cannot be distinguished from a suite that cannot. Each flag reintroduces
exactly one channel and nothing else:

  status-oracle     403 for unentitled, 404 for absent
  body-oracle       an error discriminator in the signed payload
  header-oracle     an extra HTTP header on the unentitled arm only
  cache-oracle      Cache-Control differs between the two arms
  ratelimit-oracle  entitlement evaluated before the counter is charged
  path-oracle       the absent arm short-circuits the entitlement-equivalent work
  always-404        every read refused, including the entitled one
  bad-signature     responses sealed with a key the fixture does not publish

Usage:
    python3 arp_read_ref.py --fixture fixture-eo-v0.1.json --port 8471
    python3 arp_read_ref.py --fixture fixture-eo-v0.1.json --defect body-oracle
"""

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------- CBOR
# RFC 8949 Section 4.2.1, Core Deterministic Encoding Requirements:
# shortest-form argument encoding, definite lengths, and map keys sorted in
# bytewise lexicographic order of their encoded forms. ARP-03 cites 4.2.1 for
# every digest preimage and every signed payload; Section 9 of RFC 9052 does
# not state a map-key ordering rule and does not reach non-COSE structures,
# which is why the citation was retargeted.


def _head(major, arg):
    if arg < 24:
        return bytes([major << 5 | arg])
    for n, tag in ((1, 24), (2, 25), (4, 26), (8, 27)):
        if arg < (1 << (8 * n)):
            return bytes([major << 5 | tag]) + arg.to_bytes(n, "big")
    raise ValueError("argument too large")


def cbor(v):
    if v is None:
        return b"\xf6"
    if v is True:
        return b"\xf5"
    if v is False:
        return b"\xf4"
    if isinstance(v, int):
        return _head(0, v) if v >= 0 else _head(1, -v - 1)
    if isinstance(v, bytes):
        return _head(2, len(v)) + v
    if isinstance(v, str):
        b = v.encode("utf-8")
        return _head(3, len(b)) + b
    if isinstance(v, (list, tuple)):
        return _head(4, len(v)) + b"".join(cbor(x) for x in v)
    if isinstance(v, dict):
        items = sorted(((cbor(k), cbor(val)) for k, val in v.items()),
                       key=lambda kv: kv[0])
        return _head(5, len(items)) + b"".join(k + val for k, val in items)
    raise TypeError("no deterministic encoding for %r" % type(v))


# ---------------------------------------------------------------- COSE_Sign1
# Tag 18, protected {1: -8} (EdDSA), Sig_structure per RFC 9052 Section 4.4 --
# which is what RFC 9052 does govern, and is cited here for that and only that.

def cose_sign1(payload: bytes, sk: Ed25519PrivateKey, kid: bytes) -> bytes:
    protected = cbor({1: -8})
    sig = sk.sign(cbor(["Signature1", protected, b"", payload]))
    return b"\xd2" + cbor([protected, {4: kid}, payload, sig])


# ---------------------------------------------------------------- signatures

def sig_base(method: str, target: str, nonce: str, keyid: str) -> bytes:
    """The RFC 9421 signature base ARP-03 Section 6.4.1 profiles.

    Covered components are @method, @target-uri, nonce and keyid, which is
    exactly the tuple the response's request-binding digest commits to, so a
    response cannot be lifted onto a different request.
    """
    return ("\n".join([
        '"@method": %s' % method,
        '"@target-uri": %s' % target,
        '"nonce": %s' % nonce,
        '"keyid": %s' % keyid,
    ])).encode("utf-8")


def request_binding(method: str, target: str, nonce: str, keyid: str) -> bytes:
    """SHA-256 over the deterministic CBOR array of the four covered values.

    The target is normalised before digesting rather than echoed as sent, per
    Sections 6.2.2 and 6.2.3 of RFC 3986, so there is nothing for a client and
    a server to disagree about.
    """
    return hashlib.sha256(cbor([method, normalise_target(target),
                                nonce, keyid])).digest()


def normalise_target(target: str) -> str:
    u = urlsplit(target)
    scheme = u.scheme.lower()
    host = u.hostname.lower() if u.hostname else ""
    port = u.port
    if port is not None and not ((scheme == "http" and port == 80) or
                                 (scheme == "https" and port == 443)):
        host = "%s:%d" % (host, port)
    path = u.path or "/"
    return "%s://%s%s%s" % (scheme, host, path,
                            ("?" + u.query) if u.query else "")


# -------------------------------------------------------------------- server

class State(object):
    def __init__(self, fx, defect=None):
        self.defect = defect
        self.seal_sk = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(fx["sealing_key_seed"]))
        self.seal_kid = fx["sealing_kid"].encode()
        # A key the fixture does not publish, so a verifier that checks
        # signatures refuses and one that checks only length does not.
        self.wrong_sk = Ed25519PrivateKey.from_private_bytes(b"\xff" * 32)
        self.principals = {
            p["keyid"]: Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(p["public_key"]))
            for p in fx["principals"]}
        self.resources = {r["id"]: set(r["audience_set"])
                          for r in fx["resources"]}
        self.absent_ids = set(fx["absent_ids"])
        self.limit = int(fx["rate_limit_per_window"])
        self.window = float(fx["rate_limit_window_seconds"])
        self.head_seq = int(fx["head"]["sequence_number"])
        self.head_hash = bytes.fromhex(fx["head"]["self_entry_hash"])
        self.counters = {}
        self.lock = threading.Lock()
        self.seen_nonces = set()

    def charge(self, keyid):
        """Charge one unit. Returns True when the request is within budget.

        Called before entitlement is evaluated, so that an unentitled read and
        a nonexistent one consume the same budget and a burst of each yields
        the same sequence of statuses.
        """
        now = time.time()
        with self.lock:
            hist = [t for t in self.counters.get(keyid, []) if now - t < self.window]
            hist.append(now)
            self.counters[keyid] = hist
            return len(hist) <= self.limit


def _equivalent_work(state, rid, keyid):
    """Work performed identically whether or not the resource exists.

    A server that looked up the Audience Set only for resources it holds would
    differ in time between the two arms, so the lookup is performed against a
    constant-shaped absent record instead of being skipped.
    """
    audience = state.resources.get(rid)
    present = audience is not None
    if audience is None:
        audience = frozenset()
    entitled = keyid in audience
    # Constant-cost membership evidence, computed on both arms.
    probe = hashlib.sha256(cbor([rid, sorted(audience), keyid])).digest()
    return present, entitled, probe


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "arp-read-ref/0.1"
    sys_version = ""

    def log_message(self, *a):
        pass

    # -- response construction ------------------------------------------
    def _emit(self, status, result, req_binding, extra_headers=None, arm=None):
        st = self.server.state
        payload = cbor([
            "arp-read-v1",
            req_binding,
            status,
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            st.head_seq,
            st.head_hash,
            result,
        ])
        sk = st.wrong_sk if st.defect == "bad-signature" else st.seal_sk
        body = cose_sign1(payload, sk, st.seal_kid)
        self.send_response(status)
        self.send_header("Content-Type", "application/arp-read-response+cose")
        self.send_header("Content-Length", str(len(body)))
        cache = "no-store"
        if st.defect == "cache-oracle" and arm == "unentitled":
            cache = "no-cache"
        self.send_header("Cache-Control", cache)
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        st = self.server.state
        target = "http://%s%s" % (self.headers.get("Host", "localhost"), self.path)

        keyid = self.headers.get("Keyid", "")
        nonce = self.headers.get("Nonce", "")
        sig_b64 = self.headers.get("Signature", "")

        # 401 is about the requester's own credential and is not signed: it
        # cannot be a statement about a resource, because no resource has been
        # resolved at this point.
        pk = st.principals.get(keyid)
        if pk is None or not nonce or not sig_b64:
            return self._plain(401, b"unauthenticated")
        try:
            pk.verify(base64.b64decode(sig_b64),
                      sig_base("GET", normalise_target(target), nonce, keyid))
        except Exception:
            return self._plain(401, b"bad signature")
        with st.lock:
            if nonce in st.seen_nonces:
                return self._plain(401, b"nonce replay")
            st.seen_nonces.add(nonce)

        rb = request_binding("GET", target, nonce, keyid)

        if not self.path.startswith("/arp/outputs/"):
            return self._emit(404, [], rb)
        rid = self.path[len("/arp/outputs/"):]

        # --- the ordering that closes the budget channel -------------------
        if st.defect == "ratelimit-oracle":
            present, entitled, _ = _equivalent_work(st, rid, keyid)
            if not (present and entitled):
                return self._emit(404, [], rb)
            if not st.charge(keyid):
                return self._emit(429, [], rb)
        else:
            if not st.charge(keyid):
                return self._emit(429, [], rb)
            if st.defect == "path-oracle":
                if rid not in st.resources:
                    return self._emit(404, [], rb)   # short-circuited
                present, entitled, _ = _equivalent_work(st, rid, keyid)
            else:
                present, entitled, _ = _equivalent_work(st, rid, keyid)

        if st.defect == "always-404":
            return self._emit(404, [], rb)

        if present and entitled:
            return self._emit(200, [rid, "sealed-output-placeholder"], rb)

        # --- the two refused arms, one path --------------------------------
        if st.defect == "status-oracle" and present:
            return self._emit(403, [], rb)
        if st.defect == "body-oracle":
            return self._emit(404, ["unentitled" if present else "absent"], rb)
        if st.defect == "header-oracle" and present:
            return self._emit(404, [], rb, {"X-Arp-Reason": "entitlement"},
                              arm="unentitled")
        return self._emit(404, [], rb,
                          arm="unentitled" if present else "absent")

    def _plain(self, status, msg):
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(msg)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(msg)


def serve(fixture_path, port, defect=None):
    fx = json.load(io.open(fixture_path, encoding="utf-8"))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    httpd.state = State(fx, defect)
    return httpd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default=os.path.join(HERE, "fixture-eo-v0.1.json"))
    ap.add_argument("--port", type=int, default=8471)
    ap.add_argument("--defect", default=None)
    a = ap.parse_args()
    httpd = serve(a.fixture, a.port, a.defect)
    sys.stderr.write("arp-read-ref on 127.0.0.1:%d defect=%s\n"
                     % (a.port, a.defect or "none"))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
