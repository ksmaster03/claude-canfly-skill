# แก้ป้ายในคลิปเปิดจาก NAT · THE MASTERMIND เป็น NATHAN · THE MASTERMIND โดยไม่แตะไฟล์ต้นฉบับใน vdo/
# ใช้ตัวอักษรจากเฟรมเดียวกันมาเรียงใหม่ ฟอนต์ สี จังหวะเฟดและการเลื่อนจึงตรงของเดิมทุกเฟรม · ทำงานบน yuv420p ตรง ๆ จึงไม่มีการแปลงสี
# ใช้: python deck/patch_clip_name.py --preview   ดูภาพตัวอย่างก่อน
#      python deck/patch_clip_name.py             เขียน deck/media/op.new.mp4
import os, subprocess, sys
import numpy as np
from scipy import ndimage as nd
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), 'vdo', 'source.mp4')
OUT = os.path.join(HERE, 'media', 'op.new.mp4')
PREVIEW = '--preview' in sys.argv
QA = os.path.join(HERE, 'qa')
W, H = 1920, 1080; FS = W * H * 3 // 2
X0, X1, Y0, Y1 = 108, 900, 838, 916      # เลขคู่ทั้งหมด ให้ตรงกับระนาบสีที่ลดความละเอียดครึ่งหนึ่ง
F0, F1 = 50, 96                          # เฟรมที่ป้ายปรากฏ 2.08 ถึง 4.00 วินาที
# ที่มาของตัวอักษร (x เริ่ม, x จบ, เลื่อนกี่พิกเซล) ทุกค่าเลื่อนเป็นเลขคู่ · ช่วงตัวอักษรเท่ากับ 33.75 พิกเซล
PLACE = [(116, 139, 0), (148, 174, 0), (183, 207, 0),      # N A T ที่เดิม
         (352, 375, -134), (148, 174, 102), (116, 139, 168),  # H จาก THE, A กับ N จาก NAT
         (255, 785, 102)]                                  # · THE MASTERMIND เลื่อนขวาสามช่อง


def planes(b):
    y = np.frombuffer(b, np.uint8, W * H).reshape(H, W).astype(np.float32)
    u = np.frombuffer(b, np.uint8, W * H // 4, W * H).reshape(H // 2, W // 2).astype(np.float32)
    v = np.frombuffer(b, np.uint8, W * H // 4, W * H * 5 // 4).reshape(H // 2, W // 2).astype(np.float32)
    return y, u, v


def text_color(b):
    y, u, v = planes(b); r = y[Y0:Y1, X0:X1]; l = r - nd.gaussian_filter(nd.grey_opening(r, size=(9, 9)), 2)
    m = l > l.max() * .82
    my, mx = np.where(m); cy, cx = (my + Y0) // 2, (mx + X0) // 2
    return float(np.median(y[my + Y0, mx + X0])), float(np.median(u[cy, cx])), float(np.median(v[cy, cx]))


def half(a):
    return (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4


def patch(b, col):
    y, u, v = planes(b); ty, tu, tv = col
    r = y[Y0:Y1, X0:X1].copy(); by = nd.gaussian_filter(nd.grey_opening(r, size=(9, 9)), 2)
    # ความทึบของตัวอักษรเทียบกับสีจริง จึงรวมการเฟดไว้แล้ว · คิดเฉพาะในกล่องตัวอักษร ฝุ่นในฉากจะได้ไม่ติดมา
    alpha = np.clip((r - by - 5) / np.maximum(ty - by - 5, 1), 0, 1)
    box = np.zeros_like(alpha)
    box[:, 114 - X0:209 - X0] = 1; box[:, 255 - X0:785 - X0] = 1; alpha *= box
    # ลบของเดิมด้วยพื้นหลังที่ประเมินจากบริเวณรอบ ๆ
    mask = nd.gaussian_filter((nd.grey_dilation(alpha, size=(7, 7)) > .04).astype(np.float32), 1.2)
    ys, xs = slice(Y0, Y1), slice(X0, X1); yc, xc = slice(Y0 // 2, Y1 // 2), slice(X0 // 2, X1 // 2)
    uc, vc = u[yc, xc].copy(), v[yc, xc].copy()
    # สีของตัวอักษรเลอะออกนอกเส้นเพราะระนาบสีละเอียดแค่ครึ่งเดียว จึงเว้นบริเวณรอบตัวอักษรออกตอนเฉลี่ยสีพื้นหลัง ไม่งั้นเหลือคราบแดงที่ตำแหน่งเดิม
    wide = half((nd.grey_dilation(alpha, size=(15, 15)) > .04).astype(np.float32)) > 0
    keep = (~wide).astype(np.float32); wt = np.maximum(nd.gaussian_filter(keep, 9), 1e-3)
    bu, bv = nd.gaussian_filter(uc * keep, 9) / wt, nd.gaussian_filter(vc * keep, 9) / wt
    mc = nd.gaussian_filter(wide.astype(np.float32), .8)
    r = r * (1 - mask) + by * mask; uc = uc * (1 - mc) + bu * mc; vc = vc * (1 - mc) + bv * mc
    # เรียงตัวอักษรใหม่แล้ววาดด้วยสีเดิม
    a = np.zeros_like(alpha)
    for x1, x2, dx in PLACE:
        s = alpha[:, x1 - X0:x2 - X0]; d = a[:, x1 + dx - X0:x2 + dx - X0]
        np.maximum(d, s, out=d)
    ac = half(a)
    r = r * (1 - a) + ty * a; uc = uc * (1 - ac) + tu * ac; vc = vc * (1 - ac) + tv * ac
    y[ys, xs] = r; u[yc, xc] = uc; v[yc, xc] = vc
    return np.concatenate([np.clip(np.rint(p), 0, 255).astype(np.uint8).ravel() for p in (y, u, v)]).tobytes()


def rgb(b):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', '%dx%d' % (W, H), '-colorspace', 'bt709', '-i', '-',
                        '-frames:v', '1', '-vf', 'scale=in_color_matrix=bt709:out_color_matrix=bt709,format=rgb24', '-f', 'rawvideo', '-'], input=b, capture_output=True, check=True)
    return Image.frombytes('RGB', (W, H), p.stdout)


dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE, bufsize=FS * 2)
enc = None
if not PREVIEW:
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', '%dx%d' % (W, H), '-r', '24', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-i', '-',
                            '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-profile:v', 'high', '-level', '4.0', '-pix_fmt', 'yuv420p',
                            '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-c:a', 'copy', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = 0; col = None; buf = []; strips = []; PICK = (54, 58, 66, 80, 90, 92, 94)
while True:
    b = dec.stdout.read(FS)
    if len(b) < FS:
        break
    if n == F0:
        # อ่านสีจากเฟรม 66 ตอนป้ายสว่างเต็มที่ ต้องอ่านล่วงหน้าก่อนเริ่มแก้
        buf = [b]
        for _ in range(F1 - F0):
            buf.append(dec.stdout.read(FS))
        col = text_color(buf[66 - F0]); print('text colour YUV', [round(x) for x in col])
        for i, f in enumerate(buf):
            g = patch(f, col)
            if PREVIEW and F0 + i in PICK:
                a, c = rgb(f), rgb(g); strips.append(a.crop((90, 830, 920, 925))); strips.append(c.crop((90, 830, 920, 925)))
                if F0 + i == 80:
                    c.save(os.path.join(QA, 'clip-patched.png'))
            if enc:
                enc.stdin.write(g)
        n += len(buf)
        if PREVIEW:
            dec.kill(); break
        continue
    if enc:
        enc.stdin.write(b)
    n += 1
if PREVIEW:
    s = Image.new('RGB', (830, len(strips) * 99), (70, 70, 70))
    for i, x in enumerate(strips):
        s.paste(x, (0, i * 99))
    s.save(os.path.join(QA, 'clip-strips.png')); print('preview', len(strips))
else:
    enc.stdin.close(); enc.wait(); dec.wait(); print('frames', n, 'exit', enc.returncode, 'size MB', os.path.getsize(OUT) // 1048576)
