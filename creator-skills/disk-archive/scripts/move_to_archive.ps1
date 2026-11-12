# Move finished work to an archive drive (robocopy /MOVE: copy, then remove the source), verify bytes at the destination, stop on the first problem.
#   -Jobs jobs.json   [{"src":"D:\\work\\proj-a","dst":"E:\\archive\\D-work\\proj-a","files":[]}]
#   files = optional masks such as ["G_*.pth","D_*.pth"]: moves only those files and leaves the folders in place
param([Parameter(Mandatory = $true)][string]$Jobs, [string]$Log = '')
$ErrorActionPreference = 'Stop'
if (-not $Log) { $Log = [IO.Path]::ChangeExtension($Jobs, '.log') }
function Log($m) { $l = (Get-Date -Format 'HH:mm:ss') + ' ' + $m; Add-Content -LiteralPath $Log -Value $l -Encoding UTF8; Write-Output $l }
function Bytes($p, $files) {
  $a = @($p, (Join-Path $env:TEMP '__robo_dummy_nonexist')) + $files + @('/L', '/S', '/NJH', '/BYTES', '/NFL', '/NDL', '/XJ', '/MT:16')
  $o = & robocopy @a 2>$null
  $l = $o | Where-Object { $_ -match '^\s*Bytes\s*:' } | Select-Object -First 1
  if ($l -match 'Bytes\s*:\s*(\d+)') { [double]$Matches[1] } else { 0 }
}
$list = Get-Content -LiteralPath $Jobs -Raw -Encoding UTF8 | ConvertFrom-Json
$drives = $list | ForEach-Object { Split-Path -Qualifier $_.dst } | Sort-Object -Unique
foreach ($d in $drives) { if (-not (Test-Path -LiteralPath "$d\")) { Log "STOP: destination drive $d is not connected, nothing moved"; exit 1 } }

Log "start: $($list.Count) items"
foreach ($j in $list) {
  $src = $j.src; $dst = $j.dst; $files = @($j.files | Where-Object { $_ })
  if (-not (Test-Path -LiteralPath $src)) { Log "SKIP not found $src"; continue }
  $before = Bytes $src $files
  $flag = if ($files.Count) { '/MOV' } else { '/MOVE' }
  $a = @($src, $dst) + $files + @('/E', $flag, '/COPY:DAT', '/DCOPY:T', '/R:1', '/W:1', '/XJ', '/MT:8', '/NFL', '/NDL', '/NP', '/NJH', '/NJS')
  & robocopy @a | Out-Null
  $rc = $LASTEXITCODE
  $after = Bytes $dst $files
  $left = if (Test-Path -LiteralPath $src) { Bytes $src $files } else { 0 }
  Log ("{0} rc={1} src {2:N3} GB -> dst {3:N3} GB, left at src {4:N3} GB" -f $src, $rc, ($before / 1GB), ($after / 1GB), ($left / 1GB))
  if ($rc -ge 8 -or $after -lt $before) { Log "STOP: copy failed or destination smaller than source for $src"; exit 1 }
}
Get-PSDrive -PSProvider FileSystem | ForEach-Object { Log ("{0}: free {1:N2} GB" -f $_.Name, ($_.Free / 1GB)) }
Log 'MOVEDONE'
exit 0   # robocopy leaves LASTEXITCODE 1 on success
