# Check every formula in one or more recalculated .xlsx files has a cached value and no #error.
# With two files (e.g. TH and EN builds of the same model) also reports whether formulas+values match.
# usage: python -I verify_xlsx.py <a.xlsx> [b.xlsx] [--no-thai]   (--no-thai: flag Thai text left in the LAST file)
import sys, re
from openpyxl import load_workbook

args = [a for a in sys.argv[1:] if not a.startswith("--")]
check_thai = "--no-thai" in sys.argv
results = []
bad = False
for path in args:
    vals, errs = {}, []
    f, v = load_workbook(path), load_workbook(path, data_only=True)
    for ws in f.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    x = v[ws.title][c.coordinate].value
                    if x is None or (isinstance(x, str) and x.startswith("#")):
                        errs.append(f"{ws.title}!{c.coordinate} {c.value} -> {x}")
                    vals[(ws.title, c.coordinate)] = (c.value, x)
    print(f"{path}: {len(vals)} formulas, {len(errs)} errors, sheets {f.sheetnames}")
    for e in errs[:50]:
        print("  ", e)
    bad |= bool(errs)
    results.append(vals)
if len(results) == 2:
    same = results[0] == results[1]
    print("formulas+values identical:", same)
    bad |= not same
if check_thai:
    f = load_workbook(args[-1])
    thai = [f"{ws.title}!{c.coordinate}" for ws in f.worksheets for row in ws.iter_rows() for c in row
            if isinstance(c.value, str) and re.search("[฀-๿]", c.value)]
    print("Thai cells left:", thai or "none")
    bad |= bool(thai)
sys.exit(1 if bad else 0)
