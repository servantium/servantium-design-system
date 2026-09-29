/**
 * Updates — a list the SENDER fills, one row per item: a category chip, a time, a title that
 * links to its `url`, and a line of context. The digest uses it.
 *
 *   <Updates field="items" />
 *
 *   fields:
 *     items:
 *       note: "The updates, newest first, as { category, time, title, context, url }"
 *       example:
 *         - { category: Task, time: "9:14 AM", title: "…", context: "…", url: "https://…" }
 *
 * Postmark repeats the row with {{#each}}; the master's example list fills the gallery.
 */
import { color, fonts } from '../theme';
import { Chip } from './Chip';

export function Updates({ field }: { field: string }) {
  const p = (extra: object) => ({ margin: 0, fontFamily: fonts.body, ...extra });
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody>
        {`{{#each ${field}}}`}
        <tr>
          <td style={{ padding: '14px 0', borderBottom: `1px solid ${color.rule}` }}>
            <p style={p({ fontSize: '13px', lineHeight: '18px', color: color.inkMuted, marginBottom: '6px' })}>
              <Chip tone="neutral">{'{{ category }}'}</Chip>&nbsp;&nbsp;{'{{ time }}'}
            </p>
            <p style={p({ fontSize: '16px', lineHeight: '24px', fontWeight: 700, marginBottom: '2px' })}>
              <a href="{{ url }}" style={{ color: color.ink, textDecoration: 'underline', textDecorationColor: color.rule }}>{'{{ title }}'}</a>
            </p>
            <p style={p({ fontSize: '14px', lineHeight: '21px', color: color.inkMuted })}>{'{{ context }}'}</p>
          </td>
        </tr>
        {'{{/each}}'}
      </tbody>
    </table>
  );
}
