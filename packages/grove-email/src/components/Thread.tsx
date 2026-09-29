/**
 * Thread — the earlier messages in a conversation, newest first, one { author, time, excerpt }
 * item each. The support reply uses it.
 *
 *   <Thread field="thread" title="Earlier in this conversation" />
 *
 * Quieter than the new message above it, and separated by hairlines — never a bar down the side,
 * which is how most mail clients draw quoted text and exactly what we don't do.
 */
import { color, fonts } from '../theme';

export function Thread({ field, title = 'Earlier in this conversation' }: { field: string; title?: string }) {
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
      <tbody>
        <tr><td style={{ paddingBottom: '4px', borderBottom: `1px solid ${color.rule}` }}>
          <p style={{ margin: '0 0 6px', fontFamily: fonts.body, fontSize: '12px', lineHeight: '16px', fontWeight: 700,
            letterSpacing: '1px', textTransform: 'uppercase', color: color.inkMuted }}>{title}</p>
        </td></tr>
        {`{{#each ${field}}}`}
        <tr>
          <td style={{ padding: '12px 0', borderBottom: `1px solid ${color.rule}` }}>
            <p style={{ margin: '0 0 2px', fontFamily: fonts.body, fontSize: '13px', lineHeight: '18px', color: color.inkMuted }}>
              <b style={{ color: color.ink }}>{'{{ author }}'}</b>&nbsp;&nbsp;·&nbsp;&nbsp;{'{{ time }}'}
            </p>
            <p style={{ margin: 0, fontFamily: fonts.body, fontSize: '14px', lineHeight: '21px', color: color.inkMuted }}>{'{{ excerpt }}'}</p>
          </td>
        </tr>
        {'{{/each}}'}
      </tbody>
    </table>
  );
}
