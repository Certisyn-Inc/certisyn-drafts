# build-draft.ps1 -- the Windows equivalent of `make`.
#
# The repo's Makefile is POSIX and will not run in PowerShell. This does the
# same three steps and adds the one thing the Makefile cannot know about:
# seeding .refcache\ so the build does not depend on bib.ietf.org, whose
# bibxml paths accept a request and never respond.
#
#     .md  --kramdown-rfc2629-->  .xml  --xml2rfc-->  .txt
#
# Usage:
#     .\build-draft.ps1            build
#     .\build-draft.ps1 -Reseed    rebuild .refcache first
#     .\build-draft.ps1 -Lint      also run idnits if present
#
# Commit the .xml. It is the only durable proof of which bytes were filed --
# the lesson of the lost -01.

[CmdletBinding()]
param(
    [string]$RepoPath = $PSScriptRoot,
    [switch]$Reseed,
    [switch]$Lint
)

$ErrorActionPreference = "Stop"
if (-not $RepoPath) { $RepoPath = (Get-Location).Path }
Set-Location $RepoPath

$Draft = "draft-hillier-scitt-arp"
$Md, $Xml, $Txt = "$Draft.md", "$Draft.xml", "$Draft.txt"

function Say($m, $c = "Gray") { Write-Host $m -ForegroundColor $c }
function Head($m) { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }

if (-not (Test-Path $Md)) { Say "No $Md here. cd to the repo first." Red; exit 1 }

# ---------------------------------------------------------------- docname
Head "Source"
Say ("  " + (Select-String -Path $Md -Pattern '^docname:').Line)
Say ("  " + (Select-String -Path $Md -Pattern '^date:').Line)
$headSha = (git rev-parse --short HEAD 2>$null)
if ($headSha) { Say "  HEAD $headSha" }

# ---------------------------------------------------------------- refcache
Head "Reference cache"
$Cache = Join-Path $RepoPath ".refcache"
$seed  = Join-Path $RepoPath "seed-refcache.ps1"
$count = if (Test-Path $Cache) { (Get-ChildItem $Cache -Filter *.xml -EA SilentlyContinue).Count } else { 0 }

if ($Reseed -or $count -lt 17) {
    if (Test-Path $seed) {
        Say "  seeding ($count entries present) ..." Yellow
        & powershell -NoProfile -ExecutionPolicy Bypass -File $seed -RepoPath $RepoPath | Out-Null
        $count = (Get-ChildItem $Cache -Filter *.xml -EA SilentlyContinue).Count
    } else {
        Say "  seed-refcache.ps1 missing; the build will try the network." Yellow
    }
}
Say "  $count entries" Green
$env:KRAMDOWN_REFCACHEDIR = $Cache

# ---------------------------------------------------------------- tools
$kd = (Get-Command kramdown-rfc2629 -EA SilentlyContinue).Source
if (-not $kd) { Say "kramdown-rfc2629 not found: gem install kramdown-rfc2629" Red; exit 1 }

# Store-installed Python hides console scripts off PATH, and xml2rfc has no
# __main__, so `python -m xml2rfc` does not work. Find the exe.
$x2r = (Get-Command xml2rfc -EA SilentlyContinue).Source
if (-not $x2r) {
    $sd = & python -c "import sysconfig;print(sysconfig.get_path('scripts',scheme='nt_user'))" 2>$null
    if ($sd) { $cand = Join-Path $sd "xml2rfc.exe"; if (Test-Path $cand) { $x2r = $cand } }
}
if (-not $x2r) { Say "xml2rfc not found: python -m pip install xml2rfc" Red; exit 1 }

# ---------------------------------------------------------------- md -> xml
Head "kramdown-rfc: $Md -> $Xml"
$o, $e = "$env:TEMP\bd.out", "$env:TEMP\bd.err"
Remove-Item $o, $e -EA SilentlyContinue
$p = Start-Process $kd -ArgumentList $Md -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError $e
if (-not $p.WaitForExit(180000)) { $p.Kill(); Say "  timed out after 3 minutes" Red; exit 1 }
$p.WaitForExit()   # second, untimed call: flushes redirected streams and populates ExitCode

# -Raw on an empty file returns $null, and $null.Trim() throws. Cast it.
[string]$err = if (Test-Path $e) { Get-Content $e -Raw } else { "" }
$size = if (Test-Path $o) { (Get-Item $o).Length } else { 0 }

# Judge on the artifact, not the exit code: with redirected streams ExitCode
# can come back empty, and $null -ne 0 would call a good build a failure.
$ok = ($size -gt 0) -and ((Get-Content $o -Tail 3 -EA SilentlyContinue) -match '</rfc>')
if (-not $ok) {
    Say "  FAILED (exit '$($p.ExitCode)', $size bytes)" Red
    Write-Host ""
    if ($err.Trim()) { Write-Host $err } else { Say "(no stderr)" DarkGray }
    $err | Out-File "$RepoPath\build-error.txt" -Encoding utf8
    Say "Saved build-error.txt" Cyan
    exit 1
}
Copy-Item $o $Xml -Force
Say ("  wrote $Xml ({0:N0} bytes)" -f (Get-Item $Xml).Length) Green
if ($err.Trim()) { Say "  warnings:" Yellow; Write-Host $err }

# ---------------------------------------------------------------- xml -> txt
Head "xml2rfc: $Xml -> $Txt"
# xml2rfc writes warnings to stderr. Under ErrorActionPreference=Stop those
# surface as terminating NativeCommandErrors and would abort a good build, so
# relax it just for this call.
$prev = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$x2rOut = & $x2r --text $Xml 2>&1
$ErrorActionPreference = $prev
$x2rOut | ForEach-Object { Say "  $_" DarkGray }
if (-not (Test-Path $Txt)) { Say "  FAILED" Red; exit 1 }
Say ("  wrote $Txt ({0:N0} bytes, {1} lines)" -f (Get-Item $Txt).Length, (Get-Content $Txt).Count) Green

# ---------------------------------------------------------------- lint
if ($Lint) {
    Head "idnits"
    if (Get-Command idnits -EA SilentlyContinue) { idnits --nitcount $Txt }
    else { Say "  not installed. Upload $Txt to https://author-tools.ietf.org/ and press Validate." DarkGray }
}

Head "Done"
Say "  $Xml   <- commit this"
Say "  $Txt   <- upload to https://datatracker.ietf.org/submit/"
