# -*- coding: utf-8 -*-
# ปฏิทินวันขาย/วันสำคัญไทยสำหรับวางแผนโพสต์
# คำนวณเฉพาะวันที่ตายตัวหรือคำนวณได้แน่นอน วันตามจันทรคติไม่เดา พิมพ์รายการให้ไปค้นเว็บแทน
# ใช้: python thai_calendar.py 2026-11-01 2026-11-30 [--csv out.csv]
import csv
import sys
from datetime import date, timedelta

WD = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

FIXED = {
    (1, 1): ("วันขึ้นปีใหม่", "festival"),
    (1, 16): ("วันครู", "festival"),
    (2, 14): ("วาเลนไทน์", "festival"),
    (4, 6): ("วันจักรี", "national"),
    (4, 13): ("สงกรานต์", "festival"),
    (4, 14): ("สงกรานต์", "festival"),
    (4, 15): ("สงกรานต์", "festival"),
    (5, 1): ("วันแรงงาน", "festival"),
    (5, 4): ("วันฉัตรมงคล", "national"),
    (6, 3): ("วันเฉลิมพระชนมพรรษาพระราชินี", "national"),
    (7, 28): ("วันเฉลิมพระชนมพรรษา ร.10", "national"),
    (8, 12): ("วันแม่", "festival"),
    (10, 13): ("วันนวมินทรมหาราช", "caution"),
    (10, 23): ("วันปิยมหาราช", "national"),
    (10, 31): ("ฮาโลวีน", "festival"),
    (12, 5): ("วันพ่อ", "festival"),
    (12, 10): ("วันรัฐธรรมนูญ", "national"),
    (12, 24): ("คริสต์มาสอีฟ", "festival"),
    (12, 25): ("คริสต์มาส", "festival"),
    (12, 31): ("วันสิ้นปี", "festival"),
}

LUNAR = ["ตรุษจีน", "มาฆบูชา", "วิสาขบูชา", "อาสาฬหบูชา", "เข้าพรรษา", "สารทจีน", "เทศกาลกินเจ", "ออกพรรษา", "ลอยกระทง", "วันพระ (งดขายแอลกอฮอล์)"]


def nth_weekday(y, m, weekday, n):
    d = date(y, m, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def events_for(d):
    out = []
    if (d.month, d.day) in FIXED:
        out.append(FIXED[(d.month, d.day)])
    if d.month == d.day:
        out.append(("วันโปรใหญ่ %d.%d" % (d.day, d.month), "shopping") if d.month >= 9 else ("วันเลขเบิ้ล %d.%d" % (d.day, d.month), "shopping"))
    if d.day == 15:
        out.append(("โปรกลางเดือน", "shopping"))
    if d.day >= 25:
        out.append(("ช่วงเงินเดือนออก", "payday"))
    if d == nth_weekday(d.year, 1, 5, 2):
        out.append(("วันเด็ก", "festival"))
    bf = nth_weekday(d.year, 11, 3, 4) + timedelta(days=1)
    if d == bf:
        out.append(("แบล็กฟรายเดย์", "shopping"))
    if d == bf + timedelta(days=3):
        out.append(("ไซเบอร์มันเดย์", "shopping"))
    if d.month == 5 and 10 <= d.day <= 20:
        out.append(("ช่วงเปิดเทอม 1 (โดยประมาณ)", "school"))
    if d.month == 11 and d.day <= 10:
        out.append(("ช่วงเปิดเทอม 2 (โดยประมาณ)", "school"))
    return out


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__ or "ใช้: python thai_calendar.py YYYY-MM-DD YYYY-MM-DD [--csv out.csv]")
        sys.exit(1)
    start, end = date.fromisoformat(args[0]), date.fromisoformat(args[1])
    csv_path = args[args.index("--csv") + 1] if "--csv" in args else None
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    rows = []
    d = start
    while d <= end:
        for label, kind in events_for(d):
            rows.append({"date": d.isoformat(), "be": "%d/%d/%d" % (d.day, d.month, d.year + 543),
                         "weekday": WD[d.weekday()], "label": label, "kind": kind})
        d += timedelta(days=1)
    for r in rows:
        mark = "  ‼ ไม่ควรโพสต์ขาย" if r["kind"] == "caution" else ""
        print("%s  %-9s %-8s %s%s" % (r["be"], r["weekday"], r["kind"], r["label"], mark))
    print("\nวันตามจันทรคติที่ต้องค้นเว็บเองสำหรับช่วงนี้ (ห้ามเดาวัน): " + ", ".join(LUNAR))
    print("ปีนี้มีวันไว้ทุกข์หรือวันงดจำหน่ายพิเศษไหม ให้ค้นข่าวก่อนวางโพสต์ขาย")
    if csv_path:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["date", "be", "weekday", "label", "kind"])
            w.writeheader()
            w.writerows(rows)
        print("เขียน", csv_path, len(rows), "แถว")


if __name__ == "__main__":
    main()
