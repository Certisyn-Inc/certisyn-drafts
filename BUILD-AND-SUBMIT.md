# Build and submit — `draft-hillier-scitt-arp`

Operational runbook for producing and filing a revision of the Attestation
Reconciliation Protocol Internet-Draft.

> **Why this file is not optional.** Revision `-01` was filed on 23 July 2026
> from a working copy that was never committed here. The repository still held
> `-00`, so the filed normative text existed in exactly one place: the IETF
> archive. **The source in this repository is the source of record. If a
> revision is filed from anywhere else, it is lost.** See `RECOVERY.md`.

---

## 0. The invariant

```
draft-hillier-scitt-arp.md   ->   .xml   ->   .txt   ->   datatracker
        (this repo)             (build)    (submit)      (published)
```

Every filed revision MUST be reachable by running `make` on a commit in this
repository, and that commit MUST be tagged. No exceptions, including for
"quick" edits made under deadline — that is precisely how `-01` went missing.

---

## 1. Toolchain

Two paths. Use whichever is available; they produce the same output.

### 1a. Local (preferred)

```bash
# Ruby side — markdown to RFCXML v3
gem install kramdown-rfc2629

# Python side — RFCXML v3 to text/html/pdf
pip install xml2rfc
```

Verify:

```bash
kramdown-rfc2629 --version
xml2rfc --version              # known good: 3.34.0
```

### 1b. Hosted, no install — IETF Author Tools

<https://author-tools.ietf.org/>

Upload `draft-hillier-scitt-arp.md` and it returns the `.xml`, `.txt`, `.html`
and an idnits report. Use this when the local Ruby toolchain is unavailable —
for example inside a sandbox where `rubygems.org` is unreachable, which is the
situation that produced this note.

**If you use the hosted path, commit the returned `.xml` alongside the `.md`.**
It is the only way to prove later which bytes were filed.

---

## 2. Build

```bash
make            # md -> xml -> txt
make html       # md -> xml -> html
make lint       # idnits, if installed
make clean
```

Or by hand:

```bash
kramdown-rfc2629 draft-hillier-scitt-arp.md > draft-hillier-scitt-arp.xml
xml2rfc --text  draft-hillier-scitt-arp.xml
xml2rfc --html  draft-hillier-scitt-arp.xml
```

### Before every submission

- [ ] `docname:` in the front matter matches the revision you intend to file
      (`draft-hillier-scitt-arp-NN`). **This is the single most common error.**
      `-00` sat in this repo with `docname: draft-hillier-scitt-arp-00` while
      `-01` was live on the datatracker.
- [ ] `date:` is the intended filing date, not a stale one.
- [ ] `python3 check-filed-state.py` is clean. It reads the tags, not this
      checklist, so it also catches a branch cut before the last filing that
      would move `docname` backwards.
- [ ] Every `{{reference}}` resolves — an unresolved reference silently renders
      as literal text.
- [ ] `make lint` is clean, or every remaining nit is understood and accepted.
- [ ] Appendix E (Document History) has a new subsection for this revision
      listing what changed. Reviewers read it first.
- [ ] Divergence-axis names use the **kebab-case** convention already filed
      (`agent-impersonation-suspected`, `agent-credential-absent`,
      `agent-principal-unverifiable`, `agent-action-scope-divergence`,
      `freshness-stale`, `register-record-absent`). Do not introduce
      snake_case variants; other implementers are already citing these.

---

## 3. Submit

1. <https://datatracker.ietf.org/submit/>
2. Upload the `.txt` **and** the `.xml`. Uploading only the text loses the
   structured source on the IETF side.
3. Author block: J. D. Hillier, Certisyn, Inc., `jhillier@certisyn.com`.
4. **Confirm by email.** The datatracker sends a confirmation link to the author
   address and the submission does not post until that link is clicked. A
   submission left unconfirmed never appears — and looks, from the author's
   side, much like a successful one.
5. Wait for `New Version Notification for draft-hillier-scitt-arp-NN.txt`.

### Verify it actually posted

Do not trust the submission screen, and do not trust the HTML status page —
it can serve a cached revision number. The API is authoritative:

```bash
curl -s "https://datatracker.ietf.org/api/v1/doc/document/?name=draft-hillier-scitt-arp&format=json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['objects'][0]; print(d['name'],'rev',d['rev'],d['time'])"
```

---

## 4. Immediately after the notification arrives

Non-negotiable, in this order:

```bash
git add draft-hillier-scitt-arp.md draft-hillier-scitt-arp.xml
git commit -m "draft-hillier-scitt-arp-NN as filed YYYY-MM-DD"
git tag -a draft-hillier-scitt-arp-NN -m "Filed YYYY-MM-DD"
git push origin main --tags
```

Then, and only then, announce to `scitt@ietf.org` from `contact@certisyn.com`,
so the links in the announcement resolve.

### The gate behind this section

This section has said "non-negotiable, in this order" since July, and section 0
has said every filed revision must be reachable on a commit here and that
commit must be tagged, "No exceptions". Measured 13 November 2026, with all of
that written down and nothing reading it:

- `-06` was filed on 23 October and its commit sat on `fix/06-clean`, so `main`
  carried `-05` while the datatracker served `-06`.
- `-04` was tagged and reachable from **no branch at all**. One deleted tag from
  being the `-01` incident again.
- An obsolete pull request stood open proposing `docname: -05` with a filing
  date of 2026-10-15, which is not a date anything was filed on.

A rule with no gate is a note. `check-filed-state.py` is the gate. It refuses
an untagged filing, a filing whose tree has no `.xml`, a filing whose front
matter contradicts the date its own commit subject asserts, the newest filing
not being reachable from the trunk, and a branch proposing a `docname` behind
the trunk. `--venue` adds the datatracker API from section 3 above, and an
unreadable venue exits 3 rather than passing.

Install it once per clone:

```bash
git config core.hooksPath .githooks
```

CI runs it on every push and pull request, and **on a daily schedule**. The
schedule is the part that matters: a push gate cannot see a revision filed from
a working copy that is never pushed, which is precisely how `-01` was lost.

Prove the gate itself still refuses:

```bash
python3 check-filed-state.py --self-test
```

---

## 5. Identities

| purpose | address |
|---|---|
| Draft author / datatracker | `jhillier@certisyn.com` |
| SCITT list posting | `contact@certisyn.com` |
| Media | `press@certisyn.com` |

---

## 6. Related drafts

The same runbook applies to:

- `draft-hillier-certisyn-ai-governance-verified`
- `draft-hillier-certisyn-essential-eight-verified`

All three are at `-01`, filed 24 July 2026. Their sources have the same exposure
as this one — check whether either is under version control before assuming it.
