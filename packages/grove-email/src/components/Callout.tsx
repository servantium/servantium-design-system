/**
 * Callout — a tinted panel for the one thing a reader must not miss. One per email.
 *
 *   <Callout title="Didn't request this?">You can ignore this email.</Callout>
 *   <Callout tone="neutral" title="What they wrote">“{{ . }}”</Callout>
 *
 *   default    reassurance          attention  something to do soon
 *   urgent     something to stop    neutral    a quoted note — not news at all
 *
 * The tone lives in the WHOLE tint and the title colour. There is no coloured bar down the side:
 * that is banned (2026-09-24), and this component offers no way to draw one.
 */
import type { ReactNode } from 'react';
import { color, fonts, tint, type Tint } from '../theme';

export function Callout({ tone = 'default', title, children }: { tone?: Tint; title?: string; children: ReactNode }) {
  const t = tint(tone);
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={t.tint}
      style={{ backgroundColor: t.tint, borderRadius: '10px' }}>
      <tbody><tr><td style={{ padding: '16px 20px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '23px', color: color.ink }}>
        {title && <p style={{ margin: '0 0 4px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '22px', fontWeight: 700, color: t.strong }}>{title}</p>}
        {children}
      </td></tr></tbody>
    </table>
  );
}
