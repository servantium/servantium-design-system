/**
 * Heading — a section heading in the body. Markdown `##` becomes one.
 *
 *   ## Your first steps
 *
 *   <Heading margin="0 0 4px">{{ headline }}</Heading>
 *
 * Level 1 (Markdown `#`) is the serif title, for the rare email without a banner headline. Every
 * master has one, so reach for `##`.
 */
import type { ReactNode } from 'react';
import { color, fonts } from '../theme';

export function Heading({ level = 2, children, margin }: { level?: 1 | 2; children: ReactNode; margin?: string }) {
  if (level === 1) {
    return (
      <h1 className="ve-title" style={{ margin: margin ?? '0 0 20px', fontFamily: fonts.display, fontSize: '28px',
        lineHeight: '36px', fontWeight: 600, color: color.ink }}>{children}</h1>
    );
  }
  return (
    <h2 style={{ margin: margin ?? '28px 0 8px', fontFamily: fonts.body, fontSize: '17px', lineHeight: '24px',
      fontWeight: 700, color: color.ink }}>{children}</h2>
  );
}
