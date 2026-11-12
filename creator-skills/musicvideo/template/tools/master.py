"""Master a track to a loudness target, measuring at every stage.

    python tools/master.py in.wav out.wav [--lufs=-9] [--tp=-1]

Three stages, because collapsing them hides which one is responsible when the
result is wrong:

  1. tone      -- highpass, 3-band split, per-band compression, EQ, glue
  2. drive     -- searched, not guessed: the gain that lands the target LUFS
  3. verify    -- re-measure the file that was actually written

Two things this deliberately does NOT do:

  * It does not boost bass. On most bass-heavy material the low end is already
    the loudest thing in the mix, and adding more makes the limiter duck the
    whole track on every kick. Tightness comes from compressing the low band
    separately and shelving the sub DOWN so the punch band leads.
  * It does not use `t=h` on highpass/lowpass/treble. Without a matching `w`,
    ffmpeg reads the width as 0.7 Hz and the filter becomes a resonator; the
    first attempt at this chain produced a master with the air band +21 dB.
"""
import argparse
import json
import re
import subprocess
import sys

FILTER = """[0:a]volume=-10dB,highpass=f=32:p=2,asplit=3[lo][md][hi];
[lo]lowpass=f=110:p=2,acompressor=level_in=1:threshold=0.03:ratio=3:attack=14:release=110:knee=4:makeup=1.7:detection=rms[loc];
[md]highpass=f=110:p=2,lowpass=f=4000:p=2,acompressor=level_in=1:threshold=0.035:ratio=2.2:attack=18:release=160:knee=6:makeup=1.5:detection=rms[mdc];
[hi]highpass=f=4000:p=2,acompressor=level_in=1:threshold=0.04:ratio=2:attack=5:release=110:knee=6:makeup=1.3:detection=rms[hic];
[loc][mdc][hic]amix=inputs=3:normalize=0[mb];
[mb]bass=f=52:t=q:w=0.8:g=-5.5,
equalizer=f=80:t=q:w=1.0:g=2.0,
equalizer=f=320:t=q:w=1.0:g=-2.0,
equalizer=f=1800:t=q:w=1.2:g=1.8,
equalizer=f=3500:t=q:w=1.1:g=1.6,
treble=f=9000:t=q:w=0.7:g=1.0,
acompressor=level_in=1:threshold=0.06:ratio=1.6:attack=30:release=300:knee=8:makeup=1:detection=rms[out]"""

# alimiter caps SAMPLE peak, but loudness targets are quoted in TRUE peak and
# inter-sample overshoot on dense material runs about 1.1 dB. The ceiling is set
# that much lower so the measured true peak lands where it was asked to.
ISP_HEADROOM_DB = 1.4


def run(args):
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                          errors='replace')


def measure(path):
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af',
             'loudnorm=I=-9:TP=-1:LRA=8:print_format=json', '-f', 'null', '-'])
    m = re.search(r'\{[^{}]*\}', r.stderr, re.S)
    if not m:
        raise SystemExit(f'could not measure {path}')
    d = json.loads(m.group(0))
    return float(d['input_i']), float(d['input_tp']), float(d['input_lra'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--lufs', type=float, default=-9.0)
    ap.add_argument('--tp', type=float, default=-1.0)
    ap.add_argument('--tone', default='_tone.wav')
    # The built-in chain was tuned for one bass-heavy electronic track and is
    # not a default worth trusting: on a rock mix whose sub already sits 3.5 dB
    # BELOW the punch band, its -5.5 dB sub shelf guts the low end. Measure the
    # source with analyse-spectrum.py, then pass a chain built for it.
    ap.add_argument('--chain', default=None, help='filter_complex script to use')
    a = ap.parse_args()

    i0, tp0, lra0 = measure(a.src)
    print(f'source : {i0:7.2f} LUFS  {tp0:6.2f} dBTP  LRA {lra0:.2f}')

    chain = FILTER
    if a.chain:
        chain = open(a.chain, encoding='utf-8').read()
        print('chain  : ' + a.chain)
    with open('_chain.txt', 'w', encoding='utf-8') as f:
        f.write(chain)
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-y', '-i', a.src,
             '-filter_complex_script', '_chain.txt', '-map', '[out]',
             '-c:a', 'pcm_s24le', '-ar', '48000', a.tone])
    clip = r.stderr.lower().count('clipping')
    if clip:
        print(f'!! {clip} clipping warnings inside the chain -- a filter is resonating')
    i1, tp1, lra1 = measure(a.tone)
    print(f'tone   : {i1:7.2f} LUFS  {tp1:6.2f} dBTP  LRA {lra1:.2f}')

    # The ceiling adapts instead of trusting one constant. alimiter caps SAMPLE
    # peak while the target is quoted in TRUE peak, and how far the inter-sample
    # peaks overshoot depends on the material: a fixed 1.4 dB allowance that fit
    # a narrow electronic mix left a wide rock mix 0.5 dB over the ceiling.
    limit_db = a.tp - ISP_HEADROOM_DB
    drive = a.lufs - i1                       # first guess: pure gain
    for step in range(8):
        limit = 10 ** (limit_db / 20)
        run(['ffmpeg', '-hide_banner', '-nostats', '-y', '-i', a.tone, '-af',
             f'volume={drive:.2f}dB,alimiter=level_in=1:level_out=1:'
             f'limit={limit:.4f}:attack=5:release=70:level=disabled',
             '-c:a', 'pcm_s24le', '-ar', '48000', a.dst])
        i2, tp2, lra2 = measure(a.dst)
        err = a.lufs - i2
        over = tp2 - a.tp
        print(f'  drive {drive:+6.2f} dB  ceil {limit_db:+5.2f} dBFS -> {i2:7.2f} LUFS  '
              f'{tp2:6.2f} dBTP  LRA {lra2:.2f}')
        if abs(err) <= 0.15 and over <= 0.02:
            break
        if over > 0.02:
            limit_db -= over + 0.1     # pull the ceiling by exactly what spilled
        # Limiting eats part of every extra dB, so chase rather than jump.
        drive += err * 0.8

    i2, tp2, lra2 = measure(a.dst)
    print(f'\nmaster : {i2:7.2f} LUFS  {tp2:6.2f} dBTP  LRA {lra2:.2f}')
    ok = abs(i2 - a.lufs) <= 0.4 and tp2 <= a.tp + 0.05
    print('target : ' + ('MET' if ok else 'NOT MET -- do not ship this'))
    if lra2 < 3:
        print(f'note   : LRA {lra2:.2f} is very flat. That is the price of '
              f'{a.lufs:g} LUFS on this source, not a bug.')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
