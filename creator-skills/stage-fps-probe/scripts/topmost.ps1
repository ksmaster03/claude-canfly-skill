# test helper: bring the first visible window whose title contains $Title to the front; print the foreground title
param([string]$Title = 'Page Title', [switch]$Report)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class Wn {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e);
}
"@
$found = [IntPtr]::Zero
$cb = [Wn+EnumProc]{ param($h, $l)
  if ([Wn]::IsWindowVisible($h)) { $s = New-Object Text.StringBuilder 256; [void][Wn]::GetWindowText($h, $s, 256)
    if ($s.ToString().Contains($Title)) { $script:found = $h; return $false } }
  return $true }
[void][Wn]::EnumWindows($cb, [IntPtr]::Zero)
if (-not $Report -and $found -ne [IntPtr]::Zero) {
  [void][Wn]::SetWindowPos($found, [IntPtr](-1), 0, 0, 0, 0, 0x0043)   # HWND_TOPMOST, NOMOVE|NOSIZE|SHOWWINDOW
  [Wn]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [Wn]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)   # ALT tap lifts the foreground lock
  [void][Wn]::SetForegroundWindow($found)
}
$s = New-Object Text.StringBuilder 256; [void][Wn]::GetWindowText([Wn]::GetForegroundWindow(), $s, 256)
"found=$($found -ne [IntPtr]::Zero) foreground=$($s.ToString())"
