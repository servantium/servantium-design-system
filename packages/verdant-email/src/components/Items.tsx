/**
 * Items — a run of titled things written into the master: release highlights, "what you'll find".
 *
 *   <Items items={[
 *     { chip: { tone: "default", label: "New" }, title: "Secure Search", body: "Search only shows what you can see." },
 *     { title: "Project Management", body: "The plans and tasks your team delivers against." },
 *   ]} />
 *
 * The items are fixed in the master. When the SENDER supplies the list, use Updates instead.
 */
import type { ReactNode } from 'react';
import { color, fonts, type Tint } from '../theme';
import { Chip } from './Chip';

export function Items({ items }: {
  items: { title: ReactNode; body: ReactNode; chip?: { tone: Tint; label: string }; meta?: ReactNode }[];
}) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody>
        {items.map((it, i) => (
          <tr key={i}>
            <td style={{ padding: i ? '18px 0 0' : '0', borderTop: i ? `1px solid ${color.rule}` : '0' }}>
              <div>
                {(it.chip || it.meta) && (
                  <p style={{ margin: '0 0 6px', fontFamily: fonts.body, fontSize: '13px', lineHeight: '18px', color: color.inkMuted }}>
                    {it.chip && <Chip tone={it.chip.tone}>{it.chip.label}</Chip>}
                    {it.chip && it.meta && <>&nbsp;&nbsp;</>}
                    {it.meta}
                  </p>
                )}
                <p style={{ margin: '0 0 4px', fontFamily: fonts.body, fontSize: '16px', lineHeight: '24px', fontWeight: 700, color: color.ink }}>{it.title}</p>
                <p style={{ margin: '0 0 18px', fontFamily: fonts.body, fontSize: '15px', lineHeight: '23px', color: color.ink }}>{it.body}</p>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
