import React from 'react';
import { Composition } from 'remotion';
import { W, H, FPS, BAR_F } from './theme';
import { BucketClip } from './clips/Bucket';
import { BoatClip } from './clips/Boat';
import { HillClip } from './clips/Hill';
import { CargoClip } from './clips/Cargo';
import { DominoClip } from './clips/Domino';
import { RingsClip } from './clips/Rings';
import { HourglassClip } from './clips/Hourglass';
import { CloserClip } from './clips/Closer';

/**
 * One composition per clip. Lengths are whole bars at 113.5 BPM so the music can
 * be cut on a downbeat and the visuals stay locked to it:
 *   3 bars = 190 frames = 6.34s   ·   4 bars = 254 frames = 8.46s
 *
 * These sit inside the 6.3–9.8s band the top 50 clips on the reference page
 * occupy; the mid-band that nobody watches runs 30.7s.
 */
export const CLIPS: Array<{ id: string; component: React.FC; bars: number; title: string }> = [
  { id: 'Bucket', component: BucketClip, bars: 4, title: 'ถังน้ำรั่ว' },
  { id: 'Boat', component: BoatClip, bars: 3, title: 'พายเรือ vs ติดเครื่องยนต์' },
  { id: 'Hill', component: HillClip, bars: 4, title: 'สบายตอนนี้ vs สบายยาว' },
  { id: 'Cargo', component: CargoClip, bars: 3, title: 'แบกทีละใบ vs ยกทีละชั้น' },
  { id: 'Domino', component: DominoClip, bars: 4, title: 'โดมิโน' },
  { id: 'Rings', component: RingsClip, bars: 3, title: 'วงแหวนโซน' },
  { id: 'Hourglass', component: HourglassClip, bars: 4, title: 'นาฬิกาทราย' },
  { id: 'Closer', component: CloserClip, bars: 4, title: 'หยุดเรียน vs เรียนต่อ' },
];

export const RemotionRoot: React.FC = () => (
  <>
    {CLIPS.map((c) => (
      <Composition
        key={c.id}
        id={c.id}
        component={c.component}
        durationInFrames={BAR_F(c.bars)}
        fps={FPS}
        width={W}
        height={H}
      />
    ))}
  </>
);
