# seed-refcache.ps1
#
# Populates .refcache\ so kramdown-rfc never needs bib.ietf.org.
#
# Why: on this machine bib.ietf.org is unreachable. TCP to its IPv4 address
# succeeds and datatracker.ietf.org resolves to the same Cloudflare range and
# answers 200, but any HTTPS request to the hostname bib.ietf.org stalls --
# hostname-level TLS filtering, not routing. kramdown-rfc fetches EVERY
# reference from there, so each one times out and the build dies.
#
#   RFC entries  -- written from rfc-editor.org metadata, embedded below.
#   I-D entries  -- fetched from datatracker.ietf.org/doc/bibxml3/, which works.
#
# Re-runnable. Delete .refcache\ once bib.ietf.org is reachable again.

[CmdletBinding()]
param([string]$RepoPath = "C:\Users\joelh\certisyn-app\scitt-arp-f39")

$ErrorActionPreference = "Stop"
Set-Location $RepoPath
$Cache = Join-Path $RepoPath ".refcache"
New-Item -ItemType Directory -Force -Path $Cache | Out-Null

function Say($m, $c = "Gray") { Write-Host $m -ForegroundColor $c }

# ---------------------------------------------------------------- RFC entries
# title | authors "Initials Surname" | year | month
$RFCS = @{
  "2119" = @("Key words for use in RFCs to Indicate Requirement Levels", @("S. Bradner"), "1997", "March")
  "3339" = @("Date and Time on the Internet: Timestamps", @("G. Klyne", "C. Newman"), "2002", "July")
  "3986" = @("Uniform Resource Identifier (URI): Generic Syntax", @("T. Berners-Lee", "R. Fielding", "L. Masinter"), "2005", "January")
  "6838" = @("Media Type Specifications and Registration Procedures", @("N. Freed", "J. Klensin", "T. Hansen"), "2013", "January")
  "6839" = @("Additional Media Type Structured Syntax Suffixes", @("T. Hansen", "A. Melnikov"), "2013", "January")
  "7638" = @("JSON Web Key (JWK) Thumbprint", @("M. Jones", "N. Sakimura"), "2015", "September")
  "8949" = @("Concise Binary Object Representation (CBOR)", @("C. Bormann", "P. Hoffman"), "2020", "December")
  "9530" = @("Digest Fields", @("R. Polli", "L. Pardue"), "2024", "February")
  "8174" = @("Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words", @("B. Leiba"), "2017", "May")
  "8067" = @("Updating When Standards Track Documents May Refer Normatively to Documents at a Lower Level", @("B. Leiba"), "2017", "January")
  "6350" = @("vCard Format Specification", @("S. Perreault"), "2011", "August")
  "8615" = @("Well-Known Uniform Resource Identifiers (URIs)", @("M. Nottingham"), "2019", "May")
  "8259" = @("The JavaScript Object Notation (JSON) Data Interchange Format", @("T. Bray"), "2017", "December")
  "8785" = @("JSON Canonicalization Scheme (JCS)", @("A. Rundgren", "B. Jordan", "S. Erdtman"), "2020", "June")
  "9052" = @("CBOR Object Signing and Encryption (COSE): Structures and Process", @("J. Schaad"), "2022", "August")
  "9053" = @("CBOR Object Signing and Encryption (COSE): Initial Algorithms", @("J. Schaad"), "2022", "August")
  "9334" = @("Remote ATtestation procedureS (RATS) Architecture", @("H. Birkholz", "D. Thaler", "M. Richardson", "N. Smith", "W. Pan"), "2023", "January")
  "9421" = @("HTTP Message Signatures", @("A. Backman", "J. Richer", "M. Sporny"), "2024", "February")
  "9942" = @("CBOR Object Signing and Encryption (COSE) Receipts", @("O. Steele", "H. Birkholz", "A. Delignat-Lavaud", "C. Fournet"), "2026", "June")
  "9943" = @("An Architecture for Trustworthy and Transparent Digital Supply Chains", @("H. Birkholz", "A. Delignat-Lavaud", "C. Fournet", "Y. Deshpande", "S. Lasker"), "2026", "June")
}

# Sub-series membership. An RFC that is also part of an STD or BCP renders as
# "STD 94, RFC 8949" rather than "RFC 8949", so the seriesInfo has to be here or
# the reference list will not match what the RFC Editor publishes. Only the ones
# this draft cites are listed.
$SUBSERIES = @{
  "3986" = @("STD", "66")
  "6838" = @("BCP", "13")
  "8949" = @("STD", "94")
}

function Esc($s) { $s -replace '&','&amp;' -replace '<','&lt;' -replace '>','&gt;' }

Say "RFC references" Cyan
foreach ($num in ($RFCS.Keys | Sort-Object)) {
    $t, $authors, $year, $month = $RFCS[$num]
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("<?xml version='1.0' encoding='UTF-8'?>")
    [void]$sb.AppendLine("<reference anchor='RFC$num' target='https://www.rfc-editor.org/info/rfc$num'>")
    [void]$sb.AppendLine("  <front>")
    [void]$sb.AppendLine("    <title>$(Esc $t)</title>")
    foreach ($a in $authors) {
        $parts   = $a -split ' ', 2
        $initials = $parts[0]
        $surname  = $parts[1]
        [void]$sb.AppendLine("    <author initials='$initials' surname='$(Esc $surname)' fullname='$(Esc $a)'><organization /></author>")
    }
    [void]$sb.AppendLine("    <date year='$year' month='$month' />")
    [void]$sb.AppendLine("  </front>")
    if ($SUBSERIES.ContainsKey($num)) {
        $sName, $sVal = $SUBSERIES[$num]
        [void]$sb.AppendLine("  <seriesInfo name='$sName' value='$sVal' />")
    }
    [void]$sb.AppendLine("  <seriesInfo name='RFC' value='$num' />")
    [void]$sb.AppendLine("  <seriesInfo name='DOI' value='10.17487/RFC$num' />")
    [void]$sb.AppendLine("</reference>")
    $p = Join-Path $Cache "reference.RFC.$num.xml"
    [IO.File]::WriteAllText($p, $sb.ToString(), (New-Object Text.UTF8Encoding $false))
    Say ("  RFC $num  " + $t.Substring(0, [Math]::Min(52, $t.Length))) Green
}

# ---------------------------------------------------------------- I-D entries
$IDS = @(
  "mih-sato-agent-accountability-composition",
  "mih-sokolov-scitt-payload-binding",
  "ietf-scitt-scrapi",
  "meunier-webbotauth-httpsig-protocol",
  "meunier-webbotauth-httpsig-directory",
  "meunier-webbotauth-registry"
)

Write-Host ""
Say "I-D references (from datatracker)" Cyan
$failed = @()
foreach ($d in $IDS) {
    $file = "reference.I-D.$d.xml"
    $dest = Join-Path $Cache $file
    $url  = "https://datatracker.ietf.org/doc/bibxml3/$file"
    $code = curl.exe --ipv4 -sL -m 25 -o $dest -w "%{http_code}" $url
    $len  = if (Test-Path $dest) { (Get-Item $dest).Length } else { 0 }
    if ($code -eq "200" -and $len -gt 200) {
        Say "  ok    $d  (${len}b)" Green
    } else {
        Say "  FAIL  $d  -> HTTP $code" Red
        $failed += $d
        Remove-Item $dest -ErrorAction SilentlyContinue
    }
}

Write-Host ""
if ($failed.Count) {
    Say "Could not fetch: $($failed -join ', ')" Yellow
    Say "The build will still try the network for those." Yellow
} else {
    Say "Cache complete: $((Get-ChildItem $Cache -Filter *.xml).Count) entries." Green
}
Say "Set this before building:" Cyan
Say "  `$env:KRAMDOWN_REFCACHEDIR = '$Cache'" Gray
