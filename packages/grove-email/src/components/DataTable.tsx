/**
 * DataTable — facts a reader looks up rather than reads: label on the left, value on the right,
 * hairlines between rows.
 *
 *   <DataTable title="{{ task_name }}" labelWidth={112} rows={[
 *     ["Due", <b>{"{{ due }}"}</b>],
 *     ["Engagement", "{{ engagement }}"],
 *   ]} />
 *
 *   <DataTable each="details" />          one row per { label, value } item the sender supplies
 *
 *   panel    a grey card, for details in the flow of a message (a task's dates, a quote's totals)
 *   outline  a white card with a border, for a record the reader will refer back to (a notice)
 *
 * Values wrap anywhere, so a long email address or URL never pushes the table off a phone.
 */
import type { ReactNode } from 'react';
import { color, fonts } from '../theme';

export function DataTable({ rows = [], title, variant = 'panel', labelWidth = 128, each }: {
  /** Fixed rows, as [label, value]. A value can be a field: "{{ client }}". */
  rows?: [label: string, value: ReactNode][];
  /** A bold line at the top of the card — usually the thing the rows describe. */
  title?: ReactNode;
  variant?: 'panel' | 'outline';
  /** The label column's width in px. Fit it to the longest label. */
  labelWidth?: number;
  /** A list field whose items ({ label, value }) become extra rows — Postmark repeats them. */
  each?: string;
}) {
  const bg = variant === 'panel' ? color.panel : color.surface;
  const labelCell = { padding: '10px 12px 10px 0', fontFamily: fonts.body, fontSize: '13px', lineHeight: '20px', color: color.inkMuted };
  const valueCell = { padding: '10px 0', fontFamily: fonts.body, fontSize: '15px', lineHeight: '22px', color: color.ink,
    wordBreak: 'break-word' as const, overflowWrap: 'anywhere' as const };
  return (
    <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0} bgcolor={bg}
      style={{ backgroundColor: bg, borderRadius: '10px', border: `1px solid ${color.rule}` }}>
      <tbody><tr><td style={{ padding: title ? '18px 20px 8px' : '8px 20px' }}>
        {title && (
          <p style={{ margin: '0 0 6px', fontFamily: fonts.body, fontSize: '18px', lineHeight: '26px', fontWeight: 700, color: color.ink }}>
            {title}
          </p>
        )}
        <table role="presentation" width="100%" cellPadding={0} cellSpacing={0} border={0}>
          <tbody>
            {rows.map(([label, value], i) => {
              const top = i ? { borderTop: `1px solid ${color.rule}` } : {};
              return (
                <tr key={label}>
                  <td className="ve-kv-label" width={labelWidth} valign="top" style={{ ...top, ...labelCell }}>{label}</td>
                  <td valign="top" style={{ ...top, ...valueCell }}>{value}</td>
                </tr>
              );
            })}
            {each && <>
              {`{{#each ${each}}}`}
              <tr>
                <td className="ve-kv-label" width={labelWidth} valign="top" style={{ borderTop: rows.length ? `1px solid ${color.rule}` : '0', ...labelCell }}>{'{{ label }}'}</td>
                <td valign="top" style={{ borderTop: rows.length ? `1px solid ${color.rule}` : '0', ...valueCell }}>{'{{ value }}'}</td>
              </tr>
              {'{{/each}}'}
            </>}
          </tbody>
        </table>
      </td></tr></tbody>
    </table>
  );
}
