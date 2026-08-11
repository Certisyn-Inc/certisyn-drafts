# verify-03.ps1 -- read-only. Confirms the -03 candidate is what it is said to be,
# then opens the folder holding the four email attachments.
#
# RUN IT AS A FILE, from anywhere:
#
#     C:\Users\joelh\certisyn-app\scitt-arp-f39\verify-03.ps1
#
# Do not paste the contents into a prompt. Pasted lines leave $PSScriptRoot
# empty, so the script would resolve to whatever directory the shell happens to
# be in and report the ARP files as missing. It now locates the repository
# itself and refuses to run anywhere else, because a check that half-runs
# against the wrong tree reports failures that are about the shell and not
# about the artefact.
#
#     verify-03.ps1            verify and open _send
#     verify-03.ps1 -NoOpen    verify only

[CmdletBinding()]
param([string]$RepoPath, [switch]$NoOpen)

$Anchor = "draft-hillier-scitt-arp.md"
$Known  = "C:\Users\joelh\certisyn-app\scitt-arp-f39"

# Resolve in order: explicit argument, the script's own folder, the current
# folder, the known path. Each is only accepted if the draft source is in it.
$candidates = @($RepoPath, $PSScriptRoot, (Get-Location).Path, $Known) |
              Where-Object { $_ } | Select-Object -Unique
$RepoPath = $candidates | Where-Object { Test-Path (Join-Path $_ $Anchor) } |
            Select-Object -First 1

if (-not $RepoPath) {
    Write-Host ""
    Write-Host "  Could not find the ARP repository." -ForegroundColor Red
    Write-Host "  Looked for $Anchor in:" -ForegroundColor Red
    $candidates | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    Write-Host ""
    Write-Host "  Run the script as a file rather than pasting it, or pass the path:" -ForegroundColor Yellow
    Write-Host "    verify-03.ps1 -RepoPath $Known" -ForegroundColor Yellow
    Write-Host ""
    exit 2
}
Set-Location $RepoPath

function Head($m) { Write-Host ""; Write-Host "=== $m ===" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  PASS  $m" -ForegroundColor Green }
function Bad($m)  { Write-Host "  FAIL  $m" -ForegroundColor Red }

# The bytes to be filed on 13 August. These are NOT the 9 August for-comment
# digests (89059b98 / 715513d4) -- those describe the document as circulated,
# before the edits made in response to Songbo Bu, Iman Schrock, Steven Mih and
# Tom Sato. ARP-03-REVISION-NOTE.md section 0 publishes the same two values.
# Anyone changing the source must change these in the same commit, or this
# script reports the change as tampering.
$expectMd  = "9a086e8832489f456ae5066848c208ceccbab9e00adadd29bc003c3a142c86c9"
$expectTxt = "8fab5b82a67f56e0735a859ecfa0a7bb78ccb44fb85a9d87a6efea3342f07c27"
$fail = 0

Write-Host ""
Write-Host "  repo  $RepoPath" -ForegroundColor DarkGray

Head "Branch and commits"
git status --short --branch
git log --oneline -3

Head "Source and text digests"
$md = (Get-FileHash (Join-Path $RepoPath $Anchor) -Algorithm SHA256).Hash.ToLower()
if ($md -eq $expectMd) { Ok "draft-hillier-scitt-arp.md  $md" }
else { Bad "draft-hillier-scitt-arp.md`n        expected $expectMd`n        actual   $md"; $fail++ }

$txPath = Join-Path $RepoPath "draft-hillier-scitt-arp.txt"
if (Test-Path $txPath) {
    $tx = (Get-FileHash $txPath -Algorithm SHA256).Hash.ToLower()
    $ln = (Get-Content $txPath).Count
    if ($tx -eq $expectTxt) { Ok "draft-hillier-scitt-arp.txt  $tx  ($ln lines)" }
    else { Bad "draft-hillier-scitt-arp.txt`n        expected $expectTxt`n        actual   $tx"; $fail++ }
} else { Write-Host "  note  no .txt present; run .\build-draft.ps1 first" -ForegroundColor Yellow }

Head "Conformance manifest"
Push-Location (Join-Path $RepoPath "conformance")
$m = & python (Join-Path $RepoPath "conformance\runners\verify_manifest.py") 2>&1
$mOk = $LASTEXITCODE -eq 0
Pop-Location
$m | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
if ($mOk) { Ok "MANIFEST: PASS" } else { Bad "MANIFEST: FAIL"; $fail++ }

Head "idnits 3.1.0"
$sendTxt = Join-Path $RepoPath "_send\draft-hillier-scitt-arp-03.txt"
$log     = Join-Path $RepoPath ".tools\idnits-03.txt"
$local   = Join-Path $RepoPath ".tools\node_modules\.bin\idnits.cmd"

if (-not (Test-Path $sendTxt)) {
    Bad "_send\draft-hillier-scitt-arp-03.txt missing"; $fail++
} else {
    # Prefer the pinned local install. npx fetches on every run, and a fetch
    # that is slow, rate-limited or racing another npx produces no output at
    # all -- which is indistinguishable from a clean document unless the
    # script says which happened. Install once with:
    #   npm install --prefix .tools @ietf-tools/idnits@3.1.0
    if (Test-Path $local) {
        Write-Host "  using $local" -ForegroundColor DarkGray
        $n = & $local $sendTxt 2>&1
    } else {
        Write-Host "  no local install; falling back to npx (needs network)" -ForegroundColor Yellow
        $n = & npx --yes @ietf-tools/idnits@3.1.0 $sendTxt 2>&1
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
    $n | Out-File -FilePath $log -Encoding utf8
    $hit = $n | Select-String -Pattern 'Review the' | Select-Object -First 1

    if (-not $hit) {
        # The check did not run. That is a different thing from the check
        # running and failing, and reporting it as a failure of the document
        # would be exactly the mistake this document is about.
        Bad "INCONCLUSIVE -- idnits produced no summary line, so nothing was measured"
        Write-Host "        $($n.Count) line(s) of output, saved to .tools\idnits-03.txt" -ForegroundColor DarkGray
        if ($n.Count) {
            Write-Host "        last lines:" -ForegroundColor DarkGray
            $n | Select-Object -Last 6 | ForEach-Object {
                Write-Host "          $($_.ToString().Trim())" -ForegroundColor DarkGray }
        } else {
            Write-Host "        no output at all. Usually a network fetch that did not" -ForegroundColor DarkGray
            Write-Host "        complete, or two npx runs racing. Install the pinned copy:" -ForegroundColor DarkGray
            Write-Host "          npm install --prefix .tools @ietf-tools/idnits@3.1.0" -ForegroundColor DarkGray
        }
        $fail++
    } else {
        $line = $hit.ToString().Trim()
        Write-Host "  $line" -ForegroundColor DarkGray
        if ($line -match '\b1 error\b') {
            Ok "1 error -- the deliberate RFC 8785 downref, documented in the Note to the RFC Editor"
        } else {
            Bad "expected exactly 1 error; full output in .tools\idnits-03.txt"; $fail++
        }
    }
}

Head "Filing package"
$send = Join-Path $RepoPath "_send"
if (Test-Path $send) {
    $files = @(Get-ChildItem $send -File)
    $files | Select-Object Name, @{n='KB';e={[math]::Round($_.Length/1KB)}} | Format-Table -AutoSize
    Write-Host "  $($files.Count) file(s)" -ForegroundColor DarkGray

    # The file that gets uploaded is the copy in _send, not the one at the repo
    # root, and only the root copy was hashed above. A stale copy here would be
    # filed without anything noticing, so compare the two directly.
    $sendCopy = Join-Path $send "draft-hillier-scitt-arp-03.txt"
    if (Test-Path $sendCopy) {
        $sh = (Get-FileHash $sendCopy -Algorithm SHA256).Hash.ToLower()
        if ($sh -eq $expectTxt) { Ok "_send copy is the same bytes as the verified text" }
        else { Bad "_send\draft-hillier-scitt-arp-03.txt differs from the verified text`n        expected $expectTxt`n        actual   $sh`n        re-copy it from the repo root before filing"; $fail++ }
    } else { Bad "_send\draft-hillier-scitt-arp-03.txt missing -- that is the file to upload"; $fail++ }

    if (-not $NoOpen) { explorer.exe $send }
} else { Bad "_send folder missing"; $fail++ }

Head "Result"
if ($fail -eq 0) {
    Write-Host "  Everything checks out against the bytes proposed as -03." -ForegroundColor Green
    Write-Host "  To file: upload _send\draft-hillier-scitt-arp-03.txt at" -ForegroundColor Green
    Write-Host "    https://datatracker.ietf.org/submit/" -ForegroundColor Green
    Write-Host "  Comments closed end of Wednesday 12 August; anything later goes into -04." -ForegroundColor DarkGray
} else {
    Write-Host "  $fail check(s) failed -- do not file until these are understood." -ForegroundColor Red
}
Write-Host ""
exit $fail
