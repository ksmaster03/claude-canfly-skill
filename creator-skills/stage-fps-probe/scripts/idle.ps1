Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class W3 { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
[DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
[StructLayout(LayoutKind.Sequential)] public struct LI { public uint cbSize; public uint dwTime; }
[DllImport("user32.dll")] public static extern bool GetLastInputInfo(ref LI i); }
"@
$h=[W3]::GetForegroundWindow(); $s=New-Object Text.StringBuilder 256; [void][W3]::GetWindowText($h,$s,256)
$i=New-Object W3+LI; $i.cbSize=8; [void][W3]::GetLastInputInfo([ref]$i)
"idle=$([math]::Round(([Environment]::TickCount - $i.dwTime)/1000))s fg=$($s.ToString())"
if (Get-Process LogonUI -ErrorAction SilentlyContinue) { 'locked' }
