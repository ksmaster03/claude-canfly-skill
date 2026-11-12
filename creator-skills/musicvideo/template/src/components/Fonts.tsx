import React from 'react';
import { FONT_CSS } from '../fonts';

/**
 * Injects the embedded Sarabun faces.
 *
 * Must be mounted in every composition. Without it the Thai lyric renders as
 * tofu boxes -- the fallback stack on this machine has no Thai glyphs at the
 * weight the design asks for, and the failure looks like a font-weight problem
 * rather than a missing script.
 */
export const Fonts: React.FC = () => <style>{FONT_CSS}</style>;
