#!/usr/bin/env python3
"""Typed, language-neutral encoding of the deterministic-encoding vector inputs.

v0.1 of this class carried each input as a Python `repr` string and called
`eval()` on it. Two things were wrong with that. A vector file is an artefact
an IETF reviewer is invited to fetch and run, and `eval` on its contents is
arbitrary code execution -- `{"__builtins__": {}}` is not a sandbox and a
proof-of-concept escaped it. And a Python `repr` cannot be consumed by an
implementer working in any other language, which is disqualifying for a file
offered as conformance evidence.

Inputs are now typed JSON:

    {"t": "uint",  "v": 24}
    {"t": "nint",  "v": -1}
    {"t": "bstr",  "v": "0102"}          hex, lowercase, no prefix
    {"t": "tstr",  "v": "IETF"}
    {"t": "array", "v": [ <item>, ... ]}
    {"t": "map",   "v": [[ <key>, <value> ], ... ]}
    {"t": "bool",  "v": true}
    {"t": "null"}

Map entries are written in the order the AUTHOR chose, which is deliberately
NOT the order Section 4.2.1 requires: a vector file that pre-sorted its own
maps would be handing the encoder the answer.

This module imports nothing outside the standard library.
"""


def parse(node):
    """Typed JSON -> the Python value the encoder under test is handed."""
    t = node["t"]
    if t == "null":
        return None
    if t == "bool":
        return bool(node["v"])
    if t in ("uint", "nint"):
        return int(node["v"])
    if t == "bstr":
        return bytes.fromhex(node["v"])
    if t == "tstr":
        return node["v"]
    if t == "array":
        return [parse(x) for x in node["v"]]
    if t == "map":
        return {_hashable(parse(k)): parse(v) for k, v in node["v"]}
    raise ValueError("unknown input type %r" % t)


def emit(value):
    """Python value -> typed JSON. Used by the builder; round-tripped there."""
    if value is None:
        return {"t": "null"}
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    if isinstance(value, int):
        return {"t": "uint" if value >= 0 else "nint", "v": value}
    if isinstance(value, bytes):
        return {"t": "bstr", "v": value.hex()}
    if isinstance(value, str):
        return {"t": "tstr", "v": value}
    if isinstance(value, (list, tuple)):
        return {"t": "array", "v": [emit(x) for x in value]}
    if isinstance(value, dict):
        return {"t": "map", "v": [[emit(k), emit(v)] for k, v in value.items()]}
    raise TypeError("no typed encoding for %r" % type(value))


def _hashable(v):
    return tuple(v) if isinstance(v, list) else v
