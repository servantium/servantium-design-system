/**
 * Chip — a one-word status beside a title: New, Changed, Resolved, Beta. It carries a word, never
 * just a colour.
 *
 *   <Chip>New</Chip> <Chip tone="attention">Changed</Chip> <Chip tone="neutral">Beta</Chip>
 */
import { fonts, tint, type Tint } from '../theme';

export function Chip({ tone = 'default', children }: { tone?: Tint; children: string }) {
  const t = tint(tone);
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: '999px', backgroundColor: t.tint, color: t.strong,
      fontFamily: fonts.body, fontSize: '11px', lineHeight: '16px', fontWeight: 700, letterSpacing: '0.8px', textTransform: 'uppercase' }}>
      {children}
    </span>
  );
}
