# rehearsal voice for /salereelclip using the Windows OneCore Thai voice (Microsoft Pattara)
# Female, robotic. For timing tests only, never for a published clip.
# Usage (PowerShell): powershell -ExecutionPolicy Bypass -File tts_rehearsal.ps1 <in_utf8.txt> <out.wav> [rate=1.15]
param([string]$In, [string]$Out, [double]$Rate = 1.15)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.SpeechSynthesis.SpeechSynthesizer, Windows.Media.SpeechSynthesis, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
$s = New-Object Windows.Media.SpeechSynthesis.SpeechSynthesizer
$v = [Windows.Media.SpeechSynthesis.SpeechSynthesizer]::AllVoices | Where-Object { $_.Language -eq 'th-TH' } | Select-Object -First 1
if ($null -eq $v) { Write-Error 'no th-TH OneCore voice installed'; exit 1 }
$s.Voice = $v
$s.Options.SpeakingRate = $Rate
$text = [IO.File]::ReadAllText($In, [Text.Encoding]::UTF8)
$stream = Await ($s.SynthesizeTextToStreamAsync($text)) ([Windows.Media.SpeechSynthesis.SpeechSynthesisStream])
$reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
$size = [uint32]$stream.Size
Await ($reader.LoadAsync($size)) ([uint32]) | Out-Null
$bytes = New-Object byte[] $size
$reader.ReadBytes($bytes)
[IO.File]::WriteAllBytes($Out, $bytes)
Write-Output ("voice " + $v.DisplayName + " -> " + $Out + " (" + $size + " bytes)")
