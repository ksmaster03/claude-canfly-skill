# -*- coding: utf-8 -*-
"""
takeoff_lib.py — เครื่องมือถอดแบบรายแผ่น + ออกไฟล์ Excel  (craft-boq step 3-6)

ใช้:
    import sys; sys.path.insert(0, r"<SKILL_DIR>/scripts")
    from takeoff_lib import Takeoff

    t = Takeoff()
    t.carcass("B3", W=2000, H=1050, D=450, ncomp=5, comp_w=370, n_shelf=2)
    t.P("B3", "หน้าบาน", "HMR18", "GWE5101", "PW201P", 390, 1090, 18, 5, edge=2*(390+1090))
    t.plinth("B3", W=2000, D=450)
    t.hw("B3", "บานพับ No Soft Close", "ตัว", 15)
    t.build("out/01_Cutting_List_and_Pricing.xlsx",
            items={"B3": ("ตู้เตี้ยเก็บแค็ตตาล็อค", "2000 x 450 x 1200 มม.")})

ต้องมี : pip install openpyxl
"""
import math
from collections import defaultdict

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

SHEET_W, SHEET_H = 1.220, 2.440
SHEET_M2 = SHEET_W * SHEET_H          # 2.9768 ตร.ม.

# ---------------------------------------------------------------- สไตล์
TH = Font(name="Tahoma", size=10, bold=True, color="FFFFFF")
TX = Font(name="Tahoma", size=10)
TBD = Font(name="Tahoma", size=10, bold=True)
HDR = PatternFill("solid", fgColor="1F4E79")
SUBF = PatternFill("solid", fgColor="DDEBF7")
WARN = PatternFill("solid", fgColor="FFF2CC")
_t = Side(style="thin", color="B0B0B0")
BD = Border(left=_t, right=_t, top=_t, bottom=_t)
CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
LFT = Alignment(horizontal="left", vertical="center", wrap_text=True)

# ---------------------------------------------------------------- อัตราตั้งต้น
#   ปรับได้ตอนสร้าง Takeoff(rates={...})  ค่าเหล่านี้เป็นค่าประมาณตลาด กทม.
DEFAULT_RATES = [
    ("SEC", "วัสดุแผ่น (ราคา/แผ่น 1220x2440)", "", "", ""),
    ("HMR18",    "ไม้ HMR หนา 18 มม.",   "แผ่น", 1250, ""),
    ("MDF16",    "ไม้ MDF หนา 16 มม.",   "แผ่น",  780, ""),
    ("MDF5",     "ไม้ MDF หนา 5 มม.",    "แผ่น",  340, ""),
    ("PLY6",     "ไม้อัดยาง หนา 6 มม.",  "แผ่น",  470, "แผงหลัง / CASE B"),
    ("SEC", "ผิวลามิเนต (ราคา/แผ่น 1220x2440)", "", "", ""),
    ("GSB107",   "HPL สีขาว (ผิวนอก)",        "แผ่น", 1150, ""),
    ("GWE5101",  "HPL ลายไม้",                "แผ่น", 1150, "ต้องล็อกทิศลาย"),
    ("PW201P",   "ลามิเนตขาว (ภายในตู้)",     "แผ่น",  950, ""),
    ("1401",     "ลามิเนตดำ",                 "แผ่น",  950, ""),
    ("PAT5594",  "ลามิเนตลายหิน",             "แผ่น", 1250, ""),
    ("SEC", "งานอื่น", "", "", ""),
    ("EDGE",     "ขอบ PVC 1 มม.",                    "เมตร",   14, ""),
    ("SPRAY_BK", "งานพ่นสี",                          "ตร.ม.",  380, ""),
    ("FELT3",    "พรมอัด 3 มม.",                      "ตร.ม.",  190, ""),
    ("STONE",    "หินสังเคราะห์ 18 มม. พร้อมติดตั้ง", "ตร.ม.", 4800, ""),
    ("FRAME",    "ไม้เนื้อแข็งทำเคร่า",               "เมตร",   70, "ใช้เฉพาะ CASE B"),
    ("SEC", "ฮาร์ดแวร์", "", "", ""),
    ("HW_HINGE", "บานพับ",              "ตัว",  38, ""),
    ("HW_LOCK",  "กุญแจล็อคหน้าบาน",    "ชุด",  95, ""),
    ("HW_LEG",   "ขาปรับระดับ",         "ตัว",  22, ""),
    ("HW_PIN",   "ตัวรองชั้นปรับระดับ", "ตัว",   4, ""),
    ("HW_SLIDE", "รางลิ้นชัก",          "ชุด", 145, ""),
    ("HW_OTHER", "ฮาร์ดแวร์อื่น",       "ชุด",   0, ""),
    ("SEC", "ตัวคูณ / เปอร์เซ็นต์", "", "", ""),
    ("W_SUB",   "เผื่อเศษ แผ่นซับสเตรต",              "%",  10, ""),
    ("W_LAM",   "เผื่อเศษ ลามิเนตทั่วไป",             "%",  10, ""),
    ("W_WOOD",  "เผื่อเศษ ลามิเนตลายไม้/ลายหิน",      "%",  15, "ล็อกทิศลายต่อเนื่อง"),
    ("W_EDGE",  "เผื่อเศษ ขอบ PVC",                   "%",   5, ""),
    ("LAB_A",   "ค่าแรงผลิต+ประกอบ CASE A",           "บาท/ตร.ม.แผ่น", 480, ""),
    ("LAB_B",   "ค่าแรงผลิต+ประกอบ CASE B (โครงเคร่า)", "บาท/ตร.ม.แผ่น", 820, ""),
    ("LAB_SLOT","ค่าแรงงานพิเศษต่อหน่วย (เช่น ช่องเก็บแผ่น)", "บาท/หน่วย", 18, ""),
    ("FRAME_M", "ความยาวเคร่าต่อพื้นที่ CASE B",      "ม./ตร.ม.", 5.0, "เคร่า @400 มม. 2 ทาง"),
    ("INSTALL", "ค่าขนส่ง + ติดตั้ง",                 "%",  12, "ของต้นทุนตรง"),
    ("OH",      "ค่าดำเนินการโรงงาน",                 "%",  10, ""),
    ("PROFIT",  "กำไร",                               "%",  15, ""),
]

HW_KEY = {
    "บานพับ": "HW_HINGE", "กุญแจ": "HW_LOCK", "ขาปรับระดับ": "HW_LEG",
    "ตัวรองชั้น": "HW_PIN", "รางลิ้นชัก": "HW_SLIDE",
}


def _hw_key(item):
    for frag, k in HW_KEY.items():
        if frag in item:
            return k
    return "HW_OTHER"


class Takeoff:
    """เก็บรายการแผ่นและฮาร์ดแวร์ แล้วออกเป็นไฟล์ Excel พร้อมสูตร"""

    def __init__(self, substrates=("HMR18", "MDF16", "MDF5", "PLY6"),
                 laminates=("GSB107", "GWE5101", "PW201P", "1401", "PAT5594"),
                 rates=None, t_carcass=18, t_back=6, shelf_inset=30):
        self.SUB = list(substrates)
        self.LAM = list(laminates)
        self.rates = list(rates or DEFAULT_RATES)
        self.T = t_carcass
        self.TB = t_back
        self.INSET = shelf_inset
        self.panels = []
        self.hardware = []

    # ------------------------------------------------------------ ป้อนข้อมูล
    def P(self, code, part, mat, fa, fb, L, W, thk, qty, edge=0, note=""):
        """เพิ่มแผ่น 1 ชนิด : fa/fb = รหัสผิวหน้า A/B ('-' = ไม่ปิดผิว), edge = มม./ชิ้น"""
        self.panels.append(dict(code=code, part=part, mat=mat, fa=fa, fb=fb,
                                L=round(L), W=round(W), thk=thk, qty=qty,
                                edge=edge, note=note))

    def carcass(self, code, W, H, D, ncomp, comp_w, ext_face="GSB107",
                int_face="PW201P", n_shelf=0, shelf_qty=None, back=True,
                mat=None, prefix=""):
        """โครงตู้มาตรฐาน : แผงตั้ง(ช่อง+1) / บน-ล่าง(ช่องละ2) / หลัง / ชั้นปรับระดับ"""
        mat = mat or ("HMR18" if self.T == 18 else "MDF16")
        nv = ncomp + 1
        self.P(code, f"{prefix}แผงตั้งข้าง+กั้น", mat, ext_face, int_face,
               H, D, self.T, nv, edge=H, note=f"{ncomp} ช่อง -> {nv} แผง")
        self.P(code, f"{prefix}แผงบน-ล่าง", mat, ext_face, int_face,
               comp_w, D, self.T, ncomp * 2, edge=comp_w)
        if back:
            self.P(code, f"{prefix}แผงหลัง", "PLY6", int_face, "-", W, H, self.TB, 1)
        if n_shelf:
            self.P(code, f"{prefix}ชั้นปรับระดับ", mat, ext_face, int_face,
                   comp_w, D - self.INSET, self.T,
                   shelf_qty if shelf_qty else ncomp * n_shelf, edge=comp_w)

    def plinth(self, code, W, D, h=100, n_side=2, face="GSB107", mat=None):
        mat = mat or ("HMR18" if self.T == 18 else "MDF16")
        self.P(code, "ตีนตู้ (หน้า)", mat, face, "-", W, h, self.T, 1, edge=W)
        self.P(code, "ตีนตู้ (ข้าง)", mat, face, "-", D, h, self.T, n_side, edge=D)

    def hw(self, code, item, unit, qty, note=""):
        self.hardware.append(dict(code=code, item=item, unit=unit, qty=qty, note=note))

    # ------------------------------------------------------------ รวมยอด
    def aggregate(self):
        sub = defaultdict(lambda: defaultdict(float))
        lam = defaultdict(lambda: defaultdict(float))
        edge, spray, felt, stone, npan = (defaultdict(float), defaultdict(float),
                                          defaultdict(float), defaultdict(float),
                                          defaultdict(int))
        for p in self.panels:
            a = p["L"] * p["W"] * p["qty"] / 1e6
            c, m = p["code"], p["mat"]
            npan[c] += p["qty"]
            if m in self.SUB:      sub[c][m] += a
            elif m == "FELT3":     felt[c] += a
            elif m == "STONE":     stone[c] += a
            for f in (p["fa"], p["fb"]):
                if f in self.LAM:      lam[c][f] += a
                elif f == "SPRAY_BK":  spray[c] += a
            edge[c] += p["edge"] * p["qty"] / 1000.0
        return dict(sub=sub, lam=lam, edge=edge, spray=spray,
                    felt=felt, stone=stone, npan=npan)

    def price(self, code, case="A", slots=0, rv=None):
        """คำนวณราคาด้วย Python (ใช้ตรวจยอดกับสูตรใน Excel)"""
        rv = rv or {k: v for k, _n, _u, v, _c in self.rates if k != "SEC"}
        g = self.aggregate()
        sub, lam = g["sub"][code], g["lam"][code]
        tot = sum(sub.values())
        if case == "A":
            s = sum(sub[m] * (1 + rv["W_SUB"] / 100) / SHEET_M2 * rv[m] for m in self.SUB)
            fr, lb = 0, tot * rv["LAB_A"]
        else:
            s = sub["HMR18"] * 2 * (1 + rv["W_SUB"] / 100) / SHEET_M2 * rv["PLY6"]
            s += sum(sub[m] * (1 + rv["W_SUB"] / 100) / SHEET_M2 * rv[m]
                     for m in self.SUB if m != "HMR18")
            fr = sub["HMR18"] * rv["FRAME_M"] * rv["FRAME"]
            lb = sub["HMR18"] * rv["LAB_B"] + (tot - sub["HMR18"]) * rv["LAB_A"]
        lb += slots * rv["LAB_SLOT"]
        l = sum(lam[x] * (1 + (rv["W_WOOD"] if x in ("GWE5101", "PAT5594")
                               else rv["W_LAM"]) / 100) / SHEET_M2 * rv[x]
                for x in self.LAM)
        e = g["edge"][code] * (1 + rv["W_EDGE"] / 100) * rv["EDGE"]
        sp = (g["spray"][code] * rv["SPRAY_BK"] + g["felt"][code] * rv["FELT3"]
              + g["stone"][code] * rv["STONE"])
        h = sum(x["qty"] * rv[_hw_key(x["item"])] for x in self.hardware if x["code"] == code)
        d = s + l + e + sp + fr + h + lb
        i = d * rv["INSTALL"] / 100
        o = (d + i) * rv["OH"] / 100
        pf = (d + i + o) * rv["PROFIT"] / 100
        return round(d + i + o + pf, -1)

    # ------------------------------------------------------------ ออกไฟล์
    def build(self, out, items, slots=None, title="ถอดแบบและประเมินราคา",
              case_b=True, notes=None):
        """items = {code: (ชื่อรายการ, ขนาด)}  ตามลำดับที่ต้องการแสดง"""
        slots = slots or {}
        g = self.aggregate()
        sub, lam = g["sub"], g["lam"]
        codes = list(items.keys())
        wb = openpyxl.Workbook()

        # ---- RATE
        ws = wb.active; ws.title = "RATE"
        ws["A1"] = f"{title} — ตารางราคาหน่วย (แก้คอลัมน์ D ที่เดียว ทุกชีตอัปเดตอัตโนมัติ)"
        ws["A1"].font = Font(name="Tahoma", size=12, bold=True)
        ws["A2"] = "⚠ ตัวเลขตั้งต้นเป็นค่าประมาณ ต้องให้ฝ่ายจัดซื้อ/โรงงานยืนยันก่อนยื่นเสนอราคา"
        ws["A2"].font = Font(name="Tahoma", size=10, bold=True, color="C00000")
        for i, h in enumerate(["KEY", "รายการ", "หน่วย", "ราคา/อัตรา", "หมายเหตุ"], 1):
            c = ws.cell(4, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
        rrow, r = {}, 5
        for k, name, unit, val, note in self.rates:
            if k == "SEC":
                ws.cell(r, 1, name).font = TBD
                for cc in range(1, 6):
                    ws.cell(r, cc).fill = SUBF; ws.cell(r, cc).border = BD
                r += 1; continue
            ws.cell(r, 1, k).font = TX
            ws.cell(r, 2, name).font = TX
            ws.cell(r, 3, unit).font = TX; ws.cell(r, 3).alignment = CEN
            ws.cell(r, 4, val).font = TBD; ws.cell(r, 4).fill = WARN
            ws.cell(r, 4).number_format = "#,##0.00"
            ws.cell(r, 5, note).font = TX
            for cc in range(1, 6): ws.cell(r, cc).border = BD
            rrow[k] = r; r += 1
        for col, w in zip("ABCDE", [12, 44, 18, 14, 42]):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A5"
        R = lambda k: f"RATE!$D${rrow[k]}"

        # ---- CUTLIST
        ws = wb.create_sheet("CUTLIST")
        hdr = ["Code", "รายการแผ่น", "วัสดุ", "ผิวหน้า A", "ผิวหน้า B", "ยาว (มม.)",
               "กว้าง (มม.)", "หนา (มม.)", "จำนวน", "พื้นที่รวม (ตร.ม.)",
               "ขอบปิดรวม (ม.)", "หมายเหตุ"]
        for i, h in enumerate(hdr, 1):
            c = ws.cell(1, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
        r = 2
        for p in self.panels:
            for i, v in enumerate([p["code"], p["part"], p["mat"], p["fa"], p["fb"],
                                   p["L"], p["W"], p["thk"], p["qty"]], 1):
                c = ws.cell(r, i, v); c.font = TX; c.border = BD
                if i != 2: c.alignment = CEN
            ws.cell(r, 10, f"=F{r}*G{r}*I{r}/1000000").number_format = "#,##0.000"
            ws.cell(r, 11, round(p["edge"] * p["qty"] / 1000.0, 2)).number_format = "#,##0.00"
            ws.cell(r, 12, p["note"])
            for i in (10, 11, 12): ws.cell(r, i).font = TX; ws.cell(r, i).border = BD
            r += 1
        for col, w in zip("ABCDEFGHIJKL", [7, 42, 10, 12, 12, 11, 11, 9, 8, 15, 15, 28]):
            ws.column_dimensions[col].width = w
        ws.auto_filter.ref = f"A1:L{r-1}"; ws.freeze_panes = "A2"

        # ---- QTY
        ws = wb.create_sheet("QTY")
        qcols = (["Code", "รายการ", "ขนาด"] + [f"ซับ:{m}" for m in self.SUB]
                 + [f"ผิว:{l}" for l in self.LAM]
                 + ["ขอบ PVC (ม.)", "พ่นสี (ตร.ม.)", "พรมอัด (ตร.ม.)", "หิน (ตร.ม.)",
                    "พื้นที่แผ่นรวม (ตร.ม.)", "พื้นที่ HMR18 (ตร.ม.)", "หน่วยงานพิเศษ"])
        for i, h in enumerate(qcols, 1):
            c = ws.cell(1, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
        qrow = {}
        for j, code in enumerate(codes, start=2):
            ws.cell(j, 1, code).font = TBD; ws.cell(j, 1).alignment = CEN
            ws.cell(j, 2, items[code][0]).font = TX
            ws.cell(j, 3, items[code][1]).font = TX
            col = 4
            vals = ([sub[code][m] for m in self.SUB] + [lam[code][l] for l in self.LAM]
                    + [g["edge"][code], g["spray"][code], g["felt"][code], g["stone"][code],
                       sum(sub[code].values()), sub[code]["HMR18"]])
            for v in vals:
                ws.cell(j, col, round(v, 3)).number_format = "#,##0.000"; col += 1
            ws.cell(j, col, slots.get(code, 0)).number_format = "#,##0"
            for i in range(1, len(qcols) + 1):
                ws.cell(j, i).border = BD
                if i > 3: ws.cell(j, i).font = TX; ws.cell(j, i).alignment = CEN
            qrow[code] = j
        for i in range(1, len(qcols) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 8 if i == 1 else (34 if i <= 3 else 15)
        ws.freeze_panes = "D2"
        Q = {c: {h: f"QTY!${get_column_letter(i)}${qrow[c]}"
                 for i, h in enumerate(qcols, 1)} for c in codes}

        # ---- HARDWARE
        ws = wb.create_sheet("HARDWARE")
        for i, h in enumerate(["Code", "รายการ", "หน่วย", "จำนวน", "ราคา/หน่วย",
                               "รวม (บาท)", "หมายเหตุ"], 1):
            c = ws.cell(1, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
        r = 2
        for h in self.hardware:
            ws.cell(r, 1, h["code"]).alignment = CEN
            ws.cell(r, 2, h["item"])
            ws.cell(r, 3, h["unit"]).alignment = CEN
            ws.cell(r, 4, h["qty"]).alignment = CEN
            ws.cell(r, 5, f"={R(_hw_key(h['item']))}").number_format = "#,##0.00"
            ws.cell(r, 6, f"=D{r}*E{r}").number_format = "#,##0.00"
            ws.cell(r, 7, h["note"])
            for i in range(1, 8): ws.cell(r, i).font = TX; ws.cell(r, i).border = BD
            r += 1
        last_hw = max(r - 1, 2)
        for col, w in zip("ABCDEFG", [8, 42, 10, 10, 14, 16, 40]):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A2"
        hwsum = lambda c: f'SUMIF(HARDWARE!$A$2:$A${last_hw},"{c}",HARDWARE!$F$2:$F${last_hw})'

        # ---- PRICE_A / PRICE_B
        def price_sheet(name, case):
            ws = wb.create_sheet(name)
            ws["A1"] = ("CASE A — สเปกตาม BOQ (แผ่นสำเร็จ ปิดลามิเนต)" if case == "A"
                        else "CASE B — สเปกตามแบบ (โครงเคร่าไม้เนื้อแข็ง + กรุไม้อัด 6 มม.)")
            ws["A1"].font = Font(name="Tahoma", size=12, bold=True, color="1F4E79")
            cols = ["Code", "รายการ", "ขนาด", "ค่าแผ่นซับสเตรต", "ค่าลามิเนต", "ค่าขอบ PVC",
                    "งานพิเศษ", "ค่าเคร่าไม้", "ฮาร์ดแวร์", "ค่าแรงผลิต", "รวมต้นทุนตรง",
                    "ขนส่ง+ติดตั้ง", "OH", "กำไร", "ราคาเสนอ/ชุด (บาท)"]
            for i, h in enumerate(cols, 1):
                c = ws.cell(3, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
            for j, code in enumerate(codes, start=4):
                q = Q[code]
                ws.cell(j, 1, code).font = TBD; ws.cell(j, 1).alignment = CEN
                ws.cell(j, 2, items[code][0]).font = TX
                ws.cell(j, 3, items[code][1]).font = TX
                if case == "A":
                    parts = [f"{q[f'ซับ:{m}']}*(1+{R('W_SUB')}/100)/{SHEET_M2}*{R(m)}"
                             for m in self.SUB]
                else:
                    parts = [f"{q['ซับ:HMR18']}*2*(1+{R('W_SUB')}/100)/{SHEET_M2}*{R('PLY6')}"]
                    parts += [f"{q[f'ซับ:{m}']}*(1+{R('W_SUB')}/100)/{SHEET_M2}*{R(m)}"
                              for m in self.SUB if m != "HMR18"]
                ws.cell(j, 4, "=" + "+".join(parts))
                ws.cell(j, 5, "=" + "+".join(
                    f"{q[f'ผิว:{l}']}*(1+{R('W_WOOD') if l in ('GWE5101','PAT5594') else R('W_LAM')}"
                    f"/100)/{SHEET_M2}*{R(l)}" for l in self.LAM))
                ws.cell(j, 6, f"={q['ขอบ PVC (ม.)']}*(1+{R('W_EDGE')}/100)*{R('EDGE')}")
                ws.cell(j, 7, f"={q['พ่นสี (ตร.ม.)']}*{R('SPRAY_BK')}"
                              f"+{q['พรมอัด (ตร.ม.)']}*{R('FELT3')}"
                              f"+{q['หิน (ตร.ม.)']}*{R('STONE')}")
                ws.cell(j, 8, 0 if case == "A"
                        else f"={q['ซับ:HMR18']}*{R('FRAME_M')}*{R('FRAME')}")
                ws.cell(j, 9, f"={hwsum(code)}")
                if case == "A":
                    lab = f"={q['พื้นที่แผ่นรวม (ตร.ม.)']}*{R('LAB_A')}"
                else:
                    lab = (f"={q['พื้นที่ HMR18 (ตร.ม.)']}*{R('LAB_B')}"
                           f"+({q['พื้นที่แผ่นรวม (ตร.ม.)']}-{q['พื้นที่ HMR18 (ตร.ม.)']})"
                           f"*{R('LAB_A')}")
                ws.cell(j, 10, lab + f"+{q['หน่วยงานพิเศษ']}*{R('LAB_SLOT')}")
                ws.cell(j, 11, f"=SUM(D{j}:J{j})")
                ws.cell(j, 12, f"=K{j}*{R('INSTALL')}/100")
                ws.cell(j, 13, f"=(K{j}+L{j})*{R('OH')}/100")
                ws.cell(j, 14, f"=(K{j}+L{j}+M{j})*{R('PROFIT')}/100")
                ws.cell(j, 15, f"=ROUND(K{j}+L{j}+M{j}+N{j},-1)")
                for i in range(4, 16):
                    ws.cell(j, i).number_format = "#,##0"; ws.cell(j, i).font = TX
                ws.cell(j, 15).font = TBD
                for i in range(1, 16): ws.cell(j, i).border = BD
            tr = 4 + len(codes)
            ws.cell(tr, 2, "รวมทั้งสิ้น (ไม่รวม VAT)").font = TBD
            for i in range(4, 16):
                L_ = get_column_letter(i)
                ws.cell(tr, i, f"=SUM({L_}4:{L_}{tr-1})")
                ws.cell(tr, i).number_format = "#,##0"; ws.cell(tr, i).font = TBD
            for i in range(1, 16): ws.cell(tr, i).border = BD; ws.cell(tr, i).fill = SUBF
            for col, w in zip("ABC", [8, 36, 40]): ws.column_dimensions[col].width = w
            for i in range(4, 16): ws.column_dimensions[get_column_letter(i)].width = 15
            ws.freeze_panes = "D4"
            return tr

        ta = price_sheet("PRICE_A", "A")
        tb = price_sheet("PRICE_B", "B") if case_b else None

        # ---- COMPARE
        if case_b:
            ws = wb.create_sheet("COMPARE")
            ws["A1"] = "เปรียบเทียบราคา CASE A (ตาม BOQ) กับ CASE B (ตามแบบ)"
            ws["A1"].font = Font(name="Tahoma", size=12, bold=True, color="1F4E79")
            for i, h in enumerate(["Code", "รายการ", "CASE A (บาท)", "CASE B (บาท)",
                                   "ส่วนต่าง (บาท)", "ส่วนต่าง (%)"], 1):
                c = ws.cell(3, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
            for j, code in enumerate(codes, start=4):
                ws.cell(j, 1, code).font = TBD; ws.cell(j, 1).alignment = CEN
                ws.cell(j, 2, items[code][0]).font = TX
                ws.cell(j, 3, f"=PRICE_A!O{j}").number_format = "#,##0"
                ws.cell(j, 4, f"=PRICE_B!O{j}").number_format = "#,##0"
                ws.cell(j, 5, f"=D{j}-C{j}").number_format = "#,##0"
                ws.cell(j, 6, f"=IF(C{j}=0,0,(D{j}-C{j})/C{j})").number_format = "0.0%"
                for i in range(1, 7): ws.cell(j, i).border = BD; ws.cell(j, i).font = TX
            tr = 4 + len(codes)
            ws.cell(tr, 2, "รวม").font = TBD
            ws.cell(tr, 3, f"=PRICE_A!O{ta}").number_format = "#,##0"
            ws.cell(tr, 4, f"=PRICE_B!O{tb}").number_format = "#,##0"
            ws.cell(tr, 5, f"=D{tr}-C{tr}").number_format = "#,##0"
            ws.cell(tr, 6, f"=IF(C{tr}=0,0,(D{tr}-C{tr})/C{tr})").number_format = "0.0%"
            for i in range(1, 7): ws.cell(tr, i).border = BD; ws.cell(tr, i).font = TBD; ws.cell(tr, i).fill = SUBF
            for col, w in zip("ABCDEF", [8, 40, 16, 16, 16, 14]):
                ws.column_dimensions[col].width = w

        # ---- MATERIAL
        ws = wb.create_sheet("MATERIAL")
        ws["A1"] = "สรุปปริมาณวัสดุสั่งซื้อ (CASE A)"
        ws["A1"].font = Font(name="Tahoma", size=12, bold=True, color="1F4E79")
        for i, h in enumerate(["วัสดุ", "ปริมาณสุทธิ", "เผื่อเศษ %", "รวมเศษ",
                               "จำนวนแผ่น 1220x2440 / หน่วย", "ราคา/หน่วย", "รวม (บาท)"], 1):
            c = ws.cell(3, i, h); c.font = TH; c.fill = HDR; c.alignment = CEN; c.border = BD
        r = 4
        for key in self.SUB + self.LAM:
            net = (sum(sub[c][key] for c in codes) if key in self.SUB
                   else sum(lam[c][key] for c in codes))
            if net <= 0: continue
            wk = "W_SUB" if key in self.SUB else ("W_WOOD" if key in ("GWE5101", "PAT5594") else "W_LAM")
            ws.cell(r, 1, key).font = TX
            ws.cell(r, 2, round(net, 3)).number_format = "#,##0.000"
            ws.cell(r, 3, f"={R(wk)}").number_format = "0"
            ws.cell(r, 4, f"=B{r}*(1+C{r}/100)").number_format = "#,##0.000"
            ws.cell(r, 5, f"=ROUNDUP(D{r}/{SHEET_M2},0)").number_format = "#,##0"
            ws.cell(r, 6, f"={R(key)}").number_format = "#,##0"
            ws.cell(r, 7, f"=E{r}*F{r}").number_format = "#,##0"
            for i in range(1, 8): ws.cell(r, i).border = BD; ws.cell(r, i).font = TX
            r += 1
        for label, key, val in [("ขอบ PVC (ม.)", "EDGE", sum(g["edge"].values())),
                                ("งานพ่นสี (ตร.ม.)", "SPRAY_BK", sum(g["spray"].values())),
                                ("พรมอัด (ตร.ม.)", "FELT3", sum(g["felt"].values())),
                                ("หินสังเคราะห์ (ตร.ม.)", "STONE", sum(g["stone"].values()))]:
            if val <= 0: continue
            ws.cell(r, 1, label).font = TX
            ws.cell(r, 2, round(val, 2)).number_format = "#,##0.00"
            ws.cell(r, 3, f"={R('W_EDGE')}" if key == "EDGE" else 0).number_format = "0"
            ws.cell(r, 4, f"=B{r}*(1+C{r}/100)").number_format = "#,##0.00"
            ws.cell(r, 5, "-").alignment = CEN
            ws.cell(r, 6, f"={R(key)}").number_format = "#,##0"
            ws.cell(r, 7, f"=D{r}*F{r}").number_format = "#,##0"
            for i in range(1, 8): ws.cell(r, i).border = BD; ws.cell(r, i).font = TX
            r += 1
        for col, w in zip("ABCDEFG", [34, 18, 12, 18, 26, 14, 16]):
            ws.column_dimensions[col].width = w

        # ---- ASSUMPTION
        ws = wb.create_sheet("ASSUMPTION")
        ws["A1"] = "สมมติฐานที่ใช้ในการถอดแบบ"
        ws["A1"].font = Font(name="Tahoma", size=12, bold=True, color="C00000")
        base = [
            "มิติทั้งหมดอ่านจากรูป FRONT และ SECTION ในแบบ ไม่มีการสเกลจากรูป",
            f"ความหนาแผ่นโครงตู้ {self.T} มม. / แผงหลัง {self.TB} มม. / ชั้นวางร่นจากขอบหน้า {self.INSET} มม.",
            "เผื่อเศษ: ซับสเตรต 10% · ลามิเนตทั่วไป 10% · ลามิเนตลายไม้/ลายหิน 15% (ล็อกทิศลาย)",
            "ราคาวัสดุและค่าแรงในชีต RATE เป็นค่าประมาณ ต้องให้ฝ่ายจัดซื้อและโรงงานยืนยันก่อนยื่นเสนอราคา",
            "ยังไม่รวม VAT 7% · งานระบบไฟ · สุขภัณฑ์ · เครื่องใช้ไฟฟ้า · งานรื้อถอน · ค่าทำงานนอกเวลา",
        ]
        for i, n in enumerate(base + list(notes or []), start=3):
            ws.cell(i, 1, f"{i-2}. {n}").font = TX
            ws.cell(i, 1).alignment = LFT
        ws.column_dimensions["A"].width = 150

        wb.save(out)
        return out
