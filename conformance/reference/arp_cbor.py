#!/usr/bin/env python3
"""Deterministic CBOR to RFC 8949 Section 4.2.1, and nothing else.

Split out of arp_read_ref.py on 2026-08-18 so that a runner testing the
encoder does not have to import an HTTP server and, through it, the
`cryptography` package. The deterministic-encoding class claimed to have no
third-party dependency while importing a module whose first act is
`from cryptography.hazmat...`; blocking that package produced a bare traceback
rather than the instruction standing rule 4 requires.

This module imports nothing outside the standard library and nothing at all.

Core Deterministic Encoding Requirements, Section 4.2.1:
  * arguments in the shortest form that holds them
  * definite lengths only, for every container and every string
  * map keys sorted in bytewise lexicographic order OF THEIR ENCODED FORMS

The third is the one implementations get wrong, because Section 4.2.3 defines
a length-first ordering that is also well-formed CBOR and was the canonical
rule of RFC 7049. Both encode the same map to different bytes and neither
raises. ARP cites 4.2.1 for every digest preimage and every signed payload.
"""


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
