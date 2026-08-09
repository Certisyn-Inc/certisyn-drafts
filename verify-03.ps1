# verify-03.ps1 -- read-only. Confirms the -03 candidate is what it is said to be,
# then opens the folder holding the four email attachments.
#
#   .\verify-03.ps1            verify and open _send
#   .\verify-03.ps1 -NoOpen    verify only

[CmdletBinding()]
param([string]$RepoPath = $PSScriptRoot, [switch]$NoOpen)

if (-not $RepoPath) { $RepoPath = (Get-Location).Path }
Set-Location $RepoPath

function Head($m) { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  PASS  $m" -ForegroundColor Green }
function Bad($m)  { Write-Host "  FAIL  $m" -ForegroundColor Red }

$expectMd  = "89059b9823ee3c3ae85d45bcae1da7bb5d2fe600dcaa1f84b159a916fcabb109"
$expectTxt = "715513d49b10d0e8ad1379db28a073b24cccb295153a210b3b8abe1f9fe6ac28"
$fail = 0

Head "Branch and commits"
git status --short --branch
git log --oneline -3

Head "Source and text digests"
$md = (Get-FileHash draft-hillier-scitt-arp.md -Algorithm SHA256).Hash.ToLower()
if ($md -eq $expectMd) { Ok "draft-hillier-scitt-arp.md  $md" }
else { Bad "draft-hillier-scitt-arp.md`n        expected $expectMd`n        actual   $md"; $fail++ }

if (Test-Path draft-hillier-scitt-arp.txt) {
    $tx = (Get-FileHash draft-hillier-scitt-arp.txt -Algorithm SHA256).Hash.ToLower()
    $ln = (Get-Content draft-hillier-scitt-arp.txt).Count
    if ($tx -eq $expectTxt) { Ok "draft-hillier-scitt-arp.txt  $tx  ($ln lines)" }
    else { Bad "draft-hillier-scitt-arp.txt`n        expected $expectTxt`n        actual   $tx"; $fail++ }
} else { Write-Host "  note  no .txt present; run .\build-draft.ps1 first" -ForegroundColor Yellow }

Head "Conformance manifest"
Push-Location conformance
$m = & python runners\verify_manifest.py 2>&1
$mOk = $LASTEXITCODE -eq 0
Pop-Location
$m | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
if ($mOk) { Ok "MANIFEST: PASS" } else { Bad "MANIFEST: FAIL"; $fail++ }

Head "idnits 3.1.0"
if (Test-Path _send\draft-hillier-scitt-arp-03.txt) {
    $n = & npx --yes @ietf-tools/idnits@latest _send\draft-hillier-scitt-arp-03.txt 2>&1
    $line = ($n | Select-String -Pattern 'Review the' | Select-Object -First 1).ToString().Trim()
    Write-Host "  $line" -ForegroundColor DarkGray
    if ($line -match '1 error') {
        Ok "1 error -- the deliberate RFC 8785 downref, documented in the Note to the RFC Editor"
    } else { Bad "expected exactly 1 error; read the full output above"; $fail++ }
} else { Bad "_send\draft-hillier-scitt-arp-03.txt missing"; $fail++ }

Head "Attachments for the emails"
if (Test-Path _send) {
    Get-ChildItem _send | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB)}} | Format-Table -AutoSize
    if (-not $NoOpen) { explorer.exe (Resolve-Path _send).Path }
} else { Bad "_send folder missing"; $fail++ }

Head "Result"
if ($fail -eq 0) {
    Write-Host "  Everything checks out. The four files in _send are the attachments." -ForegroundColor Green
    Write-Host "  Attach all four to the typed-reference mail before sending it." -ForegroundColor Green
} else {
    Write-Host "  $fail check(s) failed -- do not send until these are understood." -ForegroundColor Red
}
Write-Host ""
