#!/usr/bin/env python3
"""Post-process the xml2rfc --v2v3 output so the filed XML is clean RFCXML v3.

  kramdown-rfc -> xml2rfc --v2v3 -> postprocess_xml.py -> xml2rfc --text

Removes processing instructions and comments, the submissionType attribute
(the datatracker assigns the stream), abstracts that kramdown-rfc copies into
reference entries, and non-ASCII characters; and marks requirement-level
keywords with the bcp14 element. Pure ASCII output.
"""
import re
import sys
from lxml import etree

SKIP = {"artwork", "sourcecode", "name", "title", "abbrev", "keyword", "bcp14",
        "tt", "seriesInfo", "organization", "street", "city", "region", "code",
        "country", "postalLine", "email", "uri", "phone", "area", "workgroup"}
KW = re.compile(r"\b(NOT\s+RECOMMENDED|MUST\s+NOT|SHALL\s+NOT|SHOULD\s+NOT|"
                r"MUST|SHALL|SHOULD|RECOMMENDED|MAY|OPTIONAL|REQUIRED)\b")
ASCII = {"ğ": "g", "—": ",", "–": "-", "‘": "'", "’": "'",
         "“": '"', "”": '"', " ": " "}


def asciify(s):
    if s is None:
        return s
    for k, v in ASCII.items():
        s = s.replace(k, v)
    return s


def wrap(el):
    """Split el.text and the tails of its children around bcp14 elements."""
    if el.tag in SKIP or not isinstance(el.tag, str):
        return
    for child in list(el):
        wrap(child)
    # text
    parts = KW.split(el.text or "")
    if len(parts) > 1:
        el.text = parts[0]
        pos = 0
        for i in range(1, len(parts), 2):
            b = etree.Element("bcp14")
            b.text = parts[i]
            b.tail = parts[i + 1]
            el.insert(pos, b)
            pos += 1
    # tails
    for child in list(el):
        if child.tag == "bcp14" or not isinstance(child.tag, str):
            continue
        parts = KW.split(child.tail or "")
        if len(parts) > 1:
            child.tail = parts[0]
            idx = el.index(child) + 1
            for i in range(1, len(parts), 2):
                b = etree.Element("bcp14")
                b.text = parts[i]
                b.tail = parts[i + 1]
                el.insert(idx, b)
                idx += 1


def main(src, dst):
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    tree = etree.parse(src, parser)
    root = tree.getroot()
    for node in list(root.iter()):
        if isinstance(node, (etree._ProcessingInstruction, etree._Comment)):
            p = node.getparent()
            if p is not None:
                if node.tail:
                    prev = node.getprevious()
                    if prev is not None:
                        prev.tail = (prev.tail or "") + node.tail
                    else:
                        p.text = (p.text or "") + node.tail
                p.remove(node)
    root.attrib.pop("submissionType", None)
    for ab in root.xpath("//reference/front/abstract"):
        ab.getparent().remove(ab)
    for el in root.iter():
        if isinstance(el.tag, str):
            el.text = asciify(el.text)
            el.tail = asciify(el.tail)
            for k, v in list(el.attrib.items()):
                el.attrib[k] = asciify(v)
    wrap(root.find("middle"))
    wrap(root.find("back"))
    wrap(root.find("front"))
    out = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
    out = out.decode("utf-8")
    bad = [c for c in out if ord(c) > 127]
    if bad:
        sys.exit("non-ASCII remains: %r" % sorted(set(bad)))
    open(dst, "w", encoding="ascii", newline="\n").write(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
