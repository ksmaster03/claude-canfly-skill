# -*- coding: utf-8 -*-
# 20/10/2026 แปลงภาพจาก chatgpt-bridge (1672x941) เป็น jpg 1920x1080 ใน img/
import glob, os
from PIL import Image
for f in sorted(glob.glob('__PROJECT__/gen/*.png')):
    o = '__PROJECT__/img/' + os.path.basename(f)[:-4] + '.jpg'
    if os.path.exists(o) and os.path.getmtime(o) > os.path.getmtime(f): continue
    im = Image.open(f).convert('RGB')
    s = max(1920 / im.width, 1080 / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - 1920) // 2, (im.height - 1080) // 2
    im.crop((l, t, l + 1920, t + 1080)).save(o, quality=92)
    print('ok', os.path.basename(o))
