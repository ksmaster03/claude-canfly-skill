import React from 'react';
import {
  AbsoluteFill, OffthreadVideo, staticFile,
  useCurrentFrame, useVideoConfig, interpolate, Easing,
} from 'remotion';
import tl from './timeline.json';

// ---------------------------------------------------------------------------
// ทิศทางดีไซน์รอบ 3 ตามรีวิว prom-design
//   เดิม: พื้นไล่น้ำเงินไปม่วง ลอกจากคลิปต้นฉบับ และเป็นคู่สีที่สกิลห้ามทุกกรณี
//   ใหม่: "โต๊ะทำงานตอนเช้า" พื้นครีมโทนเดียวกับหน้าจอ claude.ai ตัวหนังสือสีหมึกอุ่น
//         สีเน้นส้มดินเผาเพียงสีเดียว เอามาจากเครื่องหมายดาวบนหน้าแรกของ Claude
// ---------------------------------------------------------------------------
const T = {
  ground: '#F3EEE4',
  card: '#FFFDF8',
  ink: '#1E1A15',
  soft: '#5A5147',
  clay: '#B24F2C',
  line: 'rgba(30,26,21,0.12)',
  dim: 'rgba(30,26,21,0.36)',
};
const SERIF = 'Trirong, Sarabun, "Leelawadee UI", serif';
const SANS = 'Sarabun, "Leelawadee UI", sans-serif';

const W = 720;
const HEAD_H = 236;
const BOX = { x: 0, y: HEAD_H, w: 720, h: 640 };
const SUB_Y = BOX.y + BOX.h + 24;
const VW = 1440, VH = 900;
const FIT = Math.max(BOX.w / VW, BOX.h / VH);

type Mark = {
  type: string; label: string; start: number; end: number; chip?: string;
  x: number; y: number; w: number; h: number; cx: number; cy: number;
};
const marks = (tl as any).marks as Mark[];
const cues = (tl as any).cues as Array<{ id: number; text: string; start: number; end: number }>;
const CTA_START = (tl as any).ctaStart as number;
const CTA_CLICK = (tl as any).ctaClick as number;

const Fonts: React.FC = () => (
  <style>{`
    @font-face{font-family:Sarabun;src:url(${staticFile('fonts/Sarabun-Regular.ttf')}) format('truetype');font-weight:400}
    @font-face{font-family:Sarabun;src:url(${staticFile('fonts/Sarabun-SemiBold.ttf')}) format('truetype');font-weight:600}
    @font-face{font-family:Sarabun;src:url(${staticFile('fonts/Sarabun-Bold.ttf')}) format('truetype');font-weight:700}
    @font-face{font-family:Trirong;src:url(${staticFile('fonts/Trirong-SemiBold.ttf')}) format('truetype');font-weight:600}
    @font-face{font-family:Trirong;src:url(${staticFile('fonts/Trirong-Bold.ttf')}) format('truetype');font-weight:700}
  `}</style>
);

// ---------- กล้อง ----------
// รอบก่อนซูมแรงจนหัวข้อหน้าและป้ายในฟอร์มโดนตัด ของที่กว้างเกิน 360 px จึงซูมน้อยลง
const zoomFor = (m: Mark) => (m.w <= 160 ? 2.5 : m.w <= 360 ? 2.0 : m.w <= 700 ? 1.3 : 1.12);
const TRAVEL = 0.7;

const camAt = (now: number) => {
  let prev = { cx: VW / 2, cy: VH / 2, z: 1 };
  let since = 0;
  for (const m of marks) {
    const t0 = m.start - TRAVEL;
    const target = { cx: m.cx, cy: m.cy, z: zoomFor(m) };
    if (now < t0) break;
    if (now < m.start) {
      const p = interpolate(now, [t0, m.start], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
      return { cx: prev.cx + (target.cx - prev.cx) * p, cy: prev.cy + (target.cy - prev.cy) * p, z: prev.z + (target.z - prev.z) * p, since: now };
    }
    prev = target;
    since = m.start;
  }
  return { ...prev, since };
};

const Screen: React.FC<{ now: number }> = ({ now }) => {
  const cam = camAt(now);
  // ไหลเข้าต่อเนื่องระหว่างค้างเป้าเดิม ต้องเกินหนึ่งพิกเซลต่อเฟรม ไม่งั้นเท่ากับไม่ได้ใส่
  const drift = 1 + 0.012 * (now - cam.since);
  const s = FIT * cam.z * drift;
  const tx = Math.min(0, Math.max(BOX.w - VW * s, BOX.w / 2 - cam.cx * s));
  const ty = Math.min(0, Math.max(BOX.h - VH * s, BOX.h / 2 - cam.cy * s));
  return (
    <div style={{ position: 'absolute', left: BOX.x, top: BOX.y, width: BOX.w, height: BOX.h, overflow: 'hidden', background: T.card, borderTop: `1px solid ${T.line}`, borderBottom: `1px solid ${T.line}` }}>
      <div style={{ width: VW, height: VH, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${s})` }}>
        <OffthreadVideo src={staticFile('screen.mp4')} style={{ width: VW, height: VH }} />
        <Marks now={now} z={cam.z * drift} />
        <Cursor now={now} z={cam.z * drift} />
      </div>
      <SourceChip now={now} />
    </div>
  );
};

// ---------- กรอบไฮไลต์ ----------
const Marks: React.FC<{ now: number; z: number }> = ({ now, z }) => (
  <>
    {marks.map((m, i) => {
      if (m.type === 'cam') return null;
      const lead = 0.45;
      const hold = Math.max(1.8, m.end - m.start + 1.4) + (m.chip ? 2.5 : 0);
      const s = m.start - lead, e = m.start + hold;
      if (now < s || now > e) return null;
      const fade = interpolate(now, [s, s + 0.22, e - 0.35, e], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const grow = interpolate(now, [s, s + 0.3], [1.12, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
      const pulse = 0.5 + 0.5 * Math.sin(now * 4.4);
      const pad = 9;
      const d = now - m.start;
      const ripple = m.type === 'click' && d >= 0 && d <= 0.5;
      const r = interpolate(d, [0, 0.5], [16, 90], { extrapolateRight: 'clamp' });
      return (
        <React.Fragment key={i}>
          <div style={{
            position: 'absolute', left: m.x - pad, top: m.y - pad, width: m.w + pad * 2, height: m.h + pad * 2,
            border: `${4.5 / z}px solid ${T.clay}`, borderRadius: 9 / z,
            boxShadow: `0 0 0 4000px ${T.dim}, 0 0 ${(10 + 10 * pulse) / z}px rgba(178,79,44,.55)`,
            opacity: fade, transform: `scale(${grow})`,
          }} />
          {ripple && (
            <div style={{
              position: 'absolute', left: m.cx - r, top: m.cy - r, width: r * 2, height: r * 2, borderRadius: '50%',
              border: `${4 / z}px solid ${T.clay}`, opacity: interpolate(d, [0, 0.5], [0.85, 0], { extrapolateRight: 'clamp' }),
            }} />
          )}
        </React.Fragment>
      );
    })}
  </>
);

// ---------- ป้ายบอกที่มาของภาพ ----------
// ประโยคตอนบันทึกงานใช้ภาพจากแบบสำเร็จรูป เพราะไม่ได้สร้างงานจริงในบัญชี จึงต้องบอกคนดูตรง ๆ
const SourceChip: React.FC<{ now: number }> = ({ now }) => {
  const m = marks.find((k) => k.chip && now >= k.start - 0.45 && now <= k.start + 4.8);
  if (!m) return null;
  const a = interpolate(now, [m.start - 0.45, m.start - 0.1, m.start + 4.4, m.start + 4.8], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <div style={{
      position: 'absolute', left: 24, top: 22, opacity: a,
      background: T.ink, color: T.card, borderRadius: 999, padding: '8px 18px',
      fontFamily: SANS, fontWeight: 600, fontSize: 22, display: 'flex', alignItems: 'center', gap: 10,
    }}>
      <span style={{ width: 9, height: 9, borderRadius: 9, background: '#E9A27F', display: 'inline-block' }} />
      {m.chip}
    </div>
  );
};

const Cursor: React.FC<{ now: number; z: number }> = ({ now, z }) => {
  const LEAD = 0.55;
  const pts = marks.filter((m) => m.type !== 'cam');
  let pos = { x: VW * 0.55, y: VH * 0.7 };
  for (let i = 0; i < pts.length; i++) {
    const m = pts[i];
    const from = i === 0 ? pos : { x: pts[i - 1].cx, y: pts[i - 1].cy };
    const travel = m.start - LEAD;
    if (now >= travel && now < m.start) {
      const p = interpolate(now, [travel, m.start], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
      pos = { x: from.x + (m.cx - from.x) * p, y: from.y + (m.cy - from.y) * p };
      break;
    }
    if (now >= m.start) pos = { x: m.cx, y: m.cy };
  }
  const k = 1.5 / z;
  return (
    <svg width={34 * k} height={44 * k} viewBox="0 0 34 44"
      style={{ position: 'absolute', left: pos.x - 2 * k, top: pos.y - 1 * k, filter: 'drop-shadow(0 2px 4px rgba(30,26,21,.45))' }}>
      <path d="M3 2 L3 32 L11 25 L16 38 L22 35 L17 23 L27 22 Z" fill={T.card} stroke={T.ink} strokeWidth="2.6" strokeLinejoin="round" />
    </svg>
  );
};

// ---------- หัวคลิป ----------
// เดิม ">> Claude Scheduled <<" ใต้ป้ายชื่อเพจคนอื่น กินพื้นที่ 26% ของจอ
// ใหม่เหลือ 18% หัวข้อภาษาไทยบอกผลลัพธ์ ป้ายบรรทัดบนเป็นชื่อฟีเจอร์ตามที่เห็นบนหน้าจอ
const Header: React.FC = () => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: W, height: HEAD_H, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 44px', gap: 8 }}>
    <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 21, color: T.clay, letterSpacing: '0.06em' }}>
      Claude · Scheduled tasks
    </div>
    <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 48, color: T.ink, lineHeight: 1.16 }}>
      ให้ Claude<br />ทำงานเองตามเวลา
    </div>
  </div>
);

// ---------- ช่วงไอเดียเอาไปใช้ ----------
// คำสั่งบนการ์ดใบแรกคือคำสั่งเดียวกับที่พิมพ์ในคลิปจริง ใบอื่นติดป้ายว่าเป็นไอเดีย
// ความถี่ใช้ชื่อตัวเลือกจริงที่เห็นบนหน้าจอ ไม่แต่งตัวเลขที่ไม่มีที่มา
const CARDS = [
  { id: 30, title: 'สรุปข่าวทุกเช้า', cmd: 'ค้นข่าว AI ที่สำคัญของเมื่อวาน สรุป 5 ข้อ พร้อมลิงก์', freq: 'Daily', tag: 'คำสั่งที่พิมพ์ในคลิปนี้' },
  { id: 31, title: 'ไล่งานค้างของทีม', cmd: 'ดูงานที่ยังไม่ปิด แยกตามคน บอกว่าใครติดอะไร', freq: 'Weekly', tag: 'ไอเดีย' },
  { id: 32, title: 'สรุปตัวเลขรายสัปดาห์', cmd: 'สรุปยอดสัปดาห์นี้ เทียบกับสัปดาห์ก่อน', freq: 'Weekly', tag: 'ไอเดีย' },
];
const FREQS = ['Manual', 'Hourly', 'Daily', 'Weekdays', 'Weekly'];

const UseCards: React.FC<{ now: number }> = ({ now }) => {
  const cs = (tl as any).cardsStart as number;
  const drift = 1 + Math.min(0.025, 0.0035 * Math.max(0, now - cs));   // เพดานกันการ์ดล้นขอบ
  return (
    <div style={{ position: 'absolute', left: BOX.x, top: BOX.y, width: BOX.w, height: BOX.h, padding: '22px 34px', display: 'flex', flexDirection: 'column', gap: 12, transform: `scale(${drift})`, transformOrigin: '50% 40%' }}>
      <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 36, color: T.ink, opacity: interpolate(now, [cs - 0.3, cs + 0.2], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        ตั้งไว้ทำอะไรได้บ้าง
        <div style={{ fontFamily: SANS, fontWeight: 400, fontSize: 20, color: T.soft, marginTop: 2 }}>ใบแรกคือคำสั่งที่พิมพ์ในคลิปนี้ อีกสองใบเป็นไอเดีย</div>
      </div>
      {CARDS.map((c, i) => {
        const cue = cues.find((q) => q.id === c.id)!;
        const appear = cs - 0.2 + i * 0.18;
        const p = interpolate(now, [appear, appear + 0.5], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
        const active = now >= cue.start - 0.4 && now <= cue.end + 0.35;
        return (
          <div key={i} style={{
            background: T.card, borderRadius: 16, padding: '12px 20px',
            border: `2px solid ${active ? T.clay : T.line}`,
            boxShadow: active ? '0 10px 26px rgba(30,26,21,.14)' : 'none',
            opacity: p, transform: `translateY(${(1 - p) * 24}px)`,
            display: 'flex', flexDirection: 'column', gap: 2,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 28, color: T.ink, flex: 1 }}>{c.title}</div>
              <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 19, color: T.clay, border: `1.5px solid ${T.clay}`, borderRadius: 999, padding: '2px 12px' }}>{c.freq}</div>
            </div>
            <div style={{ fontFamily: SANS, fontWeight: 400, fontSize: 22, color: T.soft, lineHeight: 1.4 }}>คำสั่ง: {c.cmd}</div>
          </div>
        );
      })}
      <div style={{ marginTop: 4, opacity: interpolate(now, [cs + 0.5, cs + 1.0], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 19, color: T.soft, marginBottom: 8 }}>ตัวเลือกความถี่ในหน้าจริง</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {FREQS.map((f) => (
            <div key={f} style={{ fontFamily: SANS, fontWeight: 600, fontSize: 19, color: T.ink, background: T.card, border: `1.5px solid ${T.line}`, borderRadius: 999, padding: '4px 14px' }}>{f}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ---------- ฉากปิด ชวนติดตาม ----------
// ขยายการ์ดลงไปคลุมพื้นที่ซับ เพราะช่วงนี้ซ่อนซับ (ข้อความบนการ์ดบอกครบแล้ว) ครึ่งล่างจะได้ไม่ว่าง
const FollowCta: React.FC<{ now: number }> = ({ now }) => {
  const enter = interpolate(now, [CTA_START - 0.35, CTA_START + 0.25], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.back(1.3)) });
  const pressed = now >= CTA_CLICK;
  const press = interpolate(now, [CTA_CLICK - 0.06, CTA_CLICK, CTA_CLICK + 0.14], [1, 0.93, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const flip = interpolate(now, [CTA_CLICK, CTA_CLICK + 0.25], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const drift = 1 + 0.004 * Math.max(0, now - CTA_START);

  const PANEL = { x: 36, y: BOX.y + 24, w: W - 72, h: 700 };
  const BTN = { w: 330, h: 84 };
  const bx = W / 2 - BTN.w / 2, by = PANEL.y + 420;
  const target = { x: bx + BTN.w * 0.9, y: by + BTN.h * 0.62 };
  const start = { x: W * 0.86, y: PANEL.y + PANEL.h + 40 };
  const mv = interpolate(now, [CTA_CLICK - 1.1, CTA_CLICK - 0.12], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  const away = interpolate(now, [CTA_CLICK + 0.35, CTA_CLICK + 1.1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
  const cur = { x: start.x + (target.x - start.x) * mv + 46 * away, y: start.y + (target.y - start.y) * mv + 52 * away };
  const d = now - CTA_CLICK;
  const r = interpolate(d, [0, 0.55], [18, 120], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <>
      <div style={{
        position: 'absolute', left: PANEL.x, top: PANEL.y, width: PANEL.w, height: PANEL.h,
        background: T.card, borderRadius: 26, border: `1px solid ${T.line}`, boxShadow: '0 20px 50px rgba(30,26,21,.12)',
        opacity: enter, transform: `translateY(${(1 - enter) * 50}px) scale(${(0.95 + 0.05 * enter) * drift})`,
        display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 110,
      }}>
        <div style={{ fontFamily: SERIF, fontWeight: 700, fontSize: 52, color: T.ink, textAlign: 'center', lineHeight: 1.25 }}>
          ฝากกดติดตาม<br />ด้วยนะครับ
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 400, fontSize: 28, color: T.soft, marginTop: 22, textAlign: 'center', lineHeight: 1.45 }}>
          คลิปหน้ามีวิธีใช้ AI<br />ช่วยทำงานมาให้อีก
        </div>
      </div>

      <div style={{
        position: 'absolute', left: bx, top: by, width: BTN.w, height: BTN.h, borderRadius: 44, opacity: enter,
        background: pressed ? T.ground : T.ink, border: `2px solid ${pressed ? T.line : T.ink}`,
        transform: `scale(${press})`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 14,
      }}>
        <svg width="36" height="36" viewBox="0 0 24 24">
          {pressed ? (
            <path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke={T.clay} strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="24" strokeDashoffset={24 * (1 - flip)} />
          ) : (
            <path d="M12 5v14M5 12h14" fill="none" stroke={T.card} strokeWidth="2.8" strokeLinecap="round" />
          )}
        </svg>
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 36, color: pressed ? T.ink : T.card }}>{pressed ? 'ติดตามแล้ว' : 'ติดตาม'}</div>
      </div>

      {d >= 0 && d <= 0.55 && (
        <div style={{ position: 'absolute', left: target.x - r, top: target.y - r, width: r * 2, height: r * 2, borderRadius: '50%', border: `4px solid ${T.clay}`, opacity: interpolate(d, [0, 0.55], [0.9, 0], { extrapolateRight: 'clamp' }) }} />
      )}
      {now >= CTA_CLICK - 1.3 && (
        <svg width={50} height={64} viewBox="0 0 34 44" style={{ position: 'absolute', left: cur.x - 3, top: cur.y - 2, filter: 'drop-shadow(0 3px 6px rgba(30,26,21,.4))', transform: `scale(${d >= 0 && d < 0.14 ? 0.88 : 1})`, transformOrigin: '0 0' }}>
          <path d="M3 2 L3 32 L11 25 L16 38 L22 35 L17 23 L27 22 Z" fill={T.card} stroke={T.ink} strokeWidth="2.6" strokeLinejoin="round" />
        </svg>
      )}
    </>
  );
};

// ---------- ซับไตเติล ----------
const Subtitle: React.FC<{ now: number }> = ({ now }) => {
  if (now >= CTA_START - 0.35) return null;
  const cur = cues.find((c) => now >= c.start - 0.12 && now <= c.end + 0.22);
  if (!cur) return null;
  const fade = interpolate(now, [cur.start - 0.12, cur.start + 0.07, cur.end, cur.end + 0.22], [0, 1, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const words = cur.text.split(' ');
  return (
    <div style={{ position: 'absolute', left: 0, top: SUB_Y, width: W, padding: '0 44px', display: 'flex', justifyContent: 'center' }}>
      <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 33, lineHeight: 1.4, textAlign: 'center', opacity: fade, textWrap: 'balance' } as React.CSSProperties}>
        {words.map((wd, i) => {
          const share = (cur.end - cur.start) / words.length;
          const on = now >= cur.start + share * i - 0.05;
          // คำที่ยังไม่ถึงคิวใช้สีจางที่ยังอ่านออก รอบก่อนจางเหลือ 32% ความต่างสีตกไปที่ 1.52:1
          // nowrap ต่อช่วงคำ: ให้ขึ้นบรรทัดได้แค่ตรงช่องว่างในบท ไม่งั้นเบราว์เซอร์หั่นคำไทยกลางคำ เช่น กี่ / โมง (keep-all ใช้กับไทยไม่ได้)
          return <React.Fragment key={i}><span style={{ color: on ? T.ink : '#8A8177', whiteSpace: 'nowrap' }}>{wd}</span>{i < words.length - 1 ? ' ' : ''}</React.Fragment>;
        })}
      </div>
    </div>
  );
};

const Progress: React.FC<{ now: number }> = ({ now }) => (
  <div style={{ position: 'absolute', left: 0, top: BOX.y + BOX.h - 5, width: W, height: 5, background: 'rgba(30,26,21,.10)' }}>
    <div style={{ width: `${Math.min(100, (now / (tl as any).totalDur) * 100)}%`, height: '100%', background: T.clay }} />
  </div>
);

export const Reel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const now = frame / fps;
  const onScreen = now <= (tl as any).screenDur;
  const inCta = now >= CTA_START - 0.35;
  return (
    <AbsoluteFill style={{ background: T.ground }}>
      <Fonts />
      <Header />
      {onScreen ? <Screen now={now} /> : inCta ? <FollowCta now={now} /> : <UseCards now={now} />}
      {!inCta && <Progress now={now} />}
      <Subtitle now={now} />
      {/* เสียงทั้งหมดมิกซ์แยกใน sound.py แล้วประกบทีหลัง */}
    </AbsoluteFill>
  );
};
