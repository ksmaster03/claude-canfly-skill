# Hide pending Windows updates whose title matches -Pattern, so a failing one stops forcing restarts.
# Must run elevated. Writes hide-update.log next to this script.
param([Parameter(Mandatory = $true)][string]$Pattern)
$log = Join-Path $PSScriptRoot 'hide-update.log'
Start-Transcript -Path $log -Force | Out-Null
try {
  $searcher = (New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher()
  "searching for pending updates..."
  $hiddenNow = 0
  foreach ($u in $searcher.Search("IsInstalled=0").Updates) {
    "found: $($u.Title) (hidden=$($u.IsHidden))"
    if ($u.Title -match $Pattern -and -not $u.IsHidden) { $u.IsHidden = $true; $hiddenNow++; "  -> hidden" }
  }
  "hidden in this run: $hiddenNow"
  "--- all hidden updates now ---"
  foreach ($u in $searcher.Search("IsInstalled=0 and IsHidden=1").Updates) { "hidden: $($u.Title)" }
  "DONE"
} catch { "ERROR: $($_.Exception.Message)" } finally { Stop-Transcript | Out-Null }
