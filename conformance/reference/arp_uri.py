#!/usr/bin/env python3
"""RFC 3986 Sections 6.2.2 and 6.2.3 normalisation of a request target.

Section 6.4.1 of draft-hillier-scitt-arp requires the request-binding digest to
commit to a NORMALISED target rather than to the bytes a client happened to
send, so that two clients addressing one resource compute one binding. The
earlier implementation lowercased the scheme and host and dropped a default
port, and did none of the rest -- no dot-segment removal, no percent-encoding
normalisation, and it discarded userinfo silently. Two clients could therefore
address the same resource, normalise differently, compute different bindings,
and neither would be told why. Found in red team on 2026-08-18.

What is implemented, by section:

  6.2.2.1  Case Normalization
             scheme and host lowercased; the hexadecimal digits of every
             percent-encoded octet uppercased.
  6.2.2.2  Percent-Encoding Normalization
             percent-encoded octets that stand for unreserved characters
             -- ALPHA / DIGIT / "-" / "." / "_" / "~" -- are decoded. Every
             other percent-encoded octet is left encoded. %2F is NOT decoded:
             a decoded slash would change the path's segment structure, which
             is a different resource.
  6.2.2.3  Path Segment Normalization
             remove_dot_segments of Section 5.2.4.
  6.2.3    Scheme-Based Normalization
             a default port for the scheme is dropped; an empty path becomes
             "/".

Userinfo is PRESERVED rather than dropped. Discarding it makes two distinct
targets normalise to one binding, which is the failure this function exists to
prevent. A deployment that wishes to refuse userinfo should refuse the request,
not silently rewrite it.

The fragment is excluded, because a fragment is not sent on the wire and so is
not part of what the parties can agree about.

Standard library only.
"""

from urllib.parse import urlsplit

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_DEFAULT_PORT = {"http": 80, "https": 443}


def _pct(s):
    """6.2.2.1 and 6.2.2.2 over one component."""
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c == "%" and i + 2 < n + 1 and len(s[i + 1:i + 3]) == 2:
            hexpair = s[i + 1:i + 3]
            try:
                val = int(hexpair, 16)
            except ValueError:
                out.append(c)
                i += 1
                continue
            ch = chr(val)
            if ch in _UNRESERVED:
                out.append(ch)                       # 6.2.2.2 decode
            else:
                out.append("%" + hexpair.upper())    # 6.2.2.1 uppercase
            i += 3
            continue
        out.append(c)
        i += 1
    return "".join(out)


def remove_dot_segments(path):
    """RFC 3986 Section 5.2.4, written out rather than approximated."""
    inp, out = path, []
    while inp:
        if inp.startswith("../"):
            inp = inp[3:]
        elif inp.startswith("./"):
            inp = inp[2:]
        elif inp.startswith("/./"):
            inp = "/" + inp[3:]
        elif inp == "/.":
            inp = "/"
        elif inp.startswith("/../"):
            inp = "/" + inp[4:]
            if out:
                out.pop()
        elif inp == "/..":
            inp = "/"
            if out:
                out.pop()
        elif inp in (".", ".."):
            inp = ""
        else:
            j = inp.find("/", 1) if inp.startswith("/") else inp.find("/")
            if j == -1:
                out.append(inp)
                inp = ""
            else:
                out.append(inp[:j])
                inp = inp[j:]
    return "".join(out)


def normalise_target(target):
    u = urlsplit(target)
    scheme = u.scheme.lower()

    host = (u.hostname or "").lower()
    authority = host
    if u.port is not None and u.port != _DEFAULT_PORT.get(scheme):
        authority = "%s:%d" % (host, u.port)
    if u.username is not None:
        userinfo = _pct(u.username)
        if u.password is not None:
            userinfo += ":" + _pct(u.password)
        authority = userinfo + "@" + authority

    path = remove_dot_segments(_pct(u.path)) or "/"
    query = _pct(u.query)
    return "%s://%s%s%s" % (scheme, authority, path,
                            ("?" + query) if query else "")
