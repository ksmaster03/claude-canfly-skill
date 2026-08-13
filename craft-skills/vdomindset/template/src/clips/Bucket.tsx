import React from 'react';
import { StickFigure } from '../Figure';
import { SplitStage, useLoop, saw, wave } from '../Stage';
import { scooping, pointing } from '../poses';
import { Bucket, Puddle, Drips, Stream, BUCKET_H } from '../props/water';
import { AiOrb } from '../props/common';

/**
 * ถังน้ำรั่ว — repetitive manual work vs fixing the leak once.
 *
 * Both sides are in a STEADY STATE rather than a progression, because a bucket
 * that fills up over the clip has to snap back to empty at the loop point. The
 * left bucket is permanently near-empty and leaking; the right one is
 * permanently full and overflowing. The comparison does the work, not a build-up.
 */
export const BucketClip: React.FC = () => {
  const u = useLoop();

  // Four scoops, one per bar — the labour reads as endless because it never
  // changes the level.
  const scoop = saw(u, 4);
  const left = scooping(scoop);

  const right = pointing(saw(u, 1));

  return (
    <SplitStage
      goal="เป้าหมายเดียวกัน"
      left={{
        label: 'ตักน้ำทุกเช้า',
        children: (
          <g>
            <Puddle x={60} w={80} />
            <Bucket id="leak" x={60} level={0.2 + 0.03 * wave(u, 4)} hole />
            <Drips x={60 - 49} y={-52} p={u} />
            <g transform="translate(-112, 0)">
              <StickFigure joints={left.joints} tone="silver" />
            </g>
          </g>
        ),
      }}
      right={{
        label: 'อุดรูครั้งเดียว',
        children: (
          <g>
            <Puddle x={60} w={66} />
            <Stream x={60} from={-250} to={-BUCKET_H - 6} p={u} />
            <Bucket id="fixed" x={60} level={0.92} patch overflow={0.9} />
            <AiOrb x={60} y={-286} t={u} r={20} />
            <g transform="translate(-112, 0)">
              <StickFigure joints={right.joints} tone="orange" />
            </g>
          </g>
        ),
      }}
    />
  );
};
