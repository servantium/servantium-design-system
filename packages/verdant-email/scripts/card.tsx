/** A body-only card: how the style sheet shows a component sample without a banner or footer. */
import type { ReactNode } from 'react';
import { Email } from '../src/components/Layout';
import { color } from '../src/theme';

export const Card = ({ children }: { children: ReactNode }) => (
  <Email>
    <tr><td className="ve-px" bgcolor={color.surface} style={{ padding: '28px 32px', backgroundColor: color.surface,
      border: `1px solid ${color.rule}`, borderRadius: '14px' }}>{children}</td></tr>
  </Email>
);
