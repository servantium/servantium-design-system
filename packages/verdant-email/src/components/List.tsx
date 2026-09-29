/**
 * List — what a Markdown `-` list becomes. Three to five short, parallel items.
 *
 *   - Drawn as a table, so bullets line up in Outlook
 *   - One line each, where you can
 *
 * A table, not a <ul>: Outlook desktop indents and spaces <ul> unpredictably, and Gmail strips
 * list padding. Numbered Markdown lists come out as bullets too; for a real sequence use Steps.
 */
import type { ReactNode } from 'react';
import { color, fonts } from '../theme';

export function List({ children }: { children: ReactNode }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} style={{ margin: '0 0 16px' }}>
      <tbody>{children}</tbody>
    </table>
  );
}

export function ListItem({ children }: { children: ReactNode }) {
  return (
    <tr>
      <td width={20} valign="top" style={{ padding: '0 0 8px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.link }}>&#8226;</td>
      <td valign="top" style={{ padding: '0 0 8px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', color: color.ink }}>{children}</td>
    </tr>
  );
}
