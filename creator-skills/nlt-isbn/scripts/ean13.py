# -*- coding: utf-8 -*-
"""บาร์โค้ด EAN-13 (Bookland) จากเลข ISBN-13 เป็น SVG ล้วน ไม่พึ่งไลบรารี

    from ean13 import isbn_label_svg
    svg = isbn_label_svg('978-616-8404-05-8')

ป้ายแบบหลังปกหนังสือไทย: พื้นขาว, บรรทัด "ISBN 978-..." ด้านบน, แท่ง + guard ยาว, ตัวเลขใต้แท่ง (ตัวแรกแยกซ้าย)
"""
import re

L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011']
G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111']
R = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100']
PARITY = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL']


def check_digit(d12):
    s = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(d12))
    return str((10 - s % 10) % 10)


def digits_of(isbn):
    d = re.sub(r'\D', '', isbn)
    if len(d) != 13 or check_digit(d[:12]) != d[12]:
        raise ValueError(f'ISBN-13 ไม่ถูกต้อง (check digit): {isbn}')
    return d


def modules(d):
    """คืนสตริง 0/1 ยาว 95 โมดูล และตำแหน่ง guard (ใช้ต่อแท่งให้ยาวกว่า)"""
    par = PARITY[int(d[0])]
    left = ''.join((L if par[i] == 'L' else G)[int(c)] for i, c in enumerate(d[1:7]))
    right = ''.join(R[int(c)] for c in d[7:13])
    bits = '101' + left + '01010' + right + '101'
    guard = set(range(0, 3)) | set(range(45, 50)) | set(range(92, 95))
    return bits, guard


def isbn_label_svg(isbn, module=1.0, bar_h=48.0):
    """SVG หน่วยเป็น 'โมดูล' (ขยายด้วย width/height ของ <img> หรือ CSS ได้เลย) quiet zone 11 โมดูลซ้าย 7 ขวา"""
    d = digits_of(isbn)
    bits, guard = modules(d)
    qz_l, qz_r, top_txt, pad = 11, 7, 11.0, 3.0
    W = qz_l + 95 + qz_r
    y0 = pad + top_txt
    H = y0 + bar_h + 10 + pad
    rects, x = [], qz_l
    i = 0
    while i < 95:
        if bits[i] == '1':
            j = i
            while j < 95 and bits[j] == '1' and ((j in guard) == (i in guard)):
                j += 1
            h = bar_h + (5 if i in guard else 0)
            rects.append(f'<rect x="{qz_l + i}" y="{y0}" width="{j - i}" height="{h}"/>')
            i = j
        else:
            i += 1
    # ใช้ขีดตามเลขที่หอสมุดออกให้ (ความยาวรหัสสำนักพิมพ์ไม่ตายตัว เช่น 616-8404 หรือ 616-588)
    hy = isbn.strip() if isbn.count('-') == 4 else '-'.join([d[:3], d[3:6], d[6:10], d[10:12], d[12]])
    ty = y0 + bar_h + 9.2
    font = "font-family:'OCR B','OCR-B','Consolas','Courier New',monospace"
    txt = [
        f'<text x="{qz_l}" y="{pad + 8}" style="{font};font-size:8.4px" textLength="95" lengthAdjust="spacingAndGlyphs">ISBN {hy}</text>',
        f'<text x="{qz_l - 2}" y="{ty}" text-anchor="end" style="{font};font-size:9px">{d[0]}</text>',
        f'<text x="{qz_l + 3 + 21}" y="{ty}" text-anchor="middle" style="{font};font-size:9px" textLength="38" lengthAdjust="spacingAndGlyphs">{d[1:7]}</text>',
        f'<text x="{qz_l + 50 + 21}" y="{ty}" text-anchor="middle" style="{font};font-size:9px" textLength="38" lengthAdjust="spacingAndGlyphs">{d[7:13]}</text>',
    ]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * module}" height="{H * module}">'
            f'<rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{"".join(rects)}</g><g fill="#000">{"".join(txt)}</g></svg>')


if __name__ == '__main__':
    import sys
    print(isbn_label_svg(sys.argv[1] if len(sys.argv) > 1 else '978-616-8404-05-8'))
