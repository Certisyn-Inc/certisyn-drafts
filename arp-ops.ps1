# arp-ops.ps1 -- the only ARP commands you should need.
#
# Nothing here is required right now: everything is committed and pushed.
# This exists so a fresh session (or you) can get to a known state fast.
#
#   .\arp-ops.ps1 status      where everything stands            (default)
#   .\arp-ops.ps1 build       rebuild the current branch
#   .\arp-ops.ps1 filed       check out the FILED -02 and verify it
#   .\arp-ops.ps1 wip         check out the -03 work in progress
#   .\arp-ops.ps1 verify      prove the filed .xml matches its .md
#
# Background you will otherwise rediscover the hard way:
#   * The repo Makefile is POSIX and will not run in PowerShell. build-draft.ps1
#     is the equivalent. Do not run `make`.
#   * bib.ietf.org answers its root but never answers its bibxml paths, so
#     kramdown-rfc hangs on every reference. seed-refcache.ps1 populates
#     .refcache\ and build-draft.ps1 calls it. Do not remove .refcache.
#   * Store-installed Python puts xml2rfc.exe off PATH and xml2rfc has no
#     __main__, so `python -m xml2rfc` fails. build-draft.ps1 resolves the exe.
#   * Adding a new RFC reference to the draft means adding it to
#     seed-refcache.ps1 too, or the build hangs on it.

[CmdletBinding()]
param(
    [ValidateSet('status','build','filed','wip','verify')]
    [string]$Action = 'status',
    [string]$RepoPath = 'C:\Users\joelh\certisyn-app\scitt-arp-f39'
)

$ErrorActionPreference = 'Stop'
Set-Location $RepoPath
function Say($m,$c='Gray'){ Write-Host $m -ForegroundColor $c }
function Head($m){ Write-Host ''; Write-Host "=== $m ===" -ForegroundColor Cyan }

$FILED = 'feat/revision-02-canonicalization'
$WIP   = 'wip/revision-03'

switch ($Action) {

'status' {
    Head 'Branches'
    git branch -vv | ForEach-Object { Say "  $_" }
    Head 'Working tree'
    $st = git status --short
    if ($st) { $st | ForEach-Object { Say "  $_" Yellow } } else { Say '  clean' Green }
    Head 'Draft on this branch'
    Say ("  " + (Select-String -Path draft-hillier-scitt-arp.md -Pattern '^docname:').Line)
    Say ("  " + (Select-String -Path draft-hillier-scitt-arp.md -Pattern '^date:').Line)
    Say ("  lines: " + (Get-Content draft-hillier-scitt-arp.md).Count)
    Head 'Filed on the datatracker'
    Say '  draft-hillier-scitt-arp-02, 2026-08-08, idnits clean'
    Say "  reproduced by: $FILED @ ae54748" DarkGray
    Head 'Reference cache'
    $n = (Get-ChildItem .refcache -Filter *.xml -EA SilentlyContinue).Count
    if ($n -ge 19) { Say "  $n entries" Green } else { Say "  $n entries -- run seed-refcache.ps1" Yellow }
}

'build' {
    Head ('Building ' + (git rev-parse --abbrev-ref HEAD))
    $m = (Select-String -Path draft-hillier-scitt-arp.md -Pattern '^<<<<<<<|^>>>>>>>' | Measure-Object).Count
    if ($m) { Say "  $m conflict markers in the source -- fix before building." Red; break }
    Remove-Item draft-hillier-scitt-arp.xml,draft-hillier-scitt-arp.txt -EA SilentlyContinue
    & powershell -NoProfile -ExecutionPolicy Bypass -File .\build-draft.ps1
}

'filed' {
    Head "Checking out the FILED revision"
    git checkout $FILED
    Say ("  " + (git log --oneline -1))
    Say ("  " + (Select-String -Path draft-hillier-scitt-arp.md -Pattern '^docname:').Line) Green
    Say '  This branch reproduces what is on the datatracker. Do not commit -03 work here.' Yellow
}

'wip' {
    Head "Checking out the -03 work in progress"
    Say '  NOT FILEABLE. See ARP-03-BLOCKERS.md and the commit message on HEAD.' Yellow
    git checkout $WIP
    Say ("  " + (git log --oneline -1))
    Say ("  " + (Select-String -Path draft-hillier-scitt-arp.md -Pattern '^docname:').Line)
}

'verify' {
    Head 'Verifying the filed XML reproduces from its markdown'
    $cur = git rev-parse --abbrev-ref HEAD
    if ($cur -ne $FILED) { Say "  On $cur. Run: .\arp-ops.ps1 filed" Yellow; break }
    $known = (Get-FileHash draft-hillier-scitt-arp.xml -Algorithm SHA256).Hash
    Say "  committed .xml sha256 $known" DarkGray
    Copy-Item draft-hillier-scitt-arp.xml "$env:TEMP\filed-known.xml" -Force
    & powershell -NoProfile -ExecutionPolicy Bypass -File .\build-draft.ps1 | Out-Null
    $new = (Get-FileHash draft-hillier-scitt-arp.xml -Algorithm SHA256).Hash
    if ($new -eq $known) {
        Say '  MATCH -- the filed bytes are reachable from this commit.' Green
    } else {
        Say '  DIFFERS from the committed .xml.' Red
        Say '  Expect this if kramdown-rfc or a cached reference changed since the filing;' DarkGray
        Say '  compare the two before concluding the source drifted.' DarkGray
        Say "  old: $env:TEMP\filed-known.xml" DarkGray
    }
}

}
