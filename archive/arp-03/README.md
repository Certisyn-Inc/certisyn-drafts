# Superseded, kept as evidence

Everything in this folder relates to `draft-hillier-scitt-arp-03`, which posted on
2026-08-14 at 04:24:24 UTC. It is kept because reviewers reproduced against some
of it, not because it is current.

**Current working document: `../../ARP-04.md`. Read that instead.**

## The three texts, so none of them can be mistaken for another

| file | sha256 | bytes | what it is |
|---|---|---|---|
| `../../draft-hillier-scitt-arp-03.FILED.txt` | `fe7ba656ef07842c365ce93938610cd874668c29f0fa06031d37d0e4e72b395d` | 339,537 | **The filed text.** Byte-identical to what the IETF archive serves. |
| `draft-hillier-scitt-arp-03.CIRCULATED-FOR-COMMENT.txt` | `8fab5b82a67f56e0735a859ecfa0a7bb78ccb44fb85a9d87a6efea3342f07c27` | 336,811 | Circulated for comment on 2026-08-11. Songbo Bu and Walter Hawkins reproduced against these bytes. Not what was filed. |
| `SUPERSEDED-build-715513d4.txt` | `715513d49b10d0e8ad1379db28a073b24cccb295153a210b3b8abe1f9fe6ac28` | 326,196 | An earlier build. Never circulated, never filed. Kept only so the digest is accounted for. |

The circulated file was tracked in this public repository as `_rt.txt`, a name that
said nothing about which revision it held. Renaming it is the point of this folder:
a file whose name does not state what it is will eventually be used as though it
were something else.

The delta from circulated to filed is four changes and nothing else. Section 6.4.3
gains an observer-independence bound and one new SHOULD, the Acknowledgments gain
Walter Hawkins and Tiago Pinto, Appendix E.1 records the change, and the date moves
from 8 to 13 August. No other normative statement in the document is added, removed
or altered. `ARP-04.md` section 1 carries the digests.

## Working notes

The `.md` files here were the `-03` working record: blockers, handoffs, the
continuation review, the filing status, the rebuttal to the `-02` review, the
adoption plan, the revision note and the for-comment document. `ARP-04.md`
supersedes all of them. Nothing in this folder is maintained.