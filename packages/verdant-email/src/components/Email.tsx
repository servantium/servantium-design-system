/**
 * Email — the 600px column every email sits in.
 *
 * Frame, not content: the MDX loader wraps every master in Email → Banner → Body → Footer, so a
 * master never writes these four itself. `width="600"` is for Outlook desktop; the inline width
 * lets every other client shrink the column to a phone.
 */
import type { ReactNode } from 'react';

export function Email({ children }: { children: ReactNode }) {
  return (
    <table role="presentation" className="ve-container" width="600" cellPadding={0} cellSpacing={0} border={0}
      style={{ width: '100%', maxWidth: '600px' }}>
      <tbody>{children}</tbody>
    </table>
  );
}
