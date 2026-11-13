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
  F6 VENUE       opt-in, needs the network: the datatracker's own API - the
                 one BUILD-AND-SUBMIT section 3 names as authoritative,
                 because the HTML status page can serve a cached revision -
                 does not hold a revision newer than this repository does.
                 Unreachable is UNKNOWN and exits 3. It is never a pass.

  python3 check-filed-state.py              F1-F5, no network
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
    """The draft this repository is for, derived rather than hardcoded, so the
    same gate serves the other drafts the runbook section 6 names."""
    out, _ = git("ls-files", cwd=repo)
    cands = [f for f in out.splitlines()
             if re.match(r"^draft-[a-z0-9-]+\.md$", f)]
    if len(cands) != 1:
        return None, cands
    return cands[0][:-3], cands


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
        if h not in filed_subjects:
            subj, _ = git("log", "-1", "--format=%s", h, cwd=repo, ok=True)
            out.refuse("F1", "tag %s points at %s, whose subject is not "
                             "'%s as filed YYYY-MM-DD': %s" % (t, h[:8], t, subj))
        else:
            revs[t]["subject_rev"], revs[t]["subject_date"] = filed_subjects[h]

    for h, (srev, sdate) in filed_subjects.items():
        if not any(r["commit"] == h for r in revs.values()):
            out.refuse("F1", "%s says it is '%s as filed %s' and carries no tag. "
                             "BUILD-AND-SUBMIT section 4 tags every filing."
                       % (h[:8], srev, sdate))
    return revs


def main(argv):
    out = Report()
    repo, _ = git("rev-parse", "--show-toplevel")
    name, cands = draft_name(repo)
    if not name:
        out.refuse("F0", "expected exactly one draft-*.md at the repository "
                         "root, found %d: %s" % (len(cands), ", ".join(cands) or "none"))
        return out.finish()
    md = name + ".md"
    xml = name + ".xml"
    out.say("draft            %s" % name)

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
        have_md = git("ls-tree", t, "--name-only", "--", md, cwd=repo, ok=True)[0]
        have_xml = git("ls-tree", t, "--name-only", "--", xml, cwd=repo, ok=True)[0]
        if not have_md:
            out.refuse("F2", "%s carries no %s" % (t, md))
        if not have_xml:
            out.refuse("F2", "%s carries no %s. The .xml is the structured "
                             "source uploaded to the datatracker and the only "
                             "proof of which bytes were filed." % (t, xml))
        fdoc, fdate = front_matter(repo, t, md)
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
    for t, r in sorted(revs.items()):
        if r is not newest and not r["on_trunk"]:
            holders = git("branch", "-a", "--contains", r["commit"], cwd=repo, ok=True)[0]
            holders = ", ".join(b.strip() for b in holders.splitlines()) or "NO BRANCH"
            out.note("F4", "%s is off %s, held by: %s. Superseded, so this is a "
                           "notice; its tag is the only thing keeping it."
                     % (t, trunk, holders))

    head_doc, _ = front_matter(repo, "HEAD", md)
    trunk_doc, _ = front_matter(repo, trunk, md)
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
