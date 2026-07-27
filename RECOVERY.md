# Recovery note — the `-01` source gap

**Status: source restored 2026-07-27; diff verification outstanding.**

## What happened

`draft-hillier-scitt-arp-01` was filed on **23 July 2026** and posted to the
datatracker on **24 July 2026 05:57 UTC**. It is live and correct:

- <https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/>
- <https://www.ietf.org/archive/id/draft-hillier-scitt-arp-01.txt>

The kramdown source that produced it was **never committed to this repository**.
As of this note the repository contains three commits, all `-00`:

```
5d506b7  Add BUILD-AND-SUBMIT.md — operational runbook for the IETF submission flow
3c37ac1  Add draft-hillier-scitt-arp.md — kramdown-rfc source for ARP -00
60c4750  Add README — IETF Internet-Draft draft-hillier-scitt-arp
```

`draft-hillier-scitt-arp.md` here still carries `docname:
draft-hillier-scitt-arp-00` and contains **no appendices at all**.

## What is missing from the repository

Everything `-01` added, per the filed table of contents:

| filed in -01 | present in this repo |
|---|---|
| §3.2 Requester Identity Binding and Agent Friend-or-Foe Gate | no |
| §4 Agentic Principal Reconciliation | no |
| §5.2 HTTP Message Signature Binding (RFC 9421, Web Bot Auth) | no |
| §6.3 Agent Impersonation and Friend-or-Foe Integrity | no |
| Appendix A.3 Agentic Principal Reconciliation | no |
| Appendix A.4 Divergent Agent-Action Reconciliation | no |
| Appendix D Composition with Agent-Action Accountability Capsules | no |
| Appendix E Document History (E.1 Since -00) | no |
| Divergence axes `agent-impersonation-suspected`, `agent-credential-absent`, `agent-principal-unverifiable`, `agent-action-scope-divergence` | no |

Note also that §3.12 in the filed `-01` is **Cryptographic-Primitive-Upgrade
Path** — the composition material landed in Appendix D, not in §3.12. Working
notes that describe "§3.12 composition" or "Appendix A.3 divergent agent-action"
predate the filing and are wrong.

## What was done

The `-01` source was reconstructed from the filed text and committed
(`draft-hillier-scitt-arp-01 — reconstruct kramdown source from the filed
text`). All sections in the filed table of contents are present, all four
`agent-*` divergence axes are present, `docname` is `-01`, `date` is
2026-07-23, and every `{{reference}}` resolves against the declared reference
sets.

**Outstanding:** the source was reconstructed, not recovered from the original
working copy. It is not authoritative until someone runs `make` and diffs the
rendered text against
`https://www.ietf.org/archive/id/draft-hillier-scitt-arp-01.txt`. Do that
before `-02` drafting begins, and record the result here. Expect cosmetic
differences in line wrapping and pagination; any *semantic* difference is a
reconstruction error and must be corrected in favour of the archive.

## How it was closed

The authoritative source is whatever was uploaded to the datatracker on 23 July.
In order of preference:

1. **The submitted `.xml` or `.md`, from the datatracker submission record** —
   <https://datatracker.ietf.org/doc/draft-hillier-scitt-arp/01/>. If an `.xml`
   was uploaded, that is the structured source and it round-trips.
2. **The local working copy** used on 23 July. Not in `certisyn-app/drafts/ietf`,
   not in `02 - Strategy and IP/Current/Standards/F39-IETF-Submission`, not in
   `.scratch`. Check `~/Downloads` and any other machine.
3. **Reconstruct from the published `.txt`** — mechanical, and verifiable: after
   reconstruction, `make` and diff the rendered output against
   `draft-hillier-scitt-arp-01.txt`. A clean diff proves the source is right.
   Do **not** accept a reconstruction that has not been diffed.

Then:

```bash
git add draft-hillier-scitt-arp.md draft-hillier-scitt-arp.xml
git commit -m "draft-hillier-scitt-arp-01 as filed 2026-07-23 (recovered)"
git tag -a draft-hillier-scitt-arp-01 -m "Filed 2026-07-23"
git tag -a draft-hillier-scitt-arp-00 3c37ac1 -m "Filed 2026-05-01"
git push origin main --tags
```

## Why it matters beyond tidiness

`-02` has committed changes pending (see `REVISION-PLAN-02.md`), several of them
normative and made publicly on the SCITT list. Drafting `-02` against the `-00`
text in this repository would silently drop every `-01` section listed above —
including four divergence axes that other implementers are already citing by
name in correspondence. **Do not begin `-02` until this note is closed.**

## Prevention

`.github/workflows/draft.yml` now builds the draft on every push and fails if it
does not compile. `Makefile` has a `check-docname` target. Neither would have
caught this specific failure — a revision filed from outside the repo — so the
real control is the post-submission checklist in `BUILD-AND-SUBMIT.md` §4:
commit and tag *the moment* the New Version Notification arrives.
