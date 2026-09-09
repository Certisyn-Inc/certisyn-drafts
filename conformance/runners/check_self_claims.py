#!/usr/bin/env python3
"""Check the document's claims about itself against the document.

Emek Can Dogru, on the SCITT list, 2026-08-20:

    "Each statement was accurate when written and false within days, always in
    the direction of claiming less than the code did, and nothing in my test
    suite compares that section against the code. So the corollary reaches
    further than either of us put it: the problem is not that our
    implementations skip the vocabulary. It is that neither of us has a check
    that would notice if they did."

He is right, and it reaches this document too. Every count in a specification
is an assertion about the specification, and this week three of the worst
defects found in ARP were exactly that: a falsifiability count that said three
in four and was one in four, an enumeration of five signature carriers where
there were six, and a sentence asserting that three sets were ordered when one
of them was not.

None of those needed a reviewer. All three are mechanically checkable against
the text that makes them. This runner checks them.

WHAT IT CHECKS

  A. Counts. Where the document states how many of something it has, count the
     things and compare.
  B. Cross-reference assertions. Where the document says "this document already
     requires X of A, B and C", check that A, B and C each carry X.

WHAT IT DOES NOT CHECK, stated so the run record is not read as wider than it is

  Claims about the world, about implementations, or about other documents.
  Claims of absence ("no construction in this document commits X"), which need
  a search over a space the runner cannot enumerate.
  Whether a count that is correct is also the right count to state.

No arguments. Standard library only.
"""
import re, sys, os

DRAFT = os.path.join(os.path.dirname(__file__), "..", "..", "draft-hillier-scitt-arp.md")

WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
WORDS.update({"twenty-one":21,"twenty-two":22,"twenty-three":23,"twenty-four":24,
              "twenty-five":25,"twenty-six":26,"twenty-seven":27,"twenty-eight":28,
              "twenty-nine":29,"thirty":30,"thirty-one":31,"thirty-two":32,
              "thirty-three":33,"thirty-four":34,"thirty-five":35})

ORDINALS = {o: i + 1 for i, o in enumerate(
    "first second third fourth fifth sixth seventh eighth ninth tenth "
    "eleventh twelfth thirteenth fourteenth fifteenth".split())}

def num(tok):
    """Cardinal or ordinal, as an integer. A count stated as an ordinal is still
    a count: "the sixth was found" asserts that there are six."""
    tok = tok.lower().strip()
    if tok.isdigit(): return int(tok)
    if tok in WORDS: return WORDS[tok]
    return ORDINALS.get(tok)

def section(text, anchor, nxt=None):
    """Body of the section carrying {#anchor}, to the next heading of same or higher level."""
    m = re.search(r'^(#{1,6})\s+.*\{#' + re.escape(anchor) + r'\}\s*$', text, re.M)
    if not m: return None
    lvl = len(m.group(1)); start = m.end()
    for h in re.finditer(r'^(#{1,6})\s+', text[start:], re.M):
        if len(h.group(1)) <= lvl:
            return text[start:start + h.start()]
    return text[start:]

CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn)); return fn
    return deco


@check("Bilateral Register Agreement declared items")
def c_bra(t):
    body = section(t, "bra-items")
    actual = len(re.findall(r'^\s*(\d+)\.\s', body, re.M))
    m = re.search(r'array has \*\*exactly ([a-z-]+)\n?elements?', t)
    if not m:
        m = re.search(r'array has \*\*exactly ([a-z-]+)', t)
    stated = num(m.group(1)) if m else None
    return stated, actual, "numbered items in {#bra-items} vs the count asserted at {#bra-hash}"


@check("Well-Known URI registrations")
def c_wk(t):
    body = section(t, "iana-wellknown")
    rows = [r for r in re.findall(r'^\| `arp-[a-z-]+` \|', body, re.M)]
    m = re.search(r'^([A-Za-z-]+) entries are requested in the Well-Known', body, re.M)
    stated = num(m.group(1)) if m else None
    return stated, len(rows), "rows in the registry table vs the count in its lead sentence"


@check("Verdict Arithmetic operators")
def c_ops(t):
    body = section(t, "verdict-arithmetic")
    defs = re.findall(r'^([a-z-]+):\n:', body, re.M)
    m = re.search(r'Subject to those rules, the\s*\n?initial ([a-z]+) are', body)
    stated = num(m.group(1)) if m else None
    return stated, len(defs), "operator definition entries vs the count in 'the initial N are'"


@check("Server-recorded Divergence Axes with a stated member form")
def c_axes(t):
    m = re.search(r'the rule is stated for all ([a-z]+) axes and not ([a-z]+)', t)
    if not m: return None, None, "no 'all N axes' sentence found"
    stated = num(m.group(1))
    # The server-recorded subset is enumerated explicitly; that is the set the
    # member-form rule governs, not every axis in the registry.
    sm = re.search(r'registry marks as such and which initially are ((?:.|\n)*?)\.', t)
    if not sm: return stated, None, "server-recorded subset enumeration not found"
    listed = re.split(r',\s*|\s+and\s+', re.sub(r'\s+', ' ', sm.group(1)).strip())
    listed = [x for x in listed if re.fullmatch(r'[a-z]+(?:-[a-z]+)+', x)]
    return stated, len(listed), ("server-recorded axes enumerated in {#terminology} ("
                                 + ", ".join(listed) + ") vs 'all N axes'")


@check("Retroactive evaluation triggers")
def c_trig(t):
    body = section(t, "sweep-statements")
    m = re.search(r'initially one of\s*\n?\s*((?:`[a-z-]+`(?:,|\s|and|or|\n)*)+)', body)
    in_text = set(re.findall(r'`([a-z-]+)`', m.group(1))) if m else set()
    reg = re.search(r'A registry of ARP Retroactive[^.]*?initially containing ((?:.|\n)*?), defined in', t)
    if not reg:
        reg = re.search(r'initially containing (`pattern-library`(?:.|\n)*?), defined in', t)
    in_reg = set(re.findall(r'`([a-z-]+)`', reg.group(1))) if reg else set()
    return (len(in_reg) if in_reg else None, len(in_text) if in_text else None,
            "triggers enumerated in {#sweep-statements} vs the IANA registry's initial contents")


@check("Signature carriers named in Signature Malleability")
def c_carriers(t):
    body = section(t, "signature-malleability")
    m = re.search(r'one\. Those are ((?:.|\n)*?)\.\n\n', body)
    if not m: return None, None, "no 'Those are ...' enumeration found"
    named = len(re.findall(r'\{\{[a-z-]+\}\}', m.group(1)))
    m2 = re.search(r'The ([a-z]+) was found after the first ([a-z]+) had been\s*\n?repaired', body)
    if not m2: return None, named, "ordinal sentence not found"
    return num(m2.group(1)), named, "carriers in the 'Those are' list vs the ordinal below it"


@check("Verification Outcomes")
def c_outcomes(t):
    body = section(t, "verification-outcomes")
    defs = re.findall(r'^`([a-z-]+)`:\n:', body, re.M)
    m = re.search(r'and ([a-z]+) conditions that arrive at "refuse"', body)
    stated = num(m.group(1)) if m else None
    return stated, len(defs), "outcome definitions vs the count in the lead paragraph"


@check("Representation classes")
def c_repr(t):
    body = section(t, "representation-invariance")
    if body is None: return None, None, "section not found"
    bullets = re.findall(r'^- \*\*[A-Z]', body, re.M)
    stated = None
    for pat in (r'is one defect in ([a-z]+) forms',
                r'one defect wearing ([a-z]+) costumes',
                r'names the ([a-z]+)\s*\n?representation classes',
                r'The ([a-z]+) named classes'):
        m = re.search(pat, t)
        if m:
            stated = num(m.group(1)); break
    return stated, len(bullets), "representation-class bullets vs the stated count of forms"


@check("'this document already requires that ordering of' names sets that are ordered")
def c_ordering(t):
    """The assertion names three specific collections. Check each NAMED
    COLLECTION carries a sort rule, not merely that its section mentions one
    somewhere.

    The weaker form of this check survived its own mutant: every section named
    contains some bytewise sort, so a check asking only "does this section sort
    anything" passes even when the collection actually named is unordered --
    which is precisely the defect the assertion had when it was written. A check
    that cannot fail on the defect it was written for is not a check.
    """
    m = re.search(r'document already requires that ordering of ((?:.|\n)*?),\s*and\s+for the same reason', t)
    if not m: return None, None, "assertion sentence not found"
    clause = re.sub(r'\s+', ' ', m.group(1)).strip()
    items = re.split(r',\s*of\s+|\s+and\s+of\s+', clause)
    SORT = 'sorted in bytewise lexicographic order'
    missing = []
    for it in items:
        it = it.strip()
        ref = re.search(r'\{\{([a-z-]+)\}\}', it)
        phrase = re.sub(r'\s*of\s*\{\{[a-z-]+\}\}\s*$', '', it).strip()
        phrase = re.sub(r'^the\s+', '', phrase)
        body = section(t, ref.group(1)) if ref else t
        if body is None:
            missing.append(phrase + " (section not found)"); continue
        flat = re.sub(r'\s+', ' ', body)
        # the head noun of the named collection must itself be sorted
        # A collection named "the algorithm array" may be written in its own
        # section as "the array of permitted signature algorithm identifiers".
        # Anchor on the distinguishing word rather than on the whole phrase.
        words = [w for w in phrase.split() if w.lower() not in
                 ('the', 'a', 'an', 'of', 'array', 'set', 'list')]
        key = words[0] if words else phrase
        hits = [mm.start() for mm in re.finditer(re.escape(key), flat, re.I)]
        if not hits:
            missing.append(phrase + " (named collection not found in the section it cites)")
            continue
        # Proximity is not enough: an enumerated payload puts several
        # collections in one sentence, and a sort rule belonging to the next
        # one sits well inside any fixed window. Bound the search to the clause
        # the collection is named in -- to the next semicolon or sentence end.
        def clause(h):
            stops = [flat.find(';', h), flat.find('. ', h)]
            stops = [x for x in stops if x != -1]
            return flat[h:min(stops)] if stops else flat[h:]
        if not any(SORT in clause(h) for h in hits):
            missing.append(phrase)
    return (0, len(missing),
            "named collections asserted to be ordered that are not: "
            + (", ".join(missing) if missing else "none"))


@check("Policy Parameters Document elements")
def c_ppd(t):
    m = re.search(r'whose payload is\s*\n?\s*the ([a-z-]+)-element CBOR array of: ((?:.|\n)*?)\n\n', t)
    if not m: return None, None, "payload description not found"
    stated = num(m.group(1))
    body = re.sub(r'\s+', ' ', m.group(2))
    # elements are separated by "; " at the top level of the sentence
    parts = [p for p in re.split(r';\s+(?:and\s+)?', body) if p.strip()]
    return stated, len(parts), "semicolon-separated payload elements vs the stated arity"


def main():
    t = open(DRAFT, encoding="utf-8").read()
    bad = 0
    print("=" * 78)
    print("SELF-CLAIM CHECK  --  the document's claims about itself, against itself")
    print("=" * 78)
    for name, fn in CHECKS:
        try:
            stated, actual, how = fn(t)
        except Exception as e:
            print(f"  ERROR    {name}: {e.__class__.__name__}: {e}")
            bad += 1
            continue
        if stated is None or actual is None:
            print(f"  SKIP     {name}")
            print(f"           {how}")
            continue
        ok = (stated == actual)
        if not ok: bad += 1
        print(f"  {'ok  ' if ok else 'FAIL'}     {name}: stated {stated}, found {actual}")
        print(f"           {how}")
    print("-" * 78)
    print(f"{len(CHECKS)} checks, {bad} failing")
    print()
    print("Does not establish: any claim about the world, about an implementation,")
    print("or about another document; any claim of absence; whether a correct count")
    print("is the right count to state.")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
