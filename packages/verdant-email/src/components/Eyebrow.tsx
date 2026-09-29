/**
 * Eyebrow — a small uppercase line above a heading or table: a project code, a section.
 *
 *   <Eyebrow>AUR-417 · Phase II</Eyebrow>
 */
import type { ReactNode } from 'react';
import { color, fonts } from '../theme';

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <p style={{ margin: '0 0 8px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '16px', fontWeight: 700,
      letterSpacing: '1px', textTransform: 'uppercase', color: color.inkMuted }}>{children}</p>
  );
}
