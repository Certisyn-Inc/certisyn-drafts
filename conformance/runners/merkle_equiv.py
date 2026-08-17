#!/usr/bin/env python3
"""ARP 4.9 vs Certificate Transparency: root and audit-path equivalence, and the empty-tree divergence.

ARP 4.9   : level-by-level; odd last node at a level carried up unchanged.
CT        : MTH(D[n]) = HASH(0x01 || MTH(D[0:k]) || MTH(D[k:n])), k = largest power of 2 < n.
            RFC 9162 Section 2.1.1, unchanged from RFC 6962 Section 2.1.

Both: leaf node = SHA-256(0x00 || leaf), internal = SHA-256(0x01 || left || right).
Leaf ORDER is taken as given here; ARP additionally sorts and dedups before this
point, RFC 6962 does not. That is a separate, real difference.
"""
import hashlib

ZERO32 = b"\x00" * 32


def H(b):
    return hashlib.sha256(b).digest()


def leaf_hash(x):
    return H(b"\x00" + x)


def node(l, r):
    return H(b"\x01" + l + r)


# ---------- ARP 4.9 ----------
def arp_root(leaves):
    if not leaves:
        return ZERO32
    level = [leaf_hash(x) for x in leaves]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(node(level[i], level[i + 1]))
        if len(level) % 2 == 1:
            nxt.append(level[-1])          # carried up unchanged
        level = nxt
    return level[0]


def arp_path(leaves, index):
    """Sibling array from the leaf's level upward; no entry where the node was carried up."""
    level = [leaf_hash(x) for x in leaves]
    idx = index
    sibs = []
    while len(level) > 1:
        if idx == len(level) - 1 and len(level) % 2 == 1:
            pass                            # carried up: no sibling entry
        else:
            sib = level[idx ^ 1]
            sibs.append(sib)
        nxt = []
        for i in range(0, len(level) - 1, 2):
            nxt.append(node(level[i], level[i + 1]))
        if len(level) % 2 == 1:
            nxt.append(level[-1])
        idx //= 2
        level = nxt
    return sibs


# ---------- RFC 9162 2.1.1 / RFC 6962 2.1 ----------
def largest_pow2_below(n):
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def mth(leaves):
    n = len(leaves)
    if n == 0:
        return H(b"")                       # e3b0c442...
    if n == 1:
        return leaf_hash(leaves[0])
    k = largest_pow2_below(n)
    return node(mth(leaves[:k]), mth(leaves[k:]))


def audit_path(leaves, m):
    """RFC 9162 Section 2.1.3 PATH(m, D[n]), leaf-upward order."""
    n = len(leaves)
    if n == 1:
        return []
    k = largest_pow2_below(n)
    if m < k:
        return audit_path(leaves[:k], m) + [mth(leaves[k:])]
    return audit_path(leaves[k:], m - k) + [mth(leaves[:k])]


# ---------- verification ----------
def check(nmax_root, nmax_path):
    leaves_all = [b"leaf-%04d" % i for i in range(nmax_root)]

    root_mismatch = []
    for n in range(1, nmax_root + 1):
        D = leaves_all[:n]
        if arp_root(D) != mth(D):
            root_mismatch.append(n)

    pair_count = 0
    path_mismatch = []
    for n in range(1, nmax_path + 1):
        D = leaves_all[:n]
        for i in range(n):
            pair_count += 1
            if arp_path(D, i) != audit_path(D, i):
                path_mismatch.append((n, i))

    print("roots compared        : n = 1..%d" % nmax_root)
    print("root mismatches       : %s" % (root_mismatch or "none"))
    print("(n,index) pairs       : %d  (n = 1..%d)" % (pair_count, nmax_path))
    print("path mismatches       : %s" % (path_mismatch or "none"))
    print()
    print("empty tree, ARP 4.9   : %s" % arp_root([]).hex())
    print("empty tree, CT       : %s" % mth([]).hex())
    print("diverge on empty tree : %s" % (arp_root([]) != mth([])))


if __name__ == "__main__":
    check(nmax_root=1024, nmax_path=256)
