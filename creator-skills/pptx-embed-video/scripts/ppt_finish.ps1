# Step in PowerPoint (no window): append another deck, make the video on a slide start automatically, or export slide images.
#   -Mode finish -Deck x.pptx [-Append other.pptx] [-Slide 2]
#   -Mode export -Deck x.pptx -OutDir dir -Slides 1,2,25
# Paths must be absolute with backslashes: InsertFromFile fails on forward slashes.
param([string]$Mode, [string]$Deck, [string]$Append = '', [string]$OutDir = '', [string]$Slides = '', [int]$Slide = 2)
$ErrorActionPreference = 'Stop'
$started = $false
try { $app = [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application') } catch { $app = New-Object -ComObject PowerPoint.Application; $started = $true }
$ro = if ($Mode -eq 'export') { -1 } else { 0 }   # export opens read-only so it can read decks it must not change
$p = $app.Presentations.Open($Deck, $ro, 0, 0)
try {
  if ($Mode -eq 'finish') {
    if ($Append) { [void]$p.Slides.InsertFromFile($Append, $p.Slides.Count); "appended -> $($p.Slides.Count) slides" }
    $s = $p.Slides.Item($Slide); $v = $null
    foreach ($sh in $s.Shapes) { if ($sh.Type -eq 16) { $v = $sh } }
    if (-not $v) { throw "no media shape on slide $Slide" }
    $v.AnimationSettings.PlaySettings.PlayOnEntry = -1
    $v.AnimationSettings.PlaySettings.HideWhileNotPlaying = 0
    # PlayOnEntry alone leaves the play effect on page click (trigger 1); after previous (3) with no previous = start automatically
    for ($i = 1; $i -le $s.TimeLine.MainSequence.Count; $i++) {
      $e = $s.TimeLine.MainSequence.Item($i)
      if ($e.Shape.Name -eq $v.Name -and $e.EffectType -eq 83) { $e.Timing.TriggerType = 3; $e.Timing.TriggerDelayTime = 0 }
    }
    for ($i = 1; $i -le $s.TimeLine.MainSequence.Count; $i++) { $e = $s.TimeLine.MainSequence.Item($i); "video effect type=$($e.EffectType) trigger=$($e.Timing.TriggerType) length(ms)=$($v.MediaFormat.Length)" }
    $p.Save()
  } elseif ($Mode -eq 'export') {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    foreach ($n in ($Slides -split ',')) { $p.Slides.Item([int]$n).Export((Join-Path $OutDir ("slide{0:D2}.png" -f [int]$n)), 'PNG', 1600, 900) }
    "exported $Slides of $($p.Slides.Count)"
  }
} finally {
  $p.Close()
  if ($started -and $app.Presentations.Count -eq 0) { $app.Quit() }
}
