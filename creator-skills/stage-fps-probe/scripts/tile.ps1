# test helper: keep one small window above others WITHOUT taking focus or keyboard. -Off clears it.
param([string]$Title = 'Page Title', [switch]$Off)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class Wn2 {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint f);
}
"@
$found = [IntPtr]::Zero
$cb = [Wn2+EnumProc]{ param($h, $l)
  if ([Wn2]::IsWindowVisible($h)) { $s = New-Object Text.StringBuilder 256; [void][Wn2]::GetWindowText($h, $s, 256)
    if ($s.ToString().Contains($Title)) { $script:found = $h; return $false } }
  return $true }
[void][Wn2]::EnumWindows($cb, [IntPtr]::Zero)
if ($found -ne [IntPtr]::Zero) {
  $after = if ($Off) { [IntPtr](-2) } else { [IntPtr](-1) }
  [void][Wn2]::SetWindowPos($found, $after, 0, 0, 0, 0, 0x0053)   # NOSIZE|NOMOVE|NOACTIVATE|SHOWWINDOW
  "tile ok"
} else {
  $names = New-Object Collections.ArrayList
  $cb2 = [Wn2+EnumProc]{ param($h, $l) if ([Wn2]::IsWindowVisible($h)) { $s = New-Object Text.StringBuilder 256; [void][Wn2]::GetWindowText($h, $s, 256); if ($s.Length) { [void]$names.Add($s.ToString()) } }; return $true }
  [void][Wn2]::EnumWindows($cb2, [IntPtr]::Zero)
  "tile: not found. want=[$Title] have=" + (($names | Select-Object -First 8 | ForEach-Object { $_.Substring(0, [Math]::Min(24, $_.Length)) }) -join ' | ')
}
