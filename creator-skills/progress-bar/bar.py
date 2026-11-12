# พิมพ์แถบความคืบหน้า 10 ช่อง สีไล่เหลืองไปเขียว
# ใช้: python bar.py <done> <total> [--label-file <path>] [--label <ascii text>]
import io
import sys

CELLS = 10
YELLOW, GREEN, EMPTY = "\U0001F7E8", "\U0001F7E9", "⬜"


def bar(done, total, label=""):
    if total <= 0:
        raise SystemExit("total ต้องมากกว่า 0")
    done = max(0, min(done, total))
    filled = round(CELLS * done / total)
    # ‼ งานที่ยังไม่ครบห้ามแสดงเต็มแถบ แม้ปัดเศษแล้วได้ 10 ช่อง
    if done < total:
        filled = min(filled, CELLS - 1)
    cells = "".join((YELLOW if i < CELLS // 2 else GREEN) if i < filled else EMPTY for i in range(CELLS))
    pct = int(100 * done / total)
    out = f"{cells} {pct}% · ขั้น {done}/{total}"
    return out + (f" · {label}" if label else "")


if __name__ == "__main__":
    a = sys.argv[1:]
    label = ""
    if "--label-file" in a:
        label = io.open(a[a.index("--label-file") + 1], encoding="utf-8").read().strip()
    elif "--label" in a:
        label = a[a.index("--label") + 1]
    sys.stdout.buffer.write((bar(int(a[0]), int(a[1]), label) + "\n").encode("utf-8"))
