# Recalculate an .xlsx in real Excel (Windows), auto-fit wrapped rows, save in place,
# optionally export a PDF. A watchdog kills ONLY the Excel instance this script started.
# usage: python -I recalc_com.py <book.xlsx> [out.pdf] [timeout_s=90]
import sys, os, threading, ctypes, subprocess
import win32com.client as w  # win32process is blocked by Smart App Control on this machine: use ctypes instead

src = os.path.normpath(sys.argv[1])
pdf = os.path.normpath(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 90

xl = w.DispatchEx("Excel.Application")  # DispatchEx = new instance; Dispatch would grab the user's open Excel
xl.Visible = False
xl.DisplayAlerts = False
pid = ctypes.c_ulong()
ctypes.windll.user32.GetWindowThreadProcessId(xl.Hwnd, ctypes.byref(pid))
dog = threading.Timer(timeout, lambda: subprocess.run(["taskkill", "/F", "/PID", str(pid.value)], capture_output=True))
dog.start()
try:
    wb = xl.Workbooks.Open(src)
    xl.CalculateFull()
    for ws in wb.Worksheets:
        ws.UsedRange.Rows.AutoFit()
    wb.Save()
    print("saved", src)
    if pdf:
        wb.ExportAsFixedFormat(0, pdf)
        print("pdf", pdf)
    wb.Close(False)
finally:
    dog.cancel()
    try:
        xl.Quit()
    except Exception:
        pass
