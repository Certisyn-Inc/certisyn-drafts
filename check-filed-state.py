#!/usr/bin/env python3
"""
CERTISYN - filed-state gate for an Internet-Draft repository.

THE THING: what this repository holds on its trunk is what was filed at the
IETF, and every filed revision is still reachable.

WHY IT EXISTS. BUILD-AND-SUBMIT.md already says all of this. Section 0: "Every
filed revision MUST be reachable by running make on a commit in this
repository, and that commit MUST be tagged. No exceptions." Section 4 gives the
four commands and calls them non-negotiable. It was written because -01 was
filed from a working copy that was never committed and survived only in the
IETF archive.

It was written down and it still happened twice more. Measured 2026-11-13:
  -06 was filed on 23 October and its commit sat on fix/06-clean, so main
     carried -05 while the datatracker served -06.
  -04 was tagged and reachable from NO branch at all - one deleted tag from
     being the -01 incident again.
A rule with no gate is a note. This is the gate.

WHAT IT CHECKS
  F1 TAGGED      every "as filed" commit carries the tag its subject names,
                 and every such tag points at an "as filed" commit
  F2 COMPLETE    that commit's tree carries BOTH the .md and the .xml. The
                 .xml is the structured source uploaded to the datatracker;
                 .gitignore says so in as many words, and BUILD-AND-SUBMIT
                 section 1b calls it the only way to prove which bytes were
                 filed
  F3 AGREES      docname and date in that commit's own front matter match the
                 tag name and the date its subject asserts
  F4 ON TRUNK    the NEWEST filed revision is reachable from the trunk.
                 Refusal. An older one off the trunk is a NOTICE, because
                 history cannot be rewritten and its tag still holds it
  F5 FORWARD     HEAD's docname is not BEHIND the trunk's. A branch cut before
                 a filing proposes to move the record backwards, which is how
                 an obsolete pull request sat open proposing -05 and a filing
                 date that never happened
  F6 VENUE       opt-in, needs the network, and DELIBERATELY NARROW: it asks
                 only whether the datatracker holds a revision this repository
                 does not. It does NOT compare bytes. _shared/verify-filings.py
                 owns that question - it reads the submission API and diffs
                 every .FILED.txt against the IETF archive, written after two
                 reference copies were found truncated and a reconstruction was
                 diffed against the corrupt copy. One question, one script: do
                 not reimplement archive comparison here.
                 the datatracker's own API - the
                 one BUILD-AND-SUBMIT section 3 names as authoritative,
                 because the HTML status page can serve a cached revision -
                 does not hold a revision newer than this repository does.
                 Unreachable is UNKNOWN and exits 3. It is never a pass.

  python3 check-filed-state.py              F1-F7, no network
  python3 check-filed-state.py --dir X      scope to subdirectory X, for a
                                            repository holding several drafts
  python3 check-filed-state.py --venue      adds F6
  python3 check-filed-state.py --self-test  drives every refusal, changes nothing

EXIT  0 clean   1 refused   3 unknown (a surface could not be read)
"""
import json, os, re, subprocess, sys, tempfile, shutil, urllib.request, urllib.error

TRUNK = os.environ.get("FILED_STATE_TRUNK", "main")
API = ("https://datatracker.ietf.org/api/v1/doc/document/"
       "?name={name}&format=json")


def git(*a, cwd=None, ok=False):
    p = subprocess.run(("git",) + a, cwd=cwd, capture_output=True, text=True)
    if p.returncode and not ok:
        raise RuntimeError("git %s: %s" % (" ".join(a), p.stderr.strip()))
    return p.stdout.strip(), p.returncode


def front_matter(repo, ref, path):
    """docname and date as that ref's own tree states them, or (None, None)."""
    out, rc = git("show", "%s:%s" % (ref, path), cwd=repo, ok=True)
    if rc:
        return None, None
    d = n = None
    for line in out.splitlines()[:20]:
        m = re.match(r"^docname:\s*(\S+)", line)
        if m:
            n = m.group(1)
        m = re.match(r"^date:\s*(\S+)", line)
        if m:
            d = m.group(1)
    return n, d


def draft_name(repo):
    """The draft this repository is for, and how its revisions are laid out.

    TWO LAYOUTS ARE REAL, and an earlier version of this gate only knew one.
      single        one live source, draft-NAME.md, revisions carried by tags.
                    draft-hillier-scitt-arp.
      per-revision  one file per revision, draft-NAME-NN.md. The other three
                    drafts the runbook section 6 names are all like this, and
                    the gate refused to run on them at all rather than saying
                    anything useful about them.
    Returns (name, layout, files)."""
    # Paths at the ROOT OF THE SCOPE only. git ls-files run with cwd set to a
    # subdirectory already returns paths relative to it, so no rewriting is
    # needed - and rewriting was wrong: basenaming pulled
    # archive/prior-revisions/draft-...-01.md into the candidate set and made a
    # single-source repository read as a per-revision one.
    out, _ = git("ls-files", cwd=repo)
    out = "\n".join(f for f in out.splitlines() if "/" not in f)
    md = [f for f in out.splitlines() if re.match(r"^draft-[a-z0-9-]+(-\d{2})?(-[A-Z]+)?\.md$", f)]
    plain = [f for f in md if re.match(r"^draft-[a-z0-9-]+\.md$", f)
             and not re.search(r"-\d{2}\.md$", f)]
    numbered = [f for f in md if re.search(r"-\d{2}(-[A-Z]+)?\.md$", f)]
    if len(plain) == 1 and not numbered:
        return plain[0][:-3], "single", plain
    if numbered:
        stems = {re.sub(r"-\d{2}(-[A-Z]+)?\.md$", "", f) for f in numbered}
        if len(stems) == 1:
            return stems.pop(), "per-revision", sorted(numbered)
        return None, None, sorted(numbered)
    return None, None, md


def rev_of(docname):
    m = re.match(r"^(.*)-(\d{2})$", docname or "")
    return (m.group(1), int(m.group(2))) if m else (None, None)


def collect(repo, name, md, out):
    """Every filed revision this repository knows about."""
    tags, _ = git("tag", "--list", "%s-[0-9][0-9]" % name, cwd=repo)
    tags = [t for t in tags.splitlines() if t]
    log, _ = git("log", "--all", "--format=%H%x1f%s", cwd=repo)
    filed_subjects = {}
    for line in log.splitlines():
        h, _, s = line.partition("\x1f")
        m = re.match(r"^(%s-\d{2}) as filed (\d{4}-\d{2}-\d{2})$" % re.escape(name), s)
        if m:
            filed_subjects.setdefault(h, (m.group(1), m.group(2)))

    revs = {}
    for t in tags:
        h, rc = git("rev-list", "-1", t, cwd=repo, ok=True)
        if rc:
            out.refuse("F1", "tag %s does not resolve to a commit" % t)
            continue
        revs[t] = {"tag": t, "commit": h, "subject_rev": None, "subject_date": None}
        if h in filed_subjects:
            revs[t]["subject_rev"], revs[t]["subject_date"] = filed_subjects[h]
        else:
            # THE TAG'S OWN ANNOTATION IS ALSO A FILING RECORD, and
            # BUILD-AND-SUBMIT section 4 is where that comes from: it says
            # `git tag -a NAME-NN -m "Filed YYYY-MM-DD"`. A repository whose
            # history is imported after the fact has one import commit carrying
            # several drafts, so no single commit subject can name a filing and
            # the tag is the only place the date can live. Requiring the commit
            # subject would have made this gate unusable on exactly the
            # repositories that most needed it.
            # TWO DATES, AND THEY ARE NOT THE SAME DATE. The datatracker
            # records a submission_date and a document_date, and they differ by
            # a day on every late-evening filing from Utah: -02 of both
            # certisyn drafts was submitted 2026-08-11 and is dated 2026-08-12.
            # The front matter carries the DOCUMENT date, so that is what F3
            # may compare against; the submission date is the venue's record of
            # when it was filed and is kept beside it, not instead of it.
            # Conflating the two is how an obsolete pull request came to assert
            # a filing date that never happened.
            ann, _ = git("for-each-ref", "--format=%(contents)",
                         "refs/tags/" + t, cwd=repo, ok=True)
            m = (re.search(r"Document date (\d{4}-\d{2}-\d{2})", ann or "")
                 or re.search(r"Filed (\d{4}-\d{2}-\d{2})", ann or ""))
            if m:
                revs[t]["subject_rev"], revs[t]["subject_date"] = t, m.group(1)
            else:
                subj, _ = git("log", "-1", "--format=%s", h, cwd=repo, ok=True)
                out.refuse("F1", "tag %s records no filing date. Its commit "
                                 "subject is %r, which is not '%s as filed "
                                 "YYYY-MM-DD', and its own annotation records "
                                 "neither 'Document date YYYY-MM-DD' nor "
                                 "'Filed YYYY-MM-DD'."
                           % (t, subj, t))

    for h, (srev, sdate) in filed_subjects.items():
        if not any(r["commit"] == h for r in revs.values()):
            out.refuse("F1", "%s says it is '%s as filed %s' and carries no tag. "
                             "BUILD-AND-SUBMIT section 4 tags every filing."
                       % (h[:8], srev, sdate))
    return revs


def main(argv):
    out = Report()
    repo, _ = git("rev-parse", "--show-toplevel")
    root = repo
    sub = ""
    if "--dir" in argv:
        sub = argv[argv.index("--dir") + 1].strip("/")
        repo = os.path.join(repo, sub)
        if not os.path.isdir(repo):
            out.refuse("F0", "no such directory: %s" % sub)
            return out.finish()
        out.say("directory        %s" % sub)
    name, layout, cands = draft_name(repo)
    if not name:
        out.refuse("F0", "cannot tell which draft this repository is for. Found "
                         "%d candidate source file(s): %s" % (len(cands), ", ".join(cands) or "none"))
        return out.finish()
    md = name + ".md"
    xml = name + ".xml"
    out.say("draft            %s" % name)
    out.say("layout           %s" % layout)

    # A docname may be claimed by exactly one source file. Two files asserting
    # the same revision means the one that was filed cannot be identified from
    # the tree, which is the whole question this gate exists to answer.
    claims = {}
    for f in cands:
        d, _ = front_matter(repo, "HEAD", f)
        if d:
            claims.setdefault(d, []).append(f)
    for d, fs in sorted(claims.items()):
        if len(fs) > 1:
            out.refuse("F7", "docname %s is claimed by %d files: %s. Which of "
                             "them was filed cannot be read off the tree."
                       % (d, len(fs), ", ".join(fs)))

    def source_for(rev_tag):
        """Where revision NN's source lives, which is the only thing the two
        layouts disagree about."""
        if layout == "single":
            return md
        nn = rev_tag[-2:]
        for f in cands:
            if re.search(r"-%s(-[A-Z]+)?\.md$" % nn, f):
                return f
        return "%s-%s.md" % (name, nn)

    trunk = TRUNK
    if git("rev-parse", "--verify", "--quiet", "origin/" + TRUNK, ok=True)[1] == 0:
        trunk = "origin/" + TRUNK
    elif git("rev-parse", "--verify", "--quiet", TRUNK, ok=True)[1] != 0:
        out.refuse("F0", "no %s or origin/%s in this repository" % (TRUNK, TRUNK))
        return out.finish()
    out.say("trunk            %s" % trunk)

    revs = collect(repo, name, md, out)
    if not revs:
        out.refuse("F1", "no filed revision is tagged in this repository")
        return out.finish()

    for t, r in sorted(revs.items()):
        h = r["commit"]
        src = source_for(t)
        rxml = (xml if layout == "single" else "%s.xml" % t)
        have_md = git("ls-tree", t, "--name-only", "--", src, cwd=repo, ok=True)[0]
        have_xml = git("ls-tree", t, "--name-only", "--", rxml, cwd=repo, ok=True)[0]
        if not have_md:
            out.refuse("F2", "%s carries no %s" % (t, src))
        r["have_xml"] = bool(have_xml)
        r["xml_name"] = rxml
        fdoc, fdate = front_matter(repo, t, src)
        if fdoc and fdoc != t:
            out.refuse("F3", "%s front matter says docname %s" % (t, fdoc))
        if fdate and r["subject_date"] and fdate != r["subject_date"]:
            out.refuse("F3", "%s front matter dates it %s, its commit subject "
                             "says filed %s" % (t, fdate, r["subject_date"]))
        r["on_trunk"] = git("merge-base", "--is-ancestor", h, trunk, cwd=repo, ok=True)[1] == 0

    newest = max(revs.values(), key=lambda r: rev_of(r["tag"])[1])
    out.say("filed revisions  %d, newest %s" % (len(revs), newest["tag"]))

    if not newest["on_trunk"]:
        holders = git("branch", "-a", "--contains", newest["commit"], cwd=repo, ok=True)[0]
        holders = ", ".join(b.strip() for b in holders.splitlines()) or "no branch at all"
        out.refuse("F4", "%s is filed and is NOT reachable from %s. It is on: %s. "
                         "The trunk does not hold what the IETF is serving."
                   % (newest["tag"], trunk, holders))
    if not newest.get("have_xml"):
        out.refuse("F2", "%s carries no %s. The .xml is the structured source "
                         "uploaded to the datatracker and the only proof of "
                         "which bytes were filed. Retrieve it from "
                         "https://www.ietf.org/archive/id/%s and commit it."
                   % (newest["tag"], newest.get("xml_name"), newest.get("xml_name")))
    for t, r in sorted(revs.items()):
        if r is not newest and not r.get("have_xml"):
            out.note("F2", "%s carries no %s. Filed before the .xml discipline, "
                           "so a notice rather than a refusal - it may not exist "
                           "in the archive either. verify-filings.py compares the "
                           "text against the archive for this one."
                     % (t, r.get("xml_name")))
    for t, r in sorted(revs.items()):
        if r is not newest and not r["on_trunk"]:
            holders = git("branch", "-a", "--contains", r["commit"], cwd=repo, ok=True)[0]
            holders = ", ".join(b.strip() for b in holders.splitlines()) or "NO BRANCH"
            out.note("F4", "%s is off %s, held by: %s. Superseded, so this is a "
                           "notice; its tag is the only thing keeping it."
                     % (t, trunk, holders))

    newest_src = source_for(newest["tag"])
    head_doc, _ = front_matter(repo, "HEAD", newest_src if layout == "per-revision" else md)
    trunk_doc, _ = front_matter(repo, trunk, newest_src if layout == "per-revision" else md)
    if layout == "per-revision":
        # On this layout a newer revision is a new FILE, so "is the tree ahead
        # of the trunk" is asked of the highest-numbered source present, and
        # the trunk is read the same way rather than reported as None.
        hi = max((int(re.search(r"-(\d{2})(-[A-Z]+)?\.md$", f).group(1)) for f in cands), default=None)
        if hi is not None:
            head_doc = "%s-%02d" % (name, hi)
        # ROOT OF THE SCOPE, not recursive. This read -r and so counted
        # working/draft-...-03.md as a revision the trunk carries, while the
        # HEAD side counted only the scope root - two scans of one question
        # disagreeing, which is the defect this gate exists to refuse. Pinned
        # by the self-test case below.
        # FROM THE REPOSITORY ROOT. Run with cwd inside the scoped directory,
        # git applies that prefix to the <rev>:<path> argument as well and the
        # listing comes back EMPTY - so this returned nothing, thi was None,
        # and F5's trunk side silently passed everything in the one mode it was
        # added for. A check that fails open is worse than no check.
        tout, _ = git("ls-tree", "--name-only", "%s:%s" % (trunk, sub), cwd=root, ok=True)
        tnum = [f for f in (tout or "").splitlines()
                if re.search(r"-\d{2}(-[A-Z]+)?\.md$", f) and f.startswith(name + "-")]
        thi = max((int(re.search(r"-(\d{2})(-[A-Z]+)?\.md$", f).group(1)) for f in tnum), default=None)
        trunk_doc = "%s-%02d" % (name, thi) if thi is not None else None
    hr, tr = rev_of(head_doc)[1], rev_of(trunk_doc)[1]
    out.say("docname          HEAD %s, %s %s" % (head_doc, trunk, trunk_doc))
    if hr is not None and tr is not None and hr < tr:
        out.refuse("F5", "HEAD proposes docname %s while %s already carries %s. "
                         "A branch cut before a filing moves the record backwards."
                   % (head_doc, trunk, trunk_doc))

    if "--venue" in argv:
        try:
            req = urllib.request.Request(API.format(name=name),
                                         headers={"User-Agent": "certisyn-filed-state"})
            with urllib.request.urlopen(req, timeout=30) as r:
                objs = json.load(r).get("objects") or []
            if not objs:
                out.unknown("F6", "the datatracker returned no object for %s" % name)
            else:
                vrev, vtime = objs[0].get("rev"), objs[0].get("time")
                out.say("datatracker      rev %s, %s" % (vrev, vtime))
                vn = int(vrev) if (vrev or "").isdigit() else None
                rn = rev_of(newest["tag"])[1]
                if vn is None:
                    out.unknown("F6", "the datatracker reported rev %r" % vrev)
                elif vn > rn:
                    out.refuse("F6", "the datatracker serves rev %02d and the newest "
                                     "revision in this repository is %02d. A filing "
                                     "was made from somewhere that is not here."
                               % (vn, rn))
                elif vn < rn:
                    out.note("F6", "this repository holds %02d and the datatracker "
                                   "serves %02d, so %02d is built and tagged but not "
                                   "posted, or the post is unconfirmed." % (rn, vn, rn))
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as e:
            out.unknown("F6", "the datatracker could not be read: %s. An unreadable "
                              "venue is not a clean one." % e)
    return out.finish()


class Report(object):
    def __init__(self):
        self.lines, self.bad, self.unk, self.notes = [], [], [], []

    def say(self, m):
        self.lines.append("  " + m)

    def refuse(self, c, m):
        self.bad.append("  REFUSED  %s  %s" % (c, m))

    def unknown(self, c, m):
        self.unk.append("  UNKNOWN  %s  %s" % (c, m))

    def note(self, c, m):
        self.notes.append("  NOTE     %s  %s" % (c, m))

    def finish(self):
        print("FILED STATE - the trunk holds what was filed")
        for l in self.lines:
            print(l)
        for l in self.notes + self.unk + self.bad:
            print(l)
        if self.bad:
            print("REFUSED - %d finding(s)." % len(self.bad))
            return 1
        if self.unk:
            print("UNKNOWN - %d surface(s) could not be read. Not a pass." % len(self.unk))
            return 3
        print("OK - every filed revision is tagged, complete, self-consistent, "
              "and the newest is on the trunk.")
        return 0


# --------------------------------------------------------------- self-test
def sh(cwd, *a):
    env = dict(os.environ)
    # THE MEASURED DEFECT, carried over from certisyn-app: git exports GIT_DIR
    # to its hooks, so a self-test that runs `git init` in a temp directory
    # with GIT_DIR inherited re-initialises the REAL repository. It set
    # core.bare there twice and committed into the real tree. Unset them.
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        env.pop(k, None)
    env.update({"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})
    p = subprocess.run(a, cwd=cwd, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def fixture(d, revs, trunk_at, head_at=None, xml=True):
    sh(d, "git", "init", "-q", "-b", "main", ".")
    for n, date in revs:
        doc = "draft-x-y-%02d" % n
        open(os.path.join(d, "draft-x-y.md"), "w").write(
            "---\ntitle: X\nabbrev: X\ndocname: %s\ndate: %s\n---\nbody\n" % (doc, date))
        if xml:
            open(os.path.join(d, "draft-x-y.xml"), "w").write("<rfc/>\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "%s as filed %s" % (doc, date))
        sh(d, "git", "tag", "-a", doc, "-m", "Filed %s" % date)
    # Resolve BEFORE moving anything, and detach first: `git branch -f` refuses
    # to move the branch that is currently checked out, which silently left an
    # earlier version of this fixture testing a different scenario than it
    # claimed to. The self-test caught it, which is the point of having one.
    trunk_sha = sh(d, "git", "rev-parse", trunk_at)[1].strip()
    head_sha = sh(d, "git", "rev-parse", head_at or trunk_at)[1].strip()
    sh(d, "git", "checkout", "-q", "--detach", head_sha)
    sh(d, "git", "branch", "-f", "main", trunk_sha)


def run(d, *extra):
    env = dict(os.environ)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(k, None)
    p = subprocess.run([sys.executable, os.path.abspath(__file__)] + list(extra),
                       cwd=d, env=env, capture_output=True, text=True)
    return p.returncode, p.stdout


def self_test():
    cases, fails = [], 0
    base = tempfile.mkdtemp(prefix="filed-state-selftest-")
    try:
        # 1. honest path
        d = os.path.join(base, "clean"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08"), (5, "2026-10-23")], "HEAD")
        cases.append(("the honest path passes", run(d)[0] == 0, run(d)[1]))

        # 2. F4 - newest filing off the trunk
        d = os.path.join(base, "offtrunk"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08"), (5, "2026-10-23")], "HEAD~1", head_at="HEAD")
        rc, o = run(d)
        cases.append(("the newest filing off the trunk REFUSES", rc == 1 and "F4" in o, o))

        # 3. F2 - a filing with no .xml
        d = os.path.join(base, "noxml"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08")], "HEAD", xml=False)
        rc, o = run(d)
        cases.append(("a filing with no .xml REFUSES", rc == 1 and "F2" in o, o))

        # 4. F3 - subject date disagrees with the front matter
        d = os.path.join(base, "datedrift"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08")], "HEAD")
        open(os.path.join(d, "draft-x-y.md"), "w").write(
            "---\ntitle: X\nabbrev: X\ndocname: draft-x-y-05\ndate: 2026-10-15\n---\nbody\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "draft-x-y-05 as filed 2026-10-23")
        sh(d, "git", "tag", "-a", "draft-x-y-05", "-m", "Filed 2026-10-23")
        sh(d, "git", "branch", "-f", "main", "HEAD")
        rc, o = run(d)
        cases.append(("a filing date that contradicts the front matter REFUSES",
                      rc == 1 and "F3" in o, o))

        # 5. F1 - an untagged filing
        d = os.path.join(base, "untagged"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08")], "HEAD")
        open(os.path.join(d, "draft-x-y.md"), "w").write(
            "---\ntitle: X\nabbrev: X\ndocname: draft-x-y-05\ndate: 2026-10-23\n---\nb\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "draft-x-y-05 as filed 2026-10-23")
        sh(d, "git", "branch", "-f", "main", "HEAD")
        rc, o = run(d)
        cases.append(("an untagged filing REFUSES", rc == 1 and "F1" in o, o))

        # 7. the per-revision layout, honest path
        d = os.path.join(base, "perrev"); os.makedirs(d)
        sh(d, "git", "init", "-q", "-b", "main", ".")
        for n in (0, 1, 2):
            open(os.path.join(d, "draft-x-y-%02d.md" % n), "w").write(
                "---\ndocname: draft-x-y-%02d\ndate: 2026-0%d-01\n---\nb\n" % (n, n + 5))
            open(os.path.join(d, "draft-x-y-%02d.xml" % n), "w").write("<rfc/>\n")
            sh(d, "git", "add", "-A")
            sh(d, "git", "commit", "-q", "-m", "draft-x-y-%02d as filed 2026-0%d-01" % (n, n + 5))
            sh(d, "git", "tag", "-a", "draft-x-y-%02d" % n, "-m", "Filed")
        rc, o = run(d)
        cases.append(("a per-revision layout passes on the honest path",
                      rc == 0 and "per-revision" in o, o))

        # 8. F7 - two source files claiming one docname
        d = os.path.join(base, "twoclaims"); os.makedirs(d)
        sh(d, "git", "init", "-q", "-b", "main", ".")
        for nm in ("draft-x-y-00.md", "draft-x-y-00-SUBMIT.md"):
            open(os.path.join(d, nm), "w").write(
                "---\ndocname: draft-x-y-00\ndate: 2026-09-27\n---\nb\n")
        open(os.path.join(d, "draft-x-y-00.xml"), "w").write("<rfc/>\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "draft-x-y-00 as filed 2026-09-27")
        sh(d, "git", "tag", "-a", "draft-x-y-00", "-m", "Filed")
        rc, o = run(d)
        cases.append(("two source files claiming one docname REFUSES",
                      rc == 1 and "F7" in o, o))

        # 9. an imported history: one commit, tags carrying the filing dates
        d = os.path.join(base, "imported"); os.makedirs(d)
        sh(d, "git", "init", "-q", "-b", "main", ".")
        for n in (0, 1, 2):
            open(os.path.join(d, "draft-x-y-%02d.md" % n), "w").write(
                "---\ndocname: draft-x-y-%02d\ndate: 2026-0%d-01\n---\nb\n" % (n, n + 5))
            open(os.path.join(d, "draft-x-y-%02d.xml" % n), "w").write("<rfc/>\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "Import the filed sources")
        for n in (0, 1, 2):
            sh(d, "git", "tag", "-a", "draft-x-y-%02d" % n, "-m",
               "Filed 2026-0%d-01" % (n + 5))
        rc, o = run(d)
        cases.append(("an imported history with annotated tags passes",
                      rc == 0, o))

        # 10. F1 - a tag that records no filing date anywhere
        d = os.path.join(base, "nodate"); os.makedirs(d)
        sh(d, "git", "init", "-q", "-b", "main", ".")
        open(os.path.join(d, "draft-x-y-00.md"), "w").write(
            "---\ndocname: draft-x-y-00\ndate: 2026-05-01\n---\nb\n")
        open(os.path.join(d, "draft-x-y-00.xml"), "w").write("<rfc/>\n")
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "Import")
        sh(d, "git", "tag", "-a", "draft-x-y-00", "-m", "no date here")
        rc, o = run(d)
        cases.append(("a tag recording no filing date REFUSES",
                      rc == 1 and "F1" in o, o))

        # 11. a working/ subdirectory of unfiled iterations is not the trunk's
        #     revision set. This refused chorale-protocol wrongly.
        d = os.path.join(base, "workingdir"); os.makedirs(d)
        sh(d, "git", "init", "-q", "-b", "main", ".")
        os.makedirs(os.path.join(d, "working"))
        open(os.path.join(d, "draft-x-y-00-SUBMIT.md"), "w").write(
            "---\ndocname: draft-x-y-00\ndate: 2026-09-27\n---\nb\n")
        open(os.path.join(d, "draft-x-y-00.xml"), "w").write("<rfc/>\n")
        for n in (1, 2, 3):
            open(os.path.join(d, "working", "draft-x-y-%02d.md" % n), "w").write(
                "---\ndocname: draft-x-y-%02d\n---\nb\n" % n)
        sh(d, "git", "add", "-A")
        sh(d, "git", "commit", "-q", "-m", "Import")
        sh(d, "git", "tag", "-a", "draft-x-y-00", "-m", "Document date 2026-09-27, submitted 2026-09-27")
        rc, o = run(d)
        cases.append(("unfiled iterations under working/ are not the trunk's "
                      "revision set", rc == 0, o))

        # 6. F5 - a branch proposing a docname behind the trunk
        d = os.path.join(base, "backwards"); os.makedirs(d)
        fixture(d, [(4, "2026-09-08"), (5, "2026-10-23")], "HEAD")
        sh(d, "git", "checkout", "-q", "-b", "stale", "HEAD~1")
        rc, o = run(d)
        cases.append(("a branch proposing a docname behind the trunk REFUSES",
                      rc == 1 and "F5" in o, o))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("FILED STATE SELF-TEST - %d case(s)" % len(cases))
    for label, ok, o in cases:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        if not ok:
            fails += 1
            for l in o.splitlines():
                print("        | " + l)
    print("SELF-TEST %s" % ("OK - every check refuses its planted case and passes "
                            "its clean one." if not fails else "FAILED"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else main(sys.argv[1:]))
