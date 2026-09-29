/**
 * Text — a paragraph. Every Markdown paragraph in a master becomes one, so you only write <Text>
 * to change its size, colour or spacing.
 *
 *   Plain Markdown is a Text.
 *
 *   <Text size="sm" muted margin="0">This link expires in {{ expires_in }}.</Text>
 */
import type { ReactNode } from 'react';
import { color, fonts } from '../theme';

const SIZES = { md: ['16px', '26px'], sm: ['14px', '22px'], xs: ['13px', '20px'] } as const;

export function Text({ children, size = 'md', muted, bold, margin }: {
  children: ReactNode;
  /** md 16px (body) · sm 14px (asides) · xs 13px (the smallest we set). */
  size?: keyof typeof SIZES;
  /** Grey, for secondary lines. Still passes AA. */
  muted?: boolean;
  bold?: boolean;
  /** CSS margin. Paragraphs default to 16px below. */
  margin?: string;
}) {
  const [fs, lh] = SIZES[size];
  return (
    <p style={{ margin: margin ?? '0 0 16px', fontFamily: fonts.body, fontSize: fs, lineHeight: lh,
      fontWeight: bold ? 700 : 400, color: muted ? color.inkMuted : color.ink }}>{children}</p>
  );
}
