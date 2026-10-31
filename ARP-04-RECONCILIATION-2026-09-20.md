# ARP-04 reconciliation

20 September 2026. Second pass, red-teamed against primary sources: the filed
`-04` text and its build artefacts, the `-03` filed text, the two 7 September
review diffs and the 7 September post-image, the standards register, the git
history, the datatracker submission API, the IETF mail archive, and the
mailbox. Every claim below names where it was checked. Four findings in the
first pass were wrong or incomplete and are corrected here; each correction is
marked.

---

# PART 0. WHERE ARP-04 ACTUALLY STANDS

**It is filed.** Posted **8 September 2026 at 21:14:50 UTC**, 213 pages, per
the datatracker notification: "successfully submitted by Joel David Hillier and
posted to the IETF repository."

Independently confirmed against the datatracker submission API today:

| Rev | State | Submitted | Bytes |
|---|---|---|---|
| 00 | posted | 2026-05-01 | 36,067 |
| 01 | posted | 2026-07-23 | 59,593 |
| 02 | **cancel** | 2026-08-08 | 83,438 |
| 02 | posted | 2026-08-08 | 83,465 |
| 03 | posted | 2026-08-13 | 339,537 |
| **04** | **posted** | **2026-09-08** | **591,005** |

So "closing out ARP-04" is not finishing a plan and filing. The freeze line was
crossed twelve days ago. What remains is post-filing work, and one item of it
is a substantive defect rather than housekeeping.

`ARP-04-STATUS-2026-09-05.md` in the repository describes the **pre-filing**
state. It is a careful note and it is stale. Do not work from it as current.

---

# PART 1. THE ONE FINDING THAT MATTERS: A9 DID NOT LAND, AND IT WAS PROMISED

**This reverses the first pass**, which said the question could not be called
from a keyword search. It can be called, and the answer is not the comfortable
one.

## What was promised, and to whom

On **7 September 2026 at 05:16:57 UTC** you wrote to Nenad Vasic, in the
present tense, under the heading "ARP-04, YOUR ITEM 2":

> "Your digest-suite point is settled and it is going in as a verifier
> obligation rather than as a Divergence Axis... So it lands in the
> Cryptographic-Primitive-Upgrade Path instead, beside the rule that already
> says a verifier recomputing a Prior-Entry Hash across a rotation boundary
> must not re-encode the protected header. Yours is the same argument one step
> further out. **The text says** the Prior-Entry Hash is a digest under the
> suite the preceding entry's protected header names, that a verifier must
> recompute it under that suite and must not recompute it under any other
> including one adopted later, and that an implementation must refuse an entry
> whose Prior-Entry Hash verifies only under a re-digest. There is a new
> non-answer reason for it... **It's attributed to you in the ARP-04 document
> history.**"

He replied at **06:04:11 UTC the same day** and agreed, on your reasoning
rather than his own:

> "Our own text named two dispositions and asked for one of them... You took
> the second, and the argument you give for it is better than our reason for
> offering both... No disagreement. The Cryptographic-Primitive-Upgrade Path is
> where it belongs, and beside the no-re-encode rule is the right neighbour."

## What the filed text says

Nothing of it. Checked six ways, and every check agrees.
**All six were redone with the line wrapping flattened out**, because a line-based
search misses a phrase broken across two lines, and that is the one mistake that
would make this finding wrong. It did not. Flattened, the whole 591,005-byte
document contains the word "suite" once, in "pass a test suite and diverge in
production", and every other term below has zero occurrences.

1. **The word "suite" occurs once in 591,005 bytes**, at line 2233: "pass a
   test suite and diverge in production." Nothing else. `digest suite`, `hash
   suite`, `hash agility`, `re-digest`, `redigest`, `re-hash`, `suite
   transition`, `successor`, `recompute the digest`, `historical bytes`: zero
   occurrences each.

2. **Section 5.22, the named landing site, was rewritten in `-04` for a
   different reason.** It now derives the Prior-Entry Hash from the Signing
   Input Digest and adds the no-re-encode rule. That is Anton Sokolov's
   signature-encoding finding, recorded at E.1.5. The rewrite is about the
   *signature* algorithm identifier, not about the *digest* suite, and it
   states no refusal rule for a re-digest.

3. **The no-re-encode rule you named as the neighbour is there. Nothing sits
   beside it.** "MUST NOT recompute", "under that suite", "adopted later",
   "verifies only under": zero occurrences.

4. **No new non-answer reason for it.** *Corrected on the second read.* The
   Section 5.11 list gains **five** reasons over `-03`, not one:
   `attestation-echo-mismatch`, `attestation-signature-invalid`,
   `attestation-binding-mismatch`, `attestation-scope-exceeded` and
   `attestation-source-version-invalid`, and it loses `attestation-unverifiable`.
   Eleven become fifteen. **None of the five concerns a re-digest.** The first pass
   said one reason and was wrong on the count while right on the point.

5. **Not in the document history.** E.1 is an exhaustive change list and names
   its three new Divergence Axis values explicitly: `register-threshold-
   divergence`, `declared-not-determined`, `source-version-skew`. Nenad is
   credited in E.1.4 and in the Acknowledgments, for the inclusion-proof
   lifted-leaf finding, which is a different item of his.

6. **It was never written.** The two 7 September review diffs in `_audit`
   (`arp04-hardening.diff`, `arp04-hardening-1.diff`, both timestamped after
   the message to Nenad) and the 7 September post-image
   (`draft-postimage-for-review.md`) contain zero occurrences of the same
   vocabulary. The text was described to him before it existed, and it did not
   come into existence in the thirty-nine hours before filing.

## What this is

It is the same shape as the Walter Hawkins error a fortnight ago: something
promised in writing to a named person, then absent from the shipped bytes.
This one is worse in two respects. It is normative specification text rather
than a credit line, and the person it was promised to agreed on the strength of
the description and has no reason to go looking.

## One thing that helps

**There is already a discriminating conformance vector pair on record for
exactly this property**, from Songbo Bu, at Row 11 of the interop report, in
his own words of 26 August: "p20 keeps the retained prefix bound under the
digest suite in force when it was written, while n29 supplies the
successor-suite digest of the same canonical prefix and must reject." So the
rule ARP does not state is already tested by a named contributor who is also an
ARP Acknowledgments name. If A9 lands in `-05`, it lands with a test.

## A10, by contrast, landed

Emek Can Doğru's two-clock question, the other item holding the freeze, is in.
Section 7.4.3 bounds both clocks, the reference instant is the reader's
receipt, the direction is backward, the forward bound is sixty seconds, and
item 26 of Section 5.23.1 states that the declared tolerance is the backward
bound only. It is recorded at E.1.11. **Of the two decisions that held the
freeze, one landed and one was described as landed.**

---

# PART 2. THE WORKING DOCUMENTS ARE GONE, AND I DID NOT RECONSTRUCT THEM

`ARP-04-STATUS-2026-09-05.md` cites `ARP-04.md` at 131,349 B and
`ARP-04-PLAN.md` at 34,268 B, both in `certisyn-app/scitt-arp-f39`. **Neither
is in any connected folder**, and that path does not exist; the workspace
README records the ARP build repository consolidated into
`ietf-drafts/draft-hillier-scitt-arp/` on 10 September.

What survives is one copy of `ARP-04.md`, **26,586 bytes, 16 August**, in
OneDrive at `Certisyn Internal/02 - Strategy and IP/Current/Standards/
IETF-Drafts/`. It contains no sections 2.8 or 2.9 and no A-numbered plan.

The git history does not help either: the whole `-04` source arrived as one
commit, `57127ce8`, at 8 September 18:50 MDT, after the filing.

**The A1 to A12 items and the Stage A to Stage E structure exist for me only as
the status note's summary of a file I cannot read, and I have not rebuilt them
from it.** Everything in Part 1 above is checked against the filed text, the
diffs, the repository and the mailbox instead, which is why A9 could be settled
without it.

---

# PART 3. WHO IS CREDITED, CHECKED LINE BY LINE

## Acknowledgments, Section 11: nine people, ten paragraphs

Read against Section 10 of `draft-hillier-scitt-arp-03.FILED.txt`, not against
any note.

| # | Person | Change from `-03` |
|---|---|---|
| 1 | Songbo Bu | carried unchanged |
| 2 | Steven Mih | carried unchanged |
| 3 | Iman Schrock | carried, **and gains a second paragraph** |
| 4 | Walter Hawkins | carried unchanged |
| 5 | Tiago Pinto | carried unchanged |
| 6 | Tom Sato | **expanded**, now naming the RFC 6962 gap |
| 7 | **Anton Sokolov** | **new paragraph.** In `-03` he appeared only inside Iman Schrock's sentence |
| 8 | **Henri Sirkkavaara** | **new** |
| 9 | **Nenad Vasic** | **new** |

The three additions are the right three. All contributed after `-03` filed and
all three are named.

## Emek Can Doğru: two credits, and neither is in the Acknowledgments

**This corrects the first pass**, which said he was credited once.

- **Appendix E.1.11**, "The two clocks a response freshness check is decided
  across", ends: *"The question is Emek Can Dogru's."*
- **Section 5.24 material at line 6254**, an *Acknowledged.* block: *"The
  general problem, and the observation that a prohibition on averaging is not a
  mechanism, are Emek Can Doğru's, put to the SCITT mailing list on 20 August
  2026."*

So he is named twice in the body and history, for two separate contributions,
one of which produced normative change in Section 7.4.3 and item 26 of
Section 5.23.1, and he has no Acknowledgments paragraph.

**Six** people are named in E.1: Tom Sato, Walter Hawkins, Anton Sokolov,
Henri Sirkkavaara, Nenad Vasic and Emek Can Doğru. Five of the six also have
Acknowledgments paragraphs. **He is the only one who does not**, and it is the
same position Anton Sokolov held in `-03` and was given a paragraph for in `-04`.

*Corrected on the second read.* The first pass said five. The sweep was line-based
and `Walter Hawkins` is split across a line break in the `.txt`, so it was missed.
Redone with the wrapping flattened out. The substantive finding is unchanged. His
attribution in E.1.7 reads "The finding that this is bounded by observer diversity
rather than by any stronger single-log property is Walter Hawkins's, carried from
`-03`", so it is a real attribution rather than an incidental mention, and he has an
Acknowledgments paragraph.

## And his name is spelled two ways in the filed text

Line 6254 reads **Doğru**. Line 11093 reads **Dogru**. The first is the **only
non-ASCII byte in the entire 591,005-byte file**; `-03` has none. The split is
in the kramdown source too, so it is not a rendering artefact. He confirmed his
byline "with the breve at deposit" for the interop report, so the spelling he
wants is on record. One of the two is wrong and the document does not say
which.

## F12 is arguable, not an omission

F12 in the interop report is Emek's ARP finding, the manifest-digest check
missing from the archive that shipped it. It is not in the `-04`
Acknowledgments, and that is defensible: it is a defect in the conformance
archive and the runner, not in the specification text. Noted beside the item
above only because the two together are the whole of what an outside reader
could say about his treatment.

## Nobody else is missing

Every interop contributor was swept against the filed text by surname: Gruszka,
Templeman, Etcheverry, Msebenzi, Abak, Wang, Wharff, Gibson, Krausz, YuTao,
babyblueviper1. **Zero occurrences, and none should appear.** Their work is
CAP-1, Cedulon, Vaara, AIREP, CCS and the registers, not ARP.

Songbo Bu's standing rule 9 and Walter Hawkins's rule 10 live in
`conformance/README.md`, attributed there. Correct placement, not a gap.

---

# PART 4. 2.9.2 IS SETTLED, AND THE ANSWER IS THE GOOD ONE

The status note flagged a discrepancy it could not resolve: `ARP-04.md` section
2.9.2 read "BLOCKING, and now urgent" with three verified defects, while your
20 August list message stated all three repaired. Its own words: *"Either the
document is stale or the message was ahead of the text."*

**The document was stale.** Filed `-04`, from line 1943:

- **Ordering.** "The Source-Data Version Identifier Set MUST be encoded as a
  CBOR array sorted in bytewise lexicographic order of the deterministic CBOR
  encoding of each member", with the six-encodings-of-one-attestation reasoning.
- **Side channel.** A register-chosen opaque string "would be an
  arbitrary-bandwidth channel from register to relying party"; the server "MUST
  reject an identifier that is not drawn from the publisher's own state
  sequence", under reason `attestation-source-version-invalid`.
- **Carrying.** MUST be carried in the `arp-source-data-version` protected
  header and into the Per-Register Result Set, covered by both signatures.

The datatracker abstract corroborates it: `-04` "adds... a source-data version
binding that makes a change in a historical verdict attributable to a change in
policy or to a change in the underlying published corpus."

**Nothing is owed to Henri Sirkkavaara or Pablo Etcheverry on this.** The
20 August statement was accurate when made.

---

# PART 5. THE FETCH-BACK, PART DONE

**This corrects the first pass**, which said it could not be run at all.

Your standing rule, `ARP-04.md` section 1: *"The archive copy was fetched back
and hashed... Do this on every filing. It is the only check that establishes
the datatracker served what was built."*

What this session could establish:

- **The datatracker submission API records `-04` posted at 591,005 bytes**,
  which is the local build's byte count exactly.
- **The archive copy at `www.ietf.org/archive/id/draft-hillier-scitt-arp-04.txt`
  serves the document**, and its header lines match the local build: "J. D.
  Hillier / Certisyn, Inc. / Intended status: Standards Track / 8 September
  2026 / Expires: 12 March 2027".

What it could not: **a byte-for-byte hash.** No raw-byte fetch path is
available from this session, so size and header agreement is as far as it goes.
That is strong and it is not the check. Run it on a networked machine.

Local build, to compare against:

    draft-hillier-scitt-arp.txt   591,005 B
      sha256 63164345921add3a6c4cebf26d6e434306e5efa4120fdf2fcec2535d59691490
    draft-hillier-scitt-arp.md    509,973 B
      sha256 cc81d943cfc1f581ff763e6ada02fa6a51eb7992c72cdeddb113f400741cd001
    draft-hillier-scitt-arp.xml
      sha256 45c89fba4813338a333f5da9db27d6bf16ec9aab7ce4876b582f9135b754ea8f

`_submit/draft-hillier-scitt-arp-04.txt` in the repository is byte-identical to
the build, same sha256. So a `-04` copy exists; what does not exist is a copy
taken from the archive.

Repository HEAD: `758d0b50fe88a2f1fdbe795f886adac17641a4bf`, 8 September 2026.

---

# PART 6. TWO THINGS OVERDUE AGAINST YOUR OWN RULES, AND THEY ARE ONE ACTION

## 6.1 The register does not list `-04`

The register of record is `ietf-drafts/_shared/STANDARDS-REGISTER.md`, 15,929
bytes, sha256 `4c0146108a5fdb0bc2d70a930ea23db54d1496c4ab78f83e49686ed3b2ed9ad1`,
with a byte-identical copy in the OneDrive `IETF-Drafts` folder. Its
filed-revisions table runs `00, 01, 02, 03` and stops. It still says "The ARP
working document is `scitt-arp-f39/ARP-04.md`", a path that no longer exists.

Read against `verify-filings.py` itself rather than from memory: it compares
register rows to the datatracker's posted set and appends a failure for every
posted revision the register omits. **Run today it returns 1, naming
`draft-hillier-scitt-arp-04` as posted and not in the register.**

## 6.2 There is no `-04.FILED.txt`

`-00` through `-03` are all in the OneDrive `IETF-Drafts` folder. `-04` is not.
Searched every connected folder for `*scitt-arp-04*`: only the `_submit` build
copy.

## Why they are one action

`verify-filings.py` also hashes every `*.FILED.txt` in that folder against
`www.ietf.org/archive/id/<name>.txt` and fails on any mismatch. So:

> Save the archive copy as `draft-hillier-scitt-arp-04.FILED.txt` in the
> OneDrive `IETF-Drafts` folder, add the `-04` row to the register, repoint the
> working-document path, then run `verify-filings.py` in that folder.

That single sequence closes 6.1, 6.2 and the fetch-back of Part 5 at once, and
the script is the thing that proves it rather than your own record agreeing
with itself. That is what it was written for.

---

# PART 7. THE CALENDAR, CONFIRMED AGAINST THE DATATRACKER

- **BOF proposals closed 18 September 2026.** Passed.
- **Working group session requests close 2 October 2026, 23:59 UTC.** Twelve
  days. Revised BOF proposals to Area Directors close the same day. **This is
  the binding date.**
- Internet-Draft submission cutoff is 2 November 2026 and does not bind `-04`,
  which is filed. It is the date an `-05` carrying A9 would have to meet.

---

# PART 8. WHAT CLOSING OUT ARP-04 MEANS NOW

In the order I would do it.

| # | Item | Why here |
|---|---|---|
| 1 | Decide A9 | It is the only substantive defect. Either `-05` carries the four sentences you described to Nenad, or he is told the text does not carry them yet. Both are fine; leaving it is not, because he agreed on the description |
| 2 | Save `-04.FILED.txt` from the archive, add the register row, repoint the path, run `verify-filings.py` | One action, three overdue items, and the script is the proof |
| 3 | Decide Emek Can Doğru's Acknowledgments paragraph, and the spelling of his name | Two credits in the body, none in the credits, and the name spelled two ways in the filed bytes |
| 4 | Stage E: notify the reviewers, put the adoption question to the list | Session requests close 2 October |

**On item 1 and the deadline.** A9 does not need `-05` before 2 October. A
session request is not a revision. If you want the adoption mail to be clean,
the honest line is that the digest-suite transition rule is identified,
agreed with the person who raised it, and scheduled, with a discriminating
vector pair already on record from Songbo Bu. That reads better than a rule
nobody has tested.

**On sequencing against the interop deposit.** The report deposits 28 September
and Stage E wants something citable, which leaves four days to 2 October. The
adoption mail can cite the report as forthcoming with its DOI reserved rather
than wait.

---

# PART 9. WHAT THIS PASS ALSO FOUND ON THE INTEROP SIDE

Not ARP, but found by the same sweep and it touches the deposit, so it is
recorded here rather than dropped.

**Nenad Vasic sent three authorised changes on 7 September at 06:59 UTC and
none had reached rev6.** He said so himself on 12 September: "Your notice of
12 September lists what moved after the freeze. Nothing I sent you on
7 September is in it." All three are now applied to rev6, verbatim where he
asked for verbatim:

1. **The section 6.6 paragraph, "How quoted material was produced."** Carried
   exactly as he wrote it, in the slot he named, between "Handling of quoted
   punctuation." and "Handling of absent fields."
2. **The section 6.5 preamble correction.** His name is out of the
   "written or filed by them" list and carries its own sentence: "Nenad
   Vasic's line is his own words, filed under his name by the arrangement
   described at section 6.6." He called this one load-bearing, because without
   it the deposit contradicts itself in adjacent sections. He made it
   conditional on 1 going in; both are in.
3. **His consent state.** The table said "Conditional on the freeze pack". It
   now carries his words: "With the two corrections above applied, the
   sentences naming me in the frozen text are confirmed, and the conditional
   becomes an unconditional yes to deposit", re-affirmed 12 September.

**And the Row 10 Message-ID is recovered.** The row said it "did not survive
transmission into the record held and is not reconstructed here". He sent it
twice and it was stripped twice. The value is:

    <ZvormG7i3EbQoihWNbXARVmqCGr7sgmBapWJo_ET7khAHlRda2hBUcVak-VRf30kbkbDY96t6_WxbUHKknxDFgTSszeS2loksljuEYqQ5kc=@protonmail.com>

Read from the header of the message itself in your mailbox, and independently
confirmed against the IETF archive copy at
`mailarchive.ietf.org/arch/msg/scitt/5cgvlmL8gdW5_nGiKGj9t_6d81M/`, which
carries the same Message-ID, the same date of Thursday 20 August 2026 20:38:50
UTC, and both quoted sentences. Two surfaces agree, so it is recovered rather
than reconstructed, and the row now says so and how.

One thing to know rather than to fix: he described it as "a 105-character
unbreakable token". It is 125 with the angle brackets, 123 without. No figure
is quoted in the report, so nothing carries the error.

**His structural correction checks out.** He said "two paragraphs later" was
wrong and both quoted sentences are in the same paragraph with one sentence
between them. Verified against the archived message: the paragraph runs from
"The rungs carry over." to "authorization-lifecycle heads.", and the
intervening sentence is the one beginning "Rung 3 is where". rev6 already
carried his replacement wording.

**Also fixed in the rows file:** six prose lines had drifted to 73 columns and
one line had broken into a one-word orphan. The rev5 wrapping claim Nenad
verified on 7 September, that every line past column 72 is a single
unbreakable token, is true of rev6 again.

### Guigui Wang: a filed vouching scope, four measurements and two errors

Your own note of **15 September** promised him seven things. **None had reached
rev6.** All are now in, from his own messages rather than from your description
of them:

1. **His section 6.5 vouching scope**, filed 14 September, verbatim. Section 6.5
   said "Guigui Wang has not filed one and his line is held rather than
   assumed"; that sentence is out.
2. **His 14 September confirmation against the frozen bytes.** He read the
   frozen text end to end, recomputed both freeze-pack digests and matched them,
   filed no correction, confirmed his byline, and expressly reserved final
   sign-off as the third step. His cell said only "Conditional on the freeze
   pack".
3. **The post-fix measurements**, in his words of 30 August: "66/66 cases matched
   expected outcome, 1477/1549 individual checks passed, manifest 513 files
   verified, exit 0." The report carried 66 of 66 alone. Three figures were
   missing.
4. **The gate and the regression vector he wrote**, `chain:spec-prev-crosscheck`
   and `10e-prev-hash-unanchored`, with his description of what the vector does.
   He did not only confirm a finding; he built the thing that stops it
   recurring, and none of it was recorded.
5. **His F15 diagnosis**, in full: the one missing character, a '3' at hex
   position 776 inside the ASCII encoding of the nonce, and his conclusion that
   signing and canonicalisation were sound and the defect a transcription fault
   in the dual-encoding manifest. The report credited him with five words.
6. **His independent Ed25519 cross-check**, 6/6 behaving as specified. Uncarried.
7. **The F15 repair commit.** The report said "The exact repair commit for this
   item is not on record." It was on record from 29 August: `60a38af` on main,
   v2.0 at 64 cases, manifest pinning 489 files. The false sentence is out and
   the appendix item listing F15 under absent repair fields is out with it.

**And the quotation error you found is fixed.** F14 printed "Chain anchor at main
0045ea4, CI green on that head, 66 of 66." inside quotation marks. He never wrote
that sentence. It is withdrawn, the entry says so, and his actual words are in.
The F14 quotation cut mid-clause at "runtime-context" now runs to the end of the
clause that states the defect.

**One thing I checked and it is not an error.** Section 1.6 item 4 attributes
"The independent consumer's suite then passed 66/66 cases with CI green on that
head." to the producer. That one is his, from the row he drafted himself on
3 September. It stays.

### Konrad Gruszka: his 17 September mail was unread, and it closes his two items

His reply of **17 September 18:45 UTC** was sitting unread. It supplies both
things your 17 September note asked him for, and rev6 already carried them, so
nothing was lost there. Three items of his were still open and are now in:

1. **The controls design named one rule where it should name two.** His
   correction of 15 September: "The break is NC-05, and it refuses under R1 and
   R5 together... If the design goes in under my name, it should name both
   rules, otherwise a reader who runs it and sees two rules fire will think the
   description is wrong." He flagged on 17 September that it had not landed. It
   has now.
2. **His precision sentences are carried verbatim** rather than transposed to
   your perspective, which is what he asked for wherever the passage sits inside
   a block presented as his own words. It did.
3. **The platform provenance** now carries his own sentence and the run
   timestamp, `2026-08-30T21:42:05Z`, which was not in either file.

**His F7 and F22 positions are already reflected.** F7 states the timestamps and
drops the inference, and records that he declines to assert the stronger reading.
F22 is written from Anton Sokolov's own message and attributed to him alone,
which is exactly what Konrad asked for.

### And the consent picture is not in trouble

I went to recount "Eleven people" and "eleven of the fifteen" and stopped,
because they are not wrong. They describe the terms people set in writing, and
your own freeze-pack mail of 7 September fixes the split exactly: eleven
conditional on the pack, Michael and Nicholas without that condition,
babyblueviper1 and YuTao on the public record, Anton and Vernon not yet a yes.
Fifteen written answers from seventeen names other than yours.

Your 17 September mail then settles the live state in one line: "Your sign-offs
stay on hold until then... and nobody's earlier answer counts against them so we
all start from the same place." That is the notice rule applied to itself, and it
means no count in the report needs to move before Monday.

**The one thing I did not touch** is the "current to 7 September 2026" date on
the status column. Several cells now carry later dates, so that line understates
what the table holds. It is one sentence and it is yours, because moving it
invites a reader to read the counts beside it as current when they are terms
rather than a tally.

### The second read found four false absences, and that is the real finding

Asked to check once more and read to the end rather than trust a summary, I found
**four fields where the report told a reader that something a named contributor had
supplied did not exist, when it was in the editor's own mailbox.** Three were found
in this pass. All four are corrected and each entry now says the earlier statement
was wrong.

| Entry | What it said | Where the material actually was |
|---|---|---|
| **F24** | Pablo Etcheverry's sentence cut at "resolved", remainder "not on record" | His message of 2 September 2026, 10:33:05 UTC, whole |
| **F20** | Henri Sirkkavaara's sentence cut at "was", remainder in a message the report "does not hold in a form it can quote" | The message the entry already quotes, 18 August 15:31 UTC. He said so himself on 15 September |
| **F16** | "The body detail identifying the unusable vector is not on record" | The editor's own run report of 29 August 03:46 UTC. The vector is `v1-allow-with-binding` |
| **F15** | "The exact repair commit for this item is not on record" | Guigui Wang's message of 29 August: `60a38af` on main |

One thing more came out of F24. Pablo Etcheverry wrote "Credit to you for naming the
shape; we just happened to have a case sitting in our own spec." That was carried
nowhere. It is in now as his sentence rather than as the editor's claim, which is the
only safe way to record a credit that flatters the person holding the pen.

And one open question rather than a correction: on the editor's own 29 August message,
**F15 and F16 look like one defect described two ways** - the odd-length hex field, and
the vector being unusable because of it. Whether they stay two findings is not settled
here.

### Henri Sirkkavaara's 15 September reply is only half applied

He listed nine items. Four were already in and two are now: his F20 sentence and repair
whole, and his sweep rule credited in his own words at F20, which he had identified as
the one thing he asked for and the one thing not carried.

**Five are still owed.** Part 4 holds nothing under his name and should hold four
self-found defects. His terminal-seal completeness component is used only inside another
contributor's quotation and is never stated in its own right, though Walter Hawkins asked
him to state it and he did. His CCF-profile review is not recorded as seven findings.
Emek Can Doğru's independent reproduction and extension of his finding 1, from a script
he shipped and pinned, is not carried. And his IETF 127 ask has no home in the text.

That is the same class as the Walter Hawkins error a fortnight ago: a named contributor's
self-found defects absent from the part of the report that exists to carry them.

### The method lesson, recorded so it is not relearned

Every one of those four absences survived an earlier sweep because the sweep was
**line-based on a wrapped file**. The same defect put `Walter Hawkins` outside the E.1
name count in Part 3 of this document's first pass. A phrase broken across a line break
is invisible to `grep`, and both the filed `-04` and the rows pack are hard-wrapped.

**Every check in this pass was rerun on flattened text.** That is now the rule: flatten
before searching, or the search is evidence of nothing.

## Still open on the interop side

- **Pablo Etcheverry's cut F24 sentence.** No reply.
- **Michael Msebenzi's 15 September note.** Not yet mined. Guigui Wang's is done, above.
- **The final recount**, which must be last: "Eleven people" in Part 7,
  "eleven of the fifteen" in the freeze sequence, and the "current to
  7 September 2026" currency note.

---

# PART 10. WHAT I DID NOT DO

- I did not reconstruct `ARP-04-PLAN.md` or the A-item list from the status
  note's summary of it.
- I did not hash the archive copy of `-04`, because no byte-exact fetch path
  exists from here. Size and header agreement is reported as that and not as a
  fetch-back.
- I did not decide A9, name Emek Can Doğru's spelling, or write an
  Acknowledgments paragraph for him. Those are yours.
- I did not accept any figure from a summary. Every count in this document was
  recomputed against the file it describes.
